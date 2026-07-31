from __future__ import annotations

from decimal import Decimal

import pytest

from app.services.size_equivalence import sanitize_parsed_line_size, sizes_equivalent


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        ("20", "20 мм", True),
        ("20", "20mm", True),
        ("20", "DN20", True),
        ("20", "Ø20", True),
        ("20 мм", "DN20", True),
        ("3x2.5", "3×2.5", True),
        ("32 PN20", "32 PN20", True),
        ("110 SDR17", "110 SDR17", True),
        ("3 м", "3000 мм", True),
        ("6 м", "6000mm", True),
        ('1/2"', '1/2"', True),
        ("25x40", "25×40", True),
        ("20", "25", False),
        ("20 м", "20 мм", False),
    ],
)
def test_sizes_equivalent(left: str, right: str, expected: bool) -> None:
    assert sizes_equivalent(left, right) is expected


def test_sanitize_parsed_line_size_strips_order_quantity() -> None:
    assert sanitize_parsed_line_size("20 м", Decimal("20"), "м") == "20"
    assert sanitize_parsed_line_size("23 м", Decimal("23"), "м") == "23"


def test_sanitize_parsed_line_size_keeps_product_length() -> None:
    assert sanitize_parsed_line_size("3 м", Decimal("6"), "м") == "3 м"
    assert sanitize_parsed_line_size("20", Decimal("20"), "м") == "20"
