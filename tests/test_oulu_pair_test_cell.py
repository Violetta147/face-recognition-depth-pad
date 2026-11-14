import importlib.util
from pathlib import Path

import pytest


def test_scoring_cell_refuses_changed_lock(tmp_path):
    script = Path(__file__).resolve().parents[1] / "scripts/oulu_pair_test_colab_cell.py"
    spec = importlib.util.spec_from_file_location("oulu_pair_test_cell", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    pair = tmp_path / "cdcn-pair-p1/seed43-1794667766717400448"
    pair.mkdir(parents=True)
    (pair / "pair_dev_lock.json").write_text("{}")
    with pytest.raises(ValueError, match="Pair Dev lock differs"):
        module.score_locked_pair(tmp_path, tmp_path, tmp_path)
    assert not (pair / "locked-test").exists()
