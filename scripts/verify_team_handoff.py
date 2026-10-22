"""Verify delivered file identities without training or inference."""
from pathlib import Path
import argparse
import json
from build_team_handoff import sha, excluded


def verify(root):
    root=Path(root).resolve()
    manifest=json.loads((root/'delivery/FILES.json').read_text(encoding='utf-8'))
    for name, record in manifest['files'].items():
        path=(root/name).resolve()
        if not path.is_relative_to(root) or path.is_symlink(): raise ValueError('unsafe delivery path')
        if any(p in {'.codex','.githooks','project_hooks','project_inventory','__pycache__','demo-runtime'} for p in Path(name).parts):
            raise ValueError(f'non-research delivery member: {name}')
        if path.stat().st_size != record['bytes'] or sha(path)!=record['sha256']:
            raise ValueError(f'changed delivery file: {name}')
        if record['bytes']>=100*1024**2: raise ValueError(f'file exceeds normal GitHub limit: {name}')
    return {'status':'PASS: delivered bytes and research-only membership','files':len(manifest['files'])}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--root',default='.')
    print(json.dumps(verify(p.parse_args().root)))
