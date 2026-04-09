from __future__ import annotations

from types import SimpleNamespace

from agent.kernel_memory_answer_packet import KernelMemoryAnswerPacketPolicy
from agent.kernel_memory_memory_objects import KernelMemoryMemoryObjectAssembler


def test_answer_packet_is_confident_for_complete_grounded_chain():
    policy = KernelMemoryAnswerPacketPolicy(SimpleNamespace())
    packet = policy.build(
        query="What is Laura's current favorite quote?",
        items=[{"id": "a"}, {"id": "b"}, {"id": "c"}],
        evidence_chain={
            "chain_completeness_score": 1.0,
            "missing_link_penalty": 0.0,
            "cross_layer_consistency_score": 1.0,
            "verification_quality_score": 0.9,
            "provenance_support_score": 0.8,
            "covered_facets": ["anchor", "answer_anchor", "correction_check", "source_support"],
            "expected_facets": ["anchor", "answer_anchor", "correction_check", "source_support"],
            "role_counts": {"solution": 2, "bridge": 1},
        },
    )

    assert packet["confidence_tier"] == "high"
    assert packet["delivery_mode"] == "confident"
    assert packet["should_abstain"] is False


def test_answer_packet_becomes_cautious_for_incomplete_chain():
    policy = KernelMemoryAnswerPacketPolicy(SimpleNamespace())
    packet = policy.build(
        query="What is Laura's current favorite quote?",
        items=[{"id": "a"}],
        evidence_chain={
            "chain_completeness_score": 0.25,
            "missing_link_penalty": 0.75,
            "cross_layer_consistency_score": 0.7,
            "verification_quality_score": 0.1,
            "provenance_support_score": 0.1,
            "covered_facets": ["anchor"],
            "expected_facets": ["anchor", "answer_anchor", "correction_check"],
            "role_counts": {"bridge": 1},
        },
    )

    assert packet["confidence_tier"] == "low"
    assert packet["delivery_mode"] == "abstain_or_ask"
    assert packet["should_abstain"] is True
    assert "insufficient_grounding" in packet["warnings"]


def test_answer_packet_warns_when_verification_and_provenance_are_weak():
    policy = KernelMemoryAnswerPacketPolicy(SimpleNamespace())
    packet = policy.build(
        query="What is Laura's current favorite quote?",
        items=[{"id": "a"}, {"id": "b"}],
        evidence_chain={
            "chain_completeness_score": 0.8,
            "missing_link_penalty": 0.1,
            "cross_layer_consistency_score": 1.0,
            "verification_quality_score": 0.2,
            "provenance_support_score": 0.15,
            "covered_facets": ["anchor", "answer_anchor", "source_support"],
            "expected_facets": ["anchor", "answer_anchor", "source_support"],
            "role_counts": {"solution": 1, "bridge": 1},
        },
    )

    assert packet["confidence_tier"] != "high"
    assert "weak_verification_support" in packet["warnings"]
    assert "weak_provenance_support" in packet["warnings"]


def test_answer_packet_abstains_when_objective_execution_is_insufficient():
    policy = KernelMemoryAnswerPacketPolicy(SimpleNamespace())
    packet = policy.build(
        query="What is the total amount I spent on luxury items?",
        items=[{"id": "a"}, {"id": "b"}],
        evidence_chain={
            "chain_completeness_score": 0.9,
            "missing_link_penalty": 0.0,
            "cross_layer_consistency_score": 1.0,
            "verification_quality_score": 0.8,
            "provenance_support_score": 0.8,
            "covered_facets": ["anchor", "answer_anchor", "source_support"],
            "expected_facets": ["anchor", "answer_anchor", "source_support"],
            "role_counts": {"solution": 2},
        },
        objective_execution={
            "objective": "aggregate_total",
            "supported": False,
            "insufficiency_reasons": ["not_enough_distinct_money_fact"],
        },
    )

    assert packet["should_abstain"] is True
    assert packet["delivery_mode"] == "abstain_or_ask"
    assert "not_enough_distinct_money_fact" in packet["warnings"]


def test_answer_packet_promotes_direct_value_grounding():
    policy = KernelMemoryAnswerPacketPolicy(SimpleNamespace())
    packet = policy.build(
        query="What breed is my dog?",
        items=[{"id": "a"}],
        evidence_chain={
            "chain_completeness_score": 0.42,
            "missing_link_penalty": 0.4,
            "cross_layer_consistency_score": 0.8,
            "verification_quality_score": 0.3,
            "provenance_support_score": 0.3,
            "covered_facets": ["anchor", "answer_anchor"],
            "expected_facets": ["anchor", "answer_anchor", "source_support"],
            "role_counts": {"solution": 1},
        },
        objective_execution={
            "objective": "general",
            "supported": True,
            "metrics": {
                "direct_value_grounded": True,
                "grounding_strength": "high",
            },
        },
    )

    assert packet["should_abstain"] is False
    assert packet["delivery_mode"] == "confident"


def test_memory_object_assembly_uses_compact_view_for_cautious_packet(tmp_path):
    config = SimpleNamespace(
        curated_memory_assembly_enabled=True,
        curated_memory_view_compact_chars=120,
        curated_memory_view_standard_chars=220,
        curated_memory_view_expanded_chars=400,
    )
    assembler = KernelMemoryMemoryObjectAssembler(config)
    result = assembler.assemble(
        query="current quote",
        items=[{"id": "m1", "title": "Quote", "summary": "A long-ish summary that would normally allow a richer view."}],
        max_chars=800,
        response_mode="source_supported",
        answer_packet={"delivery_mode": "cautious"},
    )

    assert result["objects"][0]["selected_view"] == "compact"
    assert result["delivery_mode"] == "cautious"
