from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Kara Invoice AI"
    app_version: str = "0.1.0"
    environment: Literal["local", "development", "staging", "production"] = "development"

    database_url: str = Field(
        default="postgresql+psycopg://kara:kara_password@db:5432/kara_orders",
        validation_alias="DATABASE_URL",
    )
    secret_key: str = Field(default="change-me", validation_alias="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=15, validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=30, validation_alias="REFRESH_TOKEN_EXPIRE_DAYS")
    password_min_length: int = Field(default=12, validation_alias="PASSWORD_MIN_LENGTH")
    auth_refresh_cookie_name: str = Field(
        default="kara_orders_refresh_token",
        validation_alias="AUTH_REFRESH_COOKIE_NAME",
    )
    auth_refresh_cookie_path: str = Field(default="/api/v1/auth", validation_alias="AUTH_REFRESH_COOKIE_PATH")
    auth_refresh_cookie_secure: bool = Field(
        default=False,
        validation_alias="AUTH_REFRESH_COOKIE_SECURE",
    )
    auth_refresh_cookie_samesite: str = Field(
        default="lax",
        validation_alias="AUTH_REFRESH_COOKIE_SAMESITE",
    )

    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:3001"],
        validation_alias="CORS_ORIGINS",
    )
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    rate_limit_enabled: bool = Field(default=False, validation_alias="RATE_LIMIT_ENABLED")
    rate_limit_window_seconds: int = Field(default=60, validation_alias="RATE_LIMIT_WINDOW_SECONDS")
    rate_limit_max_requests: int = Field(default=100, validation_alias="RATE_LIMIT_MAX_REQUESTS")

    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    openai_recognition_model: str = Field(default="gpt-4.1-mini", validation_alias="OPENAI_RECOGNITION_MODEL")
    openai_transcription_model: str = Field(
        default="gpt-4o-mini-transcribe",
        validation_alias="OPENAI_TRANSCRIPTION_MODEL",
    )
    ai_request_timeout_seconds: int = Field(default=90, validation_alias="AI_REQUEST_TIMEOUT_SECONDS")
    ai_retry_attempts: int = Field(default=2, validation_alias="AI_RETRY_ATTEMPTS")
    ai_low_confidence_threshold: float = Field(default=0.75, validation_alias="AI_LOW_CONFIDENCE_THRESHOLD")
    supabase_url: str | None = Field(default=None, validation_alias="SUPABASE_URL")
    supabase_service_role_key: str | None = Field(
        default=None, validation_alias="SUPABASE_SERVICE_ROLE_KEY"
    )
    supabase_storage_bucket: str = Field(default="kara-orders", validation_alias="SUPABASE_STORAGE_BUCKET")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> list[str]:
        if value is None:
            return ["http://localhost:3000", "http://localhost:3001"]
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        if isinstance(value, list):
            return [str(origin).strip() for origin in value if str(origin).strip()]
        raise TypeError("cors_origins must be a string or a list of strings")

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.environment == "production":
            if self.secret_key in {"change-me", "super-secret", "secret"} or len(self.secret_key) < 32:
                raise ValueError("SECRET_KEY must be set to a strong production secret")
            if any(origin == "*" for origin in self.cors_origins):
                raise ValueError("CORS origins cannot contain wildcards in production")
            self.auth_refresh_cookie_secure = True
            if self.auth_refresh_cookie_samesite.lower() == "lax":
                self.auth_refresh_cookie_samesite = "strict"

        normalized_samesite = self.auth_refresh_cookie_samesite.lower()
        if normalized_samesite not in {"lax", "strict", "none"}:
            raise ValueError("AUTH_REFRESH_COOKIE_SAMESITE must be lax, strict, or none")
        self.auth_refresh_cookie_samesite = normalized_samesite
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
