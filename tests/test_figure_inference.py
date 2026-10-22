import numpy as np
import pytest
import torch

from deepface_pad.figure_inference import un_normalize_rgb


@pytest.mark.parametrize("normalization",["imagenet","cdcn_official"])
def test_rgb_panel_matches_the_actual_normalized_input_without_per_image_stretch(normalization):
    original = torch.tensor([.1,.4,.8])[:,None,None].expand(3,2,2)
    if normalization == "cdcn_official":
        tensor = (original-.5)/(128/255)
    else:
        tensor = (original-torch.tensor([.485,.456,.406])[:,None,None])/torch.tensor([.229,.224,.225])[:,None,None]
    before = tensor.clone()
    result = un_normalize_rgb(tensor,normalization)
    np.testing.assert_allclose(result,original.numpy().transpose(1,2,0),atol=1e-7)
    assert torch.equal(tensor,before)


def test_case_panels_preserve_values_above_one_and_share_color_scales(tmp_path):
    import matplotlib.pyplot as plt
    import pandas as pd
    from deepface_pad.figure_data import DEPTH_MODELS
    from deepface_pad.figure_inference import render_depth_cases
    (tmp_path / "data").mkdir()
    captured = []
    class Writer:
        root = tmp_path
        def save(self,fig,*args):
            captured.extend((ax.get_title(),image.norm.vmin,image.norm.vmax) for ax in fig.axes for image in ax.images)
            plt.close(fig)
    cases = pd.DataFrame([{"sample_id":"s","video_id":"v","label":0,"frame_index":10,"quality":"low","role":"synthetic_test"}])
    samples = {"s":{"image":torch.zeros(3,4,4),"depth":torch.zeros(1,32,32)}}
    outputs = {name:{"s":np.full((32,32),2. if name == "E3" else .1,dtype=np.float32)} for name in DEPTH_MODELS}
    evidence = {"runs":{name:{"threshold":.5,"test_video":pd.DataFrame([{"video_id":"v","score":.2,"prediction":0}])} for name in DEPTH_MODELS}}
    limits = render_depth_cases(evidence,Writer(),cases,samples,outputs)
    assert limits["depth_color_limits"] == [0,2.]
    assert limits["absolute_error_color_limits"] == [0,2.]
    assert np.load(tmp_path / "data/qualitative_depth_arrays.npz")["s_E3_prediction"].max() == 2.
    maps = [(low,high) for title,low,high in captured if title not in {"Target mask","RGB model input"}]
    assert all((low,high) == (0,2.) for low,high in maps)


def test_benchmark_records_randomized_rounds_native_sizes_and_raw_samples(tmp_path,monkeypatch):
    import matplotlib.pyplot as plt
    import pandas as pd
    import deepface_pad.figure_inference as module
    from deepface_pad.figure_data import MODELS
    class Tiny(torch.nn.Module):
        def __init__(self):
            super().__init__(); self.weight = torch.nn.Parameter(torch.ones(1))
        def forward(self,value):
            return value.mean()*self.weight
    monkeypatch.setattr(module,"load_model",lambda run,device:Tiny())
    original_randn = torch.randn
    monkeypatch.setattr(torch,"randn",lambda *shape,**kwargs:original_randn(*shape))
    monkeypatch.setattr(torch.cuda,"synchronize",lambda:None)
    monkeypatch.setattr(torch.cuda,"empty_cache",lambda:None)
    monkeypatch.setattr(torch.cuda,"get_device_name",lambda device:"synthetic-unit-test")
    (tmp_path / "data").mkdir()
    class Writer:
        root = tmp_path
        def save(self,fig,*args): plt.close(fig)
    runs = {}
    for name in MODELS:
        folder = tmp_path / name; folder.mkdir(); (folder / "best.ckpt").write_bytes(b"synthetic test")
        runs[name] = {"folder":folder,"config":{"data":{"image_size":224 if name == "E0" else 256}}}
    metadata = module.benchmark_figures({"runs":runs},Writer(),torch.device("cuda"),rounds=2,warmup=1,repeats=3)
    raw = pd.read_csv(tmp_path / "data/latency_raw.csv")
    assert len(raw) == 2*2*6*3
    assert all(group.model.nunique() == 6 for _,group in raw.groupby(["profile","round"]))
    assert set(raw.query("profile == 'native' and model == 'E0'").input_side) == {224}
    assert set(raw.query("profile == 'common256'").input_side) == {256}
    assert metadata["latency_device"] == "synthetic-unit-test"
