import pytest

from app.services.matching import (
    cosine_similarity,
)


def test_identical_vectors():
    score = cosine_similarity(
        [1.0, 2.0, 3.0],
        [1.0, 2.0, 3.0],
    )

    assert score == pytest.approx(1.0)


def test_orthogonal_vectors():
    score = cosine_similarity(
        [1.0, 0.0],
        [0.0, 1.0],
    )

    assert score == pytest.approx(0.0)


def test_opposite_vectors():
    score = cosine_similarity(
        [1.0, 0.0],
        [-1.0, 0.0],
    )

    assert score == pytest.approx(-1.0)


def test_different_dimensions_are_rejected():
    with pytest.raises(ValueError):
        cosine_similarity(
            [1.0, 2.0],
            [1.0, 2.0, 3.0],
        )
