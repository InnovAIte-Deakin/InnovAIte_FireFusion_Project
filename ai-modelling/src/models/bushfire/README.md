# Bushfire Modelling — Models Reference

## Overview
This folder contains the core bushfire forecasting + fire-risk components used by the FireFusion API. Two production models are provided:

- A 2D ConvLSTM spatiotemporal forecaster that predicts future environmental variables across grid cells.
- A Temporal Convolutional Network (TCN) classifier that predicts fire probability per cell (supports multi-step inference).

Both model implementations live here:
- Forecaster: `src/models/bushfire/ts_convlstm_forecaster.py`
- Classifier: `src/models/bushfire/tcn_classifier.py`

Saved checkpoints are located under `src/models/bushfire/checkpoints/`.



## Models summary

- ConvLSTM Forecaster
  - Purpose: Forecast multivariate environmental variables for each grid cell (spatial + temporal).
  - Input: grid sequences [batch, seq_len, height, width, input_channels]
  - Output: forecasts [batch, horizon, height, width, output_channels]

- TCN Classifier
  - Purpose: Given recent history (and forecast steps) predict fire probability per cell.
  - Input (single-step training / inference): ($B\times H \times W$, lookback, n_features)
  - Multi-step inference input (to produce horizon more than 1): ($B\times H \times W$, lookback + horizon - 1, n_features)
  - Output: ($B\times H \times W$, horizon, 1) or ($B\times H \times W$, 1)


## ConvLSTM Forecaster

### Architecture (high level)
- Two stacked ConvLSTM cells (ConvLSTMCell)
- Dropout after each ConvLSTM layer (Dropout2d)
- Final 1×1 Conv2d projection layer to produce horizon × output_channels
- Reshape / permute to return [batch, horizon, height, width, output_channels]

### Config
The model uses `ForecasterConfig`:
- `input_channels`: number of features per grid cell (e.g., 7)
- `horizon`: forecast horizon (e.g., 2)
- `output_channels`: output feature count (defaults to input_channels)
- `hidden_size_1`, `hidden_size_2`: hidden channel sizes for two ConvLSTM layers
- `dropout`: dropout probability

### Input / Output shapes
- Input: numpy or torch tensor shaped:
  - [batch, seq_len, height, width, input_channels]
  - The implementation internally permutes to [batch, seq_len, input_channels, height, width] before per-time-step processing.
- Output:
  - [batch, horizon, height, width, output_channels]


## TCN Classifier

### Architecture
- Input permuted to (batch, n_features, time) for 1D convs
- Stack of TCNBlock(s), each block:
  - Dilated causal conv → BatchNorm → ReLU → Dropout (×2)
  - Residual connection (1×1 conv if channel dims change)
- AdaptiveAvgPool1d collapses time dimension
- Head: Flatten → Linear(32) → ReLU → Dropout → Linear(1) → Sigmoid

### Config (ClassifierConfig)
- `n_features`: number of features per timestep (e.g., 7)
- `lookback_steps`: history window length (e.g., 60)
- `channels`: list of channel sizes per TCN block (default 6 blocks)
- `kernel_size`: convolution kernel size (default 3)
- `dilation_base`: base used to compute dilations (default 2)
- `dropout`: dropout probability

### Receptive field
- Receptive field = 2 * (kernel_size - 1) * sum(dilations)
- Default dilations = `[1,2,4,8,16,32]` → sum = 63 → receptive field = $2*(3-1)*63 = 252$ timesteps

### Forward behavior and multi-step inference
- When `model.horizon == 1` the forward pass returns shape (N, 1)
- If `model.horizon > 1` the model expects input windows shaped:
  - (N, lookback + horizon - 1, n_features)
  - The model slides a window of length `lookback` across the time axis to produce `horizon` outputs:
    - For t in 0..horizon-1 run `_forward_single(x[:, t:t+lookback, :])`
  - Output shape: (N, horizon, 1) — caller can `squeeze(-1)` to (N, horizon)

### Input / Output
- Caller typically flattens spatial dims: B,H,W → N = $B\times H \times W$
- Training input shape: (N, lookback_steps, n_features)
- Inference (multi-step): supply (N, lookback + horizon - 1, n_features)



## Inference pipeline

Typical pipeline (high-level):
1. Run forecaster to get forecasts per cell: outputs [batch, horizon, H, W, features]
2. For each cell, gather recent history (lookback steps). Pad or truncate to `lookback_steps`.
3. Build classifier input window:
   - If classifier horizon > 1: concatenate history_last_lookback + forecast_first_(horizon-1) → length = lookback + horizon - 1
   - Stack windows across cells → shape (N, L, n_features) where N = number of cells
5. Flatten spatial dims if needed and call `model(x_tensor)`
6. Post-process probabilities to risk levels

Reference implementation: the API's adapter in `api/inference/bushfire_classifier.py` follows this pipeline.