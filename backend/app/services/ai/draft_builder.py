from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any
from uuid import UUID

from app.schemas.ai import AIRecognitionItemRead, AIRecognitionRead
from app.services.ai.product_matcher import MatchedAIItem, ProductMatcher


@dataclass(frozen=True)
class AIRecognitionDraft:
    raw_payload: dict[str, Any]
    matched_payload: dict[str, Any]
    confidence: Decimal | None
    status: str
    items: list[AIRecognitionItemRead]


class OrderDraftBuilder:
    def __init__(self, matcher: ProductMatcher) -> None:
        self.matcher = matcher

    def build(self, *, raw_payload: dict[str, Any], matched_items: list[MatchedAIItem]) -> AIRecognitionDraft:
        item_reads = [self.matcher.to_read_item(item) for item in matched_items]
        confidence = self._average_confidence([item.confidence for item in matched_items])
        status = "needs_review" if any(item.selected_product is None for item in matched_items) else "completed"
        return AIRecognitionDraft(
            raw_payload=raw_payload,
            matched_payload={
                "items": [self._serialize_item(item) for item in matched_items],
                "confidence": str(confidence) if confidence is not None else None,
                "status": status,
            },
            confidence=confidence,
            status=status,
            items=item_reads,
        )

    def _serialize_item(self, item: MatchedAIItem) -> dict[str, Any]:
        return {
            "recognized_name": item.recognized_name,
            "product_name": item.recognized_name,
            "quantity": str(item.quantity),
            "unit": item.unit,
            "confidence": str(item.confidence),
            "status": item.status,
            "match_method": item.match_method,
            "needs_review": item.needs_review,
            "selected_product_id": str(item.selected_product.id) if item.selected_product else None,
        }

    def _average_confidence(self, values: list[Decimal]) -> Decimal | None:
        if not values:
            return None
        total = sum(values, Decimal("0"))
        average = total / Decimal(len(values))
        return average.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
