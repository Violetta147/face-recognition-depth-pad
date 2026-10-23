import hashlib
import json
from pathlib import Path
import shutil

root = Path(__file__).resolve().parents[2]
bundle = root / 'artifacts/figure-handoff-20261016'
metadata_path = bundle / 'package-metadata.json'
metadata = json.loads(metadata_path.read_text())
destination = Path('G:/My Drive/face-pad/handoffs/figures-e0-e4-20261016')
destination.mkdir(parents=True,exist_ok=True)
files = [bundle / name for name in metadata['files']] + [metadata_path]
copied = []
for source in files:
    target = destination / source.name
    expected = hashlib.sha256(source.read_bytes()).hexdigest()
    if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() != expected:
        raise RuntimeError(f'Existing handoff differs: {target}')
    if not target.exists(): shutil.copy2(source,target)
    assert hashlib.sha256(target.read_bytes()).hexdigest() == expected
    copied.append({'path':str(target),'sha256':expected,'bytes':target.stat().st_size})
(bundle / 'drive-delivery.json').write_text(json.dumps(copied,indent=2)+'\n')
print(json.dumps(copied,indent=2))
