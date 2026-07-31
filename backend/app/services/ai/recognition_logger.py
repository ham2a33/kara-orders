from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

LOGGER = logging.getLogger("kara_orders.ai_recognition")

_LOG_RECORD_RESERVED = frozenset(
    {
        "name",
        "msg",
        "message",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
        "exc_info",
        "exc_text",
        "stack_info",
        "stage",
    }
)


def log_recognition_stage(stage: str, *, exc: BaseException | None = None, **context: Any) -> None:
    payload: dict[str, Any] = {"stage": stage}
    for key, value in context.items():
        safe_key = f"ctx_{key}" if key in _LOG_RECORD_RESERVED else key
        payload[safe_key] = _json_safe(value)
    if exc is not None:
        LOGGER.error(stage, extra=payload, exc_info=exc)
        return
    LOGGER.info(stage, extra=payload)


def _json_safe(value: Any) -> Any:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)
