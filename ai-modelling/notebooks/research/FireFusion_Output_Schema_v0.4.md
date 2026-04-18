# FireFusion — Output Schema Reference

**AI Modelling Stream · Sprint 1 · v0.4**

---

## Overview

The model returns a GeoJSON `FeatureCollection`. Each `Feature` represents one grid cell at a given forecast timestep. The frontend dashboard renders this directly as a fire risk map. This document lists every field in the response, its source, and what each consumer (dashboard, operations, model validation, alerting, API) uses it for.

The spatial grid covers Victoria at **5 km × 5 km** resolution (~900 cells total). Predictions are issued at **12-hourly intervals** — a sliding-window sequential LSTM learns temporal patterns across time windows and predicts the next interval. Input and output schemas will be adjusted in step with any architecture changes as the project matures.

---

## Full Response Schema

> Strip the `_meta` block before sending to the frontend dashboard.

```json
{
  "type": "FeatureCollection",

  "metadata": {
    "model_version":       "0.4.0",
    "generated_at":        "2024-01-15T14:05:00Z",
    "forecast_horizon_h":  12,
    "forecast_interval_h": 12,
    "grid_resolution_m":   5000,
    "total_cells":         900,
    "bbox":                [140.9, -37.5, 147.2, -34.1],
    "crs":                 "EPSG:4326",

    "at_risk_facilities": [{
      "facility_name": "Toolangi Primary School",
      "facility_type": "school",
      "cell_id":       "grid_-37.10_145.40",
      "distance_m":    320
    }]
  },

  "features": [{
    "type": "Feature",
    "geometry": {
      "type":        "Polygon",
      "coordinates": [[...]]
    },
    "properties": {

      "cell_id":    "grid_-37.10_145.40",
      "timestamp":  "2024-01-15T14:00:00Z",
      "interval_h": 12,

      "severity_class": 4,

      "confidence": {
        "severity_class_prob": 0.81
      },

      "environment": {
        "temperature_c":         34.2,
        "relative_humidity_pct": 11.0,
        "wind_speed_kmh":        62.0,
        "wind_direction_deg":    315,
        "ffdi":                  78.4,
        "fuel_moisture_pct":     4.1
      },

      "_meta": {
        "model_version": "0.4.0",
        "cell_id_note":  "Encoded as lat_lng of cell centroid to 2 decimal places",
        "interval_note": "12-hourly chosen over daily (loses temporal detail) and hourly (too resource-heavy)"
      }

    }
  }]
}
```

---

## Field Reference

Source tag definitions:

| Tag | Meaning |
|---|---|
| `Model output` | Direct training target — value produced by the model head |
| `Derived` | Computed post-inference from a model output |
| `Spatial join` | Not a model prediction — joined at query time from external data |
| `Internal` | Backend / pipeline only — strip before sending to frontend |

---

### `grid_resolution_m` · int, metres · `Reference` (metadata)

Lets the frontend render cell polygons at the correct scale without hardcoding a value. Grid covers Victoria at 5 km × 5 km (~900 cells), balancing spatial resolution against computational cost.

> **e.g.** `grid_resolution_m=5000` → draw 5 km × 5 km polygons. Change to 10000 later, nothing else breaks.

---

### `forecast_interval_h` · int, hours · `Reference` (metadata)

Records the temporal frequency of the model's predictions. Set to **12** — coarser than hourly (too resource-heavy) and finer than daily (loses too much temporal detail for the sliding-window LSTM). All input datasets must be aligned to this interval before training.

> **e.g.** Two predictions per day: 00:00 UTC and 12:00 UTC. Model learns patterns across the rolling window and predicts the next 12-hour state.

---

### `cell_id` · string · `Reference`

Primary key for each grid cell. Encoded as the lat/lng of the cell centroid to 2 decimal places (e.g. `"grid_-37.10_145.40"`). Allows the backend to efficiently map time-series data from the LSTM back to a specific spatial coordinate without recalculating geometry on every request. Also used to join `at_risk_facilities` records in the metadata back to the feature that contains them.

> **e.g.** LSTM produces a 12-hourly sequence keyed by `cell_id`. Backend resolves geometry once at query time rather than per timestep.

---

### `timestamp` · string, ISO 8601 · `Reference`

The start of the 12-hour forecast window this feature represents. Combined with `cell_id`, forms a composite unique key across the full time-series output.

> **e.g.** `"2024-01-15T14:00:00Z"` → this feature covers the window 14:00–02:00 UTC.

---

### `severity_class` · int 1–5 · `Model output`

Primary colour-coding variable for the map heatmap (1 = low risk, 5 = catastrophic). Drives automated alert thresholds — class ≥ 4 triggers emergency broadcast. Directly comparable to FESM ground truth for model validation without any conversion. Target variable derived from historical fire occurrence and severity mapped to each 5 km cell.

> **e.g.** class 5 → dark red on map + state-level emergency alert triggered.

---

### `confidence.severity_class_prob` · float, 0–1 · `Derived`

Flags uncertain predictions on the map — cells with high severity but low confidence get a visual indicator (hatching, reduced opacity) so operators do not act on a shaky prediction. Also tracked over time as a model health metric: if mean confidence drops, the model may be encountering out-of-distribution weather conditions.

> **e.g.** `severity_class=5` but `class_prob=0.51` → dashboard adds warning badge, operator prompted to verify.

---

### `environment` · object · `Model output`

Raw predicted environmental state for the cell at the forecast horizon. The model is trained on historical fire data merged with environmental and atmospheric inputs (weather, temperature, climate) — providing these values alongside `severity_class` makes the prediction explainable. Sub-fields:

| Sub-field | Type | Description |
|---|---|---|
| `temperature_c` | float, °C | Predicted air temperature |
| `relative_humidity_pct` | float, 0–100 | Predicted relative humidity |
| `wind_speed_kmh` | float, km/h | Predicted wind speed |
| `wind_direction_deg` | float, 0–360 | Predicted wind direction (meteorological) |
| `ffdi` | float | Forest Fire Danger Index — composite fire weather score (Bureau of Meteorology) |
| `fuel_moisture_pct` | float, % | Predicted fine fuel moisture content |

> **e.g.** `temperature_c=34`, `relative_humidity_pct=11`, `ffdi=78` → operator can trace the high severity rating back to extreme heat and low humidity rather than treating the class label as a black-box output.

---

### `at_risk_facilities[]` · array · `Spatial join` (metadata)

Static contextual data — facilities do not change between forecast runs. Placed in the top-level `metadata` block to keep `features` focused on dynamic model predictions. Each record references its parent cell via `cell_id`. `risk_category` has been removed; severity is fully expressed by `severity_class` on the linked cell.

Sub-fields:

| Sub-field | Type | Description |
|---|---|---|
| `facility_name` | string | Name of the at-risk facility |
| `facility_type` | string | Category: `school`, `hospital`, `aged_care`, etc. |
| `cell_id` | string | Links facility to its parent grid cell |
| `distance_m` | int, metres | Distance from facility to cell boundary — used to prioritise notification order |

> **e.g.** School 320 m from cell `grid_-37.10_145.40` → backend looks up `severity_class` for that `cell_id` and auto-notifies principal if class ≥ 4.

---

### `_meta` · object · `Internal`

Records pipeline assumptions for auditability. **Strip this block before sending the response to the frontend.**

> **e.g.** `interval_note` documents why 12-hourly was chosen so future engineers don't revisit the decision without context.

---

## Confidence Fields — Implementation Note

The `confidence` block requires a design decision before sprint 2. Three options:

**1. Quantile regression** — train three output heads (10th, 50th, 90th percentile). Adds training complexity but intervals are calibrated.

**2. MC dropout** — run inference N times with dropout active, take the distribution. No training change needed; higher inference cost.

**3. Conformal prediction** — wrap the existing model output with a post-hoc calibration layer on a held-out set. Easiest to retrofit; intervals are statistically valid.
