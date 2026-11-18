import ast
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace


NOTEBOOK = Path(__file__).resolve().parents[1] / "notebooks/Colab_Runtime_Inventory.ipynb"


def notebook_namespace():
    cells = json.loads(NOTEBOOK.read_text(encoding="utf-8"))["cells"]
    source, = ["".join(cell["source"]) for cell in cells if cell["cell_type"] == "code"]
    module = ast.parse(source)
    assert isinstance(module.body.pop(), ast.Expr)
    namespace = {}
    exec(compile(module, str(NOTEBOOK), "exec"), namespace)
    return namespace


def test_inventory_reports_cpu_affinity_quota_and_effective_ram():
    scope = notebook_namespace()
    files = {
        "/proc/cpuinfo": "model name : Test CPU",
        "/proc/meminfo": "MemTotal: 52428800 kB\nMemAvailable: 41943040 kB",
        "/sys/fs/cgroup/cpu.max": "450000 100000",
        "/sys/fs/cgroup/memory.max": str(32 * 2**30),
        "/sys/fs/cgroup/memory.current": str(8 * 2**30),
    }
    scope.update(read_text=lambda path: files.get(path, ""),
                 os=SimpleNamespace(cpu_count=lambda: 12, sched_getaffinity=lambda _: set(range(8))),
                 shutil=SimpleNamespace(which=lambda _: None))
    result = scope["runtime_inventory"]()
    assert result["cpu_model"] == "Test CPU"
    assert result["affinity_vcpus"] == 8
    assert result["effective_vcpus"] == 4.5
    assert result["visible_ram_gib"] == 50
    assert result["available_ram_gib"] == 24
    assert result["nvidia_gpus"] == []


def test_nvidia_inventory_only_reads_devices_and_handles_driver_failure():
    scope = notebook_namespace()
    scope["shutil"] = SimpleNamespace(which=lambda _: "/usr/bin/nvidia-smi")

    def run(command, **kwargs):
        assert command[1] == "--query-gpu=name,memory.total"
        assert kwargs["timeout"] == 5
        return SimpleNamespace(stdout="NVIDIA A100-SXM4-80GB, 81920\n")

    scope["subprocess"] = SimpleNamespace(run=run, SubprocessError=subprocess.SubprocessError)
    assert scope["nvidia_gpus"]() == [{"name": "NVIDIA A100-SXM4-80GB", "vram_mib": 81920}]

    def unavailable(command, **kwargs):
        raise subprocess.CalledProcessError(1, command)

    scope["subprocess"].run = unavailable
    assert scope["nvidia_gpus"]() == []
