"""
Pydantic input schemas for the FireFusion prediction API.

Maps to the project's Inference Schema — terrain (static) features
plus time-series weather (temporal) features per grid cell.
"""

from pydantic import BaseModel, Field, model_validator
from typing import List


# ── Static (terrain / fuel) features for a single grid cell ──────────

class StaticFeatures(BaseModel):
    """Eight terrain and fuel-load variables that don't change across timesteps."""

    elevation_m: float = Field(
        ..., description="Elevation above sea level in metres"
    )
    slope_deg: float = Field(
        ..., ge=0, le=90, description="Terrain slope in degrees (0–90)"
    )
    aspect_deg: float = Field(
        ..., ge=0, le=360, description="Terrain aspect in degrees (0–360, north=0)"
    )
    land_cover_class: int = Field(
        ..., ge=0, description="MODIS land-cover classification code"
    )
    ndvi: float = Field(
        ..., ge=-1.0, le=1.0,
        description="Normalised Difference Vegetation Index (−1 to 1)"
    )
    soil_moisture_pct: float = Field(
        ..., ge=0, le=100, description="Volumetric soil moisture (%)"
    )
    fuel_load_t_per_ha: float = Field(
        ..., ge=0, description="Surface fuel load in tonnes per hectare"
    )
    distance_to_road_km: float = Field(
        ..., ge=0, description="Distance to nearest road in km"
    )


# ── One weather observation (timestep) ───────────────────────────────

class Timestep(BaseModel):
    """A single weather observation within the temporal sequence."""

    temperature_c: float = Field(
        ..., description="Air temperature in Celsius"
    )
    rel_humidity_pct: float = Field(
        ..., ge=0, le=100, description="Relative humidity (%)"
    )
    wind_speed_kmh: float = Field(
        ..., ge=0, description="Wind speed in km/h"
    )
    wind_direction_deg: float = Field(
        ..., ge=0, le=360, description="Wind direction in degrees (0–360)"
    )
    precipitation_mm: float = Field(
        ..., ge=0, description="Precipitation in mm"
    )
    drought_index: float = Field(
        ..., description="Drought factor / index value"
    )
    solar_radiation_w_m2: float = Field(
        ..., ge=0, description="Incoming solar radiation (W/m²)"
    )
    air_pressure_hpa: float = Field(
        ..., ge=0, description="Atmospheric pressure in hPa"
    )
    day_offset: int = Field(
        ..., ge=0, description="Day offset from forecast start (0-based)"
    )
    hour_offset: int = Field(
        ..., ge=0, le=23, description="Hour of day (0–23)"
    )


# ── Temporal feature wrapper (sequence of timesteps) ────────────────

class TemporalFeatures(BaseModel):
    """
    Ordered sequence of weather timesteps for one grid cell.

    The model expects exactly 8 timesteps (4 days × 2 observations/day).
    """

    timesteps: List[Timestep] = Field(
        ..., min_length=8, max_length=8,
        description="Exactly 8 weather timesteps (4 days × 2/day)"
    )


# ── One grid cell with both static and temporal data ────────────────

class CellInput(BaseModel):
    """Input data for a single Victorian grid cell."""

    cell_id: str = Field(
        ..., pattern=r"^VIC_GRID_\d{4}$",
        description="Grid cell identifier, e.g. VIC_GRID_0042"
    )
    static_features: StaticFeatures
    temporal_features: TemporalFeatures


# ── Top-level prediction request ────────────────────────────────────

class PredictRequest(BaseModel):
    """
    Top-level request body for POST /predict.

    Contains metadata plus a list of grid cells to predict.
    """

    request_id: str = Field(
        ..., description="Unique identifier for this prediction request"
    )
    region_id: str = Field(
        ..., description="Region identifier, e.g. 'VIC_GIPPSLAND'"
    )
    forecast_horizon_days: int = Field(
        ..., ge=1, le=7,
        description="Number of days to forecast (1–7)"
    )
    total_timesteps: int = Field(
        ..., description="Total timesteps per cell (must equal 8)"
    )
    cells: List[CellInput] = Field(
        ..., min_length=1,
        description="One or more grid cells to predict"
    )

    @model_validator(mode="after")
    def validate_total_timesteps(self) -> "PredictRequest":
        """Ensure total_timesteps matches the expected 8."""
        if self.total_timesteps != 8:
            raise ValueError(
                f"total_timesteps must be 8, got {self.total_timesteps}"
            )
        return self
