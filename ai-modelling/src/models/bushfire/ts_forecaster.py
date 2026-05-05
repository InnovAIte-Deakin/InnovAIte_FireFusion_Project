"""
Time-series forecaster for bushfire risk inputs.

This module defines the forecasting component that predicts future values of
weather/environmental features (e.g., temperature, wind, humidity, dryness)
over a prediction horizon. The output forecasts are designed to be consumed by
the downstream risk classifier in `fire_risk_pipeline.py`.

Initial scope:
- Define the forecaster class interface (fit, predict, save, load)
- Standardize expected input/output tensor or dataframe shapes
- Provide a simple baseline forecasting strategy before advanced models
"""

"""
Multivariate time-series forecaster template.

This is intentionally architecture-agnostic.
Team members can implement layers and forecasting strategy later.
"""
from dataclasses import dataclass
from typing import Optional

import torch
from torch import Tensor, nn


@dataclass
class ForecasterConfig:
    """Configuration placeholder for model architecture and training assumptions."""
    input_size: int                 # Number of input features per timestep
    horizon: int                    # Number of timesteps to forecast
    output_size: Optional[int] = None  # Defaults to input_size when None


class MultivariateTSForecaster(nn.Module):
    """
    Empty template for a multivariate time-series forecasting model.

    Expected input:
        x: Tensor of shape [batch_size, seq_len, input_size]

    Expected output:
        y_hat: Tensor of shape [batch_size, horizon, output_size]
    """

    def __init__(self, config: ForecasterConfig) -> None:
        super().__init__()
        self.config = config
        self.input_size = config.input_size
        self.horizon = config.horizon
        self.output_size = config.output_size or config.input_size

        # TODO: Add model layers here
        # Example placeholders:
        # self.encoder = ...
        # self.decoder = ...
        # self.projection = ...

    def forward(self, x: Tensor) -> Tensor:
        """
        Forward pass for forecasting.

        Args:
            x: Historical multivariate sequence [B, T, F]

        Returns:
            Forecasted sequence [B, H, O]
        """
        # TODO: Implement forward pass once architecture is chosen.
        raise NotImplementedError("Implement model architecture and forward pass.")

    def predict(self, x: Tensor) -> Tensor:
        """Inference helper wrapper."""
        self.eval()
        with torch.no_grad():
            return self.forward(x)