# Data Cleaning & Preprocessing

General-purpose preprocessing module for the FireFusion AI Modelling pipeline.
Designed to be reusable across different datasets — just swap in a new DataFrame and schema.

## Location

```
ai-modelling/src/data/preprocessing.py
ai-modelling/src/data/transforms.py
```

## Requirements

Install from the project root:

```bash
pip install -r ai-modelling/requirements.txt
```

| Package | Version |
|---|---|
| `pandas` | >= 2.0.0 |
| `numpy` | >= 1.24.0 |
| `pytest` | >= 8.0.0 (testing only) |

---

## Quick Start

```python
import pandas as pd
from src.data import DataCleaner

df = pd.read_csv("your_dataset.csv")

schema = {
    "temperature": "float",
    "humidity":    "float",
    "timestamp":   "datetime",
    "station_id":  "int",
    "city":        "str",
    "is_active":   "bool",
}

cleaner = DataCleaner(df, schema=schema)
cleaned_df = cleaner.clean()
print(cleaner.report())
```

---

## Supported Data Types

| Type string | Aliases | Result dtype |
|---|---|---|
| `"int"` | `"integer"` | `int64` |
| `"float"` | `"double"` | `float64` |
| `"str"` | `"string"` | `object` |
| `"bool"` | `"boolean"` | `bool` |
| `"datetime"` | `"date"` | `datetime64` |
| `"timedelta"` | — | `timedelta64` |
| `"category"` | `"categorical"` | `category` |

> **Note:** Columns listed in the schema that do not exist in the DataFrame are skipped with a warning in the report — no exception is raised.

---

## API Reference

### `DataCleaner(df, schema=None)`

| Parameter | Type | Description |
|---|---|---|
| `df` | `pd.DataFrame` | Raw input DataFrame |
| `schema` | `dict[str, str]` | Column-to-dtype mapping for type casting. Optional. |

---

### `.remove_missing(strategy, fill_value, subset)`

Handles missing (NaN) values.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `strategy` | `"drop"` \| `"fill"` | `"drop"` | Drop rows with NaN, or fill them |
| `fill_value` | scalar or dict | `None` | Required when `strategy="fill"`. Pass a dict to fill different columns with different values |
| `subset` | `list[str]` | `None` | Only check these columns for NaN. Defaults to all columns |

```python
# Drop any row that has a NaN
cleaner.remove_missing()

# Fill all NaN with 0
cleaner.remove_missing(strategy="fill", fill_value=0)

# Fill NaN per column
cleaner.remove_missing(strategy="fill", fill_value={"temperature": -1.0, "city": "Unknown"})

# Only drop rows where 'temperature' is NaN
cleaner.remove_missing(strategy="drop", subset=["temperature"])
```

---

### `.remove_duplicates(subset, keep)`

Removes duplicate rows.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `subset` | `list[str]` | `None` | Columns to check for duplicates. Defaults to all columns |
| `keep` | `"first"` \| `"last"` \| `False` | `"first"` | Which duplicate to keep. `False` drops all |

```python
# Remove exact duplicate rows
cleaner.remove_duplicates()

# Deduplicate based on specific columns
cleaner.remove_duplicates(subset=["station_id", "timestamp"])
```

---

### `.cast_types()`

Casts columns to the types defined in `schema`. Skips columns not present in the DataFrame.

```python
schema = {"temperature": "float", "timestamp": "datetime"}
cleaner = DataCleaner(df, schema=schema)
cleaner.cast_types()
```

---

### `.clean(missing_strategy, fill_value, missing_subset, dup_subset)`

Runs the full pipeline in order:
1. `remove_missing`
2. `remove_duplicates`
3. `cast_types`

Returns the cleaned `pd.DataFrame`.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `missing_strategy` | `"drop"` \| `"fill"` | `"drop"` | Strategy for missing values |
| `fill_value` | scalar or dict | `None` | Used when `missing_strategy="fill"` |
| `missing_subset` | `list[str]` | `None` | Columns to check for missing values |
| `dup_subset` | `list[str]` | `None` | Columns to check for duplicates |

---

### `.report()`

Returns a human-readable summary string of all steps performed.

```
original: (1000, 6) → final: (987, 6) (13 rows removed)
[missing] dropped 10 row(s) with NaN (all columns)
[duplicates] removed 3 duplicate row(s)
[types] 'temperature' cast to float64
[types] 'humidity' cast to float64
[types] 'timestamp' cast to datetime
[types] 'station_id' cast to int64
```

---

## Adding a New Dataset

When integrating a new dataset, define a schema dict mapping each column name to its expected type.
Only the columns you want to cast need to be listed — unlisted columns are left as-is.

```python
# Example: soil moisture dataset
schema = {
    "latitude":               "float",
    "longitude":              "float",
    "surface_soil_moisture":  "float",
    "rootzone_soil_moisture": "float",
    "timestamp":              "datetime",
}

cleaner = DataCleaner(df, schema=schema)
cleaned_df = cleaner.clean()
```

---

## Running Tests

```bash
pytest ai-modelling/tests/test_preprocessing.py -v
```

## Environmental Data Transforms

Use `transforms.py` for time-aware interpolation and model-oriented scaling.
These are kept separate from `DataCleaner` so generic cleaning stays independent
from temporal logic and training transforms.

### `interpolate_time_series(df, time_col, cols, group_cols, method, limit_direction)`

Interpolates selected columns after sorting by time. If `group_cols` is supplied,
each group is interpolated independently.

```python
from src.data import interpolate_time_series

weather_df = interpolate_time_series(
    df,
    time_col="fire_start_date",
    group_cols=["cell_id"],
    cols=["soil_moisture", "precipitation_mm"],
    method="linear",
)
```

Typical use:
- `soil_moisture`: linear interpolation over time
- `precipitation_mm`: forward fill may be more appropriate in some datasets, but
  that should be decided at the pipeline level

### `scale_features(df, cols, method, suffix)`

Creates scaled copies of selected numeric columns and returns scaling parameters.

```python
from src.data import scale_features

scaled_df, params = scale_features(
    df,
    cols=["max_temp_c", "elevation_m"],
    method="standard",
)
```

Supported methods:
- `"standard"`: `(x - mean) / std`
- `"minmax"`: `(x - min) / (max - min)`

Recommended usage:
- `minmax` for bounded features such as `ndvi_at_ignition`
- `standard` for broader continuous features such as `max_temp_c`
