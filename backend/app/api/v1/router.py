from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.analytics import router as analytics_router
from app.api.v1.ai import router as ai_router
from app.api.v1.auth import router as auth_router
from app.api.v1.companies import router as companies_router
from app.api.v1.platform import router as platform_router
from app.api.v1.orders import router as orders_router
from app.api.v1.products import router as products_router

router = APIRouter(prefix="/api/v1", tags=["system"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "kara-orders-backend",
        "version": "0.1.0",
    }


router.include_router(auth_router)
router.include_router(companies_router)
router.include_router(products_router)
router.include_router(orders_router)
router.include_router(analytics_router)
router.include_router(platform_router)
router.include_router(ai_router)
