from agent.replay_assembly_policy import ReplayAssemblyPolicy, ReplayAssemblyPolicyConfig


def test_replay_assembly_policy_prefers_raw_tail_for_tiny_clean_turns():
    policy = ReplayAssemblyPolicy(ReplayAssemblyPolicyConfig(enabled=True))

    decision = policy.decide(
        policy_name="conversation",
        tool_profile="conversation",
        raw_history_tokens=90,
        rewritten_history_tokens=72,
        open_loop_count=0,
        recent_tool_run_count=0,
        has_patch_digest=False,
        has_blocker_reason=False,
        has_exact_source_guard=False,
        has_stale_sensitive_artifact=False,
        large_tool_output_detected=False,
    )

    assert decision.mode == "raw_tail"
    assert decision.reason == "tiny turn without replay pressure"


def test_replay_assembly_policy_uses_task_micro_state_for_single_open_loop():
    policy = ReplayAssemblyPolicy(ReplayAssemblyPolicyConfig(enabled=True))

    decision = policy.decide(
        policy_name="task_management",
        tool_profile="task",
        raw_history_tokens=180,
        rewritten_history_tokens=130,
        open_loop_count=1,
        recent_tool_run_count=1,
        has_patch_digest=False,
        has_blocker_reason=False,
        has_exact_source_guard=False,
        has_stale_sensitive_artifact=False,
        large_tool_output_detected=False,
    )

    assert decision.mode == "micro_state"
    assert decision.micro_state_kind == "task"


def test_replay_assembly_policy_prefers_task_micro_state_over_generic_raw_tail():
    policy = ReplayAssemblyPolicy(ReplayAssemblyPolicyConfig(enabled=True))

    decision = policy.decide(
        policy_name="task_management",
        tool_profile="task",
        raw_history_tokens=90,
        rewritten_history_tokens=72,
        open_loop_count=1,
        recent_tool_run_count=0,
        has_patch_digest=False,
        has_blocker_reason=False,
        has_exact_source_guard=False,
        has_stale_sensitive_artifact=False,
        large_tool_output_detected=False,
    )

    assert decision.mode == "micro_state"
    assert decision.micro_state_kind == "task"


def test_replay_assembly_policy_uses_exact_source_micro_state_for_source_guard():
    policy = ReplayAssemblyPolicy(ReplayAssemblyPolicyConfig(enabled=True))

    decision = policy.decide(
        policy_name="exact_source_required",
        tool_profile="research",
        raw_history_tokens=160,
        rewritten_history_tokens=120,
        open_loop_count=0,
        recent_tool_run_count=0,
        has_patch_digest=False,
        has_blocker_reason=False,
        has_exact_source_guard=True,
        has_stale_sensitive_artifact=False,
        large_tool_output_detected=False,
    )

    assert decision.mode == "micro_state"
    assert decision.micro_state_kind == "exact_source"


def test_replay_assembly_policy_preserves_answer_bearing_kernel_context_over_task_micro_state():
    policy = ReplayAssemblyPolicy(ReplayAssemblyPolicyConfig(enabled=True))

    decision = policy.decide(
        policy_name="task_management",
        tool_profile="task",
        kernel_context=(
            "[Kernel memory context; additive only; mode=source_supported.]\n"
            "# Kernel Memory\n"
            "Resolved answer from kernel memory: Roscioli\n"
            "Support: There's also Roscioli, a famous deli."
        ),
        raw_history_tokens=180,
        rewritten_history_tokens=130,
        open_loop_count=1,
        recent_tool_run_count=1,
        has_patch_digest=False,
        has_blocker_reason=False,
        has_exact_source_guard=False,
        has_stale_sensitive_artifact=False,
        large_tool_output_detected=False,
    )

    assert decision.mode == "summary"
    assert decision.reason == "answer-bearing kernel context must survive weaving"


def test_replay_assembly_policy_detects_hungarian_exact_source_without_core_regexes():
    policy = ReplayAssemblyPolicy(ReplayAssemblyPolicyConfig(enabled=True))

    decision = policy.decide(
        policy_name="chat_followup",
        tool_profile="research",
        priority_context="Add vissza a pontos forrást, szó szerint.",
        raw_history_tokens=150,
        rewritten_history_tokens=110,
        open_loop_count=0,
        recent_tool_run_count=0,
        has_patch_digest=False,
        has_blocker_reason=False,
        has_exact_source_guard=False,
        has_stale_sensitive_artifact=False,
        large_tool_output_detected=False,
    )

    assert decision.mode == "micro_state"
    assert decision.micro_state_kind == "exact_source"
