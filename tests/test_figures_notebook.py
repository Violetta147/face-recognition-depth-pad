import ast
import json
from pathlib import Path


def test_export_notebook_is_clean_run_all_and_uses_frozen_evidence():
    root = Path(__file__).resolve().parents[1]
    notebook = json.loads((root / "notebooks/Face_PAD_Export_All_Figures_E0_E4.ipynb").read_text(encoding="utf-8"))
    sources = []
    for cell in notebook["cells"]:
        if cell["cell_type"] == "code":
            assert cell["outputs"] == [] and cell["execution_count"] is None
            source = "".join(cell["source"]); ast.parse(source); sources.append(source)
    text = "\n".join(sources)
    assert "comparison_freeze.json" in text and "export_report_figures.py" in text
    assert "figure_manifest.json" in text and "files.download" in text
    assert "subprocess.Popen" in text
    assert "run_experiment.py" not in text
    assert "OPEN_TEST" not in text and "RUN_FULL" not in text
    assert "generate_depth.py" not in text
