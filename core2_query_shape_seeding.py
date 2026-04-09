from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

from agent.core2_query_signal_primitives import (
    build_legacy_aggregate_total_bundle,
    build_legacy_current_conflict_bundle,
    build_legacy_temporal_duration_bundle,
)
from agent.core2_types import (
    QUERY_FAMILY_FACTUAL_SUPPORTED,
    QUERY_FAMILY_PERSONAL_RECALL,
    QUERY_FAMILY_RELATION_MULTIHOP,
    QUERY_FAMILY_UPDATE_RESOLUTION,
)

_ALLOWED_QUERY_FAMILIES = {
    QUERY_FAMILY_PERSONAL_RECALL,
    QUERY_FAMILY_FACTUAL_SUPPORTED,
    QUERY_FAMILY_RELATION_MULTIHOP,
    QUERY_FAMILY_UPDATE_RESOLUTION,
}

_SHAPE_HINTS = (
    "between ",
    " after ",
    " first, ",
    " first ",
    " previous ",
    " more ",
    " less ",
    " ratio ",
    " percentage ",
    " percent ",
    " total ",
    " average ",
    " in total ",
    " days ago ",
    " weeks ago ",
    " months ago ",
    " years ago ",
    " days passed ",
    " how many days ",
    " how long ",
    " how many weeks ",
    " switch ",
    " switched ",
    " previously ",
    " this year ",
)

_NOISY_PHRASES = {
    "what",
    "which",
    "how many",
    "how much",
    "how long",
    "do i",
    "did i",
    "is my",
    "was my",
    "for me",
    "the day i",
    "the cost of",
    "the total number of",
    "the total amount i spent on",
}


@dataclass(frozen=True)
class QueryShapeSeedPlan:
    operator_family: str = ""
    arity: str = ""
    slots: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    seed_family: str = ""
    signal_family: str = ""
    seed_queries: List[str] = field(default_factory=list)

    @property
    def applicable(self) -> bool:
        return bool(self.operator_family and self.seed_queries)


def build_query_shape_seed_plan(query: str, *, route_plan) -> QueryShapeSeedPlan:
    if route_plan.query_family not in _ALLOWED_QUERY_FAMILIES:
        return QueryShapeSeedPlan()

    original = " ".join(str(query or "").strip().split())
    normalized = f" {original.lower()} "
    if not any(hint in normalized for hint in _SHAPE_HINTS) and not re.search(r"['\"][^'\"]+['\"]", original):
        return QueryShapeSeedPlan()

    for builder in (
        _build_temporal_elapsed_plan,
        _build_current_previous_plan,
        _build_pairwise_compare_plan,
        _build_aggregate_pair_plan,
    ):
        plan = builder(original)
        if plan.applicable:
            return plan

    return QueryShapeSeedPlan()


def build_query_shape_seed_queries(query: str, *, route_plan) -> List[str]:
    return list(build_query_shape_seed_plan(query, route_plan=route_plan).seed_queries)


def _build_temporal_elapsed_plan(query: str) -> QueryShapeSeedPlan:
    normalized = f" {query.lower()} "
    signal_bundle = build_legacy_temporal_duration_bundle(query)
    if not any(
        hint in normalized
        for hint in (
            " between ",
            " after ",
            " days ago ",
            " weeks ago ",
            " months ago ",
            " years ago ",
            " days passed ",
            " how long ",
        )
    ) and not signal_bundle.applicable:
        return QueryShapeSeedPlan()

    seeds: List[str] = []
    seeds.extend(_between_clauses(query))
    seeds.extend(_after_clauses(query))
    seeds.extend(_days_ago_clause(query))
    seeds.extend(_quoted_phrases(query))
    seeds.extend(signal_bundle.seed_queries)
    seed_queries = _dedupe_seed_queries(seeds)
    return QueryShapeSeedPlan(
        operator_family="temporal_elapsed",
        arity="pair",
        slots=["anchor_earlier", "anchor_later"],
        constraints=["temporal"],
        seed_family="temporal_anchor_pair",
        signal_family=signal_bundle.signal_family,
        seed_queries=seed_queries,
    )


def _build_pairwise_compare_plan(query: str) -> QueryShapeSeedPlan:
    normalized = f" {query.lower()} "
    if " first " not in normalized and " first," not in normalized and " more " not in normalized and " less " not in normalized:
        return QueryShapeSeedPlan()

    seeds: List[str] = []
    seeds.extend(_pairwise_first_clauses(query))
    seeds.extend(_quoted_phrases(query))
    if not seeds and any(hint in normalized for hint in (" more ", " less ")):
        seeds.extend(_comparison_focus_clauses(query))
    seed_queries = _dedupe_seed_queries(seeds)
    return QueryShapeSeedPlan(
        operator_family="pairwise_compare",
        arity="pair",
        slots=["operand_left", "operand_right"],
        constraints=["comparison"],
        seed_family="pairwise_seed",
        seed_queries=seed_queries,
    )


def _build_current_previous_plan(query: str) -> QueryShapeSeedPlan:
    normalized = f" {query.lower()} "
    signal_bundle = build_legacy_current_conflict_bundle(query)
    if " previous " not in normalized and not signal_bundle.applicable:
        return QueryShapeSeedPlan()
    seed_queries = _dedupe_seed_queries(_comparison_focus_clauses(query) + signal_bundle.seed_queries)
    return QueryShapeSeedPlan(
        operator_family="current_previous",
        arity="pair",
        slots=["previous_fact", "current_fact"],
        constraints=["temporal"],
        seed_family="previous_current_seed",
        signal_family=signal_bundle.signal_family,
        seed_queries=seed_queries,
    )


def _build_aggregate_pair_plan(query: str) -> QueryShapeSeedPlan:
    normalized = f" {query.lower()} "
    signal_bundle = build_legacy_aggregate_total_bundle(query)
    if not any(hint in normalized for hint in (" percentage ", " percent ", " ratio ", " average ", " total ", " in total ", " this year ")) and not signal_bundle.applicable:
        return QueryShapeSeedPlan()

    seeds: List[str] = []
    seeds.extend(_aggregate_operand_clauses(query))
    seeds.extend(_quoted_phrases(query))
    seeds.extend(signal_bundle.seed_queries)
    seed_queries = _dedupe_seed_queries(seeds)
    arity = "set" if " total " in normalized and len(seed_queries) > 2 else "pair"
    return QueryShapeSeedPlan(
        operator_family="aggregate_numeric",
        arity=arity,
        slots=["operand_left", "operand_right"] if arity == "pair" else ["operand_set"],
        constraints=["numeric", "scope"],
        seed_family="aggregate_operand_seed",
        signal_family=signal_bundle.signal_family,
        seed_queries=seed_queries,
    )


def _quoted_phrases(query: str) -> List[str]:
    return [match.group(1).strip() for match in re.finditer(r"['\"]([^'\"]{3,})['\"]", query) if match.group(1).strip()]


def _between_clauses(query: str) -> List[str]:
    match = re.search(r"\bbetween\s+(.+?)\s+and\s+(.+?)(?:\?|$)", query, flags=re.IGNORECASE)
    if not match:
        return []
    return [_clean_seed_phrase(match.group(1)), _clean_seed_phrase(match.group(2))]


def _after_clauses(query: str) -> List[str]:
    seeds: List[str] = []
    match = re.search(r"did it take(?:\s+for me)?\s+to\s+(.+?)\s+after\s+(.+?)(?:\?|$)", query, flags=re.IGNORECASE)
    if match:
        seeds.extend([_clean_seed_phrase(match.group(1)), _clean_seed_phrase(match.group(2))])
        return seeds
    match = re.search(r"\bafter\s+(.+?)(?:\?|$)", query, flags=re.IGNORECASE)
    if match:
        seeds.append(_clean_seed_phrase(match.group(1)))
    return seeds


def _pairwise_first_clauses(query: str) -> List[str]:
    lowered = query.lower()
    if " first " not in lowered and " first," not in lowered:
        return []
    if re.search(r"['\"][^'\"]+['\"]", query):
        return []
    split_match = re.search(r"\bfirst,\s+(.+?)\s+or\s+(.+?)(?:\?|$)", query, flags=re.IGNORECASE)
    if split_match:
        return [_clean_seed_phrase(split_match.group(1)), _clean_seed_phrase(split_match.group(2))]
    split_match = re.search(r"\bfirst\s+(.+?)\s+or\s+(.+?)(?:\?|$)", query, flags=re.IGNORECASE)
    if split_match:
        return [_clean_seed_phrase(split_match.group(1)), _clean_seed_phrase(split_match.group(2))]
    return []


def _days_ago_clause(query: str) -> List[str]:
    match = re.search(r"\bdays ago did i\s+(.+?)(?:\?|$)", query, flags=re.IGNORECASE)
    if not match:
        return []
    return [_clean_seed_phrase(match.group(1))]


def _comparison_focus_clauses(query: str) -> List[str]:
    normalized = " ".join(query.strip().split())
    lowered = normalized.lower()
    seeds: List[str] = []
    if " more " in lowered or " less " in lowered:
        words = normalized.split()
        focus = [
            word
            for word in words
            if word.lower() not in {"what", "is", "the", "to", "did", "i", "my", "for", "of", "or", "more", "less"}
        ]
        if focus:
            seeds.append(_clean_seed_phrase(" ".join(focus[:6])))
    if " previous " in lowered:
        after = normalized.split("previous", 1)[-1].strip()
        before = normalized.split("previous", 1)[0].strip()
        if after:
            seeds.append(_clean_seed_phrase(after))
        if before:
            seeds.append(_clean_seed_phrase(before))
    return seeds


def _aggregate_operand_clauses(query: str) -> List[str]:
    seeds: List[str] = []
    match = re.search(r"\bfrom\s+(.+?)\s+and\s+(.+?)(?:\?|$)", query, flags=re.IGNORECASE)
    if match:
        seeds.extend([_clean_seed_phrase(match.group(1)), _clean_seed_phrase(match.group(2))])
    match = re.search(r"\bof\s+(.+?)\s+is\s+(.+?)(?:\?|$)", query, flags=re.IGNORECASE)
    if match:
        seeds.extend([_clean_seed_phrase(match.group(1)), _clean_seed_phrase(match.group(2))])
    return seeds


def _clean_seed_phrase(value: str) -> str:
    cleaned = " ".join(str(value or "").strip().split())
    cleaned = re.sub(r"^[^A-Za-z0-9]+|[^A-Za-z0-9]+$", "", cleaned)
    lowered = cleaned.lower()
    for noisy in sorted(_NOISY_PHRASES, key=len, reverse=True):
        if lowered.startswith(noisy + " "):
            cleaned = cleaned[len(noisy) :].strip()
            lowered = cleaned.lower()
    return cleaned.strip(" ,.?;:()[]{}")


def _dedupe_seed_queries(seeds: List[str]) -> List[str]:
    deduped: List[str] = []
    seen = set()
    for seed in seeds:
        cleaned = " ".join(str(seed or "").strip().split())
        if len(cleaned) < 3:
            continue
        normalized = cleaned.casefold()
        if normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(cleaned)
    return deduped[:4]
