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
AIItemStatus = Literal["matched", "needs_review", "unmatched"]


class AIRecognitionItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_name: str
    quantity: Decimal
    unit: str | None = None
    confidence: Decimal
    status: AIItemStatus
    match_method: str | None = None
    needs_review: bool = False
    matched_product: ProductRead | None = None


class AIExtractionItem(BaseModel):
    product_name: str = Field(min_length=1, max_length=255)
    quantity: Decimal = Field(gt=0)
    unit: str | None = Field(default=None, max_length=32)
    confidence: Decimal = Field(ge=0, le=1)


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


class AIRecognitionResponse(BaseModel):
    recognition: AIRecognitionRead


class AIRecognitionConfirmResponse(BaseModel):
    recognition: AIRecognitionRead
    order: OrderRead
