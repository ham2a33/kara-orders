from __future__ import annotations

from app.services.ai.ocr_text_normalize import (
    apply_product_synonyms,
    build_ai_learning_key,
    normalize_ocr_line,
    normalize_ocr_word,
)


def test_normalize_ocr_word_fixes_common_errors() -> None:
    assert normalize_ocr_word("тру6а") == "труба"
    assert normalize_ocr_word("кранн") == "кран"
    assert normalize_ocr_word("крон") == "кран"
    assert normalize_ocr_word("ТРУБА") == "труба"


def test_normalize_ocr_line_preserves_sizes() -> None:
    assert normalize_ocr_line("тру6а 20 29 шт") == "труба 20 29 шт"


def test_apply_product_synonyms() -> None:
    assert apply_product_synonyms("шаровый 20") == "кран 20"


def test_build_ai_learning_key() -> None:
    assert build_ai_learning_key("Труба", "20") == "труба 20"
