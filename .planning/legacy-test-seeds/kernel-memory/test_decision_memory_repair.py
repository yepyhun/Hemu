from __future__ import annotations

from agent.decision_memory_repair import repair_decision_noise
from agent.decision_memory_runtime import DecisionMemoryRuntime
from agent.decision_memory_types import DecisionCandidate


def _runtime(tmp_path):
    return DecisionMemoryRuntime.from_agent_config(
        {"enabled": True, "root_dir": str(tmp_path / "decision_memory"), "namespace": "test", "profile_memory_enabled": True},
        default_namespace="test",
        hermes_home=tmp_path,
    )


def test_repair_decision_noise_obsoletes_tool_and_file_error_payloads(tmp_path):
    runtime = _runtime(tmp_path)
    runtime.record_candidate(
        DecisionCandidate(
            kind="decision",
            subject="tool.patch",
            fact_text='{"success": false, "error": "old_string not found"}',
            scope_type="project",
            scope_key="test",
            confidence=0.6,
            importance=20,
            source_type="runtime",
            source_ref="sess-1",
        )
    )
    runtime.record_candidate(
        DecisionCandidate(
            kind="decision",
            subject="file._hermes-home_.hermes",
            fact_text='{"total_count": 0, "error": "Path not found"}',
            scope_type="project",
            scope_key="test",
            confidence=0.6,
            importance=20,
            source_type="runtime",
            source_ref="sess-2",
        )
    )

    result = repair_decision_noise(runtime=runtime, source_ref="repair-decision")
    snapshot = runtime.debug_snapshot(limit=20)

    assert result["issues_found"] == 2
    assert result["records_obsoleted"] >= 2
    assert any("tool_error_artifact" in item["problems"] for item in result["issues"])
    assert any("file_error_artifact" in item["problems"] for item in result["issues"])
    assert any(item["status"] == "obsolete" and item["subject"] == "tool.patch" for item in snapshot["recent"])
    assert any(item["status"] == "obsolete" and item["subject"] == "file._hermes-home_.hermes" for item in snapshot["recent"])


def test_repair_decision_noise_obsoletes_tool_failure_status_payloads(tmp_path):
    runtime = _runtime(tmp_path)
    runtime.record_candidate(
        DecisionCandidate(
            kind="decision",
            subject="tool.skill_manage",
            fact_text='{"status": "failure", "error": "old_string not found in the file."}',
            scope_type="project",
            scope_key="test",
            confidence=0.6,
            importance=20,
            source_type="runtime",
            source_ref="sess-3",
        )
    )

    result = repair_decision_noise(runtime=runtime, source_ref="repair-decision")
    snapshot = runtime.debug_snapshot(limit=20)

    assert result["issues_found"] == 1
    assert result["records_obsoleted"] >= 1
    assert result["issues"][0]["subject"] == "tool.skill_manage"
    assert "tool_error_artifact" in result["issues"][0]["problems"]
    assert any(item["status"] == "obsolete" and item["subject"] == "tool.skill_manage" for item in snapshot["recent"])


def test_repair_decision_noise_obsoletes_truncated_error_payloads(tmp_path):
    runtime = _runtime(tmp_path)
    runtime.record_candidate(
        DecisionCandidate(
            kind="decision",
            subject="tool.skill_manage",
            fact_text='{"success": false, "error": "old_string not found in the file.", "file_preview": "---\\nname: timezone-safe-reminders...',
            scope_type="project",
            scope_key="test",
            confidence=0.6,
            importance=20,
            source_type="runtime",
            source_ref="sess-4",
        )
    )

    result = repair_decision_noise(runtime=runtime, source_ref="repair-decision")
    snapshot = runtime.debug_snapshot(limit=20)

    assert result["issues_found"] == 1
    assert result["records_obsoleted"] >= 1
    assert result["issues"][0]["subject"] == "tool.skill_manage"
    assert any(item["status"] == "obsolete" and item["subject"] == "tool.skill_manage" for item in snapshot["recent"])
