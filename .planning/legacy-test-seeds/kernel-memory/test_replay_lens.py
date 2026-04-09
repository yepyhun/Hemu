from agent.replay_lens import ReplayLens, ReplayLensConfig


def test_replay_lens_leaves_short_history_unchanged():
    lens = ReplayLens(ReplayLensConfig(enabled=True, min_messages=6, keep_last_n=3))
    messages = [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi"},
        {"role": "user", "content": "short thread"},
    ]

    rewritten, meta = lens.rewrite_history(messages)

    assert rewritten == messages
    assert meta["applied"] is False


def test_replay_lens_condenses_older_tool_history():
    lens = ReplayLens(
        ReplayLensConfig(
            enabled=True,
            min_messages=8,
            keep_last_n=3,
            max_recent_tool_runs=4,
            max_summary_chars=3000,
        )
    )
    messages = [
        {"role": "user", "content": "Find the auth bug and fix it"},
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "search_text",
                        "arguments": "{\"query\":\"auth\"}",
                    },
                }
            ],
        },
        {
            "role": "tool",
            "tool_call_id": "call_1",
            "content": "Found 17 matches in /workspace/run_agent.py",
        },
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "call_2",
                    "type": "function",
                    "function": {
                        "name": "read_file",
                        "arguments": "{\"path\":\"/workspace/run_agent.py\"}",
                    },
                }
            ],
        },
        {
            "role": "tool",
            "tool_call_id": "call_2",
            "content": "error: none\npath=/workspace/run_agent.py\nstatus=ok",
        },
        {"role": "assistant", "content": "I found the root cause in auth flow."},
        {"role": "user", "content": "Apply the patch and verify tests."},
        {"role": "assistant", "content": "Working on the patch."},
        {"role": "user", "content": "Any update?"},
    ]

    rewritten, meta = lens.rewrite_history(messages)

    assert meta["applied"] is True
    assert len(rewritten) == 4
    assert rewritten[0]["role"] == "assistant"
    assert "[REPLAY LENS]" in rewritten[0]["content"]
    assert "Find the auth bug" in rewritten[0]["content"]
    assert "search_text" in rewritten[0]["content"]
    assert "read_file" in rewritten[0]["content"]
    assert rewritten[-1]["content"] == "Any update?"


def test_replay_lens_uses_artifact_descriptor_when_available():
    lens = ReplayLens(
        ReplayLensConfig(
            enabled=True,
            min_messages=6,
            keep_last_n=2,
            max_recent_tool_runs=4,
            max_summary_chars=3000,
        )
    )
    messages = [
        {"role": "user", "content": "Find why nginx is failing"},
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "terminal",
                        "arguments": "{\"command\":\"tail -n 200 /var/log/nginx/error.log\"}",
                    },
                }
            ],
        },
        {
            "role": "tool",
            "tool_call_id": "call_1",
            "content": "very large log output",
        },
        {"role": "assistant", "content": "Checking the error log."},
        {"role": "user", "content": "What did you find?"},
        {"role": "assistant", "content": "Still processing."},
    ]

    artifact_by_index = {
        2: {
            "artifact_id": "art_deadbeef1234",
            "summary": "nginx error log shows upstream timeout and permission denied",
            "char_count": 18234,
        }
    }

    rewritten, meta = lens.rewrite_history(messages, artifact_lookup=artifact_by_index.get)

    assert meta["applied"] is True
    assert "art_deadbeef1234" in rewritten[0]["content"]
    assert "upstream timeout" in rewritten[0]["content"]


def test_replay_lens_small_turn_fast_path_preserves_original_messages():
    lens = ReplayLens(
        ReplayLensConfig(
            enabled=True,
            min_messages=4,
            keep_last_n=2,
            small_turn_raw_max_tokens=200,
        )
    )
    messages = [
        {"role": "user", "content": "Quote the exact source."},
        {"role": "assistant", "content": "I will use the exact source."},
        {"role": "user", "content": "Do not summarize it."},
        {"role": "assistant", "content": "Understood."},
    ]

    rewritten, meta = lens.rewrite_history(messages)

    assert rewritten == messages
    assert meta["applied"] is False
    assert meta["reason"] == "small_turn_fast_path"


def test_replay_lens_skips_condense_when_summary_is_not_cheaper():
    lens = ReplayLens(
        ReplayLensConfig(
            enabled=True,
            min_messages=4,
            keep_last_n=2,
            small_turn_raw_max_tokens=80,
        )
    )
    messages = [
        {"role": "user", "content": "follow this task"},
        {"role": "assistant", "content": "understood"},
        {"role": "user", "content": "continue"},
        {"role": "user", "content": "continue"},
    ]

    rewritten, meta = lens.rewrite_history(messages)

    assert rewritten == messages
    assert meta["applied"] is False
    assert meta["reason"] == "small_turn_fast_path"


def test_replay_lens_micro_state_fast_path_keeps_only_latest_user_turn():
    lens = ReplayLens(
        ReplayLensConfig(
            enabled=True,
            min_messages=4,
            keep_last_n=2,
            small_turn_raw_max_tokens=60,
        )
    )
    messages = [
        {"role": "user", "content": "Install libpq-dev and continue."},
        {"role": "assistant", "content": "I will install it."},
        {
            "role": "assistant",
            "tool_calls": [
                {
                    "id": "call_2",
                    "function": {"name": "terminal", "arguments": '{"command": "apt-get install libpq-dev"}'},
                }
            ],
        },
        {
            "role": "tool",
            "tool_call_id": "call_2",
            "content": "E: Package 'libpq-dev' has no installation candidate",
        },
        {"role": "assistant", "content": "The blocker is that the package has no installation candidate."},
        {"role": "user", "content": "continue"},
    ]

    rewritten, meta = lens.rewrite_history(messages, policy_overrides={"policy_name": "debugging_hot_loop"})

    assert meta["applied"] is True
    assert meta["micro_state_fast_path"] is True
    assert rewritten == [{"role": "user", "content": "continue"}]


def test_replay_lens_task_management_bypasses_small_turn_fast_path_for_compact_state():
    lens = ReplayLens(
        ReplayLensConfig(
            enabled=True,
            min_messages=4,
            keep_last_n=2,
            small_turn_raw_max_tokens=180,
        )
    )
    messages = [
        {"role": "user", "content": "Branch A: keep working on replay benchmarks."},
        {"role": "assistant", "content": "I am tracking branch A."},
        {"role": "user", "content": "Branch B: kernel memory cleanup."},
        {"role": "assistant", "content": "I am tracking branch B."},
        {"role": "user", "content": "Continue branch A only."},
    ]

    rewritten, meta = lens.rewrite_history(messages, policy_overrides={"policy_name": "task_management"})

    assert meta["applied"] is True
    assert meta["micro_state_fast_path"] is True
    assert rewritten == [{"role": "user", "content": "Continue branch A only."}]
