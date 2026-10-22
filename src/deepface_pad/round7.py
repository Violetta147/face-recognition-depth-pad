"""Round 7: read-only frozen-score adapter and predeclared case selection."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .figure_data import verify_scores

ROLES = ("corrected", "new_errors", "both_wrong", "both_correct")
SELECTION = ("Within each seed/outcome/attack_type, lexicographically first video_id; "
             "frame at sorted temporal index len//2 (11th of 20); no RGB inspection.")


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def csv(path):
    return pd.read_csv(path, keep_default_na=False, float_precision="round_trip")


def pair_videos(e1, e3, t1, t3, metadata):
    """Require complete one-to-one membership, labels and per-video metadata."""
    keys = ["video_id", "label"]
    if e1.video_id.duplicated().any() or e3.video_id.duplicated().any():
        raise ValueError("duplicate video")
    if not e1[keys].sort_values(keys).reset_index(drop=True).equals(
        e3[keys].sort_values(keys).reset_index(drop=True)):
        raise ValueError("video membership/labels differ")
    cols = ["subject_id", "label", "attack_type", "quality"]
    if (metadata.groupby("video_id")[cols].nunique() != 1).any().any():
        raise ValueError("inconsistent video metadata")
    meta = metadata[["video_id"] + cols].drop_duplicates("video_id")
    result = e1.rename(columns={"score": "E1_score"}).merge(
        e3.rename(columns={"score": "E3_score"}), on=keys, validate="one_to_one")
    result = result.merge(meta, on=keys, how="left", validate="one_to_one", indicator=True)
    if not result._merge.eq("both").all():
        raise ValueError("missing metadata")
    result = result.drop(columns="_merge")
    for model, threshold in (("E1", t1), ("E3", t3)):
        if not np.isfinite(result[f"{model}_score"]).all() or not np.isfinite(threshold):
            raise ValueError("nonfinite score/threshold")
        result[f"{model}_threshold"] = threshold
        result[f"{model}_prediction"] = (result[f"{model}_score"] >= threshold).astype(int)
        result[f"{model}_error"] = result[f"{model}_prediction"] != result.label
        result[f"{model}_error_type"] = np.where(
            ~result[f"{model}_error"], "correct", np.where(result.label == 0, "false_live", "false_spoof"))
    a, b = result.E1_error, result.E3_error
    result["role"] = np.select([a & ~b, ~a & b, a & b], ROLES[:3], default="both_correct")
    return result.sort_values("video_id").reset_index(drop=True)


def choose_cases(paired, manifest):
    rows = []
    for (seed, role, attack), group in paired.groupby(["seed", "role", "attack_type"], sort=True):
        video = group.sort_values("video_id").iloc[0]
        frames = manifest[manifest.video_id == video.video_id].sort_values(["frame_index", "sample_id"])
        frame = frames.iloc[len(frames) // 2]
        row = {**frame.to_dict(), **video.to_dict(), "selection_reason": SELECTION}
        rows.append(row)
    return pd.DataFrame(rows)


def subgroup_table(paired):
    rows = []
    for dimensions in (("attack_type",), ("quality",), ("attack_type", "quality")):
        for keys, group in paired.groupby(["seed", *dimensions], sort=True):
            seed, *values = keys
            for model in ("E1", "E3"):
                for label, kind in ((0, "false_live"), (1, "false_spoof")):
                    subset = group[group.label == label]
                    n = len(subset)
                    errors = int(subset[f"{model}_error"].sum())
                    rows.append({"seed": seed, "model": model, "dimension": "+".join(dimensions),
                                 "stratum": "+".join(map(str, values)), "error_type": kind,
                                 "errors": errors, "denominator": n,
                                 "rate": errors / n if n else None})
    return pd.DataFrame(rows)


def analyze(project, evidence, output):
    project, evidence, output = map(Path, (project, evidence, output))
    audit = read(project / "reports/ROUND_6_RESULTS_2026-10-22.json")
    sources = {}
    def check(path, expected):
        actual = sha(path)
        if actual != expected:
            raise ValueError(f"changed frozen artifact: {path}")
        sources[str(path)] = actual
    check(evidence / "comparison_freeze.json", audit["freeze_sha256"])
    check(evidence / "registration.json", audit["registration_sha256"])
    manifest_path = evidence / "casia_fasd_debug_with_depth.csv"
    check(manifest_path, audit["manifest_sha256"])
    manifest = csv(manifest_path)
    test = manifest[manifest.split == "test"]
    if len(test) != 7200 or test.video_id.nunique() != 360 or test.sample_id.duplicated().any():
        raise ValueError("test membership/counts changed")
    if not test.groupby("video_id").size().eq(20).all():
        raise ValueError("expected 20 frames/video")
    pairs, counts = [], {}
    for seed in (43, 44, 45):
        videos, thresholds = {}, {}
        for model in ("E1", "E3"):
            record = audit["runs"][f"{model}_{seed}"]
            folder = evidence / record["run_id"]
            for name in ("test_scores.csv", "test_frame_scores.csv", "threshold.json", "config.yaml"):
                check(folder / name, record["hashes"][name])
            threshold = read(folder / "threshold.json")
            if threshold["source"] != "validation":
                raise ValueError("threshold must come from validation")
            thresholds[model] = threshold["threshold"]
            videos[model] = csv(folder / "test_scores.csv")
            verify_scores(csv(folder / "test_frame_scores.csv"), videos[model], test,
                          thresholds[model], record["test"])
        pair = pair_videos(videos["E1"], videos["E3"], thresholds["E1"], thresholds["E3"], test)
        pair["seed"] = seed
        for model in ("E1", "E3"):
            pair[f"{model}_run_id"] = audit["runs"][f"{model}_{seed}"]["run_id"]
        counts[str(seed)] = {role: int(pair.role.eq(role).sum()) for role in ROLES}
        if counts[str(seed)] != audit["paired_video_errors"][str(seed)]:
            raise ValueError("paired counts differ from Round 6")
        pairs.append(pair)
    paired = pd.concat(pairs, ignore_index=True)
    cases = choose_cases(paired, test)
    output.mkdir(parents=True, exist_ok=False)
    paired.to_csv(output / "paired_videos.csv", index=False)
    subgroup_table(paired).to_csv(output / "subgroups.csv", index=False)
    cases.to_csv(output / "case_index.csv", index=False)
    coverage = []
    for seed in (43, 44, 45):
        for role in ROLES:
            for attack in sorted(test.attack_type.unique()):
                part = paired[(paired.seed == seed) & (paired.role == role) & (paired.attack_type == attack)]
                coverage.append({"seed": seed, "role": role, "attack_type": attack, "available": len(part)})
    pd.DataFrame(coverage).to_csv(output / "case_coverage.csv", index=False)
    report = {"status": "PASS: saved CSV analysis only", "paired_counts": counts,
              "selection_rule": SELECTION, "selected_cases": len(cases), "sources": sources,
              "scope": "Same 360 videos repeated over seeds, not 1080 independent videos. Quality is metadata, not lighting/blur measurement."}
    (output / "analysis.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report
