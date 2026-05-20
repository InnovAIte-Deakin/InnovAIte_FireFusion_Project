# Bushfire Modelling Module

## Overview

This folder contains the core bushfire forecasting and fire-risk modelling components used in the FireFusion AI system.

The module combines:
- environmental forecasting
- spatiotemporal deep learning
- fire risk classification
- inference pipelines
- trained checkpoint management

The bushfire modelling system is designed to:
1. forecast future environmental conditions
2. generate spatiotemporal climate predictions
3. classify bushfire risk levels
4. support emergency forecasting workflows

The models operate on:
- ERA5-Land environmental datasets
- gridded climate features
- temporal environmental sequences
- 5 km spatial structures

---

# Folder Structure

| File / Folder | Purpose |
|---|---|
| `README.md` | Main overview and onboarding guide for the bushfire modelling module |
| `checkpoints/` | Stores trained model weights and preprocessing scalers |
| `LSTM forecaster/` | Contains LSTM forecasting architecture and inference utilities |
| `fire_risk_pipeline.py` | End-to-end bushfire forecasting and risk prediction pipeline |
| `risk_classifier.py` | Generic risk classification abstraction |
| `tcn_classifier.py` | TCN-based bushfire classification model |
| `ts_convlstm_forecaster.py` | ConvLSTM spatiotemporal forecasting model |
| `ts_convlstm_forecaster_inference.py` | ConvLSTM forecasting inference pipeline |

---

# System Architecture

```text
Historical Environmental Data
        ↓
LSTM / ConvLSTM Forecasting
        ↓
Future Environmental Predictions
        ↓
TCN Risk Classification
        ↓
Bushfire Risk Prediction
```

---

# Main Components

## 1. Environmental Forecasting
- LSTM Forecaster
- ConvLSTM Forecaster

## 2. Fire Risk Classification
- Temporal Convolutional Network (TCN)

## 3. End-to-End Risk Pipeline
- Forecast + Classification Integration

---

# LSTM Forecasting Module

## Folder
```text
LSTM forecaster/
```

The LSTM forecasting subsystem predicts future environmental variables using historical climate sequences.

### Main Files

| File | Purpose |
|---|---|
| `ts_forecaster.py` | Defines the stacked LSTM forecasting architecture |
| `ts_forecaster_inference.py` | Loads trained LSTM checkpoints and performs inference |
| `README.md` | Detailed LSTM forecasting documentation |

---

# ConvLSTM Spatiotemporal Forecaster

### Main Files

| File | Purpose |
|---|---|
| `ts_convlstm_forecaster.py` | ConvLSTM forecasting architecture |
| `ts_convlstm_forecaster_inference.py` | ConvLSTM inference utilities |

The ConvLSTM model supports:
- spatial forecasting
- environmental grid prediction
- temporal climate modelling

---

# TCN Bushfire Risk Classifier

## File
```text
tcn_classifier.py
```

The classifier predicts bushfire risk from:
- environmental sequences
- forecasted climate conditions
- temporal feature windows

---

# Fire Risk Pipeline

## File
```text
fire_risk_pipeline.py
```

This pipeline:
1. loads environmental input data
2. generates forecasts
3. predicts fire risk
4. returns structured outputs

---

# Checkpoints Folder

## Folder
```text
checkpoints/
```

Stores trained model artifacts and preprocessing scalers.

### Stored Artifacts

| File | Description |
|---|---|
| `convlstm_forecaster.pth` | Trained ConvLSTM forecasting model |
| `convlstm_scaler.pkl` | ConvLSTM preprocessing scaler |
| `tcn_classifier.pth` | Trained TCN classifier |
| `tcn_scaler.pkl` | TCN preprocessing scaler |
| `lstm_forecaster.pth` | Trained LSTM forecasting model |
| `firefusion_scaler.pkl` | Shared LSTM preprocessing scaler |

---

# Technologies Used

- Python
- PyTorch
- NumPy
- Pandas
- Joblib
- ConvLSTM
- LSTM
- TCN
- Scikit-learn

---

# Typical Use Cases

- Bushfire forecasting
- Environmental prediction
- Fire-risk classification
- Spatiotemporal modelling
- Climate sequence forecasting
- Emergency forecasting systems

---

# Notes

- Forecasting models rely heavily on temporal ordering and feature scaling.
- The checkpoints folder stores binary artifacts and should not be manually modified.
- Forecasting outputs integrate directly with downstream risk classification systems.
