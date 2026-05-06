"""Shared FastAPI dependencies, including JWT authentication.

Two dependencies are exposed:

  - get_current_user — apply to any route that requires authentication.
    It returns the JWT claims dict, so the route handler can use the
    user's `sub`, email, etc.

  - require_role(name) — a *factory* that returns a dependency. Use it
    when a route needs more than just authentication; e.g.
        @router.get("/", dependencies=[Depends(require_role("admin"))])

Reference: https://fastapi.tiangolo.com/tutorial/dependencies/
"""
from typing import Annotated, Any

from fastapi import Depends, Header

from app.auth.exceptions import (
    InsufficientRoleError,
    MissingTokenError,
)
from app.auth.jwt_validator import verify_token
from app.config.config import Environment, environment


def _extract_bearer(authorization: str | None) -> str:
    """Pull the raw token out of an `Authorization: Bearer <token>` header."""
    if not authorization:
        raise MissingTokenError()
    parts = authorization.split(maxsplit=1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise MissingTokenError()
    return parts[1]


def get_environment() -> Environment:
    """Dependency-injectable accessor for the singleton Environment."""
    return environment


def get_current_user(
    env: Annotated[Environment, Depends(get_environment)],
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    """FastAPI dependency: requires a valid JWT, returns the claims dict.

    Apply with `user: Annotated[dict, Depends(get_current_user)]` or
    `user = Depends(get_current_user)` in a path operation function.
    """
    token = _extract_bearer(authorization)
    return verify_token(token, env)


def require_role(role: str):
    """Dependency factory: requires the user to have the named role.

    `require_role` is *called* with the role name; it *returns* the actual
    dependency. This is a standard FastAPI pattern for parameterised
    dependencies. See:
    https://fastapi.tiangolo.com/advanced/advanced-dependencies/#parameterized-dependencies
    """

    def _checker(
        user: Annotated[dict[str, Any], Depends(get_current_user)],
        env: Annotated[Environment, Depends(get_environment)],
    ) -> dict[str, Any]:
        # The role list lives in the namespaced custom claim our
        # Post-Login Action wrote into the token at issuance time.
        roles = user.get(env.role_claim, [])
        if role not in roles:
            raise InsufficientRoleError(required=role)
        return user

    return _checker
