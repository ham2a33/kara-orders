from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import CompanyScopedMixin, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.company import Company
    from app.db.models.order import Order
    from app.db.models.user import User


class AIRecognition(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, CompanyScopedMixin):
    __tablename__ = "ai_recognitions"
    __table_args__ = (
        CheckConstraint("input_type in ('photo', 'voice', 'text', 'pdf')", name="input_type_valid"),
        CheckConstraint(
            "status in ('completed', 'needs_review', 'failed', 'converted')",
            name="status_valid",
        ),
        CheckConstraint("confidence IS NULL OR (confidence >= 0 AND confidence <= 1)", name="confidence_bounds"),
        CheckConstraint("tokens_used IS NULL OR tokens_used >= 0", name="tokens_used_non_negative"),
        CheckConstraint(
            "recognition_time_ms IS NULL OR recognition_time_ms >= 0",
            name="recognition_time_ms_non_negative",
        ),
        Index("ix_ai_recognitions_company_created_at", "company_id", "created_at"),
        Index("ix_ai_recognitions_company_status", "company_id", "status"),
        Index("ix_ai_recognitions_company_user_created_at", "company_id", "user_id", "created_at"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.dialects.postgresql.UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    input_type: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="completed",
        server_default=sa.text("'completed'"),
    )
    model_used: Mapped[str] = mapped_column(String(128), nullable=False)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    recognition_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    original_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    original_file_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    original_file_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    original_file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    original_file_mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    raw_ai_response: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    recognized_payload: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    matched_payload: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_order_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.dialects.postgresql.UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    company: Mapped[Company] = relationship("Company")
    user: Mapped[User] = relationship("User")
    created_order: Mapped[Order | None] = relationship("Order")
