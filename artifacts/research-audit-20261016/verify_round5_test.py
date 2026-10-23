"""Verify frozen test scores and paired errors; never tune or rerun inference."""
import hashlib
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from deepface_pad.metrics import aggregate_video_scores, evaluate_scores

DRIVE = Path('G:/My Drive/face-pad')
OUT = ROOT / 'artifacts/round5-test-audit-20261016'
OUT.mkdir(parents=True, exist_ok=True)
BASE = ROOT / 'artifacts/research-audit-20261016/drive-snapshot'
COMMIT = '525c80889106c06525f5b758e8725c8ac9cee856'
REPORTS = DRIVE / f'reports/round5-{COMMIT[:12]}'
RUNS = {
    'E0':'CASIA_E0_BCE_5E_seed42_20260920T082941Z',
    'E1':'CASIA_E1_CDCN_OFFICIAL_seed42_20260921T114029Z',
    'E2':'CASIA_E2_CDCN_OFFICIAL_HEAD_FROZEN_seed42_20261001T155213Z',
    'E3':'CASIA_E3_CDCN_OFFICIAL_JOINT_BCE_seed42_20261015T203645Z',
    'E3b':'CASIA_E3B_CDCN_OFFICIAL_STAGED_BCE_seed42_20261015T204943Z',
    'E4':'CASIA_E4_CDCN_OFFICIAL_STAGED_FOCAL_seed42_20261015T210039Z',
}

def js(path):
    return json.loads(path.read_text(encoding='utf-8'))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def csv(path):
    return pd.read_csv(path, float_precision='round_trip')

freeze = js(REPORTS / 'comparison_freeze.json')
assert freeze == js(ROOT / 'artifacts/round5-full-audit-20261016/comparison_freeze.json')
assert freeze['selected_variant'] == 'E3' and freeze['selection_source'] == 'validation'
manifest = csv(BASE / 'reports/casia_fasd_debug_with_depth.csv')
test = manifest[manifest.split == 'test']
expected = test[['sample_id','video_id','label']].sort_values('sample_id').reset_index(drop=True)
metadata = test[['video_id','label','attack_type','quality']].drop_duplicates()
assert len(metadata) == 360 and not metadata.video_id.duplicated().any()
results, frames = {}, {}
for variant, run_id in RUNS.items():
    source = DRIVE / 'runs' / run_id
    folder = OUT / run_id
    folder.mkdir(exist_ok=True)
    for name in ('test_frame_scores.csv','test_scores.csv','test_metrics.json','threshold.json'):
        shutil.copy2(source / name, folder / name)
    if variant in freeze['runs']:
        assert freeze['runs'][variant]['run'] == run_id
        for name, digest in freeze['runs'][variant]['hashes'].items():
            assert sha(source / name) == digest, (variant, name)
    else:
        for name in ('test_frame_scores.csv','test_scores.csv','test_metrics.json','threshold.json'):
            assert sha(folder / name) == sha(BASE / 'runs' / run_id / name), ('Historical artifact changed',variant,name)
    frame, video = csv(folder / 'test_frame_scores.csv'), csv(folder / 'test_scores.csv')
    pd.testing.assert_frame_equal(frame[['sample_id','video_id','label']].sort_values('sample_id').reset_index(drop=True), expected)
    assert np.isfinite(frame.score).all()
    assert (frame.groupby('video_id').size() == 20).all()
    pd.testing.assert_frame_equal(aggregate_video_scores(frame), video.sort_values('video_id').reset_index(drop=True), atol=1e-12,rtol=0)
    threshold = js(folder / 'threshold.json')
    assert threshold['source'] == 'validation'
    computed = evaluate_scores(video.label.to_numpy(),video.score.to_numpy(),threshold=threshold['threshold']).to_dict()
    saved = js(folder / 'test_metrics.json')
    assert all(abs(computed[key]-saved[key]) < 1e-12 for key in computed)
    video = video.merge(metadata,on=['video_id','label'],validate='one_to_one')
    video['prediction'] = (video.score >= threshold['threshold']).astype(int)
    video['correct'] = video.prediction == video.label
    false_accept = int(((video.label == 0) & ~video.correct).sum())
    false_reject = int(((video.label == 1) & ~video.correct).sum())
    groups = []
    for (label,attack,quality), group in video.groupby(['label','attack_type','quality']):
        groups.append({'label':int(label),'attack_type':attack,'quality':quality,'videos':len(group),
                       'errors':int((~group.correct).sum()),'error_rate':float((~group.correct).mean())})
    results[variant] = {'run_id':run_id,'metrics':computed,'attack_videos':270,'live_videos':90,
        'false_accepts':false_accept,'false_rejects':false_reject,
        'error_video_ids':video.loc[~video.correct,'video_id'].tolist(),'groups':groups,
        'test_artifact_hashes':{name:sha(folder / name) for name in ('test_frame_scores.csv','test_scores.csv','test_metrics.json')}}
    frames[variant] = video
    print('VERIFIED',variant,computed['acer'],false_accept,false_reject,flush=True)
paired = {}
for first,second in [('E1','E2'),('E1','E3'),('E1','E3b'),('E1','E4'),('E3','E3b'),('E3b','E4')]:
    pair = frames[first][['video_id','label','score','correct']].merge(
        frames[second][['video_id','label','score','correct']],on=['video_id','label'],validate='one_to_one',suffixes=('_first','_second'))
    pair['change'] = np.select([~pair.correct_first & pair.correct_second,
                               pair.correct_first & ~pair.correct_second,
                               ~pair.correct_first & ~pair.correct_second],
                               ['fixed','new_error','both_wrong'],default='both_correct')
    assert len(pair) == 360
    pair.to_csv(OUT / f'{first}-vs-{second}-paired.csv',index=False)
    paired[f'{first}_vs_{second}'] = {'counts':{str(key):int(value) for key,value in pair.change.value_counts().items()},
        'fixed_ids':pair.loc[pair.change == 'fixed','video_id'].tolist(),
        'new_error_ids':pair.loc[pair.change == 'new_error','video_id'].tolist(),
        'both_wrong_ids':pair.loc[pair.change == 'both_wrong','video_id'].tolist()}
saved_table = csv(REPORTS / 'development-test.csv')
for row in saved_table.itertuples():
    assert row.run == results[row.variant]['run_id']
    assert all(abs(getattr(row,key)-value) < 1e-12 for key,value in results[row.variant]['metrics'].items())
payload = {'status':'PASS: frozen development-test audit', 'selected_by_validation':'E3',
           'source_commit':COMMIT,'runs':results,'paired':paired}
(OUT / 'verification.json').write_text(json.dumps(payload,indent=2)+'\n')
print(json.dumps({'status':payload['status'],'paired':paired},indent=2),flush=True)
