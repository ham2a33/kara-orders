from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from app.services.product_size_parser import normalize_size_text

_CROSS = re.compile(r"[x×хX]")
_LENGTH_UNITS = frozenset({"м", "m"})
_MASS_VOLUME_UNITS = frozenset({"кг", "kg", "л", "l", "мл", "ml", "г", "g"})
_ORDER_QTY_UNITS = frozenset({"м", "m", "шт", "pcs", "pc", "кг", "kg", "л", "l", "м²", "m2", "м³", "m3"})


def sanitize_parsed_line_size(
    size: str | None,
    quantity: Decimal | None,
    unit: str | None,
) -> str | None:
    """Ensure product characteristic size never duplicates order quantity + unit."""
    if size is None or not str(size).strip():
        return None
    text = normalize_size_text(str(size).strip())
    if quantity is None:
        return text or None

    qty_token = _decimal_token(quantity)
    unit_token = _normalize_unit_token(unit)

    if unit_token and qty_token:
        glued = rf"^{re.escape(qty_token)}\s*{_unit_pattern(unit_token)}$"
        if re.fullmatch(glued, text, flags=re.IGNORECASE):
            return None
        compact = rf"^{re.escape(qty_token)}{_unit_pattern(unit_token)}$"
        if re.fullmatch(compact, text, flags=re.IGNORECASE):
            return None

    length_match = re.fullmatch(r"(\d+(?:\.\d+)?)\s*([мm])\b", text, flags=re.IGNORECASE)
    if length_match and unit_token in _LENGTH_UNITS and qty_token:
        try:
            size_qty = Decimal(length_match.group(1).replace(",", "."))
        except InvalidOperation:
            return text
        if size_qty == quantity and _looks_like_diameter_only(length_match.group(1)):
            return length_match.group(1).replace(",", ".")

    return text or None


def sizes_equivalent(left: str | None, right: str | None) -> bool:
    if left is None and right is None:
        return True
    if left is None or right is None:
        return False
    left_keys = size_equivalence_keys(left)
    right_keys = size_equivalence_keys(right)
    if not left_keys or not right_keys:
        return _normalize_token(normalize_size_text(left)) == _normalize_token(normalize_size_text(right))
    return bool(left_keys & right_keys)


def size_equivalence_keys(size: str) -> frozenset[str]:
    normalized = normalize_size_text(size.strip())
    if not normalized:
        return frozenset()

    keys: set[str] = {_normalize_token(normalized)}

    for variant in _expand_size_variants(normalized):
        keys.add(_normalize_token(variant))

    composite = _composite_size_key(normalized)
    if composite:
        keys.add(_normalize_token(composite))

    return frozenset(keys)


def _expand_size_variants(normalized: str) -> set[str]:
    variants: set[str] = set()

    dn_match = re.fullmatch(r"DN\s*(\d+(?:\.\d+)?)", normalized, flags=re.IGNORECASE)
    if dn_match:
        variants.update(_diameter_keys(dn_match.group(1)))
        return variants

    diameter_symbol = re.fullmatch(r"[Øø⌀]\s*(\d+(?:\.\d+)?)(?:\s*мм)?", normalized, flags=re.IGNORECASE)
    if diameter_symbol:
        variants.update(_diameter_keys(diameter_symbol.group(1)))
        return variants

    mm_match = re.fullmatch(r"(\d+(?:\.\d+)?)\s*мм", normalized, flags=re.IGNORECASE)
    if mm_match:
        if _numeric_value(mm_match.group(1)) >= 1000:
            variants.update(_length_mm_keys(mm_match.group(1)))
        else:
            variants.update(_diameter_keys(mm_match.group(1)))
        return variants

    compact_mm = re.fullmatch(r"(\d+(?:\.\d+)?)мм", normalized, flags=re.IGNORECASE)
    if compact_mm:
        if _numeric_value(compact_mm.group(1)) >= 1000:
            variants.update(_length_mm_keys(compact_mm.group(1)))
        else:
            variants.update(_diameter_keys(compact_mm.group(1)))
        return variants

    mm_ascii = re.fullmatch(r"(\d+(?:\.\d+)?)\s*mm", normalized, flags=re.IGNORECASE)
    if mm_ascii:
        variants.update(_diameter_keys(mm_ascii.group(1)))
        return variants

    length_m = re.fullmatch(r"(\d+(?:\.\d+)?)\s*([мm])\b", normalized, flags=re.IGNORECASE)
    if length_m:
        variants.update(_length_meter_keys(length_m.group(1)))
        return variants

    mm_ascii = re.fullmatch(r"(\d+(?:\.\d+)?)\s*mm", normalized, flags=re.IGNORECASE)
    if mm_ascii:
        if _numeric_value(mm_ascii.group(1)) >= 1000:
            variants.update(_length_mm_keys(mm_ascii.group(1)))
        else:
            variants.update(_diameter_keys(mm_ascii.group(1)))
        return variants

    inch_match = re.fullmatch(
        r'(\d+(?:\s+\d+/\d+)?|\d+/\d+)\s*(["\'\u2033″])?',
        normalized,
        flags=re.IGNORECASE,
    )
    if inch_match:
        variants.add(inch_match.group(1).strip())
        return variants

    if re.fullmatch(r"\d+(?:\.\d+)?", normalized):
        variants.update(_diameter_keys(normalized))
        return variants

    if _CROSS.search(normalized):
        variants.add(_normalize_cross_dimensions(normalized))
        cable = re.fullmatch(r"(\d+(?:\.\d+)?)\s*[x×хX]\s*(\d+(?:\.\d+)?)", normalized, flags=re.IGNORECASE)
        if cable:
            left, right = cable.group(1).replace(",", "."), cable.group(2).replace(",", ".")
            variants.add(f"{left}x{right}")
        return variants

    pn_sdr = re.fullmatch(
        r"(\d+(?:\.\d+)?)\s+(PN\d+|SDR\d+)|(?:PN\d+|SDR\d+)\s+(\d+(?:\.\d+)?)",
        normalized,
        flags=re.IGNORECASE,
    )
    if pn_sdr:
        variants.add(normalized)
        return variants

    profile = re.fullmatch(r"((?:UD|CD|CW|UW)\s*\d+)", normalized, flags=re.IGNORECASE)
    if profile:
        variants.add(re.sub(r"\s+", "", profile.group(1).upper()))
        return variants

    return variants


def _composite_size_key(normalized: str) -> str | None:
    pipe_combo = re.fullmatch(
        r"(\d+(?:\.\d+)?)\s+(PN\d+|SDR\d+)",
        normalized,
        flags=re.IGNORECASE,
    )
    if pipe_combo:
        return f"{pipe_combo.group(1).replace(',', '.')} {pipe_combo.group(2).upper()}"

    sdr_first = re.fullmatch(r"(SDR\d+)\s+(\d+(?:\.\d+)?)", normalized, flags=re.IGNORECASE)
    if sdr_first:
        return f"{sdr_first.group(2).replace(',', '.')} {sdr_first.group(1).upper()}"

    pn_first = re.fullmatch(r"(PN\d+)\s+(\d+(?:\.\d+)?)", normalized, flags=re.IGNORECASE)
    if pn_first:
        return f"{pn_first.group(2).replace(',', '.')} {pn_first.group(1).upper()}"

    return None


def _diameter_keys(diameter: str) -> set[str]:
    value = diameter.replace(",", ".")
    keys = {
        value,
        f"{value} mm",
        f"{value}mm",
        f"{value} мм",
        f"{value}мм",
        f"DN{value}",
        f"Ø{value}",
    }
    if value.endswith(".0"):
        int_value = value[:-2]
        keys.update(
            {
                int_value,
                f"{int_value} mm",
                f"{int_value}mm",
                f"{int_value} мм",
                f"{int_value}мм",
                f"DN{int_value}",
                f"Ø{int_value}",
            }
        )
    return keys


def _length_meter_keys(meters: str) -> set[str]:
    value = meters.replace(",", ".")
    keys = {f"{value} м", f"{value}m", value}
    try:
        mm = Decimal(value) * Decimal("1000")
        if mm == mm.to_integral_value():
            int_mm = str(int(mm))
            keys.add(f"{int_mm} мм")
            keys.add(f"{int_mm}mm")
    except InvalidOperation:
        pass
    return keys


def _length_mm_keys(mm_value: str) -> set[str]:
    value = mm_value.replace(",", ".")
    keys = {f"{value} мм", f"{value}mm", value}
    try:
        meters = Decimal(value) / Decimal("1000")
        normalized = format(meters.normalize(), "f").rstrip("0").rstrip(".")
        keys.add(f"{normalized} м")
        keys.add(f"{normalized}m")
    except InvalidOperation:
        pass
    return keys


def _normalize_cross_dimensions(value: str) -> str:
    parts = re.split(r"[x×хX]", value)
    normalized_parts = [part.strip().replace(",", ".") for part in parts if part.strip()]
    return "x".join(normalized_parts)


def _numeric_value(token: str) -> float:
    try:
        return float(token.replace(",", "."))
    except ValueError:
        return 0.0


def _looks_like_diameter_only(token: str) -> bool:
    try:
        value = float(token.replace(",", "."))
    except ValueError:
        return False
    return 0 < value <= 500


def _decimal_token(value: Decimal) -> str:
    normalized = format(value.normalize(), "f")
    if "." in normalized:
        normalized = normalized.rstrip("0").rstrip(".")
    return normalized.replace(",", ".")


def _normalize_unit_token(unit: str | None) -> str:
    if not unit:
        return ""
    token = str(unit).strip().casefold().replace(" ", "")
    aliases = {
        "pcs": "шт",
        "pc": "шт",
        "piece": "шт",
        "pieces": "шт",
        "m": "м",
        "meter": "м",
        "metre": "м",
        "kg": "кг",
        "l": "л",
        "liter": "л",
        "litre": "л",
        "m2": "м²",
        "m3": "м³",
    }
    return aliases.get(token, token)


def _unit_pattern(unit: str) -> str:
    if unit == "м":
        return r"(?:м|m)\b"
    if unit == "шт":
        return r"(?:шт|pcs|pc)\.?"
    if unit == "кг":
        return r"(?:кг|kg)\.?"
    if unit == "л":
        return r"(?:л|l|литр)\.?"
    if unit == "м²":
        return r"(?:м²|m2|m\^2)\.?"
    if unit == "м³":
        return r"(?:м³|m3|m\^3)\.?"
    return re.escape(unit)


def _normalize_token(value: str) -> str:
    text = value.casefold().replace("×", "x").replace("х", "x")
    text = re.sub(r"\s+", " ", text.strip())
    return text


__all__ = ["sanitize_parsed_line_size", "size_equivalence_keys", "sizes_equivalent"]
