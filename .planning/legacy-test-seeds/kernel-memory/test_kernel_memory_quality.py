from __future__ import annotations

from agent.kernel_memory import KernelMemoryConfig
from agent.kernel_memory_quality import KernelMemoryQualityStore


def test_live_retrieval_records_hard_negative_when_grounding_is_missing(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        retrieval_live_telemetry_enabled=True,
        retrieval_live_telemetry_sample_percent=100,
    )
    store = KernelMemoryQualityStore(config)

    entry = store.record_live_retrieval(
        query="What exactly is the current rehab rule?",
        namespaces={"bestie"},
        result={
            "plan": {"response_mode": "source_supported", "budget_profile": "short_query", "max_records": 3, "max_chars": 1200},
            "routes": ["curated", "graph"],
            "items": [{"id": "cur_1", "route": "curated"}],
            "text": "partial context",
            "telemetry": {
                "route_item_counts": {"curated": 1, "graph": 0},
                "useful_count": 0,
                "retrieved_count": 1,
                "usefulness_rate": 0.0,
                "noise_rate": 1.0,
                "route_value_breakdown": {"curated": {"retrieved": 1, "useful": 0, "usefulness_rate": 0.0}},
            },
            "answer_packet": {
                "confidence_tier": "low",
                "delivery_mode": "abstain_or_ask",
                "should_abstain": True,
                "warnings": ["insufficient_grounding", "missing_answer_anchor"],
            },
            "evidence_chain": {
                "covered_facets": ["anchor"],
                "expected_facets": ["anchor", "answer_anchor", "source_support"],
                "chain_completeness_score": 0.33,
                "missing_link_penalty": 0.67,
                "cross_layer_consistency_score": 0.0,
            },
        },
    )

    snapshot = store.read_snapshot()
    hard_negatives = store.list_runs(run_type="hard_negative_retrieval")

    assert entry["answer_should_abstain"] is True
    assert entry["missing_facets"] == ["answer_anchor", "source_support"]
    assert hard_negatives
    assert hard_negatives[0]["missing_facets"] == ["answer_anchor", "source_support"]
    assert snapshot["last_hard_negative_retrieval"]["query_hash"] == entry["query_hash"]
    assert snapshot["last_hard_negative_retrieval"]["answer_warnings"] == [
        "insufficient_grounding",
        "missing_answer_anchor",
    ]


def test_live_retrieval_does_not_record_hard_negative_for_grounded_success(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        retrieval_live_telemetry_enabled=True,
        retrieval_live_telemetry_sample_percent=100,
    )
    store = KernelMemoryQualityStore(config)

    store.record_live_retrieval(
        query="What is Laura's current favorite quote?",
        namespaces={"bestie"},
        result={
            "plan": {"response_mode": "source_supported", "budget_profile": "short_query", "max_records": 3, "max_chars": 1200},
            "routes": ["curated", "semantic"],
            "items": [{"id": "cur_1", "route": "curated"}],
            "text": "good context",
            "telemetry": {
                "route_item_counts": {"curated": 1, "semantic": 1},
                "useful_count": 1,
                "retrieved_count": 1,
                "usefulness_rate": 1.0,
                "noise_rate": 0.0,
                "route_value_breakdown": {"curated": {"retrieved": 1, "useful": 1, "usefulness_rate": 1.0}},
            },
            "answer_packet": {
                "confidence_tier": "high",
                "delivery_mode": "confident",
                "should_abstain": False,
                "warnings": [],
            },
            "evidence_chain": {
                "covered_facets": ["anchor", "answer_anchor", "source_support"],
                "expected_facets": ["anchor", "answer_anchor", "source_support"],
                "chain_completeness_score": 1.0,
                "missing_link_penalty": 0.0,
                "cross_layer_consistency_score": 1.0,
            },
        },
    )

    assert store.list_runs(run_type="hard_negative_retrieval") == []


def test_hard_negative_summary_aggregates_missing_facets_and_routes(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
    )
    store = KernelMemoryQualityStore(config)

    store.append_run(
        run_type="hard_negative_retrieval",
        payload={
            "query_hash": "a",
            "routes": ["curated", "graph"],
            "answer_warnings": ["insufficient_grounding"],
            "missing_facets": ["answer_anchor", "source_support"],
        },
    )
    store.append_run(
        run_type="hard_negative_retrieval",
        payload={
            "query_hash": "b",
            "routes": ["graph"],
            "answer_warnings": ["missing_answer_anchor"],
            "missing_facets": ["answer_anchor"],
        },
    )

    summary = store.summarize_hard_negatives()

    assert summary["sample_size"] == 2
    assert summary["warning_counts"]["insufficient_grounding"] == 1
    assert summary["missing_facet_counts"]["answer_anchor"] == 2
    assert summary["route_counts"]["graph"] == 2
