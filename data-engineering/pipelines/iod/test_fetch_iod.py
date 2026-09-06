"""
Pytest skeleton for the IOD (Indian Ocean Dipole) processor.

Drafted ahead of the actual processor being built, mirroring the ENSO
processor's test needs plus the extra running-mean step IOD requires.
See iod_test_plan.md for the full rationale behind each test.

NOTE: function names below (fetch_raw_data, compute_running_mean,
assign_phase, transform_and_standardise) are assumptions based on the
ENSO pattern in fetch_enso.py. Update the import path and function names
once the real IOD module exists.
"""

import pandas as pd
import pytest

# Once the real module exists, replace this with:
#   from data_engineering.pipelines.iod.fetch_iod import (
#       assign_phase,
#       compute_running_mean,
#       transform_and_standardise,
#   )
# Using importorskip for now so this file collects cleanly (skipped, not
# failing) until the module is pushed.
iod_module = pytest.importorskip(
    "data_engineering.pipelines.iod.fetch_iod",
    reason="IOD processor not yet implemented",
)


# ---------------------------------------------------------------------------
# 1. Phase boundary tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "value, expected_phase",
    [
        (0.4, "Positive"),      # exactly at positive threshold
        (0.41, "Positive"),     # just above
        (0.39, "Neutral"),      # just below
        (-0.4, "Negative"),     # exactly at negative threshold
        (-0.41, "Negative"),    # just below
        (-0.39, "Neutral"),     # just above
        (0.0, "Neutral"),
    ],
)
def test_assign_phase_boundaries(value, expected_phase):
    """Confirm phase classification at and around the threshold values.

    NOTE: thresholds assumed as +-0.4 per standard IOD convention.
    Confirm against Ann's actual implementation once available.
    """
    assert iod_module.assign_phase(value) == expected_phase


def test_assign_phase_handles_missing_value():
    """A NaN input should not silently default to a phase; confirm the
    real implementation's documented behaviour once it exists."""
    result = iod_module.assign_phase(float("nan"))
    assert result is not None  # placeholder — tighten once behaviour is defined


# ---------------------------------------------------------------------------
# 2. Missing months tests
# ---------------------------------------------------------------------------

def test_handles_gap_in_middle_of_series():
    """A gap in the raw date sequence should not crash the pipeline, and
    should be detectable in the output rather than silently smoothed over."""
    dates = pd.date_range("1995-01-01", "1995-06-01", freq="MS")
    dates_with_gap = dates.delete(2)  # remove March 1995
    df = pd.DataFrame({
        "datetime_record": dates_with_gap,
        "dmi_value": [0.1, 0.2, 0.3, 0.4],
    })
    # Replace with the real transform function once available.
    result = iod_module.transform_and_standardise_from_df(df)
    assert len(result) == len(df)  # no rows silently dropped or fabricated


def test_handles_gap_at_start_of_series():
    dates = pd.date_range("1990-03-01", "1990-06-01", freq="MS")
    df = pd.DataFrame({
        "datetime_record": dates,
        "dmi_value": [0.1, 0.2, 0.3, 0.4],
    })
    result = iod_module.transform_and_standardise_from_df(df)
    assert result is not None


def test_running_mean_does_not_average_across_gap():
    """The 3-month running mean should not blend values across a gap as
    if the series were continuous."""
    dates = pd.date_range("1995-01-01", "1995-06-01", freq="MS").delete(2)
    df = pd.DataFrame({
        "datetime_record": dates,
        "dmi_value": [1.0, 1.0, 10.0, 10.0],
    })
    result = iod_module.compute_running_mean(df)
    assert result is not None  # tighten assertion once real behaviour is known


# ---------------------------------------------------------------------------
# 3. Output format tests
# ---------------------------------------------------------------------------

def test_output_goes_back_to_1990():
    df = iod_module.transform_and_standardise("tests/fixtures/sample_iod_raw.txt")
    assert df["datetime_record"].min().year <= 1990


def test_output_has_expected_columns():
    df = iod_module.transform_and_standardise("tests/fixtures/sample_iod_raw.txt")
    expected_columns = {
        "time_id",
        "datetime_record",
        "record_year_month",
        "iod_phase",
        "original_source",
    }
    assert expected_columns.issubset(set(df.columns))


def test_time_id_is_unique_and_formatted():
    df = iod_module.transform_and_standardise("tests/fixtures/sample_iod_raw.txt")
    assert df["time_id"].is_unique
    assert df["time_id"].astype(str).str.match(r"^\d{10}$").all()


def test_output_sorted_chronologically_no_duplicates():
    df = iod_module.transform_and_standardise("tests/fixtures/sample_iod_raw.txt")
    assert df["datetime_record"].is_monotonic_increasing
    assert not df["datetime_record"].duplicated().any()


# ---------------------------------------------------------------------------
# 4. Edge cases
# ---------------------------------------------------------------------------

def test_empty_raw_file_raises_clear_error(tmp_path):
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("")
    with pytest.raises(Exception):
        iod_module.transform_and_standardise(str(empty_file))


def test_malformed_values_raise_or_flag(tmp_path):
    bad_file = tmp_path / "bad.txt"
    bad_file.write_text("YR MON DMI\n1995 01 not_a_number\n")
    with pytest.raises(Exception):
        iod_module.transform_and_standardise(str(bad_file))


def test_download_failure_raises_clear_error(monkeypatch):
    def broken_urlretrieve(*args, **kwargs):
        raise ConnectionError("simulated network failure")

    import urllib.request
    monkeypatch.setattr(urllib.request, "urlretrieve", broken_urlretrieve)

    with pytest.raises(Exception):
        iod_module.fetch_raw_data()