# FireFusion — Synthetic Data Generator
### `generate_synthetic_data.py`

**Project:** FireFusion | AI Modelling Stream
**Version:** 2.0.0 | Sprint 2 | Trimester 1 | Deakin SIT Capstone

---

## Overview

`generate_synthetic_data.py` generates realistic synthetic bushfire training data for the FireFusion time series forecasting model. Each record represents one 500m × 500m Victorian grid cell fire event with a 4-day lead-up weather sequence, static terrain and fuel features, historical fire context, and derived target labels.

The data is physically grounded — weather variables are correlated, conditions intensify toward ignition day, and target labels are derived from a proxy fire danger index rather than randomly assigned. This makes the synthetic dataset suitable for:

- Model architecture prototyping before real data is fully assembled
- Testing ETL pipeline tensor conversion
- Validating that the training and inference schemas are correctly structured
- Benchmarking LSTM and Transformer architectures on a controlled dataset

---

## Requirements

```bash
pip install numpy pandas geopandas shapely
```

Python 3.10+ recommended. If you encounter NumPy 2.x compatibility issues:

```bash
pip install "numpy<2" geopandas shapely
```

---

## Quick Start

```bash
# Generate 200 records with default settings
python generate_synthetic_data.py

# Generate 1000 records with a fixed seed
python generate_synthetic_data.py --n 1000 --seed 42

# Save outputs to a specific directory
python generate_synthetic_data.py --n 500 --out ./data
```

---

## Arguments

| Argument | Type | Default | Description |
|---|---|---|---|
| `--n` | int | 200 | Number of synthetic fire event records to generate |
| `--seed` | int | 42 | Random seed for reproducibility. Use the same seed to regenerate identical datasets. |
| `--out` | str | `.` | Output directory for generated files |

---

## Outputs

Running the script produces two files:

### 1. `firefusion_training.geojson`
GeoJSON FeatureCollection containing all generated records. Each Feature includes:
- Point geometry (lon, lat within Victoria bounding box)
- Static terrain and fuel features
- Historical fire context
- 8-timestep weather sequence (4 days × 2 sub-daily steps)
- Target labels for model training

Use this file for model training and train/test splitting.

### 2. `firefusion_inference_sample.json`
Standard JSON containing the first 5 records formatted as model inference requests. Contains:
- Fixed tensor shape metadata
- Static features as ordered numeric arrays
- Temporal features as 8-step ordered arrays
- No geometry, no target labels

Use this file to test the model endpoint and validate tensor conversion logic.

---

## Tensor Shape

Both files conform to the fixed tensor shape required by LSTM and Transformer architectures:

| Parameter | Value |
|---|---|
| Grid resolution | 500m × 500m |
| Cell area | 25.0 ha |
| Temporal window | 4 days |
| Steps per day | 2 (06:00, 18:00) |
| Total timesteps | 8 |
| Static features | 8 |
| Temporal features | 10 |

---

## Feature Groups

### Static Features (8 — constant across timesteps)

| Feature | Source logic | Range |
|---|---|---|
| `elevation_m` | Increases toward north-east alpine corridor | 0 – 1986 m |
| `slope_deg` | Correlates with elevation | 0 – 45° |
| `aspect_deg` | North-facing aspects over-represented (35%) | 0 – 360° |
| `dist_to_water_m` | Lower in wetter east Victoria | 50 – 15,000 m |
| `veg_type_encoded` | Elevation-dependent (1=Grassland → 5=Rainforest) | 1 – 6 |
| `ndvi_at_ignition` | Inversely correlated with vegetation stress | −0.2 to 0.9 |
| `ndwi_at_ignition` | Canopy water — correlated with NDVI | −0.6 to 0.4 |
| `nbr_at_ignition` | Pre-fire fuel stress index | −0.3 to 0.7 |

### Temporal Features (10 — change at each of 8 timesteps)

| Feature | Physical behaviour in generated data |
|---|---|
| `max_temp_c` | Increases toward ignition day. Afternoon hotter than morning. |
| `wind_speed_kmh` | Intensifies toward day 0. Afternoon peak. |
| `wind_dir_deg` | North-westerly dominant (270–340°) — most dangerous in Victoria |
| `rel_humidity_pct` | Decreases toward ignition day. Inversely correlated with temperature. |
| `precipitation_mm` | Near-zero. Small chance of rain early in sequence only. |
| `evapotranspiration` | Scales with temperature and dryness. |
| `soil_moisture` | Depletes across the 4-day sequence as dry conditions persist. |
| `soil_temp_c` | Increases toward ignition day. Afternoon peak. |
| `days_since_rain` | Accumulates daily. Resets only if rain occurs. |
| `years_since_last_fire` | Constant across timesteps — contextual fuel accumulation feature. |

### Target Labels (training file only)

| Label | Derivation |
|---|---|
| `severity_class` (1–5) | Derived from proxy FFDI score combining wind, temperature, humidity, soil moisture, slope and vegetation stress |
| `area_ha_burned` | Scales with severity class and fuel load (years since last fire) using log-normal distribution |
| `rate_of_spread_ha_per_day` | Wind and slope dominated regression target |

---

## Physical Realism Design

The generator enforces the following physical correlations:

**Weather intensification** — conditions build realistically toward ignition day. Day -3 is moderately hot and dry. Day 0 at 18:00 represents peak fire danger conditions.

**Diurnal cycle** — afternoon (18:00) is always hotter, drier and windier than morning (06:00), reflecting the real Victorian fire weather pattern where fires most commonly escape control in the mid-to-late afternoon.

**Soil moisture depletion** — soil moisture decreases day by day across the 4-day window as the dry spell persists, reflecting the real-world drying of fine surface fuels.

**Vegetation stress correlation** — NDVI, NDWI and NBR are generated from a shared stress parameter, ensuring they are physically consistent with each other and with the vegetation type.

**Target label derivation** — severity is not randomly assigned. It is computed from a proxy FFDI score:

```
FFDI_proxy = (temp × 0.8) + (wind × 0.4) + ((100 − humidity) × 0.3)
             − (soil_moisture × 20) + (slope × 0.5) + (stress × 15)

Class 1: FFDI < 20
Class 2: FFDI 20–40
Class 3: FFDI 40–60
Class 4: FFDI 60–85
Class 5: FFDI > 85
```

---

## Loading the Training Data

```python
import geopandas as gpd
import pandas as pd
import json

# Load training GeoJSON
gdf = gpd.read_file("firefusion_training.geojson")
print(f"Records: {len(gdf)}")
print(gdf.columns.tolist())

# Extract target labels into a flat dataframe
labels = pd.json_normalize(
    gdf["properties"].apply(lambda x: x["target_labels"])
    if "properties" in gdf.columns
    else [json.loads(r) for r in gdf.to_json(show_bbox=False)["features"]]
)
print(labels.head())
```

---

## Converting to Model Tensors

```python
import json
import numpy as np

with open("firefusion_inference_sample.json") as f:
    data = json.load(f)

shape = data["tensor_shape"]  # timesteps=8, static=8, temporal=10

for cell in data["cells"]:
    # Static tensor: shape (8,)
    static = np.array(cell["static_features"]["values"], dtype=np.float32)

    # Temporal tensor: shape (8, 10)
    temporal = np.array(
        [step["values"] for step in cell["temporal_features"]["timesteps"]],
        dtype=np.float32
    )

    print(f"Cell: {cell['cell_id']}")
    print(f"  Static shape:   {static.shape}")
    print(f"  Temporal shape: {temporal.shape}")
```

---

## Train / Test Split

```python
import geopandas as gpd
from sklearn.model_selection import train_test_split

gdf = gpd.read_file("firefusion_training.geojson")

train, test = train_test_split(gdf, test_size=0.2, random_state=42)
print(f"Train: {len(train)}  Test: {len(test)}")

train.to_file("firefusion_train_split.geojson", driver="GeoJSON")
test.to_file("firefusion_test_split.geojson", driver="GeoJSON")
```

---

## Expected Output Summary

Running with `--n 200 --seed 42`:

```
Generating 200 synthetic fire records (seed=42)...
Saved → firefusion_training.geojson
Saved → firefusion_inference_sample.json

=======================================================
SYNTHETIC DATASET SUMMARY  (200 records)
=======================================================

Severity class distribution:
  Class 1:      0 (0.0%)
  Class 2:      0 (0.0%)
  Class 3: █    9 (4.5%)
  Class 4: ████████████████████████  123 (61.5%)
  Class 5: █████████████   68 (34.0%)

Area burned (ha):
  Min:             30.3
  Median:        1584.8
  Max:          44187.2

Rate of spread (ha/day):
  Min:              1.0
  Median:          35.8
  Max:            104.4

Ignition-day peak conditions (day 0, 18:00):
  Avg temp:   37.9 °C
  Avg wind:   45.0 km/h
=======================================================
```

The high proportion of class 4–5 events is expected and realistic — low-severity fires rarely grow large enough to become historical fire records in the Victorian dataset.

---

## Limitations

- Terrain and fuel features are spatially approximated — real DEM and GEE extractions will replace these in the production pipeline
- Vegetation type is elevation-based rather than from actual land cover data
- NDVI, NDWI and NBR are synthetically correlated but not derived from real satellite imagery
- Target labels approximate fire behaviour — the production model will be validated against FESM ground truth labels

---

## File Structure

```
firefusion/
├── generate_synthetic_data.py       # This script
├── firefusion_training.geojson      # Generated training data
├── firefusion_inference_sample.json # Generated inference sample (5 records)
└── SYNTHETIC_DATA_USAGE.md          # This file
```

---

*FireFusion — InnovAIte | Deakin University SIT Capstone 2025*