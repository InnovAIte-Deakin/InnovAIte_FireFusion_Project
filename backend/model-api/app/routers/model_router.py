from fastapi import APIRouter
from pydantic import BaseModel
from app.internal.services.model_service import ModelService

from app.models.geojson_model import FeatureCollection
from app.internal.services.geojson_service import GeoJsonService

router = APIRouter(
    prefix="/model",
    tags=["model"]
)
model_service = ModelService()


class PredictionRequest(BaseModel):
    features: list[float]


@router.get("/hello")
async def hello():
    return {"message": "Hello from model-api"}




geojson_service = GeoJsonService()


@router.get("/geojson")
async def get_geojson():
    return geojson_service.get_geojson()

