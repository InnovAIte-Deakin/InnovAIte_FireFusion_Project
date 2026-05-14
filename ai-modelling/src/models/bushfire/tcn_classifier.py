"""
FireFusion — TCN Classifier Architecture
=========================================
Location : src/models/bushfire/tcn_classifier.py

Defines the TCN model architecture only.
No data loading, no training logic, no config constants.

Imported by:
    src/training/train_classifier.py
    src/models/bushfire/classification_inference.py
"""

from dataclasses import dataclass, field
import torch
import torch.nn as nn


@dataclass
class ClassifierConfig:
    """
    All architecture hyperparameters in one place.
    Pass an instance of this to TCNClassifier.__init__.

    Dilations are auto-set as dilation_base^i per block:
        6 blocks, base=2 → dilations 1, 2, 4, 8, 16, 32
        Receptive field = 2 * (kernel_size-1) * sum(dilations) = 252 steps
    """
    n_features:    int        = 7
    lookback_steps: int       = 60
    channels:      list       = field(default_factory=lambda: [64, 64, 64, 64, 64, 64])
    kernel_size:   int        = 3
    dilation_base: int        = 2
    dropout:       float      = 0.2


class CausalConv1d(nn.Module):
    """
    Dilated causal convolution.
    Left-pads only — future timesteps are never seen by the model.
    """
    def __init__(self, in_ch: int, out_ch: int, kernel_size: int, dilation: int):
        super().__init__()
        self.padding = (kernel_size - 1) * dilation
        self.conv    = nn.Conv1d(
            in_ch, out_ch, kernel_size,
            padding=0, dilation=dilation
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.conv(nn.functional.pad(x, (self.padding, 0)))


class TCNBlock(nn.Module):
    """
    Residual dilated TCN block:
        CausalConv → BatchNorm → ReLU → Dropout  (×2)
        + residual 1×1 conv if channel dimensions differ
    """
    def __init__(self, in_ch: int, out_ch: int,
                 kernel_size: int, dilation: int, dropout: float):
        super().__init__()
        self.conv1 = CausalConv1d(in_ch,  out_ch, kernel_size, dilation)
        self.conv2 = CausalConv1d(out_ch, out_ch, kernel_size, dilation)
        self.norm1 = nn.BatchNorm1d(out_ch)
        self.norm2 = nn.BatchNorm1d(out_ch)
        self.relu  = nn.ReLU()
        self.drop  = nn.Dropout(dropout)
        self.residual_conv = (
            nn.Conv1d(in_ch, out_ch, 1) if in_ch != out_ch else nn.Identity()
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        res = self.residual_conv(x)
        out = self.drop(self.relu(self.norm1(self.conv1(x))))
        out = self.drop(self.relu(self.norm2(self.conv2(out))))
        return self.relu(out + res)


class TCNClassifier(nn.Module):
    """
    Full TCN for binary fire occurrence classification.

    Single-step input/output (used during training):
        Input  : (B*H*W, lookback, n_features)  — spatial dims flattened into batch
        Output : (B*H*W, 1)                     — fire probability per cell

    Multi-step inference (horizon loop, used at inference time):
        Input  : (B*H*W, lookback, n_features)
        Output : (B*H*W, horizon, 1)            — probability per cell per forecast step
                 where horizon=2 matches the 2-timestep forecast convention

    The spatial flatten (B, H, W → B*H*W) is the caller's responsibility —
    this model classifies one cell at a time and is unaware of grid topology.

    Architecture:
        Permute input to (B*H*W, n_features, lookback) for Conv1d
        → Stack of TCNBlock (exponentially increasing dilation)
        → AdaptiveAvgPool1d (collapse time dimension)
        → Linear(32) → ReLU → Dropout
        → Linear(1)  → Sigmoid
    """
    def __init__(self, config: ClassifierConfig = None, horizon: int = 1):
        super().__init__()
        if config is None:
            config = ClassifierConfig()

        self.config  = config
        self.horizon = horizon
        layers, in_ch = [], config.n_features

        for i, out_ch in enumerate(config.channels):
            dilation = config.dilation_base ** i
            layers.append(
                TCNBlock(in_ch, out_ch, config.kernel_size, dilation, config.dropout)
            )
            in_ch = out_ch

        self.tcn  = nn.Sequential(*layers)
        self.pool = nn.AdaptiveAvgPool1d(1)
        self.head = nn.Sequential(
            nn.Flatten(),
            nn.Linear(config.channels[-1], 32),
            nn.ReLU(),
            nn.Dropout(config.dropout),
            nn.Linear(32, 1),
            nn.Sigmoid(),
        )

    def _forward_single(self, x: torch.Tensor) -> torch.Tensor:
        """
        Classify one window of shape (B*H*W, lookback, n_features).
        Returns (B*H*W, 1).
        """
        x = x.permute(0, 2, 1)   # → (B*H*W, n_features, lookback)
        x = self.tcn(x)           # → (B*H*W, channels, lookback)
        x = self.pool(x)          # → (B*H*W, channels, 1)
        return self.head(x)       # → (B*H*W, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        
        if self.horizon == 1: ### CHANGE from 1 - 2 STEPS
            return self._forward_single(x)

        # x: (B*H*W, lookback + horizon - 1, n_features) to allow window sliding
        steps = []
        for t in range(self.horizon):
            window = x[:, t : t + self.config.lookback_steps, :]  # (B*H*W, lookback, n_features)
            steps.append(self._forward_single(window))             # (B*H*W, 1)

        return torch.stack(steps, dim=1)  # → (B*H*W, horizon, 1)

    def parameter_count(self) -> int:
        return sum(p.numel() for p in self.parameters())

    def receptive_field(self) -> int:
        cfg = self.config
        return 2 * (cfg.kernel_size - 1) * sum(
            cfg.dilation_base ** i for i in range(len(cfg.channels))
        )
