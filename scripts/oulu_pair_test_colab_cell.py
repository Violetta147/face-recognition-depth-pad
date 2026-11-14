"""Paste as a new cell after PAIR_DEV_READY in the E1–E3 Colab notebook."""
import json
from pathlib import Path

import pandas as pd
import torch
import yaml
from torch.utils.data import DataLoader

from deepface_pad.colab_cache import copy_progress, file_hash, restore_cache
from deepface_pad.data import PadDataset
from deepface_pad.metrics import aggregate_video_scores
from deepface_pad.oulu_fast import checked_manifest
from deepface_pad.oulu_metrics import attach_attack_types, oulu_metrics
from deepface_pad.train import build_model, score_loader
from zipfile import ZipFile


def score_locked_pair(base, work, root):
    pair = base / "cdcn-pair-p1/seed43-1794667766717400448"
    lock_path = pair / "pair_dev_lock.json"
    lock_sha = "85f5624c445429b71156317498473633c2eb4d266ac29e6a684e07dd6f6e5b8d"
    if file_hash(lock_path) != lock_sha:
        raise ValueError("Pair Dev lock differs from the verified file")
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    for record in lock["runs"].values():
        run = Path(record["run"])
        for name, expected in record["sha256"].items():
            if file_hash(run / name) != expected:
                raise ValueError(f"Locked file changed: {run / name}")

    name = "rgb-p1-test-0a9c316e4899e0d87b7c.zip"
    manifest = root / "p1/test.csv"
    test_sha = "0a514b83c5e58465d767c597d9098282e829202d177ba37612c92cf0de71cb34"
    if not manifest.is_file() or not manifest.with_suffix(".json").is_file():
        archive = copy_progress(base / "prepared-cache" / name, work / name, "Fetch cached Test RGB")
        with ZipFile(archive) as z:
            index = json.loads(z.read("CACHE_INDEX.json"))
        if index["sha256"]["p1/test.csv"] != test_sha:
            raise ValueError("Unexpected Test manifest in RGB archive")
        restore_cache(root, archive, index["identity"])
    if file_hash(manifest) != test_sha:
        raise ValueError("Unexpected Test manifest")
    test, _ = checked_manifest(manifest, root, "test")
    if len(test) != 4800 or test.video_id.nunique() != 600 or test.depth_path.ne("").any():
        raise ValueError("Expected 600 Test videos and 4,800 RGB frames")
    if not torch.cuda.is_available():
        raise RuntimeError("Connect the GPU runtime used for the pair first")
    device = torch.device("cuda")
    results = {}
    for branch, record in lock["runs"].items():
        run = Path(record["run"])
        output = pair / "locked-test" / branch
        output.mkdir(parents=True, exist_ok=True)
        result_path = output / "test_metrics.json"
        binding = {"pair_dev_lock_sha256": lock_sha, "test_manifest_sha256": test_sha}
        if result_path.is_file():
            saved = json.loads(result_path.read_text(encoding="utf-8"))
            if saved["binding"] != binding:
                raise ValueError(f"Existing result has different inputs: {result_path}")
            results[branch] = saved["metrics"]
            continue
        config = yaml.safe_load((run / "config.yaml").read_text(encoding="utf-8"))
        threshold = json.loads((run / "threshold.json").read_text(encoding="utf-8"))
        if threshold["source"] != "validation" or threshold["threshold"] != lock["dev_metrics"][branch]["threshold"]:
            raise ValueError(f"Unexpected threshold for {branch}")
        dataset = PadDataset(manifest, root, "test", config["data"]["image_size"],
                             normalization=config["data"]["normalization"])
        loader = DataLoader(dataset, batch_size=config["training"]["batch_size"],
                            num_workers=config["training"]["workers"])
        model = build_model(config).to(device)
        model.load_state_dict(torch.load(run / "best.ckpt", map_location=device, weights_only=True)["model"])
        print("Scoring", branch, flush=True)
        frames = score_loader(model, loader, device)
        videos = attach_attack_types(aggregate_video_scores(frames, config["evaluation"]["aggregation"]), test)
        results[branch] = oulu_metrics(videos, threshold["threshold"])
        frames.to_csv(output / "test_frame_scores.csv", index=False)
        videos.to_csv(output / "test_scores.csv", index=False)
        temp = result_path.with_suffix(".tmp")
        temp.write_text(json.dumps({"binding": binding, "metrics": results[branch]}, indent=2), encoding="utf-8")
        temp.replace(result_path)
        del model
    print(json.dumps(results, indent=2))
    print("PAIR_TEST_READY", pair / "locked-test", flush=True)


if __name__ == "__main__":
    score_locked_pair(BASE, WORK, ROOT)
