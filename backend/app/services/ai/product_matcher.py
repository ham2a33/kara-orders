from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models.product import Product
from app.schemas.ai import AICandidateProductRead, AIExtractionItem, AIItemStatus, AIRecognitionItemRead
from app.schemas.product import ProductRead
from app.services.ai.catalog_match import (
    build_catalog_search_key,
    build_match_diagnostics,
    rank_catalog_matches,
)
from app.services.ai.handwritten_line_parser import normalize_order_unit
from app.services.ai.learning_service import AILearningService
from app.services.ai.ocr_text_normalize import apply_product_synonyms, build_ai_learning_key
from app.services.ai.recognition_logger import log_recognition_stage
from app.services.size_equivalence import sanitize_parsed_line_size


@dataclass(frozen=True)
class MatchedAIItem:
    recognized_name: str
    product_name: str
    size: str | None
    catalog_search_key: str
    quantity: Decimal
    unit: str
    confidence: Decimal
    status: AIItemStatus
    match_method: str | None
    needs_review: bool
    selected_product: Product | None
    candidate_products: list[Product]
    source_line: str | None = None
    match_diagnostics: dict[str, Any] | None = None


class ProductMatcher:
    def __init__(self, session: Session, *, low_confidence_threshold: Decimal | float) -> None:
        self.session = session
        self.low_confidence_threshold = Decimal(str(low_confidence_threshold))
        self.learning = AILearningService(session)

    def match_items(self, company_id: UUID, items: list[AIExtractionItem]) -> list[MatchedAIItem]:
        products = self._fetch_products(company_id)
        matched_items: list[MatchedAIItem] = []
        for item in items:
            matched_items.append(self._match_single_item(company_id, products, item))
        return matched_items

    def resolve_item(self, company_id: UUID, payload: dict[str, object]) -> AIRecognitionItemRead:
        return self.resolve_payload_items(company_id, [payload])[0]

    def resolve_payload_items(self, company_id: UUID, payload_items: list[dict[str, object]]) -> list[AIRecognitionItemRead]:
        products = self._fetch_products(company_id)
        return [self._resolve_item_from_products(company_id, products, payload) for payload in payload_items if isinstance(payload, dict)]

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
            product_name=item.product_name,
            size=item.size,
            catalog_search_key=item.catalog_search_key,
            quantity=item.quantity,
            unit=item.unit,
            confidence=item.confidence,
            status=item.status,
            selected_product_id=selected_product.id if selected_product is not None else None,
            candidate_products=[self._candidate_to_read(product) for product in item.candidate_products],
            match_method=item.match_method,
            needs_review=item.needs_review,
            matched_product=ProductRead.model_validate(selected_product) if selected_product is not None else None,
            match_diagnostics=item.match_diagnostics,
        )

    def _fetch_products(self, company_id: UUID) -> list[Product]:
        return list(
            self.session.scalars(
                select(Product)
                .where(Product.company_id == company_id, Product.deleted_at.is_(None))
                .options(selectinload(Product.images))
            ).all()
        )

    def _get_company_product(self, company_id: UUID, product_id: UUID) -> Product | None:
        return self.session.scalar(
            select(Product)
            .where(
                Product.id == product_id,
                Product.company_id == company_id,
                Product.deleted_at.is_(None),
            )
            .options(selectinload(Product.images))
        )

    def _match_single_item(self, company_id: UUID, products: list[Product], item: AIExtractionItem) -> MatchedAIItem:
        query_name = apply_product_synonyms(item.product_name)
        query_size = sanitize_parsed_line_size(item.size, item.quantity, normalize_order_unit(item.unit))
        item = item.model_copy(update={"size": query_size})
        catalog_key = build_catalog_search_key(query_name, query_size)
        learning_key = build_ai_learning_key(item.product_name, query_size)

        learned_product_id = self.learning.lookup_product_id(
            company_id,
            product_name=item.product_name,
            size=query_size,
        )
        if learned_product_id is not None:
            learned_product = next((product for product in products if product.id == learned_product_id), None)
            if learned_product is None:
                learned_product = self._get_company_product(company_id, learned_product_id)
            if learned_product is not None:
                log_recognition_stage(
                    "AI_LEARNING_HIT",
                    company_id=company_id,
                    learning_key=learning_key,
                    product_id=str(learned_product.id),
                    product_name=learned_product.name,
                )
                return self._build_matched_item(
                    item=item,
                    query_name=query_name,
                    catalog_key=catalog_key,
                    products=products,
                    candidate_products=[learned_product],
                    selected_product=learned_product,
                    status="matched",
                    needs_review=False,
                    match_method="learned",
                    match_count=1,
                )

        scored_matches = rank_catalog_matches(
            products,
            query_name=query_name,
            query_size=query_size,
        )
        candidate_products = [match.profile.product for match in scored_matches]
        diagnostics = build_match_diagnostics(
            products,
            query_name=query_name,
            query_size=query_size,
            matches=scored_matches,
        )
        match_method = "name_then_size" if query_size and scored_matches else ("fuzzy_name" if scored_matches else None)

        selected_product = candidate_products[0] if len(candidate_products) == 1 else None
        if selected_product is not None:
            status: AIItemStatus = "matched"
            needs_review = False
        elif not candidate_products:
            status = "not_found"
            needs_review = True
        else:
            status = "needs_review"
            needs_review = True

        return self._build_matched_item(
            item=item,
            query_name=query_name,
            catalog_key=catalog_key,
            products=products,
            candidate_products=candidate_products,
            selected_product=selected_product,
            status=status,
            needs_review=needs_review,
            match_method=match_method,
            diagnostics=diagnostics,
            match_count=diagnostics.catalog_match_count,
        )

    def _build_matched_item(
        self,
        *,
        item: AIExtractionItem,
        query_name: str,
        catalog_key: str,
        products: list[Product],
        candidate_products: list[Product],
        selected_product: Product | None,
        status: AIItemStatus,
        needs_review: bool,
        match_method: str | None,
        match_count: int,
        diagnostics: Any | None = None,
    ) -> MatchedAIItem:
        if diagnostics is None:
            diagnostics = build_match_diagnostics(
                products,
                query_name=query_name,
                query_size=item.size,
                matches=[],
            )
        ocr_line = item.source_line or catalog_key
        diagnostics_payload = {
            **diagnostics.as_dict(),
            "ocr_line": ocr_line,
            "parser_product_name": query_name,
            "normalized_product_name": query_name,
            "learning_key": build_ai_learning_key(item.product_name, item.size),
            "parser_size": item.size,
            "parser_quantity": str(item.quantity),
            "parser_unit": normalize_order_unit(item.unit),
        }
        log_recognition_stage(
            "CATALOG_LINE_MATCH",
            ocr_line=ocr_line,
            parser_product_name=query_name,
            parser_size=item.size,
            parser_quantity=str(item.quantity),
            parser_unit=item.unit,
            catalog_match_count=match_count,
            best_match_name=diagnostics.best_match_name,
            best_match_score=diagnostics.best_match_score,
            outcome=diagnostics.outcome if match_count != 1 or selected_product is None else "matched",
            failure_reason=diagnostics.failure_reason,
            item_status=status,
            match_method=match_method,
        )

        recognized_name = item.source_line or catalog_key
        return MatchedAIItem(
            recognized_name=recognized_name,
            product_name=query_name.strip(),
            size=item.size,
            catalog_search_key=catalog_key,
            quantity=item.quantity,
            unit=normalize_order_unit(item.unit),
            confidence=item.confidence,
            status=status,
            match_method=match_method,
            needs_review=needs_review,
            selected_product=selected_product,
            candidate_products=candidate_products,
            source_line=item.source_line,
            match_diagnostics=diagnostics_payload,
        )

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

    def _resolve_item_from_products(
        self,
        company_id: UUID,
        products: list[Product],
        payload: dict[str, object],
    ) -> AIRecognitionItemRead:
        product_name = str(payload.get("product_name") or payload.get("recognized_name") or "")
        size_value = payload.get("size")
        size = str(size_value).strip() if isinstance(size_value, str) and size_value.strip() else None
        catalog_key = str(payload.get("catalog_search_key") or build_catalog_search_key(product_name, size))
        item = AIExtractionItem(
            product_name=product_name,
            size=size,
            quantity=Decimal(str(payload.get("quantity") or "0")),
            unit=str(payload.get("unit") or "шт"),
            confidence=Decimal(str(payload.get("confidence") or "0")),
            source_line=str(payload.get("source_line") or payload.get("recognized_name") or catalog_key),
        )
        matched = self._match_single_item(company_id, products, item)

        selected_product_id = self._parse_uuid(payload.get("selected_product_id"))
        selected_product = matched.selected_product
        if selected_product_id is not None:
            selected_product = next(
                (product for product in matched.candidate_products if product.id == selected_product_id),
                None,
            )
            if selected_product is None:
                selected_product = self._get_company_product(company_id, selected_product_id)
        if selected_product is None and len(matched.candidate_products) == 1:
            selected_product = matched.candidate_products[0]
            selected_product_id = selected_product.id
        elif selected_product is None:
            selected_product_id = None

        if selected_product is not None:
            status: AIItemStatus = "matched"
            needs_review = False
        elif not matched.candidate_products:
            status = "not_found"
            needs_review = True
        else:
            status = "needs_review"
            needs_review = True

        recognized_name = str(payload.get("recognized_name") or payload.get("source_line") or catalog_key)
        unit_raw = payload.get("unit")
        unit = normalize_order_unit(unit_raw if isinstance(unit_raw, str) else None)

        return AIRecognitionItemRead(
            recognized_name=recognized_name,
            product_name=matched.product_name or None,
            size=size,
            catalog_search_key=catalog_key,
            quantity=item.quantity,
            unit=unit,
            confidence=item.confidence,
            status=status,
            selected_product_id=selected_product_id,
            candidate_products=[self._candidate_to_read(product) for product in matched.candidate_products],
            match_method=matched.match_method,
            needs_review=needs_review,
            matched_product=ProductRead.model_validate(selected_product) if selected_product is not None else None,
            match_diagnostics=matched.match_diagnostics,
        )

    def _parse_uuid(self, value: object) -> UUID | None:
        if value is None:
            return None
        try:
            return UUID(str(value))
        except (TypeError, ValueError):
            return None
