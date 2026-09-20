from __future__ import annotations

import torch
from torch import nn
from torchvision.models import MobileNet_V3_Small_Weights, mobilenet_v3_small


class MobileNetBaseline(nn.Module):
    def __init__(self, pretrained: bool = True) -> None:
        super().__init__()
        weights = MobileNet_V3_Small_Weights.DEFAULT if pretrained else None
        self.model = mobilenet_v3_small(weights=weights)
        self.model.classifier[-1] = nn.Linear(self.model.classifier[-1].in_features, 1)

    def forward(self, image: torch.Tensor) -> dict[str, torch.Tensor]:
        return {"logit": self.model(image).flatten()}
