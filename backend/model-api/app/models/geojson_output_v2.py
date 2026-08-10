from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class AtRiskFacilityV2(BaseModel):
    facility_name: str
    facility_type: str
    cell_id: str
    distance_m: float


class MetadataV2(BaseModel):
    model_version: str
    generated_at: str
    forecast_horizon_h: int
    forecast_interval_h: int
    grid_resolution_m: int
    total_cells: int

    bbox: List[float] = Field(..., min_length=4, max_length=4)

    crs: str = "EPSG:4326"

    at_risk_facilities: List[AtRiskFacilityV2] = []


class PolygonGeometryV2(BaseModel):
    type: Literal["Polygon"] = "Polygon"

    coordinates: List


class ConfidenceV2(BaseModel):
    severity_class_prob: float


class EnvironmentV2(BaseModel):
    temperature_c: float
    relative_humidity_pct: float
    wind_speed_kmh: float
    wind_direction_deg: float
    ffdi: float
    fuel_moisture_pct: float


class FeatureMetaV2(BaseModel):
    model_version: str

    cell_id_note: Optional[str] = None
    interval_note: Optional[str] = None


class PredictionPropertiesV2(BaseModel):
    cell_id: str
    timestamp: str
    interval_h: int

    severity_class: int

    confidence: ConfidenceV2

    environment: EnvironmentV2

    meta: FeatureMetaV2 = Field(..., alias="_meta")

    class Config:
        populate_by_name = True


class GeoJSONFeatureV2(BaseModel):
    type: Literal["Feature"] = "Feature"

    geometry: PolygonGeometryV2

    properties: PredictionPropertiesV2


class GeoJSONFeatureCollectionV2(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"

    metadata: MetadataV2

    features: List[GeoJSONFeatureV2]