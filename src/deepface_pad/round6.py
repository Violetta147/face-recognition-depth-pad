"""Registered six-run CASIA replication. No training or scoring on import."""
from __future__ import annotations

import copy
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import yaml

from .data import manifest_checksum
from .metrics import aggregate_video_scores, evaluate_scores
from .preflight import inspect_training_inputs

SEEDS = (43, 44, 45)
KEYS = tuple(f"{variant}_{seed}" for seed in SEEDS for variant in ("E1", "E3"))
SOURCE_MANIFEST = "58fffcc2fb29649af1b8424d78b85067eefbd0321fde6b27fbd0803ef0fd7192"
DEPTH_MANIFEST = "4c302c9039e48a8ea6baedf426b26e1b0a6663bc295c661bb71fefccdb9b37fd"
RUN_FILES = ("config.yaml", "best.ckpt", "best_stage_01_joint.ckpt",
             "checkpoint_selection.json", "train_log.csv", "threshold.json",
             "metrics.json", "val_scores.csv", "val_frame_scores.csv",
             "manifest_checksum.json", "depth_input_snapshot.json", "environment.txt",
             "round6_binding.json")
TEST_FILES = ("test_metrics.json", "test_scores.csv", "test_frame_scores.csv")
METRICS = ("apcer", "bpcer", "acer", "eer", "auc")


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False,
                                     separators=(",", ":")).encode()).hexdigest()


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def immutable_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if read(path) != payload:
            raise ValueError(f"stale/different immutable artifact: {path}")
    else:
        # Exclusive creation: never replace an existing registration or freeze.
        with path.open("x", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write("\n")


def environment() -> dict:
    """Stable identity, excluding transient GPU load/free memory and timestamps."""
    if not torch.cuda.is_available():
        raise ValueError("Round 6 requires the registered A100 CUDA runtime")
    props = torch.cuda.get_device_properties(0)
    if "A100" not in props.name:
        raise ValueError(f"expected A100, found {props.name}")
    driver = subprocess.check_output([
        "nvidia-smi", "--query-gpu=uuid,name,driver_version,memory.total",
        "--format=csv,noheader"], text=True).strip()
    packages = subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True)
    return {"python": sys.version, "platform": platform.platform(),
            "torch": torch.__version__, "cuda": torch.version.cuda,
            "cudnn": torch.backends.cudnn.version(), "gpu": props.name,
            "gpu_memory": props.total_memory, "driver_inventory": driver,
            "packages": sorted(packages.splitlines()),
            "cudnn_deterministic": torch.backends.cudnn.deterministic,
            "cudnn_benchmark": torch.backends.cudnn.benchmark,
            "deterministic_algorithms": torch.are_deterministic_algorithms_enabled()}


def verify_source(root: Path) -> dict:
    lock = read(root / "SOURCE_LOCK.json")
    if (root / "SOURCE_COMMIT.txt").read_text().strip() != lock["commit"]:
        raise ValueError("source commit does not match bundle")
    for name, expected in lock["files"].items():
        if manifest_checksum(root / name) != expected:
            raise ValueError(f"source changed: {name}")
    return lock


def depth_identity(snapshot: dict) -> dict:
    return {"files": snapshot["files"],
            "artifacts": snapshot["depth_audit"]["artifact_checksums"]}


class Batch:
    def __init__(self, root: Path, output: Path):
        self.root, self.output = Path(root), Path(output)
        self.registration_path = self.output / "registration.json"
        self.freeze_path = self.output / "comparison_freeze.json"

    def register(self, data_root: Path, runs_dir: Path) -> dict:
        source = verify_source(self.root)
        configs = {}
        for key in KEYS:
            cfg = yaml.safe_load((self.root / f"configs/round6/{key}.yaml").read_text())
            cfg["source_commit"] = source["commit"]
            cfg["runs_dir"] = str(runs_dir)
            cfg["round6_registration"] = str(self.registration_path)
            cfg["data"].update(root=str(data_root),
                manifest=str(self.root / "data/manifests/casia_fasd_debug_with_depth.csv"),
                source_manifest=str(self.root / "data/manifests/casia_fasd_debug.csv"),
                depth_ledger=str(data_root / "depth/depth_status.csv"))
            configs[key] = cfg
        cfg = configs["E1_43"]
        if manifest_checksum(cfg["data"]["source_manifest"]) != SOURCE_MANIFEST:
            raise ValueError("source manifest mismatch")
        if manifest_checksum(cfg["data"]["manifest"]) != DEPTH_MANIFEST:
            raise ValueError("derived manifest mismatch")
        _, snapshot = inspect_training_inputs(cfg)
        reference = read(self.root / "configs/round6/depth_reference.json")
        if digest(snapshot["depth_audit"]["artifact_checksums"]) != reference["artifact_digest"]:
            raise ValueError("depth cache differs from locked historical cache")
        mf = pd.read_csv(cfg["data"]["manifest"])
        counts = mf.groupby("split").agg(frames=("sample_id", "size"),
                   videos=("video_id", "nunique"), subjects=("subject_id", "nunique"))
        if counts.to_dict() != {"frames": {"test":7200,"train":3840,"val":960},
                                "videos": {"test":360,"train":192,"val":48},
                                "subjects": {"test":30,"train":16,"val":4}}:
            raise ValueError("split counts differ from registered protocol")
        record = {"schema_version": 1, "source": source, "environment": environment(),
                  "depth": depth_identity(snapshot), "configs": configs,
                  "primary_metric": "video ACER", "paired_delta": "E3 - E1",
                  "seeds": list(SEEDS), "epochs": 138, "budget_hours_estimate": [2,3]}
        immutable_json(self.registration_path, record)
        return record

    def current(self, *, inspect_depth=True) -> dict:
        reg = read(self.registration_path)
        if verify_source(self.root) != reg["source"] or environment() != reg["environment"]:
            raise ValueError("source/environment changed since registration")
        if set(reg["configs"]) != set(KEYS):
            raise ValueError("registration must contain exactly six runs")
        if inspect_depth:
            _, snapshot = inspect_training_inputs(reg["configs"]["E1_43"])
            if depth_identity(snapshot) != reg["depth"]:
                raise ValueError("input/cache changed since registration")
        return reg

    def config_for(self, key: str, folders: dict[str, Path], reg: dict) -> dict:
        cfg = copy.deepcopy(reg["configs"][key])
        if key.startswith("E3_"):
            peer = "E1_" + key.split("_")[1]
            self.validate_run(peer, folders[peer], reg, folders)
            initial = folders[peer] / "best.ckpt"
            cfg["training"]["init_checkpoint"] = str(initial)
            cfg["round6_initializer_sha256"] = manifest_checksum(initial)
        return cfg

    def validate_run(self, key: str, folder: Path, reg: dict, folders: dict) -> dict:
        cfg = self.config_for(key, folders, reg) if key.startswith("E3_") else reg["configs"][key]
        if not all((folder / name).is_file() for name in RUN_FILES):
            raise ValueError(f"incomplete run, preserve and inspect; no full resume: {folder}")
        if yaml.safe_load((folder / "config.yaml").read_text()) != cfg:
            raise ValueError(f"run config mismatch: {key}")
        if not folder.name.startswith(f"{cfg['experiment_id']}_seed{cfg['seed']}_"):
            raise ValueError("run ID mismatch")
        binding = read(folder / "round6_binding.json")
        if binding != {"registration_sha256": manifest_checksum(self.registration_path),
                       "environment": reg["environment"]}:
            raise ValueError("run environment/registration binding mismatch")
        if read(folder / "manifest_checksum.json") != {"sha256": DEPTH_MANIFEST}:
            raise ValueError("run manifest mismatch")
        if depth_identity(read(folder / "depth_input_snapshot.json")) != reg["depth"]:
            raise ValueError("run depth snapshot mismatch")
        metric = "classification_bce" if key.startswith("E3_") else "val_loss"
        epochs = 16 if key.startswith("E3_") else 30
        log = pd.read_csv(folder / "train_log.csv")
        losses = log[["train_loss", "val_loss", "val_selection_loss"]].to_numpy()
        if (len(log) != epochs or log.epoch.tolist() != list(range(1, epochs+1))
                or set(log.stage) != {"joint"} or not np.isfinite(losses).all()):
            raise ValueError("incomplete/nonfinite training log")
        selected = read(folder / "checkpoint_selection.json")
        stages = selected["stages"]
        best_row = log.iloc[int(np.argmin(log.val_selection_loss.to_numpy()))]
        if (selected["reported_stage"] != "joint" or len(stages) != 1
                or stages[0]["selection_metric"] != metric
                or stages[0]["epoch"] != int(best_row.epoch)
                or not np.isclose(stages[0]["selection_value"], best_row.val_selection_loss,
                                  rtol=1e-10, atol=1e-12)):
            raise ValueError("checkpoint was not selected by minimum validation loss")
        if manifest_checksum(folder / "best.ckpt") != manifest_checksum(folder / "best_stage_01_joint.ckpt"):
            raise ValueError("best checkpoint differs from selected stage")
        checkpoint = torch.load(folder / "best.ckpt", map_location="cpu", weights_only=False)
        if (checkpoint["config"] != cfg or checkpoint["epoch"] != stages[0]["epoch"]
                or checkpoint["selection_metric"] != metric
                or checkpoint["selection_value"] != stages[0]["selection_value"]):
            raise ValueError("checkpoint metadata mismatch")
        if key.startswith("E3_"):
            initial = read(folder / "initial_checkpoint.json")
            if initial != {"path": cfg["training"]["init_checkpoint"],
                           "sha256": cfg["round6_initializer_sha256"]}:
                raise ValueError("E3 initializer must be best E1 of the same seed")
        self.validate_scores(folder, cfg, "val")
        names = RUN_FILES + (("initial_checkpoint.json",) if key.startswith("E3_") else ())
        return {"run": str(folder), "hashes": {name: manifest_checksum(folder/name) for name in names}}

    def validate_scores(self, folder: Path, cfg: dict, split: str) -> dict:
        frames = pd.read_csv(folder / f"{split}_frame_scores.csv")
        mf = pd.read_csv(cfg["data"]["manifest"])
        expected = mf[mf.split == split][["sample_id", "video_id", "label"]]
        actual = frames[["sample_id", "video_id", "label"]]
        if (frames.sample_id.duplicated().any() or
                not actual.sort_values("sample_id").reset_index(drop=True).equals(
                    expected.sort_values("sample_id").reset_index(drop=True))):
            raise ValueError(f"{split} scores have wrong sample IDs/labels")
        video = aggregate_video_scores(frames, "mean")
        saved = pd.read_csv(folder / f"{split}_scores.csv").sort_values("video_id").reset_index(drop=True)
        if (not saved[["video_id","label"]].equals(video[["video_id","label"]])
                or not np.allclose(saved.score, video.score, rtol=1e-10, atol=1e-12)):
            raise ValueError("saved video scores differ from mean frame scores")
        threshold = read(folder / "threshold.json")
        if threshold["source"] != "validation":
            raise ValueError("threshold must come from validation")
        metrics = evaluate_scores(video.label.to_numpy(), video.score.to_numpy(),
                                 None if split == "val" else threshold["threshold"]).to_dict()
        stored = read(folder / ("metrics.json" if split == "val" else "test_metrics.json"))
        if (not np.isclose(threshold["threshold"], metrics["threshold"], rtol=0, atol=1e-12)
                or any(not np.isclose(stored[k], v, rtol=1e-10, atol=1e-12) for k,v in metrics.items())):
            raise ValueError(f"{split} metrics/validation threshold mismatch")
        return metrics

    def train_pair(self, seed: int, *, allow_train=False) -> dict:
        if not allow_train:
            raise ValueError("RUN_TRAIN is closed; review PREFLIGHT and remaining A100 budget")
        if seed not in SEEDS or self.freeze_path.exists():
            raise ValueError("unknown seed or batch already frozen")
        reg = self.current()
        folders = {}
        for key in (f"E1_{seed}", f"E3_{seed}"):
            cfg = self.config_for(key, folders, reg)
            directory = Path(cfg["runs_dir"])
            candidates = list(directory.glob(f"{cfg['experiment_id']}_seed{seed}_*"))
            if len(candidates) > 1:
                raise ValueError("multiple runs; preserve all, do not select a favorable run")
            if candidates:
                folder = candidates[0]
            else:
                path = self.output / f"{key}.yaml"
                path.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
                # Imported lazily; no GPU work until the explicit train gate.
                from .train import run
                folder = run(path)
            self.validate_run(key, folder, reg, folders)
            folders[key] = folder
            immutable_json(self.output / f"{key}-run.json", {"run": str(folder)})
            print(key, folder, flush=True)
        return folders

    def frozen_state(self, reg: dict) -> dict:
        folders = {key: Path(read(self.output / f"{key}-run.json")["run"]) for key in KEYS}
        return {"registration_sha256": manifest_checksum(self.registration_path),
                "selection_source": "validation", "candidate": "E3", "runs": {
                    key: self.validate_run(key, folders[key], reg, folders) for key in KEYS}}

    def freeze(self) -> dict:
        reg = self.current()
        state = self.frozen_state(reg)
        if not self.freeze_path.exists():
            if any(list(Path(record["run"]).glob("test_*")) for record in state["runs"].values()):
                raise ValueError("test artifacts exist before the six-run freeze")
        immutable_json(self.freeze_path, state)
        return state

    def verify_freeze(self) -> dict:
        state = self.frozen_state(self.current())
        if read(self.freeze_path) != state:
            raise ValueError("freeze stale: run artifacts/source/environment changed")
        return state

    def test(self, *, allow_test=False) -> pd.DataFrame:
        if not allow_test:
            raise ValueError("OPEN_TEST is closed; all six validation runs must be frozen")
        state = self.verify_freeze()
        rows = []
        for key in KEYS:
            folder = Path(state["runs"][key]["run"])
            present = [(folder / name).exists() for name in TEST_FILES]
            receipt = self.output / f"{key}-test.json"
            if any(present):
                if not all(present) or not receipt.is_file():
                    raise ValueError("partial/unreceipted test; preserve artifacts and inspect")
            else:
                if receipt.exists():
                    raise ValueError("test receipt exists but output is missing")
                subprocess.run([sys.executable, str(self.root / "scripts/score_checkpoint.py"),
                    "--run-dir", str(folder), "--split", "test", "--round6-freeze",
                    str(self.freeze_path)], check=True, cwd=self.root)
            cfg = yaml.safe_load((folder / "config.yaml").read_text())
            metrics = self.validate_scores(folder, cfg, "test")
            immutable_json(receipt, {"freeze_sha256": manifest_checksum(self.freeze_path),
                "hashes": {name: manifest_checksum(folder/name) for name in TEST_FILES}})
            rows.append({"variant": key.split("_")[0], "seed": int(key.split("_")[1]),
                         "run": folder.name, **metrics})
        return pd.DataFrame(rows)


def summarize(rows: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    if (len(rows) != 6 or rows.duplicated(["variant", "seed"]).any()
            or set(zip(rows.variant, rows.seed)) != {(v,s) for s in SEEDS for v in ("E1","E3")}
            or not np.isfinite(rows[list(METRICS)].to_numpy()).all()):
        raise ValueError("summary requires all six runs; never omit unfavorable seeds")
    summary = rows.groupby("variant")[list(METRICS)].agg(["mean", "std"])
    paired = rows.pivot(index="seed", columns="variant", values="acer")
    paired["delta_E3_minus_E1"] = paired.E3 - paired.E1
    paired.attrs["delta_mean"] = float(paired.delta_E3_minus_E1.mean())
    paired.attrs["delta_sample_sd_ddof1"] = float(paired.delta_E3_minus_E1.std(ddof=1))
    return summary, paired
