from fastapi import APIRouter, Depends

from app.dependencies import verify_auth0_token, require_scope

router = APIRouter(prefix="/auth-demo", tags=["auth-demo"])


@router.get("/public")
async def public_route():
    return {
        "message": "This is a public FireFusion API endpoint. No JWT token is required."
    }


@router.get("/protected")
async def protected_route(payload: dict = Depends(verify_auth0_token)):
    return {
        "message": "Access granted. Auth0 JWT token is valid.",
        "user": payload.get("sub"),
        "audience": payload.get("aud"),
        "issuer": payload.get("iss")
    }


@router.get("/fire-data")
async def protected_fire_data(
    payload: dict = Depends(require_scope("read:fire-data"))
):
    return {
        "message": "Scope validation successful. Protected FireFusion fire data can be accessed.",
        "sample_data": {
            "region": "Victoria",
            "risk_level": "High",
            "temperature": "32°C",
            "wind_speed": "28 km/h",
            "source": "Auth0 protected demo endpoint"
        },
        "user": payload.get("sub"),
        "scope": payload.get("scope")
    }