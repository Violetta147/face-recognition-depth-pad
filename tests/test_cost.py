import io
import itertools
import json
import zipfile
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
import pytest
import torch

from deepface_pad import cost
from deepface_pad.data import MANIFEST_COLUMNS
from deepface_pad.models import OfficialCDCN, OfficialCDCNWithDepthHead


def test_balanced_schedule_covers_all_orders_and_positions():
    schedule = cost.orders(20261022)
    assert set(schedule) == set(itertools.permutations(cost.MODELS))
    for model in cost.MODELS:
        assert Counter(s.index(model) for s in schedule) == {0:2,1:2,2:2}
    assert schedule == cost.orders(20261022)


def test_quantiles_are_linear_and_reject_invalid_timing():
    stats = cost.quantiles(np.arange(1,101))
    assert stats["n"] == 100 and stats["p50"] == 50.5
    assert stats["p95"] == pytest.approx(95.05)
    for values in ([1], [1,np.nan], [0,1], [-1,2], [1,np.inf]):
        with pytest.raises(ValueError): cost.quantiles(values)


def test_summary_requires_complete_registered_order_and_keeps_slow_samples():
    config = {"iterations_per_block":4,"order_seed":20261022}
    rows = [{"round":r,"position":p,"model":m,"iteration":i,"input_index":i%2,
             "cuda_event_forward_ms":float(i+1),"synchronized_host_forward_ms":float(i+2)}
            for r,order in enumerate(cost.orders(config["order_seed"])) for p,m in enumerate(order) for i in range(4)]
    frame = pd.DataFrame(rows)
    result = cost.summarize(frame,config)
    assert result["pooled"]["E1"]["cuda_event_forward_ms"]["n"] == 24
    assert result["pooled"]["E4"]["cuda_event_forward_ms"]["p95"] == 4
    assert len(result["blocks"]) == 18
    for changed in (frame.iloc[:-1],frame.iloc[::-1]):
        with pytest.raises(ValueError,match="schedule"): cost.summarize(changed,config)


def test_default_cost_gate_does_not_touch_hardware_or_files(tmp_path,monkeypatch):
    monkeypatch.setattr(cost,"prepare",lambda *a: pytest.fail("closed gate reached prepare"))
    with pytest.raises(ValueError,match="RUN_BENCHMARK"):
        cost.run_cost(tmp_path,tmp_path,tmp_path)


def test_validation_selection_and_transform_use_real_zip_images_only(tmp_path):
    rows = [["z_test","test","t","vt",0,"test.png","",1,"live"],
            ["v_live","val","v1","vl",0,"live.png","",1,"live"],
            ["v_attack","val","v0","va",0,"attack.png","",0,"print"]]
    manifest = tmp_path/"manifest.csv"
    pd.DataFrame(rows,columns=MANIFEST_COLUMNS).to_csv(manifest,index=False)
    archive = tmp_path/"dataset.zip"
    with zipfile.ZipFile(archive,"w") as z:
        for name,value in (("live.png",255),("attack.png",0)):
            stream=io.BytesIO();Image.new("RGB",(4,4),(value,)*3).save(stream,format="PNG")
            z.writestr("casia-fasd/"+name,stream.getvalue())
    tensors,metadata = cost.validation_inputs(manifest,archive)
    assert [m["sample_id"] for m in metadata] == ["v_attack","v_live"]
    assert [m["split"] for m in metadata] == ["val","val"]
    assert list(tensors[0].shape) == [1,3,256,256]
    assert tensors[0].mean().item() == pytest.approx(-.5/(128/255))
    assert tensors[1].mean().item() == pytest.approx(.5/(128/255))
    assert metadata[0]["tensor_sha256"] != metadata[1]["tensor_sha256"]


def test_load_rejects_changed_checkpoint_before_unpickling(tmp_path):
    directory = tmp_path/"runs/fake"; directory.mkdir(parents=True)
    (directory/"best.ckpt").write_bytes(b"not a checkpoint")
    plan = {"models":{"E1":{"run_id":"fake","checkpoint_sha256":"different"}}}
    with pytest.raises(ValueError,match="hash"):
        cost.load_models(plan,tmp_path)


def test_official_parameter_counts_and_identical_head_architecture():
    baseline = sum(p.numel() for p in OfficialCDCN().parameters())
    head = sum(p.numel() for p in OfficialCDCNWithDepthHead().parameters())
    assert baseline == 2245016 and head == 2246281 and head-baseline == 1265


def test_timed_block_excludes_warmup_and_disables_gradients(monkeypatch):
    events=[]
    class Event:
        def record(self): events.append("record")
        def synchronize(self): events.append("end_sync")
        def elapsed_time(self,other): return 2.0
    monkeypatch.setattr(torch.cuda,"Event",lambda **kw:Event())
    monkeypatch.setattr(torch.cuda,"synchronize",lambda:events.append("sync"))
    clock=iter([1.,1.003,2.,2.004,3.,3.005,4.,4.006])
    monkeypatch.setattr(cost.time,"perf_counter",lambda:next(clock))
    class Tiny(torch.nn.Module):
        calls=0
        def forward(self,x):
            assert not torch.is_grad_enabled()
            self.calls+=1
            return {"score":x.mean(dim=1)}
    model=Tiny().eval()
    rows=cost.timed_block(model,[torch.ones(1,2),torch.zeros(1,2)],2,4)
    assert model.calls == 6 and len(rows) == 4
    assert [r["input_index"] for r in rows] == [0,1,0,1]
    assert [r["cuda_event_forward_ms"] for r in rows] == [2.]*4
    assert [r["synchronized_host_forward_ms"] for r in rows] == pytest.approx([3,4,5,6])
    assert events.count("sync") == 5 and events.count("end_sync") == 4


def test_prepare_registration_can_be_read_back_and_reused(tmp_path,monkeypatch):
    root=tmp_path/"source"; (root/"configs").mkdir(parents=True)
    drive=tmp_path/"drive"; (drive/"reports").mkdir(parents=True)
    manifest=drive/"reports/casia_fasd_debug_with_depth.csv";manifest.write_text("fixture")
    plan={"input":{"manifest_sha256":cost.manifest_checksum(manifest)},"timing":{"order_seed":20261022}}
    (root/"configs/round6_cost.json").write_text(json.dumps(plan))
    monkeypatch.setattr(cost,"verify_source",lambda root:{"commit":"fixture"})
    monkeypatch.setattr(cost,"validation_inputs",lambda *a:([torch.ones(1,3,2,2)]*2,[{"sample_id":"fixture"}]))
    monkeypatch.setattr(cost,"load_models",lambda *a:({},{}))
    monkeypatch.setattr(cost,"environment",lambda:{"gpu":"CPU test fixture"})
    flags=(torch.backends.cudnn.benchmark,torch.backends.cudnn.deterministic,
           torch.backends.cuda.matmul.allow_tf32,torch.backends.cudnn.allow_tf32)
    try:
        first,_,_=cost.prepare(root,drive,tmp_path/"output")
        second,_,_=cost.prepare(root,drive,tmp_path/"output")
        assert first==second==cost.read(tmp_path/"output/registration.json")
    finally:
        torch.backends.cudnn.benchmark,torch.backends.cudnn.deterministic=flags[:2]
        torch.backends.cuda.matmul.allow_tf32,torch.backends.cudnn.allow_tf32=flags[2:]
