"""
Unit tests for src/data/preprocessing.py
Dataset: FireFusion bushfire prediction feature schema

Run with: pytest ai-modelling/tests/test_preprocessing.py -v
"""

import numpy as np
import pandas as pd
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data import DataCleaner, interpolate_time_series, scale_features


# ---------------------------------------------------------------------------
# Schema — matches the FireFusion feature specification
# ---------------------------------------------------------------------------

FIRE_SCHEMA = {
    "cell_id":                  "str",
    "suburb":                   "str",
    "elevation_m":              "float",
    "slope_deg":                "float",
    "aspect_deg":               "float",
    "dist_to_water_m":          "float",
    "veg_type":                 "str",
    "ndvi_at_ignition":         "float",
    "ndwi_at_ignition":         "float",
    "nbr_at_ignition":          "float",
    "dist_to_powerlines_m":     "float",
    "fire_start_date":          "datetime",
    "fire_end_date":            "datetime",
    "severity":                 "int",
    "area_ha_burned":           "float",
    "day":                      "int",
    "max_temp_c":               "float",
    "wind_speed_kmh":           "float",
    "wind_dir_deg":             "float",
    "rel_humidity_pct":         "float",
    "precipitation_mm":         "float",
    "evapotranspiration":       "float",
    "soil_moisture":            "float",
    "soil_temp_c":              "float",
    "days_since_rain":          "int",
    "severity_class":           "int",
    "rate_of_spread_ha_per_day":"float",
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def fire_df():
    """
    Small representative sample of the bushfire dataset.
    Row 1 has NaN in weather columns.
    Row 2 has NaN in terrain columns.
    Rows 3 and 4 are exact duplicates (same cell_id + fire_start_date).
    Numeric columns are stored as strings to allow cast_types testing.
    """
    return pd.DataFrame({
        "cell_id":                  ["C001", "C002", "C003", "C004", "C004"],
        "suburb":                   ["Kinglake", "Marysville", "Healesville", "Warburton", "Warburton"],
        "elevation_m":              ["312.5", "480.0", np.nan, "210.0", "210.0"],
        "slope_deg":                ["18.3", "22.1", "9.5", "14.7", "14.7"],
        "aspect_deg":               ["45.0", "180.0", "270.0", "90.0", "90.0"],
        "dist_to_water_m":          ["1200.0", "300.0", "850.0", "500.0", "500.0"],
        "veg_type":                 ["Wet Sclerophyll", "Dry Sclerophyll", "Grassland", "Wet Sclerophyll", "Wet Sclerophyll"],
        "ndvi_at_ignition":         ["0.65", "0.42", "0.21", "0.58", "0.58"],
        "ndwi_at_ignition":         ["0.30", "0.15", "-0.10", "0.25", "0.25"],
        "nbr_at_ignition":          ["0.55", "0.38", "0.12", "0.47", "0.47"],
        "dist_to_powerlines_m":     ["2500.0", "800.0", "1500.0", "3000.0", "3000.0"],
        "fire_start_date":          ["2009-02-07", "2009-02-07", "2019-11-21", "2020-01-04", "2020-01-04"],
        "fire_end_date":            ["2009-02-14", "2009-02-20", "2019-12-10", "2020-01-25", "2020-01-25"],
        "severity":                 ["5", "4", "2", "3", "3"],
        "area_ha_burned":           ["12500.0", "8400.0", "320.0", "1750.0", "1750.0"],
        "day":                      ["0", "-3", "-6", "0", "0"],
        "max_temp_c":               ["46.4", np.nan, "38.1", "41.2", "41.2"],
        "wind_speed_kmh":           ["95.0", np.nan, "55.0", "72.0", "72.0"],
        "wind_dir_deg":             ["315.0", np.nan, "270.0", "290.0", "290.0"],
        "rel_humidity_pct":         ["8.0",  np.nan, "22.0", "14.0", "14.0"],
        "precipitation_mm":         ["0.0",  np.nan, "1.2", "0.0", "0.0"],
        "evapotranspiration":       ["12.5", np.nan, "7.3", "9.8", "9.8"],
        "soil_moisture":            ["0.04", np.nan, "0.12", "0.07", "0.07"],
        "soil_temp_c":              ["38.0", np.nan, "29.0", "33.5", "33.5"],
        "days_since_rain":          ["21", "14", "8", "18", "18"],
        "severity_class":           ["5", "4", "2", "3", "3"],
        "rate_of_spread_ha_per_day":["1785.7", "600.0", "14.5", "87.5", "87.5"],
    })


@pytest.fixture
def fire_df_clean(fire_df):
    """fire_df with NaN rows dropped, ready for type casting."""
    return fire_df.dropna().reset_index(drop=True)


# ---------------------------------------------------------------------------
# Missing value tests
# ---------------------------------------------------------------------------

class TestRemoveMissing:
    def test_drop_removes_nan_rows(self, fire_df):
        cleaner = DataCleaner(fire_df)
        cleaner.remove_missing(strategy="drop")
        assert cleaner.df.isna().sum().sum() == 0

    def test_drop_correct_row_count(self, fire_df):
        # Row 1 (C002) has NaN in weather columns
        # Row 2 (C003) has NaN in elevation_m
        # Rows 3 and 4 are duplicates but complete — both survive drop
        cleaner = DataCleaner(fire_df)
        cleaner.remove_missing(strategy="drop")
        assert len(cleaner.df) == 3  # C001, C004 x2 (dup not removed yet)

    def test_fill_nan_scalar(self, fire_df):
        cleaner = DataCleaner(fire_df)
        cleaner.remove_missing(strategy="fill", fill_value=0)
        assert cleaner.df.isna().sum().sum() == 0

    def test_fill_nan_per_column(self, fire_df):
        fill = {"elevation_m": "0.0", "max_temp_c": "-999", "wind_speed_kmh": "-999"}
        cleaner = DataCleaner(fire_df)
        cleaner.remove_missing(strategy="fill", fill_value=fill)
        assert cleaner.df["elevation_m"].isna().sum() == 0
        assert cleaner.df["max_temp_c"].isna().sum() == 0
        assert cleaner.df.loc[1, "max_temp_c"] == "-999"

    def test_drop_subset_only_weather(self, fire_df):
        # Only drop rows missing weather columns — row 1 (C002) should be removed
        weather_cols = ["max_temp_c", "wind_speed_kmh", "rel_humidity_pct"]
        cleaner = DataCleaner(fire_df)
        cleaner.remove_missing(strategy="drop", subset=weather_cols)
        assert "C002" not in cleaner.df["cell_id"].values
        assert "C003" in cleaner.df["cell_id"].values  # C003 has NaN in elevation only

    def test_invalid_strategy_raises(self, fire_df):
        with pytest.raises(ValueError, match="Unknown strategy"):
            DataCleaner(fire_df).remove_missing(strategy="interpolate")

    def test_fill_without_value_raises(self, fire_df):
        with pytest.raises(ValueError, match="fill_value must be provided"):
            DataCleaner(fire_df).remove_missing(strategy="fill")


# ---------------------------------------------------------------------------
# Duplicate tests
# ---------------------------------------------------------------------------

class TestRemoveDuplicates:
    def test_removes_exact_duplicate_rows(self, fire_df):
        # Rows 3 and 4 (both C004) are exact duplicates
        cleaner = DataCleaner(fire_df)
        cleaner.remove_duplicates()
        assert cleaner.df["cell_id"].tolist().count("C004") == 1

    def test_dedup_on_cell_and_date(self, fire_df):
        cleaner = DataCleaner(fire_df)
        cleaner.remove_duplicates(subset=["cell_id", "fire_start_date"])
        assert len(cleaner.df[cleaner.df["cell_id"] == "C004"]) == 1

    def test_no_duplicates_unchanged(self, fire_df_clean):
        # fire_df_clean still has the C004 duplicate — drop it first
        df = fire_df_clean.drop_duplicates().reset_index(drop=True)
        before = len(df)
        cleaner = DataCleaner(df)
        cleaner.remove_duplicates()
        assert len(cleaner.df) == before


# ---------------------------------------------------------------------------
# Type casting tests
# ---------------------------------------------------------------------------

class TestCastTypes:
    def test_cast_float_columns(self, fire_df_clean):
        schema = {"elevation_m": "float", "slope_deg": "float", "ndvi_at_ignition": "float"}
        cleaner = DataCleaner(fire_df_clean, schema=schema)
        cleaner.cast_types()
        assert cleaner.df["elevation_m"].dtype == np.float64
        assert cleaner.df["slope_deg"].dtype == np.float64
        assert cleaner.df["ndvi_at_ignition"].dtype == np.float64

    def test_cast_int_columns(self, fire_df_clean):
        schema = {"severity": "int", "day": "int", "days_since_rain": "int", "severity_class": "int"}
        cleaner = DataCleaner(fire_df_clean, schema=schema)
        cleaner.cast_types()
        for col in schema:
            assert cleaner.df[col].dtype == np.int64

    def test_cast_str_columns(self, fire_df_clean):
        schema = {"cell_id": "str", "suburb": "str", "veg_type": "str"}
        cleaner = DataCleaner(fire_df_clean, schema=schema)
        cleaner.cast_types()
        for col in schema:
            assert cleaner.df[col].dtype == object

    def test_cast_datetime_columns(self, fire_df_clean):
        schema = {"fire_start_date": "datetime", "fire_end_date": "datetime"}
        cleaner = DataCleaner(fire_df_clean, schema=schema)
        cleaner.cast_types()
        assert pd.api.types.is_datetime64_any_dtype(cleaner.df["fire_start_date"])
        assert pd.api.types.is_datetime64_any_dtype(cleaner.df["fire_end_date"])

    def test_missing_column_logged_not_raised(self, fire_df_clean):
        schema = {"nonexistent_feature": "float"}
        cleaner = DataCleaner(fire_df_clean, schema=schema)
        cleaner.cast_types()
        assert any("not found" in entry for entry in cleaner._log)

    def test_no_schema_skips_casting(self, fire_df_clean):
        cleaner = DataCleaner(fire_df_clean)
        cleaner.cast_types()
        assert any("skipped" in entry for entry in cleaner._log)


# ---------------------------------------------------------------------------
# Environmental transform tests
# ---------------------------------------------------------------------------

class TestInterpolation:
    def test_interpolate_time_series_per_group(self):
        df = pd.DataFrame({
            "cell_id": ["A", "A", "A", "B", "B", "B"],
            "fire_start_date": [
                "2024-01-01", "2024-01-02", "2024-01-03",
                "2024-01-01", "2024-01-02", "2024-01-03",
            ],
            "soil_moisture": [0.10, np.nan, 0.30, 0.50, np.nan, 0.70],
        })

        result = interpolate_time_series(
            df,
            time_col="fire_start_date",
            group_cols=["cell_id"],
            cols=["soil_moisture"],
        )

        assert result.loc[result["cell_id"] == "A", "soil_moisture"].tolist() == [0.10, 0.20, 0.30]
        assert result.loc[result["cell_id"] == "B", "soil_moisture"].tolist() == [0.50, 0.60, 0.70]

    def test_missing_time_column_raises(self):
        df = pd.DataFrame({"soil_moisture": [0.1, np.nan, 0.3]})

        with pytest.raises(KeyError, match="time column"):
            interpolate_time_series(df, time_col="timestamp", cols=["soil_moisture"])


class TestScaling:
    def test_standard_scaling_creates_new_columns_and_params(self):
        df = pd.DataFrame({
            "max_temp_c": [30.0, 40.0, 50.0],
            "elevation_m": [100.0, 200.0, 300.0],
        })

        scaled_df, params = scale_features(df, ["max_temp_c", "elevation_m"], method="standard")

        assert "max_temp_c_standard" in scaled_df.columns
        assert "elevation_m_standard" in scaled_df.columns
        assert pytest.approx(float(scaled_df["max_temp_c_standard"].mean()), abs=1e-9) == 0.0
        assert params["max_temp_c"]["mean"] == 40.0

    def test_minmax_scaling_bounds_values_between_zero_and_one(self):
        df = pd.DataFrame({"ndvi_at_ignition": [-1.0, 0.0, 1.0]})

        scaled_df, params = scale_features(df, ["ndvi_at_ignition"], method="minmax")

        assert scaled_df["ndvi_at_ignition_minmax"].tolist() == [0.0, 0.5, 1.0]
        assert params["ndvi_at_ignition"] == {"min": -1.0, "max": 1.0}

    def test_invalid_scaling_method_raises(self):
        df = pd.DataFrame({"max_temp_c": [30.0, 40.0]})

        with pytest.raises(ValueError, match="method must"):
            scale_features(df, ["max_temp_c"], method="robust")


# ---------------------------------------------------------------------------
# Full pipeline test
# ---------------------------------------------------------------------------

class TestCleanPipeline:
    def test_full_clean_no_missing_no_duplicates(self, fire_df):
        cleaner = DataCleaner(fire_df, schema=FIRE_SCHEMA)
        result = cleaner.clean()

        assert result.isna().sum().sum() == 0
        assert result.duplicated().sum() == 0

    def test_full_clean_correct_dtypes(self, fire_df):
        cleaner = DataCleaner(fire_df, schema=FIRE_SCHEMA)
        result = cleaner.clean()

        assert result["elevation_m"].dtype == np.float64
        assert result["severity"].dtype == np.int64
        assert result["days_since_rain"].dtype == np.int64
        assert pd.api.types.is_datetime64_any_dtype(result["fire_start_date"])
        assert pd.api.types.is_datetime64_any_dtype(result["fire_end_date"])
        assert result["rate_of_spread_ha_per_day"].dtype == np.float64

    def test_full_clean_final_row_count(self, fire_df):
        # Row 1 (C002) dropped → NaN in weather; Row 2 (C003) dropped → NaN in elevation
        # Rows 3+4 (C004) are duplicates → keep one
        # Remaining: C001, C004 = 2 rows
        cleaner = DataCleaner(fire_df, schema=FIRE_SCHEMA)
        result = cleaner.clean()
        assert len(result) == 2

    def test_report_contains_summary(self, fire_df):
        cleaner = DataCleaner(fire_df, schema=FIRE_SCHEMA)
        cleaner.clean()
        report = cleaner.report()
        assert "original:" in report
        assert "final:" in report
        assert "[missing]" in report
        assert "[duplicates]" in report
        assert "[types]" in report
