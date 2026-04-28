"""
Health check endpoint for the FireFusion AI Model API.

Used by the backend/orchestrator to verify the service is alive
and whether a real model is loaded before sending prediction requests.
"""

from fastapi import APIRouter, Request

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(request: Request):
    """
    Return service health status.

    Response:
        - status: "ok" if the service is running
        - model_loaded: true if a trained model file was loaded at startup
    """
    model = request.app.state.model
    return {
        "status": "ok",
        "model_loaded": model is not None,
    }
