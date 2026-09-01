import hashlib
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.ai_cost_log import AICostLog
from app.models.embedding import Embedding
from app.models.image import Image
from app.models.post import Post
from app.services.embedding import EmbeddingService


embedding_service = EmbeddingService()


def build_image_text(
    image: Image,
) -> str:
    metadata = image.metadata_record

    if metadata is None:
        raise ValueError(
            "Image does not have metadata."
        )

    attributes = ", ".join(
        metadata.attributes
    )

    return (
        f"Subject: {metadata.subject}. "
        f"Category: {metadata.category}. "
        f"Attributes: {attributes}. "
        f"Caption: {metadata.caption}"
    )


def build_post_text(
    post: Post,
) -> str:
    return (
        f"Title: {post.title}. "
        f"Content: {post.content}"
    )


def create_content_hash(
    text: str,
) -> str:
    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()


def save_embedding(
    db: Session,
    resource_type: str,
    resource_id: int,
    text: str,
) -> Embedding:
    content_hash = create_content_hash(
        text
    )

    existing = db.scalar(
        select(Embedding).where(
            Embedding.resource_type
            == resource_type,
            Embedding.resource_id
            == resource_id,
            Embedding.model_name
            == settings.embedding_model,
        )
    )

    if (
        existing is not None
        and existing.content_hash
        == content_hash
    ):
        return existing

    result = embedding_service.embed_text(
        text
    )

    if existing is None:
        embedding = Embedding(
            resource_type=resource_type,
            resource_id=resource_id,
            model_name=settings.embedding_model,
            vector=result.vector,
            dimensions=len(result.vector),
            content_hash=content_hash,
        )

        db.add(embedding)

    else:
        embedding = existing
        embedding.vector = result.vector
        embedding.dimensions = len(
            result.vector
        )
        embedding.content_hash = (
            content_hash
        )

    cost_log = AICostLog(
        operation="embedding_generation",
        model_name=settings.embedding_model,
        resource_type=resource_type,
        resource_id=resource_id,
        input_tokens=result.input_tokens,
        output_tokens=0,
        estimated_cost_usd=Decimal("0"),
    )

    db.add(cost_log)

    db.commit()
    db.refresh(embedding)

    return embedding


def embed_image(
    db: Session,
    image: Image,
) -> Embedding:
    text = build_image_text(
        image
    )

    return save_embedding(
        db=db,
        resource_type="image",
        resource_id=image.id,
        text=text,
    )


def embed_post(
    db: Session,
    post: Post,
) -> Embedding:
    text = build_post_text(
        post
    )

    return save_embedding(
        db=db,
        resource_type="post",
        resource_id=post.id,
        text=text,
    )
