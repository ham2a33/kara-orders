from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.mixins import CompanyScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin


class AILearning(Base, UUIDPrimaryKeyMixin, TimestampMixin, CompanyScopedMixin):
    __tablename__ = "ai_learning"
    __table_args__ = (
        UniqueConstraint("company_id", "normalized_text", name="uq_ai_learning_company_normalized_text"),
        Index("ix_ai_learning_company_normalized_text", "company_id", "normalized_text"),
        Index("ix_ai_learning_company_product_id", "company_id", "product_id"),
    )

    ocr_text: Mapped[str] = mapped_column(String(500), nullable=False)
    normalized_text: Mapped[str] = mapped_column(String(255), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )
    count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    last_used: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
