from pydantic_settings import BaseSettings, SettingsConfigDict

# gets from environment variables (case-insensitive)
# In Docker, env vars come from docker-compose. In local dev, load from .env.
class Environment(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ── Existing infrastructure config ───────────────────────────────────
    broker_url: str
    cache_url: str

    # ── Auth0 / JWT config ───────────────────────────────────────────────
    # Auth0 tenant domain, e.g. "firefusion-dev.au.auth0.com".
    auth0_domain: str

    # The Auth0 API resource identifier we expect in every JWT's `aud` claim.
    # Example: "https://api.firefusion.com".
    auth0_audience: str

    # URL prefix used by our Post-Login Action when writing custom claims.
    # Auth0 requires custom claims to be namespaced like a URL.
    auth0_role_namespace: str = "https://firefusion.com/"

    # Computed properties used by the JWT validator ----------------------
    @property
    def issuer(self) -> str:
        """The full issuer URL Auth0 sets in every JWT's `iss` claim."""
        return f"https://{self.auth0_domain}/"

    @property
    def jwks_url(self) -> str:
        """The JWKS endpoint we fetch Auth0's public keys from."""
        return f"https://{self.auth0_domain}/.well-known/jwks.json"

    @property
    def role_claim(self) -> str:
        """The full claim key our Post-Login Action writes role data under."""
        return f"{self.auth0_role_namespace}roles"


environment = Environment() # type: ignore
