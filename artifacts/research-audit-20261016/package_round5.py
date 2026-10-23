from pathlib import Path
import hashlib
import io
import json
import subprocess
import zipfile

root = Path(__file__).resolve().parents[2]
output = root / "artifacts/round5-handoff-20261016"
output.mkdir(parents=True, exist_ok=True)
commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
raw = subprocess.check_output(["git", "archive", "--format=zip", "--prefix=DeepFace-PAD/", "HEAD"], cwd=root)
archive = output / "DeepFace-PAD-Round5-source.zip"
excluded = []
with zipfile.ZipFile(io.BytesIO(raw)) as source, zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as dest:
    for item in source.infolist():
        payload = source.read(item.filename)
        if item.filename.endswith(".ipynb") and any(cell.get("outputs") for cell in json.loads(payload).get("cells", [])):
            excluded.append(item.filename)
            continue
        dest.writestr(item, payload)
    dest.writestr("DeepFace-PAD/SOURCE_COMMIT.txt", commit + "\n")
notebook = output / "Face_PAD_Round5_CASIA_E3_E4.ipynb"
notebook.write_bytes(subprocess.check_output(["git", "show", "HEAD:notebooks/Face_PAD_Round5_CASIA_E3_E4.ipynb"], cwd=root))
metadata = {"source_commit":commit, "excluded_executed_notebooks":excluded,
            "files":{path.name:{"sha256":hashlib.sha256(path.read_bytes()).hexdigest(), "bytes":path.stat().st_size}
                     for path in (archive, notebook)}}
(output / "package-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
check_root = output / "source-check"
with zipfile.ZipFile(archive) as package:
    package.extractall(check_root)
print(json.dumps(metadata, indent=2))
