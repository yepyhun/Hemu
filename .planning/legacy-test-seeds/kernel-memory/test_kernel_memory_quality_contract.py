from __future__ import annotations

from agent.kernel_memory import KernelMemoryConfig, KernelMemoryStore
from agent.kernel_memory_quality_contract import derive_quality_contract
from agent.kernel_memory_retrieval import KernelMemoryRetriever
from agent.kernel_memory_semantic_policy import record_answer_usefulness
from agent.kernel_memory_usefulness import summarize_retrieval_usefulness


def test_quality_contract_derives_verified_grounded_fields():
    contract = derive_quality_contract(
        kind="claim",
        confidence=0.91,
        status="active",
        metadata={
            "verified": True,
            "verification_evidence": ["source:doc:1", "source:doc:1"],
            "artifact_refs": ["art-2", "art-1"],
            "tool_name": "memory",
        },
        provenance={
            "resource_ids": ["res-2", "res-1"],
        },
    )

    assert contract["verification_state"] == "verified"
    assert contract["quality_tier"] == "high"
    assert contract["verification_evidence"] == ["source:doc:1"]
    assert contract["artifact_refs"] == ["art-1", "art-2"]
    assert contract["source_tool"] == "memory"


def test_retrieval_usefulness_dedupes_per_route_ids():
    summary = summarize_retrieval_usefulness(
        items=[
            {"id": "cur-1", "route": "curated"},
            {"id": "cur-1", "route": "curated"},
            {"id": "evt-1", "route": "graph"},
        ],
        evidence_items=[
            {"id": "cur-1", "route": "curated"},
            {"id": "cur-1", "route": "curated"},
        ],
    )

    assert summary["retrieved_count"] == 2
    assert summary["useful_count"] == 1
    assert summary["missed_count"] == 1
    assert summary["usefulness_rate"] == 0.5
    assert summary["miss_rate"] == 0.5
    assert summary["noise_rate"] == 0.5
    assert summary["route_value_breakdown"]["curated"]["retrieved"] == 1
    assert summary["route_value_breakdown"]["curated"]["useful"] == 1
    assert summary["route_value_breakdown"]["curated"]["missed"] == 0
    assert summary["route_value_breakdown"]["graph"]["retrieved"] == 1
    assert summary["route_value_breakdown"]["graph"]["useful"] == 0
    assert summary["route_value_breakdown"]["graph"]["missed"] == 1


def test_record_answer_usefulness_keeps_retrieval_counts_consistent():
    patch = record_answer_usefulness(
        record={
            "confidence": 0.86,
            "derivation_count": 1,
            "status": "active",
            "retrieval_count": 0,
            "successful_retrieval_count": 0,
            "retrieval_miss_count": 0,
            "used_in_answer_count": 0,
            "last_retrieved_at": None,
        },
        used_at="2026-04-04T12:00:00+00:00",
    )

    assert patch["retrieval_count"] == 1
    assert patch["successful_retrieval_count"] == 1
    assert patch["retrieval_miss_count"] == 0
    assert patch["used_in_answer_count"] == 1
    assert patch["last_retrieved_at"] == "2026-04-04T12:00:00+00:00"
    assert patch["last_used_in_answer_at"] == "2026-04-04T12:00:00+00:00"


def test_preview_retrieval_tracks_quality_and_answer_usefulness(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        retrieval_policy_order=["curated"],
    )
    store = KernelMemoryStore.from_config(config)
    memory = store.materialize_curated_memory(
        title="Scheduler rule",
        summary="Only promise reminders when a scheduler tool is actually available.",
        metadata={
            "verified": True,
            "verification_evidence": ["tool:memory"],
            "artifact_refs": ["artifact:scheduler"],
            "source_tool": "memory",
        },
    )
    retriever = KernelMemoryRetriever(config, store)

    preview = retriever.preview_retrieval(
        "What is the scheduler rule for reminders?",
        max_records=2,
        max_chars=1200,
    )

    item = preview["retrieval"]["items"][0]
    refreshed = store.get_record("curated_memory", memory["id"])

    assert item["verification_state"] == "verified"
    assert item["quality_tier"] == "high"
    assert preview["retrieval"]["telemetry"]["retrieved_count"] == 1
    assert preview["retrieval"]["telemetry"]["useful_count"] == 1
    assert preview["retrieval"]["telemetry"]["missed_count"] == 0
    assert preview["retrieval"]["telemetry"]["usefulness_rate"] == 1.0
    assert preview["retrieval"]["telemetry"]["route_value_breakdown"]["curated"]["useful"] == 1
    assert refreshed is not None
    assert refreshed["retrieval_count"] == 1
    assert refreshed["successful_retrieval_count"] == 1
    assert refreshed["retrieval_miss_count"] == 0
    assert refreshed["used_in_answer_count"] == 1
    assert refreshed["last_used_in_answer_at"]
