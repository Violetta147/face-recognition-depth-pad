import ast
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def builder():
    spec = importlib.util.spec_from_file_location("build_round6_colab", ROOT / "scripts/build_round6_colab.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_notebook_is_clean_reproducible_and_gates_are_closed():
    nb = json.loads((ROOT / "notebooks/Face_PAD_Round6_CASIA_E1_E3.ipynb").read_text(encoding="utf-8"))
    assert nb == builder().build(ROOT)
    assignments, sources = {}, []
    for c in nb["cells"]:
        if c["cell_type"] != "code":
            continue
        assert c["outputs"] == [] and c["execution_count"] is None
        source = "".join(c["source"])
        sources.append(source)
        for node in ast.parse(source).body:
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        assignments[target.id] = node.value.value
    for gate in ("RUN_SEED43", "RUN_SEED44", "RUN_SEED45", "OPEN_TEST"):
        assert assignments[gate] is False
    source = "\n".join(sources)
    assert source.index("PREFLIGHT PASS") < source.index("RUN_SEED43 = False")
    assert source.index("freeze = batch.freeze()") < source.index("OPEN_TEST = False")
    assert "seed42_" not in source and "3ddfa_worker.py" not in source and "kagglehub" not in source
    assert 'CUDA_VISIBLE_DEVICES=""' in source
    assert "batch.register(DATA_ROOT, RUNS_DIR)" in source
    assert '"--frames-per-video", "20"' in source and '"4,9,14,19"' in source


def test_package_cpu_suite_is_present_and_runtime_scripts_exist():
    for name in builder().CPU_TESTS:
        assert (ROOT / "tests" / name).is_file()
    source = (ROOT / "scripts/package_round6.py").read_text(encoding="utf-8")
    assert '"git","show",f"{commit}:{name}"' in source
    assert "SOURCE_LOCK.json" in source and "archive.testzip()" in source
    assert '"src/", "configs/"' in source


def test_direct_round6_test_cli_requires_freeze_before_loading_data(tmp_path):
    # Exercise the real CLI default (test), without any checkpoint/data available.
    import subprocess
    import yaml
    (tmp_path / "config.yaml").write_text(yaml.safe_dump({"round6_registration":"missing"}))
    result = subprocess.run([sys.executable, str(ROOT / "scripts/score_checkpoint.py"),
                             "--run-dir", str(tmp_path)], text=True, capture_output=True)
    assert result.returncode != 0
    assert "Round 6 test requires --round6-freeze" in result.stderr
    assert "FileNotFoundError" not in result.stderr
