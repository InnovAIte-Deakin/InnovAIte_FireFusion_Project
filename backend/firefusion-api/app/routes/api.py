from fastapi import APIRouter, Depends
from app.security.jwt import verify_token
from app.services.model_service import get_prediction
from app.services.weather_service import get_weather
from app.utils.geojson import to_geojson
from app.services.redis_service import (
    save_prediction,
    get_all_history,
    get_latest
)

router = APIRouter()


@router.get("/")
def root(token: dict = Depends(verify_token)):
    return {"message": "FireFusion API running"}


@router.get("/dashboard")
async def dashboard(token: dict = Depends(verify_token)):

    weather = get_weather()  # used only for ML input, NOT stored
    prediction = get_prediction()

    geojson = to_geojson(prediction)

    # 🔥 STORE ONLY PREDICTION GEOJSON
    save_prediction(geojson)

    return {
        "weather": weather,
        "prediction": prediction
    }


@router.get("/history")
def history(token: dict = Depends(verify_token)):
    return get_all_history()


@router.get("/history/latest")
def latest(token: dict = Depends(verify_token)):
    return get_latest()