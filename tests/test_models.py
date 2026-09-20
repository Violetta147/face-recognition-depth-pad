import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("torchvision")

from deepface_pad.losses import FocalLoss, depth_loss
from deepface_pad.models import CDCN, CDCNMultiTaskLite, MobileNetBaseline


def test_model_shapes_and_backward():
    image = torch.randn(2, 3, 64, 64)
    depth = torch.rand(2, 1, 32, 32)
    cdcn = CDCN(base_channels=4)
    output = cdcn(image)
    assert output["depth"].shape == depth.shape
    depth_loss(output["depth"], depth).backward()
    multi = CDCNMultiTaskLite(base_channels=4)
    output = multi(image)
    assert output["logit"].shape == (2,)
    (depth_loss(output["depth"], depth) + FocalLoss()(output["logit"], torch.tensor([0.0, 1.0]))).backward()


def test_mobilenet_output():
    output = MobileNetBaseline(pretrained=False)(torch.randn(2, 3, 64, 64))
    assert output["logit"].shape == (2,)
