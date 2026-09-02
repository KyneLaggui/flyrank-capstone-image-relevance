import pytest
from pydantic import ValidationError

from app.schemas.image_analysis import (
    ImageAnalysisResult,
)


def test_valid_image_analysis_result():
    result = ImageAnalysisResult(
        subject="fox",
        category="mammal",
        attributes=[
            "red fur",
            "pointed ears",
        ],
        caption="A red fox in a field.",
        confidence=0.95,
    )

    assert result.subject == "fox"
    assert result.confidence == 0.95


def test_confidence_cannot_exceed_one():
    with pytest.raises(ValidationError):
        ImageAnalysisResult(
            subject="fox",
            category="mammal",
            attributes=["red fur"],
            caption="A red fox.",
            confidence=1.5,
        )


def test_attributes_cannot_be_empty():
    with pytest.raises(ValidationError):
        ImageAnalysisResult(
            subject="fox",
            category="mammal",
            attributes=[],
            caption="A red fox.",
            confidence=0.90,
        )
