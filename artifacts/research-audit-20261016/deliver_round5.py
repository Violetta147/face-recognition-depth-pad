from pathlib import Path
import hashlib
import json
import shutil

root = Path(__file__).resolve().parents[2]
bundle = root / "artifacts/round5-handoff-20261016"
metadata_path = bundle / "package-metadata.json"
metadata = json.loads(metadata_path.read_text())
metadata["source_bundle_validation"] = {"passed":70, "skipped":1, "subtests_passed":26,
    "skip_reason":"private presentation binary is intentionally not in the source archive"}
metadata_path.write_text(json.dumps(metadata, indent=2) + "\n")
destination = Path("G:/My Drive/face-pad/handoffs/round5-20261016")
destination.mkdir(parents=True, exist_ok=True)
files = [bundle / "DeepFace-PAD-Round5-source.zip", bundle / "Face_PAD_Round5_CASIA_E3_E4.ipynb",
         metadata_path, root / "reports/ROUND_5_CASIA_RUNBOOK.md"]
copied = []
for source in files:
    target = destination / source.name
    expected = hashlib.sha256(source.read_bytes()).hexdigest()
    if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() != expected:
        raise RuntimeError(f"Existing handoff differs; preserve and inspect: {target}")
    if not target.exists():
        shutil.copy2(source, target)
    assert hashlib.sha256(target.read_bytes()).hexdigest() == expected
    copied.append({"path":str(target), "sha256":expected, "bytes":target.stat().st_size})
(bundle / "drive-delivery.json").write_text(json.dumps(copied, indent=2) + "\n")
print(json.dumps(copied, indent=2))
