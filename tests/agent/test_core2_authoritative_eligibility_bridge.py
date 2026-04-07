from __future__ import annotations

from pathlib import Path

from agent.core2_authoritative import try_authoritative_answer
from agent.core2_runtime import Core2Runtime
from agent.core2_types import Core2RecallPacket


def _init_runtime(tmp_path, session_id: str) -> Core2Runtime:
    runtime = Core2Runtime(str(Path(tmp_path) / "core2.db"), hybrid_substrate_mode="on")
    runtime.initialize(session_id)
    return runtime


def _packet_with_bridge_path(
    runtime: Core2Runtime,
    *,
    query: str,
    fact_keys: set[str],
    retrieval_path: str,
    query_family: str = "personal_recall",
):
    records = []
    for record in runtime.store.list_canonical_objects(include_inactive=False):
        metadata = dict(record.get("metadata") or {})
        if not metadata.get("digest_fact"):
            continue
        if str(metadata.get("fact_key") or "").strip().lower() not in fact_keys:
            continue
        records.append(record)
    assert records, f"no records found for {sorted(fact_keys)}"

    items = []
    for record in records:
        candidate = dict(record)
        metadata = dict(candidate.get("metadata") or {})
        metadata["retrieval_path"] = retrieval_path
        candidate["metadata"] = metadata
        items.append(runtime._record_to_item(candidate))  # type: ignore[attr-defined]

    return Core2RecallPacket(
        query=query,
        mode="source_supported",
        operator=None,
        risk_class="standard",
        support_tier="source_supported",
        confidence="high",
        abstained=False,
        query_family=query_family,
        route_family="curated_memory_view",
        query_mode="source_supported",
        items=items,
        confidence_tier="high",
    )


def test_preference_guidance_bridge_accepts_hybrid_scoped_turn_digested_facts(tmp_path):
    runtime = _init_runtime(tmp_path, "bridge-preference")
    try:
        runtime.ingest_note(
            "I prefer relaxing activities that can be done in the evening, preferably before 9:30 pm.",
            title="evening preference",
            namespace="personal",
            risk_class="standard",
            language="en",
        )
        runtime.ingest_note(
            "Using my phone or watching TV in the evening has been affecting my sleep quality, so I want to avoid that at night.",
            title="sleep routine",
            namespace="personal",
            risk_class="standard",
            language="en",
        )
        packet = _packet_with_bridge_path(
            runtime,
            query="Can you suggest some activities that I can do in the evening?",
            fact_keys={
                "preference.evening.activities.current",
                "preference.evening.screen_avoid.current",
            },
            retrieval_path="hybrid_scoped_turn",
        )
        resolved = try_authoritative_answer("Can you suggest some activities that I can do in the evening?", packet)
    finally:
        runtime.shutdown()

    assert resolved is not None
    assert resolved["mode"] == "preference_guidance"
    assert resolved["answer_surface"]["retrieval_path"] == "hybrid_scoped_turn"
    assert "watching tv" in str(resolved["text"]).lower()


def test_collection_total_bridge_accepts_hybrid_scoped_raw_digested_fact(tmp_path):
    runtime = _init_runtime(tmp_path, "bridge-collection")
    try:
        runtime.ingest_note(
            "I was thinking of organizing my vintage vinyl records by genre. I have a total of 24 records in that collection.",
            title="vinyl collection",
            namespace="personal",
            risk_class="standard",
            language="en",
        )
        packet = _packet_with_bridge_path(
            runtime,
            query="How many vinyl records are in my collection now?",
            fact_keys={"aggregate.collection.total.current"},
            retrieval_path="hybrid_scoped_raw",
        )
        resolved = try_authoritative_answer("How many vinyl records are in my collection now?", packet)
    finally:
        runtime.shutdown()

    assert resolved is not None
    assert resolved["mode"] == "aggregate_count"
    assert resolved["winner"] == "24"
    assert resolved["answer_surface"]["retrieval_path"] == "hybrid_scoped_raw"


def test_trip_order_bridge_accepts_hybrid_scoped_turn_digested_fact(tmp_path):
    runtime = _init_runtime(tmp_path, "bridge-trip-order")
    try:
        runtime.ingest_note(
            "I went on a day hike to Muir Woods with Maya, my cousin from Portland.",
            title="trip-muir",
            namespace="personal",
            risk_class="standard",
            language="en",
            effective_from="2024-01-03T00:00:00+00:00",
        )
        runtime.ingest_note(
            "I went on a day hike to Mount Tam with Rowan.",
            title="trip-tam",
            namespace="personal",
            risk_class="standard",
            language="en",
            effective_from="2024-01-02T00:00:00+00:00",
        )
        packet = _packet_with_bridge_path(
            runtime,
            query="Which trip happened first, 'day hike to Muir Woods' or 'day hike to Mount Tam'?",
            fact_keys={"event.trip.recent"},
            retrieval_path="hybrid_scoped_turn",
        )
        resolved = try_authoritative_answer(
            "Which trip happened first, 'day hike to Muir Woods' or 'day hike to Mount Tam'?",
            packet,
        )
    finally:
        runtime.shutdown()

    assert resolved is not None
    assert resolved["mode"] == "trip_order"
    ordered_values = resolved["answer_surface"]["structured"]["ordered_values"]
    assert "Mount Tam" in ordered_values[0]
    assert resolved["answer_surface"]["retrieval_path"] == "hybrid_scoped_turn"


def test_bridge_does_not_widen_to_plain_lexical_structured_items(tmp_path):
    runtime = _init_runtime(tmp_path, "bridge-negative")
    try:
        runtime.ingest_note(
            "I prefer relaxing activities that can be done in the evening, preferably before 9:30 pm.",
            title="evening preference",
            namespace="personal",
            risk_class="standard",
            language="en",
        )
        packet = _packet_with_bridge_path(
            runtime,
            query="Can you suggest some activities that I can do in the evening?",
            fact_keys={"preference.evening.activities.current"},
            retrieval_path="semantic_first",
        )
        resolved = try_authoritative_answer("Can you suggest some activities that I can do in the evening?", packet)
    finally:
        runtime.shutdown()

    assert resolved is None
