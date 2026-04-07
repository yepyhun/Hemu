from __future__ import annotations

import re
from typing import Optional

from agent.core2_types import (
    Core2RoutePlan,
    DELIVERY_VIEW_EXPLORATORY_FULL,
    DELIVERY_VIEW_FINAL_COMPACT,
    DELIVERY_VIEW_SUPPORTED_COMPACT,
    MODE_AUTO,
    MODE_COMPACT_MEMORY,
    MODE_EXACT_SOURCE_REQUIRED,
    MODE_EXPLORATORY_FULL,
    MODE_SOURCE_SUPPORTED,
    QUERY_FAMILY_EXACT_LOOKUP,
    QUERY_FAMILY_EXPLORATORY_DISCOVERY,
    QUERY_FAMILY_FACTUAL_SUPPORTED,
    QUERY_FAMILY_HIGH_RISK_STRICT,
    QUERY_FAMILY_PERSONAL_RECALL,
    QUERY_FAMILY_RELATION_MULTIHOP,
    QUERY_FAMILY_UPDATE_RESOLUTION,
    ROUTE_FAMILY_ASSOCIATION_GRAPH,
    ROUTE_FAMILY_CURATED_MEMORY,
    ROUTE_FAMILY_SEMANTIC_FIRST,
    ROUTE_FAMILY_SOURCE_FIRST,
)


PERSONAL_HINTS = {
    "my",
    "me",
    "i",
    "prefer",
    "preference",
    "timezone",
    "role",
    "setup",
    "favorite",
    "favourite",
}
RELATION_HINTS = {
    "related",
    "relationship",
    "between",
    "connected",
    "depends",
    "dependency",
    "linked",
    "reports",
    "owner",
}
UPDATE_HINTS = {
    "current",
    "latest",
    "newest",
    "updated",
    "changed",
    "change",
    "version",
    "superseded",
    "previous",
    "before",
    "after",
    "as of",
    "valid",
}
EXPLORATORY_HINTS = {
    "explore",
    "discovery",
    "discover",
    "overview",
    "theme",
    "themes",
    "broad",
    "survey",
}
PERSONAL_ACTIVITY_HINTS = {
    "reading history",
    "finished reading",
    "books finished",
    "finished first",
    "read first",
}
PERSONAL_COMPARE_TEMPORAL_HINTS = {
    " first ",
    " last ",
    " before ",
    " after ",
    " earlier ",
    " later ",
    " order ",
    " compare ",
    " finished ",
}

CONVERSATION_REFERENCE_HINTS = {
    "previous conversation",
    "check back",
    "do you remember",
    "remember what",
    "remember which",
    "used as an example",
    "used as example",
}

CONVERSATION_REFERENCE_TARGET_HINTS = {
    "show",
    "movie",
    "series",
    "title",
    "example",
    "mentioned",
}


def _normalized_mode(mode: str | None) -> str:
    normalized = (mode or MODE_AUTO).strip().lower()
    if normalized not in {MODE_AUTO, MODE_EXACT_SOURCE_REQUIRED, MODE_SOURCE_SUPPORTED, MODE_COMPACT_MEMORY, MODE_EXPLORATORY_FULL}:
        return MODE_AUTO
    return normalized


def is_conversation_reference_query(query: str) -> bool:
    normalized_query = f" {' '.join((query or '').strip().lower().split())} "
    has_reference_signal = any(f" {hint} " in normalized_query for hint in CONVERSATION_REFERENCE_HINTS)
    has_target_signal = any(f" {hint} " in normalized_query for hint in CONVERSATION_REFERENCE_TARGET_HINTS)
    return has_reference_signal and has_target_signal


def infer_query_family(query: str, *, mode: str | None, operator: Optional[str], risk_class: str) -> str:
    normalized_mode = _normalized_mode(mode)
    normalized_query = " ".join((query or "").strip().lower().split())
    normalized_risk = (risk_class or "standard").strip().lower()

    if normalized_risk in {"high", "medical", "legal"}:
        return QUERY_FAMILY_HIGH_RISK_STRICT
    if normalized_mode == MODE_EXACT_SOURCE_REQUIRED:
        return QUERY_FAMILY_EXACT_LOOKUP
    if normalized_mode == MODE_EXPLORATORY_FULL:
        return QUERY_FAMILY_EXPLORATORY_DISCOVERY
    if is_conversation_reference_query(query):
        return QUERY_FAMILY_PERSONAL_RECALL

    if any(hint in normalized_query for hint in UPDATE_HINTS):
        return QUERY_FAMILY_UPDATE_RESOLUTION
    if any(hint in normalized_query for hint in RELATION_HINTS):
        return QUERY_FAMILY_RELATION_MULTIHOP
    if any(hint in normalized_query for hint in EXPLORATORY_HINTS):
        return QUERY_FAMILY_EXPLORATORY_DISCOVERY
    if any(hint in normalized_query for hint in PERSONAL_ACTIVITY_HINTS):
        return QUERY_FAMILY_PERSONAL_RECALL
    if operator in {"count", "aggregate"}:
        return QUERY_FAMILY_FACTUAL_SUPPORTED
    if any(f" {hint} " in f" {normalized_query} " for hint in PERSONAL_HINTS):
        return QUERY_FAMILY_PERSONAL_RECALL
    if normalized_mode == MODE_COMPACT_MEMORY:
        return QUERY_FAMILY_PERSONAL_RECALL
    return QUERY_FAMILY_FACTUAL_SUPPORTED


def resolve_query_mode(query_family: str, *, requested_mode: str | None) -> str:
    normalized_mode = _normalized_mode(requested_mode)
    if normalized_mode != MODE_AUTO:
        return normalized_mode

    if query_family == QUERY_FAMILY_EXACT_LOOKUP:
        return MODE_EXACT_SOURCE_REQUIRED
    if query_family in {QUERY_FAMILY_HIGH_RISK_STRICT, QUERY_FAMILY_FACTUAL_SUPPORTED, QUERY_FAMILY_UPDATE_RESOLUTION, QUERY_FAMILY_RELATION_MULTIHOP}:
        return MODE_SOURCE_SUPPORTED
    if query_family == QUERY_FAMILY_EXPLORATORY_DISCOVERY:
        return MODE_EXPLORATORY_FULL
    return MODE_COMPACT_MEMORY


def build_route_plan(query: str, *, mode: str | None, operator: Optional[str], risk_class: str, max_items: int) -> Core2RoutePlan:
    query_family = infer_query_family(query, mode=mode, operator=operator, risk_class=risk_class)
    query_mode = resolve_query_mode(query_family, requested_mode=mode)
    normalized_query = f" {re.sub(r'[^a-z0-9]+', ' ', (query or '').strip().lower())} "
    personal_compare_temporal = any(hint in normalized_query for hint in PERSONAL_COMPARE_TEMPORAL_HINTS)

    if query_family == QUERY_FAMILY_EXACT_LOOKUP:
        return Core2RoutePlan(
            query_family=query_family,
            route_family=ROUTE_FAMILY_SOURCE_FIRST,
            query_mode=query_mode,
            retrieval_cap=min(max_items, 3),
            delivery_view=DELIVERY_VIEW_SUPPORTED_COMPACT,
            strict_grounding=True,
            notes=["Prefer exact lexical/source matches and require precise grounding."],
        )
    if query_family == QUERY_FAMILY_HIGH_RISK_STRICT:
        return Core2RoutePlan(
            query_family=query_family,
            route_family=ROUTE_FAMILY_SOURCE_FIRST,
            query_mode=query_mode,
            retrieval_cap=min(max_items, 4),
            delivery_view=DELIVERY_VIEW_SUPPORTED_COMPACT,
            strict_grounding=True,
            temporal_strict=True,
            notes=["High-risk route: source-first, temporal validation, contradiction checks."],
        )
    if query_family == QUERY_FAMILY_UPDATE_RESOLUTION:
        return Core2RoutePlan(
            query_family=query_family,
            route_family=ROUTE_FAMILY_SOURCE_FIRST,
            query_mode=query_mode,
            retrieval_cap=min(max_items, 4),
            delivery_view=DELIVERY_VIEW_SUPPORTED_COMPACT,
            strict_grounding=True,
            temporal_strict=True,
            completeness_required=True,
            notes=["Resolve currentness through temporal and supersession-aware selection."],
        )
    if query_family == QUERY_FAMILY_RELATION_MULTIHOP:
        return Core2RoutePlan(
            query_family=query_family,
            route_family=ROUTE_FAMILY_ASSOCIATION_GRAPH,
            query_mode=query_mode,
            retrieval_cap=min(max_items, 6),
            delivery_view=DELIVERY_VIEW_SUPPORTED_COMPACT,
            completeness_required=True,
            graph_hops=1,
            notes=["Use bounded association expansion and verify evidence chain completeness."],
        )
    if query_family == QUERY_FAMILY_EXPLORATORY_DISCOVERY:
        return Core2RoutePlan(
            query_family=query_family,
            route_family=ROUTE_FAMILY_ASSOCIATION_GRAPH,
            query_mode=query_mode,
            retrieval_cap=min(max_items, 8),
            delivery_view=DELIVERY_VIEW_EXPLORATORY_FULL,
            graph_hops=1,
            notes=["Exploratory route may broaden the candidate pool but must remain bounded."],
        )
    if query_family == QUERY_FAMILY_PERSONAL_RECALL:
        return Core2RoutePlan(
            query_family=query_family,
            route_family=ROUTE_FAMILY_CURATED_MEMORY,
            query_mode=query_mode,
            retrieval_cap=min(max_items, 6 if personal_compare_temporal else 12),
            delivery_view=DELIVERY_VIEW_SUPPORTED_COMPACT if personal_compare_temporal else DELIVERY_VIEW_FINAL_COMPACT,
            notes=[
                "Prefer compact curated memory for personal recall unless evidence forces supported mode."
                if not personal_compare_temporal
                else "For compare/timeline personal recall, keep retrieval bounded and prefer temporally explicit curated memory."
            ],
        )
    return Core2RoutePlan(
        query_family=QUERY_FAMILY_FACTUAL_SUPPORTED,
        route_family=ROUTE_FAMILY_SEMANTIC_FIRST,
        query_mode=query_mode,
        retrieval_cap=min(max_items, 6),
        delivery_view=DELIVERY_VIEW_SUPPORTED_COMPACT,
        notes=["Use bounded semantic-first recall with grounding refs preserved."],
    )
