from __future__ import annotations

import re

_ORDER_LINE_END = re.compile(
    r"\d+(?:[.,]\d+)?\s*(?:"
    r"шт|штук|м(?![мМa-zA-Z])|метр|метров|кг|л|литр|"
    r"м²|м2|м³|m3|m2|m\^2|m\^3|"
    r"pcs|pc|piece|pieces"
    r")\.?\s*",
    re.IGNORECASE | re.UNICODE,
)


def postprocess_ocr_order_text(text: str) -> str:
    """Normalize OCR output and restore one order line per item where possible."""
    if not text or not text.strip():
        return ""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"[ \t]+", " ", normalized)
    lines: list[str] = []
    for physical_line in normalized.split("\n"):
        stripped = physical_line.strip()
        if not stripped:
            continue
        lines.extend(_split_merged_order_line(stripped))
    if not lines:
        return normalized.strip()
    return "\n".join(lines)


def recover_order_lines_from_ocr(text: str) -> list[str]:
    stripped = text.strip() if text else ""
    if not stripped:
        return []

    processed = postprocess_ocr_order_text(text)
    source = processed.strip() if processed.strip() else stripped
    lines = [line.strip() for line in source.split("\n") if line.strip()]
    if not lines:
        lines = [source]

    if len(lines) > 1:
        return lines

    single = lines[0]
    split = _split_merged_order_line(single)
    return split if len(split) > 1 else [single]


def _split_merged_order_line(line: str) -> list[str]:
    matches = list(_ORDER_LINE_END.finditer(line))
    if len(matches) <= 1:
        return [line.strip()] if line.strip() else []

    segments: list[str] = []
    start = 0
    for match in matches:
        end = match.end()
        segment = line[start:end].strip()
        if segment:
            segments.append(segment)
        start = end
    remainder = line[start:].strip()
    if remainder:
        segments.append(remainder)
    return segments
