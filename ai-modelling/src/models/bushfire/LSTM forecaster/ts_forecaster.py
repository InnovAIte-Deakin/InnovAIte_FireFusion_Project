"""
LSTM-based Multivariate Time-Series Forecaster
 
Defines an LSTM architecture for forecasting multiple environmental
variables simultaneously. Supports configurable hidden sizes, dropout, and
flexible input/output dimensions.
 
Architecture:
    - Layer 1: LSTM (input_size -> hidden_size_1)
    - Dropout
    - Layer 2: LSTM (hidden_size_1 -> hidden_size_2)
    - Dropout
    - Linear Projection (hidden_size_2 -> horizon * output_size)
    - Reshape to [batch, horizon, output_size]
"""
from dataclasses import dataclass
from typing import Optional
import torch
from torch import Tensor, nn

@dataclass
class ForecasterConfig:
    """
    Configuration dataclass for the LSTM multivariate time-series forecaster.
    
    Attributes:
        input_size (int): Number of input features (multivariate dimension).
            
        horizon (int): Number of future timesteps to forecast.
            
        output_size (Optional[int]): Number of output features. If None, defaults to input_size.
            
        hidden_size_1 (int): Hidden dimension of first LSTM layer.
            
        hidden_size_2 (int): Hidden dimension of second LSTM layer.
            
        dropout (float): Dropout probability applied after each LSTM layer.
    """
    input_size: int
    horizon: int
    output_size: Optional[int] = None
    hidden_size_1: int = 64
    hidden_size_2: int = 32
    dropout: float = 0.2

class MultivariateTSForecaster(nn.Module):
    """
    LSTM multivariate time-series forecasting model.
    
    Learns patterns from historical sequences to predict future values of
    multiple variables simultaneously. Uses two stacked LSTM layers with
    dropout regularization.

    Inputs:
        x: [batch_size, seq_len, input_size]

    Outputs:
        y_hat: [batch_size, horizon, output_size]
    """
    def __init__(self, config: ForecasterConfig) -> None:
        """
        Initialize the LSTM forecaster with the given configuration.
        
        Constructs a two-layer LSTM with dropout regularization and a
        linear projection head for forecasting.
        
        Inputs:
            config (ForecasterConfig): Model configuration specifying
                - input_size: Number of input features
                - horizon: Forecast horizon
                - output_size: Number of output features (defaults to input_size)
                - hidden_size_1: Hidden dimension of first LSTM
                - hidden_size_2: Hidden dimension of second LSTM
                - dropout: Dropout probability
        """
        super().__init__()
        self.config = config
        self.input_size = config.input_size
        self.horizon = config.horizon
        self.output_size = config.output_size or config.input_size
        self.lstm1 = nn.LSTM(
            input_size=self.input_size,
            hidden_size=config.hidden_size_1,
            batch_first=True
        )

        self.dropout1 = nn.Dropout(config.dropout)
        self.lstm2 = nn.LSTM(
            input_size=config.hidden_size_1,
            hidden_size=config.hidden_size_2,
            batch_first=True
        )

        self.dropout2 = nn.Dropout(config.dropout)
        self.projection = nn.Linear(
            config.hidden_size_2,
            self.horizon * self.output_size
        )

    def forward(self, x: Tensor) -> Tensor:
        """
        Forward pass through the LSTM forecaster.
        
        Processes input sequences through two stacked LSTM layers, extracts
        the final hidden state, applies dropout, and projects to forecast.
        
        Processing Steps:
            1. Input sequence through LSTM1: [B, T, F] -> [B, T, H1]
            2. Apply dropout
            3. Sequence through LSTM2: [B, T, H1] -> [B, T, H2]
            4. Extract final timestep: [B, T, H2] -> [B, H2]
            5. Apply dropout
            6. Linear projection: [B, H2] -> [B, H*O]
            7. Reshape: [B, H*O] -> [B, H, O]
        
        Inputs:
            x (Tensor): Input sequence of shape [batch_size, seq_len, input_size]
        
        Outputs:
            Tensor: Forecast of shape [batch_size, horizon, output_size]
        """
        # First LSTM returns full sequence:
        # [B, T, F] -> [B, T, 64]
        x, _ = self.lstm1(x)
        x = self.dropout1(x)

        # Second LSTM also returns sequence:
        # [B, T, 64] -> [B, T, 32]
        x, _ = self.lstm2(x)

        x = x[:, -1, :]
        x = self.dropout2(x)

        # Project to horizon * output_size:
        # [B, 32] -> [B, H * O]
        x = self.projection(x)

        # Reshape:
        # [B, H * O] -> [B, H, O]
        y_hat = x.view(-1, self.horizon, self.output_size)
        return y_hat

    def predict(self, x: Tensor) -> Tensor:
        """
        Generate predictions without computing gradients.
        
        Wrapper around forward() that sets the model to evaluation mode
        and disables gradient computation for efficiency during inference.
        
        Inputs:
            x (Tensor): Input sequence of shape [batch_size, seq_len, input_size]
        
        Outputs:
            Tensor: Forecast of shape [batch_size, horizon, output_size]
        """
        self.eval()
        with torch.no_grad():
            return self.forward(x)

    def save(self, path: str) -> None:
        """
        Save the model checkpoint to disk.
        
        Saves both model weights (state_dict) and configuration to enable
        complete model reconstruction during loading.
        
        Args:
            path (str): Path where to save the checkpoint (.pth file).
        """
        torch.save(
            {
                "model_state_dict": self.state_dict(),
                "config": self.config,
            },
            path
        )

    @classmethod
    def load(cls, path: str, map_location: Optional[str] = None):
        """
        Load a trained model from a checkpoint file.
        
        Reconstructs the model architecture from saved configuration and
        restores trained weights. Automatically sets model to evaluation mode.
        
        Inputs:
            path (str): Path to the model checkpoint (.pth file).
                
            map_location (Optional[str]): Device to load the model onto.
        
        Outputs:
            MultivariateTSForecaster: Loaded model in evaluation mode, ready for inference.
        
        Raises:
            FileNotFoundError: If checkpoint file doesn't exist
            RuntimeError: If checkpoint is corrupted or incompatible
        """
        checkpoint = torch.load(path, map_location=map_location, weights_only=False)
        model = cls(checkpoint["config"])
        model.load_state_dict(checkpoint["model_state_dict"])
        model.eval()
        return model