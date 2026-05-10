"""
Bushfire risk level classifier (classes 1-5).

This module defines the classification component that takes forecasted
time-series features and predicts a discrete bushfire risk level from 1 to 5.
It serves as the second stage of the bushfire modelling pipeline after
`ts_forecaster.py`.

Initial scope:
- Define classifier interface (fit, predict, predict_proba, save, load)
- Map model outputs to risk labels 1-5
- Provide baseline classification behavior and evaluation-ready outputs
"""

from dataclasses import dataclass
from typing import Dict

import torch
from torch import Tensor, nn

@dataclass
class RiskClassifierConfig:
    """Configuration placeholder for classifier architecture."""
    input_size: int          # Number of features per timestep
    horizon: int             # Number of forecast timesteps used as input
    num_classes: int = 5     # Risk classes: 1..5

class BushfireRiskClassifier(nn.Module):
    """
    Empty template for bushfire risk level classification.
    Expected input:
        x: Tensor of shape [batch_size, horizon, input_size]
    Expected output:
        logits: Tensor of shape [batch_size, num_classes]
    """
    def __init__(self, config: RiskClassifierConfig) -> None:
        super().__init__()
        self.config = config
        self.input_size = config.input_size
        self.horizon = config.horizon
        self.num_classes = config.num_classes
        # Class index -> risk label mapping (0-based index to 1..5)
        self.class_to_risk: Dict[int, int] = {
            i: i + 1 for i in range(self.num_classes)
        }
        # TODO: Add classifier layers here
        # Example placeholders:
        # self.encoder = ...
        # self.classifier_head = ...
    
    def forward(self, x: Tensor) -> Tensor:
        """
        Forward pass for classification.
        Args:
            x: Forecast feature sequence [B, H, F]
        Returns:
            Logits [B, C]
        """
        # TODO: Implement forward pass once architecture is chosen.
        raise NotImplementedError("Implement classifier architecture and forward pass.")
    
    def predict_proba(self, x: Tensor) -> Tensor:
        """Return class probabilities [B, C]."""
        self.eval()
        with torch.no_grad():
            logits = self.forward(x)
            return torch.softmax(logits, dim=-1)
    
    def predict_label(self, x: Tensor) -> Tensor:
        """
        Return predicted risk labels in range (1, 5) as tensor [B].
        """
        probs = self.predict_proba(x)
        class_idx = torch.argmax(probs, dim=-1)
        return class_idx + 1