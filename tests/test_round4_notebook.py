import ast
import json
from pathlib import Path


def test_round4_notebook_is_clean_python_and_uses_official_frozen_run():
    root = Path(__file__).resolve().parents[1]
    notebook = json.loads((root / "notebooks/Face_PAD_Round4_Official_Frozen_Head.ipynb").read_text(encoding="utf-8"))
    for cell in notebook["cells"]:
        if cell["cell_type"] == "code":
            ast.parse("".join(cell["source"]))
            assert cell["outputs"] == []
            assert cell["execution_count"] is None
    source = "\n".join("".join(cell["source"]) for cell in notebook["cells"])
    assert "CASIA_E1_CDCN_OFFICIAL_seed42_20260921T114029Z" in source
    assert "comparison_freeze.json" in source
    assert "casia_e2_official_head_frozen.yaml" in source
    assert "CASIA_E1_CDCN_seed42_20260921T024300Z" not in source


def test_clean_official_e1_notebook_has_no_pilot_branch():
    root = Path(__file__).resolve().parents[1]
    notebook = json.loads((root / "notebooks/Face_PAD_Official_CDCN_E1_Clean.ipynb").read_text(encoding="utf-8"))
    for cell in notebook["cells"]:
        if cell["cell_type"] == "code":
            ast.parse("".join(cell["source"]))
            assert cell["outputs"] == []
            assert cell["execution_count"] is None
    source = "\n".join("".join(cell["source"]) for cell in notebook["cells"])
    assert "PILOT_RUN" not in source
    assert "E1_Lite_Pilot" not in source
    assert "CASIA_E1_CDCN_OFFICIAL_seed42_*" in source
