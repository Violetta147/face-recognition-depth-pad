import importlib.util
from pathlib import Path

import pandas as pd
import pytest

pytest.importorskip("sklearn")
script = Path(__file__).resolve().parents[1] / "scripts/audit_cdc_n_p1_scores.py"
spec = importlib.util.spec_from_file_location("audit_cdc_n_p1_scores", script)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def test_dev_threshold_is_frozen_and_equal_scores_are_rejected():
    dev = pd.DataFrame({"label": [0, 0, 1, 1], "score": [0.1, 0.2, 0.6, 0.9]})
    test = pd.DataFrame({"label": [0, 0, 1, 1], "score": [0.6, 0.7, 0.6, 0.8]})
    result = audit.score(dev, test)
    assert result["threshold_from_dev"] == 0.6
    assert result["test"]["live_rejected"] == 1
    assert result["test"]["attack_accepted"] == 1
    assert result["test"]["acer_pooled"] == 0.5
