"""
Bushfire fire-risk pipeline template.

This module composes:
1) a multivariate time-series forecaster, and
2) a risk classifier (levels 1-5).

Flow:
historical features -> forecast future features -> classify risk level
"""

from dataclasses import dataclass
from typing import Optional, Tuple

import torch
from torch import Tensor, nn

from .risk_classifier import BushfireRiskClassifier, RiskClassifierConfig
from .ts_forecaster import ForecasterConfig, MultivariateTSForecaster


@dataclass
class FireRiskPipelineConfig:
    """Pipeline-level config that wires forecaster and classifier configs."""
    forecaster: ForecasterConfig
    classifier: RiskClassifierConfig


class FireRiskPipeline(nn.Module):
    """
    End-to-end bushfire risk model wrapper.

    Expected input:
        x_hist: Tensor [B, T, F]  (historical multivariate sequence)

    Intermediate:
        x_forecast: Tensor [B, H, F'] from forecaster

    Output:
        logits: Tensor [B, C] where C=5 by default
    """

    def __init__(
        self,
        config: FireRiskPipelineConfig,
        forecaster: Optional[MultivariateTSForecaster] = None,
        classifier: Optional[BushfireRiskClassifier] = None,
    ) -> None:
        super().__init__()
        self.config = config

        # Allow dependency injection for testing/experimentation.
        self.forecaster = forecaster or MultivariateTSForecaster(config.forecaster)
        self.classifier = classifier or BushfireRiskClassifier(config.classifier)

    def forward(self, x_hist: Tensor) -> Tensor:
        """
        Forward pass: historical features -> forecast -> classification logits.
        """
        x_forecast = self.forecaster(x_hist)      # [B, H, F']
        logits = self.classifier(x_forecast)      # [B, C]
        return logits

    def predict_proba(self, x_hist: Tensor) -> Tensor:
        """Return risk class probabilities [B, C]."""
        self.eval()
        with torch.no_grad():
            logits = self.forward(x_hist)
            return torch.softmax(logits, dim=-1)

    def predict_label(self, x_hist: Tensor) -> Tensor:
        """Return predicted risk labels in range 1..5 as tensor [B]."""
        probs = self.predict_proba(x_hist)
        class_idx = torch.argmax(probs, dim=-1)
        return class_idx + 1
    
    def predict_with_forecast(self, x_hist: Tensor) -> Tuple[Tensor, Tensor]:
        """
        Helper for debugging/analysis:
        returns (forecasted_features, logits).
        """
        self.eval()
        with torch.no_grad():
            x_forecast = self.forecaster(x_hist)
            logits = self.classifier(x_forecast)
        return x_forecast, logits