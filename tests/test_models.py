import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("torchvision")

from deepface_pad.losses import (
    ContrastiveDepthLoss,
    FocalLoss,
    OfficialContrastiveDepthLoss,
    depth_loss,
    official_cdcn_depth_loss,
)
from deepface_pad.models import (
    CDCN,
    CDCNMultiTaskLite,
    MobileNetBaseline,
    OFFICIAL_CDCN_PROVENANCE,
    OfficialCDCN,
)
from deepface_pad.train import load_initial_weights


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


def test_official_cdcn_topology_output_and_backward():
    model = OfficialCDCN(theta=0.7)
    image = torch.randn(1, 3, 64, 64)
    target = torch.rand(1, 1, 32, 32)

    output = model(image)

    assert output["depth"].shape == target.shape
    assert output["score"].shape == (1,)
    assert model.block1[0].conv.in_channels == 64
    assert model.block1[0].conv.out_channels == 128
    assert model.block1[3].conv.out_channels == 196
    assert model.lastconv1[0].conv.in_channels == 384
    official_cdcn_depth_loss(output["depth"], target).backward()


def test_official_cdcn_provenance_is_pinned():
    assert OFFICIAL_CDCN_PROVENANCE["git_commit"] == (
        "fd8370e8f32bdd090a3552f5a1fe4c301fa99f2b"
    )
    assert OFFICIAL_CDCN_PROVENANCE["source_file"].endswith("models/CDCNs.py")


def test_contrastive_depth_loss_has_eight_unique_neighbours():
    kernels = ContrastiveDepthLoss().kernels[:, 0]
    assert kernels.shape == (8, 3, 3)
    assert torch.unique(kernels.reshape(8, -1), dim=0).shape[0] == 8
    assert torch.all(kernels[:, 1, 1] == 1)
    assert torch.all((kernels == -1).sum(dim=(1, 2)) == 1)


def test_contrastive_depth_loss_matches_prediction_device_and_dtype():
    prediction = torch.rand(2, 1, 8, 8, dtype=torch.float64, requires_grad=True)
    target = torch.rand(2, 1, 8, 8, dtype=torch.float32)
    loss = ContrastiveDepthLoss()(prediction, target)
    assert loss.dtype == prediction.dtype
    loss.backward()
    assert prediction.grad is not None


def test_official_contrastive_depth_loss_matches_source_shape_and_dtype():
    prediction = torch.rand(2, 1, 32, 32, dtype=torch.float64, requires_grad=True)
    target = torch.rand(2, 1, 32, 32, dtype=torch.float32)
    loss = OfficialContrastiveDepthLoss()(prediction, target)
    assert loss.dtype == prediction.dtype
    assert OfficialContrastiveDepthLoss().kernels.shape == (8, 1, 3, 3)
    loss.backward()
    assert prediction.grad is not None


def test_e1_checkpoint_initializes_e2_backbone(tmp_path):
    e1 = CDCN(base_channels=4)
    checkpoint = tmp_path / "e1.ckpt"
    torch.save({"model": e1.state_dict()}, checkpoint)
    e2 = CDCNMultiTaskLite(base_channels=4)

    load_initial_weights(e2, checkpoint, torch.device("cpu"))

    for key, value in e1.state_dict().items():
        assert torch.equal(e2.backbone.state_dict()[key], value)
