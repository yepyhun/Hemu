from __future__ import annotations

import json

from agent.core2_invariants import (
    check_current_state_uniqueness,
    check_structured_truth_precedence,
    core2_invariant_specs,
)
from agent.core2_noise_repair import repair_core2_noise
from agent.core2_runtime import Core2Runtime
from agent.core2_authoritative import try_authoritative_answer
from plugins.memory import load_memory_provider


def _init_core2(tmp_path, session_id: str):
    provider = load_memory_provider("core2")
    assert provider is not None
    provider.initialize(session_id, hermes_home=str(tmp_path), platform="cli")
    return provider


def test_core2_invariant_catalog_is_small_and_explicit():
    specs = core2_invariant_specs()
    ids = [spec.invariant_id for spec in specs]
    assert ids == ["INV-1", "INV-2", "INV-3"]
    assert len(specs) == 3
    assert all(spec.rule and spec.checker for spec in specs)


def test_invariant_structured_truth_precedence_for_covered_family(tmp_path):
    provider = _init_core2(tmp_path, "invariant-structured-truth")
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
        packet = runtime.recall(
            "Can you suggest some activities that I can do in the evening?",
            mode="source_supported",
            operator=None,
            risk_class="standard",
            max_items=6,
        )
        check = check_structured_truth_precedence(packet)
        resolved = try_authoritative_answer(
            "Can you suggest some activities that I can do in the evening?",
            packet,
        )
    finally:
        provider.shutdown()

    assert check["ok"] is True
    assert check["retrieval_path"] == "fact_first"
    assert resolved is not None
    assert "relaxing activities" in str(resolved["text"]).lower()


def test_invariant_current_state_uniqueness_for_deterministic_current_facts(tmp_path):
    provider = _init_core2(tmp_path, "invariant-current-uniqueness")
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
        result = check_current_state_uniqueness(runtime.store.list_canonical_objects())
    finally:
        provider.shutdown()

    assert result["ok"] is True
    assert result["collision_count"] == 0


def test_noise_repair_rejects_obvious_artifacts_only(tmp_path):
    runtime = Core2Runtime(":memory:")
    runtime.initialize("noise-repair")
    try:
        good = runtime.ingest_note(
            "I prefer green tea in the afternoon.",
            title="tea preference",
            namespace="personal",
            risk_class="standard",
            language="en",
        )
        tool_bad = runtime.ingest_note(
            json.dumps({"error": "permission denied", "success": False}),
            title="tool.exec",
            namespace="workspace",
            risk_class="standard",
            language="en",
            source_type="tool_artifact",
            metadata={"noise_fixture": True},
        )
        file_bad = runtime.ingest_note(
            json.dumps({"status": "error", "error": "file not found"}),
            title="file.config",
            namespace="workspace",
            risk_class="standard",
            language="en",
            source_type="file_artifact",
            metadata={"noise_fixture": True},
        )

        result = repair_core2_noise(runtime=runtime, source_ref="pytest:noise-repair")

        repaired_tool = runtime.store.get_canonical_object(tool_bad["object_id"])
        repaired_file = runtime.store.get_canonical_object(file_bad["object_id"])
        good_record = runtime.store.get_canonical_object(good["object_id"])
    finally:
        runtime.shutdown()

    assert result["success"] is True
    assert result["issues_found"] == 2
    assert result["records_repaired"] == 2
    assert repaired_tool is not None
    assert repaired_file is not None
    assert good_record is not None
    assert repaired_tool["state_status"] == "rejected"
    assert repaired_file["state_status"] == "rejected"
    assert good_record["state_status"] == "canonical_active"
    assert "noise_repair" in repaired_tool["metadata"]
    assert "noise_repair" in repaired_file["metadata"]
