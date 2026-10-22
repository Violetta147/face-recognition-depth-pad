"""Score a frozen run checkpoint on validation or test without retuning its threshold."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch
import yaml
from torch.utils.data import DataLoader

from deepface_pad.data import PadDataset, depth_supervision_required
from deepface_pad.metrics import aggregate_video_scores, evaluate_scores
from deepface_pad.preflight import inspect_training_inputs
from deepface_pad.train import build_model, score_loader


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--split", choices=["val", "test"], default="test")
    parser.add_argument("--manifest", help="optional manifest override")
    parser.add_argument("--data-root", help="optional data root override")
    parser.add_argument("--round6-freeze", help="required six-run freeze for Round 6 test")
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    config = yaml.safe_load((run_dir / "config.yaml").read_text(encoding="utf-8"))
    if config.get("round6_registration") and args.split == "test":
        from deepface_pad.round6 import Batch
        if not args.round6_freeze or args.manifest or args.data_root:
            raise SystemExit("Round 6 test requires --round6-freeze and no data overrides")
        batch = Batch(Path(__file__).resolve().parents[1], Path(config["round6_registration"]).parent)
        if Path(args.round6_freeze).resolve() != batch.freeze_path.resolve():
            raise SystemExit("wrong Round 6 freeze path")
        state = batch.verify_freeze()
        if run_dir.resolve() not in {Path(item["run"]).resolve() for item in state["runs"].values()}:
            raise SystemExit("run does not belong to the frozen six-run batch")
    manifest = args.manifest or config["data"]["manifest"]
    data_root = args.data_root or config["data"]["root"]
    config["data"]["manifest"] = manifest
    config["data"]["root"] = data_root
    threshold_path = run_dir / "threshold.json"
    if not threshold_path.is_file():
        raise SystemExit("threshold.json is missing; freeze the validation threshold before scoring test")
    threshold_payload = json.loads(threshold_path.read_text(encoding="utf-8"))
    if threshold_payload.get("source") != "validation":
        raise SystemExit("refusing to score with a threshold not recorded as validation-derived")
    threshold = float(threshold_payload["threshold"])

    require_depth = depth_supervision_required(config)
    if require_depth:
        saved_snapshot = json.loads((run_dir / "depth_input_snapshot.json").read_text(encoding="utf-8"))
        _, current_snapshot = inspect_training_inputs(config)
        if current_snapshot is None:
            raise SystemExit("depth preflight did not return a snapshot")
        if saved_snapshot.get("files") != current_snapshot.get("files"):
            raise SystemExit("depth manifest or provenance files changed since training")
        saved_checksums = saved_snapshot.get("depth_audit", {}).get("artifact_checksums")
        current_checksums = current_snapshot.get("depth_audit", {}).get("artifact_checksums")
        if saved_checksums != current_checksums:
            raise SystemExit("depth artifacts changed since training")
    dataset = PadDataset(
        manifest,
        data_root,
        args.split,
        config["data"].get("image_size", 256),
        augment=False,
        require_depth=require_depth,
        normalization=config["data"].get("normalization", "imagenet"),
    )
    loader = DataLoader(
        dataset,
        batch_size=config["training"].get("batch_size", 16),
        shuffle=False,
        num_workers=config["training"].get("workers", 0),
    )
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = build_model(config).to(device)
    checkpoint = torch.load(run_dir / "best.ckpt", map_location=device, weights_only=False)
    model.load_state_dict(checkpoint["model"])

    frame_scores = score_loader(model, loader, device)
    video_scores = aggregate_video_scores(
        frame_scores,
        config.get("evaluation", {}).get("aggregation", "mean"),
    )
    metrics = evaluate_scores(
        video_scores["label"].to_numpy(),
        video_scores["score"].to_numpy(),
        threshold=threshold,
    ).to_dict()
    frame_scores.to_csv(run_dir / f"{args.split}_frame_scores.csv", index=False)
    video_scores.to_csv(run_dir / f"{args.split}_scores.csv", index=False)
    (run_dir / f"{args.split}_metrics.json").write_text(
        json.dumps(metrics, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
