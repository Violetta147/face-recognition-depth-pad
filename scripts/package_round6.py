"""Export only committed Round 6 runtime sources; never copy datasets/weights."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

from build_round6_colab import CPU_TESTS

SCRIPTS = ("build_round6_colab.py", "package_round6.py", "run_experiment.py",
           "score_checkpoint.py", "prepare_casia_fasd.py", "generate_depth.py",
           "materialize_depth_manifest.py", "verify_depth_provenance.py",
           "validate_manifest.py", "audit_depth.py")


def selected_files(root: Path, commit: str) -> list[str]:
    tracked = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", commit], cwd=root, text=True).splitlines()
    explicit = {"pyproject.toml", "AGENTS.md", "data/README.md",
                "reports/ROUND_6_CASIA_RUNBOOK.md", "reports/ROUND_6_REPLICATION_PLAN.md",
                "notebooks/Face_PAD_Round6_CASIA_E1_E3.ipynb"}
    explicit.update("tests/"+name for name in CPU_TESTS)
    explicit.update("scripts/"+name for name in SCRIPTS)
    missing = explicit.difference(tracked)
    if missing:
        raise ValueError(f"commit lacks package members: {sorted(missing)}")
    return sorted(name for name in tracked if name in explicit or name.startswith(("src/", "configs/")))


def package(root: Path, destination: Path) -> dict:
    commit = subprocess.check_output(["git","rev-parse","HEAD"], cwd=root, text=True).strip()
    names = selected_files(root, commit)
    dirty = subprocess.check_output(["git","diff","HEAD","--name-only","--",*names], cwd=root, text=True).splitlines()
    if dirty:
        raise ValueError(f"commit package changes first: {dirty}")
    contents = {name:subprocess.check_output(["git","show",f"{commit}:{name}"],cwd=root) for name in names}
    lock = {"commit":commit,"files":{name:hashlib.sha256(value).hexdigest() for name,value in contents.items()}}
    contents["SOURCE_COMMIT.txt"] = (commit+"\n").encode()
    contents["SOURCE_LOCK.json"] = (json.dumps(lock, indent=2, sort_keys=True)+"\n").encode()
    destination.mkdir(parents=True, exist_ok=True)
    path = destination / "DeepFace-PAD-Round6-source.zip"
    if path.exists():
        raise FileExistsError(f"preserve existing delivery: {path}")
    with zipfile.ZipFile(path, "x", zipfile.ZIP_DEFLATED) as archive:
        for name, payload in sorted(contents.items()):
            item = zipfile.ZipInfo("DeepFace-PAD/"+name, date_time=(2026,10,22,0,0,0))
            item.compress_type = zipfile.ZIP_DEFLATED
            item.external_attr = 0o100644 << 16
            archive.writestr(item, payload)
    with zipfile.ZipFile(path) as archive:
        assert archive.testzip() is None
        assert all(archive.read("DeepFace-PAD/"+name) == payload for name,payload in contents.items())
    notebook = destination / "Face_PAD_Round6_CASIA_E1_E3.ipynb"
    notebook.write_bytes(contents["notebooks/Face_PAD_Round6_CASIA_E1_E3.ipynb"])
    receipt = {"source_commit":commit, "zip_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
               "zip_bytes":path.stat().st_size,"source_files":len(names),
               "notebook_sha256":hashlib.sha256(notebook.read_bytes()).hexdigest(),
               "notebook_clean":True,"gpu_training_executed":False,"test_scoring_executed":False}
    (destination / "package-receipt.json").write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(receipt,indent=2))
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    package(Path(__file__).resolve().parents[1], args.output)
