from pydantic import BaseModel, Field
from typing import Literal


class Confidence(BaseModel):
    severity_class_prob: float = Field(..., ge=0, le=1)


class Environment(BaseModel):
    temperature_c: float | None = None
    relative_humidity_pct: float | None = None
    wind_speed_kmh: float | None = None
    wind_direction_deg: float | None = None
    ffdi: float | None = None
    fuel_moisture_pct: float | None = None


class Properties(BaseModel):
    cell_id: str | None = None
    timestamp: str | None = None
    interval_h: int | None = None
    severity_class: int = Field(..., ge=1, le=5)
    confidence: Confidence
    environment: Environment | None = None


class Geometry(BaseModel):
    type: Literal["Polygon"]
    coordinates: list[list[list[float]]]


class Feature(BaseModel):
    type: Literal["Feature"] = "Feature"
    geometry: Geometry
    properties: Properties


class Metadata(BaseModel):
    model_version: str | None = None
    generated_at: str | None = None
    forecast_horizon_h: int | None = None
    forecast_interval_h: int | None = None
    grid_resolution_m: int | None = None
    total_cells: int | None = None
    bbox: list[float] | None = None
    crs: str | None = None


class FeatureCollection(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    metadata: Metadata | None = None
    features: list[Feature]