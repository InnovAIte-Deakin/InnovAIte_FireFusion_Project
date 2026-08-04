# AI Modelling API Interface

## Table of Contents
1. Overview
2. Folder Structure
3. File Directory & Purpose
4. Architecture & Data Flow
5. Setup & Installation
6. API Endpoints
7. Testing Guide
8. Known Issues & Future Improvements
9. Contributing

## Overview

The **AI Modelling API** is a FastAPI-based REST service that exposes machine learning models for:
- **Misinformation Detection**: Binary classification of social media posts using DeBERTa v3-large
- **Bushfire Fire Prediction**: Spatiotemporal fire-occurrence probability per grid cell using a single ConvLSTM (5-D in, 5-D out)
- **Bushfire Risk Classification (deprecated)**: TCN classifier, retired by the single-ConvLSTM refactor

The API uses a **YAML-driven model registry** to manage checkpoints, scalers, and metadata, enabling easy addition of new models without code changes.

**Key Design Principles:**
- Separation of concerns (routers, inference, schemas, config)
- Stateless, pure inference functions
- GeoJSON-based I/O for spatial data
- Pydantic validation at API boundaries

## Folder Structure

```
api/
├── __init__.py                      # Package marker
├── README.md                        # This file
├── main.py                          # FastAPI app entrypoint + lifespan setup
├── model_loader.py                  # Model registry loader (YAML → checkpoint)
│
├── config/
│   └── models.yaml                  # Model registry (paths, metadata, kinds)
│
├── routers/
│   ├── __init__.py
│   ├── health.py                    # Health & readiness endpoints
│   └── predict.py                   # Inference endpoints (misinformation, bushfire)
│
├── inference/
│   ├── __init__.py
│   ├── misinformation.py            # DeBERTa inference adapter
│   ├── bushfire_forecaster.py       # ConvLSTM forecasting adapter
│   └── bushfire_classifier.py       # TCN classification adapter (deprecated)
│
├── schemas/
│   ├── bushfire.py                  # GeoJSON timeseries Pydantic schemas
│   └── misinformation.py            # Social post input/output schemas
│
├── examples/
│   ├── bushfire_input.geojson       # Sample forecast input (60 timesteps × 7 features)
│   └── misinfo_test.json            # Sample misinfo post
│
└── utils/
    └── geojson.py                   # Placeholder for geo utilities (empty)
```

## File Directory & Purpose

| Path | Type | Purpose |
|------|------|---------|
| main.py | Module | FastAPI app, lifespan (model loading at startup) |
| model_loader.py | Module | YAML-driven registry loader, checkpoint resolution |
| `config/models.yaml` | Config | Model registry with checkpoint paths & metadata |
| `routers/health.py` | Module | `GET /health`, `GET /ready` endpoints |
| `routers/predict.py` | Module | `POST /predict/*` endpoints for inference |
| `inference/misinformation.py` | Module | DeBERTa text classification logic |
| `inference/bushfire_forecaster.py` | Module | ConvLSTM time-series forecasting adapter |
| `inference/bushfire_classifier.py` | Module | TCN risk classification & orchestration — **deprecated** by the single-ConvLSTM refactor |
| `schemas/bushfire.py` | Module | Pydantic models for GeoJSON I/O validation |
| `schemas/misinformation.py` | Module | Pydantic models for post input/output |
| `examples/bushfire_input.geojson` | Data | Example forecast input payload |
| `examples/misinfo_test.json` | Data | Example misinfo post payload |
| `utils/geojson.py` | Module | Geo utilities (placeholder, empty) | ⏳ Future |

## Architecture & Data Flow

### System Diagram

[Insert architecture diagram here: FastAPI app → Routers → Inference Adapters → Models]

### Request Flow (Example: Bushfire Forecast)

```
1. Client POST /predict/bushfire/forecast
   ↓
2. FastAPI validates input via ForecastRequest (Pydantic)
   ↓
3. predict.py route handler:
   - Resolves model_id from query param (or uses default)
   - Fetches LoadedModel bundle from _REGISTRY
   - Validates model kind == "bushfire_forecaster"
   ↓
4. bushfire_forecaster.py:predict_bushfire_forecast():
   - Validates GeoJSON structure
   - Extracts observations (timeseries per Feature)
   - Pads/truncates to input_steps (default 60)
   - Builds gridded or batch tensor
   - Applies scaler
   - Runs bundle.model.predict() -> 5-D fire probability grid
   - Postprocesses to GeoJSON FeatureCollection
   ↓
5. FastAPI serializes response to JSON
   ↓
6. Client receives FeatureCollection with fire_probability per cell
```

## API Endpoints

### Health & Status

#### `GET /health`
Liveness probe (always returns 200).

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{"status": "ok"}
```

---

#### `GET /ready`
Readiness probe (checks if models loaded successfully).

```bash
curl http://localhost:8000/ready
```

**Response:**
```json
{
  "ready": true,
  "load_errors": []
}
```

If `ready=false` or `load_errors` is non-empty, models failed to load—check server logs.

---

#### `GET /predict/models`
List all loaded models and their metadata.

```bash
curl http://localhost:8000/predict/models
```

**Response:**
```json
{
  "models": [
    {
      "model_id": "misinfo-deberta",
      "domain": "misinformation",
      "kind": "deberta_sequence_binary",
      "checkpoint": "/path/to/deberta"
    },
    {
      "model_id": "bushfire-forecaster-v1",
      "domain": "bushfire",
      "kind": "bushfire_forecaster",
      "checkpoint": "/path/to/convlstm_forecaster.pth"
    },
    {
      "model_id": "bushfire-classifier-v1",
      "domain": "bushfire",
      "kind": "bushfire_classifier",
      "checkpoint": "/path/to/tcn_classifier.pth"
    }
  ]
}
```

---

### Misinformation Detection

#### `POST /predict/misinformation`
Classify a single social media post for misinformation.

**Request Body:**
```json
{
  "id": "post-1",
  "author_name": "Alice",
  "platform": "twitter",
  "content": "Vaccines contain microchips inserted via 5G networks",
  "share_count": 12,
  "ts": null,
  "post_url": ""
}
```

**Query Parameters:**
- `model_id` (optional): Specific model to use (defaults to first misinformation model)

**Response:**
```json
{
  "model_id": "misinfo-deberta",
  "domain": "misinformation",
  "id": "post-1",
  "author_name": "Alice",
  "platform": "twitter",
  "content": "Vaccines contain microchips...",
  "label_id": 1,
  "label": "misinformation",
  "confidence": 0.92,
  "probabilities": {
    "non_misinformation": 0.08,
    "misinformation": 0.92
  },
  "risk_score": 0.92,
  "severity": "HIGH",
  "checkpoint": "/path/to/deberta"
}
```

**Severity Mapping:**
- `risk_score < 0.6` → `LOW`
- `0.6 ≤ risk_score < 0.75` → `MEDIUM`
- `0.75 ≤ risk_score < 0.9` → `HIGH`
- `risk_score ≥ 0.9` → `CRITICAL`

---

### Bushfire Fire Prediction

#### `POST /predict/bushfire/forecast`
Predict fire-occurrence probability per grid cell for the next timestep (`horizon = 1`).

**Request Body (GeoJSON FeatureCollection):**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [144.9631, -37.8136]
      },
      "properties": {
        "id": "cell-001",
        "grid_row": 3,
        "grid_col": 7,
        "observations": [
          [20.5, 15.2, 100.3, 50.1, 22.1, 2.5, 1.3],
          [21.0, 15.5, 105.2, 52.0, 23.0, 2.4, 1.2],
          ...
        ]
      }
    }
  ]
}
```

**Input properties:**

| Property | Required | Description |
|---|---|---|
| `observations` | yes | `[seq_len, n_features]` array (e.g. 60 timesteps × 7 features). Padded/truncated to the checkpoint's `input_steps`. |
| `id` | no | Cell identifier, echoed in the response and used to join forecaster → classifier output. |
| `timestamps` | no | ISO-8601 timestamps, must be the same length as `observations`. |
| `grid_row`, `grid_col` | no | Position of the cell in the model grid. Must be supplied **together**. |

**Channel order** (`feature_names`, defaults to `DEFAULT_FEATURE_NAMES`):
`[skin_temperature_c, soil_temperature_level_1_c, surface_solar_radiation_downwards, surface_thermal_radiation_downwards, temperature_2m_c, u_component_of_wind_10m, v_component_of_wind_10m]`

**Gridded vs batched input:** the ConvLSTM is spatiotemporal — it expects
`[batch, seq_len, height, width, n_features]`. When every cell carries `grid_row`/`grid_col`
**and** the checkpoint's scaler bundle declares `grid_shape`, the adapter reassembles the real
grid so neighbouring cells inform each other. Otherwise each cell is processed as a
degenerate 1×1 grid (`[n_samples, seq_len, 1, 1, n_features]`) and spatial context is lost —
functional, but not what the model was trained on. Cells inside `grid_shape` that are not
supplied are filled with the training mean (0 after scaling), matching
`ts_convlstm_forecaster_train.scale_and_fill`.

**Query Parameters:**
- `model_id` (optional): Specific forecaster model

**Response:**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {...},
      "properties": {
        "id": "cell-001",
        "fire_probability": [0.85],
        "is_burning_predicted": [true],
        "fire_threshold": 0.5,
        "risk_score": 0.85,
        "risk_levels": [4],
        "risk_labels": ["HIGH"],
        "forecast": [[0.85]],
        "horizon": 1,
        "n_output_channels": 1,
        "grid_row": 3,
        "grid_col": 7,
        "model_id": "bushfire-convlstm-v1"
      }
    }
  ]
}
```

**Output properties:**

| Property | Description |
|---|---|
| `fire_probability` | Fire-occurrence probability in `[0, 1]`, one entry per horizon step. Primary output. |
| `is_burning_predicted` | `fire_probability > fire_threshold`, one entry per horizon step |
| `fire_threshold` | The threshold used for `is_burning_predicted` |
| `risk_score` | Mean `fire_probability` across the horizon |
| `risk_levels`, `risk_labels` | Discrete level `0..4` and its label, one entry per horizon step |
| `forecast` | `[horizon, n_output_channels]` raw model output — one **row** per horizon step. For the fire-probability model each row is `[p]`. Kept so a multi-channel checkpoint can still be served. |
| `horizon` | Number of predicted timesteps returned (1 for the current model) |
| `n_output_channels` | Values per predicted timestep (1 for the current model) |
| `grid_row`, `grid_col` | Echoed grid position, so a gridded response can be reassembled by the caller |

All per-horizon-step fields (`fire_probability`, `is_burning_predicted`, `risk_levels`,
`risk_labels`, `forecast`) are validated to have the same length.

### Bushfire Risk Classification (deprecated)

> **Deprecated.** The architecture has been reduced from two models (ConvLSTM forecaster →
> TCN classifier) to a single ConvLSTM that predicts fire probability directly. The TCN
> classifier and `POST /predict/bushfire/classify` are being retired — use
> `POST /predict/bushfire/forecast`, which now returns `fire_probability` per cell.

**Risk Level Mapping (from fire probability):**

| Probability | Level | Label |
|---|---|---|
| `p < 0.2` | 0 | `LOW` |
| `0.2 ≤ p < 0.4` | 1 | `MEDIUM_LOW` |
| `0.4 ≤ p < 0.6` | 2 | `MEDIUM` |
| `0.6 ≤ p < 0.8` | 3 | `MEDIUM_HIGH` |
| `p ≥ 0.8` | 4 | `HIGH` |

Thresholds live in one place — `prob_to_risk_level()` in `api/schemas/bushfire.py`.

## Contributing

### Adding a New Model

1. **Place checkpoint** in `src/models/<domain>/checkpoints/`

2. **Add YAML entry** in `api/config/models.yaml`:
   ```yaml
   - id: my-model-v1
     domain: <domain>
     kind: <kind>
     enabled: true
     checkpoint: src/models/<domain>/checkpoints/<file>.pth
     scaler_checkpoint: <path_or_null>
   ```

3. **Create inference adapter** `api/inference/my_domain.py`:
   ```python
   def predict_my_domain(payload: dict, bundle: LoadedModel) -> dict:
       # Validate, preprocess, infer, postprocess
       return result
   ```
5. **Add Pydantic schemas** in `api/schemas/my_domain.py`
6. **Add route** in `api/routers/predict.py`
7. **Test** with example payloads