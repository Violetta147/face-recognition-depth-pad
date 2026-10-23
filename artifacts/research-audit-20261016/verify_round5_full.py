"""Audit saved validation artifacts only; never train or score test."""
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
from deepface_pad.depth_evaluation import summarize_depth_errors

torch.set_num_threads(1)
DRIVE = Path('G:/My Drive/face-pad')
OUT = ROOT / 'artifacts/round5-full-audit-20261016'
OUT.mkdir(parents=True, exist_ok=True)
COMMIT = '525c80889106c06525f5b758e8725c8ac9cee856'
REPORTS = DRIVE / f'reports/round5-{COMMIT[:12]}'
BASE = ROOT / 'artifacts/research-audit-20261016/drive-snapshot'
RUNS = {
    'E3': 'CASIA_E3_CDCN_OFFICIAL_JOINT_BCE_seed42_20261015T203645Z',
    'E3b': 'CASIA_E3B_CDCN_OFFICIAL_STAGED_BCE_seed42_20261015T204943Z',
    'E4': 'CASIA_E4_CDCN_OFFICIAL_STAGED_FOCAL_seed42_20261015T210039Z',
}

def js(path):
    return json.loads(path.read_text(encoding='utf-8'))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def csv(path):
    return pd.read_csv(path, float_precision='round_trip')

def close_dict(first, second):
    assert first.keys() == second.keys()
    for key, value in first.items():
        other = second[key]
        if isinstance(value, dict):
            close_dict(value, other)
        elif isinstance(value, float):
            assert abs(value - other) < 1e-12, (key, value, other)
        else:
            assert value == other, (key, value, other)

manifest = csv(BASE / 'reports/casia_fasd_debug_with_depth.csv')
expected_rows = manifest.loc[manifest.split == 'val', ['sample_id', 'video_id', 'label']].sort_values('sample_id').reset_index(drop=True)
e1_snapshot = js(BASE / 'runs/CASIA_E1_CDCN_OFFICIAL_seed42_20260921T114029Z/depth_input_snapshot.json')
results = {}
for variant, name in RUNS.items():
    source = DRIVE / 'runs' / name
    assert not list(source.glob('test*')), 'Test already exists; inspect before freezing'
    folder = OUT / name
    folder.mkdir(exist_ok=True)
    for path in source.iterdir():
        if path.is_file():
            shutil.copy2(path, folder / path.name)
    cfg = yaml.safe_load((folder / 'config.yaml').read_text())
    registration = js(REPORTS / f'{variant}-full-registration.json')
    assert cfg == registration['config'] and sha(folder / 'config.yaml') == registration['config_sha256']
    assert cfg['source_commit'] == COMMIT
    assert js(folder / 'initial_checkpoint.json')['sha256'] == '679810c001e526cafed8685fe731a7d5c539fd3fb9c5a9fb31725b7dbdf57024'
    assert js(folder / 'manifest_checksum.json')['sha256'] == '4c302c9039e48a8ea6baedf426b26e1b0a6663bc295c661bb71fefccdb9b37fd'
    assert js(folder / 'depth_input_snapshot.json')['depth_audit']['artifact_checksums'] == e1_snapshot['depth_audit']['artifact_checksums']
    log = csv(folder / 'train_log.csv')
    stages = cfg['training']['stages']
    assert sum(s['epochs'] for s in stages) == len(log) == 16
    assert log.stage.tolist() == [s['name'] for s in stages for _ in range(s['epochs'])]
    assert log.epoch.tolist() == [i for s in stages for i in range(1, s['epochs']+1)]
    assert np.isfinite(log[['train_loss', 'val_loss', 'val_selection_loss']]).all().all()
    selection = js(folder / 'checkpoint_selection.json')
    assert selection['reported_stage'] == 'joint'
    for record in selection['stages']:
        checkpoint = torch.load(folder / f"best_stage_{record['stage_index']:02d}_{record['stage']}.ckpt", map_location='cpu', weights_only=True)
        candidate = log[log.stage == record['stage']]
        best_index = candidate.val_selection_loss.idxmin()
        best = log.loc[best_index]
        assert checkpoint['epoch'] == record['epoch'] == best.epoch
        assert checkpoint['global_epoch'] == record['global_epoch'] == best_index + 1
        assert abs(checkpoint['selection_value'] - best.val_selection_loss) < 1e-12
        assert abs(checkpoint['val_loss'] - best.val_loss) < 1e-12
        assert all(torch.isfinite(value).all() for value in checkpoint['model'].values())
    final = torch.load(folder / 'best.ckpt', map_location='cpu', weights_only=True)
    assert final['stage'] == 'joint' and final['selection_metric'] == 'classification_bce'
    assert sha(folder / 'best.ckpt') == sha(folder / f'best_stage_{len(stages):02d}_joint.ckpt')
    if variant != 'E3':
        depth = torch.load(folder / 'best_stage_01_depth.ckpt', map_location='cpu', weights_only=True)['model']
        head = torch.load(folder / 'best_stage_02_head.ckpt', map_location='cpu', weights_only=True)['model']
        backbone = [key for key in depth if key.startswith('backbone.')]
        assert len(backbone) == 73 and all(torch.equal(depth[key], head[key]) for key in backbone)
        assert any(not torch.equal(depth[key], head[key]) for key in depth if key.startswith('head.'))
        assert any(not torch.equal(head[key], final['model'][key]) for key in backbone)
    frame = csv(folder / 'val_frame_scores.csv')
    pd.testing.assert_frame_equal(frame[['sample_id', 'video_id', 'label']].sort_values('sample_id').reset_index(drop=True), expected_rows)
    video = csv(folder / 'val_scores.csv')
    pd.testing.assert_frame_equal(aggregate_video_scores(frame), video.sort_values('video_id').reset_index(drop=True), atol=1e-12, rtol=0)
    threshold = js(folder / 'threshold.json')
    assert threshold['source'] == 'validation'
    measured = evaluate_scores(video.label.to_numpy(), video.score.to_numpy()).to_dict()
    close_dict(measured, js(folder / 'metrics.json'))
    assert abs(measured['threshold'] - threshold['threshold']) < 1e-12
    scores, labels = frame.score.to_numpy(), frame.label.to_numpy()
    assert ((scores > 0) & (scores < 1)).all()
    bce = float(np.mean(-(labels*np.log(scores)+(1-labels)*np.log1p(-scores))))
    assert abs(bce - final['selection_value']) < 1e-6
    depth_rows = csv(folder / 'depth_val_errors.csv')
    pd.testing.assert_frame_equal(depth_rows[['sample_id', 'video_id', 'label']].sort_values('sample_id').reset_index(drop=True), expected_rows)
    assert np.isfinite(depth_rows[['mae_full', 'masked_error_sum', 'masked_pixels']]).all().all()
    depth_report = js(folder / 'depth_val_metrics.json')
    depth_recomputed = summarize_depth_errors(depth_rows)
    close_dict(depth_recomputed, {key:depth_report[key] for key in depth_recomputed})
    assert depth_report['split'] == 'val' and depth_report['checkpoint_sha256'] == sha(folder / 'best.ckpt')
    assert depth_report['manifest_sha256'] == js(folder / 'manifest_checksum.json')['sha256']
    results[variant] = {'run_id':name, 'epochs_trained':len(log), 'checkpoint':{
        key:final[key] for key in ('stage', 'epoch', 'global_epoch', 'val_loss', 'selection_metric', 'selection_value')},
        'validation':measured, 'classification_bce_recomputed':bce, 'depth_validation':depth_report,
        'stages_selected':selection['stages'], 'test_artifacts_present':False,
        'hashes':{key:sha(folder / key) for key in ('config.yaml', 'best.ckpt', 'threshold.json', 'metrics.json', 'manifest_checksum.json')}}
    print('VERIFIED', variant, name, flush=True)
ordered = sorted(results, key=lambda key:(results[key]['validation']['acer'], results[key]['validation']['eer'],
                 -results[key]['validation']['auc'], results[key]['checkpoint']['selection_value'], list(RUNS).index(key)))
assert ordered[0] == 'E3'
saved_table = csv(REPORTS / 'validation.csv')
assert saved_table.variant.tolist() == list(RUNS)
for row in saved_table.itertuples():
    record = results[row.variant]
    assert row.run == record['run_id'] and row.selected_epoch == record['checkpoint']['epoch']
    assert abs(row.val_selection_bce - record['checkpoint']['selection_value']) < 1e-12
    for key, value in record['validation'].items():
        assert abs(getattr(row, key) - value) < 1e-12
payload = {'status':'PASS: full validation audit', 'source_commit':COMMIT,
           'selected_variant':ordered[0], 'selection_source':'validation', 'runs':results}
(OUT / 'verification.json').write_text(json.dumps(payload, indent=2)+'\n')
print('PASS, selected:', ordered[0], flush=True)
