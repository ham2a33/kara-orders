from __future__ import annotations

import re
from pathlib import Path

from app.core.exceptions import ValidationAppError


def normalize_text(value: str) -> str:
    cleaned = value.strip().lower()
    return re.sub(r"\s+", " ", cleaned)


def ensure_non_empty(value: str, field_name: str = "value") -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name} cannot be empty")
    return cleaned


def sanitize_filename(filename: str) -> str:
    stem = Path(filename).stem.strip().lower()
    suffix = Path(filename).suffix.lower().lstrip(".")
    cleaned_stem = re.sub(r"[^a-z0-9._-]+", "-", stem).strip("-._") or "upload"
    cleaned_suffix = re.sub(r"[^a-z0-9]+", "", suffix)
    return f"{cleaned_stem}.{cleaned_suffix}" if cleaned_suffix else cleaned_stem


def validate_upload(
    *,
    content: bytes,
    filename: str,
    content_type: str,
    max_upload_size_mb: int,
    allowed_file_types: list[str],
    allowed_mime_types: set[str] | None = None,
) -> None:
    if not content:
        raise ValidationAppError("Uploaded file is empty")

    max_bytes = max_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise ValidationAppError("Uploaded file exceeds the maximum size")

    suffix = Path(filename).suffix.lower().lstrip(".")
    if allowed_file_types and suffix and suffix not in {item.lower() for item in allowed_file_types}:
        raise ValidationAppError("Uploaded file type is not allowed")

    if allowed_mime_types is not None:
        normalized_content_type = content_type.lower().split(";", 1)[0].strip()
        if normalized_content_type not in allowed_mime_types:
            raise ValidationAppError("Uploaded file MIME type is not allowed")
