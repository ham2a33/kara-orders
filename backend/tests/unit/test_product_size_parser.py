from __future__ import annotations

import pytest

from app.services.product_size_parser import (
    clean_product_name,
    extract_size_from_name,
    normalize_product_name_and_size,
    normalize_size_text,
)

# fmt: off
REAL_PRODUCT_CASES: list[tuple[str, str, str | None]] = [
    ("Труба ППР 20 мм белая", "Труба ППР белая", "20 мм"),
    ("Труба ППР 20 мм", "Труба ППР", "20 мм"),
    ("Труба 20мм", "Труба", "20 мм"),
    ("Труба 16 мм", "Труба", "16 мм"),
    ("Труба Ø20", "Труба", "Ø20"),
    ("Муфта DN20", "Муфта", "DN20"),
    ("Муфта DN25", "Муфта", "DN25"),
    ('Отвод 1/2"', "Отвод", '1/2"'),
    ('Тройник 1 1/4"', "Тройник", '1 1/4"'),
    ('Заглушка 2"', "Заглушка", '2"'),
    ("Кабель ВВГ 3x2.5", "Кабель ВВГ", "3x2.5"),
    ("Кабель ВВГнг-LS 3x2.5", "Кабель ВВГнг-LS", "3x2.5"),
    ("Кабель NYM 5x4", "Кабель NYM", "5x4"),
    ("Кабель 2×0.75", "Кабель", "2×0.75"),
    ("Кабель ВВГ 5x2.5", "Кабель ВВГ", "5x2.5"),
    ("Труба ППР PN20 20×2.8", "Труба ППР PN20", "20×2.8"),
    ("Труба PE100 SDR17 110", "Труба PE100", "110 SDR17"),
    ("Труба 110 SDR17", "Труба", "110 SDR17"),
    ("Труба 32 PN20", "Труба", "32 PN20"),
    ("Труба 25×3.5", "Труба", "25×3.5"),
    ("Арматура A500C 12 мм", "Арматура A500C", "12 мм"),
    ("Арматура A500C 16 мм", "Арматура A500C", "16 мм"),
    ("Саморез 3.5x25", "Саморез", "3.5x25"),
    ("Саморез 4.2x16", "Саморез", "4.2x16"),
    ("Саморез 6x60", "Саморез", "6x60"),
    ("Анкер 10x100", "Анкер", "10x100"),
    ("Дюбель 8x120", "Дюбель", "8x120"),
    ("Гипсокартон 2500x1200x12.5", "Гипсокартон", "2500x1200x12.5"),
    ("OSB-3 1220x2440x9", "OSB-3", "1220x2440x9"),
    ("Минвата 1200x600x50", "Минвата", "1200x600x50"),
    ("Гипсокартон 12.5 мм", "Гипсокартон", "12.5 мм"),
    ("Лист OSB 1220x2440", "Лист OSB", "1220x2440"),
    ("Плита 1250x2500", "Плита", "1250x2500"),
    ("Плита 1200x2500", "Плита", "1200x2500"),
    ("Пена монтажная 750 мл", "Пена монтажная", "750 мл"),
    ("Клей плиточный 25 кг", "Клей плиточный", "25 кг"),
    ("Клей 25 кг", "Клей", "25 кг"),
    ("Краска 750 мл", "Краска", "750 мл"),
    ("Штукатурка 40 кг", "Штукатурка", "40 кг"),
    ("Краска 10 л", "Краска", "10 л"),
    ("Пленка 3x50 м", "Пленка", "3x50 м"),
    ("Сетка 1x20 м", "Сетка", "1x20 м"),
    ("Рубероид 1x10 м", "Рубероид", "1x10 м"),
    ("Линолеум 3x25 м", "Линолеум", "3x25 м"),
    ("Профиль CD60 3 м", "Профиль CD60", "3 м"),
    ("Профиль CD60", "Профиль", "CD60"),
    ("Профиль UW75", "Профиль", "UW75"),
    ("Профиль UD27", "Профиль", "UD27"),
    ("Профиль CW50", "Профиль", "CW50"),
    ("Профиль CW100", "Профиль", "CW100"),
    ("Профиль UW100", "Профиль", "UW100"),
    ("Профиль 50x50 мм", "Профиль", "50x50 мм"),
    ("Плита 200x300", "Плита", "200x300"),
    ("Плита 40×20", "Плита", "40×20"),
    ("Плита 20x40", "Плита", "20x40"),
    ("Труба 6 м", "Труба", "6 м"),
    ("Труба 2 м", "Труба", "2 м"),
    ("Труба 3000 мм", "Труба", "3000 мм"),
    ("Труба 6000мм", "Труба", "6000 мм"),
    ("Труба 0.35 мм", "Труба", "0.35 мм"),
    ("Труба 0.4 мм", "Труба", "0.4 мм"),
    ("Труба 0.45 мм", "Труба", "0.45 мм"),
    ("Труба 8 мм", "Труба", "8 мм"),
    ("Труба 10 мм", "Труба", "10 мм"),
    ("Труба 18 мм", "Труба", "18 мм"),
    ("Уголок 50x50x5", "Уголок", "50x50x5"),
    ("Труба профильная 40x20x2", "Труба профильная", "40x20x2"),
    ("1220×2440×9 лист", "лист", "1220×2440×9"),
    ("600×1200×50 минвата", "минвата", "600×1200×50"),
    ("Труба PPR PN25 25×3.5", "Труба PPR PN25", "25×3.5"),
    ("Муфта PN16", "Муфта", "PN16"),
    ("Муфта PN20", "Муфта", "PN20"),
    ("Труба SDR11 90", "Труба", "90 SDR11"),
    ("Лист OSB 1220x2440, белый", "Лист OSB, белый", "1220x2440"),
    ("Труба - 20 мм - белая", "Труба белая", "20 мм"),
    ("Клей (25 кг)", "Клей", "25 кг"),
    ("Кабель, 3x2.5, медный", "Кабель, медный", "3x2.5"),
    ("Плита 50x50", "Плита", "50x50"),
    ("Плита 100x50", "Плита", "100x50"),
    ("Плита 200x300", "Плита", "200x300"),
    ("Труба 20×2.8", "Труба", "20×2.8"),
    ("Труба 110 SDR17", "Труба", "110 SDR17"),
    ("Кабель 3x1.5", "Кабель", "3x1.5"),
    ("Кабель 5x2.5", "Кабель", "5x2.5"),
    ("Саморез 10x100", "Саморез", "10x100"),
    ("Шуруп 8x120", "Шуруп", "8x120"),
    ("Гвоздь 6x60", "Гвоздь", "6x60"),
    ("Профиль CD60, 3 м", "Профиль CD60", "3 м"),
    ("Профиль CD60 - 3 м", "Профиль CD60", "3 м"),
    ("Труба ППР, 20 мм", "Труба ППР", "20 мм"),
    ("Труба ППР (20 мм)", "Труба ППР", "20 мм"),
    ("Лист 1220x2440 (OSB)", "Лист (OSB)", "1220x2440"),
    ("Кабель NYM 3x1.5 ГОСТ", "Кабель NYM ГОСТ", "3x1.5"),
    ("Кабель NYM 3x2.5", "Кабель NYM", "3x2.5"),
    ("Кабель NYM 5x2.5", "Кабель NYM", "5x2.5"),
    ("Труба PE100 PN20 63", "Труба PE100", "63 PN20"),
    ("Минеральная вата 1000x600x50", "Минеральная вата", "1000x600x50"),
    ("Плита 1220x2440x12", "Плита", "1220x2440x12"),
    ("Профиль 40x20", "Профиль", "40x20"),
    ("Профиль 50x50", "Профиль", "50x50"),
    ("Лист 1200x2400", "Лист", "1200x2400"),
    ("Пленка 3 x 50 м", "Пленка", "3 x 50 м"),
    ("Клей 50 кг", "Клей", "50 кг"),
    ("Раствор 25 кг", "Раствор", "25 кг"),
    ("Цемент 50 кг м500", "Цемент м500", "50 кг"),
    ("Арматура 10 мм", "Арматура", "10 мм"),
    ("Арматура B500B 14 мм", "Арматура B500B", "14 мм"),
    ("Швеллер 10", "Швеллер 10", None),
    ("Уголок 63x63x5", "Уголок", "63x63x5"),
    ("Труба профильная 60x40x2", "Труба профильная", "60x40x2"),
    ("Труба профильная 80x80x3", "Труба профильная", "80x80x3"),
    ("Плита 600x1200x50", "Плита", "600x1200x50"),
    ("Плита 1220x2440x9", "Плита", "1220x2440x9"),
    ("Плита 2500x1200x12.5", "Плита", "2500x1200x12.5"),
    ("Саморез 3,5x25", "Саморез", "3.5x25"),
    ("Труба 20 x 2.8", "Труба", "20 x 2.8"),
    ("Кабель 3 x 2.5", "Кабель", "3 x 2.5"),
]

MODEL_BLACKLIST_CASES: list[tuple[str, str | None]] = [
    ("Дрель Makita DHP482", "Дрель Makita DHP482"),
    ("Шуруповерт Bosch GSR120", "Шуруповерт Bosch GSR120"),
    ("Гайковерт DeWalt DCD791", "Гайковерт DeWalt DCD791"),
    ("Болгарка Milwaukee M18", "Болгарка Milwaukee M18"),
    ("Перфоратор Metabo KHE2644", "Перфоратор Metabo KHE2644"),
    ("Лобзик Hilti SJT150-A", "Лобзик Hilti SJT150-A"),
]

EXPLICIT_SIZE_CASES: list[tuple[str, str | None, str, str | None]] = [
    ("Труба ППР 20 мм", "25", "Труба ППР", "25"),
    ("Муфта", "20", "Муфта", "20"),
    ("Труба ППР 20 мм белая", "32", "Труба ППР белая", "32"),
    ("Кабель ВВГ 3x2.5", "4x6", "Кабель ВВГ", "4x6"),
]

NAME_CLEANING_CASES: list[tuple[str, str]] = [
    ("Труба   ППР   белая", "Труба ППР белая"),
    ("Труба - - белая", "Труба белая"),
    ("Труба,, белая", "Труба, белая"),
    ("Труба ( ) белая", "Труба белая"),
    ("  - Труба -  ", "Труба"),
    ("Труба; белая", "Труба; белая"),
]
# fmt: on


@pytest.mark.parametrize(("name", "expected_name", "expected_size"), REAL_PRODUCT_CASES)
def test_extract_size_from_name_real_products(
    name: str,
    expected_name: str,
    expected_size: str | None,
) -> None:
    size, cleaned_name = extract_size_from_name(name)
    assert cleaned_name == expected_name
    assert size == expected_size


@pytest.mark.parametrize(("name", "expected_name"), MODEL_BLACKLIST_CASES)
def test_extract_size_skips_tool_models(name: str, expected_name: str) -> None:
    size, cleaned_name = extract_size_from_name(name)
    assert cleaned_name == expected_name
    assert size is None


@pytest.mark.parametrize(("name", "explicit_size", "expected_name", "expected_size"), EXPLICIT_SIZE_CASES)
def test_normalize_product_name_and_size_prefers_explicit_column(
    name: str,
    explicit_size: str | None,
    expected_name: str,
    expected_size: str | None,
) -> None:
    cleaned_name, size = normalize_product_name_and_size(name, explicit_size)
    assert cleaned_name == expected_name
    assert size == expected_size


@pytest.mark.parametrize(("raw", "expected"), NAME_CLEANING_CASES)
def test_clean_product_name(raw: str, expected: str) -> None:
    assert clean_product_name(raw) == expected


@pytest.mark.parametrize(
    ("size", "expected"),
    [
        ("20мм", "20 мм"),
        ("DN 20", "DN20"),
        ("PN 20", "PN20"),
        ("SDR 17", "SDR17"),
        ("cd 60", "CD60"),
        ("3,5x25", "3.5x25"),
    ],
)
def test_normalize_size_text(size: str, expected: str) -> None:
    assert normalize_size_text(size) == expected


def test_priority_prefers_pipe_wall_over_pn() -> None:
    size, name = extract_size_from_name("Труба ППР PN20 20×2.8")
    assert size == "20×2.8"
    assert name == "Труба ППР PN20"


def test_priority_prefers_sdr_combo_over_profile_length() -> None:
    size, name = extract_size_from_name("Труба PE100 SDR17 110")
    assert size == "110 SDR17"
    assert name == "Труба PE100"


def test_priority_prefers_length_over_profile_code() -> None:
    size, name = extract_size_from_name("Профиль CD60 3 м")
    assert size == "3 м"
    assert name == "Профиль CD60"


def test_priority_prefers_cable_over_sheet_when_both_match_patterns() -> None:
    size, name = extract_size_from_name("Кабель NYM 5x4")
    assert size == "5x4"
    assert name == "Кабель NYM"


def test_material_grade_stays_in_name() -> None:
    size, name = extract_size_from_name("Арматура A500C 12 мм")
    assert size == "12 мм"
    assert "A500C" in name


def test_pe100_stays_in_name_for_pipe() -> None:
    size, name = extract_size_from_name("Труба PE100 SDR17 110")
    assert "PE100" in name
    assert size == "110 SDR17"


def test_at_least_one_hundred_real_product_cases() -> None:
    assert len(REAL_PRODUCT_CASES) >= 100
