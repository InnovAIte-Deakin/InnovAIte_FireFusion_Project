from fastapi import APIRouter, Depends
from app.security.jwt import verify_token
from app.services.model_service import get_prediction
from app.services.weather_service import get_weather

router = APIRouter()

@router.get("/")
def root(token: dict = Depends(verify_token)):
    return {"message": "FireFusion API running"}

@router.get("/dashboard")
def dashboard(token: dict = Depends(verify_token)):
    weather = get_weather()
    prediction = get_prediction()

    return {
        "weather": weather,
        "prediction": prediction
    }