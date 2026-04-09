import json

from agent.replay_duplicate_guard import ReplayDuplicateGuard
from agent.replay_execution_ledger import ReplayExecutionLedger


def test_replay_execution_ledger_records_and_renders_context(tmp_path):
    ledger = ReplayExecutionLedger.from_env_config(
        {
            "enabled": True,
            "root_dir": str(tmp_path / "ledger"),
            "recent_actions_limit": 4,
        },
        hermes_home=tmp_path,
    )

    first = ledger.record_tool_action(
        session_id="sess_ledger",
        tool_name="read_file",
        function_args={"path": "/workspace/app.py"},
        result_summary="Loaded /workspace/app.py successfully.",
        status="success",
        artifact_id="art_file123",
    )
    second = ledger.record_tool_action(
        session_id="sess_ledger",
        tool_name="search_files",
        function_args={"pattern": "auth"},
        result_summary="Found auth references in 3 files.",
        status="success",
    )

    assert first is not None
    assert second is not None
    recent = ledger.get_recent_actions("sess_ledger")
    assert len(recent) == 2
    context = ledger.build_turn_context("sess_ledger")
    assert "read_file" in context
    assert "search_files" in context
    assert "art_file123" in context


def test_replay_execution_ledger_keeps_failure_reason_and_change_digest(tmp_path):
    ledger = ReplayExecutionLedger.from_env_config(
        {
            "enabled": True,
            "root_dir": str(tmp_path / "ledger"),
        },
        hermes_home=tmp_path,
    )

    failure = ledger.record_tool_action(
        session_id="sess_fail",
        tool_name="terminal",
        function_args={"command": "apt-get install libpq-dev"},
        result_summary="E: Package 'libpq-dev' has no installation candidate",
        status="failure",
    )
    change = ledger.record_tool_action(
        session_id="sess_fail",
        tool_name="patch",
        function_args={"path": "/workspace/app.py", "patch": "@@\n-db_url = 'localhost'\n+db_url = os.getenv('DB')\n"},
        result_summary="Applied patch successfully.",
        status="success",
    )

    assert failure is not None
    assert "no installation candidate" in failure["failure_reason"]
    assert change is not None
    assert "db_url" in change["change_digest"]

    context = ledger.build_turn_context("sess_fail")
    assert "blocker:" in context
    assert "changed:" in context

    snapshot = ledger.debug_snapshot("sess_fail")
    assert snapshot["stats"]["total"] == 2
    assert snapshot["recent"][0]["tool_name"] in {"terminal", "patch"}


def test_replay_duplicate_guard_short_circuits_safe_exact_duplicate(tmp_path):
    ledger = ReplayExecutionLedger.from_env_config(
        {
            "enabled": True,
            "root_dir": str(tmp_path / "ledger"),
            "duplicate_window": 6,
        },
        hermes_home=tmp_path,
    )
    ledger.record_tool_action(
        session_id="sess_dup",
        tool_name="read_file",
        function_args={"path": "/workspace/app.py"},
        result_summary="Loaded /workspace/app.py successfully.",
        status="success",
        artifact_id="art_prev",
    )
    guard = ReplayDuplicateGuard.from_dict(
        {"enabled": True, "duplicate_window": 6},
        ledger=ledger,
    )

    payload = guard.maybe_short_circuit(
        session_id="sess_dup",
        tool_name="read_file",
        function_args={"path": "/workspace/app.py"},
    )

    assert payload is not None
    parsed = json.loads(payload)
    assert parsed["reason"] == "recent_duplicate_action"
    assert parsed["artifact_id"] == "art_prev"


def test_replay_duplicate_guard_does_not_short_circuit_unsafe_tools(tmp_path):
    ledger = ReplayExecutionLedger.from_env_config(
        {
            "enabled": True,
            "root_dir": str(tmp_path / "ledger"),
        },
        hermes_home=tmp_path,
    )
    ledger.record_tool_action(
        session_id="sess_dup",
        tool_name="terminal",
        function_args={"command": "ls"},
        result_summary="Listed files.",
        status="success",
    )
    guard = ReplayDuplicateGuard.from_dict({"enabled": True}, ledger=ledger)

    payload = guard.maybe_short_circuit(
        session_id="sess_dup",
        tool_name="terminal",
        function_args={"command": "ls"},
    )

    assert payload is None


def test_replay_execution_ledger_exposes_session_tool_totals(tmp_path):
    ledger = ReplayExecutionLedger.from_env_config(
        {
            "enabled": True,
            "root_dir": str(tmp_path / "ledger"),
        },
        hermes_home=tmp_path,
    )
    ledger.record_tool_action(
        session_id="sess_tools",
        tool_name="rehydrate_artifact",
        function_args={"artifact_id": "art_1"},
        result_summary="Rehydrated artifact art_1.",
        status="success",
    )
    ledger.record_tool_action(
        session_id="sess_tools",
        tool_name="rehydrate_artifact",
        function_args={"artifact_id": "art_2"},
        result_summary="Artifact not found.",
        status="failure",
    )
    ledger.record_tool_action(
        session_id="sess_tools",
        tool_name="read_file",
        function_args={"path": "/workspace/app.py"},
        result_summary="Loaded file.",
        status="success",
    )

    assert ledger.session_tool_totals("sess_tools") == {
        "rehydrate_artifact": 2,
        "read_file": 1,
    }
    assert ledger.session_tool_totals("sess_tools", status="success") == {
        "rehydrate_artifact": 1,
        "read_file": 1,
    }
