import math
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.embedding import Embedding
from app.models.image import Image
from app.models.post import Post


@dataclass
class RankedImage:
    image_id: int
    filename: str
    subject: str | None
    category: str | None
    similarity: float


def cosine_similarity(
    vector_a: list[float],
    vector_b: list[float],
) -> float:
    if len(vector_a) != len(vector_b):
        raise ValueError(
            "Embedding vectors must have the same dimensions."
        )

    dot_product = sum(
        a * b
        for a, b in zip(
            vector_a,
            vector_b,
        )
    )

    magnitude_a = math.sqrt(
        sum(
            value * value
            for value in vector_a
        )
    )

    magnitude_b = math.sqrt(
        sum(
            value * value
            for value in vector_b
        )
    )

    if magnitude_a == 0 or magnitude_b == 0:
        raise ValueError(
            "Cannot calculate cosine similarity "
            "for a zero-length vector."
        )

    return dot_product / (
        magnitude_a * magnitude_b
    )


def rank_images_for_post(
    db: Session,
    post: Post,
    limit: int = 10,
) -> list[RankedImage]:
    post_embedding = db.scalar(
        select(Embedding).where(
            Embedding.resource_type == "post",
            Embedding.resource_id == post.id,
            Embedding.model_name
            == settings.embedding_model,
        )
    )

    if post_embedding is None:
        raise ValueError(
            "Post does not have an embedding."
        )

    image_embeddings = list(
        db.scalars(
            select(Embedding)
            .where(
                Embedding.resource_type == "image",
                Embedding.model_name
                == settings.embedding_model,
            )
            .order_by(Embedding.resource_id)
        )
    )

    if not image_embeddings:
        raise ValueError(
            "No image embeddings are available."
        )

    ranked_images: list[RankedImage] = []

    for image_embedding in image_embeddings:
        image = db.get(
            Image,
            image_embedding.resource_id,
        )

        if image is None:
            continue

        similarity = cosine_similarity(
            post_embedding.vector,
            image_embedding.vector,
        )

        metadata = image.metadata_record

        ranked_images.append(
            RankedImage(
                image_id=image.id,
                filename=image.filename,
                subject=(
                    metadata.subject
                    if metadata
                    else None
                ),
                category=(
                    metadata.category
                    if metadata
                    else None
                ),
                similarity=similarity,
            )
        )

    ranked_images.sort(
        key=lambda result: result.similarity,
        reverse=True,
    )

    return ranked_images[:limit]


def get_similarity_for_candidate(
    db: Session,
    post: Post,
    image: Image,
) -> float:
    post_embedding = db.scalar(
        select(Embedding).where(
            Embedding.resource_type == "post",
            Embedding.resource_id == post.id,
            Embedding.model_name
            == settings.embedding_model,
        )
    )

    if post_embedding is None:
        raise ValueError(
            "Post does not have an embedding."
        )

    image_embedding = db.scalar(
        select(Embedding).where(
            Embedding.resource_type == "image",
            Embedding.resource_id == image.id,
            Embedding.model_name
            == settings.embedding_model,
        )
    )

    if image_embedding is None:
        raise ValueError(
            "Image does not have an embedding."
        )

    return cosine_similarity(
        post_embedding.vector,
        image_embedding.vector,
    )
