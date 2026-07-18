from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.company_invitation import CompanyInvitation
from app.repositories.base import BaseRepository, CompanyScopedRepository


class CompanyInvitationRepository(CompanyScopedRepository[CompanyInvitation]):
    def __init__(self, session: Session) -> None:
        super().__init__(session=session, model=CompanyInvitation)

    def get_by_token_hash(self, token_hash: str) -> CompanyInvitation | None:
        statement = select(CompanyInvitation).where(CompanyInvitation.token_hash == token_hash)
        return self.session.scalar(statement)

    def get_pending_by_company(self, company_id) -> list[CompanyInvitation]:
        statement = select(CompanyInvitation).where(
            CompanyInvitation.company_id == company_id,
            CompanyInvitation.deleted_at.is_(None),
            CompanyInvitation.accepted_at.is_(None),
            CompanyInvitation.expires_at > datetime.now(UTC),
        )
        return list(self.session.scalars(statement).all())
