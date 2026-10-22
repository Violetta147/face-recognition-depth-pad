"""Build a new research-only snapshot. Never move or delete source files."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def restore_source_manifest(derived, destination, expected):
    """Recover only if serialization has the exact previously registered identity."""
    import pandas as pd
    frame=pd.read_csv(derived,keep_default_na=False)
    if 'depth_path' not in frame: raise ValueError('missing depth_path')
    data=frame.assign(depth_path='').to_csv(index=False,lineterminator='\n').encode('utf-8')
    if hashlib.sha256(data).hexdigest()!=expected:
        raise ValueError('source manifest cannot be restored byte-identically')
    destination=Path(destination)
    if destination.exists(): raise FileExistsError(destination)
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_bytes(data)


def excluded(path):
    parts = Path(path).parts
    if any(p in {'.codex', '.githooks', 'project_hooks', 'project_inventory', '__pycache__', '.venv'} for p in parts):
        return 'Local agent automation or installed runtime'
    if path in {'tests/test_project_hooks.py','tests/test_project_inventory.py','KE_HOACH_HOOKS_VA_BAN_GIAO.md'}:
        return 'Local agent automation only'
    if path.startswith(('reports/marp_slides_tutorial/', 'reports/archive/briefings/', 'notes/Hỏi đáp')):
        return 'Tutorial, early briefing or conversation; not experimental evidence'
    if path.startswith('docs/') and not path.startswith('docs/team_handoff/') and path not in {'docs/ROUND6_COST_COLAB_GUIDE.md'}:
        return 'Superseded local operating context; replaced by team handbook'
    if path in {'README.md','AGENTS.md','.gitignore','COLAB.md'}:
        return 'Replaced by portable team entry point'
    return None


class Export:
    def __init__(self, output):
        self.output = Path(output).resolve()
        self.output.mkdir(parents=True, exist_ok=False)
        self.files = {}

    def copy(self, source, relative, role, expected=None):
        source = Path(source)
        dest = (self.output / relative).resolve()
        if not dest.is_relative_to(self.output) or source.is_symlink():
            raise ValueError('unsafe export member')
        if not source.is_file():
            raise FileNotFoundError(source)
        digest = sha(source)
        if expected is not None and digest != expected:
            raise ValueError(f'changed source: {source}')
        if dest.exists():
            if sha(dest) != digest:
                raise ValueError(f'conflicting export member: {relative}')
            return
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dest)
        if sha(dest) != digest:
            raise ValueError('copy integrity failure')
        self.files[relative] = {'sha256':digest, 'bytes':dest.stat().st_size, 'role':role,
                                'source':str(source)}

    def finish(self, source_commit, exclusions):
        manifest = {'schema_version':1, 'source_commit':source_commit,
                    'source_state':'Selected working-tree snapshot. Per-file hashes identify delivered bytes; source_commit alone does not identify newly authored files.',
                    'scope':'Research snapshot; original repository and excluded files preserved.',
                    'files':self.files, 'excluded_tracked_files':exclusions}
        folder = self.output/'delivery'; folder.mkdir(exist_ok=True)
        (folder/'FILES.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        return manifest


def build(root, drive, output):
    root, drive = Path(root).resolve(), Path(drive).resolve()
    output = Path(output).resolve()
    if output == root or root.is_relative_to(output):
        raise ValueError('output must be a new independent subfolder or external folder')
    ex = Export(output)
    names = subprocess.check_output(['git','ls-files','-z'],cwd=root).decode().split('\0')
    # Include the new, tested authoring files even before their local commit.
    names = sorted(set(n for n in names if n) | {
        'scripts/build_team_handoff.py','scripts/verify_team_handoff.py','tests/test_team_handoff.py'} |
        {p.relative_to(root).as_posix() for p in (root/'docs/team_handoff').rglob('*') if p.is_file()})
    removed = []
    for name in names:
        why = excluded(name)
        if why:
            removed.append({'path':name,'reason':why})
        else:
            ex.copy(root/name,name,'Research source, test, config, manuscript or recorded evidence')
    for source,target in [('README_TEAM.md','README.md'),('AGENTS_TEAM.md','AGENTS.md'),
                           ('GITIGNORE_TEAM.txt','.gitignore'),('COLAB_TEAM.md','COLAB.md'),
                           ('CURRENT_TEAM.md','docs/handoffs/CURRENT.md')]:
        ex.copy(root/'docs/team_handoff'/source,target,'Portable team entry point')
    # Exact figure/template dependencies used by the retained manuscript tests.
    for rel in ('reports/slides_round5/assets','reports/bao_cao_cuoi_ky/hinh_anh'):
        for p in (root/rel).rglob('*'):
            if p.is_file(): ex.copy(p,p.relative_to(root).as_posix(),'Manuscript or slide input asset')
    provenance = json.loads((root/'reports/slides_round5/assets/provenance.json').read_text())
    for row in provenance['figures']:
        ex.copy(root/row['source'],row['source'],'Original plotted figure supporting slides',row['sha256'])
    template = 'artifacts/workspace-audit-20261016/Template_UD_JST_original.docx'
    ex.copy(root/template,template,'Original paper template required by builder')
    # Frozen score recovery is small and makes CPU analysis possible after cloning.
    for folder in ('round6-test-audit-20261022','round6-cost-audit-20261022'):
        for p in (root/'artifacts'/folder).rglob('*'):
            if p.is_file(): ex.copy(p,p.relative_to(root).as_posix(),'Frozen score/timing recovery')
    for rel in ('artifacts/round6-cost-colab-20261022/DeepFace-PAD-Round6-cost-source.zip',
                'artifacts/round6-colab-20261022/DeepFace-PAD-Round6-source.zip',
                'artifacts/round7/figures-attempt03/qualitative_arrays.npz',
                'artifacts/round7/numeric-diagnostic.json',
                'artifacts/round7/figures-attempt02/failure.json'):
        ex.copy(root/rel,rel,'Historical source identity or numeric/failure evidence')
    # Publish numerical webcam evidence, never camera pixels or installed packages.
    for name in ('webcam-live-01','webcam-live-02','webcam-live-03','webcam-replay-01',
                 'webcam-replay-02','webcam-live-reset-01','camera-probe-01'):
        for fn in ('summary.json','frames.csv'):
            p = root/'artifacts/round7'/name/fn
            if p.is_file(): ex.copy(p,p.relative_to(root).as_posix(),'Webcam numerical log; video shared separately')
    ex.copy(root/'artifacts/round7/detector/face_detection_yunet_2023mar.onnx',
            'artifacts/round7/detector/face_detection_yunet_2023mar.onnx','Pinned public face detector',
            '8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4')
    r6 = json.loads((root/'reports/ROUND_6_RESULTS_2026-10-22.json').read_text())
    r5 = json.loads((root/'reports/ROUND_5_TEST_RESULTS_2026-10-16.json').read_text())
    for audit in (r5,r6):
        for record in audit['runs'].values():
            folder = drive/'runs'/record['run_id']
            for p in folder.iterdir():
                if p.is_file() and p.suffix in {'.json','.yaml','.csv','.txt','.ckpt'}:
                    expected = record.get('hashes',{}).get(p.name)
                    if not expected: expected = record.get('test_artifact_hashes',{}).get(p.name)
                    ex.copy(p,f'evidence/face-pad/runs/{folder.name}/{p.name}',
                            'Registered non-smoke run: model, selection and saved scores',expected)
    for folder in ('round6-a00614999668','round5-525c80889106'):
        for p in (drive/'reports'/folder).iterdir():
            if p.is_file() and p.suffix in {'.json','.yaml','.csv','.txt'}:
                ex.copy(p,f'evidence/face-pad/reports/{folder}/{p.name}','Original registration, freeze or test receipt')
    for fn in ('casia_fasd_debug_with_depth.csv','casia_fasd_debug_with_depth.csv.provenance.json',
               'depth_status.csv','depth_status.csv.worker.json'):
        p=drive/'reports'/fn
        ex.copy(p,f'evidence/face-pad/reports/{fn}','Original manifest/depth provenance')
    ex.copy(root/'artifacts/round6-test-audit-20261022/casia_fasd_debug_with_depth.csv',
            'data/manifests/casia_fasd_debug_with_depth.csv','Frozen 12000-row manifest',r6['manifest_sha256'])
    restored=ex.output/'data/manifests/casia_fasd_debug.csv'
    original_sha='58fffcc2fb29649af1b8424d78b85067eefbd0321fde6b27fbd0803ef0fd7192'
    restore_source_manifest(ex.output/'data/manifests/casia_fasd_debug_with_depth.csv',restored,original_sha)
    ex.files['data/manifests/casia_fasd_debug.csv']={'sha256':sha(restored),'bytes':restored.stat().st_size,
        'role':'Source manifest recovered with blank depth paths; exact historical SHA verified',
        'source':'Deterministic recovery from frozen derived CSV; not a new sampling or split'}
    ex.copy(restored,'evidence/face-pad/reports/casia_fasd_debug.csv','Byte-identical source for provenance verifier',original_sha)
    # A read-only source archive preserves old commit identity without old automation history.
    for sub in ('round5-20261016','figures-e0-e4-20261016'):
        for p in (drive/'handoffs'/sub).glob('*source.zip'):
            ex.copy(p,f'evidence/source_archives/{p.name}','Historical experiment source, do not execute open gates')
    external = []
    for relative, expected in (
        ('casia-fasd.zip','84096c9734cf6120d36ed8f45d82864259420b2af0bd5ce4c7230fd9a572cd1b'),
        ('depth-checkpoints/casia-fasd-depth-checkpoint.tar','26cfa7f26d61e3a71372404008f5dc9dd696af931172850986a8642e440b3d80')):
        source=drive/relative
        if sha(source)!=expected: raise ValueError(f'changed external asset: {source}')
        external.append({'name':relative,'source':str(source),'restore_to':'evidence/face-pad/'+relative,
                         'bytes':source.stat().st_size,'sha256':expected,'included_in_git':False,
                         'delivery':'Project owner must provide private access; recipient access not verified.'})
    webcam=json.loads((root/'reports/round7/WEBCAM_RESULTS.json').read_text(encoding='utf-8'))
    for record in webcam['runs']:
        source=root/record['folder']/'backup.avi'
        if sha(source)!=record['video_sha256']: raise ValueError('changed private webcam video')
        external.append({'name':record['folder'].replace('\\','/')+'/backup.avi',
                         'source':str(source),'bytes':source.stat().st_size,'sha256':record['video_sha256'],
                         'included_in_git':False,'delivery':'Private webcam ZIP held locally by project owner.'})
    metadata=ex.output/'delivery/EXTERNAL_ASSETS.json'
    metadata.parent.mkdir(exist_ok=True)
    metadata.write_text(json.dumps({'schema_version':1,'assets':external,
        'private_webcam_package':'artifacts/team-private-20261022/webcam-evidence-private.zip',
        'original_manifest_status':'Bundled: blank-depth-path source manifest recovered with exact historical SHA-256; derived manifest also bundled.'},
        ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    ex.files['delivery/EXTERNAL_ASSETS.json']={'sha256':sha(metadata),'bytes':metadata.stat().st_size,
        'role':'External asset identities and explicit delivery/access limits','source':'Generated from verified source archives and webcam receipt'}
    attributes=ex.output/'.gitattributes'
    attributes.write_bytes(b'* -text\n')
    ex.files['.gitattributes']={'sha256':sha(attributes),'bytes':attributes.stat().st_size,
        'role':'Preserve exact bytes across Git checkout on Windows and Linux',
        'source':'Generated delivery policy; no automatic line-ending conversion'}
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    return ex.finish(commit,removed)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument('--drive',type=Path,default='G:/My Drive/face-pad')
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); m=build(a.root,a.drive,a.output)
    print(json.dumps({'files':len(m['files']),'bytes':sum(r['bytes'] for r in m['files'].values()),
                      'excluded_tracked':len(m['excluded_tracked_files'])}))
