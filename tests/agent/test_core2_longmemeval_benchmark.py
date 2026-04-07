from __future__ import annotations

import json
from unittest.mock import patch

from agent.core2_authoritative import build_answer_surface
from agent.core2_longmemeval_benchmark import (
    Core2LongMemEvalRunResult,
    DEFAULT_CANARY_QUESTION_IDS,
    DEFAULT_DATASET,
    _failure_pattern,
    _response_contains_answer,
    _seed_core2_kernel,
    build_gate_status_artifact,
    run_core2_longmemeval_subset,
    select_benchmark_fast_profile,
)
from agent.core2_types import Core2RecallItem, Core2RecallPacket
from agent.core2_routing import infer_query_family
from plugins.memory import load_memory_provider


def _dataset_entry(question_id: str) -> dict:
    entries = json.loads(DEFAULT_DATASET.read_text(encoding="utf-8"))
    for entry in entries:
        if str(entry.get("question_id") or "") == question_id:
            return entry
    raise AssertionError(f"LongMemEval entry not found: {question_id}")


def test_failure_pattern_distinguishes_memory_abstention_from_prompt_overlap():
    recall_packet = {"abstained": True, "items": []}

    pattern = _failure_pattern(
        passed=False,
        recall_packet=recall_packet,
        evidence_contains_answer=False,
        prompt_contains_question_terms=True,
        response="I don't know based on the stored memory.",
    )

    assert pattern == "memory_abstention"


def test_failure_pattern_detects_grounding_handoff_miss_when_evidence_had_answer():
    recall_packet = {
        "abstained": False,
        "items": [{"content": "The Hate U Give was finished before The Nightingale."}],
    }

    pattern = _failure_pattern(
        passed=False,
        recall_packet=recall_packet,
        evidence_contains_answer=True,
        prompt_contains_question_terms=True,
        response="I don't know which one came first.",
    )

    assert pattern == "grounding_handoff_miss"


def test_seed_core2_kernel_makes_temporal_personal_case_retrievable(tmp_path):
    entry = _dataset_entry("gpt4_2d58bcd6")

    seeded = _seed_core2_kernel(tmp_path, entry, oracle_only=False)
    assert seeded > 0

    provider = load_memory_provider("core2")
    assert provider is not None
    provider.initialize("benchmark-recall", hermes_home=str(tmp_path), platform="cli")

    try:
        payload = json.loads(
            provider.handle_tool_call(
                "core2_recall",
                {
                    "query": "Which book did I finish reading first, 'The Hate U Give' or 'The Nightingale'?",
                    "mode": "source_supported",
                },
            )
        )
    finally:
        provider.shutdown()

    assert payload["abstained"] is False
    assert payload["query_family"] == "personal_recall"
    assert payload["retrieved_item_count"] >= 1
    assert len(str(payload["items"][0]["content"])) <= 320
    joined = " ".join(str(item.get("content") or "") for item in payload["items"])
    assert "The Hate U Give" in joined


def test_seed_core2_kernel_supports_preference_guidance_authoritative_answer(tmp_path):
    entry = _dataset_entry("195a1a1b")
    _seed_core2_kernel(tmp_path, entry, oracle_only=False)

    provider = load_memory_provider("core2")
    assert provider is not None
    provider.initialize("benchmark-pref-guidance", hermes_home=str(tmp_path), platform="cli")

    try:
        resolved = provider.authoritative_answer(str(entry["question"]))
    finally:
        provider.shutdown()

    assert resolved is not None
    text = str(resolved["text"])
    assert "relaxing activities in the evening" in text
    assert "9:30 pm" in text
    assert "using your phone" in text
    assert "watching TV" in text


def test_seed_core2_kernel_supports_temporal_elapsed_authoritative_answer(tmp_path):
    entry = _dataset_entry("0db4c65d")
    _seed_core2_kernel(tmp_path, entry, oracle_only=False)

    provider = load_memory_provider("core2")
    assert provider is not None
    provider.initialize("benchmark-temporal-elapsed", hermes_home=str(tmp_path), platform="cli")

    try:
        resolved = provider.authoritative_answer(str(entry["question"]))
    finally:
        provider.shutdown()

    assert resolved is not None
    assert resolved["winner"] == "18 days"


def test_seed_core2_kernel_supports_food_delivery_count_authoritative_answer(tmp_path):
    entry = _dataset_entry("d682f1a2")
    _seed_core2_kernel(tmp_path, entry, oracle_only=False)

    provider = load_memory_provider("core2")
    assert provider is not None
    provider.initialize("benchmark-food-delivery", hermes_home=str(tmp_path), platform="cli")

    try:
        resolved = provider.authoritative_answer(str(entry["question"]))
    finally:
        provider.shutdown()

    assert resolved is not None
    assert resolved["winner"] == "3"


def test_seed_core2_kernel_supports_collection_total_authoritative_answer(tmp_path):
    entry = _dataset_entry("69fee5aa")
    _seed_core2_kernel(tmp_path, entry, oracle_only=False)

    provider = load_memory_provider("core2")
    assert provider is not None
    provider.initialize("benchmark-collection-total", hermes_home=str(tmp_path), platform="cli")

    try:
        resolved = provider.authoritative_answer(str(entry["question"]))
    finally:
        provider.shutdown()

    assert resolved is not None
    assert resolved["winner"] == "38"


def test_seed_core2_kernel_supports_trip_order_authoritative_answer(tmp_path):
    entry = _dataset_entry("gpt4_7f6b06db")
    _seed_core2_kernel(tmp_path, entry, oracle_only=False)

    provider = load_memory_provider("core2")
    assert provider is not None
    provider.initialize("benchmark-trip-order", hermes_home=str(tmp_path), platform="cli")

    try:
        resolved = provider.authoritative_answer(str(entry["question"]))
    finally:
        provider.shutdown()

    assert resolved is not None
    text = str(resolved["text"])
    assert "Muir Woods" in text
    assert "Big Sur and Monterey" in text
    assert "Yosemite" in text


def test_seed_core2_kernel_supports_single_session_assistant_reference_answer(tmp_path):
    entry = _dataset_entry("f523d9fe")
    _seed_core2_kernel(tmp_path, entry, oracle_only=False)

    provider = load_memory_provider("core2")
    assert provider is not None
    provider.initialize("benchmark-single-session-assistant", hermes_home=str(tmp_path), platform="cli")

    try:
        payload = json.loads(
            provider.handle_tool_call(
                "core2_recall",
                {
                    "query": str(entry["question"]),
                    "mode": "source_supported",
                },
            )
        )
        resolved = provider.authoritative_answer(str(entry["question"]))
    finally:
        provider.shutdown()

    assert payload["abstained"] is False
    assert payload["query_family"] == "personal_recall"
    assert payload["retrieved_item_count"] >= 1
    assert "conversation_reference_expand" in list(payload["route_plan"].get("notes") or [])
    assert resolved is not None
    assert resolved["winner"] == "Doc Martin"


def test_reading_history_rewrite_stays_in_personal_recall_family():
    query = "books finished reading history The Hate U Give The Nightingale order completed"

    family = infer_query_family(query, mode="source_supported", operator=None, risk_class="standard")

    assert family == "personal_recall"


def test_run_subset_supports_targeted_question_ids_and_latency_abort():
    def _fake_generation(*, entry, mode, model, base_url, api_key, provider, oracle_seed, benchmark_fast):
        return Core2LongMemEvalRunResult(
            question_id=str(entry["question_id"]),
            question_type=str(entry.get("question_type") or "unknown"),
            passed=False,
            judge="no",
            hypothesis="not enough information",
            answer=str(entry.get("answer") or ""),
            prompt_excerpt="prompt",
            prompt_tokens_estimate=10,
            baseline_replay_tokens_estimate=100,
            estimated_token_savings=90,
            estimated_savings_ratio=0.9,
            seeded_core2_entries=3,
            seed_seconds=0.01,
            tool_seconds=0.02,
            conversation_seconds=9.0,
            api_seconds=8.0,
            judge_seconds=0.5,
            total_wall_seconds=10.0,
            kernel_local_seconds=0.98,
            prompt_tokens=20,
            completion_tokens=5,
            total_tokens=25,
            api_calls=1,
            provider=provider,
            base_url=base_url,
            model=model,
            budget_profile="supported",
            failure_pattern="retrieval_or_reasoning_miss",
            recall_abstained=False,
            recall_route_family="curated_memory_view",
            recall_query_family="personal_recall",
            evidence_item_count=1,
            evidence_contains_answer=False,
            memory_tool_calls=1,
            prompt_contains_answer=False,
            prompt_contains_question_terms=True,
        )

    with patch("agent.core2_longmemeval_benchmark.run_core2_longmemeval_generation", side_effect=_fake_generation):
        report = run_core2_longmemeval_subset(
            sample_size=20,
            seed=7,
            mode="core2",
            model="demo-model",
            base_url="https://example.invalid/v1",
            api_key="test-key",
            question_ids=["gpt4_2d58bcd6"],
            max_conversation_seconds=5.0,
        )

    assert report["summary"]["sample_size_completed"] == 1
    assert report["summary"]["aborted_early"] is True
    assert report["summary"]["aborted_reason"] == "latency_threshold_exceeded"
    assert report["summary"]["budget_profiles"] == {"supported": 1}
    assert report["results"][0]["question_id"] == "gpt4_2d58bcd6"
    assert report["results"][0]["failure_pattern"] == "latency_abort"


def test_select_benchmark_fast_profile_prefers_supported_for_comparison_timeline_questions():
    entry = _dataset_entry("gpt4_2d58bcd6")

    profile = select_benchmark_fast_profile(entry)

    assert profile == "supported"


def test_build_gate_status_artifact_summarizes_latest_gate_state():
    artifact = build_gate_status_artifact(
        {
            "summary": {
                "sample_size_requested": 10,
                "sample_size_completed": 7,
                "pass_rate": 4 / 7,
                "aborted_early": True,
                "aborted_reason": "latency_threshold_exceeded",
                "answer_surface_hit_rate": 0.5714,
                "answer_surface_modes": {"fact_only": 4, "fallback": 3},
                "failure_patterns": {
                    "passed": 4,
                    "retrieval_or_reasoning_miss": 2,
                    "latency_abort": 1,
                },
                "avg_total_wall_seconds": 9.18,
                "avg_conversation_seconds": 5.675,
                "avg_api_seconds": 4.318,
            },
            "results": [
                {"question_id": "a"},
                {"question_id": "b"},
            ],
        }
    )

    assert artifact["status"] == "needs_work"
    assert artifact["classification_mode"] == "fail_closed"
    assert artifact["sample_size_requested"] == 10
    assert artifact["sample_size_completed"] == 7
    assert artifact["dominant_failure_pattern"] == "retrieval_or_reasoning_miss"
    assert artifact["dominant_failure_family"] == "unknown"
    assert artifact["failure_families"] == {"unknown": 2, "latency": 1}
    assert artifact["current_blocker"] == "unknown"
    assert artifact["answer_surface_hit_rate"] == 0.5714
    assert artifact["answer_surface_modes"] == {"fact_only": 4, "fallback": 3}
    assert artifact["canary_question_ids"] == list(DEFAULT_CANARY_QUESTION_IDS)
    assert artifact["latest_question_ids"] == ["a", "b"]


def test_tool_budget_profiles_are_graded_instead_of_binary():
    item = Core2RecallItem(
        object_id="obj-1",
        plane="canonical_truth",
        object_kind="state",
        title="Reading history",
        namespace="personal",
        namespace_class="personal",
        risk_class="standard",
        source_type="document_source",
        support_level="source_supported",
        state_status="canonical_active",
        content="A" * 600,
        snippet="B" * 400,
        metadata={"question_id": "q1", "session_index": 1, "noise": "drop-me"},
    )
    packet = Core2RecallPacket(
        query="Which book came first?",
        mode="source_supported",
        operator=None,
        risk_class="standard",
        support_tier="source_supported",
        confidence="high",
        abstained=False,
        display_value="C" * 500,
        canonical_value="D" * 500,
        grounding_refs=[{"object_id": f"ref-{idx}"} for idx in range(1, 6)],
        items=[item, item, item, item, item],
    )

    minimal = packet.to_dict(compact=True, tool_budget_profile="minimal")
    compact = packet.to_dict(compact=True, tool_budget_profile="compact")
    supported = packet.to_dict(compact=True, tool_budget_profile="supported")

    assert len(minimal["items"]) == 2
    assert len(compact["items"]) == 3
    assert len(supported["items"]) == 3
    assert len(minimal["grounding_refs"]) == 2
    assert len(compact["grounding_refs"]) == 3
    assert len(supported["grounding_refs"]) == 3
    assert len(minimal["items"][0]["content"]) < len(compact["items"][0]["content"]) < len(supported["items"][0]["content"])
    assert "noise" not in minimal["items"][0]["metadata"]


def test_response_contains_answer_tolerates_formatting_noise():
    response = "You finished **'The Hate U Give'** first."

    assert _response_contains_answer(response, "'The Hate U Give'") is True


def test_response_contains_answer_rejects_late_mention_when_first_sentence_picks_other_option():
    response = (
        "You finished **'The Nightingale'** first. "
        "The Hate U Give was completed two weeks earlier for a book club meeting."
    )

    assert _response_contains_answer(response, "'The Hate U Give'") is False


def test_benchmark_lean_payload_omits_route_diagnostics_and_heavy_item_fields():
    item = Core2RecallItem(
        object_id="obj-1",
        plane="canonical_truth",
        object_kind="state",
        title="Reading history",
        namespace="personal",
        namespace_class="personal",
        risk_class="standard",
        source_type="document_source",
        support_level="source_supported",
        state_status="canonical_active",
        content="Finished The Hate U Give before The Nightingale.",
        snippet="Finished The Hate U Give before The Nightingale.",
        metadata={"question_id": "q1", "session_index": 1},
    )
    packet = Core2RecallPacket(
        query="Which book came first?",
        mode="source_supported",
        operator=None,
        risk_class="standard",
        support_tier="source_supported",
        confidence="high",
        abstained=False,
        query_family="personal_recall",
        route_family="curated_memory_view",
        route_plan={"route": "curated"},
        answer_type="compact_memory",
        canonical_value="The Hate U Give",
        display_value="The Hate U Give",
        grounding_refs=[{"object_id": "obj-1", "title": "Reading history", "raw_id": "raw-1"}],
        items=[item],
    )

    lean = packet.to_dict(compact=True, tool_budget_profile="supported", tool_payload_mode="benchmark_lean")

    assert "route_plan" not in lean
    assert "query_family" not in lean
    assert "route_family" not in lean
    assert "answer_surface" not in lean
    assert set(lean["items"][0].keys()) <= {
        "object_id",
        "title",
        "content",
        "snippet",
        "support_level",
        "state_status",
        "effective_from",
        "source_created_at",
        "metadata",
        "score",
    }


def test_benchmark_lean_payload_keeps_answer_surface_when_present():
    item = Core2RecallItem(
        object_id="obj-1",
        plane="canonical_truth",
        object_kind="state",
        title="Residence",
        namespace="personal",
        namespace_class="personal",
        risk_class="standard",
        source_type="digested_fact",
        support_level="source_supported",
        state_status="canonical_active",
        content="Budapest",
        snippet="Budapest",
        metadata={
            "digest_fact": True,
            "canonical_value": "Budapest",
            "fact_key": "attribute.residence.current",
            "retrieval_path": "fact_first",
        },
    )
    packet = Core2RecallPacket(
        query="Where do I live?",
        mode="source_supported",
        operator=None,
        risk_class="standard",
        support_tier="source_supported",
        confidence="high",
        abstained=False,
        items=[item],
    )
    packet.answer_surface = build_answer_surface("Where do I live?", packet)

    lean = packet.to_dict(compact=True, tool_budget_profile="supported", tool_payload_mode="benchmark_lean")

    assert lean["answer_surface"]["mode"] == "fact_only"
    assert lean["answer_surface"]["text"] == "Answer: Budapest."
