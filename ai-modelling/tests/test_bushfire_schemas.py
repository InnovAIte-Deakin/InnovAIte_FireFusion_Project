"""
Tests for the bushfire API I/O schemas (api/schemas/bushfire.py).

Schema-only: imports pydantic and nothing else, so these run without torch installed.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api.schemas.bushfire import (
    DEFAULT_FEATURE_NAMES,
    DEFAULT_HORIZON,
    DEFAULT_INPUT_STEPS,
    N_DEFAULT_FEATURES,
    RISK_LEVEL_LABELS,
    ForecastPropertiesOut,
    ForecastRequest,
    RiskPropertiesOut,
    RiskResponse,
    prob_to_risk_level,
    risk_level_label,
)

SEQ_LEN = 4


def observations(seq_len=SEQ_LEN, n_features=N_DEFAULT_FEATURES):
    return [[float(t + f) for f in range(n_features)] for t in range(seq_len)]


def collection(*properties):
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [144.9631, -37.8136]},
                "properties": props,
            }
            for props in properties
        ],
    }


# --- dimension constants ---------------------------------------------------
def test_dimension_constants_match_training_config():
    assert N_DEFAULT_FEATURES == len(DEFAULT_FEATURE_NAMES) == 7
    assert DEFAULT_INPUT_STEPS == 60
    assert DEFAULT_HORIZON == 2


# --- risk level mapping ----------------------------------------------------
@pytest.mark.parametrize(
    "prob,level",
    [(0.0, 0), (0.19, 0), (0.2, 1), (0.39, 1), (0.4, 2), (0.59, 2),
     (0.6, 3), (0.79, 3), (0.8, 4), (1.0, 4)],
)
def test_prob_to_risk_level_thresholds(prob, level):
    assert prob_to_risk_level(prob) == level


def test_risk_level_labels():
    assert [risk_level_label(i) for i in range(len(RISK_LEVEL_LABELS))] == list(RISK_LEVEL_LABELS)
    assert risk_level_label(99) == "UNKNOWN"


# --- input schema ----------------------------------------------------------
def test_accepts_payload_without_grid_position():
    """Backward compatibility: the pre-refactor payload shape must still validate."""
    req = ForecastRequest(**collection({"id": "cell-001", "observations": observations()}))
    assert req.features[0].properties.grid_row is None
    assert req.features[0].properties.grid_col is None


def test_accepts_grid_position():
    req = ForecastRequest(**collection(
        {"id": "c00", "observations": observations(), "grid_row": 0, "grid_col": 0},
        {"id": "c01", "observations": observations(), "grid_row": 0, "grid_col": 1},
    ))
    assert [(f.properties.grid_row, f.properties.grid_col) for f in req.features] == [(0, 0), (0, 1)]


def test_grid_row_and_col_must_come_together():
    with pytest.raises(ValueError, match="must be provided together"):
        ForecastRequest(**collection({"observations": observations(), "grid_row": 0}))


def test_grid_indices_must_be_non_negative():
    with pytest.raises(ValueError):
        ForecastRequest(**collection({"observations": observations(), "grid_row": -1, "grid_col": 0}))


def test_duplicate_grid_cell_rejected():
    with pytest.raises(ValueError, match="duplicate grid cell"):
        ForecastRequest(**collection(
            {"id": "a", "observations": observations(), "grid_row": 1, "grid_col": 1},
            {"id": "b", "observations": observations(), "grid_row": 1, "grid_col": 1},
        ))


def test_unknown_property_still_rejected():
    with pytest.raises(ValueError):
        ForecastRequest(**collection({"observations": observations(), "not_a_field": 1}))


def test_empty_observations_rejected():
    with pytest.raises(ValueError, match="non-empty"):
        ForecastRequest(**collection({"observations": []}))


def test_ragged_sequence_lengths_rejected():
    with pytest.raises(ValueError, match="same sequence length"):
        ForecastRequest(**collection(
            {"observations": observations(seq_len=4)},
            {"observations": observations(seq_len=5)},
        ))


def test_feature_names_length_must_match_channels():
    with pytest.raises(ValueError, match="feature_names length"):
        ForecastRequest(
            type="FeatureCollection",
            feature_names=DEFAULT_FEATURE_NAMES[:3],
            features=collection({"observations": observations()})["features"],
        )


def test_schema_version_is_optional_and_accepted():
    req = ForecastRequest(schema_version="2.0.0", **collection({"observations": observations()}))
    assert req.schema_version == "2.0.0"


# --- output schemas --------------------------------------------------------
def test_forecast_properties_reports_output_dimensions():
    props = ForecastPropertiesOut(
        id="cell-001",
        forecast=[[1.0] * N_DEFAULT_FEATURES, [2.0] * N_DEFAULT_FEATURES],
        horizon=2,
        n_output_channels=N_DEFAULT_FEATURES,
        output_feature_names=DEFAULT_FEATURE_NAMES,
        model_id="bushfire-forecaster-v1",
    )
    dumped = props.model_dump(mode="json")
    assert dumped["horizon"] == 2
    assert dumped["n_output_channels"] == N_DEFAULT_FEATURES
    assert dumped["output_feature_names"] == DEFAULT_FEATURE_NAMES
    # Risk fields exist for a single-channel (risk probability) model but stay unset here.
    assert dumped["risk_probabilities"] is None
    assert dumped["risk_levels"] is None


def test_forecast_properties_can_carry_risk_probability_directly():
    """A refined single-channel ConvLSTM can be served through the forecast response."""
    props = ForecastPropertiesOut(
        id="cell-001",
        forecast=[[0.15], [0.85]],
        horizon=2,
        n_output_channels=1,
        risk_probabilities=[0.15, 0.85],
        risk_levels=[prob_to_risk_level(0.15), prob_to_risk_level(0.85)],
        model_id="bushfire-forecaster-v2",
    )
    assert props.risk_levels == [0, 4]


def test_risk_response_shape():
    resp = RiskResponse(
        type="FeatureCollection",
        features=[{
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [144.9631, -37.8136]},
            "properties": {
                "id": "cell-001",
                "risk_probabilities": [0.15, 0.85],
                "risk_levels": [0, 4],
                "risk_labels": ["LOW", "HIGH"],
                "horizon": 2,
                "model_id": "bushfire-classifier-v1",
            },
        }],
    )
    props = resp.model_dump(mode="json")["features"][0]["properties"]
    # Keys the pre-refactor endpoint already returned must all still be present.
    assert {"id", "risk_probabilities", "risk_levels", "model_id"} <= set(props)
    assert props["risk_labels"] == ["LOW", "HIGH"]
    assert props["horizon"] == 2


def test_risk_vectors_must_be_aligned():
    with pytest.raises(ValueError, match="same length"):
        RiskPropertiesOut(risk_probabilities=[0.1, 0.2], risk_levels=[0])
    with pytest.raises(ValueError, match="same length"):
        RiskPropertiesOut(risk_probabilities=[0.1], risk_levels=[0], risk_labels=["LOW", "LOW"])
