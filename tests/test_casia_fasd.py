from pathlib import Path

from deepface_pad.casia_fasd import VIDEO_METADATA, parse_frame_path


def test_hr1_is_protocol_live_despite_kaggle_folder():
    root = Path("dataset")
    frame = parse_frame_path(root / "test" / "spoof" / "s1vHR_1f7.png", root)
    assert frame is not None
    assert VIDEO_METADATA[frame.video_token] == (1, "live", "high")


def test_precomputed_derivatives_are_excluded():
    root = Path("dataset")
    assert parse_frame_path(root / "train" / "live" / "bs1v1f0.png", root) is None
    assert parse_frame_path(root / "train" / "live" / "fs1v1f0.png", root) is None


def test_other_folder_label_contradiction_is_rejected():
    root = Path("dataset")
    try:
        parse_frame_path(root / "train" / "live" / "s1v3f0.png", root)
    except ValueError as error:
        assert "contradicts" in str(error)
    else:
        raise AssertionError("protocol contradiction was accepted")
