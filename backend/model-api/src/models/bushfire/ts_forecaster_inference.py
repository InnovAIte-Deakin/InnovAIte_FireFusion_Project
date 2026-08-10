"""
Forecasting Inference Module
Loads trained LSTM model and makes prediction.
"""

from pathlib import Path
from typing import Union
import joblib
import pandas as pd
import numpy as np
import torch

from .ts_forecaster import MultivariateTSForecaster

# Environmental features - update with climate features as training data becomes available
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
    LSTM-based multivariate time-series forecasting predictor.
    
    Loads a pre-trained LSTM model and its associated scaler for inference.
    Handles scaling consistency, batch predictions, and inverse transformation
    to original units.
    
    Attributes:
        model (MultivariateTSForecaster): Loaded LSTM model
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
            model_path (str or Path): Path to saved PyTorch model checkpoint (.pth file)
            scaler_path (str or Path): Path to saved scaler (.pkl file)
        
        Raises:
            FileNotFoundError: If model_path or scaler_path does not exist
            RuntimeError: If model or scaler loading fails
        """
        self.model_path = Path(model_path)
        self.scaler_path = Path(scaler_path)
        
        # Load scaler - handles format
        scaler_data = joblib.load(self.scaler_path)
            
        if isinstance(scaler_data, dict):
            self.scaler = scaler_data["scaler"]
            self.metadata = {
                "features": scaler_data.get("features"),
                "input_steps": scaler_data.get("input_steps"),
                "horizon": scaler_data.get("horizon")
            }
        else:
            self.scaler = scaler_data
            self.metadata = None
        
        # Load model
        self.model = MultivariateTSForecaster.load(str(self.model_path))

        self.n_features = self.model.input_size
        self.horizon = self.model.horizon
    
    def predict(self, x_scaled: np.ndarray, return_original_scale: bool = True):
        """
        Generate forecasts for input sequences.
        
        Takes scaled input sequences and produces predictions either in
        normalized (scaled) or original unit space.
        
        Inputs:
            x_scaled (np.ndarray): Scaled input sequences of shape 
                [n_samples, input_steps, n_features] where:
                - n_samples: Number of independent prediction tasks
                - input_steps: Lookback window (typically 60 timesteps)
                - n_features: Number of features (typically 7)
                
            return_original_scale (bool, default=True): 
                If True, inverse-transform predictions to original units using
                the fitted scaler. If False, return predictions in scaled space.
        
        Outputs:
            np.ndarray: Forecasted values of shape [n_samples, horizon, n_features] where:
                - horizon: Number of future timesteps (typically 2)
                - Values in original scale if return_original_scale=True, otherwise in normalized scale
        
        Raises:
            AssertionError: If input feature dimension doesn't match model's
                expected input size
            RuntimeError: If model prediction fails
        """
        # Confirm expected features and ordering
        assert x_scaled.shape[-1] == self.n_features, f"Expected {self.n_features} features, got {x_scaled.shape[-1]}"
        
        x_tensor = torch.from_numpy(x_scaled).float()
        
        # Predict
        with torch.no_grad():
            y_pred_scaled = self.model.predict(x_tensor).numpy()
        
        if return_original_scale:
            n_samples, horizon, n_features = y_pred_scaled.shape
            y_flat = y_pred_scaled.reshape(-1, n_features)
            y_original = self.scaler.inverse_transform(y_flat)
            return y_original.reshape(n_samples, horizon, n_features)
        
        return y_pred_scaled

if __name__ == "__main__":
    """
    Example inference usage on test data.
    
    Loads the trained model and scaler, then makes predictions on the last
    60 timesteps of test data.
    """
    # Initialize predictor
    predictor = ForecastingPredictor(
        model_path="src/models/bushfire/checkpoints/lstm_forecaster.pth",
        scaler_path="src/models/bushfire/checkpoints/firefusion_scaler.pkl"
    )
    
    df = pd.read_csv("src/data/bushfire/forecaster_test_data.csv")
    data = df[FEATURES].values[-60:].astype(np.float32)
    
    # Scale using the loaded scaler
    x_scaled = predictor.scaler.transform(data)
    x_scaled = np.expand_dims(x_scaled, axis=0)
    
    forecasts = predictor.predict(x_scaled, return_original_scale=True)
    
    print(f"Forecasts shape: {forecasts.shape}")
    print(f"Forecast for next 2 timesteps:")
    print(forecasts[0])
