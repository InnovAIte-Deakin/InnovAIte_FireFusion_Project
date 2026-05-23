# FireFusion — AI Modelling

The AI modelling component of the FireFusion project. This module handles all machine learning work for the system — including geospatial data ingestion from ERA5, bushfire risk forecasting, misinformation detection, a lightweight FastAPI for serving predictions, and integration with LLM APIs.

---

## Folder Structure

```
ai-modelling/
├── api/                        # FastAPI app for model serving
│   ├── config/                 # YAML configuration for model registry
│   ├── inference/              # Inference logic called by routers
│   ├── routers/                # Endpoint modules (health, predict)
│   ├── schemas/                # Pydantic request/response models
│   ├── __init__.py
│   ├── main.py                 # Application entrypoint
│   └── model_loader.py         # Loads and caches trained models
│
├── notebooks/                  # Jupyter notebooks for research & exploration
│   ├── exploratory/            # Data exploration and EDA notebooks
│   ├── images/                 # Figures and plots generated from notebooks
│   ├── research/               # Research and experimental notebooks
│   └── ERA5_Land_Dataset_Documentation.md
│
├── src/                        # Core ML source code
│   ├── data/                   # ETL and data preprocessing
│   │   ├── bushfire/           # Bushfire-specific data scripts
│   │   └── storage/            # Cloud storage utilities (AWS S3)
│   ├── models/                 # Model definitions and architecture
│   │   ├── bushfire/           # Bushfire forecasting models
│   │   └── misinformation/     # Misinformation detection models
│   ├── training/               # Training scripts and pipelines
│   │   └── LSTM/               # LSTM-specific training scripts
│   ├── utils/                  # Shared helper functions
│   └── __init__.py
│
├── tests/                      # Unit and integration tests
├── README.md
├── pr-template.md              # Pull request template for this stream
└── requirements.txt            # Python dependencies
```

---

## `api/` — Model Serving Layer

A lightweight **FastAPI** application that exposes trained models as HTTP endpoints for consumption by the backend and other services.

### Top-level scripts

| Script | Purpose |
|---|---|
| `main.py` | Application entrypoint. Initialises the FastAPI app, registers the `health` and `predict` routers, and triggers `load_models()` on startup via the lifespan context manager. Run with `uvicorn api.main:app --reload --host 0.0.0.0 --port 8080`. |
| `model_loader.py` | Loads and caches all enabled model checkpoints declared in `config/models.yaml` at startup. Provides `get_model(model_id)`, `list_models()`, `default_model_id_for_domain()`, `is_ready()`, and `load_errors()` for use by routers and inference modules. Supports `deberta_sequence_binary` kind; extensible for new model types. |

### `api/routers/`

| Script | Purpose |
|---|---|
| `health.py` | Liveness and readiness probes. Exposes `GET /health` (returns `{"status": "ok"}`) and `GET /ready` (returns readiness state and any model load errors). |
| `predict.py` | Prediction endpoint. Accepts a social media post payload, resolves the appropriate loaded model via `model_loader`, and calls the misinformation inference pipeline. |
| `__init__.py` | Marks `routers/` as a Python package. |

### `api/schemas/`

| Script | Purpose |
|---|---|
| `misinformation.py` | Pydantic models for the misinformation prediction endpoint. `MisinformationPostIn` validates incoming post data (id, content, platform, share count, timestamp, URL). `MisinformationPostOut` defines the structured response including label, confidence, probabilities, risk score, and severity. |

### `api/inference/`

| Script | Purpose |
|---|---|
| `misinformation.py` | Pure inference logic for misinformation scoring. Calls `deberta.classify_text()` with the loaded model bundle, computes a `risk_score` via max-softmax, maps it to a severity level (`LOW` / `MEDIUM` / `HIGH` / `CRITICAL`), and returns a fully structured result dict. Decoupled from routing so it can be tested independently. |
| `__init__.py` | Exports `predict_misinformation` as the public inference entrypoint for the package. |

---

## `src/` — Core ML Codebase

### `src/data/bushfire/`

ETL and preprocessing scripts for geospatial bushfire data ingested from Google Earth Engine (GEE) and the ERA5 Land dataset.

| Script | Purpose |
|---|---|
| `era5_dataset.py` | Fetches and processes ERA5 reanalysis climate data (temperature, wind, radiation, soil moisture) used as input features for the bushfire models. |
| `era5_land_dataset_extraction.js` | Google Earth Engine JavaScript script for extracting ERA5-Land dataset time series from GEE. |
| `cams-dataset.py` | Implements ingestion of CAMS (Copernicus Atmosphere Monitoring Service) atmospheric data as an additional data source. |
| `climate_dataset.py` | General climate dataset loading and preparation utilities shared across data sources. |
| `gee_api.py` | Python wrapper for authenticating and querying the Google Earth Engine API. |
| `preprocessing.py` | Data cleaning and preprocessing pipeline: handles missing values, type coercion, and timestep alignment across datasets. |
| `data_processing.py` | Higher-level data processing orchestration combining multiple sources into model-ready feature sets. |
| `transforms.py` | Feature transformation utilities: scaling, normalisation, and resampling of geospatial time series. |


### `src/data/storage/`

| Script | Purpose |
|---|---|
| `s3_client.py` | AWS S3 storage client. Centralises S3 authentication and common bucket operations (list, read, write, upload, download) so bushfire and NLP pipelines can load inputs and persist outputs and model artifacts consistently. |

### `src/models/bushfire/`

Bushfire risk prediction model definitions and architecture code.

| Script / Folder | Purpose |
|---|---|
| `fire_risk_pipeline.py` | End-to-end pipeline that chains preprocessing, feature extraction, and model inference to produce a fire risk score from raw climate inputs. |
| `risk_classifier.py` | Classifier model definition for categorical fire risk prediction (e.g. low / moderate / high / extreme). |
| `tcn_classifier.py` | Temporal Convolutional Network (TCN) classifier architecture for sequence-based fire risk classification. Dimensions aligned to match LSTM input shape. |
| `ts_convlstm_forecaster.py` | ConvLSTM model architecture for spatiotemporal forecasting of fire conditions across a grid. |
| `ts_convlstm_forecaster_inference.py` | Inference wrapper for the ConvLSTM forecaster: loads a saved checkpoint and runs predictions on new input sequences. |
| `LSTM forecaster/` | Subfolder containing the full LSTM forecasting model implementation. |
| `checkpoints/` | Saved model weights and scaler artifacts produced during training (`.pth` and `.pkl` files, not tracked in git). |

### `src/models/misinformation/`

Misinformation detection model definitions using transformer-based NLP.

| Script | Purpose |
|---|---|
| `deberta.py` | DeBERTa-based sequence classifier for binary misinformation detection. Provides `classify_text()` (used by the inference layer) and `load_classifier_from_checkpoint()` (used by `model_loader.py`). Also defines `DebertaMisinfoTrainConfig` with default hyperparameters. |
| `llm_client.py` | Client for calling external LLM APIs (OpenAI / Google Gemini) to support narrative analysis and alternative misinformation detection approaches. |
| `nlp_pipeline.py` | Higher-level NLP pipeline incorporating narrative clustering logic to group related misinformation posts and identify coordinated patterns. |

### `src/training/`

Training scripts for all model types.

| Script / Folder | Purpose |
|---|---|
| `bushfire_training.py` | Training entrypoint for bushfire risk classifier models. Loads prepared climate features, runs the training loop, and saves model checkpoints. |
| `tcn_train_classifier.py` | Training script for the TCN classifier. Handles TCN-specific configuration and dimension alignment with LSTM outputs. |
| `train_deberta.py` | Fine-tuning script for the DeBERTa misinformation classifier. Loads labelled social media post data, fine-tunes the transformer, and saves the checkpoint and training metadata. |
| `ts_convlstm_forecaster_train.py` | Training script for the ConvLSTM spatiotemporal forecaster. |
| `LSTM/ts_forecaster_train.py` | Full training pipeline for the multivariate LSTM time-series forecaster. Loads ERA5 climate features, scales data, creates sliding-window sequences (60-step input → 2-step horizon), trains with early stopping, evaluates on the test set in original units (MAE, RMSE, MAPE per feature), and saves the trained model and scaler to `checkpoints/`. |

### `src/utils/`

| Script | Purpose |
|---|---|
| `visualisers.py` | Plotting and visualisation utilities for model outputs, training curves, and geospatial data. Used across notebooks and evaluation scripts. |

---

## Dependencies

| Category | Libraries |
|---|---|
| Geospatial | `earthengine-api >= 1.0.0` |
| Data | `pandas >= 2.2.0`, `numpy >= 1.26.0` |
| ML | `scikit-learn >= 1.4.0` |
| Visualisation | `matplotlib >= 3.8.0` |
| Notebooks | `ipython >= 8.20.0` |
| LLM | `openai`, `google-genai` |
| Testing | `pytest >= 8.0.0` |

---

## Quick Start

### 1. Set up a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run the API locally

```bash
cd ai-modelling
uvicorn api.main:app --reload --host 0.0.0.0 --port 8080
```

- Liveness check: `GET http://localhost:8080/health`
- Readiness check: `GET http://localhost:8080/ready`
- Predict: `POST http://localhost:8080/predict`

### 3. Run training

```bash
# Bushfire LSTM forecaster
python src/training/LSTM/ts_forecaster_train.py

# Misinformation DeBERTa classifier
python src/training/train_deberta.py

# TCN classifier
python src/training/tcn_train_classifier.py
```

### 4. Run tests

```bash
pytest tests/
```

---

## Contributing

Please use `pr-template.md` when opening pull requests against this module.
