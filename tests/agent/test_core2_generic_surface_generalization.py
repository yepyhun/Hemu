from __future__ import annotations

import json

from agent.core2_authoritative import try_authoritative_answer
from agent.core2_longmemeval_benchmark import DEFAULT_DATASET, _seed_core2_kernel
from agent.core2_runtime import Core2Runtime
from plugins.memory import load_memory_provider


def _dataset_entry(question_id: str) -> dict:
    entries = json.loads(DEFAULT_DATASET.read_text(encoding="utf-8"))
    for entry in entries:
        if str(entry.get("question_id") or "") == question_id:
            return entry
    raise AssertionError(f"LongMemEval entry not found: {question_id}")


def _seeded_resolution(tmp_path, question_id: str):
    entry = _dataset_entry(question_id)
    _seed_core2_kernel(tmp_path, entry, oracle_only=False)
    provider = load_memory_provider("core2")
    assert provider is not None
    provider.initialize(f"generic-surface-{question_id}", hermes_home=str(tmp_path), platform="cli")
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
    return entry, packet, resolved


def test_failed_cluster_charity_total_surfaces_as_generic_aggregate(tmp_path):
    _, packet, resolved = _seeded_resolution(tmp_path, "d851d5ba")

    assert packet.abstained is False
    assert resolved is not None
    assert resolved["winner"] == "$3,750"
    assert resolved["answer_surface"]["structured"]["kind"] == "aggregate_count"
    assert resolved["answer_surface"]["structured"]["count"] == 3750


def test_failed_cluster_threshold_remaining_surfaces_as_generic_aggregate(tmp_path):
    _, packet, resolved = _seeded_resolution(tmp_path, "9ee3ecd6")

    assert packet.abstained is False
    assert resolved is not None
    assert resolved["winner"] == "100"
    assert resolved["answer_surface"]["structured"]["kind"] == "aggregate_count"
    assert resolved["answer_surface"]["structured"]["count"] == 100


def test_failed_cluster_spotify_current_total_surfaces_as_generic_aggregate(tmp_path):
    _, packet, resolved = _seeded_resolution(tmp_path, "c960da58")

    assert packet.abstained is False
    assert resolved is not None
    assert resolved["winner"] == "20"
    assert resolved["answer_surface"]["structured"]["kind"] == "aggregate_count"


def test_failed_cluster_courses_total_surfaces_as_generic_aggregate(tmp_path):
    _, packet, resolved = _seeded_resolution(tmp_path, "c2ac3c61")

    assert packet.abstained is False
    assert resolved is not None
    assert resolved["winner"] == "5"
    assert resolved["answer_surface"]["structured"]["kind"] == "aggregate_count"


def test_failed_cluster_natgeo_total_prefers_current_total_over_partial_history(tmp_path):
    _, packet, resolved = _seeded_resolution(tmp_path, "8fb83627")

    assert packet.abstained is False
    assert resolved is not None
    assert resolved["winner"] == "5"
    assert resolved["answer_surface"]["structured"]["kind"] == "aggregate_count"


def test_failed_cluster_generic_event_order_surfaces_without_trip_family(tmp_path):
    _, packet, resolved = _seeded_resolution(tmp_path, "gpt4_18c2b244")

    assert packet.abstained is False
    assert resolved is not None
    structured = resolved["answer_surface"]["structured"]
    assert structured["kind"] == "trip_order"
    assert structured["ordered_values"][0].startswith("I used a Buy One Get One Free coupon")
    assert "I signed up for the rewards program at ShopRite" in structured["ordered_values"][-1]


def test_failed_cluster_two_option_temporal_compare_surfaces_as_scalar_winner(tmp_path):
    _, packet, resolved = _seeded_resolution(tmp_path, "gpt4_70e84552")

    assert packet.abstained is False
    assert resolved is not None
    assert resolved["winner"] == "fixing the fence"
    assert resolved["answer_surface"]["structured"]["kind"] == "scalar"
    assert resolved["answer_surface"]["structured"]["value"] == "fixing the fence"


def test_failed_cluster_missing_operand_savings_question_abstains_canonically(tmp_path):
    _, packet, resolved = _seeded_resolution(tmp_path, "09ba9854_abs")

    assert packet.abstained is False
    assert resolved is not None
    assert resolved["mode"] == "canonical_abstention"
    assert resolved["answer_surface"]["structured"]["kind"] == "canonical_abstention"
    assert "grounded information" in str(resolved["text"]).lower()
    assert "bus fare is missing" in str(resolved["text"]).lower()


def test_failed_cluster_place_reference_surfaces_as_conversation_reference(tmp_path):
    _, packet, resolved = _seeded_resolution(tmp_path, "e9327a54")

    assert packet.abstained is False
    assert resolved is not None
    assert resolved["mode"] == "conversation_reference"
    assert resolved["winner"] == "The Sugar Factory at Icon Park"
    assert resolved["answer_surface"]["structured"]["kind"] == "scalar"
    assert resolved["answer_surface"]["structured"]["value"] == "The Sugar Factory at Icon Park"


def test_negative_proof_generic_aggregate_does_not_sum_unrelated_money(tmp_path):
    runtime = Core2Runtime(":memory:")
    runtime.initialize("negative-generic-money")
    try:
        runtime.ingest_note(
            "I raised $100 for charity at the bake sale.",
            title="charity bake sale",
            namespace="personal",
            risk_class="standard",
            language="en",
            effective_from="2024-01-01T00:00:00+00:00",
        )
        runtime.ingest_note(
            "A music benefit brought in $5,000 overall.",
            title="music benefit",
            namespace="personal",
            risk_class="standard",
            language="en",
            effective_from="2024-01-02T00:00:00+00:00",
        )
        packet = runtime.recall(
            "How much money did I raise for charity in total?",
            mode="source_supported",
            operator=None,
            risk_class="standard",
            max_items=6,
        )
        resolved = try_authoritative_answer("How much money did I raise for charity in total?", packet)
    finally:
        runtime.shutdown()

    assert resolved is not None
    assert resolved["winner"] == "$100"


def test_negative_proof_generic_event_order_requires_all_options(tmp_path):
    runtime = Core2Runtime(":memory:")
    runtime.initialize("negative-generic-order")
    try:
        runtime.ingest_note(
            "I signed up for ShopRite rewards today.",
            title="shoprite",
            namespace="personal",
            risk_class="standard",
            language="en",
            effective_from="2024-01-03T00:00:00+00:00",
        )
        runtime.ingest_note(
            "I redeemed cashback on Ibotta yesterday.",
            title="ibotta",
            namespace="personal",
            risk_class="standard",
            language="en",
            effective_from="2024-01-02T00:00:00+00:00",
        )
        packet = runtime.recall(
            "What is the order of the three events: 'I signed up for ShopRite rewards', 'I used a Buy One Get One Free coupon on diapers', and 'I redeemed cashback on Ibotta'?",
            mode="source_supported",
            operator=None,
            risk_class="standard",
            max_items=6,
        )
        resolved = try_authoritative_answer(
            "What is the order of the three events: 'I signed up for ShopRite rewards', 'I used a Buy One Get One Free coupon on diapers', and 'I redeemed cashback on Ibotta'?",
            packet,
        )
    finally:
        runtime.shutdown()

    assert resolved is None


def test_negative_proof_threshold_surface_does_not_guess_without_target(tmp_path):
    runtime = Core2Runtime(":memory:")
    runtime.initialize("negative-generic-threshold")
    try:
        runtime.ingest_note(
            "I earned 50 points, bringing my total to 200 points so far.",
            title="points total",
            namespace="personal",
            risk_class="standard",
            language="en",
            effective_from="2024-02-01T00:00:00+00:00",
        )
        packet = runtime.recall(
            "How many points do I need to earn to redeem a free skincare product?",
            mode="source_supported",
            operator=None,
            risk_class="standard",
            max_items=6,
        )
        resolved = try_authoritative_answer(
            "How many points do I need to earn to redeem a free skincare product?",
            packet,
        )
    finally:
        runtime.shutdown()

    assert resolved is None
