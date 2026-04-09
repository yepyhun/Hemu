from __future__ import annotations

from pathlib import Path

from agent.core2_hybrid_substrate import Core2HybridSubstrate
from agent.core2_runtime import Core2Runtime


def _init_runtime(tmp_path, *, mode: str) -> Core2Runtime:
    runtime = Core2Runtime(str(Path(tmp_path) / "core2.db"), hybrid_substrate_mode=mode)
    runtime.initialize(f"hybrid-{mode}")
    return runtime


def _seed_trip_turns(runtime: Core2Runtime) -> None:
    runtime.ingest_turn(
        "I went on a day hike to Muir Woods with Maya, my cousin from Portland, today.",
        "",
        session_id="trip-muir",
    )
    runtime.ingest_turn(
        "I went on a day hike to Mount Tam with Rowan today.",
        "",
        session_id="trip-tam",
    )


def test_hybrid_turn_scope_recovers_trip_from_verbatim_turn_context(tmp_path):
    runtime_off = _init_runtime(tmp_path, mode="off")
    _seed_trip_turns(runtime_off)

    packet_off = runtime_off.recall(
        "Which trip involved my cousin from Portland?",
        mode="auto",
        operator=None,
        risk_class="standard",
        max_items=6,
    )
    runtime_off.shutdown()

    runtime_on = _init_runtime(tmp_path, mode="on")
    packet_on = runtime_on.recall(
        "Which trip involved my cousin from Portland?",
        mode="auto",
        operator=None,
        risk_class="standard",
        max_items=6,
    )
    runtime_on.shutdown()

    assert packet_on.abstained is False
    assert "hybrid_turn_hit" in list(packet_on.route_plan.get("notes") or [])
    assert packet_on.items[0].metadata.get("retrieval_path") == "hybrid_scoped_turn"
    assert "Muir Woods" in packet_on.items[0].content
    assert packet_off.abstained or "Muir Woods" not in packet_off.items[0].content


def test_hybrid_raw_archive_path_is_callable_without_crossing_answer_ownership(tmp_path):
    runtime = _init_runtime(tmp_path, mode="on")
    runtime.ingest_note(
        "The backup drill runbook lives in the blue binder on the mezzanine shelf.",
        title="backup drill runbook",
        namespace="project",
        risk_class="standard",
        language="en",
    )

    packet = runtime.recall(
        "Where does the backup drill runbook live?",
        mode="auto",
        operator=None,
        risk_class="standard",
        max_items=6,
    )
    runtime.shutdown()

    assert packet.abstained is False
    assert "hybrid_raw_hit" in list(packet.route_plan.get("notes") or [])
    assert packet.items[0].metadata.get("retrieval_path") == "hybrid_scoped_raw"
    assert packet.items[0].metadata.get("hybrid_scope") == "raw_archive"


def test_hybrid_shadow_mode_keeps_old_path_but_records_trace(tmp_path):
    runtime_off = _init_runtime(tmp_path, mode="off")
    _seed_trip_turns(runtime_off)
    packet_off = runtime_off.recall(
        "Which trip involved my cousin from Portland?",
        mode="auto",
        operator=None,
        risk_class="standard",
        max_items=6,
    )
    runtime_off.shutdown()

    runtime_shadow = _init_runtime(tmp_path, mode="shadow")
    packet_shadow = runtime_shadow.recall(
        "Which trip involved my cousin from Portland?",
        mode="auto",
        operator=None,
        risk_class="standard",
        max_items=6,
    )
    runtime_shadow.shutdown()

    assert "hybrid_shadow_only" in list(packet_shadow.route_plan.get("notes") or [])
    assert packet_off.abstained == packet_shadow.abstained
    if not packet_off.abstained and not packet_shadow.abstained:
        assert packet_off.items[0].object_id == packet_shadow.items[0].object_id


def test_hybrid_session_lookup_keys_ignore_benchmark_question_id_fallback():
    keys = Core2HybridSubstrate._session_lookup_keys(
        {"question_id": "gpt4_123", "session_index": "2"}
    )
    assert keys == []


def test_runtime_recall_forwards_session_id_into_hybrid_search(tmp_path):
    runtime = _init_runtime(tmp_path, mode="on")
    captured: dict[str, object] = {}

    def fake_search(query, **kwargs):
        captured["query"] = query
        captured["kwargs"] = kwargs
        return [], {}

    runtime.hybrid_substrate.search = fake_search  # type: ignore[assignment]
    runtime.store.search_canonical = lambda *args, **kwargs: []  # type: ignore[assignment]

    packet = runtime.recall(
        "Which trip involved my cousin from Portland?",
        mode="auto",
        operator=None,
        risk_class="standard",
        max_items=6,
        session_id="trip-muir",
    )
    runtime.shutdown()

    assert captured["query"] == "Which trip involved my cousin from Portland?"
    assert captured["kwargs"]["session_id"] == "trip-muir"
    assert packet.abstained is True


def test_prepare_selector_candidate_does_not_treat_question_id_as_scope():
    candidate = Core2HybridSubstrate._prepare_selector_candidate(
        {
            "object_id": "obj-1",
            "title": "evening walk",
            "content": "I took a long evening walk yesterday.",
            "metadata": {"question_id": "gpt4_123"},
            "effective_from": "2026-04-01T12:00:00Z",
        },
        query_terms={"evening", "walk"},
        selector_shape="temporal_pair",
    )
    assert candidate is not None
    assert candidate["scope"] == ""
