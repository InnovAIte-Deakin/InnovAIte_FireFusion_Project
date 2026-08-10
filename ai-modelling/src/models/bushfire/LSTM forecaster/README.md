# LSTM Multivariate Time-Series Forecaster Component

A PyTorch-based LSTM model for forecasting environmental variables relevant to bushfire prediction. Predicts 2 timesteps ahead using 60 timesteps of historical data across environmental and climate features. Outputs are intended to be used as inputs for the Classification model component.

### Key Features
- **Multivariate Forecasting**: Predicts multiple environmental features simultaneously
- **2-Step Ahead Horizon**: Generates forecasts 2 timesteps into the future
- **Stacked LSTM Architecture**: Two LSTM layers with dropout regularization
- **Seperate Inference Module**: Simple API for loading trained models and generating predictions

## Project Structure

```
ai-modelling/
├── src/
│   ├── data/
│   │   └── bushfire/
│   │       └── **path-to-training-data**
│   │
│   ├── models/
│   │   └── bushfire/
│   │       ├── ts_forecaster.py
│   │       ├── forecasting_inference.py
│   │       └── checkpoints/
│   │           ├── lstm_forecaster.pth
│   │           └── firefusion_scaler.pkl
│   │
│   ├── training/
│   │   └── train_forecaster.py
│   │
│   └── __init__.py
```

## Scripts Overview
 
### `ts_forecaster.py` - Model Definition
**Location**: `src/models/bushfire/ts_forecaster.py`
 
Defines the LSTM architecture and configuration:
- **ForecasterConfig**: Dataclass storing model hyperparameters (input size, hidden sizes, dropout, horizon)
- **MultivariateTSForecaster**: PyTorch nn.Module implementing the stacked LSTM
- **Methods**: forward(), predict(), save(), load()
 
### `train_forecaster.py` - Training Pipeline
**Location**: `src/training/train_forecaster.py`
 
Complete training workflow:
- Loads CSV data and sorts by timestamp
- Splits data (train/val/test) before scaling to avoid data leakage
- Fits StandardScaler on training data only
- Creates sliding-window sequences (60-step input, 2-step output)
- Trains LSTM with early stopping and validation monitoring
- Evaluates on test set with per-feature metrics (MAE, RMSE, MAPE)
- Saves trained model weights and scaler for inference
**Run this** to train new models or retrain with different hyperparameters.
 
### `forecasting_inference.py` - Inference API
**Location**: `src/models/bushfire/forecasting_inference.py`
 
Simple interface for making predictions:
- **ForecastingPredictor**: Loads trained model and scaler
- **predict()**: Takes scaled input sequences, returns forecasts in original units
**Use this** for generating predictions on new data during deployment.

## Installation

### Requirements

- Python 3.8+
- PyTorch >= 1.9.0
- scikit-learn >= 0.24
- pandas >= 1.2
- numpy >= 1.19
- joblib >= 1.0

## Quick Start

### Training a Model
```bash
cd ai-modelling
python -m src.training.train_forecaster
```

This will:
1. Load training data from `src/data/bushfire/forecaster_test_data.csv`
2. Split data (90% train/val, 10% test)
3. Train LSTM for up to 50 epochs with early stopping
4. Evaluate on test set
5. Save model to `src/models/bushfire/checkpoints/lstm_forecaster.pth`
6. Save scaler to `src/models/bushfire/checkpoints/firefusion_scaler.pkl`

### Making Predictions
For testing:
```bash
cd ai-modelling
python -m src.models.bushfire.forecasting_inference
```

As part of the pipeline:
```python
from src.models.bushfire.forecasting_inference import ForecastingPredictor

# Load trained model and scaler
predictor = ForecastingPredictor(
    model_path="src/models/bushfire/checkpoints/lstm_forecaster.pth",
    scaler_path="src/models/bushfire/checkpoints/firefusion_scaler.pkl"
)

# 60 timesteps of data
# [1 sample, 60 timesteps, No. of features]
x_scaled = np.random.randn(1, 60, 7) 

# Generate 2-step ahead forecast
forecasts = predictor.predict(x_scaled, return_original_scale=True)

print(f"Timestep 1: {forecasts[0, 0]}")  # First future timestep, all features
print(f"Timestep 2: {forecasts[0, 1]}")  # Second future timestep, all features
```

## Model Architecture

### Network Diagram

```
Input: [Batch, 60, No. of features]
    ↓
LSTM Layer 1 (hidden_size=64)
    ↓
Dropout (p=0.2)
    ↓
LSTM Layer 2 (hidden_size=32)
    ↓
Extract final timestep → [Batch, 32]
    ↓
Dropout (p=0.2)
    ↓
Linear projection → [Batch, 14]  (2 horizon * No. of features)
    ↓
Reshape → [Batch, 2, No. of features]
    ↓
Output: [Batch, 2, No. of features]
```

### Architecture Details

| Component | Configuration |
|-----------|----------------|
| **Input Features** | features from training data |
| **Lookback Window** | 60 timesteps |
| **Forecast Horizon** | 2 timesteps |
| **LSTM Layer 1** | 64 hidden units |
| **LSTM Layer 2** | 32 hidden units |
| **Dropout Rate** | 0.2 (20%) |

## Configuration

Edit `src/training/train_forecaster.py` to adjust:

```python
INPUT_STEPS = 60 # Historical window size
HORIZON = 2 # Forecast timesteps ahead
TRAIN_VAL_RATIO = 0.9 # 90% train/val, 10% test
BATCH_SIZE = 32 # Samples per batch
EPOCHS = 50 # Maximum epochs
LEARNING_RATE = 0.001 # Optimizer learning rate
```

### Features Used
The model currently trains on these 7 environmental variables:

```python
FEATURES = [
    "skin_temperature_c",                      # Surface temperature
    "soil_temperature_level_1_c",              # Soil temperature
    "surface_solar_radiation_downwards",       # Solar irradiance
    "surface_thermal_radiation_downwards",     # Thermal radiation
    "temperature_2m_c",                        # 2m air temperature
    "u_component_of_wind_10m",                 # East-west wind
    "v_component_of_wind_10m"                  # North-south wind
]
```