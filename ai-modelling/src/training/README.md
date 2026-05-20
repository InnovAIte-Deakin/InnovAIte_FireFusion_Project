# Training Module

## Overview

This folder contains the training pipelines used for the FireFusion AI modelling system.

The module includes:
- Bushfire classification training pipelines
- Environmental forecasting model training
- Spatiotemporal ConvLSTM forecasting
- Transformer fine-tuning for misinformation detection
- Time-series preprocessing and evaluation workflows
- Model checkpoint and scaler generation

The training scripts are designed for:
- reproducible experiments
- time-aware dataset splitting
- leakage prevention
- scalable GPU training
- model checkpointing and evaluation

---

# Folder Structure

| File / Folder | Purpose |
|---|---|
| `LSTM/` | Contains LSTM forecasting training pipelines |
| `tcn_train_classifier.py` | Training pipeline for TCN-based bushfire classification |
| `train_deberta.py` | Fine-tuning pipeline for DeBERTa misinformation detection |
| `ts_convlstm_forecaster_train.py` | ConvLSTM spatiotemporal forecasting training pipeline |
| `bushfire_training.py` | Placeholder/experimental bushfire training script |

---

# Training Architectures

This module contains multiple independent AI training systems.

```text
Environmental Forecasting
    ├── LSTM Forecaster
    └── ConvLSTM Forecaster

Bushfire Classification
    └── TCN Classifier

Misinformation Detection
    └── DeBERTa Transformer
```

---

# 1. TCN Bushfire Classification

## File
```text
tcn_train_classifier.py
```

This training pipeline builds a Temporal Convolutional Network (TCN) classifier for bushfire prediction using:
- ERA5-Land environmental data
- satellite fire detections
- spatiotemporal grid alignment

The workflow:
1. loads environmental datasets
2. spatially joins fire detections to grid cells
3. creates labelled training sequences
4. performs time-based train/validation/test splitting
5. trains a TCN classifier
6. evaluates fire prediction performance
7. saves trained checkpoints and scalers

## Key Features

### Time-Based Splitting
The pipeline prevents temporal leakage using fixed chronological splits:
- train
- validation
- test

### Spatial Joining
Fire detections are mapped onto:
- ERA5 5 km grid cells
- shared timestamps

### Sequence Generation
Sliding windows are generated dynamically for:
- temporal classification
- fire probability prediction

### Evaluation Metrics
- ROC-AUC
- F1-score
- Precision
- Recall
- Confusion matrix

---

# 2. DeBERTa Misinformation Fine-Tuning

## File
```text
train_deberta.py
```

This script fine-tunes:
```text
microsoft/deberta-v3-large
```

for binary misinformation classification.

The model is trained on JSON datasets containing:
- claim text
- misinformation labels

## Features

### Transformer Fine-Tuning
- Hugging Face Transformers
- mixed precision training
- gradient accumulation
- gradient checkpointing

### Evaluation
Validation metrics include:
- accuracy
- macro F1-score
- precision
- recall

### Early Stopping
Training stops automatically when validation performance no longer improves.

### Outputs
The pipeline saves:
- model checkpoints
- tokenizer files
- training metadata

---

# 3. ConvLSTM Spatiotemporal Forecasting

## File
```text
ts_convlstm_forecaster_train.py
```

This pipeline trains a ConvLSTM forecasting model on:
- gridded environmental data
- spatiotemporal climate sequences

The model predicts future environmental conditions across spatial grids.

---

# ConvLSTM Workflow

```text
Environmental CSV Data
        ↓
Grid Formatting
        ↓
Spatial Tensor Construction
        ↓
Sliding Window Sequences
        ↓
ConvLSTM Training
        ↓
Forecast Prediction
```

---

## Key Features

### Grid Construction
Environmental CSV data is converted into:
```text
[n_timesteps, height, width, n_features]
```

tensor format.

### Land Masking
The model excludes:
- ocean cells
- invalid spatial regions

during loss computation.

### Temporal Forecasting
The ConvLSTM predicts:
- future climate variables
- spatiotemporal environmental evolution

### Metrics
- MAE
- RMSE
- R² score

---

# 4. LSTM Multivariate Forecasting

## Folder
```text
LSTM/
```

## Main File
```text
ts_forecaster_train.py
```

This training pipeline builds a multivariate LSTM forecaster for environmental time-series prediction.

The model learns temporal relationships between:
- temperature
- wind
- radiation
- soil conditions

using sliding-window forecasting.

---

# LSTM Forecasting Workflow

```text
Environmental Time-Series
        ↓
Scaling & Normalisation
        ↓
Sliding Window Generation
        ↓
LSTM Forecasting
        ↓
Future Environmental Predictions
```

---

## Features

### Time-Series Processing
- chronological ordering
- leakage-safe scaling
- sliding-window sequence generation

### Forecasting
The model predicts:
- multiple future timesteps
- multiple environmental variables simultaneously

### Evaluation Metrics
- MAE
- RMSE
- MAPE

### Outputs
The pipeline saves:
- trained model weights
- fitted scalers
- forecasting metadata

---

# Shared Training Design Principles

All training pipelines follow several common principles:

## Leakage Prevention
- chronological splits
- train-only scaling
- held-out evaluation sets

## GPU Support
Pipelines automatically use:
- CUDA when available
- CPU fallback otherwise

## Checkpointing
Training scripts save:
- model weights
- fitted scalers
- metadata

## Early Stopping
Most models implement:
- validation monitoring
- patience-based stopping

---

# Technologies Used

- Python
- PyTorch
- Hugging Face Transformers
- Scikit-learn
- NumPy
- Pandas
- GeoPandas
- ConvLSTM
- LSTM
- TCN
- DeBERTa v3-large

---

# Typical Use Cases

This module supports:
- Bushfire prediction
- Environmental forecasting
- Spatiotemporal climate modelling
- Fire risk classification
- NLP misinformation detection
- Emergency AI workflows

---

# Running Training Pipelines

From the project root:

## TCN Bushfire Classifier
```bash
python -m src.training.tcn_train_classifier
```

## DeBERTa Fine-Tuning
```bash
python src/training/train_deberta.py --train data/train.json --output-dir checkpoints/misinfo-deberta
```

## ConvLSTM Forecasting
```bash
python -m src.training.ts_convlstm_forecaster_train
```

## LSTM Forecasting
```bash
python -m src.training.LSTM.ts_forecaster_train
```

---

# Notes

- Most training scripts assume ERA5-Land environmental datasets are already preprocessed.
- Forecasting pipelines rely heavily on consistent temporal ordering.
- Spatial models require properly aligned grid structures.
- Model checkpoints are saved under:
```text
src/models/bushfire/checkpoints/
```
- Training pipelines are designed to support future expansion into larger multi-modal AI workflows.
