from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile

from app.dependencies.ai import get_ai_service
from app.dependencies.auth import get_current_user
from app.db.models.user import User
from app.schemas.ai import (
    AIRecognitionConfirmRequest,
    AIRecognitionConfirmResponse,
    AIRecognitionDraftOrderResponse,
    AIRecognitionItemSelectionRequest,
    AIRecognitionListResponse,
    AIRecognitionRead,
    AITextRecognitionRequest,
)
from app.services.ai.service import AIService

router = APIRouter(prefix="/ai/order-recognitions", tags=["ai"])


@router.get("", response_model=AIRecognitionListResponse)
def list_recognitions(
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    status: Literal["completed", "needs_review", "failed", "converted"] | None = None,
    input_type: Literal["photo", "voice", "text", "pdf"] | None = None,
    current_user: User = Depends(get_current_user),
    service: AIService = Depends(get_ai_service),
) -> AIRecognitionListResponse:
    return service.list_history(
        current_user.company_id,
        page=page,
        page_size=page_size,
        search=search,
        status=status,
        input_type=input_type,
    )


@router.get("/{recognition_id}", response_model=AIRecognitionRead)
def get_recognition(
    recognition_id: UUID,
    current_user: User = Depends(get_current_user),
    service: AIService = Depends(get_ai_service),
) -> AIRecognitionRead:
    return service.get_history(current_user.company_id, recognition_id)


@router.post("/text", response_model=AIRecognitionRead, status_code=201)
def recognize_text(
    payload: AITextRecognitionRequest,
    current_user: User = Depends(get_current_user),
    service: AIService = Depends(get_ai_service),
) -> AIRecognitionRead:
    return service.recognize_text(current_user.company_id, current_user, payload)


@router.post("/photo", response_model=AIRecognitionRead, status_code=201)
def recognize_photo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    service: AIService = Depends(get_ai_service),
) -> AIRecognitionRead:
    return service.recognize_photo(current_user.company_id, current_user, file=file)


@router.post("/voice", response_model=AIRecognitionRead, status_code=201)
def recognize_voice(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    service: AIService = Depends(get_ai_service),
) -> AIRecognitionRead:
    return service.recognize_voice(current_user.company_id, current_user, file=file)


@router.post("/pdf", response_model=AIRecognitionRead, status_code=201)
def recognize_pdf(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    service: AIService = Depends(get_ai_service),
) -> AIRecognitionRead:
    return service.recognize_pdf(current_user.company_id, current_user, file=file)


@router.post("/{recognition_id}/draft-order", response_model=AIRecognitionDraftOrderResponse, status_code=201)
def create_draft_order_from_recognition(
    recognition_id: UUID,
    current_user: User = Depends(get_current_user),
    service: AIService = Depends(get_ai_service),
) -> AIRecognitionDraftOrderResponse:
    order = service.create_draft_order_from_recognition(
        current_user.company_id,
        recognition_id,
        current_user,
    )
    return AIRecognitionDraftOrderResponse(order=order)


@router.post("/{recognition_id}/confirm", response_model=AIRecognitionConfirmResponse)
def confirm_recognition(
    recognition_id: UUID,
    payload: AIRecognitionConfirmRequest,
    current_user: User = Depends(get_current_user),
    service: AIService = Depends(get_ai_service),
    ) -> AIRecognitionConfirmResponse:
    recognition, order = service.create_order_from_recognition(
        current_user.company_id,
        recognition_id,
        current_user,
        payload,
    )
    return AIRecognitionConfirmResponse(recognition=recognition, order=order)


@router.patch("/{recognition_id}/items/{item_index}/selection", response_model=AIRecognitionRead)
def update_item_selection(
    recognition_id: UUID,
    item_index: int,
    payload: AIRecognitionItemSelectionRequest,
    current_user: User = Depends(get_current_user),
    service: AIService = Depends(get_ai_service),
) -> AIRecognitionRead:
    return service.update_item_selection(
        current_user.company_id,
        recognition_id,
        item_index,
        payload.selected_product_id,
        current_user,
    )
