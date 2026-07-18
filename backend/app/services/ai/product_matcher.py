from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import re
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.product import Product
from app.schemas.ai import AIExtractionItem, AIItemStatus, AIRecognitionItemRead
from app.schemas.product import ProductRead


@dataclass(frozen=True)
class MatchedAIItem:
    product_name: str
    quantity: Decimal
    unit: str | None
    confidence: Decimal
    status: AIItemStatus
    match_method: str | None
    needs_review: bool
    matched_product: Product | None


class ProductMatcher:
    def __init__(self, session: Session, *, low_confidence_threshold: Decimal | float) -> None:
        self.session = session
        self.low_confidence_threshold = Decimal(str(low_confidence_threshold))

    def match_items(self, company_id: UUID, items: list[AIExtractionItem]) -> list[MatchedAIItem]:
        products = list(
            self.session.scalars(
                select(Product).where(Product.company_id == company_id, Product.deleted_at.is_(None))
            ).all()
        )
        matched_items: list[MatchedAIItem] = []
        for item in items:
            matched_product, match_method = self._match_product(products, item.product_name)
            needs_review = item.confidence < self.low_confidence_threshold or matched_product is None
            if item.confidence < self.low_confidence_threshold:
                status: AIItemStatus = "needs_review"
            elif matched_product is None:
                status: AIItemStatus = "unmatched"
            else:
                status = "matched"
            matched_items.append(
                MatchedAIItem(
                    product_name=item.product_name,
                    quantity=item.quantity,
                    unit=item.unit,
                    confidence=item.confidence,
                    status=status,
                    match_method=match_method,
                    needs_review=needs_review,
                    matched_product=matched_product,
                )
            )
        return matched_items

    def _match_product(self, products: list[Product], product_name: str) -> tuple[Product | None, str | None]:
        normalized_name = self._normalize(product_name)
        exact_matches: list[tuple[int, Product, str]] = []

        for product in products:
            if self._normalize(product.name) == normalized_name:
                exact_matches.append((100, product, "normalized_name"))
                continue
            if product.name.strip().casefold() == product_name.strip().casefold():
                exact_matches.append((110, product, "exact_name"))
                continue
            if product.sku and self._normalize(product.sku) == normalized_name:
                exact_matches.append((120, product, "sku"))
                continue
            if product.barcode and self._normalize(product.barcode) == normalized_name:
                exact_matches.append((130, product, "barcode"))
                continue
            for alias in product.aliases or []:
                if self._normalize(alias) == normalized_name:
                    exact_matches.append((105, product, "alias"))
                    break
                if alias.strip().casefold() == product_name.strip().casefold():
                    exact_matches.append((115, product, "alias_exact"))
                    break

        if not exact_matches:
            return None, None

        exact_matches.sort(key=lambda item: item[0], reverse=True)
        return exact_matches[0][1], exact_matches[0][2]

    def to_read_item(self, item: MatchedAIItem) -> AIRecognitionItemRead:
        return AIRecognitionItemRead(
            product_name=item.product_name,
            quantity=item.quantity,
            unit=item.unit,
            confidence=item.confidence,
            status=item.status,
            match_method=item.match_method,
            needs_review=item.needs_review,
            matched_product=ProductRead.model_validate(item.matched_product) if item.matched_product else None,
        )

    def _normalize(self, value: str) -> str:
        normalized = re.sub(r"[^a-zA-Z0-9]+", " ", value.casefold()).strip()
        return re.sub(r"\s+", " ", normalized)
