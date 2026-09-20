"""Export auditable RGB/target/mask/predicted-depth cases from a completed E1 run."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
import torch
import yaml
from PIL import Image, ImageDraw, ImageOps
from torch.utils.data import DataLoader

from deepface_pad.data import PadDataset
from deepface_pad.preflight import inspect_training_inputs
from deepface_pad.reporting import select_depth_cases
from deepface_pad.train import build_model


MEAN = np.asarray([0.485, 0.456, 0.406], dtype=np.float32)[:, None, None]
STD = np.asarray([0.229, 0.224, 0.225], dtype=np.float32)[:, None, None]


def _rgb_image(tensor: torch.Tensor, size: int) -> Image.Image:
    array = tensor.detach().cpu().numpy() * STD + MEAN
    array = np.clip(array.transpose(1, 2, 0) * 255.0, 0, 255).astype(np.uint8)
    return ImageOps.fit(Image.fromarray(array, mode="RGB"), (size, size))


def _map_image(array: np.ndarray, size: int) -> Image.Image:
    array = np.asarray(array, dtype=np.float32)
    array = np.clip(array, 0.0, 1.0)
    pixels = (array * 255.0).astype(np.uint8)
    return Image.fromarray(pixels, mode="L").resize((size, size), Image.Resampling.NEAREST).convert("RGB")


def _histogram_image(target: np.ndarray, prediction: np.ndarray, size: int) -> Image.Image:
    canvas = Image.new("RGB", (size, size), "white")
    draw = ImageDraw.Draw(canvas)
    margin = 24
    draw.line((margin, size - margin, size - 8, size - margin), fill="#777777", width=1)
    draw.line((margin, 8, margin, size - margin), fill="#777777", width=1)
    bins = np.linspace(0.0, 1.0, 25)
    target_hist, _ = np.histogram(target.ravel(), bins=bins)
    pred_hist, _ = np.histogram(prediction.ravel(), bins=bins)
    peak = max(int(target_hist.max()), int(pred_hist.max()), 1)
    usable_width = size - margin - 10
    usable_height = size - margin - 12
    for histogram, colour in ((target_hist, "#2878B5"), (pred_hist, "#E07A1F")):
        points = []
        for index, value in enumerate(histogram):
            x = margin + index * usable_width / max(1, len(histogram) - 1)
            y = size - margin - int(value / peak * usable_height)
            points.append((x, y))
        if len(points) > 1:
            draw.line(points, fill=colour, width=3)
    draw.text((margin + 4, 10), "target", fill="#2878B5")
    draw.text((margin + 70, 10), "prediction", fill="#E07A1F")
    return canvas


def _write_case(
    destination: Path,
    sample: dict[str, object],
    target: np.ndarray,
    prediction: np.ndarray,
    metadata: dict[str, object],
) -> None:
    panel = 224
    caption = 72
    sheet = Image.new("RGB", (panel * 5, panel + caption), "white")
    panels = [
        ("RGB", _rgb_image(sample["image"], panel)),
        ("target depth", _map_image(target, panel)),
        ("target mask", _map_image((target > 1e-6).astype(np.float32), panel)),
        ("predicted depth", _map_image(prediction, panel)),
        ("histogram", _histogram_image(target, prediction, panel)),
    ]
    draw = ImageDraw.Draw(sheet)
    for index, (title, image) in enumerate(panels):
        x = index * panel
        sheet.paste(image, (x, 0))
        draw.text((x + 8, panel + 4), title, fill="black")
    result = "CORRECT" if metadata["correct"] else "ERROR"
    details = (
        f"{result} | sample={metadata['sample_id']} | video={metadata['video_id']} | "
        f"label={metadata['label']} | score={float(metadata['score']):.6f} | "
        f"threshold={float(metadata['threshold']):.6f}"
    )
    draw.text((8, panel + 30), details, fill="#333333")
    sheet.save(destination)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, help="completed E1 run containing config.yaml and best.ckpt")
    parser.add_argument("--split", choices=["train", "val", "test"], default="val")
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--output-dir", default="reports/e1-depth-cases")
    parser.add_argument("--manifest", help="optional manifest override")
    parser.add_argument("--data-root", help="optional data root override")
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    config = yaml.safe_load((run_dir / "config.yaml").read_text(encoding="utf-8"))
    manifest = args.manifest or config["data"]["manifest"]
    data_root = args.data_root or config["data"]["root"]
    config["data"]["manifest"] = manifest
    config["data"]["root"] = data_root
    threshold_payload = json.loads((run_dir / "threshold.json").read_text(encoding="utf-8"))
    threshold = float(threshold_payload["threshold"])
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    saved_snapshot = json.loads((run_dir / "depth_input_snapshot.json").read_text(encoding="utf-8"))
    _, current_snapshot = inspect_training_inputs(config)
    if current_snapshot is None:
        raise SystemExit("the selected run does not consume pseudo-depth targets")
    if saved_snapshot.get("files") != current_snapshot.get("files"):
        raise SystemExit("depth manifest or provenance files changed since training")
    if saved_snapshot.get("depth_audit", {}).get("artifact_checksums") != current_snapshot.get("depth_audit", {}).get("artifact_checksums"):
        raise SystemExit("depth artifacts changed since training")

    dataset = PadDataset(
        manifest,
        data_root,
        args.split,
        config["data"].get("image_size", 256),
        augment=False,
        require_depth=True,
    )
    loader = DataLoader(
        dataset,
        batch_size=config["training"].get("batch_size", 16),
        shuffle=False,
        num_workers=config["training"].get("workers", 0),
    )
    model = build_model(config).to(device)
    checkpoint = torch.load(run_dir / "best.ckpt", map_location=device, weights_only=False)
    model.load_state_dict(checkpoint["model"])
    model.eval()

    rows: list[dict[str, object]] = []
    with torch.no_grad():
        for batch in loader:
            output = model(batch["image"].to(device))
            scores = torch.sigmoid(output["logit"]) if "logit" in output else output["score"]
            for sample_id, video_id, label, score in zip(
                batch["sample_id"], batch["video_id"], batch["label"], scores.cpu()
            ):
                label_value = int(label.item())
                score_value = float(score.item())
                prediction = int(score_value >= threshold)
                rows.append(
                    {
                        "sample_id": str(sample_id),
                        "video_id": str(video_id),
                        "label": label_value,
                        "score": score_value,
                        "threshold": threshold,
                        "prediction": prediction,
                        "correct": prediction == label_value,
                    }
                )

    selected = select_depth_cases(rows, args.count)
    row_by_sample = {str(row.sample_id): index for index, row in dataset.rows.iterrows()}
    destination = Path(args.output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    index_rows = []
    with torch.no_grad():
        for order, metadata in enumerate(selected, start=1):
            dataset_index = row_by_sample[str(metadata["sample_id"])]
            sample = dataset[dataset_index]
            output = model(sample["image"][None].to(device))
            prediction = output["depth"][0, 0].detach().cpu().numpy()
            target = sample["depth"][0].detach().cpu().numpy()
            file_name = f"{order:02d}_{metadata['sample_id']}.png"
            _write_case(destination / file_name, sample, target, prediction, metadata)
            index_rows.append({**metadata, "file": file_name})

    with (destination / "index.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(index_rows[0].keys()) if index_rows else [])
        if index_rows:
            writer.writeheader()
            writer.writerows(index_rows)
    error_count = sum(not bool(row["correct"]) for row in index_rows)
    print(f"wrote {len(index_rows)} cases ({error_count} errors) to {destination}")


if __name__ == "__main__":
    main()
