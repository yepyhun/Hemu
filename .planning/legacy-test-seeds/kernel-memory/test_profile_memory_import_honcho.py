from __future__ import annotations

from types import SimpleNamespace

from agent.decision_memory_runtime import DecisionMemoryRuntime
from agent.profile_memory_import_honcho import import_honcho_profile


def test_import_honcho_profile_converts_peer_card_to_profile_entries(tmp_path):
    runtime = DecisionMemoryRuntime.from_agent_config(
        {"enabled": True, "root_dir": str(tmp_path / "decision_memory"), "namespace": "test", "profile_memory_enabled": True},
        default_namespace="test",
        hermes_home=tmp_path,
    )
    manager = SimpleNamespace(
        get_or_create=lambda session_key: object(),
        get_peer_card=lambda session_key: [
            "Prefers concise technical answers.",
            "Never wants destructive git resets without approval.",
        ],
    )

    result = import_honcho_profile(
        session_key="sess-1",
        runtime=runtime,
        manager=manager,
        source_ref="honcho:sess-1",
    )
    snapshot = runtime.debug_snapshot(limit=10)

    assert result["success"] is True
    assert result["imported"] == 2
    assert any(item["metadata_json"] and '"profile_origin":"manual_import"' in item["metadata_json"] for item in snapshot["recent"])
