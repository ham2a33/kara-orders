from __future__ import annotations

from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy import Boolean, CheckConstraint, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class SystemSetting(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "system_settings"
    __table_args__ = (
        CheckConstraint("default_currency ~ '^[A-Z]{3}$'", name="default_currency_valid"),
        CheckConstraint("default_tax >= 0 AND default_tax <= 100", name="default_tax_valid"),
        CheckConstraint("max_upload_size_mb >= 0", name="max_upload_size_mb_non_negative"),
    )

    ai_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=sa.text("true"))
    maintenance_mode: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa.text("false"))
    max_upload_size_mb: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=20, server_default=sa.text("20"))
    allowed_file_types: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=lambda: ["pdf", "png", "jpg", "jpeg", "csv", "xlsx"],
        server_default=sa.text("to_jsonb(ARRAY['pdf','png','jpg','jpeg','csv','xlsx']::text[])"),
    )
    default_currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="KZT",
        server_default=sa.text("'KZT'"),
    )
    default_tax: Mapped[Decimal] = mapped_column(
        sa.Numeric(5, 2),
        nullable=False,
        default=Decimal("0"),
        server_default=sa.text("0"),
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

