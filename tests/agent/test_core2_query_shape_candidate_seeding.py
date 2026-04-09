from __future__ import annotations

from agent.core2_hybrid_substrate import Core2HybridSubstrate
from agent.core2_query_shape_seeding import build_query_shape_seed_plan
from agent.core2_routing import build_route_plan
from agent.core2_runtime import Core2Runtime
from agent.core2_types import (
    Core2RoutePlan,
    QUERY_FAMILY_PERSONAL_RECALL,
    QUERY_FAMILY_UPDATE_RESOLUTION,
    ROUTE_FAMILY_CURATED_MEMORY,
)


class _SeedOnlyStore:
    def __init__(self) -> None:
        self._records = [
            {
                "object_id": "farmfresh",
                "source_raw_id": "raw-farmfresh",
                "score": 1.0,
                "content": "I canceled my FarmFresh subscription on January 5, 2023.",
                "metadata": {"question_id": "demo-q", "session_index": 1},
            },
            {
                "object_id": "instacart",
                "source_raw_id": "raw-instacart",
                "score": 1.0,
                "content": "I did my online grocery shopping from Instacart on February 28, 2023.",
                "metadata": {"question_id": "demo-q", "session_index": 1},
            },
        ]

    def search_raw_archive(self, query, *, max_items, namespace_classes, source_first, exact_phrase):
        lowered = str(query or "").lower()
        if "how many days passed" in lowered:
            return []
        hits = []
        if "farmfresh" in lowered:
            hits.append({"raw_id": "raw-farmfresh", "session_id": "longmemeval:demo-q:session:1", "score": 4.0})
        if "instacart" in lowered:
            hits.append({"raw_id": "raw-instacart", "session_id": "longmemeval:demo-q:session:1", "score": 4.0})
        return hits

    def search_turn_archive(self, query, *, max_items):
        return []

    def list_canonical_objects(self, *, include_inactive):
        return list(self._records)


class _AggregateSeedStore:
    def __init__(self) -> None:
        self._records = [
            {
                "object_id": "country-price",
                "source_raw_id": "raw-country",
                "score": 1.0,
                "content": "The countryside property costs 250000 euros.",
                "metadata": {"question_id": "demo-q2", "session_index": 1},
            },
            {
                "object_id": "renovation-cost",
                "source_raw_id": "raw-renovation",
                "score": 1.0,
                "content": "My current house renovations will cost 40000 euros.",
                "metadata": {"question_id": "demo-q2", "session_index": 1},
            },
        ]

    def search_raw_archive(self, query, *, max_items, namespace_classes, source_first, exact_phrase):
        lowered = str(query or "").lower()
        if "what percentage of the countryside property's price" in lowered:
            return []
        hits = []
        if "countryside property" in lowered:
            hits.append({"raw_id": "raw-country", "session_id": "longmemeval:demo-q2:session:1", "score": 4.0})
        if "renovations i plan to do on my current house" in lowered or "renovations will cost" in lowered:
            hits.append({"raw_id": "raw-renovation", "session_id": "longmemeval:demo-q2:session:1", "score": 4.0})
        return hits

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


def test_query_shape_seed_plan_detects_temporal_operator_and_slots():
    plan = build_query_shape_seed_plan(
        (
            "How many days passed between the day I canceled my FarmFresh subscription "
            "and the day I did my online grocery shopping from Instacart?"
        ),
        route_plan=_route_plan(),
    )

    assert plan.applicable is True
    assert plan.operator_family == "temporal_elapsed"
    assert plan.arity == "pair"
    assert plan.slots == ["anchor_earlier", "anchor_later"]
    assert plan.seed_family == "temporal_anchor_pair"
    assert any("FarmFresh" in query for query in plan.seed_queries)
    assert any("Instacart" in query for query in plan.seed_queries)


def test_query_shape_seed_plan_detects_aggregate_numeric_schema():
    plan = build_query_shape_seed_plan(
        "What percentage of the countryside property's price is the cost of the renovations I plan to do on my current house?",
        route_plan=_update_resolution_route_plan(),
    )

    assert plan.applicable is True
    assert plan.operator_family == "aggregate_numeric"
    assert plan.arity == "pair"
    assert plan.seed_family == "aggregate_operand_seed"
    assert len(plan.seed_queries) >= 2


def test_query_shape_seed_plan_detects_pairwise_compare_schema():
    plan = build_query_shape_seed_plan(
        "Which event came first, the workshop or the webinar?",
        route_plan=_route_plan(),
    )

    assert plan.applicable is True
    assert plan.operator_family == "pairwise_compare"
    assert plan.arity == "pair"
    assert plan.seed_family == "pairwise_seed"
    assert len(plan.seed_queries) == 2
    assert any("workshop" in query.lower() for query in plan.seed_queries)
    assert any("webinar" in query.lower() for query in plan.seed_queries)


def test_query_shape_seed_plan_detects_current_previous_schema():
    plan = build_query_shape_seed_plan(
        "What was my previous spirituality stance?",
        route_plan=_route_plan(),
    )

    assert plan.applicable is True
    assert plan.operator_family == "current_previous"
    assert plan.arity == "pair"
    assert plan.seed_family == "previous_current_seed"
    assert "previous_fact" in plan.slots
    assert any("spirituality stance" in query.lower() for query in plan.seed_queries)


def test_query_shape_seed_plan_uses_legacy_temporal_duration_primitive_for_weeks_ago():
    plan = build_query_shape_seed_plan(
        "How many weeks ago did I meet up with my aunt and receive the crystal chandelier?",
        route_plan=_route_plan(),
    )

    assert plan.applicable is True
    assert plan.operator_family == "temporal_elapsed"
    assert plan.signal_family == "legacy_temporal_duration"
    assert any("meet up with my aunt" in query.lower() for query in plan.seed_queries)


def test_query_shape_seed_plan_uses_legacy_aggregate_total_primitive_for_total_count():
    plan = build_query_shape_seed_plan(
        "How many days did I take social media breaks in total?",
        route_plan=_route_plan(),
    )

    assert plan.applicable is True
    assert plan.operator_family == "aggregate_numeric"
    assert plan.signal_family == "legacy_aggregate_total"
    assert any("social media breaks" in query.lower() for query in plan.seed_queries)


def test_query_shape_seed_plan_uses_legacy_current_conflict_primitive_for_switch_query():
    plan = build_query_shape_seed_plan(
        "For the coffee-to-water ratio in my French press, did I switch to more water per tablespoon of coffee, or less?",
        route_plan=_update_resolution_route_plan(),
    )

    assert plan.applicable is True
    assert plan.operator_family == "current_previous"
    assert plan.signal_family == "legacy_current_conflict"
    assert any("coffee-to-water ratio in my french press" in query.lower() for query in plan.seed_queries)


def test_query_shape_seed_expansion_opens_candidates_when_full_query_misses():
    substrate = Core2HybridSubstrate(_SeedOnlyStore(), mode="on")
    query = (
        "How many days passed between the day I canceled my FarmFresh subscription "
        "and the day I did my online grocery shopping from Instacart?"
    )

    items, trace = substrate.search(
        query,
        route_plan=_route_plan(),
        max_items=4,
        namespace_classes=["personal"],
        source_first=False,
        exact_phrase=False,
    )

    assert trace["query_shape_operator_family"] == "temporal_elapsed"
    assert trace["query_shape_seed_family"] == "temporal_anchor_pair"
    assert trace["query_shape_slot_count"] == 2
    assert trace["query_shape_seed_expansions"] >= 2
    assert {item["object_id"] for item in items} == {"farmfresh", "instacart"}
    assert all((item.get("metadata") or {}).get("hybrid_seed_family") == "temporal_anchor_pair" for item in items)


def test_query_shape_seed_expansion_opens_aggregate_operands_when_full_query_misses():
    substrate = Core2HybridSubstrate(_AggregateSeedStore(), mode="on")
    query = "What percentage of the countryside property's price is the cost of the renovations I plan to do on my current house?"

    items, trace = substrate.search(
        query,
        route_plan=_update_resolution_route_plan(),
        max_items=4,
        namespace_classes=["personal"],
        source_first=False,
        exact_phrase=False,
    )

    assert trace["query_shape_operator_family"] == "aggregate_numeric"
    assert trace["query_shape_seed_family"] == "aggregate_operand_seed"
    assert trace["query_shape_slot_count"] == 2
    assert trace["query_shape_seed_expansions"] >= 2
    assert {item["object_id"] for item in items} == {"country-price", "renovation-cost"}


def test_runtime_retrieve_candidates_records_query_shape_schema_note():
    runtime = Core2Runtime(":memory:", hybrid_substrate_mode="on")
    runtime.initialize("query-shape-note")
    try:
        route_plan = build_route_plan(
            "How many days passed between the day I canceled my FarmFresh subscription and the day I did my online grocery shopping from Instacart?",
            mode="source_supported",
            operator=None,
            risk_class="standard",
            max_items=6,
        )
        runtime.hybrid_substrate.search = lambda *args, **kwargs: (  # type: ignore[assignment]
            [],
            {
                "raw_hits": 0,
                "turn_hits": 0,
                "query_shape_operator_family": "temporal_elapsed",
                "query_shape_signal_family": "legacy_temporal_duration",
                "query_shape_slot_count": 2,
                "query_shape_seed_expansions": 2,
            },
        )

        runtime._retrieve_candidates(
            "How many days passed between the day I canceled my FarmFresh subscription and the day I did my online grocery shopping from Instacart?",
            route_plan=route_plan,
        )

        notes = list(route_plan.notes)
        assert "hybrid_query_shape_schema" in notes
        assert "hybrid_query_signal_primitive" in notes
        assert "hybrid_query_shape_seed" in notes
    finally:
        runtime.shutdown()
