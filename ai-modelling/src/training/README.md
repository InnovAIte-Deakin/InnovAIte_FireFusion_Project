# Overview

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

# Folder Structure

| File / Folder | Purpose |
|---|---|
| `tcn_classifier_train.py` | Training pipeline for TCN-based bushfire classification |
| `deberta_train.py` | Fine-tuning pipeline for DeBERTa misinformation detection |
| `ts_convlstm_forecaster_train.py` | ConvLSTM spatiotemporal forecasting training pipeline |

# 1. TCN Bushfire Classification

## File
```text
tcn_classifier_train.py
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
deberta_train.py
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

# Running Training Pipelines

From the project root:

## TCN Bushfire Classifier
```bash
python -m src.training.tcn_classifier_train
```

## DeBERTa Fine-Tuning
```bash
python src/training/deberta_train.py --train data/train.json --output-dir checkpoints/misinfo-deberta
```

## ConvLSTM Forecasting
```bash
python -m src.training.ts_convlstm_forecaster_train
```

# Notes

- Most training scripts assume ERA5-Land environmental datasets are already preprocessed.
- Forecasting pipelines rely heavily on consistent temporal ordering.
- Spatial models require properly aligned grid structures.
- Model checkpoints are saved under:
```text
src/models/bushfire/checkpoints/
```