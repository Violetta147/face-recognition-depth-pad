import hashlib
import io
import json
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
BASE = Path(__file__).parent / 'drive-snapshot'


def read_csv(path):
    return pd.read_csv(path, keep_default_na=False, float_precision='round_trip')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


manifest_path = BASE / 'reports/casia_fasd_debug_with_depth.csv'
manifest = read_csv(manifest_path)
assert len(manifest) == 12000
assert not manifest.sample_id.duplicated().any()
assert manifest.groupby('video_id')['split'].nunique().max() == 1
assert manifest.groupby('subject_id')['split'].nunique().max() == 1
assert (manifest.groupby('video_id').size() == 20).all()
subjects = {split: sorted(frame.subject_id.unique()) for split, frame in manifest.groupby('split')}
split_counts = {
    split: {'subjects': frame.subject_id.nunique(), 'videos': frame.video_id.nunique(),
            'frames': len(frame), 'attack_videos': frame[frame.label == 0].video_id.nunique(),
            'live_videos': frame[frame.label == 1].video_id.nunique()}
    for split, frame in manifest.groupby('split')
}
source = manifest.copy()
source['depth_path'] = ''
reconstructed_source_sha = hashlib.sha256(source.to_csv(index=False, lineterminator='\n').encode()).hexdigest()
checks = []
states = {}
for folder in sorted((BASE / 'runs').iterdir()):
    cfg = yaml.safe_load((folder / 'config.yaml').read_text())
    item = {'run_id': folder.name, 'seed': cfg['seed'], 'model': cfg['model']['name'],
            'file_count': len(list(folder.iterdir())), 'manifest_sha256': load_json(folder / 'manifest_checksum.json')['sha256'],
            'splits': {}, 'checkpoint': None, 'status': 'incomplete'}
    log_path = folder / 'train_log.csv'
    if log_path.exists():
        log = read_csv(log_path)
        best = log.loc[log.val_loss.idxmin()]
        item['epochs_logged'] = len(log)
        item['best_epoch_from_log'] = int(best.epoch)
        item['best_stage_from_log'] = best.stage
        item['best_val_loss_from_log'] = float(best.val_loss)
    checkpoint = folder / 'best.ckpt'
    if checkpoint.exists():
        state = torch.load(checkpoint, map_location='cpu', weights_only=True)
        item['checkpoint'] = {'sha256': sha(checkpoint), 'bytes': checkpoint.stat().st_size,
                              'val_loss': state.get('val_loss'), 'state_tensors': len(state['model'])}
        assert abs(state['val_loss'] - item['best_val_loss_from_log']) < 1e-12, folder.name
        if folder.name in {
            'CASIA_E1_CDCN_OFFICIAL_seed42_20260921T114029Z',
            'CASIA_E2_CDCN_OFFICIAL_HEAD_FROZEN_seed42_20261001T155213Z'
        }:
            states[folder.name] = state
    for split, metric_name in [('val', 'metrics.json'), ('test', 'test_metrics.json')]:
        scores_path = folder / f'{split}_scores.csv'
        if not scores_path.exists():
            continue
        scores = read_csv(scores_path)
        threshold_record = load_json(folder / 'threshold.json')
        assert threshold_record['source'] == 'validation'
        threshold = threshold_record['threshold']
        assert not scores.video_id.duplicated().any()
        truth = manifest[manifest.split == split].groupby('video_id', as_index=False).label.first()
        joined = scores.merge(truth, on='video_id', suffixes=('', '_manifest'), validate='one_to_one')
        assert len(joined) == len(scores) == len(truth)
        assert (joined.label == joined.label_manifest).all()
        computed = evaluate_scores(scores.label.to_numpy(), scores.score.to_numpy(), threshold).to_dict()
        saved = load_json(folder / metric_name)
        differences = {key: abs(computed[key] - saved[key]) for key in computed}
        assert max(differences.values()) < 1e-12, (folder.name, split, differences)
        frame_scores = read_csv(folder / f'{split}_frame_scores.csv')
        assert not frame_scores.sample_id.duplicated().any()
        assert len(frame_scores) == len(manifest[manifest.split == split])
        frame_truth = manifest[manifest.split == split][['sample_id', 'video_id', 'label']]
        paired_frames = frame_scores.merge(frame_truth, on='sample_id', suffixes=('', '_manifest'), validate='one_to_one')
        assert len(paired_frames) == len(frame_scores)
        assert (paired_frames.label == paired_frames.label_manifest).all()
        assert (paired_frames.video_id == paired_frames.video_id_manifest).all()
        agg = aggregate_video_scores(frame_scores)
        paired = scores.merge(agg, on=['video_id', 'label'], suffixes=('_saved', '_aggregate'), validate='one_to_one')
        aggregate_error = float(np.abs(paired.score_saved - paired.score_aggregate).max())
        assert aggregate_error < 1e-12
        prediction = scores.score >= threshold
        false_accepts = int(((scores.label == 0) & prediction).sum())
        false_rejects = int(((scores.label == 1) & ~prediction).sum())
        item['splits'][split] = {'videos': len(scores), 'frames': len(frame_scores), 'metrics': saved,
            'max_metric_error': max(differences.values()), 'max_aggregation_error': aggregate_error,
            'false_accepts': false_accepts, 'false_rejects': false_rejects,
            'scores_sha256': sha(scores_path)}
        item['status'] = 'test_complete' if split == 'test' else 'validation_complete'
    if folder.name.startswith('CASIA_E0'):
        assert item['manifest_sha256'] == reconstructed_source_sha
    else:
        assert item['manifest_sha256'] == sha(manifest_path)
    checks.append(item)

e1_name = 'CASIA_E1_CDCN_OFFICIAL_seed42_20260921T114029Z'
e2_name = 'CASIA_E2_CDCN_OFFICIAL_HEAD_FROZEN_seed42_20261001T155213Z'
e1_state = states[e1_name]['model']
e2_state = states[e2_name]['model']
assert all(torch.equal(value, e2_state['backbone.' + key]) for key, value in e1_state.items())
e1_hash = sha(BASE / 'runs' / e1_name / 'best.ckpt')
assert load_json(BASE / 'runs' / e2_name / 'initial_checkpoint.json')['sha256'] == e1_hash
freeze = load_json(BASE / 'runs' / e2_name / 'comparison_freeze.json')
for field, name in [('config_sha256', 'config.yaml'), ('checkpoint_sha256', 'best.ckpt'),
                    ('threshold_sha256', 'threshold.json')]:
    assert freeze[field] == sha(BASE / 'runs' / e2_name / name), field
assert freeze['manifest_sha256'] == sha(manifest_path)
paired = read_csv(BASE / 'runs' / e1_name / 'test_scores.csv').merge(
    read_csv(BASE / 'runs' / e2_name / 'test_scores.csv'), on=['video_id', 'label'],
    suffixes=('_e1', '_e2'), validate='one_to_one')
t1 = load_json(BASE / 'runs' / e1_name / 'threshold.json')['threshold']
t2 = load_json(BASE / 'runs' / e2_name / 'threshold.json')['threshold']
ok1 = (paired.score_e1 >= t1) == paired.label
ok2 = (paired.score_e2 >= t2) == paired.label
pair_counts = {'both_correct': int((ok1 & ok2).sum()), 'fixed_by_e2': int((~ok1 & ok2).sum()),
               'new_error_e2': int((ok1 & ~ok2).sum()), 'both_wrong': int((~ok1 & ~ok2).sum())}
assert sum(pair_counts.values()) == 360
wrong = paired[~ok1 & ~ok2].to_dict(orient='records')
report = {'date': '2026-10-16', 'scope': 'saved artifacts; no retraining or new test scoring',
          'snapshot_manifest': 'artifacts/research-audit-20261016/snapshot-manifest.json',
          'derived_manifest_sha256': sha(manifest_path), 'reconstructed_source_manifest_sha256': reconstructed_source_sha,
          'split_counts': split_counts, 'subjects': subjects, 'runs': checks,
          'e1_e2_backbone_tensors_identical': len(e1_state), 'e2_initial_checkpoint_matches_e1': True,
          'e2_freeze_hashes_match': True, 'paired_errors': pair_counts, 'both_wrong_videos': wrong}
target = Path(__file__).parent / 'verified-results.json'
target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print('PASS: saved frame/video scores, truth, metrics, thresholds, manifests, checkpoint losses and E1/E2 backbone verified')
print(json.dumps({'split_counts': split_counts, 'paired_errors': pair_counts,
                  'derived_manifest_sha256': sha(manifest_path), 'source_manifest_sha256': reconstructed_source_sha}, indent=2))
for item in checks:
    print(item['run_id'], item['status'], 'epoch', item.get('best_epoch_from_log'), 'checkpoint_sha', (item['checkpoint'] or {}).get('sha256'))
print(target)
