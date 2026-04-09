from agent.replay_feature_flags import apply_replay_feature_flags


def test_apply_replay_feature_flags_disables_selected_components():
    agent_cfg = {
        "artifact_registry": {"enabled": True},
        "replay_episodes": {"enabled": True},
        "replay_execution_ledger": {"enabled": True},
        "decision_memory": {"enabled": True},
        "replay_duplicate_guard": {"enabled": True},
        "replay_tool_profiles": {"enabled": True},
        "replay_context_weaver": {"enabled": True},
        "replay_feature_flags": {
            "artifacts": False,
            "episodes": False,
            "decision_memory": False,
            "stable_memory_refinement": False,
            "stable_memory_guardrails": False,
            "assembly_selector": False,
            "micro_state": False,
            "maintenance": False,
            "benchmarks": False,
            "debug_tools": False,
        },
    }

    flags = apply_replay_feature_flags(agent_cfg)

    assert flags.artifacts is False
    assert flags.episodes is False
    assert flags.decision_memory is False
    assert flags.stable_memory_refinement is False
    assert flags.stable_memory_guardrails is False
    assert flags.assembly_selector is False
    assert flags.micro_state is False
    assert flags.maintenance is False
    assert flags.benchmarks is False
    assert flags.debug_tools is False
    assert agent_cfg["artifact_registry"]["enabled"] is False
    assert agent_cfg["replay_episodes"]["enabled"] is False
    assert agent_cfg["decision_memory"]["enabled"] is False
    assert agent_cfg["decision_memory"]["stable_memory_refinement_enabled"] is False
    assert agent_cfg["decision_memory"]["stable_memory_guardrails_enabled"] is False
    assert agent_cfg["replay_execution_ledger"]["enabled"] is True
    assert agent_cfg["replay_context_weaver"]["assembly_selector_enabled"] is False
    assert agent_cfg["replay_context_weaver"]["micro_state_enabled"] is False
