"""Shared 2D ConvLSTM cell used by the forecaster and its optional layers."""
from typing import Optional, Tuple

import torch
from torch import Tensor, nn

from .attention import PatchwiseAttention2d

class ConvLSTMCell(nn.Module):
    """2D ConvLSTM cell for spatiotemporal data."""

    def __init__(self, input_channels: int, hidden_channels: int, kernel_size: int = 3, attention: str = "none", footprint: int = 7, dilation: int = 1, share_planes: int = 8) -> None:
        super().__init__()
        self.input_channels = input_channels
        self.hidden_channels = hidden_channels
        self.attention = attention
        padding = kernel_size // 2

        combined_channels = input_channels + hidden_channels
        gate_channels = 4 * hidden_channels

        if attention == "patchwise":
            self.conv = PatchwiseAttention2d(
                in_channels=combined_channels,
                out_channels=gate_channels,
                footprint=footprint,
                dilation=dilation,
                share_planes=share_planes,
            )
        elif attention == "none":
            self.conv = nn.Conv2d(
                combined_channels,
                gate_channels,
                kernel_size,
                padding=padding,
            )
        else:
            raise ValueError(
                f"Unsupported attention mode: {attention!r}. "
                "Expected 'none' or 'patchwise'."
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
