from __future__ import annotations

from agent.kernel_memory import KernelMemoryConfig, KernelMemoryStore
from agent.kernel_memory_fusion import KernelMemoryFusionPolicy
from agent.kernel_memory_query_planner import KernelMemoryQueryPlanner


def test_query_planner_exact_source_mode_routes_only_to_source(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel", namespace="bestie")
    )
    planner = KernelMemoryQueryPlanner(store.config, store)

    plan = planner.plan(
        "Please quote the exact source for Hohmann transfer",
        max_records=3,
        max_chars=900,
        namespaces={"bestie"},
    )

    assert plan.response_mode == "exact_source_required"
    assert plan.budget_profile == "exact_source"
    assert plan.max_records == 2
    assert plan.max_chars == 900
    assert len(plan.routes) == 1
    assert plan.routes[0].route == "source"
    assert plan.routes[0].hard_requirement is True


def test_query_planner_boosts_graph_route_for_relationship_queries(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(
            enabled=True,
            root_dir=tmp_path / "kernel",
            namespace="bestie",
            curated_retrieval_only=False,
        )
    )
    planner = KernelMemoryQueryPlanner(store.config, store)

    plan = planner.plan(
        "What is the relationship between Earth and Mars?",
        max_records=4,
        max_chars=1200,
        namespaces={"bestie"},
    )
    weights = {route.route: route.weight for route in plan.routes}

    assert "graph_hint" in plan.reason_codes
    assert weights["graph"] > weights["semantic"]


def test_query_planner_uses_short_query_budget_profile(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        retrieval_budget_short_query_chars=24,
        retrieval_budget_short_query_max_records=2,
        retrieval_budget_short_query_max_chars=700,
    )
    store = KernelMemoryStore.from_config(config)
    planner = KernelMemoryQueryPlanner(config, store)

    plan = planner.plan(
        "orbital mechanics",
        max_records=6,
        max_chars=1600,
        namespaces={"bestie"},
    )

    assert plan.budget_profile == "short_query"
    assert plan.max_records == 2
    assert plan.max_chars == 700
    assert "short_query" in plan.reason_codes


def test_query_planner_curated_only_defaults_to_curated_route(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        curated_retrieval_only=True,
    )
    store = KernelMemoryStore.from_config(config)
    planner = KernelMemoryQueryPlanner(config, store)

    plan = planner.plan(
        "What do we know about Tomi's preferences?",
        max_records=4,
        max_chars=1200,
        namespaces={"bestie"},
    )

    assert [route.route for route in plan.routes] == ["curated"]


def test_query_planner_curated_only_keeps_graph_as_fallback_for_relationship_queries(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        curated_retrieval_only=True,
    )
    store = KernelMemoryStore.from_config(config)
    planner = KernelMemoryQueryPlanner(config, store)

    plan = planner.plan(
        "What is the relationship between Laura and Tomi?",
        max_records=4,
        max_chars=1200,
        namespaces={"bestie"},
    )

    assert [route.route for route in plan.routes] == ["curated", "graph"]


def test_query_planner_curated_only_keeps_semantic_fallback_for_current_state_queries(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        curated_retrieval_only=True,
    )
    store = KernelMemoryStore.from_config(config)
    planner = KernelMemoryQueryPlanner(config, store)

    plan = planner.plan(
        "What is Laura's current favorite quote?",
        max_records=4,
        max_chars=1200,
        namespaces={"bestie"},
    )

    assert [route.route for route in plan.routes] == ["curated", "semantic"]


def test_query_planner_classifies_exact_source_queries_as_local(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel", namespace="bestie")
    )
    planner = KernelMemoryQueryPlanner(store.config, store)

    plan = planner.plan(
        "Quote the exact source for Laura's current preference",
        max_records=4,
        max_chars=1200,
        namespaces={"bestie"},
    )

    assert plan.query_mode == "local"
    assert "query_mode:local" in plan.reason_codes


def test_query_planner_classifies_overview_queries_as_global(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(
            enabled=True,
            root_dir=tmp_path / "kernel",
            namespace="bestie",
            curated_retrieval_only=False,
        )
    )
    planner = KernelMemoryQueryPlanner(store.config, store)

    plan = planner.plan(
        "Give me a high level overview of what we know about orbital mechanics",
        max_records=4,
        max_chars=1200,
        namespaces={"bestie"},
    )
    weights = {route.route: route.weight for route in plan.routes}

    assert plan.query_mode == "global"
    assert "query_mode:global" in plan.reason_codes
    assert weights["curated"] > weights["semantic"]


def test_query_planner_defaults_generic_queries_to_hybrid(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel", namespace="bestie")
    )
    planner = KernelMemoryQueryPlanner(store.config, store)

    plan = planner.plan(
        "orbital mechanics transfer windows",
        max_records=4,
        max_chars=1200,
        namespaces={"bestie"},
    )

    assert plan.query_mode == "hybrid"
    assert "query_mode:hybrid" in plan.reason_codes


def test_query_planner_boosts_semantic_and_graph_for_event_queries(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(
            enabled=True,
            root_dir=tmp_path / "kernel",
            namespace="bestie",
            curated_retrieval_only=False,
        )
    )
    planner = KernelMemoryQueryPlanner(store.config, store)

    plan = planner.plan(
        "When did Laura start rehab progress?",
        max_records=4,
        max_chars=1200,
        namespaces={"bestie"},
    )
    weights = {route.route: route.weight for route in plan.routes}

    assert "event_hint" in plan.reason_codes
    assert weights["semantic"] > weights["curated"]
    assert any(anchor.anchor_type == "temporal" for anchor in plan.anchors)
    assert any(slot.slot_id == "event_core" for slot in plan.slot_reservations)


def test_query_planner_adds_current_state_slot_for_current_queries(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(
            enabled=True,
            root_dir=tmp_path / "kernel",
            namespace="bestie",
            curated_retrieval_only=False,
        )
    )
    planner = KernelMemoryQueryPlanner(store.config, store)

    plan = planner.plan(
        "What is Laura's current favorite quote?",
        max_records=4,
        max_chars=1200,
        namespaces={"bestie"},
    )

    assert any(anchor.anchor_type == "current_state" for anchor in plan.anchors)
    assert any(slot.slot_id == "current_state_core" for slot in plan.slot_reservations)
    assert "current_state_hint" in plan.reason_codes
    assert plan.response_mode == "source_supported"


def test_query_planner_adds_conflict_slots_for_conflict_queries(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(
            enabled=True,
            root_dir=tmp_path / "kernel",
            namespace="bestie",
            curated_retrieval_only=False,
        )
    )
    planner = KernelMemoryQueryPlanner(store.config, store)

    plan = planner.plan(
        "What changed and what conflicts with Laura's previous rehab state?",
        max_records=4,
        max_chars=1200,
        namespaces={"bestie"},
    )

    assert any(anchor.anchor_type == "conflict" for anchor in plan.anchors)
    assert any(slot.slot_id == "conflict_core" for slot in plan.slot_reservations)
    assert "conflict_hint" in plan.reason_codes
    assert any(route.route == "graph" for route in plan.routes)


def test_query_planner_allocates_per_route_budgets_instead_of_global_budget(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        curated_retrieval_only=False,
        retrieval_policy_order=["curated", "semantic", "graph", "source"],
    )
    store = KernelMemoryStore.from_config(config)
    planner = KernelMemoryQueryPlanner(config, store)

    plan = planner.plan(
        "orbital mechanics",
        max_records=6,
        max_chars=1200,
        namespaces={"bestie"},
        response_mode="source_supported",
    )

    assert all(route.max_records <= plan.max_records for route in plan.routes)


def test_fusion_policy_prioritizes_current_replacement_for_current_query(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(
            enabled=True,
            root_dir=tmp_path / "kernel",
            namespace="bestie",
            curated_retrieval_only=False,
        )
    )
    planner = KernelMemoryQueryPlanner(store.config, store)
    fusion = KernelMemoryFusionPolicy(store.config)

    plan = planner.plan(
        "What is the current favorite quote?",
        max_records=3,
        max_chars=900,
        namespaces={"bestie"},
    )
    route_results = {
        "semantic": {
            "items": [
                {
                    "id": "old",
                    "kind": "claim",
                    "route": "semantic",
                    "evidence_class": "semantic_lexical",
                    "status": "active",
                    "content": 'Favorite quote: "Old quote"',
                    "superseded_by": "new",
                },
                {
                    "id": "new",
                    "kind": "claim",
                    "route": "semantic",
                    "evidence_class": "semantic_lexical",
                    "status": "active",
                    "content": 'Favorite quote: "New quote"',
                    "supersedes": "old",
                    "metadata": {"conflict_signal": "correction"},
                    "updated_at": "2099-01-01T00:00:00+00:00",
                },
            ],
        },
    }

    fused = fusion.fuse(
        query=plan.normalized_query,
        plan=plan,
        route_results=route_results,
        max_records=2,
    )

    assert fused[0].record_id == "new"
    assert any(route.max_records < plan.max_records for route in plan.routes)
    assert sum(route.max_records for route in plan.routes) >= plan.max_records


def test_query_planner_extracts_entity_anchor_and_graph_slot(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(
            enabled=True,
            root_dir=tmp_path / "kernel",
            namespace="bestie",
            curated_retrieval_only=False,
        )
    )
    planner = KernelMemoryQueryPlanner(store.config, store)

    plan = planner.plan(
        "What happened with Laura and Tomi on Wednesday?",
        max_records=5,
        max_chars=1200,
        namespaces={"bestie"},
    )

    entity_values = {anchor.normalized_value for anchor in plan.anchors if anchor.anchor_type == "entity"}
    slot_ids = {slot.slot_id for slot in plan.slot_reservations}
    route_variants = {route.route: route.query_variant for route in plan.routes}
    assert "laura" in entity_values
    assert "tomi" in entity_values
    assert "entity_anchor" in slot_ids
    assert "Laura" in route_variants["graph"]
    assert "Tomi" in route_variants["graph"]


def test_query_planner_filters_discourse_verbs_from_entity_anchors(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(
            enabled=True,
            root_dir=tmp_path / "kernel",
            namespace="bestie",
            curated_retrieval_only=False,
        )
    )
    planner = KernelMemoryQueryPlanner(store.config, store)

    plan = planner.plan(
        "Please show me what Laura said about rehab",
        max_records=5,
        max_chars=1200,
        namespaces={"bestie"},
    )

    entity_values = {anchor.normalized_value for anchor in plan.anchors if anchor.anchor_type == "entity"}
    assert "laura" in entity_values
    assert "please" not in entity_values
    assert "show" not in entity_values


def test_query_planner_extracts_quoted_value_anchor(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(
            enabled=True,
            root_dir=tmp_path / "kernel",
            namespace="bestie",
            curated_retrieval_only=False,
        )
    )
    planner = KernelMemoryQueryPlanner(store.config, store)

    plan = planner.plan(
        'Is my favorite quote "Egyik szél sem jó annak a hajósnak"?',
        max_records=5,
        max_chars=1200,
        namespaces={"bestie"},
    )

    value_anchors = [anchor.value for anchor in plan.anchors if anchor.anchor_type == "value"]
    slot_ids = {slot.slot_id for slot in plan.slot_reservations}
    semantic_variant = next(route.query_variant for route in plan.routes if route.route == "semantic")
    assert value_anchors
    assert "Egyik szél sem jó annak a hajósnak" in value_anchors[0]
    assert "value_anchor" in slot_ids
    assert "Egyik szél sem jó annak a hajósnak" in semantic_variant


def test_query_planner_models_aggregate_count_queries_as_local_fact_objectives(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(
            enabled=True,
            root_dir=tmp_path / "kernel",
            namespace="bestie",
            curated_retrieval_only=False,
        )
    )
    planner = KernelMemoryQueryPlanner(store.config, store)

    plan = planner.plan(
        "How many model kits did I buy this year?",
        max_records=5,
        max_chars=1200,
        namespaces={"bestie"},
    )

    weights = {route.route: route.weight for route in plan.routes}
    assert plan.query_objective == "aggregate_count"
    assert plan.query_mode == "local"
    assert any(slot.slot_id == "aggregate_core" for slot in plan.slot_reservations)
    assert weights["semantic"] > weights["curated"]
    assert any(anchor.anchor_type == "aggregate" and anchor.normalized_value == "count" for anchor in plan.anchors)


def test_query_planner_models_relative_temporal_measure_queries_as_temporal_delta(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(
            enabled=True,
            root_dir=tmp_path / "kernel",
            namespace="bestie",
            curated_retrieval_only=False,
        )
    )
    planner = KernelMemoryQueryPlanner(store.config, store)

    plan = planner.plan(
        "How many months ago did I attend the Seattle International Film Festival?",
        max_records=5,
        max_chars=1200,
        namespaces={"bestie"},
    )

    assert plan.query_objective == "temporal_delta"
    assert plan.query_mode == "local"


def test_query_planner_keeps_time_anchored_event_queries_on_event_objective(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(
            enabled=True,
            root_dir=tmp_path / "kernel",
            namespace="bestie",
            curated_retrieval_only=False,
        )
    )
    planner = KernelMemoryQueryPlanner(store.config, store)

    plan = planner.plan(
        "What did I do with Rachel on the Wednesday two months ago?",
        max_records=5,
        max_chars=1200,
        namespaces={"bestie"},
    )

    assert plan.query_objective == "event"
    assert plan.query_mode == "local"


def test_query_planner_models_ordering_queries_with_named_targets_as_event_compare(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(
            enabled=True,
            root_dir=tmp_path / "kernel",
            namespace="bestie",
            curated_retrieval_only=False,
        )
    )
    planner = KernelMemoryQueryPlanner(store.config, store)

    plan = planner.plan(
        "Who became a parent first, Rachel or Alex?",
        max_records=5,
        max_chars=1200,
        namespaces={"bestie"},
    )

    assert plan.query_objective == "event_compare"
    assert plan.query_mode == "local"


def test_query_planner_models_aggregate_total_queries_with_total_variant(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(
            enabled=True,
            root_dir=tmp_path / "kernel",
            namespace="bestie",
            curated_retrieval_only=False,
        )
    )
    planner = KernelMemoryQueryPlanner(store.config, store)

    plan = planner.plan(
        "How much total did I spend on luxury items?",
        max_records=5,
        max_chars=1200,
        namespaces={"bestie"},
    )

    semantic_variant = next(route.query_variant for route in plan.routes if route.route == "semantic")
    assert plan.query_objective == "aggregate_total"
    assert any(slot.slot_id == "aggregate_core" for slot in plan.slot_reservations)
    assert "total" in semantic_variant.lower()
    assert "luxury items" in semantic_variant.lower()


def test_query_planner_models_average_queries_as_aggregate_average(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(
            enabled=True,
            root_dir=tmp_path / "kernel",
            namespace="bestie",
            curated_retrieval_only=False,
        )
    )
    planner = KernelMemoryQueryPlanner(store.config, store)

    plan = planner.plan(
        "What is the average GPA of my undergraduate and graduate studies?",
        max_records=5,
        max_chars=1200,
        namespaces={"bestie"},
    )

    assert plan.query_objective == "aggregate_average"
    assert plan.query_mode == "local"


def test_query_planner_models_recommendation_queries_as_preference_grounded(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(
            enabled=True,
            root_dir=tmp_path / "kernel",
            namespace="bestie",
            curated_retrieval_only=False,
        )
    )
    planner = KernelMemoryQueryPlanner(store.config, store)

    plan = planner.plan(
        "What should I do for fun this evening?",
        max_records=5,
        max_chars=1200,
        namespaces={"bestie"},
    )

    weights = {route.route: route.weight for route in plan.routes}
    semantic_variant = next(route.query_variant for route in plan.routes if route.route == "semantic")
    assert plan.query_objective == "recommendation"
    assert plan.query_mode == "local"
    assert any(slot.slot_id == "preference_core" for slot in plan.slot_reservations)
    assert weights["curated"] > weights["graph"]
    assert "this evening" in semantic_variant.lower()


def test_query_planner_models_temporal_compare_queries_as_event_compare(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(
            enabled=True,
            root_dir=tmp_path / "kernel",
            namespace="bestie",
            curated_retrieval_only=False,
        )
    )
    planner = KernelMemoryQueryPlanner(store.config, store)

    plan = planner.plan(
        "What happened first, the rehab milestone or the wedding news?",
        max_records=5,
        max_chars=1200,
        namespaces={"bestie"},
    )

    weights = {route.route: route.weight for route in plan.routes}
    assert plan.query_objective == "event_compare"
    assert plan.query_mode == "local"
    assert any(slot.slot_id == "event_core" for slot in plan.slot_reservations)
    assert weights["semantic"] > weights["curated"]


def test_fusion_policy_dedupes_duplicate_hits_and_prefers_higher_trust_route(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        curated_retrieval_only=False,
    )
    store = KernelMemoryStore.from_config(config)
    planner = KernelMemoryQueryPlanner(config, store)
    fusion = KernelMemoryFusionPolicy(config)
    plan = planner.plan(
        "Mars transfer",
        max_records=3,
        max_chars=1000,
        namespaces={"bestie"},
        response_mode="source_supported",
    )
    route_results = {
        "semantic": {
            "items": [
                {"id": "rec-1", "route": "semantic", "title": "Semantic", "summary": "semantic summary"},
            ]
        },
        "source": {
            "items": [
                {"id": "rec-1", "route": "source", "title": "Source", "content": "source excerpt"},
            ]
        },
    }

    fused = fusion.fuse(query="Mars transfer", plan=plan, route_results=route_results, max_records=3)

    assert len(fused) == 1
    assert fused[0].record_id == "rec-1"
    assert fused[0].route == "source"
    assert set(fused[0].routes) == {"semantic", "source"}


def test_fusion_policy_prioritizes_contradiction_items_for_conflict_queries(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        curated_retrieval_only=False,
    )
    store = KernelMemoryStore.from_config(config)
    planner = KernelMemoryQueryPlanner(config, store)
    fusion = KernelMemoryFusionPolicy(config)
    plan = planner.plan(
        "What is the conflict in the rollout rule?",
        max_records=3,
        max_chars=1000,
        namespaces={"bestie"},
        response_mode="source_supported",
    )
    route_results = {
        "graph": {
            "items": [
                {
                    "id": "rel-1",
                    "route": "graph",
                    "kind": "relation",
                    "relation_type": "contradicts",
                    "title": "Conflict edge",
                    "summary": "Old rule contradicts new rule.",
                    "evidence_class": "graph_fact",
                },
                {
                    "id": "evt-1",
                    "route": "graph",
                    "kind": "event",
                    "event_type": "milestone",
                    "title": "Regular rollout event",
                    "summary": "Rollout proceeded normally.",
                    "evidence_class": "graph_event",
                },
            ]
        }
    }

    fused = fusion.fuse(
        query="What is the conflict in the rollout rule?",
        plan=plan,
        route_results=route_results,
        max_records=3,
    )

    assert fused
    assert fused[0].record_id == "rel-1"
