from __future__ import annotations

import torch
from torch import nn


class DepthHead(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.layers = nn.Sequential(nn.Conv2d(1, 8, 3, padding=1), nn.ReLU(inplace=True), nn.Conv2d(8, 16, 3, padding=1), nn.ReLU(inplace=True), nn.AdaptiveAvgPool2d(1))
        self.classifier = nn.Linear(16, 1)

    def forward(self, depth: torch.Tensor) -> torch.Tensor:
        return self.classifier(self.layers(depth).flatten(1)).flatten()
