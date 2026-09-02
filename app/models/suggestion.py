from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Suggestion(Base):
    __tablename__ = "suggestions"

    __table_args__ = (
        UniqueConstraint(
            "post_id",
            "image_id",
            name="uq_suggestion_post_image",
        ),
        Index(
            "ix_suggestions_post_id",
            "post_id",
        ),
        Index(
            "ix_suggestions_status",
            "status",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    post_id: Mapped[int] = mapped_column(
        ForeignKey(
            "posts.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    image_id: Mapped[int] = mapped_column(
        ForeignKey(
            "images.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    similarity: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    guard_accepted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )

    guard_reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        server_default="pending",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class SuggestionReview(Base):
    __tablename__ = "suggestion_reviews"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    suggestion_id: Mapped[int] = mapped_column(
        ForeignKey(
            "suggestions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
        index=True,
    )

    decision: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
