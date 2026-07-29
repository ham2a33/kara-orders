from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import Settings
from app.core.exceptions import ConflictError, ConfigurationError, NotFoundError, ValidationAppError
from app.db.models.inventory_transaction import InventoryTransaction
from app.db.models.product import Product
from app.db.models.product_category import ProductCategory
from app.db.models.product_image import ProductImage
from app.db.models.product_tag import ProductTag
from app.db.models.user import User
from app.repositories.inventory_transaction_repository import InventoryTransactionRepository
from app.repositories.product_category_repository import ProductCategoryRepository
from app.repositories.product_image_repository import ProductImageRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.product_tag_repository import ProductTagRepository
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
from app.services.platform_service import PlatformService
from app.services.storage_service import StorageService, build_storage_object_name


class ProductService:
    _SORT_COLUMNS = {
        "created_at": Product.created_at,
        "updated_at": Product.updated_at,
        "name": Product.name,
        "sku": Product.sku,
        "barcode": Product.barcode,
        "price": Product.price,
        "stock_qty": Product.stock_qty,
        "is_active": Product.is_active,
    }

    def __init__(self, session: Session, settings: Settings, storage_service: StorageService | None = None) -> None:
        self.session = session
        self.settings = settings
        self.storage = storage_service
        self.products = ProductRepository(session)
        self.categories = ProductCategoryRepository(session)
        self.tags = ProductTagRepository(session)
        self.images = ProductImageRepository(session)
        self.transactions = InventoryTransactionRepository(session)

    def list_products(
        self,
        company_id: UUID,
        *,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        category_id: UUID | None = None,
        tag_id: UUID | None = None,
        is_active: bool | None = None,
        include_deleted: bool = False,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
    ) -> ProductListResponse:
        sort_column = self._SORT_COLUMNS.get(sort_by, Product.created_at)
        sort_expression = sort_column.asc() if sort_dir.lower() == "asc" else sort_column.desc()

        statement = (
            select(Product)
            .where(Product.company_id == company_id)
            .options(selectinload(Product.tags), selectinload(Product.images), selectinload(Product.category_rel))
        )
        if not include_deleted:
            statement = statement.where(Product.deleted_at.is_(None))
        if is_active is not None:
            statement = statement.where(Product.is_active.is_(is_active))
        if category_id is not None:
            statement = statement.where(Product.category_id == category_id)
        if tag_id is not None:
            statement = statement.join(Product.tags).where(ProductTag.id == tag_id)
        if search and search.strip():
            term = f"%{search.strip()}%"
            statement = statement.where(
                or_(
                    Product.name.ilike(term),
                    Product.manufacturer.ilike(term),
                    Product.sku.ilike(term),
                    Product.barcode.ilike(term),
                    sa.cast(Product.aliases, sa.Text).ilike(term),
                    Product.category.ilike(term),
                    Product.search_vector.match(search.strip()),
                )
            )

        statement = statement.distinct().order_by(sort_expression)
        total = self._count_products(statement)
        items = list(self.session.scalars(statement.offset((page - 1) * page_size).limit(page_size)).unique().all())

        return ProductListResponse(
            items=[self._serialize_product(product) for product in items],
            page=page,
            page_size=page_size,
            total=total,
        )

    def get_product(self, company_id: UUID, product_id: UUID) -> ProductRead:
        product = self.products.get_with_relations(product_id, company_id)
        if product is None or product.deleted_at is not None:
            raise NotFoundError("Product not found")
        return self._serialize_product(product)

    def create_product(self, company_id: UUID, payload: ProductCreateRequest) -> ProductRead:
        platform = PlatformService(self.session)
        current_products = self.session.scalar(
            select(func.count(Product.id)).where(Product.company_id == company_id, Product.deleted_at.is_(None))
        ) or 0
        platform.ensure_limit(company_id, "maximum_products", 1, current=int(current_products))
        sku = payload.sku or self._generate_sku(company_id)
        self._validate_unique_product_fields(company_id, sku=sku, barcode=payload.barcode)
        category = self._resolve_category(company_id, payload.category_id, payload.category)

        product = Product(
            company_id=company_id,
            category_id=category.id if category else None,
            category=category.name if category else payload.category,
            name=payload.name,
            manufacturer=payload.manufacturer,
            sku=sku,
            barcode=payload.barcode,
            aliases=payload.aliases,
            unit=payload.unit,
            currency=payload.currency,
            price=payload.price,
            cost=payload.cost,
            tax_rate=payload.tax_rate,
            stock_qty=payload.stock_qty if payload.stock_qty is not None else Decimal("0"),
            low_stock_threshold=payload.low_stock_threshold,
            is_active=payload.is_active,
        )
        self.session.add(product)
        self.session.flush()
        self._sync_tags(product, company_id, payload.tag_ids)
        self.session.commit()
        self.session.refresh(product)
        platform.log_action(
            action="product_created",
            company_id=company_id,
            actor_user_id=None,
            resource_type="product",
            resource_id=str(product.id),
            description="Product created",
            metadata={"name": payload.name, "sku": sku},
        )
        return self.get_product(company_id, product.id)

    def _generate_sku(self, company_id: UUID) -> str:
        existing_skus = self.session.scalars(
            select(Product.sku).where(
                Product.company_id == company_id,
                Product.sku.like("SKU-%"),
            )
        ).all()
        max_num = 0
        for existing_sku in existing_skus:
            if existing_sku and existing_sku.startswith("SKU-"):
                try:
                    max_num = max(max_num, int(existing_sku[4:]))
                except ValueError:
                    continue
        return f"SKU-{max_num + 1:06d}"

    def update_product(self, company_id: UUID, product_id: UUID, payload: ProductUpdateRequest) -> ProductRead:
        product = self._get_product_or_404(company_id, product_id)
        self._validate_unique_product_fields(
            company_id,
            sku=payload.sku if payload.sku != product.sku else None,
            barcode=payload.barcode if payload.barcode != product.barcode else None,
        )

        updates = payload.model_dump(exclude_unset=True)
        for field, value in updates.items():
            if field in {"category_id", "category", "tag_ids"}:
                continue
            if field == "aliases":
                setattr(product, field, list(value or []))
                continue
            setattr(product, field, value)

        if "category_id" in updates or "category" in updates:
            category = self._resolve_category(company_id, updates.get("category_id"), updates.get("category"))
            product.category_id = category.id if category else None
            product.category = category.name if category else updates.get("category")

        if "tag_ids" in updates:
            self._sync_tags(product, company_id, updates.get("tag_ids"))

        self.session.commit()
        self.session.refresh(product)
        PlatformService(self.session).log_action(
            action="product_updated",
            company_id=company_id,
            actor_user_id=None,
            resource_type="product",
            resource_id=str(product.id),
            description="Product updated",
            metadata=updates,
        )
        return self.get_product(company_id, product.id)

    def delete_product(self, company_id: UUID, product_id: UUID) -> None:
        product = self._get_product_or_404(company_id, product_id)
        product.deleted_at = sa.func.now()
        product.is_active = False
        self.session.commit()
        PlatformService(self.session).log_action(
            action="product_deleted",
            company_id=company_id,
            actor_user_id=None,
            resource_type="product",
            resource_id=str(product.id),
            description="Product soft deleted",
        )

    def restore_product(self, company_id: UUID, product_id: UUID) -> ProductRestoreResponse:
        product = self._get_product_or_404(company_id, product_id, include_deleted=True)
        product.deleted_at = None
        product.is_active = True
        self.session.commit()
        PlatformService(self.session).log_action(
            action="product_restored",
            company_id=company_id,
            actor_user_id=None,
            resource_type="product",
            resource_id=str(product.id),
            description="Product restored",
        )
        return ProductRestoreResponse(detail="Product restored")

    def create_category(self, company_id: UUID, payload: ProductCategoryCreateRequest) -> ProductCategoryRead:
        if self.categories.get_by_slug(company_id, payload.slug):
            raise ConflictError("Category slug already exists")
        if payload.parent_id is not None:
            self._get_category_or_404(company_id, payload.parent_id)

        category = ProductCategory(
            company_id=company_id,
            name=payload.name,
            slug=payload.slug,
            description=payload.description,
            parent_id=payload.parent_id,
            sort_order=payload.sort_order,
        )
        self.session.add(category)
        self.session.commit()
        self.session.refresh(category)
        return self._serialize_category(category, product_count=0)

    def list_categories(self, company_id: UUID) -> ProductCategoryListResponse:
        categories = self.session.scalars(
            select(ProductCategory)
            .where(ProductCategory.company_id == company_id, ProductCategory.deleted_at.is_(None))
            .order_by(ProductCategory.sort_order.asc(), ProductCategory.name.asc())
        ).all()

        product_counts = dict(
            self.session.execute(
                select(Product.category_id, func.count(Product.id))
                .where(Product.company_id == company_id, Product.deleted_at.is_(None))
                .group_by(Product.category_id)
            ).all()
        )

        children_by_parent: dict[UUID | None, list[ProductCategory]] = {}
        for category in categories:
            children_by_parent.setdefault(category.parent_id, []).append(category)

        def build_tree(category: ProductCategory) -> ProductCategoryRead:
            return self._serialize_category(
                category,
                product_count=int(product_counts.get(category.id, 0)),
                children=[build_tree(child) for child in children_by_parent.get(category.id, [])],
            )

        return ProductCategoryListResponse(
            items=[build_tree(category) for category in children_by_parent.get(None, [])]
        )

    def update_category(
        self,
        company_id: UUID,
        category_id: UUID,
        payload: ProductCategoryUpdateRequest,
    ) -> ProductCategoryRead:
        category = self._get_category_or_404(company_id, category_id)
        updates = payload.model_dump(exclude_unset=True)
        if "slug" in updates and updates["slug"] != category.slug and self.categories.get_by_slug(company_id, updates["slug"]):
            raise ConflictError("Category slug already exists")
        if "parent_id" in updates and updates["parent_id"] is not None:
            if updates["parent_id"] == category.id:
                raise ValidationAppError("Category cannot be its own parent")
            self._get_category_or_404(company_id, updates["parent_id"])

        for field, value in updates.items():
            setattr(category, field, value)
        self.session.commit()
        self.session.refresh(category)
        product_count = self._count_products_for_category(company_id, category.id)
        return self._serialize_category(category, product_count=product_count)

    def delete_category(self, company_id: UUID, category_id: UUID) -> None:
        category = self._get_category_or_404(company_id, category_id)
        category.deleted_at = sa.func.now()
        category.is_active = False
        self.session.commit()

    def list_tags(self, company_id: UUID) -> ProductTagListResponse:
        tags = self.session.scalars(
            select(ProductTag)
            .where(ProductTag.company_id == company_id, ProductTag.deleted_at.is_(None))
            .order_by(ProductTag.name.asc())
        ).all()
        return ProductTagListResponse(items=[self._serialize_tag(tag) for tag in tags])

    def create_tag(self, company_id: UUID, payload: ProductTagCreateRequest) -> ProductTagRead:
        if self.tags.get_by_slug(company_id, payload.slug):
            raise ConflictError("Tag slug already exists")
        tag = ProductTag(company_id=company_id, name=payload.name, slug=payload.slug, color=payload.color)
        self.session.add(tag)
        self.session.commit()
        self.session.refresh(tag)
        return self._serialize_tag(tag)

    def update_tag(self, company_id: UUID, tag_id: UUID, payload: ProductTagUpdateRequest) -> ProductTagRead:
        tag = self._get_tag_or_404(company_id, tag_id)
        updates = payload.model_dump(exclude_unset=True)
        if "slug" in updates and updates["slug"] != tag.slug and self.tags.get_by_slug(company_id, updates["slug"]):
            raise ConflictError("Tag slug already exists")

        for field, value in updates.items():
            setattr(tag, field, value)
        self.session.commit()
        self.session.refresh(tag)
        return self._serialize_tag(tag)

    def delete_tag(self, company_id: UUID, tag_id: UUID) -> None:
        tag = self._get_tag_or_404(company_id, tag_id)
        tag.deleted_at = sa.func.now()
        tag.is_active = False
        self.session.commit()

    def create_inventory_transaction(
        self,
        company_id: UUID,
        product_id: UUID,
        actor: User,
        payload: ProductInventoryTransactionCreateRequest,
    ) -> ProductInventoryResponse:
        product = self._get_product_or_404(company_id, product_id)
        current_stock = Decimal(str(product.stock_qty or 0))
        quantity = Decimal(str(payload.quantity))

        if payload.transaction_type == "stock_in":
            new_stock = current_stock + quantity
        elif payload.transaction_type == "stock_out":
            new_stock = current_stock - quantity
        elif payload.transaction_type == "adjustment":
            new_stock = quantity
        else:
            raise ValidationAppError("Invalid inventory transaction type")

        if new_stock < 0:
            raise ValidationAppError("Inventory cannot go below zero")

        transaction = InventoryTransaction(
            company_id=company_id,
            product_id=product_id,
            transaction_type=payload.transaction_type,
            quantity=quantity,
            quantity_before=current_stock,
            quantity_after=new_stock,
            unit_cost=payload.unit_cost,
            note=payload.note,
            created_by_id=actor.id,
        )
        product.stock_qty = new_stock
        self.session.add(transaction)
        self.session.commit()
        return self.get_inventory(company_id, product_id)

    def list_inventory_history(self, company_id: UUID, product_id: UUID) -> list[ProductInventoryTransactionRead]:
        transactions = self.transactions.list_for_product(company_id, product_id)
        return [ProductInventoryTransactionRead.model_validate(transaction) for transaction in transactions]

    def get_inventory(self, company_id: UUID, product_id: UUID) -> ProductInventoryResponse:
        product = self._get_product_or_404(company_id, product_id, include_deleted=True)
        stock_qty = Decimal(str(product.stock_qty or 0))
        cost = Decimal(str(product.cost if product.cost is not None else product.price))
        stock_value = stock_qty * cost
        low_stock = bool(product.low_stock_threshold is not None and stock_qty <= product.low_stock_threshold)
        return ProductInventoryResponse(current_stock=stock_qty, stock_value=stock_value, low_stock=low_stock)

    def upload_product_image(
        self,
        company_id: UUID,
        product_id: UUID,
        *,
        content: bytes,
        content_type: str,
        filename: str | None = None,
        alt_text: str | None = None,
        is_primary: bool = False,
    ) -> ProductImageRead:
        if self.storage is None:
            raise ConfigurationError("Product image storage is not configured")

        product = self._get_product_or_404(company_id, product_id)
        suffix = Path(filename or "").suffix.lstrip(".") or content_type.split("/")[-1].lower() or "bin"
        object_path = build_storage_object_name(
            "products",
            str(company_id),
            str(product_id),
            "images",
            uuid4().hex,
            suffix=suffix,
        )
        upload_result = self.storage.upload_public_file(
            bucket=self.settings.supabase_storage_bucket,
            object_path=object_path,
            content=content,
            content_type=content_type,
        )

        if is_primary:
            self.session.query(ProductImage).filter(
                ProductImage.company_id == company_id,
                ProductImage.product_id == product_id,
            ).update({ProductImage.is_primary: False}, synchronize_session=False)

        next_sort_order = (
            self.session.scalar(
                select(func.coalesce(func.max(ProductImage.sort_order), -1) + 1).where(
                    ProductImage.company_id == company_id,
                    ProductImage.product_id == product_id,
                )
            )
            or 0
        )
        image = ProductImage(
            company_id=company_id,
            product_id=product.id,
            url=upload_result.public_url,
            storage_path=upload_result.object_path,
            alt_text=alt_text,
            sort_order=int(next_sort_order),
            is_primary=is_primary,
        )
        self.session.add(image)
        self.session.commit()
        self.session.refresh(image)
        return self._serialize_image(image)

    def delete_product_image(self, company_id: UUID, product_id: UUID, image_id: UUID) -> None:
        image = self.session.scalar(
            select(ProductImage).where(
                ProductImage.company_id == company_id,
                ProductImage.product_id == product_id,
                ProductImage.id == image_id,
            )
        )
        if image is None:
            raise NotFoundError("Image not found")
        self.session.delete(image)
        self.session.commit()

    def _validate_unique_product_fields(
        self,
        company_id: UUID,
        *,
        sku: str | None,
        barcode: str | None,
    ) -> None:
        if sku and self.products.get_by_sku(company_id, sku):
            raise ConflictError("SKU already exists")
        if barcode and self.products.get_by_barcode(company_id, barcode):
            raise ConflictError("Barcode already exists")

    def _sync_tags(self, product: Product, company_id: UUID, tag_ids: list[UUID] | None) -> None:
        product.tags.clear()
        if not tag_ids:
            return

        tags = list(
            self.session.scalars(
                select(ProductTag).where(
                    ProductTag.company_id == company_id,
                    ProductTag.id.in_(tag_ids),
                    ProductTag.deleted_at.is_(None),
                )
            ).all()
        )
        if len(tags) != len(set(tag_ids)):
            raise NotFoundError("One or more tags were not found")
        product.tags.extend(tags)

    def _resolve_category(
        self,
        company_id: UUID,
        category_id: UUID | None,
        category_name: str | None,
    ) -> ProductCategory | None:
        if category_id is not None:
            return self._get_category_or_404(company_id, category_id)
        if category_name:
            category = self.session.scalar(
                select(ProductCategory).where(
                    ProductCategory.company_id == company_id,
                    ProductCategory.name == category_name,
                    ProductCategory.deleted_at.is_(None),
                )
            )
            return category
        return None

    def _get_product_or_404(self, company_id: UUID, product_id: UUID, include_deleted: bool = False) -> Product:
        statement = select(Product).where(Product.company_id == company_id, Product.id == product_id)
        if not include_deleted:
            statement = statement.where(Product.deleted_at.is_(None))
        product = self.session.scalar(statement)
        if product is None:
            raise NotFoundError("Product not found")
        return product

    def _get_category_or_404(self, company_id: UUID, category_id: UUID) -> ProductCategory:
        category = self.session.scalar(
            select(ProductCategory).where(
                ProductCategory.company_id == company_id,
                ProductCategory.id == category_id,
                ProductCategory.deleted_at.is_(None),
            )
        )
        if category is None:
            raise NotFoundError("Category not found")
        return category

    def _get_tag_or_404(self, company_id: UUID, tag_id: UUID) -> ProductTag:
        tag = self.session.scalar(
            select(ProductTag).where(
                ProductTag.company_id == company_id,
                ProductTag.id == tag_id,
                ProductTag.deleted_at.is_(None),
            )
        )
        if tag is None:
            raise NotFoundError("Tag not found")
        return tag

    def _count_products(self, statement) -> int:
        return int(self.session.scalar(select(func.count()).select_from(statement.subquery())) or 0)

    def _count_products_for_category(self, company_id: UUID, category_id: UUID) -> int:
        return int(
            self.session.scalar(
                select(func.count(Product.id)).where(
                    Product.company_id == company_id,
                    Product.category_id == category_id,
                    Product.deleted_at.is_(None),
                )
            )
            or 0
        )

    def _serialize_product(self, product: Product) -> ProductRead:
        stock_qty = Decimal(str(product.stock_qty or 0))
        cost = Decimal(str(product.cost if product.cost is not None else product.price))
        stock_value = stock_qty * cost
        low_stock = bool(product.low_stock_threshold is not None and stock_qty <= product.low_stock_threshold)
        return ProductRead(
            id=product.id,
            company_id=product.company_id,
            category_id=product.category_id,
            name=product.name,
            manufacturer=product.manufacturer,
            sku=product.sku,
            barcode=product.barcode,
            aliases=list(product.aliases or []),
            category=product.category,
            unit=product.unit,
            currency=product.currency,
            price=product.price,
            cost=product.cost,
            tax_rate=product.tax_rate,
            stock_qty=product.stock_qty,
            low_stock_threshold=product.low_stock_threshold,
            is_active=product.is_active,
            created_at=product.created_at,
            updated_at=product.updated_at,
            deleted_at=product.deleted_at,
            stock_value=stock_value,
            low_stock=low_stock,
            tags=[self._serialize_tag(tag) for tag in product.tags],
            images=[self._serialize_image(image) for image in product.images],
            category_rel=self._serialize_category(product.category_rel) if product.category_rel else None,
        )

    def _serialize_category(
        self,
        category: ProductCategory,
        *,
        product_count: int | None = None,
        children: list[ProductCategoryRead] | None = None,
    ) -> ProductCategoryRead:
        if product_count is None:
            product_count = self._count_products_for_category(category.company_id, category.id)
        return ProductCategoryRead(
            id=category.id,
            name=category.name,
            slug=category.slug,
            description=category.description,
            parent_id=category.parent_id,
            sort_order=category.sort_order,
            is_active=category.is_active,
            created_at=category.created_at,
            updated_at=category.updated_at,
            product_count=product_count,
            children=children or [],
        )

    def _serialize_tag(self, tag: ProductTag) -> ProductTagRead:
        return ProductTagRead.model_validate(tag)

    def _serialize_image(self, image: ProductImage) -> ProductImageRead:
        return ProductImageRead.model_validate(image)
