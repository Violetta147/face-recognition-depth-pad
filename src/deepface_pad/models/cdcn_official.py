"""CDCN architecture ported from the authors' CVPR 2020 research code.

This module preserves the layer topology of ``CVPR2020_paper_codes/models/CDCNs.py``
while adapting the return value to the project's dictionary-based model API.  The
dataset, pseudo-depth generator, training schedule, and evaluator remain those of
this repository, so runs must be described as an architecture reproduction under
our protocol rather than a reproduction of the paper's published numbers.
"""
from __future__ import annotations

import math

import torch
from torch import nn
from torch.nn import functional as F


OFFICIAL_CDCN_PROVENANCE = {
    "implementation": "ZitongYu/CDCN",
    "repository": "https://github.com/ZitongYu/CDCN",
    "git_commit": "fd8370e8f32bdd090a3552f5a1fe4c301fa99f2b",
    "source_file": "CVPR2020_paper_codes/models/CDCNs.py",
    "source_sha256": "9edd5f4a4ea4d9c642b9777dbeb614d3fddae5821c2cde124798bc41fe24c331",
    "architecture": "CDCN",
    "paper": "Searching Central Difference Convolutional Networks for Face Anti-Spoofing (CVPR 2020)",
    "adaptations": [
        "dictionary output compatible with deepface-pad",
        "depth channel retained as Bx1x32x32 instead of squeezing to Bx32x32",
        "frame score is the spatial mean because protocol-independent PRNet masks are unavailable",
        "CASIA subject-disjoint manifest and 3DDFA V2 pseudo-depth replace the paper's OULU/PRNet pipeline",
        "frozen face-centric CASIA frames are resized without a new crop to preserve E0 preprocessing compatibility",
    ],
}


class OfficialCentralDifferenceConv2d(nn.Module):
    """Central-difference convolution matching the authors' ``Conv2d_cd``."""

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int = 3,
        stride: int = 1,
        padding: int = 1,
        dilation: int = 1,
        groups: int = 1,
        bias: bool = False,
        theta: float = 0.7,
    ) -> None:
        super().__init__()
        self.conv = nn.Conv2d(
            in_channels,
            out_channels,
            kernel_size=kernel_size,
            stride=stride,
            padding=padding,
            dilation=dilation,
            groups=groups,
            bias=bias,
        )
        self.theta = theta

    def forward(self, image: torch.Tensor) -> torch.Tensor:
        normal = self.conv(image)
        if math.fabs(self.theta) < 1e-8:
            return normal
        # Preserve the upstream reduction order exactly. A tuple reduction can
        # accumulate floating-point values in a different order and defeats the
        # numerical-equivalence check even when the operator is mathematically
        # identical.
        kernel_diff = self.conv.weight.sum(2).sum(2)[:, :, None, None]
        difference = F.conv2d(
            image,
            kernel_diff,
            bias=self.conv.bias,
            stride=self.conv.stride,
            padding=0,
            groups=self.conv.groups,
        )
        return normal - self.theta * difference


def _official_block(channels: tuple[int, int, int, int], theta: float) -> nn.Sequential:
    first, second, third, fourth = channels
    return nn.Sequential(
        OfficialCentralDifferenceConv2d(first, second, theta=theta),
        nn.BatchNorm2d(second),
        nn.ReLU(),
        OfficialCentralDifferenceConv2d(second, third, theta=theta),
        nn.BatchNorm2d(third),
        nn.ReLU(),
        OfficialCentralDifferenceConv2d(third, fourth, theta=theta),
        nn.BatchNorm2d(fourth),
        nn.ReLU(),
        nn.MaxPool2d(kernel_size=3, stride=2, padding=1),
    )


class OfficialCDCN(nn.Module):
    """The authors' CDCN topology with a project-compatible output contract."""

    def __init__(self, theta: float = 0.7) -> None:
        super().__init__()
        self.conv1 = nn.Sequential(
            OfficialCentralDifferenceConv2d(3, 64, theta=theta),
            nn.BatchNorm2d(64),
            nn.ReLU(),
        )
        self.block1 = _official_block((64, 128, 196, 128), theta)
        self.block2 = _official_block((128, 128, 196, 128), theta)
        self.block3 = _official_block((128, 128, 196, 128), theta)
        self.lastconv1 = nn.Sequential(
            OfficialCentralDifferenceConv2d(128 * 3, 128, theta=theta),
            nn.BatchNorm2d(128),
            nn.ReLU(),
        )
        self.lastconv2 = nn.Sequential(
            OfficialCentralDifferenceConv2d(128, 64, theta=theta),
            nn.BatchNorm2d(64),
            nn.ReLU(),
        )
        self.lastconv3 = nn.Sequential(
            OfficialCentralDifferenceConv2d(64, 1, theta=theta),
            nn.ReLU(),
        )
        self.resize_to_depth = nn.Upsample(size=(32, 32), mode="bilinear")

    def forward(self, image: torch.Tensor) -> dict[str, torch.Tensor]:
        first = self.block1(self.conv1(image))
        second = self.block2(first)
        third = self.block3(second)
        fused = torch.cat(
            (
                self.resize_to_depth(first),
                self.resize_to_depth(second),
                self.resize_to_depth(third),
            ),
            dim=1,
        )
        depth = self.lastconv3(self.lastconv2(self.lastconv1(fused)))
        return {
            "depth": depth,
            "score": depth.mean(dim=(1, 2, 3)),
        }
