"""
Prediction routes for misinformation and bushfire models.
"""
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from api.inference.misinformation import predict_misinformation
from api.inference.bushfire_classifier import predict_bushfire_classify, predict_bushfire_classify_from_forecast
from api.inference.bushfire_forecaster import predict_bushfire_forecast
from api.model_loader import default_model_id_for_domain, get_model, list_models
from api.schemas.misinformation import MisinformationPostIn, MisinformationPostOut
from api.schemas.bushfire import ForecastRequest

router = APIRouter(prefix="/predict", tags=["predict"])

# --- Misinformation Detection ---
@router.post("/misinformation", response_model=MisinformationPostOut)
def predict_misinformation_route(
    body: MisinformationPostIn,
    model_id: str | None = Query(
        default=None,
        description="Registry id from config/models.yaml; defaults to first misinformation model",
    ),
) -> dict[str, Any]:
    mid = model_id or default_model_id_for_domain("misinformation")
    try:
        bundle = get_model(mid)
    except KeyError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if bundle.domain != "misinformation":
        raise HTTPException(
            status_code=400,
            detail=f"model {mid!r} is domain={bundle.domain!r}, expected misinformation",
        )
    payload = body.model_dump(mode="json")
    return predict_misinformation(payload, bundle)


# --- Bushfire Forecasting ---
@router.post("/bushfire/forecast", response_model=dict)
def forecast_bushfire_route(
    body: ForecastRequest,
    model_id: str | None = Query(None, description="Registry id; defaults to first bushfire forecaster"),
) -> dict[str, Any]:
    mid = model_id or default_model_id_for_domain("bushfire")
    try:
        bundle = get_model(mid)
    except KeyError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    
    if bundle.domain != "bushfire" or bundle.kind != "bushfire_forecaster":
        raise HTTPException(
            status_code=400,
            detail=f"model {mid!r} is kind={bundle.kind!r}, expected bushfire_forecaster",
        )
    
    payload = body.model_dump(mode="json")
    return predict_bushfire_forecast(payload, bundle)


# --- Bushfire Classification ---
@router.post("/bushfire/classify", response_model=dict)
def classify_bushfire_route(
    body: ForecastRequest,
    classifier_id: str | None = Query(None, description="Classifier model id; defaults to first bushfire classifier"),
    forecaster_id: str | None = Query(None, description="Forecaster model id; defaults to first bushfire forecaster"),
) -> dict[str, Any]:
    # select classifier bundle
    if classifier_id:
        try:
            classifier_bundle = get_model(classifier_id)
        except KeyError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        if classifier_bundle.kind != "bushfire_classifier":
            raise HTTPException(status_code=400, detail=f"model {classifier_id!r} is kind={classifier_bundle.kind!r}, expected bushfire_classifier")
    else:
        classifiers = [m for m in list_models(domain="bushfire") if m.kind == "bushfire_classifier"]
        if not classifiers:
            raise HTTPException(status_code=400, detail="no bushfire classifier loaded")
        classifier_bundle = classifiers[0]

    # select forecaster bundle
    if forecaster_id:
        try:
            forecaster_bundle = get_model(forecaster_id)
        except KeyError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        if forecaster_bundle.kind != "bushfire_forecaster":
            raise HTTPException(status_code=400, detail=f"model {forecaster_id!r} is kind={forecaster_bundle.kind!r}, expected bushfire_forecaster")
    else:
        forecasters = [m for m in list_models(domain="bushfire") if m.kind == "bushfire_forecaster"]
        if not forecasters:
            raise HTTPException(status_code=400, detail="no bushfire forecaster loaded")
        forecaster_bundle = forecasters[0]

    payload = body.model_dump(mode="json")
    # 1) run forecaster
    forecast_fc = predict_bushfire_forecast(payload, forecaster_bundle)
    # 2) run classifier on forecaster output + original input
    return predict_bushfire_classify_from_forecast(forecast_fc, payload, classifier_bundle)


@router.get("/models")
def list_loaded_models(domain: str | None = None) -> dict[str, Any]:
    models = list_models(domain=domain)
    return {
        "models": [
            {
                "model_id": m.model_id,
                "domain": m.domain,
                "kind": m.kind,
                "checkpoint": str(m.checkpoint_path),
            }
            for m in models
        ]
    }