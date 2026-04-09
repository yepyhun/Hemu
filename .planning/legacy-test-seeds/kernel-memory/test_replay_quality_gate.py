from agent.replay_quality_gate import evaluate_replay_release_gate


def test_replay_release_gate_requires_pass_rate_and_average_savings():
    gate = evaluate_replay_release_gate(
        {
            "total": 3,
            "passed": 3,
            "results": [
                {"savings_ratio": 0.12},
                {"savings_ratio": 0.18},
                {"savings_ratio": 0.14},
            ],
        },
        min_pass_rate=1.0,
        min_average_savings_ratio=0.10,
    )

    assert gate.passed is True
    assert gate.actual_average_savings_ratio > 0.10

    failing = evaluate_replay_release_gate(
        {
            "total": 3,
            "passed": 2,
            "results": [
                {"savings_ratio": 0.12},
                {"savings_ratio": 0.02},
                {"savings_ratio": 0.01},
            ],
        },
        min_pass_rate=1.0,
        min_average_savings_ratio=0.10,
    )
    assert failing.passed is False
