from __future__ import annotations

import json
import time
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
from app.schemas.ai import AIExtractionPayload, AIRecognitionItemRead, AIRecognitionListResponse, AIRecognitionRead, AITextRecognitionRequest
from app.schemas.order import OrderCreateRequest, OrderRead
from app.services.ai.draft_builder import AIRecognitionDraft, OrderDraftBuilder
from app.services.ai.openai_provider import AIProviderResult, OpenAIProvider
from app.services.ai.prompt_manager import PromptManager
from app.services.ai.product_matcher import ProductMatcher
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
        platform = PlatformService(self.session)
        if not platform.get_system_settings().ai_enabled:
            raise ConfigurationError("AI is disabled by system settings")
        platform.ensure_limit(company_id, "maximum_ai_requests", 1, message="AI request limit reached")
        provider = self._provider()
        start = time.perf_counter()
        raw_payload, draft, provider_result = self._extract_and_match(
            company_id=company_id,
            provider_call=lambda: provider.extract_from_text(
                text=payload.text,
                instruction=self.prompt_manager.build_instruction(),
                context=self.prompt_manager.build_context(source_type="text"),
                schema=self.prompt_manager.schema(),
            ),
        )
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
        return self._serialize_recognition(recognition)

    def recognize_photo(
        self,
        company_id: UUID,
        current_user: User,
        *,
        file: UploadFile,
    ) -> AIRecognitionRead:
        platform = PlatformService(self.session)
        if not platform.get_system_settings().ai_enabled:
            raise ConfigurationError("AI is disabled by system settings")
        platform.ensure_limit(company_id, "maximum_ai_requests", 1, message="AI request limit reached")
        provider = self._provider()
        self._ensure_storage()
        content, mime_type, filename = self._read_upload(file)
        file_info = self._store_input_file(company_id, current_user.id, "photo", filename, mime_type, content)
        start = time.perf_counter()
        raw_payload, draft, provider_result = self._extract_and_match_from_image(
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
            input_bytes=0,
        )
        platform.record_storage_usage(company_id, len(content))
        platform.log_action(
            action="ai_requested",
            company_id=company_id,
            actor_user_id=current_user.id,
            resource_type="ai_recognition",
            resource_id=str(recognition.id),
            description="AI photo recognition requested",
        )
        return self._serialize_recognition(recognition)

    def recognize_voice(
        self,
        company_id: UUID,
        current_user: User,
        *,
        file: UploadFile,
    ) -> AIRecognitionRead:
        platform = PlatformService(self.session)
        if not platform.get_system_settings().ai_enabled:
            raise ConfigurationError("AI is disabled by system settings")
        platform.ensure_limit(company_id, "maximum_ai_requests", 1, message="AI request limit reached")
        provider = self._provider()
        self._ensure_storage()
        content, mime_type, filename = self._read_upload(file)
        file_info = self._store_input_file(company_id, current_user.id, "voice", filename, mime_type, content)
        start = time.perf_counter()
        transcription = provider.transcribe_audio(file_bytes=content, filename=filename, mime_type=mime_type)
        raw_payload, draft, provider_result = self._extract_and_match(
            company_id=company_id,
            provider_call=lambda: provider.extract_from_text(
                text=transcription.text,
                instruction=self.prompt_manager.build_instruction(),
                context=self.prompt_manager.build_context(source_type="voice"),
                schema=self.prompt_manager.schema(),
            ),
        )
        total_tokens = self._sum_tokens([transcription, provider_result])
        recognition = self._create_recognition(
            company_id=company_id,
            current_user=current_user,
            input_type="voice",
            model_used=f"{transcription.model} + {provider_result.model}",
            original_text=transcription.text,
            original_file_url=file_info[0],
            original_file_path=file_info[1],
            original_file_name=filename,
            original_file_mime_type=mime_type,
            provider_result=replace(provider_result, usage=self._merge_usage(provider_result.usage, transcription.usage)),
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
            input_bytes=0,
        )
        platform.record_storage_usage(company_id, len(content))
        platform.log_action(
            action="ai_requested",
            company_id=company_id,
            actor_user_id=current_user.id,
            resource_type="ai_recognition",
            resource_id=str(recognition.id),
            description="AI voice recognition requested",
        )
        return self._serialize_recognition(recognition)

    def recognize_pdf(
        self,
        company_id: UUID,
        current_user: User,
        *,
        file: UploadFile,
    ) -> AIRecognitionRead:
        platform = PlatformService(self.session)
        if not platform.get_system_settings().ai_enabled:
            raise ConfigurationError("AI is disabled by system settings")
        platform.ensure_limit(company_id, "maximum_ai_requests", 1, message="AI request limit reached")
        provider = self._provider()
        self._ensure_storage()
        content, mime_type, filename = self._read_upload(file)
        file_info = self._store_input_file(company_id, current_user.id, "pdf", filename, mime_type, content)
        start = time.perf_counter()
        raw_payload, draft, provider_result = self._extract_and_match_from_file(
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
            input_bytes=0,
        )
        platform.record_storage_usage(company_id, len(content))
        platform.log_action(
            action="ai_requested",
            company_id=company_id,
            actor_user_id=current_user.id,
            resource_type="ai_recognition",
            resource_id=str(recognition.id),
            description="AI pdf recognition requested",
        )
        return self._serialize_recognition(recognition)

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
        if recognition.created_order_id is not None or recognition.status == "converted":
            raise ValidationAppError("Recognition already converted")
        resolved_payload = self._resolve_confirmation_payload(company_id, recognition, payload)
        order = OrderService(self.session, self.settings).create_order(company_id, current_user, resolved_payload)
        recognition.created_order_id = order.id
        recognition.status = "converted"
        self.session.commit()
        self.session.refresh(recognition)
        return self._serialize_recognition(recognition)

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
        if recognition.created_order_id is not None or recognition.status == "converted":
            raise ValidationAppError("Recognition already converted")
        resolved_payload = self._resolve_confirmation_payload(company_id, recognition, payload)
        order = OrderService(self.session, self.settings).create_order(company_id, current_user, resolved_payload)
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
        if recognition.created_order_id is not None or recognition.status == "converted":
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

        resolved_items = self.matcher.resolve_payload_items(company_id, [item])
        resolved_item = resolved_items[0] if resolved_items else None
        if resolved_item is not None:
            candidate_ids = {candidate.id for candidate in resolved_item.candidate_products}
            if not candidate_ids or selected_product_id not in candidate_ids:
                raise ValidationAppError("Selected product is not a valid candidate")
        else:
            raise ValidationAppError("Recognition item could not be resolved")

        item["selected_product_id"] = str(selected_product_id)
        matched_payload["items"] = items
        recognition.matched_payload = matched_payload
        flag_modified(recognition, "matched_payload")
        recognition.status = "completed" if self._all_items_selected(company_id, items) else "needs_review"
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
    ) -> tuple[dict[str, object], AIRecognitionDraft, AIProviderResult]:
        attempts = max(int(self.settings.ai_retry_attempts), 0) + 1
        last_error: Exception | None = None
        for _ in range(attempts):
            try:
                provider_result = provider.extract_from_image(
                    file_bytes=image_bytes,
                    mime_type=mime_type,
                    filename=filename,
                    instruction=self.prompt_manager.build_instruction(),
                    context=self.prompt_manager.build_context(source_type="photo"),
                    schema=self.prompt_manager.schema(),
                )
                raw_payload = self._validate_payload(provider_result.text)
                matched_items = self.matcher.match_items(company_id, raw_payload.items)
                draft = self.draft_builder.build(raw_payload=raw_payload.model_dump(mode="json"), matched_items=matched_items)
                return raw_payload.model_dump(mode="json"), draft, provider_result
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
    ) -> tuple[dict[str, object], AIRecognitionDraft, AIProviderResult]:
        attempts = max(int(self.settings.ai_retry_attempts), 0) + 1
        last_error: Exception | None = None
        for _ in range(attempts):
            try:
                provider_result = provider.extract_from_file(
                    file_bytes=file_bytes,
                    filename=filename,
                    instruction=self.prompt_manager.build_instruction(),
                    context=self.prompt_manager.build_context(source_type="pdf"),
                    schema=self.prompt_manager.schema(),
                )
                raw_payload = self._validate_payload(provider_result.text)
                matched_items = self.matcher.match_items(company_id, raw_payload.items)
                draft = self.draft_builder.build(raw_payload=raw_payload.model_dump(mode="json"), matched_items=matched_items)
                return raw_payload.model_dump(mode="json"), draft, provider_result
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
        return AIExtractionPayload.model_validate(payload)

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
        matched_payload = recognition.matched_payload or {}
        items = matched_payload.get("items")
        if not isinstance(items, list) or len(items) != len(payload.items):
            raise ValidationAppError("Выберите товар для всех позиций.")

        resolved_item_reads = self.matcher.resolve_payload_items(company_id, [item for item in items if isinstance(item, dict)])
        if len(resolved_item_reads) != len(payload.items):
            raise ValidationAppError("Выберите товар для всех позиций.")

        resolved_items: list[dict[str, object]] = []
        for item_payload, resolved_item in zip(payload.items, resolved_item_reads, strict=True):
            selected_product_id = resolved_item.selected_product_id
            if selected_product_id is None:
                raise ValidationAppError("Выберите товар для всех позиций.")
            if item_payload.product_id != selected_product_id:
                raise ValidationAppError("Выберите товар для всех позиций.")
            resolved_items.append(
                {
                    "product_id": selected_product_id,
                    "quantity": item_payload.quantity,
                    "discount_amount": item_payload.discount_amount,
                }
            )

        return OrderCreateRequest.model_validate({**payload.model_dump(mode="json"), "items": resolved_items})

    def _all_items_selected(self, company_id: UUID, items: list[object]) -> bool:
        resolved_items = self.matcher.resolve_payload_items(company_id, [item for item in items if isinstance(item, dict)])
        return bool(resolved_items) and all(item.selected_product_id is not None for item in resolved_items)

    def _provider(self) -> OpenAIProvider:
        return OpenAIProvider(self.settings)

    def _ensure_storage(self) -> None:
        if self.storage is None:
            raise ConfigurationError("Supabase storage is not configured")

    def _read_upload(self, file: UploadFile) -> tuple[bytes, str, str]:
        content = file.file.read()
        filename = file.filename or "upload.bin"
        mime_type = file.content_type or "application/octet-stream"
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
        return content, mime_type, filename

    def _store_input_file(
        self,
        company_id: UUID,
        user_id: UUID,
        input_type: str,
        filename: str,
        mime_type: str,
        content: bytes,
    ) -> tuple[str, str]:
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
