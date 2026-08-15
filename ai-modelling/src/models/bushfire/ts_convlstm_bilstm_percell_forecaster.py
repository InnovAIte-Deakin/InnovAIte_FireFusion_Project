"""
2D ConvLSTM + Per-Cell BiLSTM Spatiotemporal Forecaster

Variant of ts_convlstm_forecaster.py that stacks a bidirectional LSTM after
both ConvLSTM2d layers, applied independently per grid cell with shared
weights across all cells (analogous to how ConvLSTM2d shares its
convolutional kernels spatially). This avoids the flatten-based approach in
ts_convlstm_bilstm_forecaster.py, whose per-timestep input size
(height * width * hidden_size_2) grows with grid size and produces an
impractically large parameter count at real grid dimensions.

Because the BiLSTM and the final projection are both applied per cell with
shared weights, neither depends on grid height/width: the same trained
instance can accept different grid sizes at inference time.

Architecture:
    - Layer 1: ConvLSTM2d (input_channels -> hidden_size_1)
    - Dropout2d
    - Layer 2: ConvLSTM2d (hidden_size_1 -> hidden_size_2), all timesteps kept
    - Dropout2d
    - Reshape [B, T, hidden_size_2, H, W] -> [B*H*W, T, hidden_size_2]
    - BiLSTM (bidirectional, shared weights across all cells)
    - Linear projection (2 * bilstm_hidden_size -> horizon * output_channels), per cell
    - Reshape to [batch, horizon, height, width, output_channels]
"""
from dataclasses import dataclass
from typing import Optional
import torch
from torch import Tensor, nn

from .ts_convlstm_forecaster import ConvLSTMCell


@dataclass
class PerCellBiLSTMForecasterConfig:
    """
    Configuration dataclass for the ConvLSTM + per-cell BiLSTM spatiotemporal
    forecaster.

    Unlike BiLSTMForecasterConfig (the flatten-based variant), this config has
    no grid_height/grid_width: the BiLSTM and the final projection are both
    applied per cell with weights shared across all cells, so no layer's size
    depends on the grid dimensions.

    Attributes:
        input_channels (int): Number of input features per grid cell.
        horizon (int): Number of future timesteps to forecast.
        output_channels (int): Number of output features.
        hidden_size_1 (int): Hidden dimension of first ConvLSTM2d layer.
        hidden_size_2 (int): Hidden dimension of second ConvLSTM2d layer.
        bilstm_hidden_size (int): Hidden dimension of the BiLSTM, per direction
            (i.e. the value passed to nn.LSTM(hidden_size=...)). Actual BiLSTM
            output width is 2 * bilstm_hidden_size (forward + backward).
        dropout (float): Dropout probability applied after each ConvLSTM2d layer.
    """
    input_channels: int
    horizon: int = 1
    output_channels: int = 1
    hidden_size_1: int = 32
    hidden_size_2: int = 16
    bilstm_hidden_size: int = 32
    dropout: float = 0.2


class MultivariateTSForecasterPerCellBiLSTM(nn.Module):
    """
    ConvLSTM + per-cell BiLSTM spatiotemporal forecasting model.

    Inputs:
        x: [batch_size, seq_len, height, width, input_channels]

    Outputs:
        y_hat: Raw logits of shape [batch_size, horizon, height, width, output_channels]
    """
    def __init__(self, config: PerCellBiLSTMForecasterConfig) -> None:
        super().__init__()
        self.config = config
        self.input_channels = config.input_channels
        self.horizon = config.horizon
        self.output_channels = config.output_channels

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

        # Shared across all cells: input_size is just hidden_size_2 (per-cell
        # feature count), not height * width * hidden_size_2. Grid size never
        # enters this layer's shape.
        self.bilstm = nn.LSTM(
            input_size=config.hidden_size_2,
            hidden_size=config.bilstm_hidden_size,
            batch_first=True,
            bidirectional=True,
        )

        # Also shared across all cells (equivalent to a Conv2d with
        # kernel_size=1, like the baseline's projection): maps each cell's
        # BiLSTM summary independently to horizon * output_channels values.
        self.projection = nn.Linear(
            2 * config.bilstm_hidden_size,
            self.horizon * self.output_channels,
        )

    def forward(self, x: Tensor) -> Tensor:
        """
        Forward pass through the ConvLSTM + per-cell BiLSTM forecaster.

        Processing Steps:
            1. Validate input
            2. Reshape input
            3. Process timesteps through ConvLSTM1
            4. Apply dropout
            5. Process through ConvLSTM2, keeping every timestep
            6. Apply dropout
            7. Reshape [B, T, C, H, W] -> [B*H*W, T, C] (per-cell sequences)
            8. BiLSTM over each cell's sequence, weights shared across cells
            9. Concatenate final forward/backward hidden states
            10. Linear projection, shared across cells
            11. Reconstruct grid and reshape to 5D

        Inputs:
            x (Tensor): Input grid sequence of shape [batch_size, seq_len, height, width, input_channels]

        Outputs:
            y_hat (Tensor): Raw logits of shape [batch_size, horizon, height, width, output_channels]
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

        # Second ConvLSTM2d processes first layer outputs, keeping every timestep
        h2_state = None
        h2_outputs = []
        for t in range(seq_len):
            h2, h2_state = self.convlstm2(h1_outputs_dropped[t], h2_state)
            h2_outputs.append(h2)

        h2_outputs_dropped = [self.dropout2(h) for h in h2_outputs]

        # Stack timesteps: [B, T, hidden_size_2, H, W]
        stacked = torch.stack(h2_outputs_dropped, dim=1)

        # Reshape to per-cell sequences: [B, H, W, T, hidden_size_2] -> [B*H*W, T, hidden_size_2]
        # Each row is one cell's own temporal sequence, never mixed with other cells.
        sequence = stacked.permute(0, 3, 4, 1, 2).reshape(
            batch_size * grid_height * grid_width, seq_len, -1
        )

        # BiLSTM over each cell's sequence, weights shared across all cells
        _, (h_n, _) = self.bilstm(sequence)

        # h_n: [num_directions, B*H*W, bilstm_hidden_size]
        # h_n[0] = forward direction final state (seen whole sequence forward)
        # h_n[1] = backward direction final state (seen whole sequence backward)
        summary = torch.cat([h_n[0], h_n[1]], dim=1)  # [B*H*W, 2 * bilstm_hidden_size]

        # Project to horizon * output_channels, shared across cells
        proj = self.projection(summary)  # [B*H*W, horizon * output_channels]

        # Reconstruct the grid and reshape to [B, horizon, H, W, output_channels]
        proj = proj.reshape(batch_size, grid_height, grid_width, self.horizon, self.output_channels)
        y_hat = proj.permute(0, 3, 1, 2, 4)

        return y_hat

    def predict(self, x: Tensor) -> Tensor:
        """
        Generate predictions without computing gradients.
        Wrapper around forward() that sets the model to evaluation mode
        and disables gradient computation.

        Inputs:
            x (Tensor): Input grid sequence of shape [batch_size, seq_len, height, width, input_channels]

        Outputs:
            y_hat (Tensor): Burning probabilities between 0 and 1 with shape [batch_size, horizon, height, width, output_channels].
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
            MultivariateTSForecasterPerCellBiLSTM: Loaded model in evaluation mode, ready for inference.

        Raises:
            FileNotFoundError: If checkpoint file doesn't exist
            RuntimeError: If checkpoint is corrupted or incompatible
        """
        checkpoint = torch.load(path, map_location=map_location, weights_only=False)
        model = cls(checkpoint["config"])
        model.load_state_dict(checkpoint["model_state_dict"])
        model.eval()
        return model
