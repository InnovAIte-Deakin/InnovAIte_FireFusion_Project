"""
Bushfire risk classifier: optional 2D conv stem on (H, W), then SGN per grid cell.

Option A per lead: sequence is ``history + one forecast step`` when ``history_steps > 0``,
otherwise forecast-only ``[B, 1, H, W, C]`` per lead. All leads run in parallel by
concatenating on the batch dimension, one ``SGN`` forward, reshaped to
``[B, horizon, H, W, num_classes]``.
"""

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Dict, List, Optional, Tuple

import torch
from torch import Tensor, nn

from .SGN import Model


@dataclass
class RiskClassifierConfig:
    """Wires SGN to ConvLSTM outputs."""

    history_steps: int
    forecast_horizon: int
    in_channels: int
    out_channels: int
    num_classes: int = 2

    num_groups: int = 4
    d_model: int = 32
    e_layers: int = 2
    depths: Tuple[int, ...] = (2, 2)
    period: int = 1
    block_num: int = 1
    kernel_size: int = 3
    num_kernels: int = 4
    mlp_ratio: int = 2
    dropout: float = 0.1
    embed: str = "timeF"
    freq: str = "h"

    groups_matrix_path: Optional[str] = None
    groups_matrix_tensor: Optional[Tensor] = None

    use_spatial_stem: bool = False
    stem_hidden: int = 32


class BushfireRiskClassifier(nn.Module):
    """
    x_hist: [B, T, H, W, C_in] — only used when history_steps > 0.
    y_forecast: [B, horizon, H, W, C_out] from ConvLSTM.

    Returns logits [B, horizon, H, W, num_classes] (softmax in pipeline or predict_proba).
    """

    def __init__(self, config: RiskClassifierConfig) -> None:
        super().__init__()
        self.config = config
        self.history_steps = config.history_steps
        self.num_classes = config.num_classes

        if config.history_steps < 0:
            raise ValueError("history_steps must be >= 0")

        self.sgn_seq_len = config.history_steps + 1
        self.sgn_channels = config.out_channels

        if config.history_steps > 0 and config.in_channels != config.out_channels:
            self.channel_align = nn.Conv2d(
                config.in_channels, config.out_channels, kernel_size=1, bias=True
            )
        else:
            self.channel_align = None

        if config.use_spatial_stem:
            self.spatial_stem = nn.Sequential(
                nn.Conv2d(config.out_channels, config.stem_hidden, kernel_size=3, padding=1, bias=False),
                nn.BatchNorm2d(config.stem_hidden),
                nn.GELU(),
                nn.Conv2d(config.stem_hidden, config.out_channels, kernel_size=3, padding=1, bias=False),
                nn.BatchNorm2d(config.out_channels),
                nn.GELU(),
            )
        else:
            self.spatial_stem = None

        if len(config.depths) != config.e_layers:
            raise ValueError("depths length must equal e_layers")

        sgn_cfg = SimpleNamespace(
            task_name="classification",
            num_class=config.num_classes,
            enc_in=self.sgn_channels,
            seq_len=self.sgn_seq_len,
            e_layers=config.e_layers,
            depths=list(config.depths),
            period=config.period,
            num_groups=config.num_groups,
            d_model=config.d_model,
            block_num=config.block_num,
            kernel_size=config.kernel_size,
            num_kernels=config.num_kernels,
            mlp_ratio=config.mlp_ratio,
            dropout=config.dropout,
            embed=config.embed,
            freq=config.freq,
            groups_matrix_path=config.groups_matrix_path,
            groups_matrix_tensor=config.groups_matrix_tensor,
        )
        self.sgn = Model(sgn_cfg)

        self.class_to_risk: Dict[int, int] = {i: i + 1 for i in range(self.num_classes)}

    def _align_recent_history(self, x_hist: Tensor) -> Tensor:
        B, Th, H, W, _ = x_hist.shape
        if Th < self.history_steps:
            raise ValueError(f"x_hist length {Th} < history_steps {self.history_steps}")
        recent = x_hist[:, -self.history_steps :, :, :, :]
        if self.channel_align is not None:
            b, t, h, w, c = recent.shape
            recent = self.channel_align(recent.reshape(b * t, c, h, w)).reshape(
                b, t, h, w, self.config.out_channels
            )
        return recent

    def _apply_spatial_stem(self, x: Tensor) -> Tensor:
        if self.spatial_stem is None:
            return x
        b, l, h, w, c = x.shape
        return self.spatial_stem(x.reshape(b * l, c, h, w)).reshape(b, l, h, w, c)

    def _build_step_sequence(self, recent: Optional[Tensor], y_forecast: Tensor, step: int) -> Tensor:
        step_slice = y_forecast[:, step : step + 1, :, :, :]
        if self.history_steps == 0:
            x = step_slice
        else:
            assert recent is not None
            x = torch.cat([recent, step_slice], dim=1)
        return self._apply_spatial_stem(x)

    def forward(self, x_hist: Tensor, y_forecast: Tensor) -> Tensor:
        logits, _ = self.forward_with_aux(x_hist, y_forecast)
        return logits

    def forward_with_aux(self, x_hist: Tensor, y_forecast: Tensor) -> Tuple[Tensor, Tensor]:
        horizon = y_forecast.shape[1]
        if horizon != self.config.forecast_horizon:
            raise ValueError(
                f"y_forecast has horizon {horizon}, expected {self.config.forecast_horizon}"
            )
        if horizon < 1:
            raise ValueError("forecast horizon must be >= 1")

        if y_forecast.shape[-1] != self.config.out_channels:
            raise ValueError(
                f"y_forecast channels {y_forecast.shape[-1]} != out_channels {self.config.out_channels}"
            )

        recent: Optional[Tensor] = None
        if self.history_steps > 0:
            recent = self._align_recent_history(x_hist)

        per_lead: List[Tensor] = []
        for s in range(horizon):
            x = self._build_step_sequence(recent, y_forecast, s)
            B, L, H, W, C = x.shape
            if L != self.sgn_seq_len:
                raise ValueError(f"SGN sequence length {L} != {self.sgn_seq_len}")
            per_lead.append(x)

        x_cat = torch.cat(per_lead, dim=0)
        B, L, Hg, Wg, C = x_cat.shape
        B_each = B // horizon
        x_seq = x_cat.permute(0, 2, 3, 1, 4).reshape(B * Hg * Wg, L, C)
        logits_flat, embed_loss = self.sgn(x_seq, None, None, None)
        logits = logits_flat.view(B_each, horizon, Hg, Wg, self.num_classes)

        if embed_loss is None:
            embed_mean = logits.new_zeros(())
        else:
            embed_mean = embed_loss

        return logits, embed_mean

    def predict_proba(self, x_hist: Tensor, y_forecast: Tensor) -> Tensor:
        self.eval()
        with torch.no_grad():
            return torch.softmax(self.forward(x_hist, y_forecast), dim=-1)

    def predict_label(self, x_hist: Tensor, y_forecast: Tensor) -> Tensor:
        probs = self.predict_proba(x_hist, y_forecast)
        return torch.argmax(probs, dim=-1) + 1