from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.order import OrderCreateRequest, OrderRead
from app.schemas.product import ProductRead

AIInputType = Literal["photo", "voice", "text", "pdf"]
AIRecognitionStatus = Literal["completed", "needs_review", "failed", "converted"]
AIItemStatus = Literal["matched", "needs_review", "unmatched", "not_found"]


class AICandidateProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    manufacturer: str | None = None
    price: Decimal
    stock_quantity: Decimal | None = None
    sku: str | None = None
    image_url: str | None = None


class AIMatchDiagnosticsRead(BaseModel):
    ocr_line: str | None = None
    parser_product_name: str | None = None
    parser_size: str | None = None
    parser_quantity: str | None = None
    parser_unit: str | None = None
    catalog_match_count: int = 0
    best_match_name: str | None = None
    best_match_score: float | None = None
    outcome: str | None = None
    failure_reason: str | None = None
    name_keyword_hits: list[str] = Field(default_factory=list)
    available_sizes_for_name: list[str] = Field(default_factory=list)
    top_matches: list[dict[str, Any]] = Field(default_factory=list)


class AIRecognitionItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    recognized_name: str
    product_name: str | None = None
    size: str | None = None
    catalog_search_key: str | None = None
    quantity: Decimal
    unit: str | None = None
    confidence: Decimal
    status: AIItemStatus
    selected_product_id: UUID | None = None
    candidate_products: list[AICandidateProductRead] = Field(default_factory=list)
    match_method: str | None = None
    needs_review: bool = False
    matched_product: ProductRead | None = None
    match_diagnostics: dict[str, Any] | None = None


class AIExtractionItem(BaseModel):
    product_name: str = Field(min_length=1, max_length=255)
    size: str | None = Field(default=None, max_length=64)
    quantity: Decimal = Field(gt=0)
    unit: str = Field(default="шт", max_length=32)
    confidence: Decimal = Field(ge=0, le=1)
    source_line: str | None = Field(default=None, max_length=500)


class AIExtractionPayload(BaseModel):
    items: list[AIExtractionItem] = Field(min_length=1)


class AIRecognitionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    user_id: UUID
    input_type: AIInputType
    status: AIRecognitionStatus
    model_used: str
    confidence: Decimal | None = None
    tokens_used: int | None = None
    recognition_time_ms: int | None = None
    original_text: str | None = None
    original_file_url: str | None = None
    original_file_path: str | None = None
    original_file_name: str | None = None
    original_file_mime_type: str | None = None
    raw_ai_response: dict[str, Any] | None = None
    recognized_payload: dict[str, Any] | None = None
    matched_payload: dict[str, Any] | None = None
    error_message: str | None = None
    created_order_id: UUID | None = None
    created_at: datetime
    updated_at: datetime
    items: list[AIRecognitionItemRead] = Field(default_factory=list)


class AIRecognitionListResponse(BaseModel):
    items: list[AIRecognitionRead]
    page: int
    page_size: int
    total: int


class AITextRecognitionRequest(BaseModel):
    text: str = Field(min_length=1, max_length=10000)


class AIRecognitionConfirmRequest(OrderCreateRequest):
    pass


class AIRecognitionItemSelectionRequest(BaseModel):
    selected_product_id: UUID


class AIRecognitionResponse(BaseModel):
    recognition: AIRecognitionRead


class AIRecognitionConfirmResponse(BaseModel):
    recognition: AIRecognitionRead
    order: OrderRead


class AIRecognitionDraftOrderResponse(BaseModel):
    order: OrderRead
