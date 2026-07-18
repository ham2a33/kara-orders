from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.ai_recognition import AIRecognition


class AIRecognitionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id_and_company(self, recognition_id: UUID, company_id: UUID) -> AIRecognition | None:
        statement = select(AIRecognition).where(
            AIRecognition.id == recognition_id,
            AIRecognition.company_id == company_id,
        )
        return self.session.scalar(statement)

    def list_by_company(
        self,
        company_id: UUID,
        *,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        status: str | None = None,
        input_type: str | None = None,
    ) -> tuple[list[AIRecognition], int]:
        statement = select(AIRecognition).where(AIRecognition.company_id == company_id)
        if search and search.strip():
            term = f"%{search.strip()}%"
            statement = statement.where(
                AIRecognition.original_text.ilike(term)
                | AIRecognition.original_file_name.ilike(term)
                | AIRecognition.error_message.ilike(term)
            )
        if status:
            statement = statement.where(AIRecognition.status == status)
        if input_type:
            statement = statement.where(AIRecognition.input_type == input_type)

        count_statement = select(func.count()).select_from(statement.subquery())
        total = int(self.session.scalar(count_statement) or 0)
        items = list(
            self.session.scalars(
                statement.order_by(AIRecognition.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
            ).all()
        )
        return items, total

    def add(self, recognition: AIRecognition) -> AIRecognition:
        self.session.add(recognition)
        return recognition
