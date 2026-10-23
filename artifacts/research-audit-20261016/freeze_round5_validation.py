"""Freeze already audited artifacts; no model inference or test scoring."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[2]
audit_dir = root / 'artifacts/round5-full-audit-20261016'
audit = json.loads((audit_dir / 'verification.json').read_text())
assert audit['status'] == 'PASS: full validation audit'
assert audit['selected_variant'] == 'E3' and audit['selection_source'] == 'validation'
drive = Path('G:/My Drive/face-pad')
freeze = {'source_commit':audit['source_commit'], 'selection_source':'validation',
          'selected_variant':audit['selected_variant'], 'runs':{}}
for key, result in audit['runs'].items():
    folder = drive / 'runs' / result['run_id']
    assert not list(folder.glob('test*')), 'Do not create a pre-test freeze after test artifacts exist'
    for name, digest in result['hashes'].items():
        assert hashlib.sha256((folder / name).read_bytes()).hexdigest() == digest, f'Changed since audit: {folder / name}'
    freeze['runs'][key] = {'run':result['run_id'], 'hashes':result['hashes']}
path = drive / f"reports/round5-{audit['source_commit'][:12]}/comparison_freeze.json"
if path.exists():
    assert json.loads(path.read_text()) == freeze, 'Existing freeze differs; preserve and inspect'
else:
    with path.open('x', encoding='utf-8') as stream:
        json.dump(freeze, stream, indent=2)
        stream.write('\n')
assert json.loads(path.read_text()) == freeze
(audit_dir / 'comparison_freeze.json').write_text(json.dumps(freeze, indent=2)+'\n')
print('FROZEN', path)
print('Selected by validation:', freeze['selected_variant'])
