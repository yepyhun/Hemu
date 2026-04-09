from __future__ import annotations

from types import SimpleNamespace

from agent.kernel_memory_evidence_chain import KernelMemoryEvidenceChainAssembler


def test_evidence_chain_prefers_items_that_close_missing_facets():
    assembler = KernelMemoryEvidenceChainAssembler(SimpleNamespace())
    items = [
        {
            "id": "curated-1",
            "kind": "curated_memory",
            "route": "curated",
            "evidence_class": "curated_summary",
            "summary": "Laura prefers the dock quote.",
            "fused_score": 0.9,
        },
        {
            "id": "event-1",
            "kind": "event",
            "route": "semantic",
            "evidence_class": "graph_event",
            "summary": "The preference was corrected on Wednesday.",
            "temporal_markers": ["Wednesday"],
            "metadata": {"conflict_signal": "correction"},
            "fused_score": 0.5,
        },
        {
            "id": "source-1",
            "kind": "extract",
            "route": "source",
            "evidence_class": "direct_source",
            "content": "Original correction note.",
            "source_id": "doc:1",
            "fused_score": 0.4,
        },
    ]

    result = assembler.assemble(
        query="What is Laura's current favorite quote?",
        items=items,
        max_chars=1200,
    )

    assert [item["id"] for item in result["items"]] == ["curated-1", "event-1", "source-1"]
    assert result["chain_completeness_score"] == 1.0
    assert result["missing_link_penalty"] == 0.0
    assert "source_support" in result["covered_facets"]
    assert "dated_support" in result["covered_facets"]


def test_evidence_chain_reports_missing_links_for_incomplete_packets():
    assembler = KernelMemoryEvidenceChainAssembler(SimpleNamespace())
    items = [
        {
            "id": "curated-1",
            "kind": "curated_memory",
            "route": "curated",
            "evidence_class": "curated_summary",
            "summary": "Laura prefers the dock quote.",
            "fused_score": 0.9,
        }
    ]

    result = assembler.assemble(
        query="What is Laura's current favorite quote?",
        items=items,
        max_chars=1200,
    )

    assert result["chain_completeness_score"] < 1.0
    assert result["missing_link_penalty"] > 0.0
    assert "correction_check" in result["expected_facets"]


def test_evidence_chain_prefers_verified_item_when_other_signals_are_equal():
    assembler = KernelMemoryEvidenceChainAssembler(SimpleNamespace())
    items = [
        {
            "id": "curated-weak",
            "kind": "curated_memory",
            "route": "curated",
            "evidence_class": "curated_summary",
            "summary": "Laura prefers the dock quote.",
            "verification_state": "inferred",
            "quality_tier": "low",
            "fused_score": 0.95,
        },
        {
            "id": "curated-strong",
            "kind": "curated_memory",
            "route": "curated",
            "evidence_class": "curated_summary",
            "summary": "Laura prefers the dock quote.",
            "verification_state": "verified",
            "quality_tier": "high",
            "verification_evidence": ["tool:memory"],
            "artifact_refs": ["artifact:quote"],
            "fused_score": 0.95,
        },
    ]

    result = assembler.assemble(
        query="What is Laura's favorite quote?",
        items=items,
        max_chars=1200,
    )

    assert result["items"][0]["id"] == "curated-strong"
    assert result["verification_quality_score"] > 0.0
