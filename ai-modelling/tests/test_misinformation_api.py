from types import SimpleNamespace

import pytest
import torch
from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app, raise_server_exceptions=False)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_endpoint():
    response = client.get("/ready")

    assert response.status_code == 200

    body = response.json()

    assert "ready" in body
    assert "load_errors" in body
    assert isinstance(body["ready"], bool)
    assert isinstance(body["load_errors"], list)


def test_models_endpoint_returns_loaded_models():
    response = client.get("/predict/models")

    assert response.status_code == 200

    body = response.json()

    assert "models" in body
    assert isinstance(body["models"], list)

    for model in body["models"]:
        assert "model_id" in model
        assert "domain" in model
        assert "kind" in model
        assert "checkpoint" in model


def test_misinformation_rejects_missing_id():
    response = client.post(
        "/predict/misinformation",
        json={
            "content": "Emergency services have issued a bushfire warning.",
        },
    )

    assert response.status_code == 422

    detail = response.json()["detail"]
    assert detail[0]["loc"] == ["body", "id"]
    assert detail[0]["type"] == "missing"


def test_misinformation_rejects_missing_content():
    response = client.post(
        "/predict/misinformation",
        json={
            "id": "test-001",
        },
    )

    assert response.status_code == 422

    detail = response.json()["detail"]
    assert detail[0]["loc"] == ["body", "content"]
    assert detail[0]["type"] == "missing"


def test_misinformation_rejects_negative_share_count():
    response = client.post(
        "/predict/misinformation",
        json={
            "id": "test-002",
            "content": "A test claim.",
            "share_count": -1,
        },
    )

    assert response.status_code == 422

    detail = response.json()["detail"]
    assert detail[0]["loc"] == ["body", "share_count"]
    assert detail[0]["type"] == "greater_than_equal"


def test_misinformation_rejects_extra_fields():
    response = client.post(
        "/predict/misinformation",
        json={
            "id": "test-003",
            "content": "A test claim.",
            "unknown_field": "should-be-rejected",
        },
    )

    assert response.status_code == 422

    detail = response.json()["detail"]
    assert detail[0]["loc"] == ["body", "unknown_field"]
    assert detail[0]["type"] == "extra_forbidden"


def test_misinformation_rejects_invalid_timestamp():
    response = client.post(
        "/predict/misinformation",
        json={
            "id": "test-004",
            "content": "A test claim.",
            "ts": "not-a-valid-date",
        },
    )

    assert response.status_code == 422

    detail = response.json()["detail"]
    assert detail[0]["loc"] == ["body", "ts"]
    assert detail[0]["type"] == "datetime_from_date_parsing"


def test_misinformation_valid_request_reaches_model_layer():
    response = client.post(
        "/predict/misinformation",
        json={
            "id": "test-005",
            "author_name": "Test User",
            "platform": "Test",
            "content": "Emergency services have issued a bushfire warning.",
            "share_count": 10,
            "ts": "2026-08-19T05:00:00",
            "post_url": "https://example.com/test",
        },
    )

    # The request is valid, but the configured misinformation
    # checkpoint is unavailable in the current checkout.
    assert response.status_code == 500


def test_misinformation_returns_prediction_with_mocked_model(monkeypatch):
    class DummyTokenizer:
        def __call__(
            self,
            text,
            truncation,
            padding,
            max_length,
            return_tensors,
        ):
            return {
                "input_ids": torch.ones(
                    (1, max_length),
                    dtype=torch.long,
                ),
                "attention_mask": torch.ones(
                    (1, max_length),
                    dtype=torch.long,
                ),
            }

    class DummyModel:
        def __init__(self):
            self.config = SimpleNamespace(
                id2label={
                    0: "non_misinformation",
                    1: "misinformation",
                }
            )

        def eval(self):
            pass

        def __call__(self, **kwargs):
            return SimpleNamespace(
                logits=torch.tensor([[0.2, 1.8]])
            )

    dummy_bundle = SimpleNamespace(
        model_id="test-misinfo-model",
        domain="misinformation",
        tokenizer=DummyTokenizer(),
        model=DummyModel(),
        device=torch.device("cpu"),
        max_len=256,
        checkpoint_path="test/checkpoint",
    )

    monkeypatch.setattr(
        "api.routers.predict.default_model_id_for_domain",
        lambda domain: "test-misinfo-model",
    )

    monkeypatch.setattr(
        "api.routers.predict.get_model",
        lambda model_id: dummy_bundle,
    )

    response = client.post(
        "/predict/misinformation",
        json={
            "id": "test-007",
            "author_name": "Test User",
            "platform": "Test",
            "content": "A bushfire warning has been issued.",
            "share_count": 10,
            "ts": "2026-08-19T05:00:00",
            "post_url": "https://example.com/test",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["model_id"] == "test-misinfo-model"
    assert body["domain"] == "misinformation"
    assert body["id"] == "test-007"
    assert body["label_id"] == 1
    assert body["label"] == "misinformation"
    assert 0.0 <= body["confidence"] <= 1.0
    assert set(body["probabilities"]) == {
        "non_misinformation",
        "misinformation",
    }
    assert sum(body["probabilities"].values()) == pytest.approx(1.0)
    assert body["risk_score"] == pytest.approx(
        max(body["probabilities"].values())
    )
    assert body["severity"] in {
        "CRITICAL",
        "HIGH",
        "MEDIUM",
        "LOW",
    }


def test_misinformation_rejects_unknown_model_id():
    response = client.post(
        "/predict/misinformation?model_id=does-not-exist",
        json={
            "id": "test-006",
            "content": "A test claim.",
        },
    )

    assert response.status_code == 400

    body = response.json()

    assert "detail" in body
    assert "unknown model_id" in body["detail"]