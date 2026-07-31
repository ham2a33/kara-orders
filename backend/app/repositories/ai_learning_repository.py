from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.ai_learning import AILearning


class AILearningRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def find_product_id(self, company_id: UUID, normalized_text: str) -> UUID | None:
        key = normalized_text.casefold().strip()
        if not key:
            return None
        row = self.session.scalar(
            select(AILearning.product_id).where(
                AILearning.company_id == company_id,
                AILearning.normalized_text == key,
            )
        )
        return row

    def record_selection(
        self,
        company_id: UUID,
        *,
        ocr_text: str,
        normalized_text: str,
        product_id: UUID,
    ) -> AILearning:
        key = normalized_text.casefold().strip()
        existing = self.session.scalar(
            select(AILearning).where(
                AILearning.company_id == company_id,
                AILearning.normalized_text == key,
            )
        )
        now = datetime.now(timezone.utc)
        if existing is not None:
            if existing.product_id != product_id:
                existing.product_id = product_id
            existing.ocr_text = ocr_text[:500]
            existing.count = int(existing.count) + 1
            existing.last_used = now
            self.session.flush()
            return existing

        row = AILearning(
            company_id=company_id,
            ocr_text=ocr_text[:500],
            normalized_text=key,
            product_id=product_id,
            count=1,
            last_used=now,
        )
        self.session.add(row)
        self.session.flush()
        return row
