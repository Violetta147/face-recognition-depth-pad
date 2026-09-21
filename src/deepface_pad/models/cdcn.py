from __future__ import annotations

import torch
from torch import nn
from torch.nn import functional as F


class CentralDifferenceConv2d(nn.Conv2d):
    def __init__(self, *args, theta: float = 0.7, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.theta = theta

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        normal = super().forward(x)
        if abs(self.theta) < 1e-8:
            return normal
        kernel_diff = self.weight.sum(dim=(2, 3), keepdim=True)
        central = F.conv2d(x, kernel_diff, bias=None, stride=self.stride, padding=0, dilation=1, groups=self.groups)
        if central.shape[-2:] != normal.shape[-2:]:
            central = F.interpolate(central, normal.shape[-2:], mode="nearest")
        return normal - self.theta * central


def _block(inputs: int, outputs: int, theta: float) -> nn.Sequential:
    return nn.Sequential(CentralDifferenceConv2d(inputs, outputs, 3, padding=1, theta=theta, bias=False), nn.BatchNorm2d(outputs), nn.ReLU(inplace=True))


class CDCN(nn.Module):
    """Legacy compact CDCN-style pilot; not the authors' full CDCN topology."""
    def __init__(self, theta: float = 0.7, base_channels: int = 32) -> None:
        super().__init__()
        c = base_channels
        self.encoder = nn.Sequential(
            _block(3, c, theta), nn.MaxPool2d(2),
            _block(c, c * 2, theta), nn.MaxPool2d(2),
            _block(c * 2, c * 4, theta), nn.MaxPool2d(2),
            _block(c * 4, c * 2, theta),
        )
        self.depth = nn.Sequential(nn.Conv2d(c * 2, 1, 1), nn.Sigmoid())

    def forward(self, image: torch.Tensor) -> dict[str, torch.Tensor]:
        feature = self.encoder(image)
        depth = self.depth(F.adaptive_avg_pool2d(feature, (32, 32)))
        return {"depth": depth, "score": depth.mean(dim=(1, 2, 3))}


class DepthHead(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.layers = nn.Sequential(nn.Conv2d(1, 8, 3, padding=1), nn.ReLU(inplace=True), nn.Conv2d(8, 16, 3, padding=1), nn.ReLU(inplace=True), nn.AdaptiveAvgPool2d(1))
        self.classifier = nn.Linear(16, 1)

    def forward(self, depth: torch.Tensor) -> torch.Tensor:
        return self.classifier(self.layers(depth).flatten(1)).flatten()


class CDCNMultiTaskLite(nn.Module):
    def __init__(self, theta: float = 0.7, base_channels: int = 32) -> None:
        super().__init__()
        self.backbone = CDCN(theta, base_channels)
        self.head = DepthHead()

    def forward(self, image: torch.Tensor) -> dict[str, torch.Tensor]:
        depth = self.backbone(image)["depth"]
        logit = self.head(depth)
        return {"depth": depth, "logit": logit, "score": torch.sigmoid(logit)}
