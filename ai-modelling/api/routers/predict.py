"""
Prediction endpoint for the FireFusion AI Model API.

Accepts a PredictRequest, runs inference (or returns mock results
when no trained model is loaded), and returns a PredictResponse.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request

from api.schemas.request import PredictRequest
from api.schemas.response import CellPrediction, PredictResponse
from api.dependencies import get_model

router = APIRouter(tags=["predict"])

# Version label for mock/stub responses
_MOCK_MODEL_VERSION = "firefusion-mock-v0.1.0"


def _mock_predict(request: PredictRequest) -> PredictResponse:
    """
    Generate deterministic mock predictions.

    Used when no trained model is available. Returns fixed, realistic
    placeholder values so the backend team can integrate and test
    the API contract without waiting for the LSTM to be trained.
    """
    predictions = [
        CellPrediction(
            cell_id=cell.cell_id,
            severity_class=3,
            area_ha_burned=12.5,
            rate_of_spread_ha_per_day=3.2,
            confidence_score=0.72,
        )
        for cell in request.cells
    ]
    return PredictResponse(
        request_id=request.request_id,
        model_version=_MOCK_MODEL_VERSION,
        created_at=datetime.now(timezone.utc),
        predictions=predictions,
    )


def _real_predict(model, request: PredictRequest) -> PredictResponse:
    """
    Run real model inference.

    This is a placeholder that will be filled in once the LSTM model
    is trained and the inference pipeline is defined.  For now it
    raises NotImplementedError to clearly signal it isn't ready.

    TODO: implement actual inference using the loaded model
    """
    # ── Future implementation outline ──────────────────────────
    # 1. Extract features from request into numpy/tensor arrays
    # 2. Run model.predict(features)
    # 3. Map raw outputs to CellPrediction objects
    # 4. Return PredictResponse
    raise NotImplementedError(
        "Real model inference is not yet implemented. "
        "The LSTM model needs to be trained first."
    )


@router.post("/predict", response_model=PredictResponse)
async def predict(
    request: PredictRequest,
    model=Depends(get_model),
):
    """
    Generate fire-spread predictions for one or more grid cells.

    - If a trained model is loaded → runs real inference
    - If no model is loaded → returns deterministic mock predictions

    The request body is validated against the full FireFusion input
    schema (terrain + weather features per cell, exactly 8 timesteps).
    """
    if model is None:
        return _mock_predict(request)

    return _real_predict(model, request)
