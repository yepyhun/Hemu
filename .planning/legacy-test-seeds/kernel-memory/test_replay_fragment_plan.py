from __future__ import annotations

from agent.replay_context_weaver import ReplayContextWeaver


def test_replay_context_weaver_fragment_planner_keeps_blocker_and_patch_digest():
    weaver = ReplayContextWeaver.from_dict(
        {
            "enabled": True,
            "fragment_planner_enabled": True,
            "max_chars": 420,
        }
    )

    content, meta = weaver.assemble_state(
        decision_context="# Decision Memory\n- [C] keep config.yaml as source of truth",
        kernel_context="# Kernel Memory\nnginx logs exist\nold low-value note",
        ledger_context="[EXECUTION LEDGER]\n- terminal -> install failed | blocker: permission denied\n- patch -> wrote fix | changed: config.yaml owner",
        plugin_context="[TOOL PROFILE] focus on the active fix",
        priority_context="Fix the permission denied blocker",
        policy_name="debugging_hot_loop",
        raw_history_tokens=260,
        rewritten_history_tokens=180,
        has_blocker_reason=True,
        has_patch_digest=True,
    )

    assert "permission denied" in content
    assert "config.yaml owner" in content
    assert meta["fragment_count"] >= 2
    assert meta["candidate_count"] >= meta["fragment_count"]
    assert meta["evicted_count"] >= 0
