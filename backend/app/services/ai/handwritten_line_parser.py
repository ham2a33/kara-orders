from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Literal

from app.services.ai.ocr_postprocess import recover_order_lines_from_ocr
from app.services.product_size_parser import clean_product_name, extract_size_from_name, normalize_size_text
from app.services.size_equivalence import sanitize_parsed_line_size

ParseMode = Literal["strict", "fallback", "raw"]

_UNIT_PATTERN = re.compile(
    r"\s+(?P<unit>"
    r"шт|штук|штуки|"
    r"м|метр|метров|метра|"
    r"кг|л|литр|литров|"
    r"м²|м2|м³|m3|m2|m\^2|m\^3|"
    r"pcs|pc|piece|pieces"
    r")\.?\s*$",
    re.IGNORECASE,
)
_QTY_PATTERN = re.compile(r"\s+(?P<qty>\d+(?:[.,]\d+)?)\s*$")
_TRAILING_NUMBER = re.compile(r"(?P<qty>\d+(?:[.,]\d+)?)\s*$")
# Trailing quantity glued to unit (23м, 15шт) — always order qty, never product size.
_COMPACT_QTY_UNIT = re.compile(
    r"(?P<qty>\d+(?:[.,]\d+)?)"
    r"(?P<unit>"
    r"шт|штук|штуки|"
    r"кг|л|литр|литров|"
    r"м²|м2|м³|m3|m2|m\^2|m\^3|"
    r"м(?![мМa-zA-Z])|"
    r"pcs|pc|piece|pieces"
    r")\.?\s*$",
    re.IGNORECASE,
)

_ORDER_UNITS = frozenset({"шт", "м", "кг", "л", "м²", "м³"})
_UNIT_ALIASES = {
    "pcs": "шт",
    "pc": "шт",
    "piece": "шт",
    "pieces": "шт",
    "шт.": "шт",
    "m": "м",
    "meter": "м",
    "meters": "м",
    "metre": "м",
    "kg": "кг",
    "l": "л",
    "liter": "л",
    "litre": "л",
    "m2": "м²",
    "m3": "м³",
    "m^2": "м²",
    "m^3": "м³",
    "кв.м": "м²",
    "куб.м": "м³",
}


@dataclass(frozen=True, slots=True)
class HandwrittenLineItem:
    product_name: str
    size: str | None
    quantity: Decimal
    unit: str
    source_line: str
    confidence: Decimal = Decimal("1")


@dataclass(frozen=True, slots=True)
class ParsedOrderLine:
    item: HandwrittenLineItem
    parse_mode: ParseMode


@dataclass(frozen=True, slots=True)
class OrderLineParseBatch:
    lines: tuple[ParsedOrderLine, ...]
    strict_count: int
    fallback_count: int
    raw_count: int

    @property
    def final_count(self) -> int:
        return len(self.lines)


def build_raw_order_item(line: str) -> HandwrittenLineItem:
    source = line.strip() or "Неизвестная позиция"
    return HandwrittenLineItem(
        product_name=source[:255],
        size=None,
        quantity=Decimal("1"),
        unit="шт",
        source_line=source,
        confidence=Decimal("0.25"),
    )


def parse_order_lines(lines: list[str]) -> OrderLineParseBatch:
    parsed: list[ParsedOrderLine] = []
    strict_count = 0
    fallback_count = 0
    raw_count = 0

    for line in lines:
        source = line.strip()
        if not source:
            continue

        strict_item = parse_handwritten_order_line(source)
        if strict_item is not None:
            parsed.append(ParsedOrderLine(item=strict_item, parse_mode="strict"))
            strict_count += 1
            continue

        fallback_item = _safe_fallback_parse(source)
        if fallback_item is not None:
            parsed.append(ParsedOrderLine(item=fallback_item, parse_mode="fallback"))
            fallback_count += 1
            continue

        parsed.append(ParsedOrderLine(item=build_raw_order_item(source), parse_mode="raw"))
        raw_count += 1

    return OrderLineParseBatch(
        lines=tuple(parsed),
        strict_count=strict_count,
        fallback_count=fallback_count,
        raw_count=raw_count,
    )


def _safe_fallback_parse(source: str) -> HandwrittenLineItem | None:
    try:
        return fallback_parse_handwritten_order_line(source)
    except (ValueError, InvalidOperation):
        return None


def parsed_item_snapshot(entry: ParsedOrderLine) -> dict[str, str | None]:
    item = entry.item
    return {
        "parse_mode": entry.parse_mode,
        "source_line": item.source_line,
        "product_name": item.product_name,
        "size": item.size,
        "quantity": str(item.quantity),
        "unit": item.unit,
    }


def normalize_order_unit(raw: str | None) -> str:
    if raw is None or not str(raw).strip():
        return "шт"
    token = str(raw).strip().casefold().replace(" ", "")
    if token in _UNIT_ALIASES:
        return _UNIT_ALIASES[token]
    for unit in _ORDER_UNITS:
        if unit.casefold() == token:
            return unit
    stripped = str(raw).strip()
    if stripped in _ORDER_UNITS:
        return stripped
    return "шт"


def parse_handwritten_order_line(line: str) -> HandwrittenLineItem | None:
    source = line.strip()
    if not source:
        return None

    split = _split_trailing_quantity_and_unit(source, allow_trailing_number=True)
    if split is None:
        return None
    text, quantity, unit = split
    if not text:
        return None

    product_name, size = _parse_name_and_size(text)
    if not product_name:
        return None
    size = sanitize_parsed_line_size(size, quantity, unit)

    return HandwrittenLineItem(
        product_name=product_name,
        size=size,
        quantity=quantity,
        unit=unit,
        source_line=source,
    )


def fallback_parse_handwritten_order_line(line: str) -> HandwrittenLineItem | None:
    source = line.strip()
    if not source:
        return None

    split = _split_trailing_quantity_and_unit(source, allow_trailing_number=True)
    if split is not None:
        text, quantity, unit = split
    else:
        text = source
        quantity = Decimal("1")
        unit = normalize_order_unit(None)

    product_name, size = _parse_name_and_size(text) if text else (source, None)
    if not product_name.strip():
        product_name = source
    size = sanitize_parsed_line_size(size, quantity, unit)

    return HandwrittenLineItem(
        product_name=clean_product_name(product_name) or source[:255],
        size=size,
        quantity=quantity,
        unit=unit,
        source_line=source,
        confidence=Decimal("0.5"),
    )


def parse_handwritten_order_line_lenient(line: str) -> HandwrittenLineItem | None:
    return parse_handwritten_order_line(line) or fallback_parse_handwritten_order_line(line)


def _split_trailing_quantity_and_unit(
    source: str,
    *,
    allow_trailing_number: bool,
) -> tuple[str, Decimal, str] | None:
    """Parse order line right-to-left: trailing token is quantity + unit, then size, then name."""
    text = source.strip()
    unit = normalize_order_unit(None)

    compact = _COMPACT_QTY_UNIT.search(text)
    if compact:
        quantity = _parse_decimal(compact.group("qty"))
        unit = normalize_order_unit(compact.group("unit"))
        return text[: compact.start()].strip(), quantity, unit

    unit_match = _UNIT_PATTERN.search(text)
    if unit_match:
        unit = normalize_order_unit(unit_match.group("unit"))
        text = text[: unit_match.start()].strip()

    qty_match = _QTY_PATTERN.search(text)
    if qty_match:
        quantity = _parse_decimal(qty_match.group("qty"))
        text = text[: qty_match.start()].strip()
        return text, quantity, unit

    if allow_trailing_number:
        trailing = _TRAILING_NUMBER.search(text)
        if trailing:
            quantity = _parse_decimal(trailing.group("qty"))
            text = text[: trailing.start()].strip()
            return text, quantity, unit

    return None


def _parse_name_and_size(remainder: str) -> tuple[str, str | None]:
    text = remainder.strip()
    tokens = text.split()
    if len(tokens) >= 2:
        for width in (3, 2, 1):
            if len(tokens) <= width:
                continue
            size_part = " ".join(tokens[-width:])
            if not _looks_like_order_size(size_part):
                continue
            name_part = " ".join(tokens[:-width]).strip()
            if name_part:
                return clean_product_name(name_part), normalize_size_text(size_part)

    extracted_size, product_name = extract_size_from_name(text)
    if extracted_size:
        return clean_product_name(product_name), normalize_size_text(extracted_size)

    if len(tokens) < 2:
        return clean_product_name(text), None

    return clean_product_name(text), None


def _looks_like_order_size(fragment: str) -> bool:
    candidate = fragment.strip()
    if not candidate:
        return False
    patterns = (
        r"^\d+(?:[xх×X]\d+(?:[.,]\d+)?)+$",
        r"^\d+\s+SDR\d+$",
        r"^\d+\s+PN\d+$",
        r"^\d+(?:[.,]\d+)?\s*мм$",
        r"^[Øø⌀]\s*\d+(?:[.,]\d+)?$",
        r"^DN\s*\d+(?:[.,]\d+)?$",
        r"^\d+(?:[.,]\d+)?$",
        r'^\d+(?:\s+\d+/\d+)?\s*["\'\u2033″]?$',
    )
    return any(re.fullmatch(pattern, candidate, flags=re.IGNORECASE) for pattern in patterns)


def parse_handwritten_order_text(text: str) -> list[HandwrittenLineItem]:
    batch = parse_order_lines(recover_order_lines_from_ocr(text))
    return [entry.item for entry in batch.lines]


def parse_handwritten_order_text_from_lines(lines: list[str]) -> list[HandwrittenLineItem]:
    batch = parse_order_lines(lines)
    return [entry.item for entry in batch.lines]


def parse_handwritten_order_text_from_lines_batch(lines: list[str]) -> OrderLineParseBatch:
    return parse_order_lines(lines)


def _parse_decimal(token: str) -> Decimal:
    try:
        return Decimal(token.replace(",", "."))
    except InvalidOperation as exc:
        raise ValueError(f"Invalid quantity: {token}") from exc


__all__ = [
    "HandwrittenLineItem",
    "OrderLineParseBatch",
    "ParsedOrderLine",
    "ParseMode",
    "build_raw_order_item",
    "fallback_parse_handwritten_order_line",
    "normalize_order_unit",
    "parse_handwritten_order_line",
    "parse_handwritten_order_line_lenient",
    "parse_handwritten_order_text",
    "parse_handwritten_order_text_from_lines",
    "parse_handwritten_order_text_from_lines_batch",
    "parse_order_lines",
    "parsed_item_snapshot",
]
