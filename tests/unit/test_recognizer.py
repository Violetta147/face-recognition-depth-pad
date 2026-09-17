import numpy as np

from deepface_pad.face.recognizer import cosine_similarity, l2_normalize


def test_same_embedding_similarity_is_one() -> None:
    embedding = np.array([0.2, -0.4, 0.8], dtype=np.float32)
    assert np.isclose(cosine_similarity(embedding, embedding), 1.0)


def test_l2_normalization_has_unit_norm() -> None:
    assert np.isclose(np.linalg.norm(l2_normalize(np.array([3.0, 4.0]))), 1.0)


def test_zero_embedding_is_rejected() -> None:
    try:
        l2_normalize(np.zeros(4))
    except ValueError as exc:
        assert "zero" in str(exc)
    else:
        raise AssertionError("Expected a zero embedding to fail")

