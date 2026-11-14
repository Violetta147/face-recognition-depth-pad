"""Video-level metrics for the OULU-NPU benchmark."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .metrics import roc_auc


def oulu_metrics(videos: pd.DataFrame, threshold: float | None = None) -> dict:
    labels = videos.label.to_numpy()
    scores = videos.score.to_numpy(dtype=float)
    if videos.video_id.duplicated().any() or not np.isin(labels, [0, 1]).all() or not np.isfinite(scores).all():
        raise ValueError("expected unique videos, binary labels and finite scores")
    groups = videos.attack_type.to_numpy()
    live = groups == "live"
    print_attack = np.isin(groups, ["print1", "print2"])
    replay_attack = np.isin(groups, ["replay1", "replay2"])
    if not np.array_equal(live, labels == 1) or not (live | print_attack | replay_attack).all():
        raise ValueError("access types and binary labels disagree")
    if not all(mask.any() for mask in (live, print_attack, replay_attack)):
        raise ValueError("all three presentation groups are required")
    cuts = np.unique(scores)
    cuts = np.r_[cuts, np.nextafter(cuts[-1], np.inf)]
    live_scores, attacks = np.sort(scores[live]), np.sort(scores[~live])
    miss = np.searchsorted(live_scores, cuts) / len(live_scores)
    false_accept = (len(attacks) - np.searchsorted(attacks, cuts)) / len(attacks)
    eer_index = np.lexsort((cuts, (miss + false_accept) / 2, np.abs(miss - false_accept)))[0]
    if threshold is None:
        threshold = float(cuts[eer_index])
    if not np.isfinite(threshold):
        raise ValueError("threshold must be finite")
    rejected = scores < threshold
    bpcer = float(rejected[live].mean())
    apcer_print = float((~rejected[print_attack]).mean())
    apcer_replay = float((~rejected[replay_attack]).mean())
    apcer = max(apcer_print, apcer_replay)
    return {"threshold": threshold, "apcer": apcer, "bpcer": bpcer, "acer": (apcer + bpcer) / 2,
            "apcer_print": apcer_print, "apcer_replay": apcer_replay,
            "apcer_pooled": float((~rejected[~live]).mean()),
            "eer": float((miss[eer_index] + false_accept[eer_index]) / 2),
            "auc": roc_auc(labels, scores),
            "counts": {"live": int(live.sum()), "print": int(print_attack.sum()), "replay": int(replay_attack.sum()),
                       "live_rejected": int((rejected & live).sum()),
                       "print_accepted": int((~rejected & print_attack).sum()),
                       "replay_accepted": int((~rejected & replay_attack).sum())}}


def attach_attack_types(videos: pd.DataFrame, manifest: pd.DataFrame) -> pd.DataFrame:
    types = manifest[["video_id", "attack_type"]].drop_duplicates()
    return videos.merge(types, on="video_id", how="left", validate="one_to_one")
