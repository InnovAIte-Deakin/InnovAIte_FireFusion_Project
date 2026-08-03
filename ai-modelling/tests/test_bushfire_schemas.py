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
    DEFAULT_FIRE_THRESHOLD,
    DEFAULT_HORIZON,
    DEFAULT_INPUT_STEPS,
    N_DEFAULT_FEATURES,
    RISK_LEVEL_LABELS,
    ForecastPropertiesOut,
    ForecastRequest,
    ForecastResponse,
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
    # Single-model ConvLSTM predicts one timestep ahead.
    assert DEFAULT_HORIZON == 1
    assert DEFAULT_FIRE_THRESHOLD == 0.5


# --- fire probability -> risk level ---------------------------------------
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
    """Grid indices are what let the adapter rebuild the 5-D ConvLSTM input tensor."""
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


# --- output schema ---------------------------------------------------------
def test_fire_probability_output():
    """Primary output of the single-model ConvLSTM: probability per horizon step."""
    prob = 0.85
    props = ForecastPropertiesOut(
        id="cell-001",
        fire_probability=[prob],
        is_burning_predicted=[prob > DEFAULT_FIRE_THRESHOLD],
        fire_threshold=DEFAULT_FIRE_THRESHOLD,
        risk_score=prob,
        risk_levels=[prob_to_risk_level(prob)],
        risk_labels=[risk_level_label(prob_to_risk_level(prob))],
        forecast=[[prob]],
        horizon=DEFAULT_HORIZON,
        n_output_channels=1,
        grid_row=3,
        grid_col=7,
        model_id="bushfire-convlstm-v1",
    )
    dumped = props.model_dump(mode="json")
    assert dumped["fire_probability"] == [0.85]
    assert dumped["is_burning_predicted"] == [True]
    assert dumped["risk_levels"] == [4]
    assert dumped["risk_labels"] == ["HIGH"]
    assert dumped["horizon"] == 1 and dumped["n_output_channels"] == 1
    assert dumped["grid_row"] == 3 and dumped["grid_col"] == 7


def test_forecast_row_is_one_horizon_step():
    """5-D model output sliced per cell is [horizon, n_output_channels] — a row per step."""
    props = ForecastPropertiesOut(forecast=[[0.15], [0.85]], horizon=2, n_output_channels=1)
    assert props.forecast == [[0.15], [0.85]]


def test_flat_forecast_rejected():
    """A flat list of probabilities belongs in fire_probability, not forecast."""
    with pytest.raises(ValueError):
        ForecastPropertiesOut(forecast=[0.15, 0.85])


def test_per_horizon_step_vectors_must_be_aligned():
    with pytest.raises(ValueError, match="same length"):
        ForecastPropertiesOut(fire_probability=[0.1, 0.2], is_burning_predicted=[False])
    with pytest.raises(ValueError, match="same length"):
        ForecastPropertiesOut(fire_probability=[0.1], risk_levels=[0], risk_labels=["LOW", "LOW"])


def test_multi_channel_checkpoint_still_serves():
    """A checkpoint with more than one output channel is not locked out by the schema."""
    props = ForecastPropertiesOut(
        forecast=[[1.0, 2.0, 3.0]], horizon=1, n_output_channels=3
    )
    assert props.n_output_channels == 3


def test_response_wraps_features():
    resp = ForecastResponse(
        type="FeatureCollection",
        features=[{
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [144.9631, -37.8136]},
            "properties": {"id": "cell-001", "fire_probability": [0.15], "risk_levels": [0]},
        }],
    )
    props = resp.model_dump(mode="json")["features"][0]["properties"]
    assert props["fire_probability"] == [0.15]
    assert props["risk_levels"] == [0]
