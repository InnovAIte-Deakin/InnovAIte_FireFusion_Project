from typing import List
from pydantic import BaseModel, Field
from datetime import datetime



LSTM_FEATURE_ORDER = [
    "skin_temperature_c",
    "soil_temperature_level_1_c",
    "surface_solar_radiation_downwards",
    "surface_thermal_radiation_downwards",
    "temperature_2m_c",
    "u_component_of_wind_10m",
    "v_component_of_wind_10m",
]


class TensorShapeV2(BaseModel):
    input_steps: int = 60
    horizon: int = 2
    temporal_features: int = 7


class TemporalTimestepV2(BaseModel):
    values: List[float] = Field(
        ...,
        min_length=7,
        max_length=7,
        description="Values must follow LSTM_FEATURE_ORDER"
    )


class TemporalFeaturesV2(BaseModel):
    feature_order: List[str] = Field(
        default=LSTM_FEATURE_ORDER,
        min_length=7,
        max_length=7
    )

    timesteps: List[TemporalTimestepV2] = Field(
        ...,
        min_length=60,
        max_length=60,
        description="Exactly 60 historical timesteps required by LSTM model"
    )


class CellInputV2(BaseModel):
    cell_id: str
    temporal_features: TemporalFeaturesV2


class FireEventV2(BaseModel):
    schema_version: str = "2.0.0"
    request_id: str
    created_at: datetime
    forecast_horizon_h: int = 2

    tensor_shape: TensorShapeV2 = TensorShapeV2()

    cells: List[CellInputV2] = Field(
        ...,
        min_length=1,
        description="One or more grid cells for forecasting"
    )