from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

try:
    import torch
    from torch.utils.data import Dataset
    from torchvision.transforms import v2
except ImportError:  # Manifest tooling remains usable without the training extras.
    torch = None
    v2 = None
    Dataset = object

MANIFEST_COLUMNS = ["sample_id", "split", "subject_id", "video_id", "frame_index", "image_path", "depth_path", "label", "attack_type"]


def manifest_checksum(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def depth_supervision_required(config: dict) -> bool:
    """Return whether a training config consumes pseudo-depth targets."""
    model_name = config.get("model", {}).get("name")
    if model_name == "cdcn":
        return True
    if model_name != "cdcn_mt_lite":
        return False
    stages = config.get("training", {}).get("stages", [{"name": "joint"}])
    uses_depth_stage = any(stage.get("name") in {"depth", "joint"} for stage in stages)
    loss = config.get("loss", {})
    uses_depth_loss = loss.get("lambda_abs", 1.0) > 0 or loss.get("lambda_contrast", 0.5) > 0
    return uses_depth_stage and uses_depth_loss


def validate_manifest(
    path: str | Path,
    data_root: str | Path,
    require_subject_disjoint: bool = False,
    check_files: bool = True,
    require_depth: bool = False,
) -> list[str]:
    frame = pd.read_csv(path, keep_default_na=False, dtype={"subject_id": str, "video_id": str})
    errors: list[str] = []
    missing = set(MANIFEST_COLUMNS).difference(frame.columns)
    if missing:
        return [f"missing columns: {sorted(missing)}"]
    if frame["sample_id"].duplicated().any():
        errors.append("duplicate sample_id")
    if not frame["label"].isin([0, 1]).all():
        errors.append("labels must be 0 or 1")
    if not frame["split"].isin(["train", "val", "test"]).all():
        errors.append("split must be train, val, or test")
    if require_depth:
        missing_depth_targets = frame.loc[(frame["label"] == 1) & (frame["depth_path"] == ""), "sample_id"].astype(str).tolist()
        if missing_depth_targets:
            errors.append(f"missing bona fide depth_path: {missing_depth_targets[:10]}")
    overlap = frame.groupby("video_id")["split"].nunique()
    if (overlap > 1).any():
        errors.append(f"video leakage: {overlap[overlap > 1].index.tolist()[:10]}")
    if require_subject_disjoint:
        overlap = frame.groupby("subject_id")["split"].nunique()
        if (overlap > 1).any():
            errors.append(f"subject leakage: {overlap[overlap > 1].index.tolist()[:10]}")
    if check_files:
        root = Path(data_root)
        missing_images = [p for p in frame["image_path"] if not (root / p).is_file()]
        missing_depth = [p for p in frame["depth_path"] if p and not (root / p).is_file()]
        if missing_images:
            errors.append(f"missing image files: {missing_images[:10]}")
        if missing_depth:
            errors.append(f"missing depth files: {missing_depth[:10]}")
    return errors


class PadDataset(Dataset):
    def __init__(
        self,
        manifest: str | Path,
        data_root: str | Path,
        split: str,
        image_size: int = 256,
        augment: bool = False,
        require_depth: bool = False,
    ):
        if torch is None or v2 is None:
            raise RuntimeError("PadDataset requires the torch and torchvision training dependencies")
        frame = pd.read_csv(manifest, keep_default_na=False, dtype={"subject_id": str, "video_id": str})
        self.rows = frame[frame["split"] == split].reset_index(drop=True)
        if require_depth:
            missing = self.rows.loc[(self.rows["label"] == 1) & (self.rows["depth_path"] == ""), "sample_id"].astype(str).tolist()
            if missing:
                raise ValueError(f"split {split} is missing bona fide depth_path: {missing[:10]}")
        self.root = Path(data_root)
        transforms = [v2.ToImage(), v2.Resize((image_size, image_size)), v2.ToDtype(torch.float32, scale=True)]
        if augment:
            transforms.insert(1, v2.RandomHorizontalFlip())
        transforms.append(v2.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)))
        self.transform = v2.Compose(transforms)

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int) -> dict[str, object]:
        row = self.rows.iloc[index]
        image = self.transform(Image.open(self.root / row.image_path).convert("RGB"))
        if row.depth_path:
            path = self.root / row.depth_path
            depth = np.load(path) if path.suffix == ".npy" else np.asarray(Image.open(path).convert("F"), dtype=np.float32)
            depth = torch.from_numpy(np.asarray(depth, dtype=np.float32))[None]
            depth = torch.nn.functional.interpolate(depth[None], (32, 32), mode="bilinear", align_corners=False)[0]
            maximum = depth.max()
            if maximum > 1:
                depth = depth / maximum
        else:
            depth = torch.zeros(1, 32, 32)
        return {"image": image, "depth": depth, "label": torch.tensor(float(row.label)), "video_id": str(row.video_id), "sample_id": str(row.sample_id)}
