from dataclasses import dataclass

from app.config import settings
from app.models.image import Image
from app.models.post import Post


SUBJECT_ALIASES = {
    "fox": (
        "red fox",
        "vulpes vulpes",
        "fox",
    ),
    "wolf": (
        "gray wolf",
        "grey wolf",
        "canis lupus",
        "wolf",
    ),
    "dog": (
        "domestic dog",
        "canis lupus familiaris",
        "dog",
    ),
    "bear": (
        "brown bear",
        "ursus arctos",
        "bear",
    ),
    "deer": (
        "deer",
        "cervid",
    ),
    "lion": (
        "african lion",
        "panthera leo",
        "lion",
    ),
}


@dataclass
class GuardDecision:
    accepted: bool
    reason: str
    post_subject: str | None
    image_subject: str | None


def normalize_subject(
    text: str,
) -> str | None:
    normalized_text = text.lower().strip()

    matches: list[
        tuple[int, str]
    ] = []

    for canonical_subject, aliases in SUBJECT_ALIASES.items():
        for alias in aliases:
            if alias in normalized_text:
                matches.append(
                    (
                        len(alias),
                        canonical_subject,
                    )
                )

    if not matches:
        return None

    matches.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    return matches[0][1]


def infer_post_subject(
    post: Post,
) -> str | None:
    title_subject = normalize_subject(
        post.title
    )

    if title_subject is not None:
        return title_subject

    return normalize_subject(
        post.content
    )


def infer_image_subject(
    image: Image,
) -> str | None:
    metadata = image.metadata_record

    if metadata is None:
        return None

    return normalize_subject(
        metadata.subject
    )


def evaluate_candidate(
    post: Post,
    image: Image,
    similarity: float,
) -> GuardDecision:
    metadata = image.metadata_record

    if metadata is None:
        return GuardDecision(
            accepted=False,
            reason=(
                "Rejected because the image "
                "does not have analyzed metadata."
            ),
            post_subject=infer_post_subject(post),
            image_subject=None,
        )

    post_subject = infer_post_subject(
        post
    )

    image_subject = infer_image_subject(
        image
    )

    if post_subject is None:
        return GuardDecision(
            accepted=False,
            reason=(
                "Rejected because the post subject "
                "could not be identified."
            ),
            post_subject=None,
            image_subject=image_subject,
        )

    if image_subject is None:
        return GuardDecision(
            accepted=False,
            reason=(
                "Rejected because the image subject "
                "could not be identified."
            ),
            post_subject=post_subject,
            image_subject=None,
        )

    if (
        metadata.confidence
        < settings.vision_confidence_threshold
    ):
        return GuardDecision(
            accepted=False,
            reason=(
                "Rejected because image analysis "
                f"confidence {metadata.confidence:.3f} "
                "is below the required threshold "
                f"{settings.vision_confidence_threshold:.3f}."
            ),
            post_subject=post_subject,
            image_subject=image_subject,
        )

    if (
        similarity
        < settings.match_similarity_threshold
    ):
        return GuardDecision(
            accepted=False,
            reason=(
                "Rejected because semantic similarity "
                f"{similarity:.3f} is below the required "
                f"threshold "
                f"{settings.match_similarity_threshold:.3f}."
            ),
            post_subject=post_subject,
            image_subject=image_subject,
        )

    if (
        post_subject is not None
        and image_subject is not None
        and post_subject != image_subject
    ):
        return GuardDecision(
            accepted=False,
            reason=(
                "Rejected because of a subject/category "
                f"mismatch: the post is about "
                f"'{post_subject}', but the image subject "
                f"is '{image_subject}'."
            ),
            post_subject=post_subject,
            image_subject=image_subject,
        )

    return GuardDecision(
        accepted=True,
        reason=(
            "Accepted because the candidate passed "
            "the confidence, similarity, and subject "
            "compatibility checks."
        ),
        post_subject=post_subject,
        image_subject=image_subject,
    )
