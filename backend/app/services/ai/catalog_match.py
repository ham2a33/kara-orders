from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher

from app.db.models.product import Product
from app.services.product_size_parser import extract_size_from_name, normalize_size_text
from app.services.size_equivalence import size_equivalence_keys, sizes_equivalent

_MIN_NAME_SCORE = 0.55
_COMPATIBLE_NAME_SCORE = 0.55

_SCORE_NAME_EXACT = 100
_SCORE_SIZE_FIELD = 80
_SCORE_SIZE_IN_NAME = 70
_SCORE_NAME_ONLY = 30

_SEARCH_UNIT_PATTERN = re.compile(
    r"\b(?:"
    r"мм|mm|"
    r"м|m|"
    r"кг|kg|"
    r"л|l|"
    r"мл|ml|"
    r"метров|метра|метр|meters|meter|"
    r"шт|pcs|pc"
    r")\b",
    flags=re.IGNORECASE,
)


def build_catalog_search_key(product_name: str, size: str | None) -> str:
    base = product_name.strip()
    if size and size.strip():
        return f"{base} {normalize_size_text(size.strip())}".strip()
    return base


def split_name_and_size(text: str) -> tuple[str, str | None]:
    extracted_size, cleaned_name = extract_size_from_name(text.strip())
    if not extracted_size:
        return text.strip(), None
    return cleaned_name.strip(), normalize_size_text(extracted_size)


def names_compatible(query_name: str, catalog_name: str) -> bool:
    return name_similarity_score(query_name, catalog_name) >= _COMPATIBLE_NAME_SCORE


def name_similarity_score(query_name: str, catalog_name: str) -> float:
    query = _normalize_name(query_name)
    catalog = _normalize_name(catalog_name)
    if not query or not catalog:
        return 0.0
    if query == catalog:
        return 1.0
    if catalog.startswith(f"{query} ") or query.startswith(f"{catalog} "):
        return 0.92

    query_tokens = query.split()
    catalog_tokens = catalog.split()
    query_set = set(query_tokens)
    catalog_set = set(catalog_tokens)
    if query_set and query_set <= catalog_set:
        coverage = len(query_set) / max(len(catalog_set), 1)
        return min(0.98, 0.82 + coverage * 0.16)

    token_overlap = len(query_set & catalog_set) / max(len(query_set), 1)
    sequence_ratio = SequenceMatcher(None, query, catalog).ratio()
    return max(sequence_ratio, token_overlap * 0.88)


def size_equivalence_tokens(size: str) -> frozenset[str]:
    return size_equivalence_keys(size)


def product_catalog_profile(product: Product) -> tuple[str, str | None]:
    stored_size = (getattr(product, "size", None) or "").strip() or None
    if stored_size:
        base_name, _ = split_name_and_size(product.name)
        return base_name, normalize_size_text(stored_size)
    base_name, size = split_name_and_size(product.name)
    return base_name, size


@dataclass(frozen=True, slots=True)
class CatalogProfile:
    product: Product
    base_name: str
    size: str | None
    source: str


@dataclass(frozen=True, slots=True)
class ScoredCatalogMatch:
    profile: CatalogProfile
    name_score: float
    size_match: bool
    rank_score: int = 0


@dataclass(frozen=True, slots=True)
class CatalogMatchDiagnostics:
    catalog_match_count: int
    best_match_name: str | None
    best_match_score: float | None
    outcome: str
    failure_reason: str | None
    name_keyword_hits: tuple[str, ...]
    available_sizes_for_name: tuple[str, ...]
    top_matches: tuple[tuple[str, float, bool], ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "catalog_match_count": self.catalog_match_count,
            "best_match_name": self.best_match_name,
            "best_match_score": self.best_match_score,
            "outcome": self.outcome,
            "failure_reason": self.failure_reason,
            "name_keyword_hits": list(self.name_keyword_hits),
            "available_sizes_for_name": list(self.available_sizes_for_name),
            "top_matches": [
                {"name": name, "score": score, "size_match": size_match}
                for name, score, size_match in self.top_matches
            ],
        }


def iter_product_profiles(product: Product) -> list[CatalogProfile]:
    base_name, size = product_catalog_profile(product)
    profiles = [
        CatalogProfile(
            product=product,
            base_name=base_name,
            size=size,
            source="name",
        )
    ]
    for alias in product.aliases or []:
        alias_base, alias_size = split_name_and_size(alias)
        profiles.append(
            CatalogProfile(
                product=product,
                base_name=alias_base,
                size=alias_size,
                source="alias",
            )
        )
    return profiles


def base_name_similar_for_sized_query(query_name: str, catalog_name: str) -> bool:
    """Stage 1 when OCR size is present: structural name match, not a second fuzzy gate."""
    query = _normalize_name(query_name)
    catalog = _normalize_name(catalog_name)
    if not query or not catalog:
        return False
    if query == catalog:
        return True
    if catalog.startswith(f"{query} ") or catalog.startswith(query):
        return True
    if query.startswith(f"{catalog} "):
        return True

    query_tokens = query.split()
    catalog_tokens = catalog.split()
    query_set = set(query_tokens)
    catalog_set = set(catalog_tokens)
    if query_set and query_set <= catalog_set:
        return True
    if query_tokens and catalog_tokens and query_tokens[0] == catalog_tokens[0]:
        return True
    return False


def profile_effective_size(profile: CatalogProfile) -> str | None:
    if profile.size:
        return profile.size
    extracted, _ = extract_size_from_name(profile.product.name)
    return extracted


def normalize_catalog_search_text(value: str) -> str:
    """Compact comparable text: lower case, no separators, units stripped."""
    text = value.casefold().replace("×", "x").replace("х", "x")
    text = _SEARCH_UNIT_PATTERN.sub("", text)
    text = re.sub(r"[^\w]+", "", text, flags=re.UNICODE)
    return text


def composite_search_key(product_name: str, size: str | None) -> str:
    base = normalize_catalog_search_text(product_name)
    if size and str(size).strip():
        size_part = normalize_catalog_search_text(normalize_size_text(str(size).strip()))
        return f"{base}{size_part}"
    return base


def size_found_in_product_name(query_size: str, product_name: str) -> bool:
    compact_name = normalize_catalog_search_text(product_name)
    if not compact_name:
        return False

    for key in size_equivalence_keys(query_size):
        token = normalize_catalog_search_text(key)
        if token and token in compact_name:
            return True

    extracted, _ = extract_size_from_name(product_name)
    if extracted and sizes_equivalent(query_size, extracted):
        return True
    return False


def _product_stored_size(product: Product) -> str | None:
    stored = (getattr(product, "size", None) or "").strip()
    return normalize_size_text(stored) if stored else None


def score_catalog_profile(
    query_name: str,
    query_size: str | None,
    profile: CatalogProfile,
) -> tuple[int, float, bool]:
    """Return (rank_score, name_similarity, size_match)."""
    product = profile.product
    name_score = 0.0
    name_ok = False
    for catalog_name in profile_name_candidates(profile):
        score = name_similarity_score(query_name, catalog_name)
        if score > name_score:
            name_score = score
        if query_size:
            if base_name_similar_for_sized_query(query_name, catalog_name):
                name_ok = True
        elif score >= _MIN_NAME_SCORE:
            name_ok = True

    if not name_ok:
        return 0, name_score, False

    if query_size:
        query_comp = composite_search_key(query_name, query_size)
        catalog_comp = normalize_catalog_search_text(product.name)
        if query_comp and query_comp == catalog_comp:
            return _SCORE_NAME_EXACT + _SCORE_SIZE_IN_NAME, name_score, True

    rank_score = 0
    base_norm = _normalize_name(profile.base_name)
    query_norm = _normalize_name(query_name)
    if query_norm == base_norm or name_score >= 0.99:
        rank_score += _SCORE_NAME_EXACT
    else:
        rank_score += _SCORE_NAME_ONLY

    size_match = False
    if query_size:
        stored_size = _product_stored_size(product)
        if stored_size and sizes_equivalent(query_size, stored_size):
            rank_score += _SCORE_SIZE_FIELD
            size_match = True
        elif profile.size and sizes_equivalent(query_size, profile.size):
            rank_score += _SCORE_SIZE_FIELD
            size_match = True
        elif size_found_in_product_name(query_size, product.name):
            rank_score += _SCORE_SIZE_IN_NAME
            size_match = True

    return rank_score, name_score, size_match


def profile_name_candidates(profile: CatalogProfile) -> tuple[str, ...]:
    names: list[str] = []
    for candidate in (profile.base_name, profile.product.name):
        cleaned = candidate.strip()
        if cleaned and cleaned not in names:
            names.append(cleaned)
    return tuple(names)


def rank_catalog_matches(
    products: list[Product],
    *,
    query_name: str,
    query_size: str | None,
    min_name_score: float = _MIN_NAME_SCORE,
) -> list[ScoredCatalogMatch]:
    """Rank catalog rows by composite name/size score; keep only top-scoring ties."""
    del min_name_score  # retained for API compatibility; scoring uses _MIN_NAME_SCORE internally
    matches: list[ScoredCatalogMatch] = []
    seen_product_ids: set[object] = set()

    for product in products:
        best_for_product: ScoredCatalogMatch | None = None
        for profile in iter_product_profiles(product):
            rank_score, name_score, size_match = score_catalog_profile(
                query_name,
                query_size,
                profile,
            )
            if rank_score <= 0:
                continue

            candidate = ScoredCatalogMatch(
                profile=profile,
                name_score=name_score,
                size_match=size_match,
                rank_score=rank_score,
            )
            if best_for_product is None or candidate.rank_score > best_for_product.rank_score:
                best_for_product = candidate
            elif (
                candidate.rank_score == best_for_product.rank_score
                and candidate.name_score > best_for_product.name_score
            ):
                best_for_product = candidate

        if best_for_product is not None and product.id not in seen_product_ids:
            seen_product_ids.add(product.id)
            matches.append(best_for_product)

    matches.sort(
        key=lambda item: (
            -item.rank_score,
            -item.name_score,
            item.profile.product.name.casefold(),
            str(item.profile.product.id),
        )
    )

    if not matches:
        return matches

    best_rank = matches[0].rank_score
    if query_size:
        sized = [item for item in matches if item.size_match]
        if not sized:
            return []
        best_rank = sized[0].rank_score
        matches = [item for item in sized if item.rank_score == best_rank]
    else:
        best_rank = matches[0].rank_score
        matches = [item for item in matches if item.rank_score == best_rank]

    return matches


def find_name_keyword_hits(products: list[Product], query_name: str, *, limit: int = 12) -> list[str]:
    hits: list[str] = []
    seen: set[str] = set()
    for product in products:
        for profile in iter_product_profiles(product):
            if any(base_name_similar_for_sized_query(query_name, name) for name in profile_name_candidates(profile)):
                if product.name not in seen:
                    seen.add(product.name)
                    hits.append(product.name)
                    break
        if len(hits) >= limit:
            break
    return hits


def collect_sizes_for_name_keyword(products: list[Product], query_name: str) -> list[str]:
    sizes: list[str] = []
    seen: set[str] = set()
    for product in products:
        matched_name = False
        for profile in iter_product_profiles(product):
            if not any(base_name_similar_for_sized_query(query_name, name) for name in profile_name_candidates(profile)):
                continue
            matched_name = True
            effective = profile_effective_size(profile)
            if effective:
                token = normalize_size_text(effective)
                if token not in seen:
                    seen.add(token)
                    sizes.append(token)
        if not matched_name:
            continue
    return sorted(sizes, key=lambda value: (len(value), value.casefold()))


def build_match_diagnostics(
    products: list[Product],
    *,
    query_name: str,
    query_size: str | None,
    matches: list[ScoredCatalogMatch],
) -> CatalogMatchDiagnostics:
    top_matches = tuple(
        (item.profile.product.name, round(item.name_score, 4), item.size_match) for item in matches[:8]
    )
    best = matches[0] if matches else None
    if len(matches) == 1:
        outcome = "matched"
        failure_reason = None
    elif len(matches) > 1:
        outcome = "multiple"
        failure_reason = None
    else:
        outcome = "not_found"
        name_hits = find_name_keyword_hits(products, query_name)
        sizes = collect_sizes_for_name_keyword(products, query_name)
        if query_size and name_hits and sizes and not any(sizes_equivalent(query_size, size) for size in sizes):
            failure_reason = (
                f"По названию «{query_name}» найдено {len(name_hits)} товар(ов), "
                f"но размер «{query_size}» не совпал. Доступные размеры: {', '.join(sizes[:20])}."
            )
        elif name_hits:
            failure_reason = (
                f"По названию «{query_name}» найдено {len(name_hits)} товар(ов), "
                f"но размер «{query_size}» не совпал с доступными."
                if query_size
                else f"По названию «{query_name}» нет достаточно похожих товаров в каталоге."
            )
        else:
            failure_reason = f"В каталоге нет товаров, похожих на «{query_name}»."

    return CatalogMatchDiagnostics(
        catalog_match_count=len(matches),
        best_match_name=best.profile.product.name if best else None,
        best_match_score=round(best.name_score, 4) if best else None,
        outcome=outcome,
        failure_reason=failure_reason,
        name_keyword_hits=tuple(find_name_keyword_hits(products, query_name)),
        available_sizes_for_name=tuple(collect_sizes_for_name_keyword(products, query_name)),
        top_matches=top_matches,
    )


def line_matches_product(*, query_name: str, query_size: str | None, product: Product) -> bool:
    return bool(rank_catalog_matches([product], query_name=query_name, query_size=query_size))


def line_matches_catalog_entry(
    query_name: str,
    query_size: str | None,
    catalog_name: str,
    catalog_size: str | None,
) -> bool:
    if query_size:
        if not base_name_similar_for_sized_query(query_name, catalog_name):
            return False
        if catalog_size and sizes_equivalent(query_size, catalog_size):
            return True
        return size_found_in_product_name(query_size, catalog_name)
    return name_similarity_score(query_name, catalog_name) >= _MIN_NAME_SCORE


def _normalize_name(value: str) -> str:
    normalized = re.sub(r"[^\w]+", " ", value.casefold(), flags=re.UNICODE).strip()
    return re.sub(r"\s+", " ", normalized)


def _normalize_token(value: str) -> str:
    text = value.casefold().replace("×", "x").replace("х", "x")
    text = re.sub(r"\s+", " ", text.strip())
    return text
