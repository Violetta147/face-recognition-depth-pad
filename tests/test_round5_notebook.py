import ast
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_casia_ablation_has_shared_data_initializer_budget_and_selection():
    paths = [ROOT / "configs" / name for name in (
        "casia_e3_joint_bce.yaml", "casia_e3b_staged_bce.yaml", "casia_e4_staged_focal.yaml")]
    joint, staged, focal = [yaml.safe_load(path.read_text(encoding="utf-8")) for path in paths]
    for cfg in (joint, staged, focal):
        assert cfg["data"] == joint["data"]
        assert cfg["model"] == joint["model"]
        assert cfg["training"]["init_checkpoint"] == joint["training"]["init_checkpoint"]
        assert cfg["training"]["selection_metric"] == "classification_bce"
        assert cfg["seed"] == 42
        assert sum(s["epochs"] for s in cfg["training"]["stages"]) == 16
        assert {s["lr"] for s in cfg["training"]["stages"]} == {1e-4}
    assert [s["name"] for s in joint["training"]["stages"]] == ["joint"]
    assert [s["name"] for s in staged["training"]["stages"]] == ["depth", "head", "joint"]
    assert staged["training"] == focal["training"]
    assert joint["loss"] == staged["loss"]
    difference = {key for key in staged["loss"].keys() | focal["loss"].keys()
                  if staged["loss"].get(key) != focal["loss"].get(key)}
    assert difference == {"classification", "alpha", "gamma"}


def test_round5_notebook_is_clean_and_all_expensive_gates_start_closed():
    notebook = json.loads((ROOT / "notebooks/Face_PAD_Round5_CASIA_E3_E4.ipynb").read_text(encoding="utf-8"))
    assignments = {}
    source = []
    for cell in notebook["cells"]:
        if cell["cell_type"] != "code":
            continue
        assert cell["outputs"] == [] and cell["execution_count"] is None
        text = "".join(cell["source"])
        source.append(text)
        tree = ast.parse(text)
        for node in tree.body:
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        assignments[target.id] = node.value.value
    assert all(assignments[gate] is False for gate in ("RUN_SMOKE", "RUN_FULL", "OPEN_TEST"))
    all_source = "\n".join(source)
    assert "PREFLIGHT PASS" in all_source
    assert "comparison_freeze.json" in all_source
    assert "evaluate_depth.py" in all_source
    assert "kagglehub" not in all_source
    assert "3ddfa_worker.py" not in all_source
    assert all_source.index('comparison_freeze.json') < all_source.index('OPEN_TEST = False')
