from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.user import User
from app.repositories.base import BaseRepository, CompanyScopedRepository


class UserRepository(CompanyScopedRepository[User]):
    def __init__(self, session: Session) -> None:
        super().__init__(session=session, model=User)

    def get_any_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email)
        return self.session.scalar(statement)

    def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email, User.deleted_at.is_(None))
        return self.session.scalar(statement)

    def get_active_by_id(self, user_id) -> User | None:
        statement = select(User).where(
            User.id == user_id,
            User.deleted_at.is_(None),
            User.is_active.is_(True),
        )
        return self.session.scalar(statement)

    def get_by_id_and_company(self, user_id, company_id) -> User | None:
        statement = select(User).where(
            User.id == user_id,
            User.company_id == company_id,
            User.deleted_at.is_(None),
        )
        return self.session.scalar(statement)

    def list_by_company(self, company_id) -> list[User]:
        statement = select(User).where(User.company_id == company_id, User.deleted_at.is_(None))
        return list(self.session.scalars(statement).all())
