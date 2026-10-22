"""Descriptive error against fixed pseudo-depth targets, not measured 3-D truth."""
from __future__ import annotations

import pandas as pd
import torch


def depth_error_rows(prediction: torch.Tensor, target: torch.Tensor,
                     labels: torch.Tensor, sample_ids, video_ids) -> list[dict]:
    if prediction.shape != target.shape or prediction.ndim != 4:
        raise ValueError("depth prediction and target must share NCHW shape")
    if not torch.isfinite(prediction).all() or not torch.isfinite(target).all():
        raise ValueError("depth prediction and target must be finite")
    error = (prediction - target).abs().flatten(1)
    mask = (target > 1e-6).flatten(1)
    return [{"sample_id":str(sample), "video_id":str(video), "label":int(label),
             "mae_full":float(values.mean()), "masked_error_sum":float(values[valid].sum()),
             "masked_pixels":int(valid.sum())}
            for sample, video, label, values, valid in
            zip(sample_ids, video_ids, labels, error, mask)]


def summarize_depth_errors(frame: pd.DataFrame) -> dict:
    if frame.empty or frame.sample_id.duplicated().any():
        raise ValueError("depth rows must be nonempty with unique sample IDs")
    if (frame.groupby("video_id").label.nunique() != 1).any():
        raise ValueError("depth rows have conflicting video labels")
    result = {}
    for label, name in ((0, "attack"), (1, "live")):
        subset = frame[frame.label == label]
        count = int(subset.masked_pixels.sum())
        result[name] = {"frames":int(len(subset)), "videos":int(subset.video_id.nunique()),
                        "frame_mean_mae_full":float(subset.mae_full.mean()) if len(subset) else None,
                        "video_mean_mae_full":float(subset.groupby("video_id").mae_full.mean().mean()) if len(subset) else None,
                        "target_mask_pixels":count,
                        "pixel_weighted_mae_target_mask":float(subset.masked_error_sum.sum() / count) if label == 1 and count else None}
    return {"target":"fixed pseudo-depth after PadDataset normalization; not true 3D",
            "mask":"target > 1e-6; masked metric for live only",
            "prediction_clipped":False, "by_class":result}
