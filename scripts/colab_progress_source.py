"""Embed the progress runner in a notebook using a locked source ZIP."""
from pathlib import Path


def progress_source():
    source = (Path(__file__).resolve().parents[1] / "src/deepface_pad/progress.py").read_text(encoding="utf-8")
    return f"""
import os, time
exec({source!r})
def notebook_run(command, cwd=None, env=None):
    command = list(map(str, command))
    env = dict(os.environ if env is None else env, PYTHONUNBUFFERED="1")
    label = next((Path(arg).stem for arg in command[1:] if not arg.startswith("-")), Path(command[0]).stem)
    run_logged(command, label=label, log=DRIVE_ROOT / "notebook-logs" / f"{{label}}-{{time.time_ns()}}.log",
               cwd=cwd, env=env)
"""
