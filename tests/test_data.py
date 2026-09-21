from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from PIL import Image

torch = pytest.importorskip("torch")
pytest.importorskip("torchvision")

from deepface_pad.data import MANIFEST_COLUMNS, PadDataset


def test_depth_augmentation_flips_rgb_and_target_together(tmp_path: Path, monkeypatch):
    pixels = np.zeros((2, 2, 3), dtype=np.uint8)
    pixels[:, 0, 0] = 255
    Image.fromarray(pixels).save(tmp_path / "image.png")
    np.save(tmp_path / "depth.npy", np.array([[1.0, 0.0], [1.0, 0.0]], dtype=np.float32))
    pd.DataFrame(
        [["sample", "train", "1", "video", 0, "image.png", "depth.npy", 1, "live"]],
        columns=MANIFEST_COLUMNS,
    ).to_csv(tmp_path / "manifest.csv", index=False)
    monkeypatch.setattr(torch, "rand", lambda *args, **kwargs: torch.tensor(0.0))

    sample = PadDataset(
        tmp_path / "manifest.csv",
        tmp_path,
        "train",
        image_size=2,
        augment=True,
        require_depth=True,
        normalization="cdcn_official",
    )[0]

    assert torch.all(sample["depth"][..., 0] == 0)
    assert torch.all(sample["depth"][..., -1] == 1)
    assert torch.all(sample["image"][0, :, 0] < 0)
    assert torch.all(sample["image"][0, :, -1] > 0)
