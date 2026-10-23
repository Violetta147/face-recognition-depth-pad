"""Read-only verification of the three user-started CASIA smoke runs."""
import hashlib
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from deepface_pad.metrics import aggregate_video_scores, evaluate_scores

torch.set_num_threads(1)
DRIVE = Path('G:/My Drive/face-pad')
OUT = ROOT / 'artifacts/round5-smoke-audit-20261016'
OUT.mkdir(parents=True, exist_ok=True)
RUNS = {
    'E3': 'CASIA_E3_CDCN_OFFICIAL_JOINT_BCE_SMOKE_seed42_20261015T201251Z',
    'E3b': 'CASIA_E3B_CDCN_OFFICIAL_STAGED_BCE_SMOKE_seed42_20261015T201352Z',
    'E4': 'CASIA_E4_CDCN_OFFICIAL_STAGED_FOCAL_SMOKE_seed42_20261015T201557Z',
}
EXPECTED_COMMIT = '525c80889106c06525f5b758e8725c8ac9cee856'
EXPECTED_INIT = '679810c001e526cafed8685fe731a7d5c539fd3fb9c5a9fb31725b7dbdf57024'
EXPECTED_MANIFEST = '4c302c9039e48a8ea6baedf426b26e1b0a6663bc295c661bb71fefccdb9b37fd'
REPORTS = DRIVE / f'reports/round5-{EXPECTED_COMMIT[:12]}'

def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read_csv(path):
    return pd.read_csv(path, float_precision='round_trip')

manifest = read_csv(ROOT / 'artifacts/research-audit-20261016/drive-snapshot/reports/casia_fasd_debug_with_depth.csv')
expected_rows = manifest.loc[manifest.split == 'val', ['sample_id', 'video_id', 'label']].sort_values('sample_id').reset_index(drop=True)
e1_depth = read_json(ROOT / 'artifacts/research-audit-20261016/drive-snapshot/runs/CASIA_E1_CDCN_OFFICIAL_seed42_20260921T114029Z/depth_input_snapshot.json')
results = {}
for key, name in RUNS.items():
    folder = OUT / name
    folder.mkdir(exist_ok=True)
    for source in (DRIVE / 'runs' / name).iterdir():
        if source.is_file():
            shutil.copy2(source, folder / source.name)
    cfg = yaml.safe_load((folder / 'config.yaml').read_text())
    assert cfg['source_commit'] == EXPECTED_COMMIT
    registration = read_json(REPORTS / f'{key}-smoke-registration.json')
    assert registration['config'] == cfg and registration['config_sha256'] == sha(folder / 'config.yaml')
    assert read_json(folder / 'initial_checkpoint.json')['sha256'] == EXPECTED_INIT
    assert read_json(folder / 'manifest_checksum.json')['sha256'] == EXPECTED_MANIFEST
    snapshot = read_json(folder / 'depth_input_snapshot.json')
    assert snapshot['depth_audit']['artifact_checksums'] == e1_depth['depth_audit']['artifact_checksums']
    assert not list(folder.glob('test*'))
    log = read_csv(folder / 'train_log.csv')
    expected_stages = ['joint'] if key == 'E3' else ['depth', 'head', 'joint']
    assert log.stage.tolist() == expected_stages and log.epoch.tolist() == [1] * len(expected_stages)
    assert np.isfinite(log[['train_loss', 'val_loss', 'val_selection_loss']]).all().all()
    selected = read_json(folder / 'checkpoint_selection.json')
    assert selected['reported_stage'] == 'joint'
    final = torch.load(folder / 'best.ckpt', map_location='cpu', weights_only=True)
    assert final['stage'] == 'joint' and final['selection_metric'] == 'classification_bce'
    assert final['global_epoch'] == len(log)
    assert abs(final['selection_value'] - log.iloc[-1].val_selection_loss) < 1e-12
    assert sha(folder / 'best.ckpt') == sha(folder / f'best_stage_{len(log):02d}_joint.ckpt')
    for stage in selected['stages']:
        checkpoint = torch.load(folder / f"best_stage_{stage['stage_index']:02d}_{stage['stage']}.ckpt", map_location='cpu', weights_only=True)
        assert all(torch.isfinite(value).all() for value in checkpoint['model'].values())
        assert checkpoint['stage'] == stage['stage'] and checkpoint['epoch'] == stage['epoch']
    frozen = None
    if key != 'E3':
        depth = torch.load(folder / 'best_stage_01_depth.ckpt', map_location='cpu', weights_only=True)['model']
        head = torch.load(folder / 'best_stage_02_head.ckpt', map_location='cpu', weights_only=True)['model']
        backbone_keys = [k for k in depth if k.startswith('backbone.')]
        assert len(backbone_keys) == 73
        assert all(torch.equal(depth[k], head[k]) for k in backbone_keys)
        assert any(not torch.equal(depth[k], head[k]) for k in depth if k.startswith('head.'))
        assert any(not torch.equal(head[k], final['model'][k]) for k in backbone_keys)
        frozen = {'head_stage_backbone_tensors_unchanged':73, 'head_changed':True, 'joint_backbone_changed':True}
    frame = read_csv(folder / 'val_frame_scores.csv')
    pd.testing.assert_frame_equal(frame[['sample_id', 'video_id', 'label']].sort_values('sample_id').reset_index(drop=True), expected_rows)
    video = read_csv(folder / 'val_scores.csv')
    aggregated = aggregate_video_scores(frame).sort_values('video_id').reset_index(drop=True)
    pd.testing.assert_frame_equal(aggregated, video.sort_values('video_id').reset_index(drop=True), atol=1e-12, rtol=0)
    threshold = read_json(folder / 'threshold.json')
    assert threshold['source'] == 'validation'
    metrics = evaluate_scores(video.label.to_numpy(), video.score.to_numpy(), threshold=threshold['threshold']).to_dict()
    stored = read_json(folder / 'metrics.json')
    assert all(abs(metrics[k] - stored[k]) < 1e-12 for k in metrics)
    scores = frame.score.to_numpy()
    assert np.isfinite(scores).all() and ((scores > 0) & (scores < 1)).all()
    labels = frame.label.to_numpy()
    bce = float(np.mean(-(labels * np.log(scores) + (1-labels) * np.log1p(-scores))))
    assert abs(bce - final['selection_value']) < 1e-6
    frame_errors = int(((scores >= threshold['threshold']).astype(int) != labels).sum())
    results[key] = {'run_id':name, 'source_commit':cfg['source_commit'], 'config_sha256':sha(folder / 'config.yaml'),
                    'checkpoint_sha256':sha(folder / 'best.ckpt'), 'stages':log.to_dict(orient='records'),
                    'validation':metrics, 'validation_frames':len(frame), 'validation_videos':len(video),
                    'validation_frame_errors':frame_errors, 'classification_bce_from_scores':bce,
                    'frozen_stage_check':frozen, 'test_artifacts_present':False}
payload = {'status':'PASS: technical smoke gate; not evidence of improvement', 'runs':results}
(OUT / 'verification.json').write_text(json.dumps(payload, indent=2) + '\n')
print(json.dumps(payload, indent=2))
