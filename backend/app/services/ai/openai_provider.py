from __future__ import annotations

import base64
import json
import mimetypes
from dataclasses import dataclass
from typing import Any
from urllib import error, request

from app.core.config import Settings
from app.core.exceptions import ConfigurationError, UpstreamServiceError


@dataclass(frozen=True)
class AIUsage:
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None


@dataclass(frozen=True)
class AIProviderResult:
    text: str
    raw_response: dict[str, Any]
    model: str
    usage: AIUsage


class OpenAIProvider:
    def __init__(self, settings: Settings) -> None:
        if not settings.openai_api_key:
            raise ConfigurationError("AI is not configured. Please add OPENAI_API_KEY.")
        self.settings = settings
        self.base_url = "https://api.openai.com/v1"

    def extract_from_text(
        self,
        *,
        text: str,
        instruction: str,
        context: str,
        schema: dict[str, Any],
    ) -> AIProviderResult:
        body = {
            "model": self.settings.openai_recognition_model,
            "input": [
                {
                    "role": "developer",
                    "content": [{"type": "input_text", "text": instruction}],
                },
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": f"{context}\n\n{text}"}],
                },
            ],
            "text": self._json_schema_text_config(schema),
        }
        payload = self._post_json("/responses", body)
        return self._build_result(payload, self.settings.openai_recognition_model)

    def extract_from_image(
        self,
        *,
        file_bytes: bytes,
        mime_type: str,
        filename: str,
        instruction: str,
        context: str,
        schema: dict[str, Any],
    ) -> AIProviderResult:
        encoded = base64.b64encode(file_bytes).decode("utf-8")
        body = {
            "model": self.settings.openai_recognition_model,
            "input": [
                {
                    "role": "developer",
                    "content": [{"type": "input_text", "text": instruction}],
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": context},
                        {
                            "type": "input_image",
                            "image_url": f"data:{mime_type or 'image/jpeg'};base64,{encoded}",
                            "detail": "high",
                        },
                    ],
                },
            ],
            "text": self._json_schema_text_config(schema),
        }
        payload = self._post_json("/responses", body)
        return self._build_result(payload, self.settings.openai_recognition_model)

    def extract_from_file(
        self,
        *,
        file_bytes: bytes,
        filename: str,
        instruction: str,
        context: str,
        schema: dict[str, Any],
    ) -> AIProviderResult:
        encoded = base64.b64encode(file_bytes).decode("utf-8")
        mime_type = self._guess_mime_type(filename)
        file_input: dict[str, Any] = {
            "type": "input_file",
            "file_data": f"data:{mime_type};base64,{encoded}",
            "filename": filename,
        }
        if mime_type == "application/pdf":
            file_input["detail"] = "high"
        body = {
            "model": self.settings.openai_recognition_model,
            "input": [
                {
                    "role": "developer",
                    "content": [{"type": "input_text", "text": instruction}],
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": context},
                        file_input,
                    ],
                },
            ],
            "text": self._json_schema_text_config(schema),
        }
        payload = self._post_json("/responses", body)
        return self._build_result(payload, self.settings.openai_recognition_model)

    def transcribe_audio(self, *, file_bytes: bytes, filename: str, mime_type: str | None = None) -> AIProviderResult:
        boundary = "----kara-orders-boundary"
        content_type = f"multipart/form-data; boundary={boundary}"
        form_data = self._multipart_body(
            boundary,
            fields={"model": self.settings.openai_transcription_model},
            files=[("file", filename, mime_type or self._guess_mime_type(filename), file_bytes)],
        )
        payload = self._post_bytes("/audio/transcriptions", form_data, content_type)
        text = str(payload.get("text") or "").strip()
        if not text:
            raise UpstreamServiceError("OpenAI transcription returned no text")
        return AIProviderResult(
            text=text,
            raw_response=payload,
            model=self.settings.openai_transcription_model,
            usage=self._parse_usage(payload.get("usage")),
        )

    def _post_json(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        data = json.dumps(body).encode("utf-8")
        payload = self._post_bytes(path, data, "application/json")
        if not isinstance(payload, dict):
            raise UpstreamServiceError("OpenAI returned an invalid response")
        return payload

    def _post_bytes(self, path: str, body: bytes, content_type: str) -> dict[str, Any]:
        req = request.Request(
            f"{self.base_url}{path}",
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.settings.openai_api_key}",
                "Content-Type": content_type,
            },
        )
        try:
            with request.urlopen(req, timeout=self.settings.ai_request_timeout_seconds) as response:
                raw = response.read()
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise UpstreamServiceError(self._extract_error_message(detail)) from exc
        except error.URLError as exc:
            raise UpstreamServiceError(f"OpenAI request failed: {exc.reason}") from exc

        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise UpstreamServiceError("OpenAI returned invalid JSON") from exc

    def _build_result(self, payload: dict[str, Any], model: str) -> AIProviderResult:
        return AIProviderResult(
            text=self._extract_output_text(payload),
            raw_response=payload,
            model=model,
            usage=self._parse_usage(payload.get("usage")),
        )

    def _extract_output_text(self, payload: dict[str, Any]) -> str:
        # Responses API exposes aggregated assistant text via output_text when available.
        output_text = payload.get("output_text")
        if isinstance(output_text, str) and output_text.strip():
            return output_text.strip()

        chunks: list[str] = []
        for item in payload.get("output", []):
            if not isinstance(item, dict) or item.get("type") != "message":
                continue
            for content in item.get("content", []):
                if not isinstance(content, dict) or content.get("type") != "output_text":
                    continue
                text = content.get("text")
                if isinstance(text, str) and text.strip():
                    chunks.append(text)
        if chunks:
            return "".join(chunks).strip()
        raise UpstreamServiceError("OpenAI response did not contain text output")

    def _parse_usage(self, usage_payload: Any) -> AIUsage:
        if not isinstance(usage_payload, dict):
            return AIUsage()
        return AIUsage(
            input_tokens=self._to_int(usage_payload.get("input_tokens")),
            output_tokens=self._to_int(usage_payload.get("output_tokens")),
            total_tokens=self._to_int(usage_payload.get("total_tokens")),
        )

    def _json_schema_text_config(self, schema: dict[str, Any]) -> dict[str, Any]:
        return {
            "format": {
                "type": "json_schema",
                "name": "kara_order_extraction",
                "strict": True,
                "schema": schema,
            }
        }

    def _multipart_body(
        self,
        boundary: str,
        *,
        fields: dict[str, str],
        files: list[tuple[str, str, str, bytes]],
    ) -> bytes:
        lines: list[bytes] = []
        for name, value in fields.items():
            lines.extend(
                [
                    f"--{boundary}".encode(),
                    f'Content-Disposition: form-data; name="{name}"'.encode(),
                    b"",
                    value.encode(),
                ]
            )
        for name, filename, mime_type, content in files:
            lines.extend(
                [
                    f"--{boundary}".encode(),
                    f'Content-Disposition: form-data; name="{name}"; filename="{filename}"'.encode(),
                    f"Content-Type: {mime_type}".encode(),
                    b"",
                    content,
                ]
            )
        lines.append(f"--{boundary}--".encode())
        lines.append(b"")
        return b"\r\n".join(lines)

    def _guess_mime_type(self, filename: str) -> str:
        return mimetypes.guess_type(filename)[0] or "application/octet-stream"

    def _extract_error_message(self, raw: str) -> str:
        try:
            payload = json.loads(raw)
            error_payload = payload.get("error")
            if isinstance(error_payload, dict):
                message = error_payload.get("message")
                if isinstance(message, str) and message.strip():
                    return message.strip()
        except json.JSONDecodeError:
            pass
        return raw.strip() or "OpenAI request failed"

    def _to_int(self, value: Any) -> int | None:
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
