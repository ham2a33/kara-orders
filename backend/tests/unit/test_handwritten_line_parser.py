from __future__ import annotations

from decimal import Decimal

import pytest

from app.services.ai.catalog_match import (
    base_name_similar_for_sized_query,
    build_catalog_search_key,
    line_matches_catalog_entry,
    name_similarity_score,
    sizes_equivalent,
)
from app.services.ai.handwritten_line_parser import parse_handwritten_order_line, parse_handwritten_order_text


@pytest.mark.parametrize(
    ("line", "name", "size", "qty", "unit"),
    [
        ("Труба 20 20 шт", "Труба", "20", Decimal("20"), "шт"),
        ("Муфта 50 10 шт", "Муфта", "50", Decimal("10"), "шт"),
        ("Арматура 12 30 м", "Арматура", "12", Decimal("30"), "м"),
        ("Кабель ВВГ 3x2.5 100 м", "Кабель ВВГ", "3x2.5", Decimal("100"), "м"),
        ("Уголок 25x25 6 шт", "Уголок", "25x25", Decimal("6"), "шт"),
        ("Клей Ceresit CM11 5 шт", "Клей Ceresit CM11", None, Decimal("5"), "шт"),
        ("Труба 20мм 15 шт", "Труба", "20 мм", Decimal("15"), "шт"),
        ("Труба 20 мм 15 шт", "Труба", "20 мм", Decimal("15"), "шт"),
        ("Труба Ø20 4 шт", "Труба", "Ø20", Decimal("4"), "шт"),
        ("Муфта DN20 3 шт", "Муфта", "DN20", Decimal("3"), "шт"),
        ("Труба 32 PN20 8 шт", "Труба", "32 PN20", Decimal("8"), "шт"),
        ("Труба 110 SDR17 2 шт", "Труба", "110 SDR17", Decimal("2"), "шт"),
        ('Отвод 1/2" 10 шт', "Отвод", '1/2"', Decimal("10"), "шт"),
        ("Кабель 3x2.5 50 м", "Кабель", "3x2.5", Decimal("50"), "м"),
        ("Профиль 25×40 12 шт", "Профиль", "25×40", Decimal("12"), "шт"),
        ("Штукатурка 40 кг", "Штукатурка", None, Decimal("40"), "кг"),
        ("Краска 10 л", "Краска", None, Decimal("10"), "л"),
        ("Пленка 2,5 м²", "Пленка", None, Decimal("2.5"), "м²"),
        ("Грунт 3 m3", "Грунт", None, Decimal("3"), "м³"),
        ("Труба 20 20", "Труба", "20", Decimal("20"), "шт"),
        ("Арматура 12 1,5 м", "Арматура", "12", Decimal("1.5"), "м"),
        ("Кабель ВВГ 3x2,5 100 м", "Кабель ВВГ", "3x2.5", Decimal("100"), "м"),
        ("Труба 20x2.8 11 шт", "Труба", "20x2.8", Decimal("11"), "шт"),
        ("Саморез 4.2x16 200 шт", "Саморез", "4.2x16", Decimal("200"), "шт"),
        ("Анкер 10x100 25 шт", "Анкер", "10x100", Decimal("25"), "шт"),
        ("Труба PE100 SDR17 110 1 шт", "Труба PE100", "110 SDR17", Decimal("1"), "шт"),
        ("Минвата 50 10 м²", "Минвата", "50", Decimal("10"), "м²"),
        ("Рубероид 1x10 м 3 м", "Рубероид", "1x10 м", Decimal("3"), "м"),
        ("Клей 25 кг 2 кг", "Клей", "25 кг", Decimal("2"), "кг"),
        ("Valve 20 5 pcs", "Valve", "20", Decimal("5"), "шт"),
        ("Труба 20 20м", "Труба", "20", Decimal("20"), "м"),
        ("Арматура 12 23м", "Арматура", "12", Decimal("23"), "м"),
        ("Муфта 20 15шт", "Муфта", "20", Decimal("15"), "шт"),
        ("Муфта 32 10шт", "Муфта", "32", Decimal("10"), "шт"),
        ("Кран шаровый 20 2шт", "Кран шаровый", "20", Decimal("2"), "шт"),
        ("Кабель ВВГ 3x2.5 100м", "Кабель ВВГ", "3x2.5", Decimal("100"), "м"),
        ("Уголок 25 50шт", "Уголок", "25", Decimal("50"), "шт"),
    ],
)
def test_parse_handwritten_order_line_matrix(line: str, name: str, size: str | None, qty: Decimal, unit: str) -> None:
    parsed = parse_handwritten_order_line(line)
    assert parsed is not None, line
    assert parsed.product_name == name
    assert parsed.size == size
    assert parsed.quantity == qty
    assert parsed.unit == unit


def test_parse_handwritten_order_text_one_line_per_item() -> None:
    text = "\n".join(
        [
            "Труба 20 20 шт",
            "Муфта 50 10 шт",
            "Арматура 12 30 м",
            "Кабель ВВГ 3x2.5 100 м",
        ]
    )
    items = parse_handwritten_order_text(text)
    assert len(items) == 4
    assert items[0].product_name == "Труба"
    assert items[-1].size == "3x2.5"


def test_build_catalog_search_key() -> None:
    assert build_catalog_search_key("Труба", "20") == "Труба 20"
    assert build_catalog_search_key("Кабель ВВГ", "3x2.5") == "Кабель ВВГ 3x2.5"


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        ("20", "20 мм", True),
        ("20", "Ø20", True),
        ("20", "DN20", True),
        ("20 мм", "DN20", True),
        ("3x2.5", "3x2.5", True),
        ("25x25", "25x40", False),
        ("12", "30", False),
        (None, None, True),
    ],
)
def test_sizes_equivalent(left: str | None, right: str | None, expected: bool) -> None:
    assert sizes_equivalent(left, right) is expected


def test_line_matches_catalog_entry_allows_short_name() -> None:
    assert line_matches_catalog_entry("Труба", "20", "Труба ППР", "20 мм") is True
    assert line_matches_catalog_entry("Муфта", "50", "Клей Ceresit CM11", None) is False


def test_name_similarity_short_pipe_name() -> None:
    assert name_similarity_score("Труба", "Труба ППР") >= 0.8
    assert name_similarity_score("Труба", "Труба PN20") >= 0.8
    assert name_similarity_score("Труба", "Труба армированная") >= 0.55


def test_base_name_similar_for_sized_query() -> None:
    assert base_name_similar_for_sized_query("Труба", "Труба ППР") is True
    assert base_name_similar_for_sized_query("Труба", "Труба армированная") is True
    assert base_name_similar_for_sized_query("Кран", "Кран шаровый") is True
    assert base_name_similar_for_sized_query("Муфта", "Клей Ceresit CM11") is False
