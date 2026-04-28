# FireFusion AI Modeling

This repository contains the AI modelling components for the FireFusion project: 

- model code, 
- ETL/feature engineering,
- lightweight FastAPI for model-serving and integration.

## What's in each folder

- `api/`: FastAPI app to serve models and expose endpoints for other services.
  - `main.py`: application entrypoint.
  - `routers/`: endpoint modules (recommended: `health.py`, `predict.py`).
  - `schemas/`: Pydantic models for request/response validation.
  - `dependencies.py`: shared DI logic (model loader, DB sessions).
- `src/`:
  - `data/`: ETL and data preprocessing code (GEE ingestion, resampling).
  - `models/`: model definitions and architecture code.
  - `training/`: training scripts, evaluation, checkpointing.
  - `utils/`: miscellaneous helpers used across modules.
- `notebooks/`: exploratory and research notebooks.
- `config/`: JSON/YAML configs and hyperparameters.
- `data/`: small sample datasets for local dev (add to `.gitignore`).
- `tests/`: unit and integration tests.

## Quick start (local development)

1. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## Running the model

### 1. Prepare your data

Your DataFrame needs these columns:

| Column | Description |
|---|---|
| `cell_id` | 5km x 5km grid cell ID |
| `datetime` | Daily timestamp |
| `temperature_2m` | Air temperature at 2m (ERA5 Land) |
| `skin_temperature` | Earth surface temperature |
| `soil_temperature_l1` | Soil temperature layer 1 |
| `surface_solar_radiation_downwards` | Solar radiation |
| `surface_thermal_radiation_downwards` | Thermal radiation |

### 2. Create sequences

```python
from src.utils.dataset import create_sequences, FEATURE_COLS

X, y = create_sequences(df, seq_len=60, horizon=2)
# X shape: (N, 60, 5)  — 60 days of input
# y shape: (N, 2,  5)  — next 2 days to predict
```

### 3. Split by time (not random)

```python
split = int(len(X) * 0.8)
X_train, X_test = X[:split], X[split:]
y_train, y_test = y[:split], y[split:]
```

### 4. Train with expanding window CV

Use this to find the best hyperparameters before final training.

```python
from src.models.lstm_model import build_lstm_model
from src.training.trainer import expanding_window_cv

model_fn = lambda: build_lstm_model(n_features=len(FEATURE_COLS))

fold_results = expanding_window_cv(
    X_train, y_train,
    model_fn,
    initial_train_size=1000,
    val_size=200,
)
```

### 5. Evaluate

```python
from src.training.evaluator import evaluate, print_evaluation

metrics = evaluate(model, X_test, y_test)
print_evaluation(metrics)
```

Example output:
```
MAE:  0.0234
RMSE: 0.0412

By forecast step:
  +1d  MAE=0.0198  RMSE=0.0367
  +2d  MAE=0.0270  RMSE=0.0457

By feature:
  temperature_2m                      MAE=0.0156  RMSE=0.0289
  skin_temperature                    MAE=0.0201  RMSE=0.0378
  ...
```

### 6. Save and load the model

```python
model.save("bushfire_lstm.keras")

from tensorflow import keras
model = keras.models.load_model("bushfire_lstm.keras")
```

---

## src/ structure

```
src/
├── data/
│   ├── preprocessing.py   # cleaning & type casting
│   └── transforms.py      # interpolation & scaling
├── models/
│   └── lstm_model.py      # LSTM architecture
├── training/
│   ├── trainer.py         # expanding window CV
│   └── evaluator.py       # MAE, RMSE per feature & per step
└── utils/
    └── dataset.py         # create_sequences + feature constants
```