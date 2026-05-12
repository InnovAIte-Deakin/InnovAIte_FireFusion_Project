"""
Prediction routes. Add ``bushfire.py`` (and include its router) when that model is ready.
"""
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from api.inference.misinformation import predict_misinformation
from api.model_loader import default_model_id_for_domain, get_model, list_models
from api.schemas.misinformation import MisinformationPostIn, MisinformationPostOut

router = APIRouter(prefix="/predict", tags=["predict"])


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