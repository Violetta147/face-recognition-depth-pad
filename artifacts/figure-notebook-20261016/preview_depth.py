from pathlib import Path
import sys
import torch
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT / 'src'))
from deepface_pad.figure_data import load_evidence,choose_cases,read_json,restore_selected_inputs,DEPTH_MODELS
from deepface_pad.data import PadDataset
from deepface_pad.figure_inference import load_model,render_depth_cases
from deepface_pad.report_figures import FigureWriter

torch.set_num_threads(1)
OUT = Path(__file__).parent
e = load_evidence(ROOT,'G:/My Drive/face-pad/runs','G:/My Drive/face-pad/reports/casia_fasd_debug_with_depth.csv','G:/My Drive/face-pad/reports/round5-525c80889106/comparison_freeze.json')
cases = choose_cases(e).query("video_id == 'casia_s32_v2'")
snapshot = read_json(e['runs']['E1']['folder'] / 'depth_input_snapshot.json')
checks = {row['sample_id']:row['sha256'] for row in snapshot['depth_audit']['artifact_checksums']}
restore_selected_inputs(cases,OUT/'case-data','G:/My Drive/face-pad/casia-fasd.zip','G:/My Drive/face-pad/depth-checkpoints/casia-fasd-depth-checkpoint.tar',checks)
cases.to_csv(OUT/'case-manifest.csv',index=False)
dataset = PadDataset(OUT/'case-manifest.csv',OUT/'case-data','test',256,augment=False,require_depth=True,normalization='cdcn_official')
sample = dataset[0]
outputs = {}
for name in DEPTH_MODELS:
    model = load_model(e['runs'][name],torch.device('cpu'))
    with torch.inference_mode():
        result = model(sample['image'][None])
    outputs[name] = {sample['sample_id']:result['depth'][0,0].numpy()}
    score = float(torch.sigmoid(result['logit'])[0]) if 'logit' in result else float(result['score'][0])
    saved = e['runs'][name]['test_frame'].set_index('sample_id').loc[sample['sample_id'],'score']
    assert abs(score-saved) < 1e-3, (name,score,saved)
    print('CPU CASE VERIFIED',name,'score error',abs(score-saved),flush=True)
    del model
writer = FigureWriter(OUT/'qualitative-preview')
limits = render_depth_cases(e,writer,cases,{sample['sample_id']:sample},outputs)
writer.finish({'phase':'local one-case QA only; not full validation MAE or GPU timing',**limits})
print('CASE PREVIEW COMPLETE',flush=True)
