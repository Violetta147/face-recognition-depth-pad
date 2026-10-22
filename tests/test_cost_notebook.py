import ast
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def test_cost_notebook_is_clean_and_measurement_stays_gated():
    spec=importlib.util.spec_from_file_location("cost_notebook_builder",ROOT/"scripts/build_round6_cost_colab.py")
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    notebook=module.build()
    sources=[];gate=None
    for cell in notebook["cells"]:
        if cell["cell_type"]!="code":continue
        assert cell["execution_count"] is None and cell["outputs"]==[]
        source="".join(cell["source"]);sources.append(source)
        for node in ast.parse(source).body:
            if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="RUN_BENCHMARK" for t in node.targets):
                gate=ast.literal_eval(node.value)
    text="\n".join(sources)
    assert gate is False
    assert text.index("COST PREFLIGHT PASS")<text.index("RUN_BENCHMARK = False")
    assert "CUDA_VISIBLE_DEVICES" in text
    assert "train_pair" not in text and "score_checkpoint.py" not in text and "generate_depth.py" not in text
    for test in module.CPU_TESTS: assert (ROOT/test).is_file()
