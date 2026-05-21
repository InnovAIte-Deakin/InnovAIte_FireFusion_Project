"""
Forecasting Inference Module for 2D ConvLSTM
Loads trained ConvLSTM model and makes predictions on gridded data.
"""
import sys
from pathlib import Path
from typing import Union
import joblib
import numpy as np
import torch

from .ts_convlstm_forecaster import MultivariateTSForecaster

FEATURES = [
    "skin_temperature_c",
    "soil_temperature_level_1_c",
    "surface_solar_radiation_downwards",
    "surface_thermal_radiation_downwards",
    "temperature_2m_c",
    "u_component_of_wind_10m",
    "v_component_of_wind_10m"
]

class ForecastingPredictor:
    """
    2D ConvLSTM-based spatiotemporal forecasting predictor.
    
    Loads a pre-trained ConvLSTM model and its associated scaler for inference
    on gridded spatial data. Handles scaling consistency, batch predictions,
    and inverse transformation to original units.
    
    Attributes:
        model (MultivariateTSForecaster): Loaded ConvLSTM model
        scaler (StandardScaler): Fitted scaler matching training distribution
        metadata (dict): Configuration metadata from training
        n_features (int): Number of input features
        horizon (int): Number of future timesteps to forecast
    """
    
    def __init__(
        self,
        model_path: Union[str, Path],
        scaler_path: Union[str, Path]
    ) -> None:
        """
        Initialize the forecasting predictor with trained model and scaler.
        Loads both the model checkpoint and the scaler used during training.
        
        Inputs:
            model_path (str/Path: Path to saved PyTorch model checkpoint (.pth file)
            scaler_path (str/Path): Path to saved scaler (.pkl file)
        
        Raises:
            FileNotFoundError: If model_path or scaler_path does not exist
            RuntimeError: If model or scaler loading fails
        """
        self.model_path = Path(model_path)
        self.scaler_path = Path(scaler_path)
        
        # Load scaler
        scaler_data = joblib.load(self.scaler_path)
            
        if isinstance(scaler_data, dict):
            self.scaler = scaler_data["scaler"]
            self.metadata = {
                "features": scaler_data.get("features"),
                "input_steps": scaler_data.get("input_steps"),
                "horizon": scaler_data.get("horizon"),
                "grid_shape": scaler_data.get("grid_shape")
            }
        else:
            self.scaler = scaler_data
            self.metadata = None
        
        # Load model
        self.model = MultivariateTSForecaster.load(str(self.model_path))

        self.n_features = self.model.input_channels
        self.horizon = self.model.horizon
    
    def predict(
        self, 
        x_scaled: np.ndarray, 
        return_original_scale: bool = True
    ) -> np.ndarray:
        """
        Generate forecasts for gridded input sequences.
        
        Takes scaled gridded input and produces predictions either in
        normalized (scaled) or original unit space.
        
        Inputs:
            x_scaled (np.ndarray): Scaled input grid sequences of shape 
                [batch, seq_len, height, width, n_features] where:
                - batch: Number of independent prediction tasks
                - seq_len: Lookback window
                - height, width: Spatial grid dimensions
                - n_features: Number of features (7)
                
            return_original_scale (bool, default=True): 
                If True, inverse-transform predictions to original units using
                the fitted scaler. 
                If False, return predictions in scaled space.
        
        Outputs:
            np.ndarray: Forecasted grid values of shape 
                [batch, horizon, height, width, n_features] where:
                - horizon: Number of future timesteps
                - Values in original scale if return_original_scale=True,
                  otherwise in normalized scale
        
        Raises:
            AssertionError: If input feature dimension doesn't match model's expected input channels
            RuntimeError: If model prediction fails
        """
        # Confirm expected features
        assert x_scaled.shape[-1] == self.n_features, \
            f"Expected {self.n_features} features, got {x_scaled.shape[-1]}"
        
        batch, seq_len, height, width, n_features = x_scaled.shape
        
        x_tensor = torch.from_numpy(x_scaled).float()
        
        # Predict
        with torch.no_grad():
            y_pred_scaled = self.model.predict(x_tensor).numpy()
        
        if return_original_scale:
            # Reshape
            b, h_pred, h_grid, w_grid, f = y_pred_scaled.shape
            y_flat = y_pred_scaled.reshape(-1, f)
            
            # Inverse transform
            y_original_flat = self.scaler.inverse_transform(y_flat)
            
            # Reshape back to grid
            y_original = y_original_flat.reshape(b, h_pred, h_grid, w_grid, f)
            return y_original
        
        return y_pred_scaled

if __name__ == "__main__":
    # Runs inference with test data in a gridded cache (.npy) format
    # Mainly used for testing. Script should be incorporated into the full pipeline for production
    MODEL_PATH = "src/models/bushfire/checkpoints/convlstm_forecaster.pth"
    SCALER_PATH = "src/models/bushfire/checkpoints/convlstm_scaler.pkl"
    SEQ_LEN = 60

    predictor = ForecastingPredictor(
        model_path=MODEL_PATH,
        scaler_path=SCALER_PATH
    )

    # Load cached grid and grab last 60 timesteps
    data_grid = np.load("src/data/bushfire/data_grid_cache.npy") # [n_timesteps, H, W, F]
    last_seq = data_grid[-SEQ_LEN:] # [60, H, W, F]

    _, height, width, n_features = data_grid.shape

    # Scale
    x_flat = last_seq.reshape(-1, n_features)
    x_scaled = predictor.scaler.transform(x_flat).reshape(SEQ_LEN, height, width, n_features)
    x_scaled = np.nan_to_num(x_scaled, nan=0.0)

    valid_mask = ~np.all(np.isnan(data_grid), axis=(0, -1))  # [H, W]


    # Add batch dimension
    x_input = x_scaled[np.newaxis, ...]

    # Predict
    forecasts = predictor.predict(x_input, return_original_scale=True)

    print(f"Forecasts shape: {forecasts.shape}  [batch, horizon, height, width, features]")
    
    # Print ten cell's results for evaluation
    cells_printed = 0
    for cy in range(height):
        for cx in range(width):
            if not valid_mask[cy, cx]:
                continue
            print(f"\nCell ({cy}, {cx}):")
            for t in range(forecasts.shape[1]):
                vals = forecasts[0, t, cy, cx, :]
                feat_str = {feat: f"{v:.4f}" for feat, v in zip(FEATURES, vals)}
                print(f"  Timestep +{t+1}: {feat_str}")
            cells_printed += 1
            if cells_printed >= 10:
                break
        if cells_printed >= 10:
            break
