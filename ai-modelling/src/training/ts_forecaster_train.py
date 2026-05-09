"""
Training script for the FireFusion LSTM multivariate time-series forecaster.

Flow:
1. Load environmental time-series data
2. Sort by timestamp
3. Split data in time order
4. Fit scaler only on train/validation data
5. Create sliding-window sequences
6. Train LSTM model
7. Evaluate on test set using unscaled values
8. Save trained model and scaler
"""

import os
import joblib
import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
from ..models.bushfire.ts_forecaster import ForecasterConfig, MultivariateTSForecaster

# Data and Save paths
# UPDATE DATA PATH WITH REAL TRAINING DATA WHEN AVAILABLE
DATA_PATH = "src/data/bushfire/forecaster_test_data.csv"
MODEL_SAVE_PATH = "src/models/bushfire/checkpoints/lstm_forecaster.pth"
SCALER_SAVE_PATH = "src/models/bushfire/checkpoints/firefusion_scaler.pkl"

TIME_COL = "datetime"

# Environmental features - update with climate as training data becomes available
FEATURES = [
    "skin_temperature_c",
    "soil_temperature_level_1_c",
    "surface_solar_radiation_downwards",
    "surface_thermal_radiation_downwards",
    "temperature_2m_c",
    "u_component_of_wind_10m",
    "v_component_of_wind_10m"
]

# Model hyperparameters
INPUT_STEPS = 60
HORIZON = 2

TRAIN_VAL_RATIO = 0.9
BATCH_SIZE = 32
EPOCHS = 50
LEARNING_RATE = 0.001

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Dataset
class TimeSeriesDataset(Dataset):
    """
    Pytorch Dataset for time-series forecasting.
    
    Wraps input sequences and target sequences for batch loading during training and evaluation
    """
    def __init__(self, X, y):
        """
        initialise t he time-series dataset.
        
        Inputs:
            X (np.ndarray): Input sequence of shape [n_samples, seq_len, n_features]
            y (np.ndarray): Target sequence of shape [n_samples, horizon, n_features]
        """
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.float32)

    def __len__(self):
        """
        Return the totla number of samples in the dataset.
        """
        return len(self.X)

    def __getitem__(self, idx):
        """
        Retreive a single sample from the dataset.
        
        Inputs:
            idx (int): Index of the sample
        
        Outputs:
            tuple: (X_sample, y_sample) where X_sample is of shape [seq_len, n_features]
                    and y_sample is of shape [horizon, n_features]
        """
        return self.X[idx], self.y[idx]

# Helpers
def create_sequences(data, input_steps, horizon):
    """
    Creates sliding-window samples by transforming a 2D time-series array into overlapping windows.

    Input:
        data (np.ndarray): 2D array of shape [n_timesteps, n_features]
        input_steps (int): Length of input sequence (lookback window)
        horizon (int): Number of tuture timesteps to predict

    Output:
        tuple: (X, y) where:
            X (np.ndarray): [n_samples, input_steps, n_features]
            y (np.ndarray): [n_samples, horizon, n_features]
    """
    X, y = [], []
    for i in range(len(data) - input_steps - horizon + 1):
        X.append(data[i:i + input_steps])
        y.append(data[i + input_steps:i + input_steps + horizon])

    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)

def load_data(path):
    """
    Load and preprocess environmental time-series data.
    
    Loads data from CSV or Excel, sorts by timestamp, converts columns to
    numeric format, and removes rows with missing values.
    
    Inputs:
        path (str): Path to data file (CSV or XLSX)
        
    Outputs:
        pd.DataFrame: Preprocessed dataframe
    """
    if path.endswith(".xlsx"):
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path)

    if TIME_COL in df.columns:
        df[TIME_COL] = pd.to_datetime(df[TIME_COL])
        df = df.sort_values(TIME_COL).reset_index(drop=True)

    df[FEATURES] = df[FEATURES].apply(pd.to_numeric, errors="coerce")
    df = df.dropna(subset=FEATURES).reset_index(drop=True)
    return df

def train_one_epoch(model, dataloader, criterion, optimizer):
    """
    Execute one training epoch.
    
    Trains the model on a single pass through the training dataloader,
    computing loss and updating model parameters via backpropagation.
    
    inputs:
        model (nn.Module): LSTM forecaster model
        dataloader (DataLoader): Training dataloader with (X, y) batches
        criterion (nn.Module): Loss function (e.g., MSELoss)
        optimizer (torch.optim.Optimizer): Optimizer for parameter updates
        
    Outputs:
        float: Mean loss across all batches in the epoch
    """
    model.train()
    losses = []
    for X_batch, y_batch in dataloader:
        X_batch = X_batch.to(DEVICE)
        y_batch = y_batch.to(DEVICE)
        optimizer.zero_grad()
        preds = model(X_batch)
        loss = criterion(preds, y_batch)
        loss.backward()
        optimizer.step()
        losses.append(loss.item())

    return np.mean(losses)

def evaluate_scaled(model, dataloader, criterion):
    """
    Evaluate model performance on validation/test data (scaled space).
    
    Computes loss without updating model parameters. Operates on scaled data
    to assess model's ability to predict normalized values.
    
    inputs:
        model (nn.Module): LSTM forecaster model
        dataloader (DataLoader): Validation/test dataloader with (X, y) batches
        criterion (nn.Module): Loss function
        
    Outputs:
        float: Mean loss across all batches
    """
    model.eval()
    losses = []
    with torch.no_grad():
        for X_batch, y_batch in dataloader:
            X_batch = X_batch.to(DEVICE)
            y_batch = y_batch.to(DEVICE)
            preds = model(X_batch)
            loss = criterion(preds, y_batch)
            losses.append(loss.item())

    return np.mean(losses)

def predict(model, dataloader):
    """
    Generate predictions on a dataloader without computing loss.
    
    inputs:
        model (nn.Module): LSTM forecaster model
        dataloader (DataLoader): Dataloader with (X, y) batches
        
    Outputs:
        tuple: (predictions, actuals) where:
            - predictions (np.ndarray): Model outputs of shape [n_samples, horizon, n_features]
            - actuals (np.ndarray): Ground truth targets of shape [n_samples, horizon, n_features]
    """
    model.eval()
    predictions = []
    actuals = []
    with torch.no_grad():
        for X_batch, y_batch in dataloader:
            X_batch = X_batch.to(DEVICE)
            preds = model(X_batch).cpu().numpy()
            predictions.append(preds)
            actuals.append(y_batch.numpy())

    return np.concatenate(predictions), np.concatenate(actuals)

def mape(y_true, y_pred):
    """
    Compute Mean Absolute Percentage Error (MAPE).
    
    Measures average percentage deviation of predictions from ground truth.
    Useful for comparing errors across features with different scales.
    Note: MAPE can be unstable for values near zero.
    
    Inputs:
        y_true (np.ndarray): Ground truth values
        y_pred (np.ndarray): Predicted values
        
    Outputs:
        float: MAPE as a percentage
    """
    return np.mean(np.abs((y_true - y_pred) / (y_true + 1e-8))) * 100

# Main Training Script
def main():
    """
    Training pipeline for the FireFusion LSTM forecaster.
    
    Orchestrates the full training workflow:
    1. Load and preprocess environmental data
    2. Split data into train/validation/test sets
    3. Fit scaler on training data only
    4. Create sliding-window sequences
    5. Train LSTM model with early stopping
    6. Evaluate on test set in original scale
    7. Save trained model and scaler for inference
    
    Outputs:
        Per-feature metrics (MAE, RMSE, MAPE)
        Trained model checkpoint
        Fitted scaler for reuse
    """
    os.makedirs("models", exist_ok=True)
    print("Using device:", DEVICE)
    df = load_data(DATA_PATH)
    data = df[FEATURES].values.astype(np.float32)
    print("Loaded data shape:", data.shape)

    # Split before scaling
    split_idx = int(len(data) * TRAIN_VAL_RATIO)
    train_val_raw = data[:split_idx]
    test_raw = data[split_idx:]
    scaler = StandardScaler()
    train_val_scaled = scaler.fit_transform(train_val_raw)
    test_scaled = scaler.transform(test_raw)
    X_train_val, y_train_val = create_sequences(
        train_val_scaled,
        INPUT_STEPS,
        HORIZON
    )

    X_test, y_test = create_sequences(
        test_scaled,
        INPUT_STEPS,
        HORIZON
    )

    if len(X_train_val) == 0 or len(X_test) == 0:
        raise ValueError(
            "Not enough data for 60:2 sliding windows. "
            "Use a larger historical dataset."
        )

    # Internal train/validation split
    val_split_idx = int(len(X_train_val) * 0.85)
    X_train = X_train_val[:val_split_idx]
    y_train = y_train_val[:val_split_idx]
    X_val = X_train_val[val_split_idx:]
    y_val = y_train_val[val_split_idx:]
    train_loader = DataLoader(
        TimeSeriesDataset(X_train, y_train),
        batch_size=BATCH_SIZE,
        shuffle=False
    )

    val_loader = DataLoader(
        TimeSeriesDataset(X_val, y_val),
        batch_size=BATCH_SIZE,
        shuffle=False
    )

    test_loader = DataLoader(
        TimeSeriesDataset(X_test, y_test),
        batch_size=BATCH_SIZE,
        shuffle=False
    )

    config = ForecasterConfig(
        input_size=len(FEATURES),
        horizon=HORIZON,
        output_size=len(FEATURES),
        hidden_size_1=64,
        hidden_size_2=32,
        dropout=0.2
    )
    model = MultivariateTSForecaster(config).to(DEVICE)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    best_val_loss = float("inf")
    best_state = None
    patience = 10
    patience_counter = 0
    print("\nStarting training...")
    for epoch in range(1, EPOCHS + 1):
        train_loss = train_one_epoch(model, train_loader, criterion, optimizer)
        val_loss = evaluate_scaled(model, val_loader, criterion)
        print(
            f"Epoch {epoch:03d} | "
            f"Train Loss: {train_loss:.6f} | "
            f"Val Loss: {val_loss:.6f}"
        )
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_state = model.state_dict()
            patience_counter = 0
        else:
            patience_counter += 1

        if patience_counter >= patience:
            print("Early stopping triggered.")
            break

    if best_state is not None:
        model.load_state_dict(best_state)

    # Test evaluation
    y_pred_scaled, y_true_scaled = predict(model, test_loader)
    y_pred_flat = y_pred_scaled.reshape(-1, len(FEATURES))
    y_true_flat = y_true_scaled.reshape(-1, len(FEATURES))

    # Convert back to original units
    y_pred_original = scaler.inverse_transform(y_pred_flat)
    y_true_original = scaler.inverse_transform(y_true_flat)
    mae = mean_absolute_error(y_true_original, y_pred_original)
    rmse = np.sqrt(mean_squared_error(y_true_original, y_pred_original))
    print("\nFinal Test Metrics:")
    print(f"MAE:  {mae:.4f}")
    print(f"RMSE: {rmse:.4f}")
    print("\nPer-feature Test Metrics:")
    for i, feature in enumerate(FEATURES):
        feature_mae = mean_absolute_error(
            y_true_original[:, i],
            y_pred_original[:, i]
        )

        feature_rmse = np.sqrt(
            mean_squared_error(
                y_true_original[:, i],
                y_pred_original[:, i]
            )
        )
        
        feature_mape = mape(y_true_original[:, i], y_pred_original[:, i])

        print(f"{feature}: MAE={feature_mae:.4f}, RMSE={feature_rmse:.4f}, MAPE={feature_mape:.2f}%")

    # Save model
    model.save(MODEL_SAVE_PATH)

    # Save scaler
    joblib.dump(
        {
            "scaler": scaler,
            "features": FEATURES,
            "input_steps": INPUT_STEPS,
            "horizon": HORIZON,
        },
        SCALER_SAVE_PATH
    )
    print("\nSaved model to:", MODEL_SAVE_PATH)
    print("Saved scaler to:", SCALER_SAVE_PATH)

if __name__ == "__main__":
    main()