from __future__ import annotations

import json

from agent.core2_routing import build_route_plan, infer_query_family
from agent.core2_runtime import Core2Runtime
from agent.core2_types import EDGE_DERIVED_FROM
from plugins.memory import load_memory_provider


def _init_core2(tmp_path, session_id: str = "core2-routing"):
    provider = load_memory_provider("core2")
    assert provider is not None
    provider.initialize(session_id, hermes_home=str(tmp_path), platform="cli")
    return provider


def test_personal_compact_query_uses_curated_route(tmp_path):
    provider = _init_core2(tmp_path)

    json.loads(
        provider.handle_tool_call(
            "core2_remember",
            {
                "content": "My timezone is Europe/Budapest and I prefer concise answers.",
                "title": "profile",
                "namespace": "personal",
                "risk_class": "standard",
                "language": "en",
            },
        )
    )

    payload = json.loads(provider.handle_tool_call("core2_recall", {"query": "What is my timezone?", "mode": "compact_memory"}))

    assert payload["abstained"] is False
    assert payload["query_family"] == "personal_recall"
    assert payload["route_family"] == "curated_memory_view"
    assert payload["route_plan"]["delivery_view"] == "final_compact"
    assert payload["answer_type"] == "compact_memory"

    provider.shutdown()


def test_runtime_fact_first_recall_prefers_digested_attribute_record():
    runtime = Core2Runtime(":memory:")
    runtime.initialize("fact-first-role")
    runtime.ingest_note(
        "The role of good documentation in delivery work is discussed at length in this noisy note.",
        title="noise",
        namespace="personal",
        risk_class="standard",
        language="en",
    )
    runtime.ingest_note(
        "Current role: staff engineer.",
        title="profile",
        namespace="personal",
        risk_class="standard",
        language="en",
    )

    packet = runtime.recall("What is my current role?", mode="source_supported", operator=None, risk_class="standard", max_items=6)

    assert packet.abstained is False
    assert "fact_first_hit" in list(packet.route_plan.get("notes") or [])
    assert packet.items[0].metadata.get("digest_fact") is True
    assert packet.items[0].metadata.get("fact_key") == "attribute.occupation.current"
    assert packet.items[0].metadata.get("retrieval_path") == "fact_first"
    assert packet.items[0].title == "Current occupation"

    runtime.shutdown()


def test_exact_lookup_uses_source_first_route(tmp_path):
    provider = _init_core2(tmp_path, session_id="core2-routing-exact")

    json.loads(
        provider.handle_tool_call(
            "core2_remember",
            {
                "content": "Release note 12 documents the sunset date for endpoint v1.",
                "title": "release note 12",
                "namespace": "library",
                "risk_class": "standard",
                "language": "en",
                "effective_from": "2026-02-01T00:00:00+00:00",
            },
        )
    )

    payload = json.loads(
        provider.handle_tool_call(
            "core2_recall",
            {"query": "release note 12", "mode": "exact_source_required", "risk_class": "standard"},
        )
    )

    assert payload["abstained"] is False
    assert payload["query_family"] == "exact_lookup"
    assert payload["route_family"] == "lexical/source-first"
    assert payload["answer_type"] == "exact_source"
    assert payload["support_tier"] == "exact_source"

    provider.shutdown()


def test_update_resolution_route_prefers_current_version(tmp_path):
    provider = _init_core2(tmp_path, session_id="core2-routing-update")
    runtime = provider.runtime
    assert runtime is not None

    old_record = runtime.ingest_note(
        "Current deployment owner is Alice.",
        title="deployment owner",
        namespace="project",
        risk_class="standard",
        language="en",
        metadata={"identity_key": "deploy.owner"},
    )
    new_record = runtime.ingest_note(
        "Current deployment owner is Bob.",
        title="deployment owner",
        namespace="project",
        risk_class="standard",
        language="en",
        metadata={"identity_key": "deploy.owner"},
    )
    assert runtime.supersede_object(new_record["object_id"], old_record["object_id"], reason="owner_changed")

    payload = json.loads(provider.handle_tool_call("core2_recall", {"query": "What is the current deployment owner?"}))

    assert payload["abstained"] is False
    assert payload["query_family"] == "update_resolution"
    assert payload["route_family"] == "lexical/source-first"
    assert "fact_first_hit" not in list(payload["route_plan"].get("notes") or [])
    assert payload["items"][0]["object_id"] == new_record["object_id"]
    assert all(item["object_id"] != old_record["object_id"] for item in payload["items"])

    provider.shutdown()


def test_relation_multihop_route_expands_related_records(tmp_path):
    provider = _init_core2(tmp_path, session_id="core2-routing-graph")
    runtime = provider.runtime
    assert runtime is not None

    alpha = runtime.ingest_note(
        "Alpha service depends on the shared mission index.",
        title="Alpha service",
        namespace="project",
        risk_class="standard",
        language="en",
    )
    beta = runtime.ingest_note(
        "Beta service consumes the shared mission index.",
        title="Beta service",
        namespace="project",
        risk_class="standard",
        language="en",
    )
    runtime.store.add_edge(
        from_plane="canonical_truth",
        from_id=alpha["object_id"],
        to_plane="canonical_truth",
        to_id=beta["object_id"],
        edge_type=EDGE_DERIVED_FROM,
    )

    payload = json.loads(
        provider.handle_tool_call(
            "core2_recall",
            {"query": "What is the relationship between Alpha and Beta?", "mode": "source_supported"},
        )
    )

    assert payload["abstained"] is False
    assert payload["query_family"] == "relation_multihop"
    assert payload["route_family"] == "association/graph-assisted"
    assert payload["retrieved_item_count"] >= 2
    assert {item["title"] for item in payload["items"]} >= {"Alpha service", "Beta service"}

    provider.shutdown()


def test_personal_compare_route_uses_supported_compact_and_bounded_cap():
    plan = build_route_plan(
        "Which book did I finish reading first, The Hate U Give or The Nightingale?",
        mode="source_supported",
        operator=None,
        risk_class="standard",
        max_items=12,
    )

    assert plan.query_family == "personal_recall"
    assert plan.delivery_view == "supported_compact"
    assert plan.retrieval_cap == 6


def test_single_session_assistant_reference_query_stays_in_personal_recall_family():
    query = (
        "I wanted to check back on our previous conversation about Netflix. "
        "Do you remember what show I used as an example, the one that only had the last season available?"
    )

    family = infer_query_family(query, mode="source_supported", operator=None, risk_class="standard")

    assert family == "personal_recall"


def test_runtime_prioritizes_granular_temporal_personal_records():
    records = [
        {
            "object_id": "session-1",
            "title": "LongMemEval session 44",
            "content": "A" * 500,
            "metadata": {"session_index": 44},
            "score": 10.0,
            "effective_from": "2023-05-30T00:00:00+00:00",
            "recorded_at": "2023-05-30T00:00:00+00:00",
            "updated_at": "2023-05-30T00:00:00+00:00",
        },
        {
            "object_id": "turn-1",
            "title": "LongMemEval turn 44.1",
            "content": "Finished The Hate U Give for book club and compared it with The Nightingale.",
            "metadata": {"session_index": 44, "turn_index": 1},
            "score": 8.0,
            "effective_from": "2023-05-15T00:00:00+00:00",
            "recorded_at": "2023-05-15T00:00:00+00:00",
            "updated_at": "2023-05-15T00:00:00+00:00",
        },
    ]

    ranked = Core2Runtime._prioritize_personal_records(
        records,
        query="Which book did I finish reading first, 'The Hate U Give' or 'The Nightingale'?",
    )

    assert ranked[0]["object_id"] == "turn-1"


def test_runtime_prioritizes_attribute_records_for_personal_queries():
    records = [
        {
            "object_id": "session-blob",
            "title": "LongMemEval session 1",
            "content": "General long session blob " * 60,
            "metadata": {"session_index": 1},
            "score": 12.0,
            "effective_from": "2023-05-30T00:00:00+00:00",
            "recorded_at": "2023-05-30T00:00:00+00:00",
            "updated_at": "2023-05-30T00:00:00+00:00",
        },
        {
            "object_id": "turn-occupation",
            "title": "LongMemEval turn 27.1",
            "content": "I used to work as a marketing specialist at a small startup before this role.",
            "metadata": {"session_index": 27, "turn_index": 1},
            "score": 10.0,
            "effective_from": "2023-05-24T00:00:00+00:00",
            "recorded_at": "2023-05-24T00:00:00+00:00",
            "updated_at": "2023-05-24T00:00:00+00:00",
        },
    ]

    ranked = Core2Runtime._prioritize_personal_records(
        records,
        query="What was my previous occupation?",
    )

    assert ranked[0]["object_id"] == "turn-occupation"
