"""
Tests for the ConvLSTM + per-cell BiLSTM forecaster
(src/models/bushfire/ts_convlstm_bilstm_percell_forecaster.py).
"""
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.models.bushfire.ts_convlstm_bilstm_percell_forecaster import (
    PerCellBiLSTMForecasterConfig,
    MultivariateTSForecasterPerCellBiLSTM,
)


def make_model(input_channels=7, horizon=2, output_channels=7):
    config = PerCellBiLSTMForecasterConfig(
        input_channels=input_channels, horizon=horizon, output_channels=output_channels,
    )
    return MultivariateTSForecasterPerCellBiLSTM(config)


def test_output_shape_and_values():
    model = make_model()
    x = torch.rand(1, 10, 4, 4, 7)
    y = model.predict(x)
    assert y.shape == (1, 2, 4, 4, 7)
    assert not torch.isnan(y).any()
    assert y.min() >= 0.0 and y.max() <= 1.0


def test_grid_size_independence():
    model = make_model()
    y1 = model.predict(torch.rand(1, 10, 4, 4, 7))
    y2 = model.predict(torch.rand(1, 10, 6, 8, 7))
    assert y1.shape == (1, 2, 4, 4, 7)
    assert y2.shape == (1, 2, 6, 8, 7)


def test_deterministic_in_eval_mode():
    model = make_model()
    x = torch.rand(1, 10, 4, 4, 7)
    y1 = model.predict(x)
    y2 = model.predict(x)
    assert torch.equal(y1, y2)


def test_save_load_roundtrip(tmp_path):
    model = make_model()
    x = torch.rand(1, 10, 4, 4, 7)
    y_before = model.predict(x)

    ckpt = tmp_path / "checkpoint.pth"
    model.save(str(ckpt))
    loaded = MultivariateTSForecasterPerCellBiLSTM.load(str(ckpt))
    y_after = loaded.predict(x)

    assert torch.equal(y_before, y_after)
