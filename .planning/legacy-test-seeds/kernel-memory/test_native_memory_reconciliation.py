from __future__ import annotations

from agent.decision_memory_runtime import DecisionMemoryRuntime
from agent.memory_stack_policy import NativeMemoryPolicy
from agent.native_memory_reconciliation import reconcile_native_memory_store
from tools.memory_tool import MemoryStore


def _runtime(tmp_path):
    return DecisionMemoryRuntime.from_agent_config(
        {"enabled": True, "root_dir": str(tmp_path / "decision_memory"), "namespace": "test", "profile_memory_enabled": True},
        default_namespace="test",
        hermes_home=tmp_path,
    )


def test_reconcile_native_memory_store_migrates_structured_only_entries_and_keeps_compact_compatibility(tmp_path, monkeypatch):
    monkeypatch.setattr("tools.memory_tool.MEMORY_DIR", tmp_path / "memories")
    store = MemoryStore(memory_char_limit=2200, user_char_limit=1375)
    (tmp_path / "memories").mkdir(parents=True, exist_ok=True)
    (tmp_path / "memories" / "MEMORY.md").write_text(
        "Cronjob: use update (supports prompt); check jobs.json before answering today's tasks.\n§\n"
        "Laura 2026. február 22-én itthoni balesetben gerincsérülést szenvedett, és a hátsó lábaira lebénult.",
        encoding="utf-8",
    )
    (tmp_path / "memories" / "USER.md").write_text(
        "The user prefers to be called Tomi.\n§\nTomi is 19 years old.",
        encoding="utf-8",
    )
    runtime = _runtime(tmp_path)

    result = reconcile_native_memory_store(
        memory_store=store,
        runtime=runtime,
        native_policy=NativeMemoryPolicy(),
        source_ref="repair-1",
    )

    store.load_from_disk()
    assert "Tomi is 19 years old." not in store.user_entries
    assert "The user prefers to be called Tomi." in store.user_entries
    assert "Laura 2026. február 22-én itthoni balesetben gerincsérülést szenvedett, és a hátsó lábaira lebénult." not in store.memory_entries
    assert any(
        item["target"] == "structured_profile"
        for item in result["targets"]["memory"]["structured_migrations"]
    )
    assert any(
        entry["status"] == "active" and entry["subject"].startswith("user.context.sensitive_context.")
        for entry in runtime.debug_snapshot(limit=50)["recent"]
    )

