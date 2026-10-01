from __future__ import annotations

import torch
from torch import nn

from .depth_head import DepthHead
from .cdcn_official import OfficialCDCN


class OfficialCDCNWithDepthHead(nn.Module):
    def __init__(self, theta: float = 0.7) -> None:
        super().__init__()
        self.backbone = OfficialCDCN(theta)
        self.head = DepthHead()

    def train(self, mode: bool = True):
        super().train(mode)
        if not any(parameter.requires_grad for parameter in self.backbone.parameters()):
            self.backbone.eval()
        return self

    def forward(self, image: torch.Tensor) -> dict[str, torch.Tensor]:
        depth = self.backbone(image)["depth"]
        logit = self.head(depth)
        return {"depth": depth, "logit": logit, "score": torch.sigmoid(logit)}
