"""Auth-specific HTTP exceptions.

Subclassing HTTPException keeps the error responses consistent and makes them
easy to log/measure later. FastAPI automatically turns these into JSON
responses with the right status code.
"""
from fastapi import HTTPException, status


class AuthError(HTTPException):
    """Base class for any auth failure. Useful for catching all of them."""


class MissingTokenError(AuthError):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing or malformed",
            # The WWW-Authenticate header is what tells API clients to send a
            # bearer token. Required by RFC 6750.
            headers={"WWW-Authenticate": "Bearer"},
        )


class InvalidTokenError(AuthError):
    def __init__(self, reason: str = "Invalid token") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=reason,
            headers={"WWW-Authenticate": "Bearer"},
        )


class InsufficientRoleError(AuthError):
    """403 — the user is logged in but doesn't have the required role."""

    def __init__(self, required: str) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{required}' required for this action",
        )
