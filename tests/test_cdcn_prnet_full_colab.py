import ast
import errno
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import time
from types import SimpleNamespace

import pytest

from deepface_pad.progress import run_logged


NOTEBOOK = Path(__file__).resolve().parents[1] / "notebooks/Face_PAD_OULU_NPU_CDCN_PRNet_Full_Train_Dev.ipynb"


def notebook_function(cell, name, namespace=None):
    source = "".join(json.loads(NOTEBOOK.read_text(encoding="utf-8"))["cells"][cell]["source"])
    function = next(node for node in ast.parse(source).body
                    if isinstance(node, ast.FunctionDef) and node.name == name)
    namespace = {} if namespace is None else namespace
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(NOTEBOOK), "exec"), namespace)
    return namespace[name]


@pytest.mark.parametrize("exit_status", [0, 3])
@pytest.mark.parametrize("drive_connected", [True, False])
def test_full_notebook_keeps_local_log_and_exit_status(tmp_path, capsys, exit_status, drive_connected):
    drive = tmp_path / "drive"
    drive.mkdir()
    local = tmp_path / "logs"

    def copyfile(source, destination):
        if not drive_connected:
            raise OSError(errno.ENOTCONN, "Drive disconnected")
        return shutil.copyfile(source, destination)

    run = notebook_function(2, "run", {
        "LOCAL_LOGS": local, "RUN": drive, "WORK": tmp_path, "time": time,
        "os": os, "shutil": SimpleNamespace(copyfile=copyfile), "run_logged": run_logged,
    })
    command = (sys.executable, "-u", "-c", f"import sys; print('worker output'); sys.exit({exit_status})")
    if exit_status:
        with pytest.raises(RuntimeError, match=f"code {exit_status}"):
            run("prepare-full", *command)
    else:
        run("prepare-full", *command)
    log, = local.glob("*.log")
    assert "worker output" in log.read_text(encoding="utf-8")
    assert (drive / log.name).is_file() == drive_connected
    stdout = capsys.readouterr().out
    assert "worker output" in stdout
    assert ("Log cục bộ:" in stdout) == (not drive_connected)


def test_full_notebook_zip_count_distinguishes_missing_and_disconnected(tmp_path):
    count = notebook_function(3, "count_zips")
    (tmp_path / "complete.zip").touch()
    (tmp_path / "partial.part").touch()
    assert count(tmp_path) == 1
    assert count(tmp_path / "missing") == 0

    def disconnected():
        raise OSError(errno.ENOTCONN, "Drive disconnected")

    with pytest.raises(OSError, match="Drive disconnected"):
        count(SimpleNamespace(iterdir=disconnected))


def test_full_notebook_preserves_the_cache_identity_for_known_zip_transport_change():
    scripts_dir = NOTEBOOK.parents[1] / "scripts"
    current = {name: hashlib.sha256((scripts_dir / name).read_text(encoding="utf-8").encode()).hexdigest()
               for name in ("cdcn_prnet_smoke.py", "cdcn_prnet_expanded.py")}
    resolve_cache_hashes = notebook_function(3, "cache_worker_hashes")
    assert resolve_cache_hashes(current) == current | {
        "cdcn_prnet_expanded.py": "9611f0b3464a441ea1582eca0ceca61741f2d644fa1230cb892592ca0751652a",
    }
    changed_smoke = current | {"cdcn_prnet_smoke.py": "0" * 64}
    assert resolve_cache_hashes(changed_smoke) == changed_smoke
