from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query
from typing import Optional
from datetime import date
from ..internal.services.forecast_service import ForecastService
from ..internal.services.websocket_connection_manager import ws_manager

router = APIRouter(prefix="/api", tags=["bushfire"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


# ✅ DO NOT TOUCH
@router.get("/bushfire-forecast")
async def get_bushfire_forecast(service: ForecastService = Depends(ForecastService)):
    return await service.fetch_predictions()


# ✅ NEW FUNCTIONALITY ONLY
@router.get("/history")
async def get_history(
    target_date: Optional[date] = Query(None, description="YYYY-MM-DD"),
    service: ForecastService = Depends(ForecastService)
):
    if target_date:
        return await service.fetch_history_by_date(target_date)

    return await service.fetch_all_history()