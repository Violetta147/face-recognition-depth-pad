import pytest
import json

import pandas as pd
from PIL import Image

torch = pytest.importorskip("torch")
pytest.importorskip("torchvision")

from deepface_pad.data import MANIFEST_COLUMNS, depth_supervision_required
from deepface_pad.models import DepthHead, OfficialCDCN, OfficialCDCNWithDepthHead
from deepface_pad.train import _set_stage, build_model, load_initial_weights, run


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
    torch.save({"model": {"encoder.0.0.weight": torch.zeros(4, 3, 3, 3), "depth.0.weight": torch.zeros(1, 8, 1, 1)}}, checkpoint)
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


def test_official_head_training_run_saves_frozen_backbone_and_validation_artifacts(tmp_path):
    import yaml

    torch.manual_seed(42)
    e1 = OfficialCDCN().eval()
    initial = tmp_path / "e1.ckpt"
    torch.save({"model": e1.state_dict()}, initial)
    rows = []
    for split in ("train", "val"):
        for label in (0, 1):
            name = f"{split}-{label}"
            Image.new("RGB", (32, 32), (40 + label * 150, 80, 100)).save(tmp_path / f"{name}.png")
            rows.append([name, split, name, name, 0, f"{name}.png", "", label, "live" if label else "print"])
    manifest = tmp_path / "all.csv"
    pd.DataFrame(rows, columns=MANIFEST_COLUMNS).to_csv(manifest, index=False)
    config = {
        "experiment_id": "E2_SYNTHETIC", "seed": 42, "runs_dir": str(tmp_path / "runs"),
        "model": {"name": "cdcn_official_head", "theta": .7},
        "data": {"manifest": str(manifest), "root": str(tmp_path), "image_size": 32, "normalization": "cdcn_official"},
        "loss": {"classification": "bce", "lambda_abs": 0., "lambda_contrast": 0., "lambda_cls": 1.},
        "training": {"init_checkpoint": str(initial), "batch_size": 2, "workers": 0, "stages": [{"name": "head", "epochs": 1, "lr": .001}]},
        "evaluation": {"aggregation": "mean"},
    }
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    folder = run(config_path)
    trained = torch.load(folder / "best.ckpt", map_location="cpu", weights_only=False)
    assert all(torch.equal(value, trained["model"]["backbone." + key]) for key, value in e1.state_dict().items())
    assert json.loads((folder / "threshold.json").read_text())["source"] == "validation"
    assert len(pd.read_csv(folder / "val_scores.csv")) == 2
    assert len(json.loads((folder / "initial_checkpoint.json").read_text())["sha256"]) == 64
    assert not (folder / "test_scores.csv").exists()


def test_extracted_head_preserves_checkpoint_schema_and_numerics():
    torch.manual_seed(42)
    legacy = torch.nn.Module()
    legacy.layers = torch.nn.Sequential(torch.nn.Conv2d(1, 8, 3, padding=1), torch.nn.ReLU(inplace=True), torch.nn.Conv2d(8, 16, 3, padding=1), torch.nn.ReLU(inplace=True), torch.nn.AdaptiveAvgPool2d(1))
    legacy.classifier = torch.nn.Linear(16, 1)
    head = DepthHead()
    head.load_state_dict(legacy.state_dict(), strict=True)
    depth = torch.rand(2, 1, 32, 32)
    expected = legacy.classifier(legacy.layers(depth).flatten(1)).flatten()
    assert torch.equal(head(depth), expected)
    assert sum(p.numel() for p in head.parameters()) == 1265


@pytest.mark.parametrize("name", ["cdcn", "cdcn_lite", "cdcn_mt_lite"])
def test_removed_pilot_model_names_fail_explicitly(name):
    with pytest.raises(ValueError, match="Lite/Pilot was removed"):
        build_model({"model": {"name": name}})


def test_all_depth_experiment_configs_use_official_models():
    from pathlib import Path
    import yaml

    root = Path(__file__).resolve().parents[1]
    for path in (root / "configs").glob("*.yaml"):
        cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
        if cfg["model"]["name"] == "mobilenet_v3_small":
            continue
        assert cfg["model"]["name"] in {"cdcn_official", "cdcn_official_head"}, path
        assert cfg["data"]["normalization"] == "cdcn_official", path
        if depth_supervision_required(cfg):
            assert cfg["loss"]["implementation"] == "official_cdcn", path
            assert cfg["loss"]["lambda_contrast"] == 1.0, path
