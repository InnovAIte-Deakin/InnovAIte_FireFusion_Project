import logging

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from ..internal.services.forecast_service import ForecastService
from ..internal.services.websocket_connection_manager import ws_manager
from ..internal.services.caching_service import cache_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["bushfire"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # leave connection open until user dc
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


@router.get(
    "/bushfire-forecast",
    tags=["bushfire"],
    summary="Fire Risk Map data",
    response_description="GeoJSON FeatureCollection of bushfire risk polygons",
    responses={
        200: {
            "description": "Risk polygons as GeoJSON. Returns an empty FeatureCollection when no prediction is available.",
            "content": {
                "application/json": {
                    "example": {
                        "type": "FeatureCollection",
                        "features": [
                            {
                                "type": "Feature",
                                "geometry": {
                                    "type": "Polygon",
                                    "coordinates": [[
                                        [142.1560, -37.5600],
                                        [142.3200, -37.7400],
                                        [142.5100, -37.6500],
                                        [142.3800, -37.5100],
                                        [142.1560, -37.5600],
                                    ]],
                                },
                                "properties": {"risk_factor": 3},
                            }
                        ],
                    }
                }
            },
        },
        503: {"description": "Forecast data temporarily unavailable"},
    },
)
async def get_bushfire_forecast(service: ForecastService = Depends(ForecastService)):
    """Serve Fire Risk Map data as a GeoJSON FeatureCollection.

    Always returns a valid FeatureCollection so the map can render without
    special-casing missing data. See docs/fire-risk-map-api-contract.md.
    """
    try:
        return await service.fetch_predictions()
    except Exception:
        logger.exception("Failed to fetch bushfire forecast")
        raise HTTPException(status_code=503, detail="Forecast data temporarily unavailable")
