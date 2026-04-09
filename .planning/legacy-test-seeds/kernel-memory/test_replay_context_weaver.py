from agent.replay_context_weaver import ReplayContextWeaver
from agent.replay_context_budget import ReplayContextBudgetAllocator
from agent.replay_fragment_extract import extract_replay_fragments
from agent.replay_lens import ReplayLens


def test_replay_context_weaver_weaves_budgeted_state_block():
    weaver = ReplayContextWeaver.from_dict(
        {
            "enabled": True,
            "max_chars": 400,
            "kernel_chars": 120,
            "ledger_chars": 120,
            "plugin_chars": 120,
        }
    )

    result = weaver.weave(
        kernel_context="[KERNEL] user prefers Python and concise answers",
        ledger_context="[EXECUTION LEDGER] read_file -> loaded app.py",
        plugin_context="[TOOL PROFILE] Active tool profile: code",
    )

    assert result.startswith("[TURN STATE]")
    assert "Stable context I should retain" in result
    assert "Recent completed work I should not repeat" in result
    assert "Current turn guidance and active constraints" in result
    assert len(result) <= 400


def test_replay_context_weaver_disabled_falls_back_to_plain_join():
    weaver = ReplayContextWeaver.from_dict({"enabled": False})
    result = weaver.weave(
        kernel_context="kernel context",
        ledger_context="ledger context",
        plugin_context="plugin context",
    )

    assert result == "kernel context\n\nledger context\n\nplugin context"


def test_replay_context_budget_allocator_dedups_duplicate_fragments():
    allocator = ReplayContextBudgetAllocator.from_dict(
        {
            "enabled": True,
            "max_chars": 300,
            "kernel_chars": 120,
            "ledger_chars": 120,
            "plugin_chars": 120,
            "min_section_chars": 60,
        }
    )

    result = allocator.allocate(
        kernel_context="user prefers Python\nactive repo is hermes-agent-port",
        ledger_context="read_file app.py\nactive repo is hermes-agent-port",
        plugin_context="tool profile: code\nread_file app.py",
    )

    assert "active repo is hermes-agent-port" in result["kernel"]
    assert "active repo is hermes-agent-port" not in result["ledger"]
    assert "read_file app.py" in result["ledger"]
    assert "read_file app.py" not in result["plugin"]


def test_replay_context_budget_allocator_prioritizes_kernel_fragments_relevant_to_current_goal():
    allocator = ReplayContextBudgetAllocator.from_dict(
        {
            "enabled": True,
            "max_chars": 180,
            "kernel_chars": 80,
            "ledger_chars": 50,
            "plugin_chars": 50,
            "min_section_chars": 40,
        }
    )

    result = allocator.allocate(
        kernel_context=(
            "user prefers concise answers\n"
            "nginx permission denied on /var/log/nginx/error.log after deploy\n"
            "project uses python tooling"
        ),
        ledger_context="read_file nginx.conf",
        plugin_context="tool profile: code",
        priority_context="Please fix the nginx permission issue",
    )

    assert "nginx permission denied" in result["kernel"]


def test_replay_context_budget_allocator_keeps_answer_synthesis_block_together():
    allocator = ReplayContextBudgetAllocator.from_dict(
        {
            "enabled": True,
            "max_chars": 220,
            "kernel_chars": 120,
            "ledger_chars": 40,
            "plugin_chars": 40,
            "min_section_chars": 40,
        }
    )

    result = allocator.allocate(
        kernel_context=(
            "Title: generic long title fragment that should not dominate\n"
            "Answer-bearing synthesis:\n"
            "- Reference item: Air Fryer.\n"
            "- Earlier/prior item identified: Instant Pot.\n"
            "Evidence chain:\n"
            "- some supporting evidence"
        ),
        priority_context="What new kitchen gadget did I invest in before getting the Air Fryer?",
    )

    assert "Answer-bearing synthesis:" in result["kernel"]
    assert "Instant Pot" in result["kernel"]


def test_replay_fragment_extract_keeps_answer_synthesis_block_critical():
    fragments = extract_replay_fragments(
        kernel_context=(
            "[System note: retrieved context]\n"
            "# Kernel Memory\n"
            "Answer-bearing synthesis:\n"
            "- Reference item: Air Fryer.\n"
            "- Earlier/prior item identified: Instant Pot.\n"
            "Evidence chain:\n"
            "- Event: Purchased Air Fryer.\n"
            "- Event: Invested in Instant Pot."
        )
    )

    synthesis = next(fragment for fragment in fragments if "Answer-bearing synthesis:" in fragment.text)
    evidence = next(fragment for fragment in fragments if "Evidence chain:" in fragment.text)

    assert "Instant Pot" in synthesis.text
    assert synthesis.priority_class == "critical_evidence"
    assert synthesis.must_keep is True
    assert evidence.priority_class == "critical_evidence"
    assert evidence.must_keep is True


def test_replay_context_weaver_uses_policy_path_to_preserve_answer_synthesis_block():
    weaver = ReplayContextWeaver.from_dict(
        {
            "enabled": True,
            "max_chars": 500,
            "kernel_chars": 220,
            "ledger_chars": 80,
            "plugin_chars": 80,
        }
    )

    woven, meta = weaver.weave_with_meta(
        kernel_context=(
            "[System note: retrieved context]\n"
            "# Kernel Memory\n"
            "Title: generic long title fragment that should not dominate\n"
            "Answer-bearing synthesis:\n"
            "- Reference item: Air Fryer.\n"
            "- Earlier/prior item identified: Instant Pot.\n"
            "Evidence chain:\n"
            "- Event: Purchased Air Fryer.\n"
            "- Event: Invested in Instant Pot."
        ),
        priority_context="What new kitchen gadget did I invest in before getting the Air Fryer?",
        policy_name="chat_followup",
    )

    assert meta["mode"] in {"summary", "full_weave"}
    assert "Answer-bearing synthesis:" in woven
    assert "Instant Pot" in woven


def test_replay_context_weaver_keeps_resolved_kernel_answer_for_task_like_query():
    weaver = ReplayContextWeaver.from_dict(
        {
            "enabled": True,
            "max_chars": 500,
            "kernel_chars": 220,
            "ledger_chars": 80,
            "plugin_chars": 80,
        }
    )

    woven, meta = weaver.weave_with_meta(
        kernel_context=(
            "[Kernel memory context; additive only; mode=source_supported.]\n"
            "# Kernel Memory\n"
            "Resolved answer from kernel memory: Roscioli\n"
            "Support: There's also Roscioli, a famous deli that serves the best cured meats"
        ),
        priority_context="I'm planning to visit the Vatican again and remind me of the deli name near the Vatican.",
        policy_name="task_management",
        open_loop_count=1,
        recent_tool_run_count=1,
        raw_history_tokens=180,
        rewritten_history_tokens=130,
    )

    assert meta["mode"] == "summary"
    assert "Resolved answer from kernel memory: Roscioli" in woven
    assert "Support: There's also Roscioli" in woven


def test_replay_lens_accepts_policy_overrides():
    lens = ReplayLens.from_config_dict(
        {
            "enabled": True,
            "min_messages": 4,
            "keep_last_n": 2,
            "max_recent_tool_runs": 2,
            "max_assistant_notes": 2,
        }
    )
    messages = [
        {"role": "user", "content": "first objective"},
        {"role": "assistant", "content": "noted first objective"},
        {"role": "user", "content": "second objective"},
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {"id": "call_1", "function": {"name": "read_file", "arguments": "{\"path\":\"/tmp/app.py\"}"}}
            ],
        },
        {"role": "tool", "tool_call_id": "call_1", "content": "loaded /tmp/app.py successfully"},
        {"role": "user", "content": "third objective"},
        {"role": "assistant", "content": "done"},
        {"role": "user", "content": "final follow-up"},
    ]
    rewritten, meta = lens.rewrite_history(
        messages,
        policy_overrides={
            "policy_name": "debugging_hot_loop",
            "keep_last_n": 3,
            "max_recent_tool_runs": 3,
            "max_assistant_notes": 3,
        },
    )

    assert meta["applied"] is True
    assert meta["policy_name"] == "debugging_hot_loop"
    assert meta["micro_state_fast_path"] is True
    assert rewritten == [{"role": "user", "content": "final follow-up"}]
