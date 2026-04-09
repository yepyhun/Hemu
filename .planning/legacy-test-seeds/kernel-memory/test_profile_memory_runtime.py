from __future__ import annotations

from agent.decision_memory_runtime import DecisionMemoryRuntime


def _runtime(tmp_path):
    return DecisionMemoryRuntime.from_agent_config(
        {"enabled": True, "root_dir": str(tmp_path / "decision_memory"), "namespace": "test", "profile_memory_enabled": True},
        default_namespace="test",
        hermes_home=tmp_path,
    )


def test_profile_memory_runtime_records_and_renders_user_preference(tmp_path):
    runtime = _runtime(tmp_path)

    created = runtime.capture_profile_turn(
        user_message="Please remember that I prefer short, direct answers.",
        source_ref="sess-1",
    )
    text, meta = runtime.build_turn_context(
        user_message="What do you know about my preferences?",
        recent_user_turns=["remember my answer style"],
        active_replay_policy={"policy_name": "conversation"},
        session_id="sess-1",
    )

    assert created
    assert "# Profile Memory" in text
    assert "prefers short, direct answers" in text
    assert meta["profile"]["hit_count"] >= 1


def test_profile_memory_runtime_keeps_profile_entries_out_of_decision_strip(tmp_path):
    runtime = _runtime(tmp_path)

    runtime.capture_profile_turn(
        user_message="Always keep answers concise.",
        source_ref="sess-1",
    )
    text, _meta = runtime.build_turn_context(
        user_message="What are my constraints?",
        recent_user_turns=["answer constraints"],
        active_replay_policy={"policy_name": "conversation"},
        session_id="sess-1",
    )

    assert text.count("# Profile Memory") == 1
    assert "# Decision Memory" not in text
