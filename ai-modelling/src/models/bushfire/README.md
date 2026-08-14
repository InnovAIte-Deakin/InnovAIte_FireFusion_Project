# ConvLSTM Bushfire Prediction Model Reference

This project implements a PyTorch-based ConvLSTM model for spatiotemporal bushfire prediction. The model uses historical environmental and climate variables from gridded spatial data to predict the probability that each grid cell is burning at the next timestep. Unlike the previous architecture, it performs direct bushfire probability prediction without an intermediate environmental forecasting stage.

## Key Features

- **Binary Bushfire Prediction**: Predicts the probability that each grid cell is burning.
- **Single-Step Prediction**: Generates predictions one timestep into the future.
- **Stacked ConvLSTM Architecture**: Two ConvLSTM layers with dropout regularisation for spatiotemporal modelling.
- **Direct Environmental Modelling**: Uses historical environmental and climate variables directly as input, without intermediate environmental forecasting.
- **Separate Inference Module**: Simple API for loading trained models and generating predictions.

## Project Components

The ConvLSTM bushfire prediction model consists of three core scripts:

- **Model definition** (`src/models/bushfire/ts_convlstm_forecaster.py`) – Defines the ConvLSTM architecture and model configuration.
- **Training pipeline** (`src/training/ts_convlstm_forecaster_train.py`) – Trains and evaluates the model using historical environmental data.
- **Inference API** (`api/inference/bushfire_forecaster.py`) – Loads the trained model and performs bushfire probability inference.

Model checkpoints are stored in `src/models/bushfire/checkpoints/`.

## Installation

### Requirements

- Python 3.8+
- PyTorch >= 1.9.0
- scikit-learn >= 0.24
- pandas >= 1.2
- numpy >= 1.19
- joblib >= 1.0

## Quick Start

### Training

```bash
cd ai-modelling
python -m src.training.ts_convlstm_forecaster_train
```

This will:

1. Load the training dataset.
2. Split the data into training, validation, and test sets.
3. Train the ConvLSTM model with early stopping.
4. Evaluate the trained model on the test set.
5. Save the trained model checkpoint.

### Inference

```bash
cd ai-modelling
python -m api.inference.bushfire_forecaster
```

The inference module loads the trained ConvLSTM model and generates bushfire probability predictions from new environmental data.

## Model Architecture

```text
Input: [Batch, Sequence Length, Height, Width, Input Channels]
   ↓
ConvLSTM Layer 1 (hidden_size=64)
   ↓
Dropout (p=0.2)
   ↓
ConvLSTM Layer 2 (hidden_size=32)
   ↓
Dropout (p=0.2)
   ↓
1×1 Conv2d Projection
   ↓
Reshape → [Batch, 1, Height, Width, 1]
   ↓
Output (Raw Logits): [Batch, 1, Height, Width, 1]
   ↓
Sigmoid (predict() only)
   ↓
Output (Burning Probability)
```

- Processes 60 historical timesteps of gridded environmental data.
- Learns both spatial and temporal dependencies using stacked ConvLSTM layers.
- Produces a single raw logit for each grid cell, representing the likelihood of burning at the next timestep.

## Configuration

The model uses `ForecasterConfig` to define its architecture and hyperparameters:

- `input_channels`: Number of environmental variables per grid cell.
- `horizon`: Prediction horizon (default: 1 timestep).
- `output_channels`: Number of output channels (default: 1).
- `hidden_size_1`: Number of hidden channels in the first ConvLSTM layer.
- `hidden_size_2`: Number of hidden channels in the second ConvLSTM layer.
- `dropout`: Dropout probability.

## Input and Output Shapes

**Input**

The model accepts a NumPy array or PyTorch tensor with shape `[batch, sequence_length, height, width, input_channels]`. Internally, the input is permuted to `[batch, sequence_length, input_channels, height, width]` before being processed by the ConvLSTM layers.

**Output**

The model returns raw logits with shape `[batch, 1, height, width, 1]`. During inference, these logits are passed through a sigmoid activation function to produce burning probabilities between 0 and 1.