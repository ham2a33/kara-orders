from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.repositories.ai_learning_repository import AILearningRepository
from app.services.ai.ocr_text_normalize import build_ai_learning_key


class AILearningService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repo = AILearningRepository(session)

    def lookup_product_id(
        self,
        company_id: UUID,
        *,
        product_name: str,
        size: str | None,
    ) -> UUID | None:
        key = build_ai_learning_key(product_name, size)
        return self.repo.find_product_id(company_id, key)

    def remember_manual_selection(
        self,
        company_id: UUID,
        *,
        ocr_text: str,
        product_name: str,
        size: str | None,
        product_id: UUID,
    ) -> None:
        normalized = build_ai_learning_key(product_name, size)
        self.repo.record_selection(
            company_id,
            ocr_text=ocr_text or product_name,
            normalized_text=normalized,
            product_id=product_id,
        )
