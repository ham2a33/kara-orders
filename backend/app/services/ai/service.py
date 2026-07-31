from __future__ import annotations

import json
import time
import traceback
from decimal import Decimal
from dataclasses import replace
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.core.config import Settings
from app.core.exceptions import ConfigurationError, NotFoundError, UpstreamServiceError, ValidationAppError
from app.db.models.ai_recognition import AIRecognition
from app.db.models.user import User
from app.repositories.ai_recognition_repository import AIRecognitionRepository
from app.schemas.ai import AIExtractionItem, AIExtractionPayload, AIRecognitionItemRead, AIRecognitionListResponse, AIRecognitionRead, AITextRecognitionRequest
from app.core.order_statuses import ORDER_STATUS_DRAFT, ORDER_STATUS_NEW
from app.schemas.order import OrderCreateRequest, OrderItemWrite, OrderRead, OrderUpdateRequest
from app.services.ai.draft_builder import AIRecognitionDraft, OrderDraftBuilder
from app.services.ai.handwritten_line_parser import (
    ParsedOrderLine,
    build_raw_order_item,
    normalize_order_unit,
    parse_handwritten_order_text_from_lines_batch,
    parsed_item_snapshot,
)
from app.services.ai.ocr_postprocess import postprocess_ocr_order_text, recover_order_lines_from_ocr
from app.services.ai.ocr_text_normalize import normalize_ocr_line
from app.services.ai.openai_provider import AIProviderResult, AIUsage, OpenAIProvider
from app.services.ai.prompt_manager import PromptManager
from app.services.ai.product_matcher import ProductMatcher
from app.services.ai.recognition_logger import log_recognition_stage
from app.services.size_equivalence import sanitize_parsed_line_size
from app.services.order_service import OrderService
from app.services.platform_service import PlatformService
from app.services.storage_service import StorageService, build_storage_object_name
from app.utils.validators import validate_upload


class AIService:
    def __init__(
        self,
        session: Session,
        settings: Settings,
        storage_service: StorageService | None = None,
    ) -> None:
        self.session = session
        self.settings = settings
        self.storage = storage_service
        self.recognitions = AIRecognitionRepository(session)
        self.prompt_manager = PromptManager()
        self.matcher = ProductMatcher(session, low_confidence_threshold=settings.ai_low_confidence_threshold)
        self.draft_builder = OrderDraftBuilder(self.matcher)

    def list_history(
        self,
        company_id: UUID,
        *,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        status: str | None = None,
        input_type: str | None = None,
    ) -> AIRecognitionListResponse:
        items, total = self.recognitions.list_by_company(
            company_id,
            page=page,
            page_size=page_size,
            search=search,
            status=status,
            input_type=input_type,
        )
        return AIRecognitionListResponse(
            items=[self._serialize_recognition(item) for item in items],
            page=page,
            page_size=page_size,
            total=total,
        )

    def get_history(self, company_id: UUID, recognition_id: UUID) -> AIRecognitionRead:
        recognition = self.recognitions.get_by_id_and_company(recognition_id, company_id)
        if recognition is None or recognition.deleted_at is not None:
            raise NotFoundError("Recognition not found")
        return self._serialize_recognition(recognition)

    def recognize_text(
        self,
        company_id: UUID,
        current_user: User,
        payload: AITextRecognitionRequest,
    ) -> AIRecognitionRead:
        log_recognition_stage(
            "START_UPLOAD",
            company_id=company_id,
            user_id=current_user.id,
            input_type="text",
            text_length=len(payload.text),
        )
        try:
            platform = PlatformService(self.session)
            if not platform.get_system_settings().ai_enabled:
                raise ConfigurationError("AI is disabled by system settings")
            platform.ensure_limit(company_id, "maximum_ai_requests", 1, message="AI request limit reached")
            log_recognition_stage("FILE_VALIDATED", company_id=company_id, input_type="text")
            start = time.perf_counter()
            raw_payload, draft, provider_result = self._match_handwritten_lines(company_id, payload.text)
            recognition = self._create_recognition(
                company_id=company_id,
                current_user=current_user,
                input_type="text",
                model_used=provider_result.model,
                original_text=payload.text,
                provider_result=provider_result,
                raw_payload=raw_payload,
                draft=draft,
                recognition_time_ms=int((time.perf_counter() - start) * 1000),
            )
            self.session.commit()
            platform.record_ai_usage(
                company_id,
                tokens_used=recognition.tokens_used,
                recognition_time_ms=recognition.recognition_time_ms,
                input_bytes=0,
            )
            platform.log_action(
                action="ai_requested",
                company_id=company_id,
                actor_user_id=current_user.id,
                resource_type="ai_recognition",
                resource_id=str(recognition.id),
                description="AI text recognition requested",
            )
            result = self._serialize_recognition(recognition)
            log_recognition_stage(
                "RESPONSE_SENT",
                company_id=company_id,
                recognition_id=recognition.id,
                input_type="text",
                status=recognition.status,
                item_count=len(result.items),
            )
            return result
        except Exception as exc:
            log_recognition_stage(
                "RECOGNITION_FAILED",
                company_id=company_id,
                user_id=current_user.id,
                input_type="text",
                location="AIService.recognize_text",
                stack_trace=traceback.format_exc(),
                exc=exc,
            )
            raise

    def recognize_photo(
        self,
        company_id: UUID,
        current_user: User,
        *,
        file: UploadFile,
    ) -> AIRecognitionRead:
        log_recognition_stage(
            "START_UPLOAD",
            company_id=company_id,
            user_id=current_user.id,
            input_type="photo",
            filename=file.filename,
            content_type=file.content_type,
        )
        try:
            platform = PlatformService(self.session)
            if not platform.get_system_settings().ai_enabled:
                raise ConfigurationError("AI is disabled by system settings")
            platform.ensure_limit(company_id, "maximum_ai_requests", 1, message="AI request limit reached")
            provider = self._provider()
            content, mime_type, filename = self._read_upload(file, input_type="photo")
            file_info = self._store_input_file(company_id, current_user.id, "photo", filename, mime_type, content)
            start = time.perf_counter()
            raw_payload, draft, provider_result, ocr_text = self._extract_and_match_from_image(
                company_id=company_id,
                image_bytes=content,
                mime_type=mime_type,
                filename=filename,
                provider=provider,
            )
            recognition = self._create_recognition(
                company_id=company_id,
                current_user=current_user,
                input_type="photo",
                model_used=provider_result.model,
                original_text=ocr_text or None,
                original_file_url=file_info[0],
                original_file_path=file_info[1],
                original_file_name=filename,
                original_file_mime_type=mime_type,
                provider_result=provider_result,
                raw_payload=raw_payload,
                draft=draft,
                recognition_time_ms=int((time.perf_counter() - start) * 1000),
            )
            self.session.commit()
            platform.record_ai_usage(
                company_id,
                tokens_used=recognition.tokens_used,
                recognition_time_ms=recognition.recognition_time_ms,
                input_bytes=len(content),
            )
            if file_info[0] is not None:
                platform.record_storage_usage(company_id, len(content))
            platform.log_action(
                action="ai_requested",
                company_id=company_id,
                actor_user_id=current_user.id,
                resource_type="ai_recognition",
                resource_id=str(recognition.id),
                description="AI photo recognition requested",
            )
            result = self._serialize_recognition(recognition)
            log_recognition_stage(
                "RESPONSE_SENT",
                company_id=company_id,
                recognition_id=recognition.id,
                input_type="photo",
                status=recognition.status,
                item_count=len(result.items),
            )
            return result
        except Exception as exc:
            log_recognition_stage(
                "RECOGNITION_FAILED",
                company_id=company_id,
                user_id=current_user.id,
                input_type="photo",
                location="AIService.recognize_photo",
                stack_trace=traceback.format_exc(),
                exc=exc,
            )
            raise

    def recognize_voice(
        self,
        company_id: UUID,
        current_user: User,
        *,
        file: UploadFile,
    ) -> AIRecognitionRead:
        log_recognition_stage(
            "START_UPLOAD",
            company_id=company_id,
            user_id=current_user.id,
            input_type="voice",
            filename=file.filename,
            content_type=file.content_type,
        )
        try:
            platform = PlatformService(self.session)
            if not platform.get_system_settings().ai_enabled:
                raise ConfigurationError("AI is disabled by system settings")
            platform.ensure_limit(company_id, "maximum_ai_requests", 1, message="AI request limit reached")
            provider = self._provider()
            content, mime_type, filename = self._read_upload(file, input_type="voice")
            file_info = self._store_input_file(company_id, current_user.id, "voice", filename, mime_type, content)
            start = time.perf_counter()
            transcription = provider.transcribe_audio(file_bytes=content, filename=filename, mime_type=mime_type)
            raw_payload, draft, line_result = self._match_handwritten_lines(company_id, transcription.text)
            provider_result = replace(line_result, usage=self._merge_usage(line_result.usage, transcription.usage))
            total_tokens = self._sum_tokens([transcription, line_result])
            recognition = self._create_recognition(
                company_id=company_id,
                current_user=current_user,
                input_type="voice",
                model_used=f"{transcription.model} + {line_result.model}",
                original_text=transcription.text,
                original_file_url=file_info[0],
                original_file_path=file_info[1],
                original_file_name=filename,
                original_file_mime_type=mime_type,
                provider_result=provider_result,
                raw_payload=raw_payload,
                draft=draft,
                recognition_time_ms=int((time.perf_counter() - start) * 1000),
                tokens_used=total_tokens,
            )
            self.session.commit()
            platform.record_ai_usage(
                company_id,
                tokens_used=recognition.tokens_used,
                recognition_time_ms=recognition.recognition_time_ms,
                input_bytes=len(content),
            )
            if file_info[0] is not None:
                platform.record_storage_usage(company_id, len(content))
            platform.log_action(
                action="ai_requested",
                company_id=company_id,
                actor_user_id=current_user.id,
                resource_type="ai_recognition",
                resource_id=str(recognition.id),
                description="AI voice recognition requested",
            )
            result = self._serialize_recognition(recognition)
            log_recognition_stage(
                "RESPONSE_SENT",
                company_id=company_id,
                recognition_id=recognition.id,
                input_type="voice",
                status=recognition.status,
                item_count=len(result.items),
            )
            return result
        except Exception as exc:
            log_recognition_stage(
                "RECOGNITION_FAILED",
                company_id=company_id,
                user_id=current_user.id,
                input_type="voice",
                location="AIService.recognize_voice",
                stack_trace=traceback.format_exc(),
                exc=exc,
            )
            raise

    def recognize_pdf(
        self,
        company_id: UUID,
        current_user: User,
        *,
        file: UploadFile,
    ) -> AIRecognitionRead:
        log_recognition_stage(
            "START_UPLOAD",
            company_id=company_id,
            user_id=current_user.id,
            input_type="pdf",
            filename=file.filename,
            content_type=file.content_type,
        )
        try:
            platform = PlatformService(self.session)
            if not platform.get_system_settings().ai_enabled:
                raise ConfigurationError("AI is disabled by system settings")
            platform.ensure_limit(company_id, "maximum_ai_requests", 1, message="AI request limit reached")
            provider = self._provider()
            content, mime_type, filename = self._read_upload(file, input_type="pdf")
            file_info = self._store_input_file(company_id, current_user.id, "pdf", filename, mime_type, content)
            start = time.perf_counter()
            raw_payload, draft, provider_result, ocr_text = self._extract_and_match_from_file(
                company_id=company_id,
                file_bytes=content,
                filename=filename,
                provider=provider,
            )
            recognition = self._create_recognition(
                company_id=company_id,
                current_user=current_user,
                input_type="pdf",
                model_used=provider_result.model,
                original_text=ocr_text or None,
                original_file_url=file_info[0],
                original_file_path=file_info[1],
                original_file_name=filename,
                original_file_mime_type=mime_type,
                provider_result=provider_result,
                raw_payload=raw_payload,
                draft=draft,
                recognition_time_ms=int((time.perf_counter() - start) * 1000),
            )
            self.session.commit()
            platform.record_ai_usage(
                company_id,
                tokens_used=recognition.tokens_used,
                recognition_time_ms=recognition.recognition_time_ms,
                input_bytes=len(content),
            )
            if file_info[0] is not None:
                platform.record_storage_usage(company_id, len(content))
            platform.log_action(
                action="ai_requested",
                company_id=company_id,
                actor_user_id=current_user.id,
                resource_type="ai_recognition",
                resource_id=str(recognition.id),
                description="AI pdf recognition requested",
            )
            result = self._serialize_recognition(recognition)
            log_recognition_stage(
                "RESPONSE_SENT",
                company_id=company_id,
                recognition_id=recognition.id,
                input_type="pdf",
                status=recognition.status,
                item_count=len(result.items),
            )
            return result
        except Exception as exc:
            log_recognition_stage(
                "RECOGNITION_FAILED",
                company_id=company_id,
                user_id=current_user.id,
                input_type="pdf",
                location="AIService.recognize_pdf",
                stack_trace=traceback.format_exc(),
                exc=exc,
            )
            raise

    def confirm_recognition(
        self,
        company_id: UUID,
        recognition_id: UUID,
        current_user: User,
        payload: OrderCreateRequest,
    ) -> AIRecognitionRead:
        recognition = self.recognitions.get_by_id_and_company(recognition_id, company_id)
        if recognition is None or recognition.deleted_at is not None:
            raise NotFoundError("Recognition not found")
        if recognition.status == "converted":
            raise ValidationAppError("Recognition already converted")
        resolved_payload = self._resolve_confirmation_payload(company_id, recognition, payload)
        order = OrderService(self.session, self.settings).create_order(company_id, current_user, resolved_payload)
        recognition.created_order_id = order.id
        recognition.status = "converted"
        self.session.commit()
        self.session.refresh(recognition)
        return self._serialize_recognition(recognition)

    def create_draft_order_from_recognition(
        self,
        company_id: UUID,
        recognition_id: UUID,
        current_user: User,
    ) -> OrderRead:
        recognition = self.recognitions.get_by_id_and_company(recognition_id, company_id)
        if recognition is None or recognition.deleted_at is not None:
            raise NotFoundError("Recognition not found")
        if recognition.status == "converted":
            raise ValidationAppError("Recognition already converted")

        order_service = OrderService(self.session, self.settings)
        if recognition.created_order_id is not None:
            existing = order_service.get_order(company_id, recognition.created_order_id)
            if existing.status == ORDER_STATUS_DRAFT:
                return existing
            raise ValidationAppError("Recognition already linked to an order")

        draft_items = self._recognition_items_to_order_writes(company_id, recognition)
        if not draft_items:
            raise ValidationAppError(
                "Нет позиций с выбранным товаром. Выберите товар вручную на экране заказа."
            )

        order = order_service.create_order(
            company_id,
            current_user,
            OrderCreateRequest(
                notes=f"Черновик из AI-распознавания {recognition.id}",
                status=ORDER_STATUS_DRAFT,
                items=draft_items,
            ),
        )
        recognition.created_order_id = order.id
        self.session.commit()
        self.session.refresh(recognition)
        PlatformService(self.session).log_action(
            action="order_draft_created_from_ai",
            company_id=company_id,
            actor_user_id=current_user.id,
            resource_type="ai_recognition",
            resource_id=str(recognition.id),
            description="AI recognition saved as draft order",
            metadata={"order_id": str(order.id)},
        )
        return order

    def create_order_from_recognition(
        self,
        company_id: UUID,
        recognition_id: UUID,
        current_user: User,
        payload: OrderCreateRequest,
    ) -> tuple[AIRecognitionRead, OrderRead]:
        recognition = self.recognitions.get_by_id_and_company(recognition_id, company_id)
        if recognition is None or recognition.deleted_at is not None:
            raise NotFoundError("Recognition not found")
        if recognition.status == "converted":
            raise ValidationAppError("Recognition already converted")

        order_service = OrderService(self.session, self.settings)
        final_status = payload.status if payload.status != ORDER_STATUS_DRAFT else ORDER_STATUS_NEW
        resolved_payload = self._resolve_confirmation_payload(company_id, recognition, payload)

        if recognition.created_order_id is not None:
            order = order_service.update_order(
                company_id,
                recognition.created_order_id,
                OrderUpdateRequest(
                    customer_name=resolved_payload.customer_name,
                    customer_phone=resolved_payload.customer_phone,
                    customer_address=resolved_payload.customer_address,
                    notes=resolved_payload.notes,
                    status=final_status,
                    items=resolved_payload.items,
                ),
            )
        else:
            order = order_service.create_order(
                company_id,
                current_user,
                resolved_payload.model_copy(update={"status": final_status}),
            )

        recognition.created_order_id = order.id
        recognition.status = "converted"
        self.session.commit()
        self.session.refresh(recognition)
        PlatformService(self.session).log_action(
            action="order_created_from_ai",
            company_id=company_id,
            actor_user_id=current_user.id,
            resource_type="ai_recognition",
            resource_id=str(recognition.id),
            description="AI recognition converted into an order",
            metadata={"order_id": str(order.id)},
        )
        return self._serialize_recognition(recognition), order

    def update_item_selection(
        self,
        company_id: UUID,
        recognition_id: UUID,
        item_index: int,
        selected_product_id: UUID,
        current_user: User,
    ) -> AIRecognitionRead:
        recognition = self.recognitions.get_by_id_and_company(recognition_id, company_id)
        if recognition is None or recognition.deleted_at is not None:
            raise NotFoundError("Recognition not found")
        if recognition.status == "converted":
            raise ValidationAppError("Recognition already converted")

        matched_payload = dict(recognition.matched_payload or {})
        items = matched_payload.get("items")
        if not isinstance(items, list):
            raise ValidationAppError("Recognition items are missing")
        if item_index < 0 or item_index >= len(items):
            raise ValidationAppError("Invalid recognition item index")

        item = items[item_index]
        if not isinstance(item, dict):
            raise ValidationAppError("Recognition item is invalid")

        # The operator edits the order manually, so any active catalog product is accepted:
        # suggested candidates are only a shortcut, not a limit.
        selected_product = self.matcher._get_company_product(company_id, selected_product_id)
        if selected_product is None:
            raise ValidationAppError("Selected product is not valid")

        item["selected_product_id"] = str(selected_product_id)
        matched_payload["items"] = items
        recognition.matched_payload = matched_payload
        flag_modified(recognition, "matched_payload")
        recognition.status = "completed" if self._all_items_selected(company_id, items) else "needs_review"

        product_name = str(item.get("product_name") or "")
        size_value = item.get("size")
        size = str(size_value).strip() if isinstance(size_value, str) and size_value.strip() else None
        ocr_text = str(item.get("source_line") or item.get("recognized_name") or product_name)
        self.matcher.learning.remember_manual_selection(
            company_id,
            ocr_text=ocr_text,
            product_name=product_name or ocr_text,
            size=size,
            product_id=selected_product_id,
        )

        self.session.commit()
        self.session.refresh(recognition)
        PlatformService(self.session).log_action(
            action="ai_recognition_item_selected",
            company_id=company_id,
            actor_user_id=current_user.id,
            resource_type="ai_recognition",
            resource_id=str(recognition.id),
            description="AI recognition item selection updated",
            metadata={"item_index": item_index, "selected_product_id": str(selected_product_id)},
        )
        return self._serialize_recognition(recognition)

    def _extract_and_match(
        self,
        *,
        company_id: UUID,
        input_type: str,
        provider_call,
    ) -> tuple[dict[str, object], AIRecognitionDraft, AIProviderResult]:
        attempts = max(int(self.settings.ai_retry_attempts), 0) + 1
        last_error: Exception | None = None
        for _ in range(attempts):
            try:
                provider_result = provider_call()
                raw_payload = self._validate_payload(provider_result.text)
                matched_items = self.matcher.match_items(company_id, raw_payload.items)
                draft = self.draft_builder.build(raw_payload=raw_payload.model_dump(mode="json"), matched_items=matched_items)
                log_recognition_stage(
                    "PARSED_PRODUCTS",
                    company_id=company_id,
                    input_type=input_type,
                    extracted_count=len(raw_payload.items),
                    matched_count=len(matched_items),
                    draft_status=draft.status,
                )
                return raw_payload.model_dump(mode="json"), draft, provider_result
            except (UpstreamServiceError, ValidationAppError) as exc:
                last_error = exc
        if last_error is not None:
            raise last_error
        raise UpstreamServiceError("AI request failed")

    def _extract_and_match_from_image(
        self,
        *,
        company_id: UUID,
        image_bytes: bytes,
        mime_type: str,
        filename: str,
        provider: OpenAIProvider,
    ) -> tuple[dict[str, object], AIRecognitionDraft, AIProviderResult, str]:
        attempts = max(int(self.settings.ai_retry_attempts), 0) + 1
        last_error: Exception | None = None
        for _ in range(attempts):
            try:
                ocr_result = provider.ocr_text_from_image(
                    file_bytes=image_bytes,
                    mime_type=mime_type,
                    filename=filename,
                )
                ocr_text = postprocess_ocr_order_text(ocr_result.text)
                log_recognition_stage(
                    "OCR_POSTPROCESSED",
                    company_id=company_id,
                    input_type="photo",
                    raw_line_count=len(ocr_result.text.splitlines()),
                    recovered_line_count=len(ocr_text.splitlines()) if ocr_text else 0,
                )
                raw_payload, draft, parse_result = self._match_handwritten_lines(company_id, ocr_text)
                provider_result = replace(
                    parse_result,
                    usage=ocr_result.usage,
                    model=f"{ocr_result.model}+handwritten-line-parser",
                    raw_response={"ocr": ocr_result.raw_response, "parser": parse_result.raw_response},
                )
                return raw_payload, draft, provider_result, ocr_text.strip()
            except (UpstreamServiceError, ValidationAppError) as exc:
                last_error = exc
        if last_error is not None:
            raise last_error
        raise UpstreamServiceError("AI request failed")

    def _extract_and_match_from_file(
        self,
        *,
        company_id: UUID,
        file_bytes: bytes,
        filename: str,
        provider: OpenAIProvider,
    ) -> tuple[dict[str, object], AIRecognitionDraft, AIProviderResult, str]:
        attempts = max(int(self.settings.ai_retry_attempts), 0) + 1
        last_error: Exception | None = None
        for _ in range(attempts):
            try:
                ocr_result = provider.ocr_text_from_file(file_bytes=file_bytes, filename=filename)
                ocr_text = postprocess_ocr_order_text(ocr_result.text)
                log_recognition_stage(
                    "OCR_POSTPROCESSED",
                    company_id=company_id,
                    input_type="pdf",
                    raw_line_count=len(ocr_result.text.splitlines()),
                    recovered_line_count=len(ocr_text.splitlines()) if ocr_text else 0,
                )
                raw_payload, draft, parse_result = self._match_handwritten_lines(company_id, ocr_text)
                provider_result = replace(
                    parse_result,
                    usage=ocr_result.usage,
                    model=f"{ocr_result.model}+handwritten-line-parser",
                    raw_response={"ocr": ocr_result.raw_response, "parser": parse_result.raw_response},
                )
                return raw_payload, draft, provider_result, ocr_text.strip()
            except (UpstreamServiceError, ValidationAppError) as exc:
                last_error = exc
        if last_error is not None:
            raise last_error
        raise UpstreamServiceError("AI request failed")

    def _validate_payload(self, raw_json: str) -> AIExtractionPayload:
        try:
            payload = json.loads(raw_json)
        except json.JSONDecodeError as exc:
            raise ValidationAppError("AI returned invalid JSON") from exc
        return self._normalize_extraction_payload(AIExtractionPayload.model_validate(payload))

    def _normalize_extraction_payload(self, payload: AIExtractionPayload) -> AIExtractionPayload:
        normalized_items = []
        for item in payload.items:
            unit = normalize_order_unit(item.unit)
            size = item.size.strip() if isinstance(item.size, str) and item.size.strip() else None
            size = sanitize_parsed_line_size(size, item.quantity, unit)
            normalized_items.append(
                AIExtractionItem(
                    product_name=item.product_name.strip(),
                    size=size,
                    quantity=item.quantity,
                    unit=unit,
                    confidence=item.confidence,
                    source_line=item.source_line.strip()
                    if isinstance(item.source_line, str) and item.source_line.strip()
                    else None,
                )
            )
        return AIExtractionPayload(items=normalized_items)

    def _match_handwritten_lines(
        self,
        company_id: UUID,
        text: str,
    ) -> tuple[dict[str, object], AIRecognitionDraft, AIProviderResult]:
        raw_text = text or ""
        ocr_nonempty = bool(raw_text.strip())
        log_recognition_stage(
            "OCR_TEXT",
            company_id=company_id,
            ocr_text=raw_text[:10000],
            ocr_text_length=len(raw_text),
            ocr_nonempty=ocr_nonempty,
        )

        if not ocr_nonempty:
            raise ValidationAppError("Не удалось распознать ни одной строки заказа. Одна строка = один товар.")

        processed_text = postprocess_ocr_order_text(raw_text)
        recovered_lines = recover_order_lines_from_ocr(raw_text)
        recovered_lines = [line.strip() for line in recovered_lines if line.strip()]
        if not recovered_lines:
            recovered_lines = [raw_text.strip()]

        original_lines = list(recovered_lines)
        normalized_lines = [normalize_ocr_line(line) for line in original_lines]
        log_recognition_stage(
            "OCR_NORMALIZED",
            company_id=company_id,
            normalized_line_count=len(normalized_lines),
            lines=normalized_lines[:200],
        )

        log_recognition_stage(
            "POSTPROCESS_LINES",
            company_id=company_id,
            processed_text=processed_text[:10000],
            postprocess_line_count=len(original_lines),
            lines=original_lines[:200],
        )

        parse_batch = parse_handwritten_order_text_from_lines_batch(normalized_lines)
        if parse_batch.final_count == 0:
            parse_batch = parse_handwritten_order_text_from_lines_batch([normalize_ocr_line(raw_text.strip())])

        strict_entries = [entry for entry in parse_batch.lines if entry.parse_mode == "strict"]
        fallback_entries = [entry for entry in parse_batch.lines if entry.parse_mode == "fallback"]
        raw_entries = [entry for entry in parse_batch.lines if entry.parse_mode == "raw"]
        final_entries: list[ParsedOrderLine] = []
        for index, entry in enumerate(parse_batch.lines):
            source_line = original_lines[index] if index < len(original_lines) else entry.item.source_line
            final_entries.append(
                ParsedOrderLine(
                    item=replace(entry.item, source_line=source_line),
                    parse_mode=entry.parse_mode,
                )
            )
        if not final_entries:
            final_entries = [
                ParsedOrderLine(item=build_raw_order_item(original_lines[0] if original_lines else raw_text.strip()), parse_mode="raw"),
            ]
            raw_entries = final_entries

        log_recognition_stage(
            "STRICT_ITEMS",
            company_id=company_id,
            strict_count=len(strict_entries),
            items=[parsed_item_snapshot(entry) for entry in strict_entries[:200]],
        )
        log_recognition_stage(
            "FALLBACK_ITEMS",
            company_id=company_id,
            fallback_count=len(fallback_entries),
            items=[parsed_item_snapshot(entry) for entry in fallback_entries[:200]],
        )

        final_items = [entry.item for entry in final_entries]
        log_recognition_stage(
            "FINAL_ITEMS",
            company_id=company_id,
            ocr_line_count=len(raw_text.splitlines()) or 1,
            postprocess_line_count=len(original_lines),
            strict_count=len(strict_entries),
            fallback_count=len(fallback_entries),
            raw_count=len(raw_entries),
            final_count=len(final_items),
            items=[parsed_item_snapshot(entry) for entry in final_entries[:200]],
        )

        items = [
            AIExtractionItem(
                product_name=line.product_name,
                size=line.size,
                quantity=line.quantity,
                unit=line.unit,
                confidence=line.confidence,
                source_line=line.source_line,
            )
            for line in final_items
        ]
        payload = self._normalize_extraction_payload(AIExtractionPayload(items=items))
        raw_payload = payload.model_dump(mode="json")
        matched_items = self.matcher.match_items(company_id, payload.items)
        draft = self.draft_builder.build(raw_payload=raw_payload, matched_items=matched_items)
        log_recognition_stage(
            "PARSED_PRODUCTS",
            company_id=company_id,
            input_type="handwritten_lines",
            extracted_count=len(payload.items),
            matched_count=len(matched_items),
            draft_status=draft.status,
        )
        provider_result = AIProviderResult(
            text=json.dumps(raw_payload, ensure_ascii=False),
            raw_response={"parser": "handwritten_line_parser", "line_count": len(payload.items)},
            model="handwritten-line-parser",
            usage=AIUsage(),
        )
        return raw_payload, draft, provider_result

    def _create_recognition(
        self,
        *,
        company_id: UUID,
        current_user: User,
        input_type: str,
        model_used: str,
        provider_result: AIProviderResult,
        raw_payload: dict[str, object],
        draft: AIRecognitionDraft,
        recognition_time_ms: int,
        original_text: str | None = None,
        original_file_url: str | None = None,
        original_file_path: str | None = None,
        original_file_name: str | None = None,
        original_file_mime_type: str | None = None,
        tokens_used: int | None = None,
    ) -> AIRecognition:
        recognition = AIRecognition(
            company_id=company_id,
            user_id=current_user.id,
            input_type=input_type,
            status=draft.status,
            model_used=model_used,
            confidence=draft.confidence,
            tokens_used=tokens_used if tokens_used is not None else provider_result.usage.total_tokens,
            recognition_time_ms=recognition_time_ms,
            original_text=original_text,
            original_file_url=original_file_url,
            original_file_path=original_file_path,
            original_file_name=original_file_name,
            original_file_mime_type=original_file_mime_type,
            raw_ai_response=provider_result.raw_response,
            recognized_payload=raw_payload,
            matched_payload=draft.matched_payload,
        )
        self.session.add(recognition)
        self.session.flush()
        return recognition

    def _serialize_recognition(self, recognition: AIRecognition) -> AIRecognitionRead:
        items = self._deserialize_items(recognition.company_id, recognition.matched_payload)
        return AIRecognitionRead(
            id=recognition.id,
            company_id=recognition.company_id,
            user_id=recognition.user_id,
            input_type=recognition.input_type,
            status=recognition.status,
            model_used=recognition.model_used,
            confidence=recognition.confidence,
            tokens_used=recognition.tokens_used,
            recognition_time_ms=recognition.recognition_time_ms,
            original_text=recognition.original_text,
            original_file_url=recognition.original_file_url,
            original_file_path=recognition.original_file_path,
            original_file_name=recognition.original_file_name,
            original_file_mime_type=recognition.original_file_mime_type,
            raw_ai_response=recognition.raw_ai_response,
            recognized_payload=recognition.recognized_payload,
            matched_payload=recognition.matched_payload,
            error_message=recognition.error_message,
            created_order_id=recognition.created_order_id,
            created_at=recognition.created_at,
            updated_at=recognition.updated_at,
            items=items,
        )

    def _deserialize_items(self, company_id: UUID, payload: dict[str, object] | None) -> list[AIRecognitionItemRead]:
        if not payload:
            return []
        items = payload.get("items")
        if not isinstance(items, list):
            return []
        return self.matcher.resolve_payload_items(company_id, [item for item in items if isinstance(item, dict)])

    def _resolve_confirmation_payload(
        self,
        company_id: UUID,
        recognition: AIRecognition,
        payload: OrderCreateRequest,
    ) -> OrderCreateRequest:
        """Validate the operator-edited order lines coming from the order screen.

        The AI result is only a starting point: lines can be added, removed, re-pointed to
        another catalog product or re-priced, so the payload is authoritative. We only check
        that every product belongs to the company (OrderService re-checks on write) and
        remember the manual picks that differ from what the matcher suggested.
        """
        for item_payload in payload.items:
            if self.matcher._get_company_product(company_id, item_payload.product_id) is None:
                raise ValidationAppError("Выберите товар из каталога для всех позиций.")

        self._remember_confirmed_selections(company_id, recognition, payload)
        return payload

    def _remember_confirmed_selections(
        self,
        company_id: UUID,
        recognition: AIRecognition,
        payload: OrderCreateRequest,
    ) -> None:
        """Teach the matcher from lines the operator kept in the same position."""
        matched_payload = recognition.matched_payload or {}
        items = matched_payload.get("items")
        if not isinstance(items, list) or len(items) != len(payload.items):
            return

        for item, item_payload in zip(items, payload.items, strict=True):
            if not isinstance(item, dict):
                continue
            product_name = str(item.get("product_name") or item.get("recognized_name") or "").strip()
            if not product_name:
                continue
            size_value = item.get("size")
            size = str(size_value).strip() if isinstance(size_value, str) and size_value.strip() else None
            ocr_text = str(item.get("source_line") or item.get("recognized_name") or product_name)
            self.matcher.learning.remember_manual_selection(
                company_id,
                ocr_text=ocr_text,
                product_name=product_name,
                size=size,
                product_id=item_payload.product_id,
            )

    def _recognition_items_to_order_writes(
        self,
        company_id: UUID,
        recognition: AIRecognition,
    ) -> list[OrderItemWrite]:
        matched_payload = recognition.matched_payload or {}
        raw_items = matched_payload.get("items")
        if not isinstance(raw_items, list):
            return []

        resolved_items = self.matcher.resolve_payload_items(
            company_id,
            [item for item in raw_items if isinstance(item, dict)],
        )
        writes: list[OrderItemWrite] = []
        for resolved_item in resolved_items:
            product_id = resolved_item.selected_product_id
            if product_id is None and resolved_item.matched_product is not None:
                product_id = resolved_item.matched_product.id
            if product_id is None and len(resolved_item.candidate_products) == 1:
                product_id = resolved_item.candidate_products[0].id
            if product_id is None:
                continue
            writes.append(
                OrderItemWrite(
                    product_id=product_id,
                    quantity=resolved_item.quantity,
                    discount_amount=Decimal("0"),
                )
            )
        return writes

    def _all_items_selected(self, company_id: UUID, items: list[object]) -> bool:
        resolved_items = self.matcher.resolve_payload_items(company_id, [item for item in items if isinstance(item, dict)])
        return bool(resolved_items) and all(item.selected_product_id is not None for item in resolved_items)

    def _provider(self) -> OpenAIProvider:
        return OpenAIProvider(self.settings)

    def _read_upload(self, file: UploadFile, *, input_type: str) -> tuple[bytes, str, str]:
        content = file.file.read()
        filename = file.filename or "upload.bin"
        mime_type = file.content_type or "application/octet-stream"
        log_recognition_stage(
            "FILE_RECEIVED",
            input_type=input_type,
            filename=filename,
            content_type=mime_type,
            size_bytes=len(content),
        )
        system_settings = PlatformService(self.session).get_system_settings()
        validate_upload(
            content=content,
            filename=filename,
            content_type=mime_type,
            max_upload_size_mb=system_settings.max_upload_size_mb,
            allowed_file_types=system_settings.allowed_file_types,
            allowed_mime_types={
                "application/pdf",
                "image/png",
                "image/jpeg",
                "image/webp",
                "audio/mpeg",
                "audio/mp3",
                "audio/wav",
                "audio/x-wav",
                "audio/mp4",
                "audio/m4a",
                "audio/aac",
                "audio/ogg",
                "application/octet-stream",
            },
        )
        log_recognition_stage(
            "FILE_VALIDATED",
            input_type=input_type,
            filename=filename,
            content_type=mime_type,
            size_bytes=len(content),
        )
        return content, mime_type, filename

    def _store_input_file(
        self,
        company_id: UUID,
        user_id: UUID,
        input_type: str,
        filename: str,
        mime_type: str,
        content: bytes,
    ) -> tuple[str | None, str | None]:
        if self.storage is None:
            log_recognition_stage(
                "FILE_STORAGE_SKIPPED",
                company_id=company_id,
                input_type=input_type,
                filename=filename,
                reason="storage_not_configured",
            )
            return None, None
        suffix = filename.split(".")[-1] if "." in filename else None
        object_path = build_storage_object_name(str(company_id), input_type, str(user_id), suffix=suffix)
        result = self.storage.upload_public_file(
            bucket=self.settings.supabase_storage_bucket,
            object_path=object_path,
            content=content,
            content_type=mime_type,
        )
        return result.public_url, result.object_path

    def _sum_tokens(self, results: list[AIProviderResult]) -> int | None:
        total = 0
        seen = False
        for result in results:
            if result.usage.total_tokens is None:
                continue
            total += result.usage.total_tokens
            seen = True
        return total if seen else None

    def _merge_usage(self, primary, secondary):
        total = None
        if primary.total_tokens is not None or secondary.total_tokens is not None:
            total = (primary.total_tokens or 0) + (secondary.total_tokens or 0)
        return replace(
            primary,
            input_tokens=(primary.input_tokens or 0) + (secondary.input_tokens or 0),
            output_tokens=(primary.output_tokens or 0) + (secondary.output_tokens or 0),
            total_tokens=total,
        )
