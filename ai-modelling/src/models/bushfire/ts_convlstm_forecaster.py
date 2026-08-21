"""
2D ConvLSTM-based Spatiotemporal Forecaster
 
Defines a 2D ConvLSTM architecture that uses environmental variables to
forecast the probability that each grid cell is burning at the next timestep. Supports configurable input channels, hidden sizes, and dropout, with a
single output channel for the 'is burning' probability.
 
Architecture:
    - Layer 1: ConvLSTM2d (input_channels -> hidden_size_1)
    - Dropout2d
    - Layer 2: ConvLSTM2d (hidden_size_1 -> hidden_size_2)
    - Dropout2d
    - Optional shared per-cell BiLSTM temporal layer
    - Conv2d Projection (temporal features -> horizon * output_channels)
    - Reshape to [batch, horizon, height, width, output_channels]
"""
from dataclasses import dataclass
from typing import Optional, Tuple
import torch
from torch import Tensor, nn

from .bilstm import PerCellBiLSTMLayer

@dataclass
class ForecasterConfig:
    """
    Configuration dataclass for the 2D ConvLSTM spatiotemporal forecaster.
    
    Attributes:
        input_channels (int): Number of input features per grid cell.
        horizon (int): Number of future timesteps to forecast.
        output_channels (int): Number of output features. Defaults to 1 for the 'is burning' output.
        hidden_size_1 (int): Hidden dimension of first ConvLSTM2d layer.
        hidden_size_2 (int): Hidden dimension of second ConvLSTM2d layer.
        dropout (float): Dropout probability applied after each ConvLSTM2d layer.
        use_bilstm (bool): Whether to apply the shared per-cell BiLSTM layer.
        bilstm_hidden_size (int): Hidden dimension per BiLSTM direction.
    """
    input_channels: int
    horizon: int = 1
    output_channels: int = 1
    hidden_size_1: int = 32
    hidden_size_2: int = 16
    dropout: float = 0.2
    use_bilstm: bool = False
    bilstm_hidden_size: int = 8


class ConvLSTMCell(nn.Module):
    """2D ConvLSTM cell for spatiotemporal data."""
    
    def __init__(self, input_channels: int, hidden_channels: int, kernel_size: int = 3) -> None:
        super().__init__()
        self.input_channels = input_channels
        self.hidden_channels = hidden_channels
        padding = kernel_size // 2
        
        self.conv = nn.Conv2d(
            input_channels + hidden_channels,
            4 * hidden_channels,
            kernel_size,
            padding=padding
        )
    
    def forward(self, x: Tensor, states: Optional[Tuple[Tensor, Tensor]] = None) -> Tuple[Tensor, Tuple[Tensor, Tensor]]:
        """Forward pass of ConvLSTM2d cell."""
        if states is None:
            h = torch.zeros(x.size(0), self.hidden_channels, x.size(2), x.size(3), device=x.device, dtype=x.dtype)
            c = torch.zeros(x.size(0), self.hidden_channels, x.size(2), x.size(3), device=x.device, dtype=x.dtype)
        else:
            h, c = states
        
        combined = torch.cat([x, h], dim=1)
        gates = self.conv(combined)
        i, f, g, o = torch.split(gates, self.hidden_channels, dim=1)
        
        i = torch.sigmoid(i)
        f = torch.sigmoid(f)
        g = torch.tanh(g)
        o = torch.sigmoid(o)
        
        c_new = f * c + i * g
        h_new = o * torch.tanh(c_new)
        
        return h_new, (h_new, c_new)


class MultivariateTSForecaster(nn.Module):
    """
    2D ConvLSTM spatiotemporal forecasting model.
    
    Learns patterns from gridded historical sequences to predict the probability
    that each grid cell is burning at the next timestep. Uses two stacked
    ConvLSTM2d layers and can optionally apply a shared BiLSTM independently to
    each grid cell before the output projection.

    Inputs:
        x: [batch_size, seq_len, height, width, input_channels]

    Outputs:
        y_hat: Raw logits of shape [batch_size, horizon, height, width, output_channels]
    """
    def __init__(self, config: ForecasterConfig) -> None:
        """
        Initialize the 2D ConvLSTM forecaster with the input configuration.
        
        Constructs a two-layer ConvLSTM2d with dropout regularization and a
        convolutional projection head for forecasting.
        
        Inputs:
            config (ForecasterConfig): Model configuration specifying
                - input_channels: Number of input features
                - horizon: Forecast horizon
                - output_channels: Number of output channels (defaults to 1)
                - hidden_size_1: Hidden dimension of first ConvLSTM2d
                - hidden_size_2: Hidden dimension of second ConvLSTM2d
                - use_bilstm: Whether to enable the per-cell BiLSTM
                - bilstm_hidden_size: Hidden size per BiLSTM direction
                - dropout: Dropout probability
        """
        super().__init__()
        self.config = config
        self.input_channels = config.input_channels
        self.horizon = config.horizon
        self.output_channels = config.output_channels
        self.use_bilstm = config.use_bilstm
        
        self.convlstm1 = ConvLSTMCell(
            input_channels=self.input_channels,
            hidden_channels=config.hidden_size_1
        )
        self.dropout1 = nn.Dropout2d(config.dropout)
        
        self.convlstm2 = ConvLSTMCell(
            input_channels=config.hidden_size_1,
            hidden_channels=config.hidden_size_2
        )
        self.dropout2 = nn.Dropout2d(config.dropout)

        if self.use_bilstm:
            self.bilstm = PerCellBiLSTMLayer(
                input_size=config.hidden_size_2,
                hidden_size=config.bilstm_hidden_size,
            )
            projection_input_channels = self.bilstm.output_size
        else:
            self.bilstm = None
            projection_input_channels = config.hidden_size_2
        
        self.projection = nn.Conv2d(
            projection_input_channels,
            self.horizon * self.output_channels,
            kernel_size=1
        )

    def forward(self, x: Tensor) -> Tensor:
        """
        Forward pass through the 2D ConvLSTM forecaster.
        
        Processes input grid sequences through two stacked ConvLSTM2d layers,
        optionally applies the imported per-cell BiLSTM layer, and projects to
        the configured prediction horizon.
        
        Processing Steps:
            1. Reshape input
            2. Process timesteps through ConvLSTM1
            3. Apply dropout
            4. Process through ConvLSTM2
            5. Apply dropout
            6. Optionally apply the shared per-cell BiLSTM
            7. Conv2d projection
            8. Reshape
        
        Inputs:
            x (Tensor): Input grid sequence of shape [batch_size, seq_len, height, width, input_channels]
        
        Outputs:
            y_hat (Tensor): Raw 'is burning' logits of shape [batch_size, 1, height, width, 1].
        """
        if x.ndim != 5:
            raise ValueError(
                "Expected input with shape [batch, time, height, width, channels], "
                f"but received {tuple(x.shape)}."
            )

        batch_size, seq_len, grid_height, grid_width, input_channels = x.shape

        if seq_len < 1:
            raise ValueError("Input sequence must contain at least one timestep.")

        if input_channels != self.input_channels:
            raise ValueError(
                "Input channel count does not match the model configuration. "
                f"Expected {self.input_channels} channels, but received {input_channels}."
            )
    
        # Reshape
        x = x.permute(0, 1, 4, 2, 3)
        
        # First ConvLSTM2d processes all timesteps
        h1_state = None
        h1_outputs = []
        for t in range(seq_len):
            h1, h1_state = self.convlstm1(x[:, t, :, :, :], h1_state)
            h1_outputs.append(h1)
        
        h1_outputs_dropped = [self.dropout1(h) for h in h1_outputs]
        
        # Second ConvLSTM2d processes first layer outputs
        h2_state = None
        h2_outputs = []
        for t in range(seq_len):
            h2, h2_state = self.convlstm2(h1_outputs_dropped[t], h2_state)

            if self.use_bilstm:
                h2_outputs.append(self.dropout2(h2))

        if self.bilstm is not None:
            # [B, T, hidden_size_2, H, W] -> [B, 2*bilstm_hidden_size, H, W]
            temporal_features = self.bilstm(torch.stack(h2_outputs, dim=1))
        else:
            temporal_features = self.dropout2(h2)
        
        # Project to horizon * output_channels:
        # [B, temporal_features, H, W] -> [B, H*O, H, W]
        proj = self.projection(temporal_features)
        
        # Reshape to [B, H, H, W, O]
        proj = proj.view(batch_size, self.horizon, self.output_channels, grid_height, grid_width)
        y_hat = proj.permute(0, 1, 3, 4, 2)
        
        return y_hat

    def predict(self, x: Tensor) -> Tensor:
        """
        Generate predictions without computing gradients.
        Wrapper around forward() that sets the model to evaluation mode
        and disables gradient computation.
        
        Inputs:
            x (Tensor): Input grid sequence of shape [batch_size, seq_len, height, width, input_channels]
        
        Outputs:
            y_hat (Tensor): Burning probabilities between 0 and 1 with shape [batch_size, 1, height, width, 1].
        """
        self.eval()
        with torch.no_grad():
            logits = self.forward(x)
            return torch.sigmoid(logits)

    def save(self, path: str) -> None:
        """
        Save the model checkpoint to disk.
        Saves both model weights (state_dict) and configuration to enable
        complete model reconstruction during loading.
        
        Inputs:
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
        
        Returns:
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
