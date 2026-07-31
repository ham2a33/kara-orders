from __future__ import annotations

from decimal import Decimal

from app.services.ai.handwritten_line_parser import (
    build_raw_order_item,
    parse_order_lines,
)


def test_parse_order_lines_one_item_per_nonempty_line() -> None:
    batch = parse_order_lines(["Труба 20 20 шт", "строка без формата", ""])
    assert batch.final_count == 2
    assert batch.strict_count == 1
    assert batch.fallback_count == 1
    assert batch.raw_count == 0


def test_parse_order_lines_uses_fallback_for_unstructured_line() -> None:
    batch = parse_order_lines(["строка без формата"])
    assert batch.final_count == 1
    assert batch.lines[0].parse_mode == "fallback"
    assert batch.lines[0].item.quantity == Decimal("1")


def test_build_raw_order_item_defaults() -> None:
    item = build_raw_order_item("  сырая строка ")
    assert item.product_name == "сырая строка"
    assert item.quantity == Decimal("1")
    assert item.unit == "шт"
