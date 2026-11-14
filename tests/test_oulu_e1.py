from pathlib import Path

import pytest

from deepface_pad.data import depth_supervision_required
from deepface_pad.oulu_e1 import e1_config


@pytest.mark.parametrize("batch", [8, 16])
def test_e1_config_binds_full_depth_and_selects_on_dev(tmp_path, batch):
    config = e1_config(tmp_path, tmp_path / "runs", batch)
    assert depth_supervision_required(config)
    assert config["seed"] == 43
    assert config["model"] == {"name": "cdcn_official", "theta": 0.7}
    assert config["training"]["batch_size"] == batch
    assert config["training"]["epochs"] == 5
    assert config["training"]["selection_metric"] == "oulu_video_acer"
    assert config["data"]["image_size"] == 256
    assert Path(config["data"]["manifest"]).name == "train_dev_with_depth.csv"
    assert Path(config["data"]["source_manifest"]).name == "train_dev.csv"


def test_e1_excludes_mobilenet_batch(tmp_path):
    with pytest.raises(ValueError, match="registered candidates"):
        e1_config(tmp_path, tmp_path / "runs", 128)
