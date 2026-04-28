from pydantic import BaseModel, Field
from typing import List, Literal


class Properties(BaseModel):
    risk_factor: int = Field(..., ge=0, le=5)


class Geometry(BaseModel):
    type: Literal["Polygon"]
    coordinates: List[List[List[float]]]


class Feature(BaseModel):
    type: Literal["Feature"]
    geometry: Geometry
    properties: Properties


class FeatureCollection(BaseModel):
    type: Literal["FeatureCollection"]
    features: List[Feature]