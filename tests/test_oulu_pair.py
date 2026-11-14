import json

import pytest
import yaml

from deepface_pad import oulu_pair
from deepface_pad.colab_cache import file_hash
from deepface_pad.oulu_e1 import e1_config


def test_pair_uses_same_checkpoint_budget_and_loader_seed(tmp_path, monkeypatch):
    root, starter, runs = (tmp_path / name for name in ("data", "starter", "runs"))
    starter.mkdir()
    for name in oulu_pair.ARTIFACTS:
        (starter / name).write_text(name)
    (starter / "config.yaml").write_text(yaml.safe_dump(e1_config(root, runs, 16)))
    hashes = {name: file_hash(starter / name) for name in oulu_pair.ARTIFACTS}
    monkeypatch.setattr(oulu_pair, "STARTER_SHA256", hashes["best.ckpt"])
    (starter / "e1_dev_lock.json").write_text(json.dumps({
        "protocol": 1, "depth_zip_sha256": "depth", "sha256": hashes,
    }))
    e1, e3 = [oulu_pair.pair_config(root, starter, runs, "depth", branch) for branch in oulu_pair.BRANCHES]
    assert e1["training"] == e3["training"]
    assert e1["training"]["loader_seed"] == 43
    assert e1["training"]["init_checkpoint"] == str(starter / "best.ckpt")
    assert e1["data"] == e3["data"] and e1["evaluation"] == e3["evaluation"]
    assert e3["model"]["name"] == "cdcn_official_head"
    assert e3["loss"] == e1["loss"] | {"classification": "bce", "lambda_cls": 1.0}
    (starter / "best.ckpt").write_text("changed")
    with pytest.raises(ValueError, match="hash mismatch: best.ckpt"):
        oulu_pair.pair_config(root, starter, runs, "depth", oulu_pair.BRANCHES[0])
