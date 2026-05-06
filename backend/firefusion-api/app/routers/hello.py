from typing import Annotated, Any

from fastapi import APIRouter, Depends

from app.dependencies import get_current_user, require_role
from app.internal.services.hello_service import HelloService

router = APIRouter(prefix="/hello", tags=["hello"])


@router.get("/")
async def hello(
    service: HelloService = Depends(HelloService),
):
    """Public — no auth required. Sanity check that the server is alive."""
    return await service.hello()


@router.get("/me")
async def hello_me(
    user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> dict[str, Any]:
    """Any authenticated user. Echoes back useful claims for debugging.

    Curl test:
      curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/hello/me
    """
    return {
        "sub": user.get("sub"),
        "scope": user.get("scope"),
        "claims": user,
    }


@router.get(
    "/admin",
    dependencies=[Depends(require_role("admin"))],
)
async def hello_admin() -> dict[str, str]:
    """Admin-only — proves the role check works.

    Returns 200 only if the JWT carries our custom `roles` claim with `admin`.
    Returns 403 otherwise (assuming the token is otherwise valid).
    """
    return {"message": "Hello, admin!"}
