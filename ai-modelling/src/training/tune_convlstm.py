"""
Optuna hyperparameter tuning for the BASELINE ConvLSTM bushfire classifier.

Tunes only the baseline architecture from ts_convlstm_forecaster.py:
attention="none", use_bilstm=False, use_biconvlstm=False.

Usage:
    pip install optuna
    python -m src.training.tune_convlstm_baseline
"""

import json
import os
import numpy as np
import optuna
import torch
from torch.utils.data import DataLoader
from sklearn.preprocessing import StandardScaler
from ..models.bushfire.ts_convlstm_forecaster import ForecasterConfig, MultivariateTSForecaster
from .ts_convlstm_forecaster_train import (
    DATA_PATH,
    LABEL_PATH,
    LABEL_CACHE,
    FEATURES,
    HORIZON,
    DEVICE,
    GriddedTimeSeriesDataset,
    MaskedTverskyLoss,
    load_and_format_gridded_data,
    load_and_format_label_grid,
    train_one_epoch,
    evaluate,
)

N_TRIALS = 30
TRIAL_EPOCHS = 15
PATIENCE = 5


def prepare_data():
    """Load, split, and scale the data once, shared across all trials."""
    grid_cache = "src/data/bushfire/data_grid_cache.npy"
    if os.path.exists(grid_cache):
        data_grid = np.load(grid_cache)
    else:
        data_grid = load_and_format_gridded_data(DATA_PATH, feature_cols=FEATURES)
        np.save(grid_cache, data_grid)

    n_timesteps, h, w, n_features = data_grid.shape
    valid_mask = ~np.all(np.isnan(data_grid), axis=(0, -1))

    if os.path.exists(LABEL_CACHE):
        label_grid = np.load(LABEL_CACHE)
    else:
        label_grid = load_and_format_label_grid(LABEL_PATH, DATA_PATH, (h, w))
        np.save(LABEL_CACHE, label_grid)

    split_idx = int(len(data_grid) * 0.9)
    val_split_idx = int(split_idx * 0.85)

    train_grid, val_grid = data_grid[:val_split_idx], data_grid[val_split_idx:split_idx]
    train_labels, val_labels = label_grid[:val_split_idx], label_grid[val_split_idx:split_idx]

    scaler = StandardScaler()
    train_flat = train_grid.reshape(-1, n_features)
    scaler.fit(train_flat[~np.all(np.isnan(train_flat), axis=1)])

    def scale_and_fill(grid):
        flat = scaler.transform(grid.reshape(-1, n_features))
        flat[np.isnan(flat)] = 0.0
        return flat.reshape(grid.shape)

    train_input = np.concatenate([scale_and_fill(train_grid), train_labels], axis=-1)
    val_input = np.concatenate([scale_and_fill(val_grid), val_labels], axis=-1)

    return {
        "train_input": train_input, "train_labels": train_labels,
        "val_input": val_input, "val_labels": val_labels,
        "n_features": n_features,
        "valid_mask_tensor": torch.tensor(valid_mask, dtype=torch.bool),
    }


def objective(trial, data):
    hidden_size_1 = trial.suggest_int("hidden_size_1", 16, 64, step=16)
    hidden_size_2 = trial.suggest_int("hidden_size_2", 8, 32, step=8)
    dropout = trial.suggest_float("dropout", 0.0, 0.5)
    learning_rate = trial.suggest_float("learning_rate", 1e-4, 1e-2, log=True)
    batch_size = trial.suggest_categorical("batch_size", [4, 8, 16, 32])
    tversky_alpha = trial.suggest_float("tversky_alpha", 0.1, 0.5)
    input_steps = trial.suggest_int("input_steps", 10, 40, step=5)

    train_ds = GriddedTimeSeriesDataset(data["train_input"], data["train_labels"], input_steps, HORIZON)
    val_ds = GriddedTimeSeriesDataset(data["val_input"], data["val_labels"], input_steps, HORIZON)
    if len(train_ds) == 0 or len(val_ds) == 0:
        raise optuna.TrialPruned("Not enough timesteps for this input_steps value.")

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)

    config = ForecasterConfig(
        input_channels=data["n_features"] + 1,
        horizon=HORIZON,
        output_channels=1,
        hidden_size_1=hidden_size_1,
        hidden_size_2=hidden_size_2,
        dropout=dropout,
        attention="none",
        use_bilstm=False,
        use_biconvlstm=False,
    )
    model = MultivariateTSForecaster(config).to(DEVICE)
    criterion = MaskedTverskyLoss(data["valid_mask_tensor"], alpha=tversky_alpha, beta=1 - tversky_alpha).to(DEVICE)
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

    best_val_loss = float("inf")
    patience_counter = 0
    for epoch in range(1, TRIAL_EPOCHS + 1):
        train_one_epoch(model, train_loader, criterion, optimizer, DEVICE)
        val_loss = evaluate(model, val_loader, criterion, DEVICE)

        best_val_loss = min(best_val_loss, val_loss)
        patience_counter = 0 if val_loss == best_val_loss else patience_counter + 1

        trial.report(val_loss, epoch)
        if trial.should_prune():
            raise optuna.TrialPruned()
        if patience_counter >= PATIENCE:
            break

    return best_val_loss


def main():
    print("Using device:", DEVICE)
    data = prepare_data()

    study = optuna.create_study(direction="minimize", pruner=optuna.pruners.MedianPruner())
    study.optimize(lambda trial: objective(trial, data), n_trials=N_TRIALS)

    print("\nBest val Tversky loss:", study.best_value)
    print("Best params:")
    for k, v in study.best_params.items():
        print(f"  {k}: {v}")

    with open("src/models/bushfire/checkpoints/optuna_best_params.json", "w") as f:
        json.dump({"value": study.best_value, "params": study.best_params}, f, indent=2)


if __name__ == "__main__":
    main()
