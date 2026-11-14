"""Register matched E1 continuation and E3 joint training from a locked E1."""
from __future__ import annotations

import json
from pathlib import Path

import yaml

from .colab_cache import file_hash
from .oulu_e1 import e1_config

BRANCHES = ("E1_CONTINUE", "E3_JOINT_BCE")
STARTER_SHA256 = "abe81fec2d5a03b76f4daad1bb996add1f48d623cf363587967124314bb00905"
ARTIFACTS = ("config.yaml", "best.ckpt", "threshold.json", "metrics.json", "train_log.csv",
             "checkpoint_selection.json", "runtime.json", "depth_input_snapshot.json")


def pair_config(root: Path, starter: Path, runs: Path, depth_sha: str, branch: str) -> dict:
    if branch not in BRANCHES:
        raise ValueError(f"unknown follow-up branch: {branch}")
    lock = json.loads((starter / "e1_dev_lock.json").read_text(encoding="utf-8"))
    if lock["protocol"] != 1 or lock["depth_zip_sha256"] != depth_sha:
        raise ValueError("starter has different protocol or depth snapshot")
    if set(lock["sha256"]) != set(ARTIFACTS) or lock["sha256"]["best.ckpt"] != STARTER_SHA256:
        raise ValueError("starter lock does not name the registered E1 checkpoint")
    for name, digest in lock["sha256"].items():
        if file_hash(starter / name) != digest:
            raise ValueError(f"starter artifact hash mismatch: {name}")
    config = yaml.safe_load((starter / "config.yaml").read_text(encoding="utf-8"))
    if config != e1_config(root, Path(config["runs_dir"]), 16):
        raise ValueError("starter config differs from registered E1")
    config["experiment_id"] = f"OULU_P1_{branch}"
    config["runs_dir"] = str(runs)
    # Adam starts from scratch for both branches. Only model weights are loaded.
    config["training"].update(init_checkpoint=str(starter / "best.ckpt"), loader_seed=43)
    if branch == "E3_JOINT_BCE":
        config["model"]["name"] = "cdcn_official_head"
        config["loss"].update(classification="bce", lambda_cls=1.0)
    return config
