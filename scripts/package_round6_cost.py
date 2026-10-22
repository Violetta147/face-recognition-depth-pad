"""Export a committed cost-only Colab source bundle without images/weights."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile


def package(root, output):
    root,output=Path(root),Path(output)
    commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=root,text=True).strip()
    tracked=subprocess.check_output(["git","ls-tree","-r","--name-only",commit],cwd=root,text=True).splitlines()
    explicit={"pyproject.toml","configs/round6_cost.json","reports/ROUND_6_COST_PLAN.md",
        "scripts/build_round6_cost_colab.py","scripts/package_round6_cost.py",
        "notebooks/Face_PAD_Round6_Cost_E1_E3_E4.ipynb","tests/test_cost.py",
        "tests/test_cost_notebook.py","tests/test_official_depth_head.py"}
    if not explicit.issubset(tracked): raise ValueError("commit all cost package files first")
    names=sorted(p for p in tracked if p in explicit or p.startswith("src/"))
    dirty=subprocess.check_output(["git","diff","HEAD","--name-only","--",*names],cwd=root,text=True)
    if dirty.strip(): raise ValueError("uncommitted cost source changes")
    contents={p:subprocess.check_output(["git","show",f"{commit}:{p}"],cwd=root) for p in names}
    lock={"commit":commit,"files":{p:hashlib.sha256(data).hexdigest() for p,data in contents.items()}}
    contents["SOURCE_LOCK.json"]=(json.dumps(lock,sort_keys=True,indent=2)+"\n").encode()
    contents["SOURCE_COMMIT.txt"]=(commit+"\n").encode()
    output.mkdir(parents=True,exist_ok=True)
    archive=output/"DeepFace-PAD-Round6-cost-source.zip"
    with zipfile.ZipFile(archive,"x",zipfile.ZIP_DEFLATED) as z:
        for p,data in sorted(contents.items()): z.writestr("DeepFace-PAD/"+p,data)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert all(z.read("DeepFace-PAD/"+p)==data for p,data in contents.items())
    notebook=output/"Face_PAD_Round6_Cost_E1_E3_E4.ipynb"
    notebook.write_bytes(contents["notebooks/Face_PAD_Round6_Cost_E1_E3_E4.ipynb"])
    receipt={"source_commit":commit,"source_files":len(names),"zip_sha256":hashlib.sha256(archive.read_bytes()).hexdigest(),
             "notebook_sha256":hashlib.sha256(notebook.read_bytes()).hexdigest(),"gpu_measurement_executed":False}
    (output/"package-receipt.json").write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(receipt,indent=2))


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--output",type=Path,required=True)
    args=p.parse_args();package(Path(__file__).resolve().parents[1],args.output)
