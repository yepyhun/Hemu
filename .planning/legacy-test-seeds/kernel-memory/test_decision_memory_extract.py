from __future__ import annotations

from agent.decision_memory_extract import (
    decision_candidate_from_runtime_normalization,
    decision_candidates_from_ledger_action,
    subject_for_ledger_action,
)


def test_decision_extracts_unknown_from_failed_apt_install():
    row = {
        "action_id": "act_1",
        "tool_name": "terminal",
        "args_json": '{"command":"apt-get install libpq-dev"}',
        "failure_reason": "E: Package 'libpq-dev' has no installation candidate",
        "status": "failure",
    }

    candidates = decision_candidates_from_ledger_action(row, session_id="sess")

    assert len(candidates) == 1
    assert candidates[0].kind == "unknown"
    assert candidates[0].subject == "tool.apt.libpq_dev"
    assert "installation candidate" in candidates[0].fact_text
    assert subject_for_ledger_action(row) == "tool.apt.libpq_dev"


def test_decision_extracts_runtime_normalization_candidate():
    candidate = decision_candidate_from_runtime_normalization(
        subject="runtime.provider_model",
        fact_text="OpenAI Codex auth only supports visible Codex models.",
        kind="constraint",
    )

    assert candidate.kind == "constraint"
    assert candidate.subject == "runtime.provider_model"

