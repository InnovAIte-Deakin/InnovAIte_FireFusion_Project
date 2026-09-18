"""Tests for multi-task misinformation API integration."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from api.inference.misinformation import predict_misinformation
from api.schemas.misinformation import MisinformationPostOut


@patch("api.inference.misinformation.classify_multitask")
def test_predict_misinformation_returns_all_task_predictions(
    mock_classify_multitask,
) -> None:
    task_predictions = {
        "misinfo": {
            "label_id": 0,
            "label": "FALSE",
            "confidence": 0.70,
            "probabilities": {
                "FALSE": 0.70,
                "TRUE": 0.30,
            },
        },
        "urgency": {
            "label_id": 2,
            "label": "URGENT",
            "confidence": 0.80,
            "probabilities": {
                "NOT_USEFUL": 0.05,
                "NOT_URGENT": 0.15,
                "URGENT": 0.80,
            },
        },
        "humanitarian": {
            "label_id": 3,
            "label": "EVAC",
            "confidence": 0.90,
            "probabilities": {
                "EVAC": 0.90,
                "NOT_HUM": 0.10,
            },
        },
    }
    mock_classify_multitask.return_value = task_predictions

    bundle = SimpleNamespace(
        model_id="misinfo-deberta",
        domain="misinformation",
        kind="deberta_multitask",
        tokenizer=object(),
        model=object(),
        device="cpu",
        max_len=256,
        checkpoint_path=Path("/tmp/multi-task-deberta"),
    )

    result = predict_misinformation(
        {
            "id": "test-post",
            "content": "Authorities issued an emergency evacuation warning.",
        },
        bundle,
    )

    assert result["task_predictions"] == task_predictions
    assert result["label"] == "FALSE"
    assert result["confidence"] == pytest.approx(0.70)
    assert result["risk_score"] == pytest.approx(0.70)
    assert result["severity"] == "MEDIUM"

    validated = MisinformationPostOut.model_validate(result)
    assert validated.task_predictions["urgency"].label == "URGENT"
    assert validated.task_predictions["humanitarian"].label == "EVAC"

    mock_classify_multitask.assert_called_once()