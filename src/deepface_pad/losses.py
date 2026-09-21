from __future__ import annotations

import torch
from torch import nn
from torch.nn import functional as F


class ContrastiveDepthLoss(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        kernels = []
        # Eight unique first-order differences around the centre pixel.  The
        # previous implementation included distance-two offsets in a 3x3
        # kernel and clamped them back to one, silently duplicating four
        # directions.
        for dy, dx in [
            (-1, -1),
            (-1, 0),
            (-1, 1),
            (0, -1),
            (0, 1),
            (1, -1),
            (1, 0),
            (1, 1),
        ]:
            kernel = torch.zeros(3, 3)
            kernel[1, 1] = 1
            y, x = 1 + dy, 1 + dx
            kernel[y, x] = -1
            kernels.append(kernel)
        self.register_buffer("kernels", torch.stack(kernels)[:, None])

    def forward(self, prediction: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        kernels = self.kernels.to(device=prediction.device, dtype=prediction.dtype)
        target = target.to(device=prediction.device, dtype=prediction.dtype)
        pred_grad = F.conv2d(prediction, kernels, padding=1)
        target_grad = F.conv2d(target, kernels, padding=1)
        return F.l1_loss(pred_grad, target_grad)


class OfficialContrastiveDepthLoss(nn.Module):
    """Contrastive depth loss from the official CDCN CVPR 2020 training code."""

    def __init__(self) -> None:
        super().__init__()
        kernels = torch.tensor(
            [
                [[1, 0, 0], [0, -1, 0], [0, 0, 0]],
                [[0, 1, 0], [0, -1, 0], [0, 0, 0]],
                [[0, 0, 1], [0, -1, 0], [0, 0, 0]],
                [[0, 0, 0], [1, -1, 0], [0, 0, 0]],
                [[0, 0, 0], [0, -1, 1], [0, 0, 0]],
                [[0, 0, 0], [0, -1, 0], [1, 0, 0]],
                [[0, 0, 0], [0, -1, 0], [0, 1, 0]],
                [[0, 0, 0], [0, -1, 0], [0, 0, 1]],
            ],
            dtype=torch.float32,
        )
        self.register_buffer("kernels", kernels[:, None])

    def forward(self, prediction: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        kernels = self.kernels.to(device=prediction.device, dtype=prediction.dtype)
        target = target.to(device=prediction.device, dtype=prediction.dtype)
        pred_grad = F.conv2d(prediction.expand(-1, 8, -1, -1), kernels, groups=8)
        target_grad = F.conv2d(target.expand(-1, 8, -1, -1), kernels, groups=8)
        return F.mse_loss(pred_grad, target_grad)


class FocalLoss(nn.Module):
    def __init__(self, alpha: float = 0.25, gamma: float = 2.0) -> None:
        super().__init__()
        self.alpha, self.gamma = alpha, gamma

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        targets = targets.float()
        bce = F.binary_cross_entropy_with_logits(logits, targets, reduction="none")
        probability = torch.sigmoid(logits)
        pt = torch.where(targets == 1, probability, 1 - probability)
        alpha_t = torch.where(targets == 1, self.alpha, 1 - self.alpha)
        return (alpha_t * (1 - pt).pow(self.gamma) * bce).mean()


def depth_loss(prediction: torch.Tensor, target: torch.Tensor, lambda_abs: float = 1.0, lambda_contrast: float = 0.5) -> torch.Tensor:
    target = target.to(device=prediction.device, dtype=prediction.dtype)
    return lambda_abs * F.l1_loss(prediction, target) + lambda_contrast * ContrastiveDepthLoss()(prediction, target)


def official_cdcn_depth_loss(
    prediction: torch.Tensor,
    target: torch.Tensor,
    lambda_abs: float = 1.0,
    lambda_contrast: float = 1.0,
) -> torch.Tensor:
    """Official CDCN loss: depth MSE plus eight-neighbour contrast MSE."""

    target = target.to(device=prediction.device, dtype=prediction.dtype)
    return lambda_abs * F.mse_loss(prediction, target) + lambda_contrast * (
        OfficialContrastiveDepthLoss()(prediction, target)
    )
