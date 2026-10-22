"""Synthetic correctness checks, never CASIA benchmark evidence."""
import json

import pandas as pd
import pytest
import torch
import yaml
from PIL import Image

from deepface_pad.data import MANIFEST_COLUMNS
from deepface_pad.train import _loss, _selection_loss, _set_stage, run


class TinyDepthHead(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.backbone = torch.nn.Linear(1, 1, bias=False)
        self.head = torch.nn.Linear(1, 1, bias=False)
        with torch.no_grad():
            self.backbone.weight.fill_(0.2)
            self.head.weight.fill_(0.3)

    def forward(self, image):
        depth = self.backbone(image[:, 0, 0, 0, None])
        return {"depth": depth, "logit": self.head(depth).flatten()}


@pytest.mark.parametrize("selection_metric", ["val_loss", "classification_bce"])
def test_staged_run_uses_final_stage_and_restores_each_stage_best(tmp_path, monkeypatch, selection_metric):
    import deepface_pad.train as training

    rows = []
    for split in ("train", "val"):
        for label in (0, 1):
            name = f"{split}-{label}"
            Image.new("RGB", (8, 8), (180, 90, 60)).save(tmp_path / f"{name}.png")
            rows.append([name, split, name, name, 0, f"{name}.png", "", label, "live" if label else "print"])
    pd.DataFrame(rows, columns=MANIFEST_COLUMNS).to_csv(tmp_path / "manifest.csv", index=False)
    model = TinyDepthHead()
    initial = tmp_path / "initial.ckpt"
    torch.save({"model": model.state_dict()}, initial)
    monkeypatch.setattr(training, "build_model", lambda config: model)
    monkeypatch.setattr(training, "inspect_training_inputs", lambda config: (False, None))
    starts = []
    original_set_stage = training._set_stage

    def record_stage(net, stage):
        starts.append({key: value.clone() for key, value in net.state_dict().items()})
        original_set_stage(net, stage)

    monkeypatch.setattr(training, "_set_stage", record_stage)
    validation = {"depth": iter([0.01, 0.02]), "head": iter([0.1, 0.2]), "joint": iter([1., 2.])}

    def objective(config, output, batch, stage):
        if torch.is_grad_enabled():
            return (output["depth"] - 1).square().mean() + (output["logit"] - 1).square().mean()
        return torch.tensor(next(validation[stage]), dtype=torch.float64)

    monkeypatch.setattr(training, "_loss", objective)
    if selection_metric == "classification_bce":
        selected_losses = {name: iter([.2, .1]) for name in ("depth", "head", "joint")}
        monkeypatch.setattr(training, "_selection_loss", lambda metric, output, batch, stage, objective:
                            torch.tensor(next(selected_losses[stage])))
    config = {
        "experiment_id": "STAGES_SYNTHETIC", "seed": 42, "runs_dir": str(tmp_path / "runs"),
        "model": {"name": "test_tiny"},
        "data": {"manifest": str(tmp_path / "manifest.csv"), "root": str(tmp_path), "image_size": 8},
        "loss": {"classification": "bce"},
        "training": {"init_checkpoint": str(initial), "batch_size": 2, "workers": 0,
                     "selection_metric": selection_metric,
                     "stages": [{"name": stage, "epochs": 2, "lr": 0.01} for stage in ("depth", "head", "joint")]},
        "evaluation": {"aggregation": "mean"},
    }
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    folder = run(path)
    selected = torch.load(folder / "best.ckpt", weights_only=True)
    assert selected["stage"] == "joint"
    epoch = 1 if selection_metric == "val_loss" else 2
    assert selected["epoch"] == epoch
    assert selected["global_epoch"] == 4 + epoch
    assert selected["val_loss"] == float(epoch)
    assert selected["selection_metric"] == selection_metric
    for index, stage in enumerate(("depth", "head"), 1):
        earlier = torch.load(folder / f"best_stage_{index:02d}_{stage}.ckpt", weights_only=True)
        assert all(torch.equal(starts[index][key], value) for key, value in earlier["model"].items())
    selection = json.loads((folder / "checkpoint_selection.json").read_text())
    assert selection["reported_stage"] == "joint"
    assert [row["epoch"] for row in selection["stages"]] == [epoch] * 3
    assert not (folder / "test_scores.csv").exists()


def test_unknown_stage_is_rejected_instead_of_silently_unfreezing():
    with pytest.raises(ValueError, match="unknown training stage"):
        _set_stage(TinyDepthHead(), "typo")


@pytest.mark.parametrize("classification", ["bce", "focal"])
def test_depth_head_joint_loss_routes_only_the_declared_objectives(classification):
    config = {"loss": {"implementation": "official_cdcn", "classification": classification,
                       "lambda_abs": 1., "lambda_contrast": 1., "lambda_cls": 1.}}
    output = {"depth": torch.ones(2, 1, 32, 32), "logit": torch.tensor([-.3, .7])}
    batch = {"depth": torch.zeros(2, 1, 32, 32), "label": torch.tensor([0., 1.])}
    depth = _loss(config, output, batch, "depth")
    head = _loss(config, output, batch, "head")
    joint = _loss(config, output, batch, "joint")
    assert depth.item() == pytest.approx(1.)
    assert joint.item() == pytest.approx(depth.item() + head.item())


def test_common_selection_uses_bce_independently_of_training_objective():
    output = {"logit": torch.tensor([-.3, .7])}
    batch = {"label": torch.tensor([0., 1.])}
    objective = torch.tensor(.01)
    expected = torch.nn.functional.binary_cross_entropy_with_logits(output["logit"], batch["label"])
    assert torch.equal(_selection_loss("classification_bce", output, batch, "joint", objective), expected)
    assert torch.equal(_selection_loss("classification_bce", output, batch, "depth", objective), objective)
    with pytest.raises(ValueError, match="requires classifier logits"):
        _selection_loss("classification_bce", {}, batch, "joint", objective)
