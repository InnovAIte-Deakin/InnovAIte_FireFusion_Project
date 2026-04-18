from fastapi import APIRouter, Query
from app.internal.weather_service import get_weather

router = APIRouter()


@router.get("/weather")
async def get_weather_endpoint(location: str = Query(...)):
    """
    GET /api/weather?location=melbourne
    """
    return await get_weather(location)
