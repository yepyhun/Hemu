from __future__ import annotations

import json

from plugins.memory import load_memory_provider


def _init_core2(tmp_path, session_id: str = "core2-transitions"):
    provider = load_memory_provider("core2")
    assert provider is not None
    provider.initialize(session_id, hermes_home=str(tmp_path), platform="cli")
    return provider


def test_candidate_can_be_rejected_without_being_deleted(tmp_path):
    provider = _init_core2(tmp_path)
    runtime = provider.runtime
    assert runtime is not None

    candidate = runtime.record_candidate_extract(
        "A noisy partial snippet with no durable value.",
        title="noise candidate",
        namespace="project",
        risk_class="standard",
        language="en",
    )
    assert runtime.reject_candidate(candidate["object_id"], reason="noise")

    explained = json.loads(provider.handle_tool_call("core2_explain", {"object_id": candidate["object_id"]}))
    assert explained["state_status"] == "rejected"
    assert explained["source_record"] is not None
    assert any(step["to_state"] == "rejected" for step in explained["transitions"])

    provider.shutdown()


def test_candidate_can_be_promoted_to_canonical(tmp_path):
    provider = _init_core2(tmp_path, session_id="core2-promote")
    runtime = provider.runtime
    assert runtime is not None

    candidate = runtime.record_candidate_extract(
        "User prefers keyboard-driven workflows.",
        title="workflow preference",
        namespace="personal",
        risk_class="standard",
        language="en",
    )

    assert runtime.promote_candidate(candidate["object_id"], reason="stable_preference")

    explained = json.loads(provider.handle_tool_call("core2_explain", {"object_id": candidate["object_id"]}))
    assert explained["state_status"] == "canonical_active"
    assert any(step["to_state"] == "canonical_active" for step in explained["transitions"])

    provider.shutdown()


def test_stale_provisional_is_archived_by_maintenance(tmp_path):
    provider = _init_core2(tmp_path, session_id="core2-stale")
    runtime = provider.runtime
    assert runtime is not None

    provisional = runtime.ingest_note(
        "Possible deployment note pending confirmation.",
        title="deployment note",
        namespace="project",
        risk_class="standard",
        language="en",
        metadata={
            "state_status": "provisional",
            "recorded_at": "2026-01-01T00:00:00+00:00",
        },
    )

    result = runtime.run_maintenance(now="2026-04-15T00:00:00+00:00", stale_days=30)
    explained = json.loads(provider.handle_tool_call("core2_explain", {"object_id": provisional["object_id"]}))

    assert result["stale_provisionals_archived"] >= 1
    assert explained["state_status"] == "archived"

    provider.shutdown()


def test_maintenance_processes_pending_supersession_metadata(tmp_path):
    provider = _init_core2(tmp_path, session_id="core2-maint-supersede")
    runtime = provider.runtime
    assert runtime is not None

    old_record = runtime.ingest_note(
        "The deployment window is Friday.",
        title="deployment window",
        namespace="project",
        risk_class="standard",
        language="en",
        metadata={"identity_key": "deploy.window"},
    )
    runtime.ingest_note(
        "The deployment window is Monday.",
        title="deployment window",
        namespace="project",
        risk_class="standard",
        language="en",
        metadata={"identity_key": "deploy.window", "supersedes": old_record["object_id"]},
    )

    result = runtime.run_maintenance()
    old_explained = json.loads(provider.handle_tool_call("core2_explain", {"object_id": old_record["object_id"]}))

    assert result["superseded_records"] >= 1
    assert old_explained["state_status"] == "superseded"

    provider.shutdown()


def test_archiving_is_non_destructive_for_forgetting(tmp_path):
    provider = _init_core2(tmp_path, session_id="core2-archive")
    runtime = provider.runtime
    assert runtime is not None

    record = runtime.ingest_note(
        "Temporary project note.",
        title="temporary note",
        namespace="project",
        risk_class="standard",
        language="en",
    )
    assert runtime.archive_object(record["object_id"], reason="manual_forgetting")

    explained = json.loads(provider.handle_tool_call("core2_explain", {"object_id": record["object_id"]}))
    recall = json.loads(provider.handle_tool_call("core2_recall", {"query": "temporary note", "mode": "compact_memory"}))

    assert explained["state_status"] == "archived"
    assert recall["abstained"] is True

    provider.shutdown()
