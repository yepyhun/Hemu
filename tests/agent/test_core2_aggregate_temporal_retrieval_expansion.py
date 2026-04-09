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


class _FakeStore:
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
                },
            },
            {
                "object_id": "anchor-filler",
                "score": 1.0,
                "content": "I compared pantry inventory and recipe ideas that week.",
                "metadata": {
                    "question_id": "demo-q",
                    "session_index": 1,
                },
            },
        ]

    def search_raw_archive(self, query, *, max_items, namespace_classes, source_first, exact_phrase):
        return [
            {
                "raw_id": "raw-1",
                "session_id": "longmemeval:demo-q:session:1",
                "score": 5.0,
            }
        ]

    def search_turn_archive(self, query, *, max_items):
        return []

    def list_canonical_objects(self, *, include_inactive):
        return list(self._records)


def _route_plan(query: str) -> Core2RoutePlan:
    return Core2RoutePlan(
        query_family=QUERY_FAMILY_PERSONAL_RECALL,
        route_family=ROUTE_FAMILY_CURATED_MEMORY,
        query_mode="source_supported",
        retrieval_cap=6,
        delivery_view="compact",
    )


def _update_resolution_route_plan(query: str) -> Core2RoutePlan:
    return Core2RoutePlan(
        query_family=QUERY_FAMILY_UPDATE_RESOLUTION,
        route_family=ROUTE_FAMILY_CURATED_MEMORY,
        query_mode="source_supported",
        retrieval_cap=6,
        delivery_view="compact",
    )


def test_constituent_anchor_expansion_promotes_session_records_for_aggregate_temporal_queries():
    substrate = Core2HybridSubstrate(_FakeStore(), mode="on")
    query = (
        "How many days passed between the day I canceled my FarmFresh subscription "
        "and the day I did my online grocery shopping from Instacart?"
    )

    items, trace = substrate.search(
        query,
        route_plan=_route_plan(query),
        max_items=6,
        namespace_classes=["personal"],
        source_first=False,
        exact_phrase=False,
    )

    assert trace["constituent_expansions"] >= 2
    assert any((item.get("metadata") or {}).get("hybrid_scope") == "session_anchor" for item in items)
    assert any("FarmFresh subscription" in str(item.get("content") or "") for item in items)
    assert any("Instacart" in str(item.get("content") or "") for item in items)


def test_constituent_anchor_expansion_stays_off_for_non_aggregate_query():
    substrate = Core2HybridSubstrate(_FakeStore(), mode="on")
    query = "What did I compare that week?"

    items, trace = substrate.search(
        query,
        route_plan=_route_plan(query),
        max_items=6,
        namespace_classes=["personal"],
        source_first=False,
        exact_phrase=False,
    )

    assert trace["constituent_expansions"] == 0
    assert all((item.get("metadata") or {}).get("hybrid_scope") != "session_anchor" for item in items)


def test_constituent_anchor_expansion_allows_update_resolution_percentage_shape():
    substrate = Core2HybridSubstrate(_FakeStore(), mode="on")
    query = "What percentage of the countryside property's price is the cost of the renovations I plan to do on my current house?"

    items, trace = substrate.search(
        query,
        route_plan=_update_resolution_route_plan(query),
        max_items=6,
        namespace_classes=["personal"],
        source_first=False,
        exact_phrase=False,
    )

    assert trace["constituent_expansions"] >= 2
    assert any((item.get("metadata") or {}).get("hybrid_scope") == "session_anchor" for item in items)


def test_runtime_retrieve_candidates_records_constituent_expansion_note():
    runtime = Core2Runtime(":memory:", hybrid_substrate_mode="on")
    runtime.initialize("constituent-note")
    try:
        route_plan = build_route_plan(
            "How many days passed between the day I canceled my FarmFresh subscription and the day I did my online grocery shopping from Instacart?",
            mode="source_supported",
            operator=None,
            risk_class="standard",
            max_items=6,
        )
        runtime.hybrid_substrate.search = lambda *args, **kwargs: ([], {"raw_hits": 1, "turn_hits": 0, "constituent_expansions": 2})  # type: ignore[assignment]

        runtime._retrieve_candidates(
            "How many days passed between the day I canceled my FarmFresh subscription and the day I did my online grocery shopping from Instacart?",
            route_plan=route_plan,
        )

        assert "hybrid_constituent_expand" in list(route_plan.notes)
    finally:
        runtime.shutdown()
