from pathlib import Path
from unittest.mock import Mock

import pytest
import torch
from fastapi import FastAPI
from fastapi.testclient import TestClient

import api.inference.misinformation as inference
import api.model_loader as model_loader
import api.routers.predict as predict_router
from api.model_loader import LoadedModel
from api.schemas.misinformation import MisinformationPostOut


def make_bundle(kind: str) -> LoadedModel:
    return LoadedModel(
        model_id="misinfo-deberta",
        domain="misinformation",
        kind=kind,
        tokenizer=object(),
        model=object(),
        device=torch.device("cpu"),
        max_len=128,
        checkpoint_path=Path("checkpoints/test"),
    )


def multitask_predictions() -> dict:
    return {
        "misinfo": {
            "label_id": 1,
            "label": "TRUE",
            "confidence": 0.90,
            "probabilities": {"FALSE": 0.10, "TRUE": 0.90},
        },
        "urgency": {
            "label_id": 2,
            "label": "URGENT",
            "confidence": 0.70,
            "probabilities": {
                "NOT_USEFUL": 0.10,
                "NOT_URGENT": 0.20,
                "URGENT": 0.70,
            },
        },
        "humanitarian": {
            "label_id": 2,
            "label": "WARN",
            "confidence": 0.60,
            "probabilities": {
                "HMN_DMG": 0.10,
                "MAT_DMG": 0.10,
                "WARN": 0.60,
                "EVAC": 0.10,
                "HMN_MISS": 0.05,
                "VOLUNTEER": 0.05,
            },
        },
    }


def test_multitask_inference_returns_all_three_predictions(monkeypatch):
    monkeypatch.setattr(
        inference,
        "classify_multitask",
        lambda *args, **kwargs: multitask_predictions(),
    )

    result = inference.predict_misinformation(
        {"id": "post-1", "content": "Emergency warning near the fire zone"},
        make_bundle("deberta_multitask"),
    )

    validated = MisinformationPostOut.model_validate(result)

    assert validated.misinformation.label == "TRUE"
    assert validated.misinformation.risk_score == pytest.approx(0.90)
    assert validated.misinformation.severity == "CRITICAL"
    assert validated.urgency is not None
    assert validated.urgency.label == "URGENT"
    assert validated.humanitarian_task is not None
    assert validated.humanitarian_task.label == "WARN"


def test_binary_model_remains_backward_compatible(monkeypatch):
    monkeypatch.setattr(
        inference,
        "classify_text",
        lambda *args, **kwargs: {
            "label_id": 0,
            "label": "non_misinformation",
            "confidence": 0.80,
            "probabilities": {
                "non_misinformation": 0.80,
                "misinformation": 0.20,
            },
        },
    )

    result = inference.predict_misinformation(
        {"id": "post-2", "content": "Official incident update"},
        make_bundle("deberta_sequence_binary"),
    )

    validated = MisinformationPostOut.model_validate(result)

    assert validated.misinformation.label == "non_misinformation"
    assert validated.urgency is None
    assert validated.humanitarian_task is None


def test_empty_content_is_rejected():
    with pytest.raises(ValueError, match="non-empty"):
        inference.predict_misinformation(
            {"id": "post-3", "content": "   "},
            make_bundle("deberta_multitask"),
        )


def test_multitask_loader_uses_manifest_checkpoint(tmp_path, monkeypatch):
    checkpoint = tmp_path / "deberta_multitask"
    checkpoint.mkdir()
    (checkpoint / "tasks.json").write_text("{}", encoding="utf-8")
    (checkpoint / "model.pt").write_bytes(b"test")

    fake_model = Mock()
    fake_model.tasks = {
        "misinfo": object(),
        "urgency": object(),
        "humanitarian": object(),
    }

    monkeypatch.setattr(
        model_loader,
        "load_multitask_from_checkpoint",
        lambda path, device: (object(), fake_model, 256),
    )

    bundle = model_loader._load_deberta_multitask(
        "misinfo-deberta",
        "misinformation",
        checkpoint,
    )

    assert bundle.kind == "deberta_multitask"
    assert bundle.max_len == 256
    assert bundle.metadata == {
        "tasks": ["misinfo", "urgency", "humanitarian"]
    }
    fake_model.eval.assert_called_once()


def test_single_and_batch_routes_return_multitask_schema(monkeypatch):
    monkeypatch.setattr(
        inference,
        "classify_multitask",
        lambda *args, **kwargs: multitask_predictions(),
    )
    monkeypatch.setattr(
        predict_router,
        "default_model_id_for_domain",
        lambda domain: "misinfo-deberta",
    )
    monkeypatch.setattr(
        predict_router,
        "get_model",
        lambda model_id: make_bundle("deberta_multitask"),
    )

    app = FastAPI()
    app.include_router(predict_router.router)
    client = TestClient(app)

    post = {
        "id": "post-4",
        "content": "Urgent warning about an approaching bushfire",
    }

    single_response = client.post("/predict/misinformation", json=post)
    assert single_response.status_code == 200
    assert single_response.json()["urgency"]["label"] == "URGENT"

    batch_response = client.post(
        "/predict/misinformation/batch",
        json={"posts": [post, {**post, "id": "post-5"}]},
    )
    assert batch_response.status_code == 200
    assert batch_response.json()["count"] == 2
    assert len(batch_response.json()["results"]) == 2