from app.models.image import (
    Image,
    ImageMetadata,
)
from app.models.post import Post
from app.services.mismatch_guard import (
    evaluate_candidate,
)


def create_image(
    subject: str,
    confidence: float,
) -> Image:
    image = Image(
        id=1,
        filename="test.jpg",
        file_path="test.jpg",
        processing_status="completed",
    )

    image.metadata_record = ImageMetadata(
        id=1,
        image_id=1,
        subject=subject,
        category="mammal",
        attributes=["wild animal"],
        caption=f"A photograph of a {subject}.",
        confidence=confidence,
        flagged=confidence < 0.70,
    )

    return image


def create_fox_post() -> Post:
    return Post(
        id=1,
        title="The Behavior of Red Foxes",
        content=(
            "The red fox, also known as "
            "Vulpes vulpes, is a wild canid."
        ),
    )


def test_matching_fox_is_accepted():
    post = create_fox_post()

    image = create_image(
        subject="fox",
        confidence=0.95,
    )

    decision = evaluate_candidate(
        post=post,
        image=image,
        similarity=0.70,
    )

    assert decision.accepted is True
    assert decision.reason


def test_wolf_for_fox_post_is_rejected():
    post = create_fox_post()

    image = create_image(
        subject="wolf",
        confidence=0.95,
    )

    decision = evaluate_candidate(
        post=post,
        image=image,
        similarity=0.90,
    )

    assert decision.accepted is False
    assert decision.reason


def test_low_confidence_image_is_rejected():
    post = create_fox_post()

    image = create_image(
        subject="fox",
        confidence=0.40,
    )

    decision = evaluate_candidate(
        post=post,
        image=image,
        similarity=0.90,
    )

    assert decision.accepted is False
    assert decision.reason
