import numpy as np

from deepface_pad.face.gallery import FaceGallery


def test_gallery_round_trip_and_match(tmp_path) -> None:
    gallery = FaceGallery()
    gallery.enroll(
        "member-1",
        "Thanh vien 1",
        [np.array([1.0, 0.0]), np.array([0.9, 0.1])],
        "arcface-test",
        enrolled_at="2026-09-17T00:00:00+00:00",
    )
    target = tmp_path / "gallery.npz"
    gallery.save(target)
    restored = FaceGallery.load(target)
    result = restored.match(np.array([1.0, 0.0]), threshold=0.8)
    assert len(restored) == 1
    assert result.person_id == "member-1"
    assert result.is_unknown is False
    assert restored.entries[0].model_version == "arcface-test"
    assert restored.entries[0].sample_count == 2


def test_gallery_returns_unknown_below_threshold() -> None:
    gallery = FaceGallery()
    gallery.enroll("a", "A", [np.array([1.0, 0.0])], "test")
    result = gallery.match(np.array([0.0, 1.0]), threshold=0.5)
    assert result.is_unknown is True
    assert result.person_id is None
    assert np.isclose(result.similarity, 0.0)


def test_empty_gallery_returns_unknown() -> None:
    result = FaceGallery().match(np.array([1.0, 0.0]), threshold=0.5)
    assert result.is_unknown is True
    assert result.similarity is None

