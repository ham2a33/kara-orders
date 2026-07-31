from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from app.services.product_size_parser import normalize_size_text

_DIGIT_TO_CYR = str.maketrans(
    {
        "0": "о",
        "1": "л",
        "5": "с",
        "6": "б",
        "8": "в",
    }
)

_LATIN_TO_CYR = str.maketrans(
    {
        "a": "а",
        "b": "в",
        "c": "с",
        "e": "е",
        "h": "н",
        "k": "к",
        "m": "м",
        "o": "о",
        "p": "р",
        "r": "р",
        "t": "т",
        "x": "х",
        "y": "у",
        "A": "а",
        "B": "в",
        "C": "с",
        "E": "е",
        "H": "н",
        "K": "к",
        "M": "м",
        "O": "о",
        "P": "р",
        "R": "р",
        "T": "т",
        "X": "х",
        "Y": "у",
    }
)

_OCR_WORD_FIXES: dict[str, str] = {
    "трба": "труба",
    "труba": "труба",
    "тру6а": "труба",
    "трубa": "труба",
    "крон": "кран",
    "кранн": "кран",
    "кpaн": "кран",
    "тpyба": "труба",
    "труб": "труба",
    "yгол": "угол",
    "yголок": "уголок",
}

_WORD_JUNK = re.compile(r"[,.:;_*\-]+")
_HAS_CYRILLIC = re.compile(r"[а-яё]", re.IGNORECASE)
_NUMERIC_SIZE = re.compile(r"^\d+(?:[.,]\d+)?(?:\s*(?:мм|mm|м|m|x|х|×))?$", re.IGNORECASE)


@lru_cache(maxsize=1)
def _load_product_synonyms() -> dict[str, tuple[str, ...]]:
    path = Path(__file__).resolve().parents[2] / "assets" / "product_synonyms.json"
    if not path.is_file():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return {}
    normalized: dict[str, tuple[str, ...]] = {}
    for key, values in raw.items():
        if not isinstance(key, str):
            continue
        canonical = key.casefold().strip()
        aliases: list[str] = []
        if isinstance(values, list):
            for value in values:
                if isinstance(value, str) and value.strip():
                    aliases.append(value.casefold().strip())
        normalized[canonical] = tuple(dict.fromkeys(aliases))
    return normalized


def collapse_double_letters(word: str) -> str:
    if len(word) < 4:
        return word
    result: list[str] = []
    prev = ""
    for char in word:
        if char == prev and result:
            continue
        result.append(char)
        prev = char
    return "".join(result)


def normalize_ocr_word(token: str) -> str:
    word = token.casefold().translate(_LATIN_TO_CYR)
    word = _WORD_JUNK.sub("", word)
    if _HAS_CYRILLIC.search(word):
        word = word.translate(_DIGIT_TO_CYR)
    word = collapse_double_letters(word)
    return _OCR_WORD_FIXES.get(word, word)


def normalize_ocr_line(line: str) -> str:
    stripped = line.strip()
    if not stripped:
        return ""
    tokens = stripped.split()
    normalized_tokens: list[str] = []
    for token in tokens:
        if _NUMERIC_SIZE.match(token.replace(" ", "")):
            normalized_tokens.append(token.replace(",", "."))
        else:
            normalized_tokens.append(normalize_ocr_word(token))
    return " ".join(normalized_tokens)


def normalize_ocr_product_name(name: str) -> str:
    text = name.strip()
    if not text:
        return ""
    return " ".join(normalize_ocr_word(part) for part in text.split())


def apply_product_synonyms(text: str) -> str:
    normalized = normalize_ocr_product_name(text)
    if not normalized:
        return normalized
    synonyms = _load_product_synonyms()
    if not synonyms:
        return normalized

    result = normalized
    for canonical, aliases in synonyms.items():
        for alias in sorted(aliases, key=len, reverse=True):
            if alias:
                result = re.sub(rf"\b{re.escape(alias)}\b", canonical, result)

    tokens = result.split()
    if tokens:
        first = tokens[0]
        for canonical, aliases in synonyms.items():
            if first == canonical or first in aliases:
                tokens[0] = canonical
                break
        result = " ".join(tokens)
    return result


def build_ai_learning_key(product_name: str, size: str | None) -> str:
    name = apply_product_synonyms(product_name)
    if size and str(size).strip():
        size_key = normalize_size_text(str(size).strip())
        return f"{name} {size_key}".strip().casefold()
    return name.casefold()
