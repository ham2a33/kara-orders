from __future__ import annotations

from decimal import Decimal

from app.services.ai.handwritten_line_parser import parse_handwritten_order_text
from app.services.ai.ocr_postprocess import postprocess_ocr_order_text, recover_order_lines_from_ocr


def test_postprocess_splits_merged_ocr_line() -> None:
    merged = "Труба 20 29 шт Муфта 50 10 шт"
    lines = recover_order_lines_from_ocr(merged)
    assert lines == ["Труба 20 29 шт", "Муфта 50 10 шт"]


def test_postprocess_splits_merged_line_with_compact_qty_unit() -> None:
    merged = "Труба 20 20м Муфта 20 15шт"
    lines = recover_order_lines_from_ocr(merged)
    assert lines == ["Труба 20 20м", "Муфта 20 15шт"]


def test_postprocess_preserves_existing_newlines() -> None:
    text = "Труба 20 20 шт\nМуфта 50 10 шт"
    assert postprocess_ocr_order_text(text).splitlines() == [
        "Труба 20 20 шт",
        "Муфта 50 10 шт",
    ]


def test_parse_handwritten_order_text_after_ocr_recovery() -> None:
    merged = "Труба 20 29 шт Арматура 12 5 м"
    items = parse_handwritten_order_text(merged)
    assert len(items) == 2
    assert items[0].product_name == "Труба"
    assert items[0].quantity == Decimal("29")
    assert items[1].product_name == "Арматура"


def test_parse_handwritten_order_text_fallback_when_strict_parser_fails() -> None:
    text = "Труба без количества"
    items = parse_handwritten_order_text(text)
    assert len(items) == 1
    assert items[0].source_line == text
    assert items[0].quantity == Decimal("1")
    assert "Труба" in items[0].product_name


def test_parse_handwritten_order_text_never_drops_lines() -> None:
    text = "строка один\nстрока два"
    items = parse_handwritten_order_text(text)
    assert len(items) == 2


def test_recover_order_lines_never_empty_for_nonempty_ocr() -> None:
    assert recover_order_lines_from_ocr("  одна строка  ") == ["одна строка"]
