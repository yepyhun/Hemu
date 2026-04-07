from __future__ import annotations

import json

from agent.core2_authoritative import try_authoritative_answer
from agent.core2_longmemeval_benchmark import DEFAULT_DATASET, _seed_core2_kernel
from agent.core2_runtime import Core2Runtime
from plugins.memory import load_memory_provider


def _init_core2(tmp_path, session_id: str):
    provider = load_memory_provider("core2")
    assert provider is not None
    provider.initialize(session_id, hermes_home=str(tmp_path), platform="cli")
    return provider


def _digested_records(runtime: Core2Runtime, fact_key: str):
    return [
        record
        for record in runtime.store.list_canonical_objects()
        if record["metadata"].get("digest_fact") and record["metadata"].get("fact_key") == fact_key
    ]


def test_handmade_case_current_attribute(tmp_path):
    provider = _init_core2(tmp_path, "handmade-current-attribute")
    try:
        json.loads(
            provider.handle_tool_call(
                "core2_remember",
                {
                    "content": "Current role: staff engineer.",
                    "title": "profile",
                    "namespace": "personal",
                    "risk_class": "standard",
                    "language": "en",
                },
            )
        )
        packet = provider.runtime.recall("What is my current occupation?", mode="source_supported", operator=None, risk_class="standard", max_items=6)
        resolved = provider.authoritative_answer("What is my current occupation?")
    finally:
        provider.shutdown()

    assert packet.abstained is False
    assert packet.answer_surface is not None
    assert packet.answer_surface.retrieval_path == "fact_first"
    assert resolved is not None
    assert resolved["winner"] == "staff engineer"


def test_handmade_case_updated_attribute_with_previous_state(tmp_path):
    provider = _init_core2(tmp_path, "handmade-updated-attribute")
    runtime = provider.runtime
    assert runtime is not None
    try:
        runtime.ingest_note(
            "I live in Vienna.",
            title="old residence",
            namespace="personal",
            risk_class="standard",
            language="en",
            effective_from="2024-01-01T00:00:00+00:00",
        )
        runtime.ingest_note(
            "I live in Budapest.",
            title="new residence",
            namespace="personal",
            risk_class="standard",
            language="en",
            effective_from="2024-02-01T00:00:00+00:00",
        )
        packet = runtime.recall("Where do I live now?", mode="source_supported", operator=None, risk_class="standard", max_items=6)
        resolved = provider.authoritative_answer("Where do I live now?")
        records = _digested_records(runtime, "attribute.residence.current")
    finally:
        provider.shutdown()

    active = [record for record in records if record["state_status"] == "canonical_active"]
    superseded = [record for record in records if record["state_status"] == "superseded"]
    assert len(active) == 1
    assert len(superseded) == 1
    assert active[0]["metadata"]["canonical_value"] == "Budapest"
    assert superseded[0]["metadata"]["canonical_value"] == "Vienna"
    assert packet.answer_surface is not None
    assert packet.answer_surface.retrieval_path == "fact_first"
    assert resolved is not None
    assert resolved["winner"] == "Budapest"


def test_handmade_case_preference_evening(tmp_path):
    provider = _init_core2(tmp_path, "handmade-preference-evening")
    runtime = provider.runtime
    assert runtime is not None
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
        packet = runtime.recall("Can you suggest some activities that I can do in the evening?", mode="source_supported", operator=None, risk_class="standard", max_items=6)
        resolved = try_authoritative_answer("Can you suggest some activities that I can do in the evening?", packet)
    finally:
        provider.shutdown()

    assert packet.abstained is False
    assert packet.answer_surface is not None
    assert packet.answer_surface.retrieval_path == "fact_first"
    assert resolved is not None
    assert "relaxing activities that can be done in the evening" in str(resolved["text"]).lower()
    assert "watching tv" in str(resolved["text"]).lower()


def test_handmade_case_routine_before_bed(tmp_path):
    provider = _init_core2(tmp_path, "handmade-routine-before-bed")
    runtime = provider.runtime
    assert runtime is not None
    try:
        runtime.ingest_note(
            "To wind down before bedtime, I prefer reading fiction or other relaxing activities before 9:30 pm.",
            title="bedtime routine",
            namespace="personal",
            risk_class="standard",
            language="en",
        )
        packet = runtime.recall(
            "Can you suggest some relaxing activities I can do before bed in the evening?",
            mode="source_supported",
            operator=None,
            risk_class="standard",
            max_items=6,
        )
        resolved = try_authoritative_answer(
            "Can you suggest some relaxing activities I can do before bed in the evening?",
            packet,
        )
    finally:
        provider.shutdown()

    assert packet.abstained is False
    assert packet.answer_surface is not None
    assert packet.answer_surface.retrieval_path == "fact_first"
    assert resolved is not None
    assert "relaxing activities" in str(resolved["text"]).lower()
    assert "9:30 pm" in str(resolved["text"])


def test_handmade_case_collection_total_update(tmp_path):
    provider = _init_core2(tmp_path, "handmade-collection-total")
    runtime = provider.runtime
    assert runtime is not None
    try:
        json.loads(
            provider.handle_tool_call(
                "core2_remember",
                {
                    "content": "I was thinking of organizing my vintage vinyl records by genre. I have a total of 24 records in that collection.",
                    "title": "record collection",
                    "namespace": "personal",
                    "risk_class": "standard",
                    "language": "en",
                },
            )
        )
        provider.sync_turn("I just added a new record to my collection.", "Nice addition.", session_id="handmade-collection-total")
        packet = runtime.recall("How many vinyl records are in my collection now?", mode="source_supported", operator=None, risk_class="standard", max_items=6)
        resolved = try_authoritative_answer("How many vinyl records are in my collection now?", packet)
    finally:
        provider.shutdown()

    assert packet.abstained is False
    assert packet.answer_surface is not None
    assert resolved is not None
    assert resolved["winner"] == "25"
    assert str(resolved["text"]) == "Answer: 25."


def test_handmade_case_temporal_before_after(tmp_path):
    runtime = Core2Runtime(":memory:")
    runtime.initialize("handmade-temporal-before-after")
    try:
        runtime.ingest_note(
            'I just finished reading "The Hate U Give" two weeks ago for book club.',
            title="reading log 1",
            namespace="personal",
            risk_class="standard",
            language="en",
            effective_from="2023-05-30T12:42:00+00:00",
            source_type="document_source",
        )
        runtime.ingest_note(
            'I finished "The Nightingale" last weekend and loved it.',
            title="reading log 2",
            namespace="personal",
            risk_class="standard",
            language="en",
            effective_from="2023-05-30T12:42:00+00:00",
            source_type="document_source",
        )
        packet = runtime.recall(
            "Which book did I finish reading first, 'The Hate U Give' or 'The Nightingale'?",
            mode="source_supported",
            operator=None,
            risk_class="standard",
            max_items=6,
        )
        resolved = try_authoritative_answer(
            "Which book did I finish reading first, 'The Hate U Give' or 'The Nightingale'?",
            packet,
        )
    finally:
        runtime.shutdown()

    assert packet.abstained is False
    assert packet.answer_surface is not None
    assert str(packet.answer_surface.text or "").startswith("Answer:")
    assert resolved is not None
    assert resolved["winner"] == "'The Hate U Give'"


def test_handmade_case_conflict_or_safe_abstention(tmp_path):
    provider = _init_core2(tmp_path, "handmade-conflict")
    runtime = provider.runtime
    assert runtime is not None
    try:
        left = runtime.ingest_note(
            "Regulation 21 requires approval from Board A.",
            title="regulation 21",
            namespace="legal",
            risk_class="legal",
            language="en",
            effective_from="2026-05-01T00:00:00+00:00",
            metadata={"source_created_at": "2026-04-20T00:00:00+00:00"},
        )
        right = runtime.ingest_note(
            "Regulation 21 requires approval from Board B.",
            title="regulation 21",
            namespace="legal",
            risk_class="legal",
            language="en",
            effective_from="2026-05-01T00:00:00+00:00",
            metadata={"source_created_at": "2026-04-21T00:00:00+00:00"},
        )
        runtime.store.update_canonical_state(
            left["object_id"],
            left["state_status"],
            "attach_source_time",
            metadata_patch={"source_created_at": "2026-04-20T00:00:00+00:00"},
            field_updates={"source_created_at": "2026-04-20T00:00:00+00:00", "support_level": "source_supported"},
        )
        runtime.store.update_canonical_state(
            right["object_id"],
            right["state_status"],
            "attach_source_time",
            metadata_patch={"source_created_at": "2026-04-21T00:00:00+00:00"},
            field_updates={"source_created_at": "2026-04-21T00:00:00+00:00", "support_level": "source_supported"},
        )
        assert runtime.mark_conflict(left["object_id"], right["object_id"], reason="regulation_conflict")
        payload = json.loads(
            provider.handle_tool_call(
                "core2_recall",
                {"query": "regulation 21", "mode": "source_supported", "risk_class": "legal"},
            )
        )
    finally:
        provider.shutdown()

    assert payload["abstained"] is True
    assert "conflict" in str(payload.get("abstain_reason") or "").lower()


def test_handmade_case_abstention(tmp_path):
    provider = _init_core2(tmp_path, "handmade-abstention")
    try:
        payload = json.loads(
            provider.handle_tool_call(
                "core2_recall",
                {"query": "Where do I live?", "mode": "source_supported", "risk_class": "standard"},
            )
        )
    finally:
        provider.shutdown()

    assert payload["abstained"] is True
    assert payload["answer_surface"]["mode"] == "fallback"


def test_handmade_case_handoff_sensitive_covered_case(tmp_path):
    entries = json.loads(DEFAULT_DATASET.read_text(encoding="utf-8"))
    entry = next(item for item in entries if item.get("question_id") == "69fee5aa")
    _seed_core2_kernel(tmp_path, entry, oracle_only=False)
    provider = _init_core2(tmp_path, "handmade-handoff")
    try:
        packet = provider.runtime.recall(
            str(entry["question"]),
            mode="source_supported",
            operator=None,
            risk_class="standard",
            max_items=6,
        )
        resolved = provider.authoritative_answer(str(entry["question"]))
    finally:
        provider.shutdown()

    assert packet.abstained is False
    assert packet.answer_surface is not None
    assert packet.answer_surface.mode in {"fact_only", "fact_plus_summary"}
    assert str(packet.answer_surface.text or "").strip()
    assert resolved is not None
    assert resolved["winner"] == "38"
    assert str(resolved["text"]) == "Answer: 38."
