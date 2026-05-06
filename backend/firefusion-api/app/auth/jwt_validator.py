"""JWT validation against Auth0's JWKS endpoint.

This is the security-critical bit. The contract is simple: given a raw JWT
string and the application Settings, either return the verified claims dict
or raise InvalidTokenError.

Reference patterns drawn from:
  - Auth0 Python (Flask) quickstart:
    https://auth0.com/docs/quickstart/backend/python/interactive
  - python-jose docs:
    https://python-jose.readthedocs.io/en/latest/jwt/api.html
"""
from functools import lru_cache
from typing import Any

import httpx
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTClaimsError, JWTError

from app.auth.exceptions import InvalidTokenError
from app.config.config import Environment


# We cache the JWKS document for the process lifetime. This is fine for the
# prototype: Auth0 rotates signing keys infrequently and a process restart
# refreshes them. A production hardening pass would add a TTL and a
# "refresh on unknown kid" path so key rotation never causes a stale-cache
# 401 storm.
@lru_cache(maxsize=1)
def _fetch_jwks(jwks_url: str) -> dict[str, Any]:
    response = httpx.get(jwks_url, timeout=5.0)
    response.raise_for_status()
    return response.json()


def _signing_key_for(token: str, jwks: dict[str, Any]) -> dict[str, Any]:
    """Find the JWKS entry whose `kid` matches the token's header.

    Every JWT header carries a `kid` (key ID) telling the verifier which key
    in the set to use. Auth0 may have multiple keys active during rotation.
    """
    try:
        unverified_header = jwt.get_unverified_header(token)
    except JWTError as exc:
        raise InvalidTokenError("Malformed token header") from exc

    kid = unverified_header.get("kid")
    if not kid:
        raise InvalidTokenError("Token header missing 'kid'")

    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key
    raise InvalidTokenError("No matching public key for token kid")


def verify_token(token: str, env: Environment) -> dict[str, Any]:
    """Verify a JWT and return its claims dict, or raise InvalidTokenError.

    Validation steps performed:
      1. Fetch JWKS (cached) and pick the public key matching the token's kid.
      2. Verify the RS256 signature against that key.
      3. Verify the audience (`aud`) matches our API.
      4. Verify the issuer (`iss`) matches our Auth0 tenant.
      5. Verify the token has not expired (`exp`).

    Skipping any one of these is a known security bug.
    """
    jwks = _fetch_jwks(env.jwks_url)
    key = _signing_key_for(token, jwks)

    try:
        claims = jwt.decode(
            token,
            key,
            algorithms=["RS256"],            # PIN the algorithm. Without this,
                                             # an attacker can craft alg=none
                                             # or alg=HS256 tokens that the
                                             # library will accept.
            audience=env.auth0_audience,
            issuer=env.issuer,
            options={
                # python-jose's default `leeway` is 0 seconds, which means
                # any clock drift between Auth0 and our server can cause
                # spurious 401s on tokens issued seconds ago. 30s is the
                # JWT-best-practice convention.
                "leeway": 30,
            },
        )
    except ExpiredSignatureError as exc:
        raise InvalidTokenError("Token has expired") from exc
    except JWTClaimsError as exc:
        # Wrong issuer or audience lands here.
        raise InvalidTokenError(f"Token claims invalid: {exc}") from exc
    except JWTError as exc:
        # Bad signature, malformed token, etc.
        raise InvalidTokenError("Token signature invalid") from exc

    return claims
