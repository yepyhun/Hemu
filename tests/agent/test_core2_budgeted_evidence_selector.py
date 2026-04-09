from __future__ import annotations

from agent.core2_hybrid_substrate import Core2HybridSubstrate
from agent.core2_routing import build_route_plan
from agent.core2_runtime import Core2Runtime
from agent.core2_types import (
    Core2RoutePlan,
    QUERY_FAMILY_PERSONAL_RECALL,
    QUERY_FAMILY_UPDATE_RESOLUTION,
    ROUTE_FAMILY_CURATED_MEMORY,
)


class _TemporalStore:
    def __init__(self) -> None:
        self._records = [
            {
                "object_id": "raw-session",
                "source_raw_id": "raw-1",
                "score": 1.0,
                "content": "Session summary for groceries planning and subscriptions.",
                "metadata": {"question_id": "demo-q", "session_index": 1},
            },
            {
                "object_id": "anchor-cancel",
                "score": 1.0,
                "content": "I canceled my FarmFresh subscription on January 5, 2023.",
                "effective_from": "2023-01-05T00:00:00+00:00",
                "metadata": {
                    "question_id": "demo-q",
                    "session_index": 1,
                    "identity_key": "cancel.farmfresh",
                },
            },
            {
                "object_id": "anchor-instacart",
                "score": 1.0,
                "content": "I did my online grocery shopping from Instacart on February 28, 2023.",
                "effective_from": "2023-02-28T00:00:00+00:00",
                "metadata": {
                    "question_id": "demo-q",
                    "session_index": 1,
                    "identity_key": "shop.instacart",
                },
            },
            {
                "object_id": "anchor-filler",
                "score": 1.0,
                "content": "I compared pantry inventory and recipe ideas that week.",
                "metadata": {
                    "question_id": "demo-q",
                    "session_index": 1,
                    "identity_key": "filler.week",
                },
            },
        ]

    def search_raw_archive(self, query, *, max_items, namespace_classes, source_first, exact_phrase):
        return [{"raw_id": "raw-1", "session_id": "longmemeval:demo-q:session:1", "score": 5.0}]

    def search_turn_archive(self, query, *, max_items):
        return []

    def list_canonical_objects(self, *, include_inactive):
        return list(self._records)


class _NumericSafetyStore:
    def __init__(self) -> None:
        self._records = [
            {
                "object_id": "raw-session",
                "source_raw_id": "raw-2",
                "score": 1.0,
                "content": "Session summary for home renovation and property prices.",
                "metadata": {"question_id": "demo-q2", "session_index": 1},
            },
            {
                "object_id": "price-house",
                "score": 1.0,
                "content": "My current house renovations will cost $40,000.",
                "metadata": {
                    "question_id": "demo-q2",
                    "session_index": 1,
                    "identity_key": "renovation.cost",
                    "unit": "money",
                    "scope": "house",
                },
            },
            {
                "object_id": "price-country",
                "score": 1.0,
                "content": "The countryside property costs 250000 euros.",
                "metadata": {
                    "question_id": "demo-q2",
                    "session_index": 1,
                    "identity_key": "country.price",
                    "unit": "euros",
                    "scope": "country",
                },
            },
        ]

    def search_raw_archive(self, query, *, max_items, namespace_classes, source_first, exact_phrase):
        return [{"raw_id": "raw-2", "session_id": "longmemeval:demo-q2:session:1", "score": 5.0}]

    def search_turn_archive(self, query, *, max_items):
        return []

    def list_canonical_objects(self, *, include_inactive):
        return list(self._records)


def _route_plan() -> Core2RoutePlan:
    return Core2RoutePlan(
        query_family=QUERY_FAMILY_PERSONAL_RECALL,
        route_family=ROUTE_FAMILY_CURATED_MEMORY,
        query_mode="source_supported",
        retrieval_cap=6,
        delivery_view="compact",
    )


def _update_resolution_route_plan() -> Core2RoutePlan:
    return Core2RoutePlan(
        query_family=QUERY_FAMILY_UPDATE_RESOLUTION,
        route_family=ROUTE_FAMILY_CURATED_MEMORY,
        query_mode="source_supported",
        retrieval_cap=6,
        delivery_view="compact",
    )


def test_budgeted_selector_prefers_complementary_temporal_anchors():
    substrate = Core2HybridSubstrate(_TemporalStore(), mode="on")
    query = (
        "How many days passed between the day I canceled my FarmFresh subscription "
        "and the day I did my online grocery shopping from Instacart?"
    )

    items, trace = substrate.search(
        query,
        route_plan=_route_plan(),
        max_items=3,
        namespace_classes=["personal"],
        source_first=False,
        exact_phrase=False,
    )

    session_anchor_items = [item for item in items if (item.get("metadata") or {}).get("hybrid_scope") == "session_anchor"]
    assert trace["selector_expansions"] >= 2
    assert trace["selector_slot_coverage"] >= 2
    assert {item["object_id"] for item in session_anchor_items} == {"anchor-cancel", "anchor-instacart"}
    assert all((item.get("metadata") or {}).get("hybrid_selector") == "budgeted" for item in session_anchor_items)


def test_budgeted_selector_abstains_on_incompatible_numeric_units():
    substrate = Core2HybridSubstrate(_NumericSafetyStore(), mode="on")
    query = "What percentage of the countryside property's price is the cost of the renovations I plan to do on my current house?"

    items, trace = substrate.search(
        query,
        route_plan=_update_resolution_route_plan(),
        max_items=6,
        namespace_classes=["personal"],
        source_first=False,
        exact_phrase=False,
    )

    assert trace["selector_expansions"] == 0
    assert trace["aggregation_safety_abstentions"] == 1
    assert all((item.get("metadata") or {}).get("hybrid_scope") != "session_anchor" for item in items)


def test_runtime_retrieve_candidates_records_budgeted_selector_and_safety_notes():
    runtime = Core2Runtime(":memory:", hybrid_substrate_mode="on")
    runtime.initialize("selector-note")
    try:
        route_plan = build_route_plan(
            "What percentage of the countryside property's price is the cost of the renovations I plan to do on my current house?",
            mode="source_supported",
            operator=None,
            risk_class="standard",
            max_items=6,
        )
        runtime.hybrid_substrate.search = lambda *args, **kwargs: (  # type: ignore[assignment]
            [],
            {
                "raw_hits": 1,
                "turn_hits": 0,
                "constituent_expansions": 0,
                "selector_expansions": 2,
                "aggregation_safety_abstentions": 1,
            },
        )

        runtime._retrieve_candidates(
            "What percentage of the countryside property's price is the cost of the renovations I plan to do on my current house?",
            route_plan=route_plan,
        )

        notes = list(route_plan.notes)
        assert "hybrid_budgeted_selector" in notes
        assert "hybrid_aggregation_safety_abstain" in notes
    finally:
        runtime.shutdown()
