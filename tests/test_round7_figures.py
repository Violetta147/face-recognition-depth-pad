import numpy as np
import pytest

from deepface_pad.round7 import sha
from deepface_pad.round7_figures import checked_copy, shared_limits, restore_target, compare_frame_score


def test_limits_preserve_extreme_prediction_values_and_reject_nan():
    assert shared_limits([np.array([0.,1.])], [np.array([-0.2,3.7])]) == [-0.2,3.7]
    with pytest.raises(ValueError, match="nonfinite"):
        shared_limits([np.array([0.])], [np.array([np.nan])])


def test_target_restore_refuses_changed_existing_file(tmp_path):
    src, dst = tmp_path/"source.npy", tmp_path/"target.npy"
    np.save(src, np.zeros((32,32), dtype=np.float32))
    checked_copy(src, dst, sha(src))
    assert sha(dst) == sha(src)
    dst.write_bytes(b"changed")
    with pytest.raises(ValueError, match="local target"):
        checked_copy(src, dst, sha(src))
    assert dst.read_bytes() == b"changed"
    with pytest.raises(ValueError, match="source target"):
        checked_copy(src, tmp_path/"other.npy", "bad hash")


def test_missing_attack_zero_requires_exact_frozen_serialization(tmp_path):
    import tarfile
    archive_path = tmp_path/"targets.tar"
    with tarfile.open(archive_path,"w"): pass
    expected = tmp_path/"expected.npy"
    np.save(expected,np.zeros((32,32),dtype=np.float32))
    with tarfile.open(archive_path) as archive:
        method = restore_target(tmp_path/"missing",tmp_path/"restored.npy",sha(expected),0,archive)
        assert "exact snapshot SHA" in method
        with pytest.raises(FileNotFoundError,match="live"):
            restore_target(tmp_path/"missing",tmp_path/"live.npy",sha(expected),1,archive)
        with pytest.raises(ValueError,match="snapshot"):
            restore_target(tmp_path/"missing",tmp_path/"bad.npy","wrong",0,archive)
    assert not (tmp_path/"bad.npy").exists()


def test_diagnostic_retains_failed_original_tolerance_without_claiming_reproduction():
    with pytest.raises(ValueError,match="differs"):
        compare_frame_score(.0015543275512754917,.0015264383982867002)
    result = compare_frame_score(.0015543275512754917,.0015264383982867002,"diagnostic")
    assert result["score_reproduction_passed"] is False
    assert result["comparison_atol"] == 1e-5
    assert result["absolute_difference"] > result["comparison_atol"]
    with pytest.raises(ValueError,match="nonfinite"):
        compare_frame_score(float("nan"),.1,"diagnostic")
