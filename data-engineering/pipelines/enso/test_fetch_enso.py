import importlib.util
from pathlib import Path

import pandas as pd
import pytest


DE = Path(__file__).resolve().parents[2]


@pytest.fixture(params=[DE / "fetch_enso.py", DE / "pipelines/enso/fetch_enso.py"],
                ids=["workflow_copy", "pipeline_copy"])
def processor(request, tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("processor_under_test", request.param)
    processor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(processor)
    monkeypatch.setattr(processor, "PROCESSED_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(processor, "DATASETS_ENSO_DIR", str(tmp_path))
    return processor


def test_six_month_lag_uses_calendar_month_when_april_is_missing(processor, tmp_path):
    raw = tmp_path / "example.ascii"
    raw.write_text(
        "SEAS YR TOTAL ANOM\nNDJ 2024 26 -0.5\nDJF 2025 26 0.1\nJFM 2025 26 0.2\n"
        "FMA 2025 26 0.3\nAMJ 2025 26 0.5\nMJJ 2025 26 0.6\nJJA 2025 26 0.7\n"
        "JAS 2025 26 0.8\nASO 2025 26 0.9\nSON 2025 26 1.0\n"
    )
    result = processor.transform_and_standardise(raw).set_index("record_year_month")
    assert result.loc["2025-07", "oni_lag6m"] == result.loc["2025-01", "oni_anomaly"]
    assert pd.isna(result.loc["2025-10", "oni_lag6m"])


def test_missing_anomaly_has_no_phase_and_stays_missing_in_its_lag(processor, tmp_path):
    raw = tmp_path / "missing-reading.ascii"
    raw.write_text("SEAS YR TOTAL ANOM\nDJF 2025 26 NA\nJJA 2025 26 0\n")
    result = processor.transform_and_standardise(raw).set_index("record_year_month")
    assert pd.isna(result.loc["2025-01", "oni_anomaly"])
    assert pd.isna(result.loc["2025-01", "enso_phase"])
    assert result.loc["2025-07", "enso_phase"] == "Neutral"
    assert pd.isna(result.loc["2025-07", "oni_lag6m"])
