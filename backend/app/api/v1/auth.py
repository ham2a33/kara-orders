from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.exceptions import UnauthorizedError
from app.dependencies.auth import get_current_user
from app.dependencies.deps import get_app_settings, get_db
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    LogoutResponse,
    MeResponse,
    RefreshRequest,
    RegisterRequest,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["authentication"])


def _set_refresh_cookie(response: Response, refresh_token: str, settings: Settings) -> None:
    response.set_cookie(
        key=settings.auth_refresh_cookie_name,
        value=refresh_token,
        httponly=True,
        secure=settings.auth_refresh_cookie_secure,
        samesite=settings.auth_refresh_cookie_samesite,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path=settings.auth_refresh_cookie_path,
    )


def _delete_refresh_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        key=settings.auth_refresh_cookie_name,
        path=settings.auth_refresh_cookie_path,
    )


@router.post("/register", response_model=AuthResponse, status_code=201)
def register(
    payload: RegisterRequest,
    response: Response,
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> AuthResponse:
    service = AuthService(session=session, settings=settings)
    auth_response, refresh_token = service.register(payload)
    _set_refresh_cookie(response, refresh_token, settings)
    return auth_response


@router.post("/login", response_model=AuthResponse)
def login(
    payload: LoginRequest,
    response: Response,
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> AuthResponse:
    service = AuthService(session=session, settings=settings)
    auth_response, refresh_token = service.login(payload)
    _set_refresh_cookie(response, refresh_token, settings)
    return auth_response


@router.post("/refresh", response_model=AuthResponse)
def refresh(
    request: Request,
    response: Response,
    payload: RefreshRequest | None = None,
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> AuthResponse:
    refresh_token = (
        payload.refresh_token
        if payload and payload.refresh_token
        else request.cookies.get(settings.auth_refresh_cookie_name)
    )
    if not refresh_token:
        raise UnauthorizedError("Missing refresh token")

    service = AuthService(session=session, settings=settings)
    auth_response, new_refresh_token = service.refresh(refresh_token)
    _set_refresh_cookie(response, new_refresh_token, settings)
    return auth_response


@router.post("/logout", response_model=LogoutResponse)
def logout(response: Response, settings: Settings = Depends(get_app_settings)) -> LogoutResponse:
    _delete_refresh_cookie(response, settings)
    return LogoutResponse(detail="Logged out")


@router.get("/me", response_model=MeResponse)
def me(
    current_user=Depends(get_current_user),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> MeResponse:
    service = AuthService(session=session, settings=settings)
    return service.get_profile(current_user)
