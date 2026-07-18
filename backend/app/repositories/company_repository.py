from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.company import Company
from app.repositories.base import BaseRepository


class CompanyRepository(BaseRepository[Company]):
    def __init__(self, session: Session) -> None:
        super().__init__(session=session, model=Company)

    def get_by_name(self, name: str) -> Company | None:
        statement = select(Company).where(Company.name == name, Company.deleted_at.is_(None))
        return self.session.scalar(statement)

    def get_active_by_id(self, company_id) -> Company | None:
        statement = select(Company).where(Company.id == company_id, Company.deleted_at.is_(None))
        return self.session.scalar(statement)
