import pytest

from app.services.ai_budget import (
    enforce_ai_call_budget,
    estimate_max_ai_calls,
)


def test_estimated_ai_calls():
    result = estimate_max_ai_calls(
        total_items=50,
        max_attempts=3,
    )

    assert result == 150


def test_job_within_budget():
    result = enforce_ai_call_budget(
        total_items=50,
        max_attempts=3,
        max_calls=250,
    )

    assert result == 150


def test_job_over_budget_is_rejected():
    with pytest.raises(
        ValueError,
        match="AI call budget exceeded",
    ):
        enforce_ai_call_budget(
            total_items=100,
            max_attempts=3,
            max_calls=250,
        )
