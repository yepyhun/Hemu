from __future__ import annotations

from agent.decision_memory_runtime import DecisionMemoryRuntime
from agent.decision_memory_types import DecisionCandidate


def _runtime(tmp_path):
    return DecisionMemoryRuntime.from_agent_config(
        {"enabled": True, "root_dir": str(tmp_path / "decision_memory"), "namespace": "test"},
        default_namespace="test",
        hermes_home=tmp_path,
    )


def test_decision_memory_runtime_builds_turn_context_from_candidates(tmp_path):
    runtime = _runtime(tmp_path)
    runtime.record_candidate(
        DecisionCandidate(
            kind="decision",
            subject="config.terminal.cwd.authority",
            fact_text="config.yaml is the authority for terminal cwd.",
            scope_type="session",
            scope_key="sess",
        )
    )

    text, meta = runtime.build_turn_context(
        user_message="continue using the chosen cwd",
        recent_user_turns=["use config.yaml for cwd"],
        active_replay_policy={"policy_name": "code_execution_continuation"},
        session_id="sess",
    )

    assert "# Decision Memory" in text
    assert "config.terminal.cwd.authority" in text
    assert meta["hit_count"] >= 1


def test_decision_memory_runtime_captures_ledger_failure_and_resolves_success(tmp_path):
    runtime = _runtime(tmp_path)
    created = runtime.capture_ledger_action(
        {
            "action_id": "act_fail",
            "tool_name": "terminal",
            "args_json": '{"command":"apt-get install libpq-dev"}',
            "failure_reason": "E: Package 'libpq-dev' has no installation candidate",
            "status": "failure",
        },
        session_id="sess",
    )
    runtime.capture_ledger_action(
        {
            "action_id": "act_ok",
            "tool_name": "terminal",
            "args_json": '{"command":"apt-get install libpq-dev"}',
            "status": "success",
        },
        session_id="sess",
    )
    snapshot = runtime.debug_snapshot()

    assert created
    assert snapshot["stats"]["total"] >= 2
    assert snapshot["stats"]["ledger_promoted_count"] >= 1
    assert any(item["subject"] == "tool.apt.libpq_dev" for item in snapshot["recent"])


def test_decision_memory_runtime_supersedes_conflicting_subject(tmp_path):
    runtime = _runtime(tmp_path)
    first = runtime.record_candidate(
        DecisionCandidate(
            kind="decision",
            subject="config.source",
            fact_text="localhost literal is the source.",
            scope_type="project",
            scope_key="test",
            source_type="assistant_inferred",
        )
    )
    second = runtime.record_candidate(
        DecisionCandidate(
            kind="decision",
            subject="config.source",
            fact_text="config.yaml is the source of truth.",
            scope_type="project",
            scope_key="test",
            source_type="runtime_normalization",
            source_ref="config.yaml",
        )
    )
    snapshot = runtime.debug_snapshot(limit=10)

    assert first is not None
    assert second is not None
    assert any(item["status"] == "superseded" for item in snapshot["recent"])
    assert snapshot["stats"]["superseded_filtered_count"] >= 1
    first_entry = next(item for item in snapshot["recent"] if item["id"] == first["id"])
    assert first_entry["feedback_negative"] >= 1


def test_decision_memory_runtime_can_disable_supersession_feedback(tmp_path):
    runtime = DecisionMemoryRuntime.from_agent_config(
        {
            "enabled": True,
            "root_dir": str(tmp_path / "decision_memory"),
            "namespace": "test",
            "stable_memory_feedback_enabled": False,
        },
        default_namespace="test",
        hermes_home=tmp_path,
    )
    first = runtime.record_candidate(
        DecisionCandidate(
            kind="decision",
            subject="config.source",
            fact_text="localhost literal is the source.",
            scope_type="project",
            scope_key="test",
            source_type="assistant_inferred",
        )
    )
    runtime.record_candidate(
        DecisionCandidate(
            kind="decision",
            subject="config.source",
            fact_text="config.yaml is the source of truth.",
            scope_type="project",
            scope_key="test",
            source_type="runtime_normalization",
            source_ref="config.yaml",
        )
    )
    snapshot = runtime.debug_snapshot(limit=10)
    first_entry = next(item for item in snapshot["recent"] if item["id"] == first["id"])
    assert first_entry["feedback_negative"] == 0
