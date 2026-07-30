from __future__ import annotations

import re
from dataclasses import dataclass

_CROSS = r"\s*[x×хX]\s*"
_NUMBER = r"\d+(?:[.,]\d+)?"


@dataclass(frozen=True, slots=True)
class SizePattern:
    key: str
    priority: int
    regex: re.Pattern[str]


@dataclass(frozen=True, slots=True)
class SizeMatch:
    text: str
    start: int
    end: int
    priority: int
    pattern_key: str


_MODEL_BLACKLIST = re.compile(
    r"\b(?:"
    r"Makita|Bosch|DeWalt|Milwaukee|Metabo|Hitachi|Hilti|Stanley|Festool|"
    r"Ryobi|Einhell|AEG|Skil|Patriot|Kress|Black\+?Decker|"
    r"Зубр|Интерскол|Stihl|Sturm|Worx|Greenworks"
    r")\s+[A-Z]{1,4}\d{2,4}[A-Z]?\d*\b",
    re.IGNORECASE,
)

_MATERIAL_GRADES = re.compile(r"\b[AB]\d{3}[A-Z]{0,2}\b", re.IGNORECASE)
_MATERIAL_MARKS = re.compile(
    r"\b(?:PE\d+|PPR|PPRC|PVC|HDPE|LDPE|VGP|OSB(?:-\d+)?|A500C|B500B|ВВГ(?:нг(?:-LS)?)?|NYM|NYY|KG(?:-H)?)\b",
    re.IGNORECASE,
)


def _compile(pattern: str, *, flags: int = re.IGNORECASE) -> re.Pattern[str]:
    return re.compile(pattern, flags)


def _build_size_patterns() -> tuple[SizePattern, ...]:
    cross = _CROSS
    num = _NUMBER
    return (
        SizePattern("pipe_diameter_sdr", 1, _compile(rf"\b{num}\s+SDR\s*\d+\b")),
        SizePattern("pipe_sdr_diameter", 1, _compile(rf"\bSDR\s*\d+\s+{num}(?!\s*[x×хX])\b")),
        SizePattern("pipe_diameter_pn", 1, _compile(rf"\b{num}\s+PN\s*\d+\b")),
        SizePattern("pipe_pn_diameter", 1, _compile(rf"\bPN\s*\d+\s+{num}(?!\s*[x×хX])\b")),
        SizePattern("dimension_3d", 1, _compile(rf"\b{num}{cross}{num}(?:\.\d+)?{cross}{num}(?:\.\d+)?\b")),
        SizePattern("pipe_wall", 1, _compile(rf"\b(?:[1-9]\d+){cross}\d+[.,]\d+\b")),
        SizePattern("fastener", 1, _compile(rf"\b\d+[.,]\d+{cross}\d+\b")),
        SizePattern("roll_material", 2, _compile(rf"\b{num}{cross}{num}\s*м\b")),
        SizePattern("wxh_mm", 2, _compile(rf"\b\d+{cross}\d+\s*мм\b")),
        SizePattern("wxh", 2, _compile(rf"\b\d+{cross}\d+\b")),
        SizePattern("cable", 3, _compile(rf"\b\d+{cross}{num}\b")),
        SizePattern("sheet_2d", 4, _compile(rf"\b\d{{3,4}}{cross}\d{{3,4}}\b")),
        SizePattern("length_mm", 5, _compile(rf"\b{num}\s*мм\b")),
        SizePattern("length_mm_compact", 5, _compile(rf"\b{num}мм\b")),
        SizePattern("length_m", 5, _compile(rf"\b{num}\s*м\b")),
        SizePattern("diameter_inch_compound", 5, _compile(r'(?<!\d)\d+\s+\d+/\d+\s*["\'\u2033″]')),
        SizePattern("diameter_inch_fraction", 5, _compile(r'(?<!\d)\d+/\d+\s*["\'\u2033″]')),
        SizePattern("diameter_inch_whole", 5, _compile(r'(?<![\d/])\d+\s*["\'\u2033″]')),
        SizePattern("diameter_symbol", 5, _compile(rf"[Øø⌀]\s*{num}(?:\s*мм)?\b")),
        SizePattern("packaging", 6, _compile(rf"\b{num}\s*(?:кг|л|мл)\b")),
        SizePattern("pipe_pn", 7, _compile(r"\bPN\s*\d+\b")),
        SizePattern("pipe_dn", 7, _compile(r"\bDN\s*\d+\b")),
        SizePattern("gkl_profile", 8, _compile(r"\b(?:UD|CD|CW|UW)\s*\d+\b")),
    )


SIZE_PATTERNS: tuple[SizePattern, ...] = _build_size_patterns()


def normalize_product_name_and_size(name: str, size: str | None = None) -> tuple[str, str | None]:
    cleaned_name = name.strip()
    explicit_size = (size or "").strip() or None
    extracted_size, cleaned_name = extract_size_from_name(cleaned_name)
    final_size = explicit_size or extracted_size
    return cleaned_name, final_size


def extract_size_from_name(name: str) -> tuple[str | None, str]:
    if not name.strip():
        return None, name

    blocked_spans = _collect_blocked_spans(name)
    matches = _find_size_matches(name, blocked_spans)
    best_match = _select_best_match(matches)
    if best_match is None:
        return None, name

    size = normalize_size_text(best_match.text)
    cleaned_name = name[: best_match.start] + name[best_match.end :]
    return size, clean_product_name(cleaned_name)


def clean_product_name(name: str) -> str:
    text = name.strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\(\s*\)", "", text)
    text = re.sub(r"\[\s*\]", "", text)
    text = re.sub(r"\{\s*\}", "", text)
    text = re.sub(r"\s*[-–—]\s*[-–—]+\s*", " ", text)
    text = re.sub(r"^\s*[-–—,;]\s*|\s*[-–—,;]\s*$", "", text)
    text = re.sub(r"\s*,\s*,+", ", ", text)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" -–—,;")


def normalize_size_text(size: str) -> str:
    text = re.sub(r"\s+", " ", size.strip())
    sdr_first = re.fullmatch(r"SDR\s*(\d+)\s+(\d+(?:[.,]\d+)?)", text, flags=re.IGNORECASE)
    if sdr_first:
        diameter = sdr_first.group(2).replace(",", ".")
        return f"{diameter} SDR{sdr_first.group(1)}"
    pn_first = re.fullmatch(r"PN\s*(\d+)\s+(\d+(?:[.,]\d+)?)", text, flags=re.IGNORECASE)
    if pn_first:
        diameter = pn_first.group(2).replace(",", ".")
        return f"{diameter} PN{pn_first.group(1)}"
    text = re.sub(r"(\d)(мм|м|кг|л|мл)\b", r"\1 \2", text, flags=re.IGNORECASE)
    text = re.sub(r"\bDN\s*(\d+)\b", r"DN\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\bPN\s*(\d+)\b", r"PN\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\bSDR\s*(\d+)\b", r"SDR\1", text, flags=re.IGNORECASE)
    text = re.sub(
        r"\b((?:UD|CD|CW|UW)\s*)(\d+)\b",
        lambda match: f"{match.group(1).upper().strip()}{match.group(2)}",
        text,
        flags=re.IGNORECASE,
    )
    return text.replace(",", ".")


def _collect_blocked_spans(name: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    for pattern in (_MODEL_BLACKLIST, _MATERIAL_GRADES, _MATERIAL_MARKS):
        for match in pattern.finditer(name):
            spans.append((match.start(), match.end()))
    return spans


def _find_size_matches(name: str, blocked_spans: list[tuple[int, int]]) -> list[SizeMatch]:
    matches: list[SizeMatch] = []
    for pattern in SIZE_PATTERNS:
        for match in pattern.regex.finditer(name):
            if _is_blocked(match.start(), match.end(), blocked_spans):
                continue
            if pattern.key == "cable" and (not _looks_like_cable(match.group()) or _looks_like_pipe_wall(match.group())):
                continue
            if pattern.key == "wxh" and _looks_like_cable(match.group()):
                continue
            matches.append(
                SizeMatch(
                    text=match.group(),
                    start=match.start(),
                    end=match.end(),
                    priority=pattern.priority,
                    pattern_key=pattern.key,
                )
            )
    return matches


def _select_best_match(matches: list[SizeMatch]) -> SizeMatch | None:
    if not matches:
        return None

    resolved = _resolve_overlapping_matches(matches)
    return min(resolved, key=lambda match: (match.priority, -len(match.text), -match.start))


def _resolve_overlapping_matches(matches: list[SizeMatch]) -> list[SizeMatch]:
    ordered = sorted(matches, key=lambda match: (match.priority, -len(match.text), -match.start))
    kept: list[SizeMatch] = []
    for candidate in ordered:
        if any(_overlaps(candidate, existing) for existing in kept):
            continue
        kept.append(candidate)
    return kept


def _is_blocked(start: int, end: int, blocked_spans: list[tuple[int, int]]) -> bool:
    return any(not (end <= blocked_start or start >= blocked_end) for blocked_start, blocked_end in blocked_spans)


def _overlaps(left: SizeMatch, right: SizeMatch) -> bool:
    return not (left.end <= right.start or right.end <= left.start)


def _looks_like_cable(text: str) -> bool:
    parts = re.split(r"[x×хX]", text, maxsplit=1)
    if len(parts) != 2:
        return False
    left, right = parts[0].strip(), parts[1].strip()
    if "." in right or "," in right:
        return True
    if left.isdigit() and right.isdigit():
        return max(int(left), int(right)) <= 10
    return False


def _looks_like_pipe_wall(text: str) -> bool:
    parts = re.split(r"[x×хX]", text, maxsplit=1)
    if len(parts) != 2:
        return False
    left = parts[0].strip()
    return left.replace(".", "").replace(",", "").isdigit() and int(float(left.replace(",", "."))) >= 10
