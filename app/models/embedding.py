from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Embedding(Base):
    __tablename__ = "embeddings"

    __table_args__ = (
        UniqueConstraint(
            "resource_type",
            "resource_id",
            "model_name",
            name="uq_embedding_resource_model",
        ),
        Index(
            "ix_embeddings_resource",
            "resource_type",
            "resource_id",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    resource_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    resource_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    model_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    vector: Mapped[list[float]] = mapped_column(
        ARRAY(Float),
        nullable=False,
    )

    dimensions: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    content_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
