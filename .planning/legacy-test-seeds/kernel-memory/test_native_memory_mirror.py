from __future__ import annotations

from agent.decision_memory_runtime import DecisionMemoryRuntime
from agent.native_memory_mirror import sync_native_memory_entries


def _runtime(tmp_path):
    return DecisionMemoryRuntime.from_agent_config(
        {"enabled": True, "root_dir": str(tmp_path / "decision_memory"), "namespace": "test", "profile_memory_enabled": True},
        default_namespace="test",
        hermes_home=tmp_path,
    )


def test_sync_native_user_memory_entries_mirrors_and_obsoletes_removed_entries(tmp_path):
    runtime = _runtime(tmp_path)

    first = sync_native_memory_entries(
        runtime=runtime,
        target="user",
        entries=["Keep replies concise and direct."],
        source_ref="sess-1",
    )
    second = sync_native_memory_entries(
        runtime=runtime,
        target="user",
        entries=["Always verify code paths before changing them."],
        source_ref="sess-2",
    )
    snapshot = runtime.debug_snapshot(limit=10)
    mirrored = [
        item for item in snapshot["recent"]
        if '"native_memory_target":"user"' in (item.get("metadata_json") or "")
    ]

    assert first.synced == 1
    assert second.obsoleted >= 1
    assert any(item["status"] == "active" and item["fact_text"] == "Always verify code paths before changing them." for item in mirrored)
    assert any(item["status"] == "obsolete" and item["fact_text"] == "Keep replies concise and direct." for item in mirrored)


def test_sync_native_memory_entries_creates_project_scoped_decision_records(tmp_path):
    runtime = _runtime(tmp_path)

    result = sync_native_memory_entries(
        runtime=runtime,
        target="memory",
        entries=["Use config.yaml as the source of truth."],
        source_ref="sess-1",
    )
    snapshot = runtime.debug_snapshot(limit=10)

    assert result.synced == 1
    assert any(
        item["source_type"] == "native_memory_tool"
        and item["scope_type"] == "project"
        and item["fact_text"] == "Use config.yaml as the source of truth."
        for item in snapshot["recent"]
    )
