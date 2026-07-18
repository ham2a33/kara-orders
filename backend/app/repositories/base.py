from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

ModelT = TypeVar("ModelT")


class BaseRepository(Generic[ModelT]):
    def __init__(self, session: Session, model: type[ModelT]) -> None:
        self.session = session
        self.model = model

    def get(self, entity_id: Any) -> ModelT | None:
        return self.session.get(self.model, entity_id)

    def list_all(self) -> list[ModelT]:
        statement = select(self.model)
        return list(self.session.scalars(statement).all())

    def add(self, entity: ModelT) -> ModelT:
        self.session.add(entity)
        return entity

    def delete(self, entity: ModelT) -> None:
        self.session.delete(entity)


class CompanyScopedRepository(BaseRepository[ModelT]):
    def list_by_company(self, company_id: Any) -> list[ModelT]:
        statement = select(self.model).where(self.model.company_id == company_id)  # type: ignore[attr-defined]
        return list(self.session.scalars(statement).all())

    def get_by_id_and_company(self, entity_id: Any, company_id: Any) -> ModelT | None:
        statement = select(self.model).where(  # type: ignore[attr-defined]
            self.model.id == entity_id,
            self.model.company_id == company_id,
        )
        return self.session.scalar(statement)
