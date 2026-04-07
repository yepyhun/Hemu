"""Legacy-inspired Core2 foundation tests.

These cases pull the useful bootstrap/runtime/store assertions forward from the
older kernel-memory suite, but bind them to the real Core2 provider surface
that exists today.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from plugins.memory import load_memory_provider


def _init_core2(tmp_path, session_id: str = "core2-legacy"):
    provider = load_memory_provider("core2")
    assert provider is not None
    provider.initialize(session_id, hermes_home=str(tmp_path), platform="cli")
    return provider


def _db_path(tmp_path) -> Path:
    return Path(tmp_path) / "core2" / "core2.db"


def test_core2_recall_abstains_when_store_is_empty(tmp_path):
    provider = _init_core2(tmp_path)

    payload = json.loads(
        provider.handle_tool_call(
            "core2_recall",
            {"query": "orbital mechanics", "mode": "exact_source_required", "risk_class": "high"},
        )
    )

    assert payload["abstained"] is True
    assert payload["support_tier"] == "none"
    assert payload["confidence"] == "low"
    assert "No stored Core2 notes matched" in payload["reason"]

    provider.shutdown()


def test_core2_provider_validates_error_paths(tmp_path):
    provider = load_memory_provider("core2")
    assert provider is not None

    uninitialized = json.loads(provider.handle_tool_call("core2_recall", {"query": "anything"}))
    assert uninitialized == {"error": "Core2 runtime is not initialized."}

    provider.initialize("core2-errors", hermes_home=str(tmp_path), platform="cli")

    missing_content = json.loads(provider.handle_tool_call("core2_remember", {}))
    assert missing_content == {"error": "content is required"}

    missing_object = json.loads(provider.handle_tool_call("core2_explain", {}))
    assert missing_object == {"error": "object_id is required"}

    unknown_tool = json.loads(provider.handle_tool_call("core2_unknown", {}))
    assert unknown_tool == {"error": "Unknown tool: core2_unknown"}

    provider.shutdown()


def test_core2_persists_notes_across_reinitialization(tmp_path):
    provider = _init_core2(tmp_path, session_id="core2-persist-a")

    stored = json.loads(
        provider.handle_tool_call(
            "core2_remember",
            {
                "content": "Mars transfer windows depend on orbital geometry.",
                "title": "orbital note",
                "namespace": "library",
                "risk_class": "standard",
                "language": "en",
                "effective_from": "2026-04-06T00:00:00+00:00",
            },
        )
    )
    object_id = stored["object_id"]
    provider.shutdown()

    reloaded = _init_core2(tmp_path, session_id="core2-persist-b")

    explained = json.loads(reloaded.handle_tool_call("core2_explain", {"object_id": object_id}))
    assert explained["object_id"] == object_id
    assert explained["title"] == "orbital note"
    assert explained["namespace"] == "library"
    assert "orbital geometry" in explained["content"]

    recalled = json.loads(
        reloaded.handle_tool_call(
            "core2_recall",
            {"query": "transfer windows", "mode": "source_supported", "risk_class": "standard"},
        )
    )
    assert recalled["abstained"] is False
    assert any(item["object_id"] == object_id for item in recalled["items"])

    reloaded.shutdown()


def test_core2_sync_turn_writes_turn_history_to_sqlite(tmp_path):
    provider = _init_core2(tmp_path, session_id="core2-turns")

    provider.sync_turn(
        "Please remember my deployment checklist.",
        "Stored the deployment checklist.",
        session_id="core2-turns",
    )

    provider.shutdown()

    conn = sqlite3.connect(_db_path(tmp_path))
    try:
        row = conn.execute(
            """
            SELECT session_id, user_content, assistant_content
            FROM core2_turns
            ORDER BY created_at DESC
            LIMIT 1
            """
        ).fetchone()
    finally:
        conn.close()

    assert row == (
        "core2-turns",
        "Please remember my deployment checklist.",
        "Stored the deployment checklist.",
    )


def test_core2_prefetch_is_consumed_once(tmp_path):
    provider = _init_core2(tmp_path, session_id="core2-prefetch")

    json.loads(
        provider.handle_tool_call(
            "core2_remember",
            {
                "content": "The user prefers concise release summaries.",
                "title": "release style",
                "namespace": "personal",
                "risk_class": "standard",
                "language": "en",
            },
        )
    )

    provider.queue_prefetch("release summaries", session_id="core2-prefetch")

    first = provider.prefetch("unused", session_id="core2-prefetch")
    second = provider.prefetch("unused", session_id="core2-prefetch")

    assert "# Core2 Prefetch" in first
    assert "release style" in first
    assert second == ""

    provider.shutdown()


def test_core2_recall_clamps_max_items_to_twelve(tmp_path):
    provider = _init_core2(tmp_path, session_id="core2-max-items")

    for idx in range(15):
        json.loads(
            provider.handle_tool_call(
                "core2_remember",
                {
                    "content": f"Orbital note {idx} tracks the same launch window.",
                    "title": f"orbital-{idx}",
                    "namespace": "project",
                    "risk_class": "standard",
                    "language": "en",
                },
            )
        )

    payload = json.loads(
        provider.handle_tool_call(
            "core2_recall",
            {"query": "launch window orbital", "mode": "compact_memory", "max_items": 50},
        )
    )

    assert payload["abstained"] is False
    assert len(payload["items"]) == 12
    assert payload["support_tier"] == "compact_memory"

    provider.shutdown()


def test_core2_on_memory_write_routes_builtin_memory_into_namespaces(tmp_path):
    provider = _init_core2(tmp_path, session_id="core2-builtin-write")

    provider.on_memory_write("add", "user", "Timezone: Europe/Budapest")
    provider.on_memory_write("add", "tool", "Repo root: /workspace/hermes")
    provider.on_memory_write("remove", "user", "this should be ignored")

    personal = json.loads(
        provider.handle_tool_call("core2_recall", {"query": "Europe/Budapest", "mode": "compact_memory"})
    )
    project = json.loads(
        provider.handle_tool_call("core2_recall", {"query": "/workspace/hermes", "mode": "compact_memory"})
    )

    assert personal["abstained"] is False
    assert personal["items"][0]["namespace"] == "personal"
    assert personal["items"][0]["source_type"] in {"builtin_memory", "digested_fact"}
    assert "Europe/Budapest" in str(personal["items"][0]["content"])

    assert project["abstained"] is False
    assert project["items"][0]["namespace"] == "project"
    assert project["items"][0]["source_type"] == "builtin_memory"

    provider.shutdown()
