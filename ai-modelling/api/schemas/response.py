"""
Pydantic output schemas for the FireFusion prediction API.

Defines the structure returned by POST /predict — one prediction per grid cell.
"""

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class CellPrediction(BaseModel):
    """Prediction result for a single grid cell."""

    cell_id: str = Field(
        ..., description="Matching cell_id from the request"
    )
    severity_class: int = Field(
        ..., ge=1, le=5,
        description="Fire severity classification (1=minimal … 5=catastrophic)"
    )
    area_ha_burned: float = Field(
        ..., ge=0,
        description="Predicted area burned in hectares"
    )
    rate_of_spread_ha_per_day: float = Field(
        ..., ge=0,
        description="Predicted fire spread rate in hectares per day"
    )
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="Model confidence for this prediction (0.0–1.0)"
    )


class PredictResponse(BaseModel):
    """Top-level response body returned by POST /predict."""

    request_id: str = Field(
        ..., description="Echoed from the original request"
    )
    model_version: str = Field(
        ..., description="Version string of the model that produced the predictions"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp when the prediction was generated"
    )
    predictions: List[CellPrediction] = Field(
        ..., description="One prediction per input cell"
    )
