from fastapi import APIRouter
from pydantic import BaseModel
from app.internal.services.model_service import ModelService

router = APIRouter()
model_service = ModelService()


class PredictionRequest(BaseModel):
    features: list[float]


@router.get("/hello")
async def hello():
    return {"message": "Hello from model-api"}


@router.post("/predict")
async def predict(request: PredictionRequest):
    prediction = await model_service.predict(request.features)
    return {"prediction": prediction}