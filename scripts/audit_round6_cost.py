"""Audit saved cost CSV/JSON against preflight; never run a model or touch CUDA."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import zipfile

import pandas as pd

from deepface_pad.cost import MODELS, orders, summarize


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def same(actual, expected):
    """Allow roundoff across NumPy versions, never missing keys or altered counts."""
    if isinstance(expected, dict):
        return isinstance(actual, dict) and actual.keys() == expected.keys() and all(
            same(actual[k], v) for k, v in expected.items())
    if isinstance(expected, list):
        return isinstance(actual, list) and len(actual) == len(expected) and all(
            same(a, b) for a, b in zip(actual, expected))
    if isinstance(expected, float):
        return isinstance(actual, (int, float)) and math.isfinite(actual) and math.isclose(
            actual, expected, rel_tol=1e-12, abs_tol=1e-10)
    return type(actual) is type(expected) and actual == expected


def audit(folder, *, plan, approved, profiles, source_lock):
    folder = Path(folder)
    require(not (folder / "failure.json").exists(), "failure receipt exists; inspect before acceptance")
    registration = read(folder / "registration.json")
    result = read(folder / "results.json")
    reg_sha, raw_sha = sha(folder / "registration.json"), sha(folder / "timings.csv")
    require(approved["status"].startswith("PASS:"), "preflight was not approved")
    require(reg_sha == approved["registration_sha256"] == result["registration_sha256"],
            "registration changed after preflight")
    require(raw_sha == result["raw_sha256"], "raw timing hash differs")
    require(registration["source"] == source_lock, "source differs from delivered ZIP")
    require(registration["source"]["commit"] == approved["source_commit"], "source commit differs")
    require(registration["plan"] == plan, "plan differs from preregistration")
    require(registration["models"] == profiles == result["models"], "model profiles differ")
    require(registration["inputs"] == approved["inputs"], "validation input identity differs")
    schedule = [list(order) for order in orders(plan["timing"]["order_seed"])]
    require(registration["model_orders"] == approved["model_orders"] == schedule, "schedule differs")
    require(result["scope"] == plan["limits"], "measurement scope differs")
    raw = pd.read_csv(folder / "timings.csv")
    replay = summarize(raw, plan["timing"])
    require(same(result["summary"], replay), "saved statistics differ from raw timing replay")
    expected_n = len(schedule) * plan["timing"]["iterations_per_block"]
    require(all(replay["pooled"][m]["cuda_event_forward_ms"]["n"] == expected_n for m in MODELS),
            "incorrect sample count")
    deltas = {}
    for m in ("E3", "E4"):
        deltas[m] = {"params_added": profiles[m]["params"] - profiles["E1"]["params"],
                     "params_added_percent": (profiles[m]["params"] / profiles["E1"]["params"] - 1)*100,
                     "checkpoint_bytes_added": profiles[m]["checkpoint_file_bytes"] - profiles["E1"]["checkpoint_file_bytes"]}
        for scope in ("cuda_event_forward_ms", "synchronized_host_forward_ms"):
            deltas[m][scope] = {}
            for quantile in ("p50", "p95"):
                base, value = replay["pooled"]["E1"][scope][quantile], replay["pooled"][m][scope][quantile]
                deltas[m][scope][quantile] = {"delta_ms": value-base, "delta_percent": (value/base-1)*100}
    return {"status":"PASS: saved Round 6 cost audit", "registration_sha256":reg_sha,
            "raw_sha256":raw_sha, "results_sha256":sha(folder / "results.json"),
            "source_commit":registration["source"]["commit"], "models":profiles,
            "environment":registration["environment"], "inputs":registration["inputs"],
            "summary":replay, "delta_vs_E1":deltas, "measured_rows":len(raw),
            "model_blocks":len(replay["blocks"]), "scope":result["scope"],
            "audit_scope":"Saved artifacts only; no training, inference or new timing. All slow samples retained.",
            "limits":"One A100 runtime and two fixed inputs; repeated forwards are not independent training seeds or end-to-end webcam measurements."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folder", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    with zipfile.ZipFile(root / "artifacts/round6-cost-colab-20261022/DeepFace-PAD-Round6-cost-source.zip") as archive:
        lock = json.loads(archive.read("DeepFace-PAD/SOURCE_LOCK.json"))
    report = audit(args.folder, plan=read(root / "configs/round6_cost.json"),
        approved=read(root / "reports/ROUND_6_COST_PREFLIGHT_REVIEW_2026-10-22.json"),
        profiles=read(root / "reports/ROUND_6_COST_STATIC_2026-10-22.json")["models"], source_lock=lock)
    args.evidence.mkdir(parents=True, exist_ok=True)
    names = {"registration.json":"registration_sha256", "timings.csv":"raw_sha256", "results.json":"results_sha256"}
    for name, key in names.items():
        payload = (args.folder / name).read_bytes()
        require(hashlib.sha256(payload).hexdigest() == report[key], "source changed during recovery")
        destination = args.evidence / name
        if destination.exists():
            require(destination.read_bytes() == payload, "existing evidence differs; preserve it")
        else:
            destination.write_bytes(payload)
    report["local_evidence_directory"] = str(args.evidence)
    report["audit_code"] = {"script_sha256":sha(__file__),
        "commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=root,text=True).strip()}
    text = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output.exists():
        require(read(args.output) == report, "existing report differs; preserve and inspect")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(json.dumps({k:report[k] for k in ("status","measured_rows","model_blocks","delta_vs_E1")},indent=2))


if __name__ == "__main__":
    main()
