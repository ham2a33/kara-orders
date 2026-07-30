from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.core.auth import Role
from app.core.config import Settings
from app.dependencies.auth import get_current_user, require_roles
from app.dependencies.deps import get_app_settings, get_db
from app.db.models.user import User
from app.schemas.product_import import (
    ProductImportConfirmRequest,
    ProductImportConfirmResponse,
    ProductImportParseResponse,
)
from app.services.platform_service import PlatformService
from app.services.product_import_service import ProductImportService
from app.utils.validators import validate_upload

router = APIRouter(prefix="/products/import", tags=["product-import"])


def _service(session: Session, settings: Settings) -> ProductImportService:
    return ProductImportService(session=session, settings=settings)


@router.post(
    "/parse-excel",
    response_model=ProductImportParseResponse,
    dependencies=[Depends(require_roles(Role.MANAGER))],
)
def parse_excel_import(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> ProductImportParseResponse:
    content = file.file.read()
    system_settings = PlatformService(session).get_system_settings()
    validate_upload(
        content=content,
        filename=file.filename or "import.xlsx",
        content_type=file.content_type or "application/octet-stream",
        max_upload_size_mb=system_settings.max_upload_size_mb,
        allowed_file_types=["csv", "xlsx"],
    )
    return _service(session, settings).parse_excel(content, file.filename or "import.xlsx")


@router.post(
    "/parse-pdf",
    response_model=ProductImportParseResponse,
    dependencies=[Depends(require_roles(Role.MANAGER))],
)
def parse_pdf_import(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> ProductImportParseResponse:
    content = file.file.read()
    system_settings = PlatformService(session).get_system_settings()
    validate_upload(
        content=content,
        filename=file.filename or "import.pdf",
        content_type=file.content_type or "application/pdf",
        max_upload_size_mb=system_settings.max_upload_size_mb,
        allowed_file_types=["pdf"],
        allowed_mime_types={"application/pdf"},
    )
    return _service(session, settings).parse_pdf(content, file.filename or "import.pdf")


@router.post(
    "/parse-photo",
    response_model=ProductImportParseResponse,
    dependencies=[Depends(require_roles(Role.MANAGER))],
)
def parse_photo_import(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> ProductImportParseResponse:
    content = file.file.read()
    system_settings = PlatformService(session).get_system_settings()
    validate_upload(
        content=content,
        filename=file.filename or "import.jpg",
        content_type=file.content_type or "image/jpeg",
        max_upload_size_mb=system_settings.max_upload_size_mb,
        allowed_file_types=["png", "jpg", "jpeg", "webp"],
        allowed_mime_types={"image/png", "image/jpeg", "image/webp"},
    )
    return _service(session, settings).parse_photo(
        content,
        file.filename or "import.jpg",
        file.content_type or "image/jpeg",
    )


@router.post(
    "/confirm",
    response_model=ProductImportConfirmResponse,
    dependencies=[Depends(require_roles(Role.MANAGER))],
)
def confirm_import(
    payload: ProductImportConfirmRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> ProductImportConfirmResponse:
    return _service(session, settings).confirm_import(current_user.company_id, payload)
