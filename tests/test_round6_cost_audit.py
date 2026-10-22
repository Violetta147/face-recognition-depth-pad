"""Synthetic timings test audit correctness, never substitute for A100 results."""
import copy
import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest

from deepface_pad.cost import orders, summarize

spec = importlib.util.spec_from_file_location("cost_audit", Path(__file__).resolve().parents[1] / "scripts/audit_round6_cost.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


@pytest.fixture
def block(tmp_path):
    def save(name, value):
        (tmp_path / name).write_text(json.dumps(value), encoding="utf-8")
    timing = {"order_seed":20261022,"iterations_per_block":4}
    plan = {"timing":timing,"limits":"fixture only"}
    source = {"commit":"fixture", "files":{"cost.py":"fixture hash"}}
    profiles = {m:{"params":100 if m=="E1" else 101,"checkpoint_file_bytes":200} for m in ("E1","E3","E4")}
    schedule = [list(v) for v in orders(timing["order_seed"])]
    registration = {"source":source,"plan":plan,"models":profiles,"inputs":["fixture validation"],
                    "environment":{"gpu":"fixture"},"model_orders":schedule}
    save("registration.json",registration)
    raw = pd.DataFrame([{"round":r,"position":p,"model":m,"iteration":i,"input_index":i%2,
        "cuda_event_forward_ms":float(i+1),"synchronized_host_forward_ms":float(i+2)}
        for r, seq in enumerate(schedule) for p,m in enumerate(seq) for i in range(4)])
    raw.to_csv(tmp_path / "timings.csv",index=False)
    result = {"registration_sha256":module.sha(tmp_path / "registration.json"),
        "raw_sha256":module.sha(tmp_path / "timings.csv"),"models":profiles,
        "scope":plan["limits"],"summary":summarize(raw,timing)}
    save("results.json",result)
    approved = {"status":"PASS: fixture", "registration_sha256":result["registration_sha256"],
        "source_commit":"fixture","inputs":registration["inputs"],"model_orders":schedule}
    return tmp_path, {"plan":plan,"approved":approved,"profiles":profiles,"source_lock":source}, save, raw, result


def test_audit_replays_complete_block_and_keeps_all_samples(block):
    folder, kwargs, _, _, _ = block
    report = module.audit(folder,**kwargs)
    assert report["measured_rows"] == 72 and report["model_blocks"] == 18
    assert report["summary"]["pooled"]["E1"]["cuda_event_forward_ms"]["p95"] == 4
    assert report["delta_vs_E1"]["E3"]["params_added"] == 1


@pytest.mark.parametrize("change",["registration","raw","statistics","profile","schedule","failure"])
def test_audit_rejects_changed_identity_or_statistics(block, change):
    folder, kwargs, save, raw, result = block
    if change == "registration":
        (folder / "registration.json").write_text("{}")
    elif change == "raw":
        raw.iloc[:-1].to_csv(folder / "timings.csv",index=False)
    elif change == "statistics":
        result["summary"]["pooled"]["E1"]["cuda_event_forward_ms"]["p95"] += .01
        save("results.json",result)
    elif change == "profile":
        kwargs["profiles"] = copy.deepcopy(kwargs["profiles"])
        kwargs["profiles"]["E3"]["params"] += 1
    elif change == "schedule":
        raw.iloc[::-1].to_csv(folder / "timings.csv",index=False)
        result["raw_sha256"] = module.sha(folder / "timings.csv")
        save("results.json",result)
    else:
        save("failure.json",{"exception":"fixture"})
    with pytest.raises(ValueError):
        module.audit(folder,**kwargs)


def test_roundoff_tolerance_never_allows_missing_fields_or_changed_counts():
    assert module.same({"p95":1+1e-13,"n":1200},{"p95":1.,"n":1200})
    assert not module.same({"p95":1.01,"n":1200},{"p95":1.,"n":1200})
    assert not module.same({"p95":1.},{"p95":1.,"n":1200})
    assert not module.same({"n":1200.},{"n":1200})
