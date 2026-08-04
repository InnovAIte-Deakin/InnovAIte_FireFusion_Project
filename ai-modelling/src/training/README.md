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

This script fine-tunes a DeBERTa model for binary misinformation classification.

The default model is:

```text
microsoft/deberta-v3-large
```

The script uses the shared model and data utilities from:

```text
src/models/misinformation/deberta.py
```

## Dataset Format

The training data can be provided as either a CSV or JSON file.

Each record must contain:

```text
claim
label
```

The `claim` field contains the text to classify.

The `label` field uses the following mapping:

```text
0 = non_misinformation
1 = misinformation
```

Example JSON:

```json
[
  {
    "claim": "Emergency services issued an official bushfire warning.",
    "label": 0
  },
  {
    "claim": "All evacuation centres have permanently closed.",
    "label": 1
  }
]
```

Example CSV:

```csv
claim,label
"Emergency services issued an official bushfire warning.",0
"All evacuation centres have permanently closed.",1
```

The training dataset should contain both label values.

## Validation Options

The script supports two validation methods.

### Separate Validation File

A separate validation dataset can be provided using `--val`.

```bash
python src/training/deberta_train.py --train data/train.json --val data/validation.json --output-dir checkpoints/misinfo-deberta
```

### Stratified Split

If `--val` is not provided, the script automatically creates a stratified training and validation split.

This keeps the proportion of labels `0` and `1` similar in both datasets.

The validation size can be changed using `--test-size`.

## Running the Training Script

Run the script from the `ai-modelling` folder.

Using JSON data:

```bash
python src/training/deberta_train.py --train data/train.json --output-dir checkpoints/misinfo-deberta
```

Using CSV data:

```bash
python src/training/deberta_train.py --train data/train.csv --output-dir checkpoints/misinfo-deberta
```

## Main Arguments

| Argument                    | Purpose                                                | Default                      |
| --------------------------- | ------------------------------------------------------ | ---------------------------- |
| `--train`                   | Path to the training CSV or JSON file                  | Required                     |
| `--val`                     | Optional validation CSV or JSON file                   | None                         |
| `--output-dir`              | Directory used to save the checkpoint                  | Required                     |
| `--hf-model-id`             | Hugging Face model ID                                  | `microsoft/deberta-v3-large` |
| `--test-size`               | Validation proportion when `--val` is not provided     | `0.1`                        |
| `--seed`                    | Random seed                                            | `42`                         |
| `--max-len`                 | Maximum token length                                   | `256`                        |
| `--batch-size`              | Number of records in each batch                        | `4`                          |
| `--grad-accum`              | Number of batches accumulated before an optimiser step | `1`                          |
| `--epochs`                  | Maximum training epochs                                | `4`                          |
| `--lr`                      | Learning rate                                          | `2e-5`                       |
| `--weight-decay`            | Weight decay                                           | `0.01`                       |
| `--warmup-ratio`            | Proportion of warm-up steps                            | `0.06`                       |
| `--max-grad-norm`           | Maximum gradient norm                                  | `1.0`                        |
| `--early-stopping-patience` | Epochs allowed without improvement                     | `2`                          |
| `--min-delta`               | Minimum macro F1 improvement                           | `0.0001`                     |
| `--num-workers`             | Data loader workers                                    | `0`                          |
| `--gradient-checkpointing`  | Enables gradient checkpointing                         | Disabled                     |

The full argument list can be displayed using:

```bash
python src/training/deberta_train.py --help
```

## Training Process

The script performs the following steps:

1. Loads the CSV or JSON dataset.
2. Uses `claim` as the text field and `label` as the target field.
3. Creates either a separate validation dataset or a stratified split.
4. Loads the DeBERTa tokenizer and classification model.
5. Creates training and validation data loaders.
6. Trains the model using gradient accumulation.
7. Updates the learning-rate scheduler after each optimiser step.
8. Handles the final incomplete accumulation group correctly.
9. Calculates training and validation results after each epoch.
10. Saves the model when the validation macro F1-score improves.
11. Stops training early if performance does not improve.
12. Reloads the saved checkpoint to confirm that it works correctly.

## Evaluation Metrics

The script reports:

* training loss
* validation loss
* accuracy
* precision
* recall
* binary F1-score
* macro F1-score

Macro F1 is calculated using both classes:

```text
0 = non_misinformation
1 = misinformation
```

## Saved Outputs

The selected output directory contains the trained model and tokenizer files.

Typical saved files include:

```text
config.json
model.safetensors
tokenizer.json
tokenizer_config.json
special_tokens_map.json
training_meta.json
```

The exact tokenizer files may vary depending on the selected Hugging Face model.

## Training Metadata

The script creates:

```text
training_meta.json
```

This file records:

* Hugging Face model ID
* label mapping
* training and validation file paths
* split method
* training and validation dataset sizes
* random seed
* maximum token length
* batch size
* gradient accumulation steps
* effective batch size
* requested and completed epochs
* learning rate
* weight decay
* warm-up ratio
* device used
* best epoch
* best validation results
* final validation results
* training history
* checkpoint reload confirmation

## Checkpoint Verification

After training, the script removes the training model, optimiser, scheduler and scaler from memory.

It then reloads the saved checkpoint using:

```python
load_classifier_from_checkpoint()
```

The script confirms that the reopened model contains two output labels and evaluates the validation dataset again.

A successful run displays:

```text
Checkpoint reload verification: passed
```

## Smoke Test

A small balanced dataset and a lightweight DeBERTa-compatible model can be used to test the complete workflow before full training.

```bash
python src/training/deberta_train.py --train data/test_misinformation.json --output-dir checkpoints/test-deberta --hf-model-id ydshieh/tiny-random-DebertaV2ForSequenceClassification --test-size 0.2 --epochs 1 --batch-size 3 --grad-accum 4 --max-len 32 --early-stopping-patience 1
```

The smoke test checks:

* dataset loading
* stratified splitting
* gradient accumulation
* final incomplete accumulation handling
* metric calculation
* checkpoint saving
* tokenizer saving
* metadata generation
* checkpoint reopening

The results from a tiny random model and a small test dataset should not be treated as real model-performance results.

## Notes and Limitations

* Full training with `microsoft/deberta-v3-large` may require a GPU with enough memory.
* Training time depends on the dataset size, token length, batch size and selected model.
* Both label values should be present in the training dataset.
* The best checkpoint is selected using validation macro F1-score.
* A smoke test should be completed before starting full training.

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

From the `ai-modelling` folder:

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