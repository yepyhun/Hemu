from __future__ import annotations

from agent.kernel_memory import KernelMemoryConfig
from agent.kernel_memory_memory_objects import KernelMemoryMemoryObjectAssembler


def test_memory_object_assembler_builds_compact_query_specific_assembly(tmp_path):
    assembler = KernelMemoryMemoryObjectAssembler(
        KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel", namespace="bestie")
    )
    assembly = assembler.assemble(
        query="coffee preference",
        items=[
            {
                "id": "cur-1",
                "title": "User preference: coffee",
                "summary": "The user prefers concise coffee tasting notes with origin and roast level only.",
                "metadata": {},
                "source_ids": ["doc:1"],
                "claim_ids": [],
                "entity_ids": [],
                "relation_ids": [],
                "route": "curated",
            }
        ],
        max_chars=320,
        response_mode="source_supported",
    )

    assert assembly["objects"]
    assert assembly["objects"][0]["memory_class"] == "profile_preference"
    assert assembly["text"].startswith("Curated memory assembly:")
    assert assembly["saved_chars"] >= 0


def test_memory_object_assembler_becomes_cautious_for_low_grounding(tmp_path):
    assembler = KernelMemoryMemoryObjectAssembler(
        KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel", namespace="bestie")
    )
    assembly = assembler.assemble(
        query="what is the current rehab rule",
        items=[
            {
                "id": "cur-1",
                "title": "Operational rule",
                "summary": "Only promise reminders when the scheduler tool is available.",
                "metadata": {"memory_class": "operational_rule"},
                "source_ids": ["doc:1"],
                "claim_ids": ["cl-1"],
                "entity_ids": [],
                "relation_ids": [],
                "route": "curated",
            },
            {
                "id": "cur-2",
                "title": "Fallback note",
                "summary": "Older summary that may be stale.",
                "metadata": {},
                "source_ids": [],
                "claim_ids": [],
                "entity_ids": [],
                "relation_ids": [],
                "route": "curated",
            },
        ],
        max_chars=320,
        response_mode="source_supported",
        answer_packet={
            "delivery_mode": "abstain_or_ask",
            "confidence_tier": "low",
            "should_abstain": True,
            "warnings": ["insufficient_grounding", "missing_answer_anchor"],
        },
    )

    assert assembly["should_abstain"] is True
    assert len(assembly["objects"]) == 1
    assert "partial support only" in assembly["text"]
    assert "Warnings:" in assembly["text"]
