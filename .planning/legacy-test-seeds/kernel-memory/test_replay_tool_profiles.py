from agent.replay_tool_profiles import ReplayToolProfiles


def _tool(name: str) -> dict:
    return {"type": "function", "function": {"name": name}}


def test_replay_tool_profiles_choose_code_profile_from_message():
    profiles = ReplayToolProfiles.from_dict({"enabled": True})
    profile, allowed = profiles.allowed_tool_names(
        tools=[_tool("terminal"), _tool("read_file"), _tool("write_file"), _tool("todo"), _tool("memory")],
        user_message="Find the bug in this file and patch it",
        messages=[],
    )

    assert profile == "code"
    assert allowed is not None
    assert "terminal" in allowed
    assert "write_file" in allowed


def test_replay_tool_profiles_choose_research_profile_from_recent_tools():
    profiles = ReplayToolProfiles.from_dict({"enabled": True})
    messages = [
        {
            "role": "assistant",
            "tool_calls": [
                {"function": {"name": "web_search"}},
            ],
        }
    ]
    profile, allowed = profiles.allowed_tool_names(
        tools=[_tool("web_search"), _tool("web_extract"), _tool("browser_navigate"), _tool("terminal"), _tool("memory")],
        user_message="Any update?",
        messages=messages,
    )

    assert profile == "research"
    assert allowed is not None
    assert "web_search" in allowed
    assert "browser_navigate" in allowed
    assert "terminal" not in allowed


def test_replay_tool_profiles_conversation_profile_keeps_core_only():
    profiles = ReplayToolProfiles.from_dict({"enabled": True})
    profile, allowed = profiles.allowed_tool_names(
        tools=[_tool("memory"), _tool("todo"), _tool("cronjob"), _tool("clarify"), _tool("terminal")],
        user_message="Thanks, just explain what happened",
        messages=[],
    )

    assert profile == "conversation"
    assert allowed == ["clarify", "memory", "todo"]


def test_replay_tool_profiles_use_ledger_recent_tools_as_workload_hint():
    profiles = ReplayToolProfiles.from_dict({"enabled": True})
    profile, allowed = profiles.allowed_tool_names(
        tools=[_tool("terminal"), _tool("read_file"), _tool("write_file"), _tool("memory")],
        user_message="continue",
        messages=[],
        ledger_recent_tools=["write_file", "read_file"],
    )

    assert profile == "code"
    assert "write_file" in (allowed or [])


def test_replay_tool_profiles_use_telemetry_counts_as_secondary_hint():
    profiles = ReplayToolProfiles.from_dict({"enabled": True})
    profile, allowed = profiles.allowed_tool_names(
        tools=[_tool("web_search"), _tool("browser_navigate"), _tool("memory"), _tool("terminal")],
        user_message="continue",
        messages=[],
        telemetry_counts={"web_search": 3, "browser_navigate": 2},
    )

    assert profile == "research"
    assert "web_search" in (allowed or [])


def test_replay_tool_profiles_choose_task_for_hungarian_reminder_request():
    profiles = ReplayToolProfiles.from_dict({"enabled": True})
    profile, allowed = profiles.allowed_tool_names(
        tools=[_tool("memory"), _tool("todo"), _tool("cronjob"), _tool("clarify"), _tool("terminal")],
        user_message="Állíts be egy emlékeztetőt ma 23:43-ra, hogy szóljak Györgynek.",
        messages=[],
    )

    assert profile == "task"
    assert "cronjob" in (allowed or [])


def test_replay_tool_profiles_explicit_task_overrides_recent_code_tools():
    profiles = ReplayToolProfiles.from_dict({"enabled": True})
    messages = [
        {
            "role": "assistant",
            "tool_calls": [
                {"function": {"name": "terminal"}},
                {"function": {"name": "read_file"}},
            ],
        }
    ]
    profile, allowed = profiles.allowed_tool_names(
        tools=[_tool("memory"), _tool("todo"), _tool("cronjob"), _tool("clarify"), _tool("terminal"), _tool("read_file")],
        user_message="Állíts be egy emlékeztetőt holnap 7-re.",
        messages=messages,
    )

    assert profile == "task"
    assert "cronjob" in (allowed or [])
    assert "terminal" not in (allowed or [])


def test_replay_tool_profiles_technical_branch_bug_stays_in_code_profile():
    profiles = ReplayToolProfiles.from_dict({"enabled": True})
    profile, allowed = profiles.allowed_tool_names(
        tools=[_tool("terminal"), _tool("read_file"), _tool("patch"), _tool("todo"), _tool("cronjob")],
        user_message="Investigate the branch prediction bug in the compiler.",
        messages=[],
    )

    assert profile == "code"
    assert "terminal" in (allowed or [])
    assert "cronjob" not in (allowed or [])


def test_replay_tool_profiles_explicit_explanation_overrides_recent_code_tools():
    profiles = ReplayToolProfiles.from_dict({"enabled": True})
    messages = [
        {
            "role": "assistant",
            "tool_calls": [
                {"function": {"name": "terminal"}},
                {"function": {"name": "read_file"}},
            ],
        }
    ]
    profile, allowed = profiles.allowed_tool_names(
        tools=[_tool("memory"), _tool("todo"), _tool("clarify"), _tool("terminal"), _tool("read_file")],
        user_message="Just explain what happened.",
        messages=messages,
    )

    assert profile == "conversation"
    assert allowed == ["clarify", "memory", "todo"]
