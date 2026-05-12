"""Liveness and readiness probes."""
from fastapi import APIRouter

from api.model_loader import is_ready, load_errors

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
def ready() -> dict[str, object]:
    return {
        "ready": is_ready(),
        "load_errors": load_errors(),
    }