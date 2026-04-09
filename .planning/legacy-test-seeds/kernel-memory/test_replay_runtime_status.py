from agent.replay_maintenance import evaluate_replay_maintenance
from agent.replay_quality_gate import evaluate_replay_release_gate
from agent.replay_runtime_status import evaluate_benchmark_gate, build_replay_runtime_status


def test_benchmark_gate_fails_when_savings_too_low():
    gate = evaluate_benchmark_gate({"savings_ratio": 0.2}, min_savings_ratio=0.5)
    assert gate.passed is False


def test_runtime_status_builds_expected_shape():
    maintenance = evaluate_replay_maintenance(
        approx_tokens=1000,
        threshold_tokens=900,
        stale_artifacts=2,
        duplicate_actions=1,
        total_artifacts=5,
    ).as_dict()
    release_gate = evaluate_replay_release_gate(
        {"total": 2, "passed": 2, "results": [{"savings_ratio": 0.2}, {"savings_ratio": 0.3}]}
    )
    gate = evaluate_benchmark_gate({"savings_ratio": 0.75}, min_savings_ratio=0.5, release_gate=release_gate.as_dict())
    status = build_replay_runtime_status(
        tool_profile="code",
        replay_policy="debugging_hot_loop",
        replay_profile="balanced",
        replay_profile_drift=["replay_lens.keep_last_n"],
        feature_flags={"benchmarks": True, "maintenance": False},
        artifact_stats={"total": 5, "stale": 2},
        episode_stats={"total": 3, "active": 1, "reinforced": 1, "archived": 1},
        ledger_stats={"total": 7, "duplicates": 1},
        operational_metrics={"tool_surface_size": 6, "total_cost_of_session": 0.42},
        benchmark={"savings_ratio": 0.75},
        maintenance=maintenance,
        benchmark_gate=gate,
    )
    assert status["tool_profile"] == "code"
    assert status["replay_policy"] == "debugging_hot_loop"
    assert status["replay_profile"] == "balanced"
    assert "replay_lens.keep_last_n" in status["replay_profile_drift"]
    assert status["feature_flags"]["maintenance"] is False
    assert status["benchmark_gate"]["passed"] is True
    assert status["benchmark_gate"]["release_gate"]["passed"] is True
    assert status["maintenance"]["should_compact"] is True
    assert status["episode_stats"]["reinforced"] == 1
    assert status["operational_metrics"]["tool_surface_size"] == 6
