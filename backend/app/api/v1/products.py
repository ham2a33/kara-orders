from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.auth import Role
from app.core.config import Settings
from app.dependencies.auth import get_current_user, require_roles
from app.dependencies.deps import get_app_settings, get_db
from app.dependencies.storage import get_storage_service
from app.db.models.user import User
from app.schemas.product import (
    ProductCategoryCreateRequest,
    ProductCategoryListResponse,
    ProductCategoryRead,
    ProductCategoryUpdateRequest,
    ProductCreateRequest,
    ProductImageRead,
    ProductInventoryResponse,
    ProductInventoryTransactionCreateRequest,
    ProductInventoryTransactionRead,
    ProductListResponse,
    ProductRead,
    ProductRestoreResponse,
    ProductTagCreateRequest,
    ProductTagListResponse,
    ProductTagRead,
    ProductTagUpdateRequest,
    ProductUpdateRequest,
)
from app.services.product_service import ProductService
from app.services.storage_service import StorageService
from app.services.platform_service import PlatformService
from app.utils.validators import validate_upload

router = APIRouter(prefix="/products", tags=["products"])


def _service(session: Session, settings: Settings, storage: StorageService | None = None) -> ProductService:
    return ProductService(session=session, settings=settings, storage_service=storage)


@router.get("", response_model=ProductListResponse)
def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(default=None, max_length=255),
    category_id: UUID | None = None,
    tag_id: UUID | None = None,
    is_active: bool | None = None,
    include_deleted: bool = False,
    sort_by: Literal["created_at", "updated_at", "name", "sku", "barcode", "price", "stock_qty", "is_active"] = "created_at",
    sort_dir: Literal["asc", "desc"] = "desc",
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> ProductListResponse:
    return _service(session, settings).list_products(
        current_user.company_id,
        page=page,
        page_size=page_size,
        search=search,
        category_id=category_id,
        tag_id=tag_id,
        is_active=is_active,
        include_deleted=include_deleted,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )


@router.post("", response_model=ProductRead, status_code=201, dependencies=[Depends(require_roles(Role.MANAGER))])
def create_product(
    payload: ProductCreateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> ProductRead:
    return _service(session, settings).create_product(current_user.company_id, payload)


@router.get("/categories", response_model=ProductCategoryListResponse)
def list_categories(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> ProductCategoryListResponse:
    return _service(session, settings).list_categories(current_user.company_id)


@router.post(
    "/categories",
    response_model=ProductCategoryRead,
    status_code=201,
    dependencies=[Depends(require_roles(Role.MANAGER))],
)
def create_category(
    payload: ProductCategoryCreateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> ProductCategoryRead:
    return _service(session, settings).create_category(current_user.company_id, payload)


@router.patch(
    "/categories/{category_id}",
    response_model=ProductCategoryRead,
    dependencies=[Depends(require_roles(Role.MANAGER))],
)
def update_category(
    category_id: UUID,
    payload: ProductCategoryUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> ProductCategoryRead:
    return _service(session, settings).update_category(current_user.company_id, category_id, payload)


@router.delete(
    "/categories/{category_id}",
    response_model=ProductRestoreResponse,
    dependencies=[Depends(require_roles(Role.MANAGER))],
)
def delete_category(
    category_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> ProductRestoreResponse:
    _service(session, settings).delete_category(current_user.company_id, category_id)
    return ProductRestoreResponse(detail="Category deleted")


@router.get("/tags", response_model=ProductTagListResponse)
def list_tags(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> ProductTagListResponse:
    return _service(session, settings).list_tags(current_user.company_id)


@router.post("/tags", response_model=ProductTagRead, status_code=201, dependencies=[Depends(require_roles(Role.MANAGER))])
def create_tag(
    payload: ProductTagCreateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> ProductTagRead:
    return _service(session, settings).create_tag(current_user.company_id, payload)


@router.patch("/tags/{tag_id}", response_model=ProductTagRead, dependencies=[Depends(require_roles(Role.MANAGER))])
def update_tag(
    tag_id: UUID,
    payload: ProductTagUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> ProductTagRead:
    return _service(session, settings).update_tag(current_user.company_id, tag_id, payload)


@router.delete("/tags/{tag_id}", response_model=ProductRestoreResponse, dependencies=[Depends(require_roles(Role.MANAGER))])
def delete_tag(
    tag_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> ProductRestoreResponse:
    _service(session, settings).delete_tag(current_user.company_id, tag_id)
    return ProductRestoreResponse(detail="Tag deleted")


@router.get("/{product_id}", response_model=ProductRead)
def get_product(
    product_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> ProductRead:
    return _service(session, settings).get_product(current_user.company_id, product_id)


@router.patch("/{product_id}", response_model=ProductRead, dependencies=[Depends(require_roles(Role.MANAGER))])
def update_product(
    product_id: UUID,
    payload: ProductUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> ProductRead:
    return _service(session, settings).update_product(current_user.company_id, product_id, payload)


@router.delete("/{product_id}", response_model=ProductRestoreResponse, dependencies=[Depends(require_roles(Role.MANAGER))])
def delete_product(
    product_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> ProductRestoreResponse:
    _service(session, settings).delete_product(current_user.company_id, product_id)
    return ProductRestoreResponse(detail="Product deleted")


@router.post("/{product_id}/restore", response_model=ProductRestoreResponse, dependencies=[Depends(require_roles(Role.MANAGER))])
def restore_product(
    product_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> ProductRestoreResponse:
    return _service(session, settings).restore_product(current_user.company_id, product_id)


@router.get("/{product_id}/inventory", response_model=ProductInventoryResponse)
def get_inventory(
    product_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> ProductInventoryResponse:
    return _service(session, settings).get_inventory(current_user.company_id, product_id)


@router.get("/{product_id}/inventory/history", response_model=list[ProductInventoryTransactionRead])
def get_inventory_history(
    product_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> list[ProductInventoryTransactionRead]:
    return _service(session, settings).list_inventory_history(current_user.company_id, product_id)


@router.post(
    "/{product_id}/inventory/transactions",
    response_model=ProductInventoryResponse,
    dependencies=[Depends(require_roles(Role.MANAGER))],
)
def create_inventory_transaction(
    product_id: UUID,
    payload: ProductInventoryTransactionCreateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> ProductInventoryResponse:
    return _service(session, settings).create_inventory_transaction(
        current_user.company_id,
        product_id,
        current_user,
        payload,
    )


@router.post(
    "/{product_id}/images",
    response_model=ProductImageRead,
    status_code=201,
    dependencies=[Depends(require_roles(Role.MANAGER))],
)
def upload_product_image(
    product_id: UUID,
    file: UploadFile = File(...),
    alt_text: str | None = Form(default=None),
    is_primary: bool = Form(default=False),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
    storage: StorageService = Depends(get_storage_service),
) -> ProductImageRead:
    content = file.file.read()
    system_settings = PlatformService(session).get_system_settings()
    validate_upload(
        content=content,
        filename=file.filename or "product-image.png",
        content_type=file.content_type or "application/octet-stream",
        max_upload_size_mb=system_settings.max_upload_size_mb,
        allowed_file_types=system_settings.allowed_file_types,
        allowed_mime_types={"image/png", "image/jpeg", "image/webp", "image/svg+xml"},
    )
    return _service(session, settings, storage).upload_product_image(
        current_user.company_id,
        product_id,
        content=content,
        content_type=file.content_type or "application/octet-stream",
        filename=file.filename,
        alt_text=alt_text,
        is_primary=is_primary,
    )


@router.delete(
    "/{product_id}/images/{image_id}",
    response_model=ProductRestoreResponse,
    dependencies=[Depends(require_roles(Role.MANAGER))],
)
def delete_product_image(
    product_id: UUID,
    image_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> ProductRestoreResponse:
    _service(session, settings).delete_product_image(current_user.company_id, product_id, image_id)
    return ProductRestoreResponse(detail="Image deleted")
