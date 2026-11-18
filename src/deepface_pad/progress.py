"""Periodic progress for notebook jobs and loops."""
from __future__ import annotations

from contextlib import suppress
import os
from pathlib import Path
import signal
import subprocess
import threading
import time


class Progress:
    def __init__(self, label, total=None, unit="items", interval=30):
        self.label, self.total, self.unit, self.interval = label, total, unit, interval
        self.done = 0
        self.last_update = self.started = time.monotonic()
        self.stop = threading.Event()

    def update(self, done):
        if done != self.done:
            self.done = done
            self.last_update = time.monotonic()

    def message(self, state):
        now = time.monotonic()
        elapsed = now - self.started
        done = self.done
        count = f" {done:,}/{self.total:,} {self.unit}" if self.total is not None else ""
        eta = ""
        if state == "running" and self.total and 0 < done < self.total:
            idle = now - self.last_update
            eta = (f" | ETA ~{(self.total - done) * elapsed / done:.0f}s" if idle < self.interval * 2
                   else f" | no new count for {idle:.0f}s")
        return f"[{self.label}] {state}{count} | elapsed {elapsed:.0f}s{eta}"

    def _heartbeat(self):
        while not self.stop.wait(self.interval):
            print(self.message("running"), flush=True)

    def __enter__(self):
        print(self.message("started"), flush=True)
        self.thread = threading.Thread(target=self._heartbeat, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop.set()
        self.thread.join()
        print(self.message("failed" if exc_type else "finished"), flush=True)


def run_logged(command, *, label, log, cwd=None, env=None, separate_process_group=False):
    """Forward combined child output to the cell and preserve the original error."""
    log = Path(log)
    log.parent.mkdir(parents=True, exist_ok=True)
    command = [str(arg) for arg in command]
    separate_process_group = separate_process_group and os.name == "posix"
    print(f"Log: {log}", flush=True)
    with log.open("x", encoding="utf-8") as out, Progress(label, interval=60):
        with subprocess.Popen(command, cwd=cwd, env=env, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace",
                              start_new_session=separate_process_group) as proc:
            try:
                for line in proc.stdout:
                    out.write(line)
                    out.flush()
                    print(line, end="", flush=True)
                code = proc.wait()
            except BaseException:
                if separate_process_group:
                    with suppress(ProcessLookupError):
                        os.killpg(proc.pid, signal.SIGTERM)
                elif proc.poll() is None:
                    proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    if separate_process_group:
                        with suppress(ProcessLookupError):
                            os.killpg(proc.pid, signal.SIGKILL)
                    else:
                        proc.kill()
                    proc.wait()
                raise
        if code:
            raise RuntimeError(f"{label} exited with code {code}. Full output: {log}")
