"""Unit tests for the SM-2 spaced repetition mathematical engine."""

import pytest

from sm2 import calculate_next_review


def test_invalid_quality():
    """Ensure the engine rejects invalid scores."""
    with pytest.raises(ValueError):
        calculate_next_review(quality=6, repetition=0, ef=2.5, interval=0)


def test_failed_review():
    """A failed review (quality < 3) should reset repetition and interval."""
    n, ef, i = calculate_next_review(quality=2, repetition=4, ef=2.6, interval=12)
    assert n == 0
    assert i == 1
    assert ef == 2.6  # EF should not drop on failure


def test_successful_review_progression():
    """Verify quality >= 3 increases interval and repetition for established cards."""
    n, ef, i = calculate_next_review(quality=4, repetition=2, ef=2.5, interval=6)
    assert n == 3
    assert i == 15  # math.ceil(6 * 2.5)
    assert ef == 2.5  # EF should increase slightly for a score of 4
