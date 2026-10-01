import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("torchvision")

from deepface_pad.data import depth_supervision_required
from deepface_pad.models import CDCN, OfficialCDCN, OfficialCDCNWithDepthHead
from deepface_pad.train import _set_stage, build_model, load_initial_weights


def test_frozen_official_head_preserves_maps_and_batchnorm_after_optimizer_step(tmp_path):
    torch.manual_seed(42)
    e1 = OfficialCDCN().eval()
    checkpoint = tmp_path / "e1.ckpt"
    torch.save({"model": e1.state_dict()}, checkpoint)
    e2 = build_model({"model": {"name": "cdcn_official_head"}})
    load_initial_weights(e2, checkpoint, torch.device("cpu"))
    _set_stage(e2, "head")
    e2.train()
    assert not e2.backbone.training
    assert e2.head.training
    initial_backbone = {key: value.clone() for key, value in e2.backbone.state_dict().items()}
    initial_head = {key: value.clone() for key, value in e2.head.state_dict().items()}
    images = torch.randn(2, 3, 32, 32)
    with torch.no_grad():
        expected = e1(images)["depth"]
    output = e2(images)
    assert torch.equal(output["depth"], expected)
    assert output["logit"].shape == (2,)
    optimizer = torch.optim.Adam(e2.head.parameters(), lr=0.001)
    loss = torch.nn.functional.binary_cross_entropy_with_logits(output["logit"], torch.tensor([0., 1.]))
    loss.backward()
    assert all(parameter.grad is None for parameter in e2.backbone.parameters())
    optimizer.step()
    assert all(torch.equal(value, e2.backbone.state_dict()[key]) for key, value in initial_backbone.items())
    assert any(not torch.equal(value, e2.head.state_dict()[key]) for key, value in initial_head.items())
    e2.eval()
    with torch.no_grad():
        assert torch.equal(e2(images)["depth"], expected)


def test_official_head_rejects_pilot_checkpoint(tmp_path):
    checkpoint = tmp_path / "pilot.ckpt"
    torch.save({"model": CDCN(base_channels=4).state_dict()}, checkpoint)
    with pytest.raises(RuntimeError, match="incompatible init checkpoint"):
        load_initial_weights(OfficialCDCNWithDepthHead(), checkpoint, torch.device("cpu"))


def test_official_head_joint_stage_restores_backbone_training():
    model = OfficialCDCNWithDepthHead()
    _set_stage(model, "head")
    model.train()
    _set_stage(model, "joint")
    model.train()
    assert model.backbone.training
    assert all(parameter.requires_grad for parameter in model.backbone.parameters())


def test_official_head_requires_depth_targets_only_when_depth_loss_is_used():
    config = {
        "model": {"name": "cdcn_official_head"},
        "training": {"stages": [{"name": "head"}]},
        "loss": {"lambda_abs": 0., "lambda_contrast": 0.},
    }
    assert not depth_supervision_required(config)
    config["training"]["stages"] = [{"name": "joint"}]
    config["loss"]["lambda_abs"] = 1.
    assert depth_supervision_required(config)
