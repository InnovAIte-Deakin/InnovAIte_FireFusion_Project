"""Unit tests for CFA pipeline (no Supabase required)."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

PIPELINE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PIPELINE_ROOT))

from config.pipeline_config import VALID_DISTRICT_NUMBERS  # noqa: E402
from scripts.preprocess_cfa_incidents import normalize_columns, parse_incident_datetime, preprocess  # noqa: E402
from scripts.validate_cfa_incidents import validate  # noqa: E402
from utils.season import get_australian_meteorological_season  # noqa: E402
from utils.time_registry import TimeRegistryResolver  # noqa: E402


def test_season_summer_january():
    assert get_australian_meteorological_season(1) == "Summer"


def test_season_winter_july():
    assert get_australian_meteorological_season(7) == "Winter"


def test_parse_incident_datetime_melbourne():
    raw = pd.Series(["1/07/2020  1:17:10 AM"])
    parsed = parse_incident_datetime(raw)
    assert parsed.dt.tz is not None
    assert str(parsed.dt.tz) == "Australia/Melbourne"


def test_normalize_columns():
    df = pd.DataFrame(
        {
            "incident_datetime": ["1/07/2020  1:17:10 AM"],
            "incident_no": [781320],
            "District_no": [24],
            "incident_type_code": [151.0],
            "incident_type": ["Passenger vehicle fire including buses"],
        }
    )
    out = normalize_columns(df)
    assert "district_no" in out.columns
    assert "incident_no" in out.columns


def test_preprocess_sample_row():
    df = pd.DataFrame(
        {
            "incident_datetime": ["1/07/2020  1:17:10 AM", "2/07/2020  2:00:00 AM"],
            "incident_no": [781320, 781321],
            "District_no": [24, 17],
            "incident_type_code": [151.0, 321.0],
            "incident_type": ["Vehicle fire", "EMS call"],
        }
    )
    processed, stats = preprocess(df)
    assert stats["output_rows"] == 2
    assert set(processed["district_no"]) <= VALID_DISTRICT_NUMBERS
    assert "reference_latitude" in processed.columns
    assert "datetime_record_key" in processed.columns


def test_preprocess_quarantines_unknown_district():
    df = pd.DataFrame(
        {
            "incident_datetime": ["1/07/2020  1:17:10 AM"],
            "incident_no": [1],
            "District_no": [99],
            "incident_type_code": [1.0],
            "incident_type": ["Test"],
        }
    )
    processed, stats = preprocess(df)
    assert stats["quarantine_unknown_district"] == 1
    assert len(processed) == 0


def test_validate_processed_ok():
    df = pd.DataFrame(
        {
            "incident_id": [1],
            "district_no": [24],
            "reference_latitude": [-36.12],
            "reference_longitude": [146.88],
            "datetime_record_key": ["2020-07-01 01:17:00"],
            "season": ["Winter"],
            "source_system": ["CFA Incident Summary"],
            "incident_type_code": [151.0],
            "incident_type": ["Test"],
        }
    )
    report = validate(df)
    assert report["validation_passed"] is True


def test_time_registry_key_format():
    ts = pd.Timestamp("2020-07-01 01:17:10")  # naive = registry storage format
    assert TimeRegistryResolver.to_registry_key(ts) == "2020-07-01 01:17:10"
