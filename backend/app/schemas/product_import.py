from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field


class ProductImportRow(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    price: Decimal = Field(ge=0)
    category: str | None = Field(default=None, max_length=120)
    manufacturer: str | None = Field(default=None, max_length=120)
    size: str | None = Field(default=None, max_length=120)


class ProductImportParseResponse(BaseModel):
    columns: list[str] = Field(default_factory=list)
    mapping: dict[str, str | None] = Field(default_factory=dict)
    rows: list[ProductImportRow] = Field(default_factory=list)


class ProductImportConfirmRequest(BaseModel):
    rows: list[ProductImportRow] = Field(min_length=1)


class ProductImportError(BaseModel):
    row_index: int
    name: str
    message: str


class ProductImportConfirmResponse(BaseModel):
    created: int
    errors: list[ProductImportError] = Field(default_factory=list)
