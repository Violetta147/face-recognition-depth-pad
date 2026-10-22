import importlib.util
from pathlib import Path

import pandas as pd
import pytest
import torch

from deepface_pad.depth_evaluation import depth_error_rows, summarize_depth_errors


def test_depth_mae_keeps_mask_denominator_and_classes_separate():
    target = torch.tensor([[[[1., 0.], [0., 0.]]], [[[1., 1.], [0., 0.]]], [[[0., 0.], [0., 0.]]]])
    prediction = torch.zeros_like(target)
    prediction[2] = .2
    rows = depth_error_rows(prediction, target, torch.tensor([1., 1., 0.]), ["a", "b", "c"], ["v1", "v1", "v2"])
    report = summarize_depth_errors(pd.DataFrame(rows))
    live, attack = report["by_class"]["live"], report["by_class"]["attack"]
    assert live["frame_mean_mae_full"] == pytest.approx(.375)
    assert live["target_mask_pixels"] == 3
    assert live["pixel_weighted_mae_target_mask"] == 1.
    assert attack["frame_mean_mae_full"] == pytest.approx(.2)
    assert attack["pixel_weighted_mae_target_mask"] is None
    assert not report["prediction_clipped"]
    prediction[0, 0, 0, 0] = float("nan")
    with pytest.raises(ValueError, match="finite"):
        depth_error_rows(prediction, target, torch.tensor([1., 1., 0.]), ["a", "b", "c"], ["v1", "v1", "v2"])


@pytest.mark.parametrize("normalization", ["imagenet", "cdcn_official"])
def test_visualized_rgb_inverts_the_actual_model_normalization(normalization):
    path = Path(__file__).resolve().parents[1] / "scripts/visualize_depth_cases.py"
    spec = importlib.util.spec_from_file_location("depth_visualization", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rgb = torch.tensor([30., 130., 230.]) / 255
    if normalization == "imagenet":
        tensor = (rgb - torch.tensor([.485, .456, .406])) / torch.tensor([.229, .224, .225])
    else:
        tensor = (rgb - .5) / (128 / 255)
    image = module._rgb_image(tensor[:, None, None], 1, normalization)
    assert all(abs(value - expected) <= 1 for value, expected in zip(image.getpixel((0, 0)), [30, 130, 230]))
