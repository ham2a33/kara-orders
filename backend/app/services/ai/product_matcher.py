from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import re
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models.product import Product
from app.schemas.ai import AICandidateProductRead, AIExtractionItem, AIItemStatus, AIRecognitionItemRead
from app.schemas.product import ProductRead


@dataclass(frozen=True)
class MatchedAIItem:
    recognized_name: str
    quantity: Decimal
    unit: str | None
    confidence: Decimal
    status: AIItemStatus
    match_method: str | None
    needs_review: bool
    selected_product: Product | None
    candidate_products: list[Product]


class ProductMatcher:
    def __init__(self, session: Session, *, low_confidence_threshold: Decimal | float) -> None:
        self.session = session
        self.low_confidence_threshold = Decimal(str(low_confidence_threshold))

    def match_items(self, company_id: UUID, items: list[AIExtractionItem]) -> list[MatchedAIItem]:
        products = self._fetch_products(company_id)
        matched_items: list[MatchedAIItem] = []
        for item in items:
            candidate_products, match_method = self._find_candidates(products, item.product_name)
            selected_product = candidate_products[0] if len(candidate_products) == 1 else None
            status: AIItemStatus
            needs_review: bool
            if selected_product is not None:
                status = "matched"
                needs_review = False
            elif not candidate_products:
                status = "unmatched"
                needs_review = True
            else:
                status = "needs_review"
                needs_review = True
            matched_items.append(
                MatchedAIItem(
                    recognized_name=item.product_name,
                    quantity=item.quantity,
                    unit=item.unit,
                    confidence=item.confidence,
                    status=status,
                    match_method=match_method,
                    needs_review=needs_review,
                    selected_product=selected_product,
                    candidate_products=candidate_products,
                )
            )
        return matched_items

    def resolve_item(self, company_id: UUID, payload: dict[str, object]) -> AIRecognitionItemRead:
        return self.resolve_payload_items(company_id, [payload])[0]

    def resolve_payload_items(self, company_id: UUID, payload_items: list[dict[str, object]]) -> list[AIRecognitionItemRead]:
        products = self._fetch_products(company_id)
        return [self._resolve_item_from_products(products, payload) for payload in payload_items if isinstance(payload, dict)]

    def to_read_item(
        self,
        item: MatchedAIItem,
        *,
        selected_product_id: UUID | None = None,
    ) -> AIRecognitionItemRead:
        selected_product = item.selected_product
        if selected_product_id is not None and (
            selected_product is None or selected_product.id != selected_product_id
        ):
            selected_product = next(
                (product for product in item.candidate_products if product.id == selected_product_id),
                selected_product,
            )
        if selected_product is None and len(item.candidate_products) == 1:
            selected_product = item.candidate_products[0]
        return AIRecognitionItemRead(
            recognized_name=item.recognized_name,
            product_name=item.recognized_name,
            quantity=item.quantity,
            unit=item.unit,
            confidence=item.confidence,
            status=item.status,
            selected_product_id=selected_product.id if selected_product is not None else None,
            candidate_products=[self._candidate_to_read(product) for product in item.candidate_products],
            match_method=item.match_method,
            needs_review=item.needs_review,
            matched_product=ProductRead.model_validate(selected_product) if selected_product is not None else None,
        )

    def _fetch_products(self, company_id: UUID) -> list[Product]:
        return list(
            self.session.scalars(
                select(Product)
                .where(Product.company_id == company_id, Product.deleted_at.is_(None))
                .options(selectinload(Product.images))
            ).all()
        )

    def _find_candidates(self, products: list[Product], product_name: str) -> tuple[list[Product], str | None]:
        normalized_name = self._normalize(product_name)
        if not normalized_name:
            return [], None
        raw_name = product_name.strip().casefold()
        scored_matches: dict[UUID, tuple[int, Product, str]] = {}

        for product in products:
            score, reason = self._score_product(product, normalized_name, raw_name)
            if score <= 0:
                continue
            existing = scored_matches.get(product.id)
            if existing is None or score > existing[0]:
                scored_matches[product.id] = (score, product, reason or "match")

        if not scored_matches:
            return [], None

        ordered_matches = sorted(
            scored_matches.values(),
            key=lambda item: (-item[0], item[1].name.casefold(), str(item[1].id)),
        )
        return [match[1] for match in ordered_matches], ordered_matches[0][2]

    def _score_product(self, product: Product, normalized_name: str, raw_name: str) -> tuple[int, str | None]:
        normalized_product_name = self._normalize(product.name)
        raw_product_name = product.name.strip().casefold()
        normalized_sku = self._normalize(product.sku) if product.sku else None
        normalized_barcode = self._normalize(product.barcode) if product.barcode else None
        normalized_manufacturer = self._normalize(product.manufacturer) if product.manufacturer else None

        exact_checks: list[tuple[bool, int, str]] = [
            (normalized_product_name == normalized_name, 100, "normalized_name"),
            (raw_product_name == raw_name, 110, "exact_name"),
            (normalized_sku == normalized_name, 120, "sku"),
            (normalized_barcode == normalized_name, 130, "barcode"),
            (normalized_manufacturer == normalized_name, 115, "manufacturer"),
        ]

        for alias in product.aliases or []:
            normalized_alias = self._normalize(alias)
            exact_checks.extend(
                [
                    (normalized_alias == normalized_name, 105, "alias"),
                    (alias.strip().casefold() == raw_name, 125, "alias_exact"),
                    (bool(normalized_alias and normalized_name and normalized_alias in normalized_name), 95, "alias_contains"),
                    (bool(normalized_alias and normalized_name and normalized_name in normalized_alias), 90, "alias_contains"),
                ]
            )

        for matched, score, reason in exact_checks:
            if matched:
                return score, reason

        containment_checks: list[tuple[bool, int, str]] = [
            (bool(normalized_name and normalized_product_name and normalized_name in normalized_product_name), 85, "name_contains"),
            (bool(normalized_name and normalized_product_name and normalized_product_name in normalized_name), 80, "name_contains"),
            (bool(normalized_name and normalized_manufacturer and normalized_name in normalized_manufacturer), 75, "manufacturer_contains"),
            (bool(normalized_name and normalized_manufacturer and normalized_manufacturer in normalized_name), 70, "manufacturer_contains"),
            (bool(normalized_name and normalized_sku and normalized_name in normalized_sku), 65, "sku_contains"),
            (bool(normalized_name and normalized_barcode and normalized_name in normalized_barcode), 60, "barcode_contains"),
        ]
        for matched, score, reason in containment_checks:
            if matched:
                return score, reason
        return 0, None

    def _candidate_to_read(self, product: Product) -> AICandidateProductRead:
        primary_image = next((image for image in product.images if image.is_primary), None)
        image = primary_image or (product.images[0] if product.images else None)
        return AICandidateProductRead(
            id=product.id,
            name=product.name,
            manufacturer=product.manufacturer,
            price=product.price,
            stock_quantity=product.stock_qty,
            sku=product.sku,
            image_url=image.url if image is not None else None,
        )

    def _resolve_item_from_products(self, products: list[Product], payload: dict[str, object]) -> AIRecognitionItemRead:
        recognized_name = str(payload.get("recognized_name") or payload.get("product_name") or "")
        candidate_products, match_method = self._find_candidates(products, recognized_name)
        selected_product_id = self._parse_uuid(payload.get("selected_product_id"))
        selected_product = None
        if selected_product_id is not None:
            selected_product = next((product for product in candidate_products if product.id == selected_product_id), None)
        if selected_product is None and len(candidate_products) == 1:
            selected_product = candidate_products[0]
            selected_product_id = selected_product.id
        elif selected_product is None:
            selected_product_id = None

        if selected_product is not None:
            status: AIItemStatus = "matched"
            needs_review = False
        elif not candidate_products:
            status = "unmatched"
            needs_review = True
        else:
            status = "needs_review"
            needs_review = True

        return AIRecognitionItemRead(
            recognized_name=recognized_name,
            product_name=recognized_name,
            quantity=Decimal(str(payload.get("quantity") or "0")),
            unit=payload.get("unit") if isinstance(payload.get("unit"), str) else None,
            confidence=Decimal(str(payload.get("confidence") or "0")),
            status=status,
            selected_product_id=selected_product_id,
            candidate_products=[self._candidate_to_read(product) for product in candidate_products],
            match_method=match_method,
            needs_review=needs_review,
            matched_product=ProductRead.model_validate(selected_product) if selected_product is not None else None,
        )

    def _normalize(self, value: str) -> str:
        normalized = re.sub(r"[^\w]+", " ", value.casefold(), flags=re.UNICODE).strip()
        normalized = re.sub(r"_+", " ", normalized)
        return re.sub(r"\s+", " ", normalized)

    def _parse_uuid(self, value: object) -> UUID | None:
        if value is None:
            return None
        try:
            return UUID(str(value))
        except (TypeError, ValueError):
            return None
