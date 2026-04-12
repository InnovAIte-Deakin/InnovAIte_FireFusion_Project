# FireFusion — Output Schema Reference

**AI Modelling Stream · Sprint 1 · v0.3**

---

## Overview

The model returns a GeoJSON `FeatureCollection`. Each `Feature` represents one grid cell at a given forecast timestep. The frontend dashboard renders this directly as a fire risk map. This document lists every field in the response, its source, and what each consumer (dashboard, operations, model validation, alerting, API) uses it for.

---

## Full Response Schema

> Strip the `_meta` block before sending to the frontend dashboard.

```json
{
  "type": "FeatureCollection",

  "metadata": {
    "model_version":      "0.3.0",
    "generated_at":       "2024-01-15T14:05:00Z",
    "forecast_horizon_h": 24,
    "grid_resolution_m":  500,
    "bbox":               [140.9, -37.5, 147.2, -34.1],
    "crs":                "EPSG:4326"
  },

  "features": [{
    "type": "Feature",
    "geometry": {
      "type":        "Polygon",
      "coordinates": [[...]]         
    },
    "properties": {

      "severity_class":        4,      
      "area_ha_burned":        4375.0, 
      "rate_of_spread_ha_day": 546.9,  
      "rate_of_spread_mpm":    85,     

      "ignition_prob_pct":     78.4,   

      "confidence": {
        "severity_class_prob": 0.81    
      },

      "at_risk_facilities": [{
        "facility_name":  "Toolangi Primary School",
        "facility_type":  "school",
        "risk_category":  "HIGH",
        "distance_m":     320
      }],

      "_meta": {
        "conversion_note":       "rate_mpm = (ha_day x 10000) / (front_width_m x 1440)",
        "assumed_front_width_m": 500
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

Lets the frontend render cell polygons at the correct scale without hardcoding a value. Also critical for the rate-of-spread conversion — the assumed fire front width should match this value.

> **e.g.** `grid_resolution_m=500` → draw 500 × 500 m polygons. Change to 1000 later, nothing else breaks.

---

### `severity_class` · int 1–5 · `Model output`

Primary colour-coding variable for the map heatmap (1 = low risk, 5 = catastrophic). Drives automated alert thresholds — class ≥ 4 triggers emergency broadcast. Directly comparable to FESM ground truth for model validation without any conversion.

> **e.g.** class 5 → dark red on map + state-level emergency alert triggered.

---

### `area_ha_burned` · float, ha · `Model output`

Quantifies the expected damage footprint. Used by incident commanders to pre-position resources. On the dashboard, drives the "estimated area at risk" summary stat. Also the primary regression target for model error metrics (MAE, RMSE).

> **e.g.** `area_ha_burned > 1000` across 3+ adjacent cells → auto-escalate to state-level response.

---

### `rate_of_spread_ha_day` · float, ha/day · `Model output`

Direct model output in training-label units. Used to compute model accuracy against historical fire records. Also useful for incident planning — how fast the fire boundary is expected to expand over 24 hours.

> **e.g.** Predicted 546 ha/day; actual spread 510 ha/day → 7% error, within acceptable range.

---

### `rate_of_spread_mpm` · float, m/min · `Derived`

Operationally useful unit for evacuation planning. Incident commanders think in metres-per-minute, not hectares-per-day. Used to calculate how many minutes before a fire front reaches a community. See [Rate-of-spread unit conversion](#rate-of-spread-unit-conversion) for the derivation formula.

> **e.g.** 85 m/min × 2 km distance = 24 min lead time → trigger evacuation order now.

---

### `ignition_prob_pct` · float, 0–100% · `Derived`

Continuous heatmap colouring for cells where fire has not yet started. Shows the risk surface across the map. Defined as softmax `P(severity_class ≥ 1)` from the classification head. Alert threshold: prob > 70% triggers pre-emptive resource pre-positioning.

> **e.g.** Cell shows orange hue at 65% probability. Crews pre-positioned before ignition detected.

---

### `confidence.severity_class_prob` · float, 0–1 · `Derived`

Flags uncertain predictions on the map — cells with high severity but low confidence get a visual indicator (hatching, reduced opacity) so operators do not act on a shaky prediction. Also tracked over time as a model health metric: if mean confidence drops, the model may be encountering out-of-distribution weather conditions.

> **e.g.** `severity_class=5` but `class_prob=0.51` → dashboard adds warning badge, operator prompted to verify.

---

### `at_risk_facilities[]` · array · `Spatial join`

Drives the community impact layer on the dashboard — schools, hospitals, and aged care facilities highlighted within high-risk cells. Triggers targeted alerts to facility managers. `facility_type` allows filtering by category; `distance_m` prioritises notification order.

Sub-fields:

| Sub-field | Type | Description |
|---|---|---|
| `facility_name` | string | Name of the at-risk facility |
| `facility_type` | string | Category: `school`, `hospital`, `aged_care`, etc. |
| `risk_category` | string | `LOW`, `MEDIUM`, `HIGH` — derived from cell severity and distance |
| `distance_m` | int, metres | Distance from facility to cell boundary |

> **e.g.** School 320 m from class-4 cell → auto-notify principal and local council.

---

### `_meta` · object · `Internal`

Records assumptions baked into derived fields so they are auditable and changeable. The `assumed_front_width_m` used to convert ha/day to m/min lives here. **Strip this block before sending the response to the frontend** — for inference pipeline and backend logs only.

> **e.g.** Update `assumed_front_width_m` from 500 to 300 → `rate_of_spread_mpm` recalculated, no schema change needed.

---

## Confidence Fields — Implementation Note

The `confidence` block requires a design decision before sprint 2. Three options:

**1. Quantile regression** — train three output heads (10th, 50th, 90th percentile). Adds training complexity but intervals are calibrated.

**2. MC dropout** — run inference N times with dropout active, take the distribution. No training change needed; higher inference cost.

**3. Conformal prediction** — wrap the existing model output with a post-hoc calibration layer on a held-out set. Easiest to retrofit; intervals are statistically valid.

---

## Rate-of-Spread Unit Conversion

The formula used to derive `rate_of_spread_mpm` from the model's `rate_of_spread_ha_day` output:

```
rate_of_spread_mpm = (rate_of_spread_ha_day × 10,000) / (assumed_front_width_m × 1,440)

Where:
  10,000               = hectares to square metres
  1,440                = minutes per day
  assumed_front_width_m = stored in _meta (default: 500 m = grid_resolution_m)


