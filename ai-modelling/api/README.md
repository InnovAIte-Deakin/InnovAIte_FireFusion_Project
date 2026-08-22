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
- **Bushfire Forecasting**: Time-series prediction of environmental variables using ConvLSTM
- **Bushfire Risk Classification**: Multi-step risk classification using TCN (Temporal Convolutional Networks)

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
│   └── bushfire_classifier.py       # TCN classification adapter
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
| `inference/bushfire_classifier.py` | Module | TCN risk classification & orchestration |
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
   - Runs bundle.model.predict()
   - Postprocesses to GeoJSON FeatureCollection
   ↓
5. FastAPI serializes response to JSON
   ↓
6. Client receives FeatureCollection with forecast arrays
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
  "misinformation": {
    "label": "misinformation",
    "confidence": 0.92,
    "probabilities": {
      "non_misinformation": 0.08,
      "misinformation": 0.92
    },
    "risk_score": 0.92,
    "severity": "HIGH"
  },
  "urgency": null,
  "humanitarian_task": null,
  "checkpoint": "/path/to/deberta"
}
```

The response is organised per classification task. `misinformation` is always populated (label, confidence, full probability distribution, plus the derived `risk_score`/`severity`). `urgency` and `humanitarian_task` follow the same `{label, probabilities}` shape but are reserved for the enhanced multi-task model — they're `null` until that model is wired in.

**Severity Mapping** (derived from `misinformation.risk_score`):
- `risk_score < 0.6` → `LOW`
- `0.6 ≤ risk_score < 0.75` → `MEDIUM`
- `0.75 ≤ risk_score < 0.9` → `HIGH`
- `risk_score ≥ 0.9` → `CRITICAL`

#### `POST /predict/misinformation/batch`
Classify multiple social media posts in a single request. This exists so callers processing a batch of posts (e.g. a feed page, an ingestion job) don't have to make one HTTP round-trip per post — the model still runs one post at a time internally, but the network/auth overhead is paid once for the whole batch.

**Request Body:**
```json
{
  "posts": [
    { "id": "post-1", "content": "Vaccines contain microchips inserted via 5G networks" },
    { "id": "post-2", "content": "Bushfire has been contained by fire crews" }
  ]
}
```
`posts` accepts 1 to 100 items; each item has the same shape as the single-post request body above (`id` and `content` are required, the rest optional).

**Query Parameters:**
- `model_id` (optional): Specific model to use for every post in the batch (defaults to first misinformation model)

**Response:**
```json
{
  "results": [
    { "id": "post-1", "misinformation": { "label": "misinformation", "...": "..." }, "urgency": null, "humanitarian_task": null, "...": "..." },
    { "id": "post-2", "misinformation": { "label": "non_misinformation", "...": "..." }, "urgency": null, "humanitarian_task": null, "...": "..." }
  ],
  "count": 2
}
```
Each entry in `results` is the exact same object shape as the single-post response. `count` is the number of posts processed. The single-post route (`/predict/misinformation`) is unchanged and still exists for callers that only need to classify one post at a time.

---

### Bushfire Forecasting

#### `POST /predict/bushfire/forecast`
Forecast environmental variables for the next N timesteps (default N=2).

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

**Features:**
- `observations`: [seq_len, n_features] array (e.g., 60 timesteps × 7 features)
- Features: `[skin_temperature_c, soil_temperature_level_1_c, surface_solar_radiation_downwards, surface_thermal_radiation_downwards, temperature_2m_c, u_component_of_wind_10m, v_component_of_wind_10m]`

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
        "forecast": [
          [20.8, 15.3, 102.5, 51.2, 22.5, 2.4, 1.25],
          [21.2, 15.6, 107.8, 53.5, 23.5, 2.3, 1.15]
        ],
        "model_id": "bushfire-forecaster-v1"
      }
    }
  ]
}
```

### Bushfire Risk Classification

#### `POST /predict/bushfire/classify`
Classify risk for each forecasted timestep (pipeline: forecaster → classifier).

**Request Body:** Same as `/predict/bushfire/forecast`

**Query Parameters:**
- `classifier_id` (optional): Specific classifier model
- `forecaster_id` (optional): Specific forecaster model

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
        "risk_probabilities": [0.15, 0.32],
        "risk_levels": [0, 1],
        "model_id": "bushfire-classifier-v1"
      }
    }
  ]
}
```

**Risk Level Mapping (from probability):**
- `p < 0.2` → level `0` (Low)
- `0.2 ≤ p < 0.4` → level `1` (Medium-Low)
- `0.4 ≤ p < 0.6` → level `2` (Medium)
- `0.6 ≤ p < 0.8` → level `3` (Medium-High)
- `p ≥ 0.8` → level `4` (High)

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