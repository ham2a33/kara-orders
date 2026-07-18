from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib import parse, request

from app.core.config import Settings
from app.core.exceptions import ConfigurationError
from app.utils.validators import sanitize_filename


@dataclass(frozen=True)
class UploadResult:
    public_url: str
    object_path: str


class StorageService:
    def upload_public_file(
        self,
        *,
        bucket: str,
        object_path: str,
        content: bytes,
        content_type: str,
    ) -> UploadResult:
        raise NotImplementedError


class SupabaseStorageService(StorageService):
    def __init__(self, settings: Settings) -> None:
        if not settings.supabase_url or not settings.supabase_service_role_key:
            raise ConfigurationError("Supabase storage is not configured")
        self.settings = settings
        self.base_url = settings.supabase_url.rstrip("/")

    def upload_public_file(
        self,
        *,
        bucket: str,
        object_path: str,
        content: bytes,
        content_type: str,
    ) -> UploadResult:
        encoded_path = "/".join(parse.quote(part) for part in object_path.split("/"))
        upload_url = f"{self.base_url}/storage/v1/object/{bucket}/{encoded_path}"
        req = request.Request(
            upload_url,
            data=content,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.settings.supabase_service_role_key}",
                "apikey": self.settings.supabase_service_role_key,
                "Content-Type": content_type,
                "x-upsert": "true",
            },
        )
        with request.urlopen(req, timeout=30) as response:
            response.read()

        public_url = f"{self.base_url}/storage/v1/object/public/{bucket}/{encoded_path}"
        return UploadResult(public_url=public_url, object_path=object_path)


def build_storage_object_name(*parts: str, suffix: str | None = None) -> str:
    filename = "-".join(part.strip() for part in parts if part.strip())
    if suffix:
        filename = f"{filename}.{suffix}"
    return str(Path(sanitize_filename(filename)))
