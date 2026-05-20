from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from typing import Literal

# Default feature order used by the forecaster model (keep in-sync with model code)
DEFAULT_FEATURE_NAMES = [
    "skin_temperature_c",
    "soil_temperature_level_1_c",
    "surface_solar_radiation_downwards",
    "surface_thermal_radiation_downwards",
    "temperature_2m_c",
    "u_component_of_wind_10m",
    "v_component_of_wind_10m",
]


class FeatureTimeseriesPropertiesIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: Optional[str] = None
    # observations: list of timesteps; each timestep is list of feature values in model order
    observations: List[List[float]] = Field(..., description="[[f1...fN], [f1...fN], ...] (seq_len × n_features)")
    timestamps: Optional[List[datetime]] = Field(None, description="ISO8601 timestamps aligned with observations")

    @field_validator("observations")
    def not_empty(cls, v):
        if not v:
            raise ValueError("observations must be a non-empty list of timesteps")
        return v


class GeoFeatureIn(BaseModel):
    type: Literal["Feature"]
    geometry: Dict[str, Any]
    properties: FeatureTimeseriesPropertiesIn


class ForecastRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["FeatureCollection"]
    features: List[GeoFeatureIn]
    # Optional override; if omitted API will use DEFAULT_FEATURE_NAMES
    feature_names: Optional[List[str]] = None
    model_id: Optional[str] = None

    @model_validator(mode="after")
    def validate_consistent_series(self):
        if not self.features:
            raise ValueError("FeatureCollection must contain at least one Feature")
        # infer expected seq_len and n_features from first feature
        first_obs = self.features[0].properties.observations
        seq_len = len(first_obs)
        n_features = len(first_obs[0])
        if self.feature_names is not None and len(self.feature_names) != n_features:
            raise ValueError("feature_names length must match number of features per timestep")
        for f in self.features:
            obs = f.properties.observations
            if len(obs) != seq_len:
                raise ValueError("All features must have the same sequence length (seq_len)")
            for row in obs:
                if len(row) != n_features:
                    raise ValueError("All observation rows must have the same number of feature values")
            if f.properties.timestamps is not None and len(f.properties.timestamps) != seq_len:
                raise ValueError("timestamps (if present) must have same length as observations")
        return self


# ---- Output schemas ----
class ForecastPropertiesOut(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: Optional[str] = None
    # forecast: list of timesteps; each timestep is list of feature values (horizon × n_features)
    forecast: List[List[float]]
    forecast_timestamps: Optional[List[datetime]] = None
    model_id: Optional[str] = None


class GeoFeatureOut(BaseModel):
    type: Literal["Feature"]
    geometry: Dict[str, Any]
    properties: ForecastPropertiesOut


class ForecastResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: Literal["FeatureCollection"]
    features: List[GeoFeatureOut]