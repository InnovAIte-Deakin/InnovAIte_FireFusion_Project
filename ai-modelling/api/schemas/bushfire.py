"""
Bushfire I/O schemas (GeoJSON) for the ConvLSTM forecaster and TCN risk classifier.

INPUT — GeoJSON FeatureCollection, one Feature per grid cell
    properties.observations : [seq_len, n_features] float matrix, channel order given by
                              ``feature_names`` (falls back to DEFAULT_FEATURE_NAMES)
    properties.grid_row/col : optional grid indices. When present — and the loaded model
                              bundle declares ``grid_shape`` — the inference adapter builds
                              the 5-D tensor the refined ConvLSTM expects:
                              [batch, seq_len, height, width, n_features].
                              When absent, cells are batched as
                              [n_samples, seq_len, 1, 1, n_features] (spatial context lost).

Data variables (default channel order, 7 channels, ERA5-Land):
    0 skin_temperature_c                      °C
    1 soil_temperature_level_1_c              °C
    2 surface_solar_radiation_downwards       J/m^2
    3 surface_thermal_radiation_downwards     J/m^2
    4 temperature_2m_c                        °C
    5 u_component_of_wind_10m                 m/s (eastward)
    6 v_component_of_wind_10m                 m/s (northward)

OUTPUT — GeoJSON FeatureCollection, one Feature per input cell
    forecast            : [horizon, n_output_channels] — forecast environmental variables
    risk_probabilities  : [horizon] bushfire risk probability in [0, 1]
    risk_levels         : [horizon] discrete level 0..4 (see RISK_LEVEL_THRESHOLDS)

Keep DEFAULT_FEATURE_NAMES, DEFAULT_INPUT_STEPS and DEFAULT_HORIZON in sync with
``src/training/ts_convlstm_forecaster_train.py``.
"""
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

# Tensor dimensions the checkpoints were trained with. The adapters prefer the values
# stored in the model bundle metadata; these are the fallbacks used when a checkpoint
# ships without them.
N_DEFAULT_FEATURES = len(DEFAULT_FEATURE_NAMES)
DEFAULT_INPUT_STEPS = 60
DEFAULT_HORIZON = 2

# Bushfire risk probability -> discrete level. Single source of truth for the mapping
# that was previously duplicated inside the classifier adapter.
RISK_LEVEL_THRESHOLDS = (0.2, 0.4, 0.6, 0.8)
RISK_LEVEL_LABELS = ("LOW", "MEDIUM_LOW", "MEDIUM", "MEDIUM_HIGH", "HIGH")


def prob_to_risk_level(prob: float) -> int:
    """Map a probability in [0, 1] to a discrete risk level 0..4."""
    for level, threshold in enumerate(RISK_LEVEL_THRESHOLDS):
        if prob < threshold:
            return level
    return len(RISK_LEVEL_THRESHOLDS)


def risk_level_label(level: int) -> str:
    """Human-readable label for a discrete risk level."""
    if 0 <= level < len(RISK_LEVEL_LABELS):
        return RISK_LEVEL_LABELS[level]
    return "UNKNOWN"


class FeatureTimeseriesPropertiesIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: Optional[str] = None
    # observations: list of timesteps; each timestep is list of feature values in model order
    observations: List[List[float]] = Field(..., description="[[f1...fN], [f1...fN], ...] (seq_len × n_features)")
    timestamps: Optional[List[datetime]] = Field(None, description="ISO8601 timestamps aligned with observations")
   
    grid_row: Optional[int] = Field(None, ge=0, description="Row index (height axis) in the model grid")
    grid_col: Optional[int] = Field(None, ge=0, description="Column index (width axis) in the model grid")

    @field_validator("observations")
    def not_empty(cls, v):
        if not v:
            raise ValueError("observations must be a non-empty list of timesteps")
        return v

    @model_validator(mode="after")
    def validate_grid_position(self):
        if (self.grid_row is None) != (self.grid_col is None):
            raise ValueError("grid_row and grid_col must be provided together")
        return self


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
    schema_version: Optional[str] = Field(None, description="Payload schema version, for compatibility tracking")

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
        seen_cells: set[tuple[int, int]] = set()
        for f in self.features:
            obs = f.properties.observations
            if len(obs) != seq_len:
                raise ValueError("All features must have the same sequence length (seq_len)")
            for row in obs:
                if len(row) != n_features:
                    raise ValueError("All observation rows must have the same number of feature values")
            if f.properties.timestamps is not None and len(f.properties.timestamps) != seq_len:
                raise ValueError("timestamps (if present) must have same length as observations")
            row_idx, col_idx = f.properties.grid_row, f.properties.grid_col
            if row_idx is not None and col_idx is not None:
                cell = (row_idx, col_idx)
                if cell in seen_cells:
                    raise ValueError(f"duplicate grid cell (grid_row={row_idx}, grid_col={col_idx})")
                seen_cells.add(cell)
        return self


# ---- Output schemas ----
class ForecastPropertiesOut(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: Optional[str] = None
    # forecast: list of timesteps; each timestep is list of feature values (horizon × n_features)
    forecast: List[List[float]]
    forecast_timestamps: Optional[List[datetime]] = None
    horizon: Optional[int] = Field(None, description="Number of forecast timesteps returned")
    n_output_channels: Optional[int] = Field(None, description="Number of values per forecast timestep")
    output_feature_names: Optional[List[str]] = Field(None, description="Channel order of each forecast timestep")
    grid_row: Optional[int] = None
    grid_col: Optional[int] = None
    risk_score: Optional[float] = None
    
    risk_probabilities: Optional[List[float]] = Field(None, description="Bushfire risk probability per horizon step")
    risk_levels: Optional[List[int]] = Field(None, description="Discrete risk level 0..4 per horizon step")
    model_id: Optional[str] = None


class GeoFeatureOut(BaseModel):
    type: Literal["Feature"]
    geometry: Dict[str, Any]
    properties: ForecastPropertiesOut


class ForecastResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: Literal["FeatureCollection"]
    features: List[GeoFeatureOut]


class RiskPropertiesOut(BaseModel):
    """Bushfire risk output for one grid cell, one probability per horizon step."""

    model_config = ConfigDict(extra="allow")

    id: Optional[str] = None
    risk_probabilities: List[float] = Field(..., description="Bushfire risk probability per horizon step")
    risk_levels: List[int] = Field(..., description="Discrete risk level 0..4 per horizon step")
    risk_labels: Optional[List[str]] = Field(None, description="Label per risk level (see RISK_LEVEL_LABELS)")
    horizon: Optional[int] = Field(None, description="Number of forecast steps scored")
    model_id: Optional[str] = None

    @model_validator(mode="after")
    def validate_aligned_vectors(self):
        n = len(self.risk_probabilities)
        if len(self.risk_levels) != n:
            raise ValueError("risk_levels must have the same length as risk_probabilities")
        if self.risk_labels is not None and len(self.risk_labels) != n:
            raise ValueError("risk_labels must have the same length as risk_probabilities")
        return self


class GeoRiskFeatureOut(BaseModel):
    type: Literal["Feature"]
    geometry: Dict[str, Any]
    properties: RiskPropertiesOut


class RiskResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: Literal["FeatureCollection"]
    features: List[GeoRiskFeatureOut]
