from agent.replay_benchmarks import benchmark_replay_messages, estimate_message_tokens


def test_estimate_message_tokens_counts_basic_payload():
    messages = [
        {"role": "user", "content": "hello world"},
        {"role": "assistant", "content": "short reply"},
    ]

    assert estimate_message_tokens(messages) > 0


def test_benchmark_replay_messages_reports_savings():
    baseline = [
        {"role": "user", "content": "x" * 400},
        {"role": "assistant", "content": "y" * 400},
    ]
    optimized = [
        {"role": "system", "content": "[TURN STATE] compact"},
        {"role": "user", "content": "follow-up"},
    ]

    result = benchmark_replay_messages(
        baseline_messages=baseline,
        optimized_messages=optimized,
        kernel_context="stable fact",
        ledger_context="recent action",
        plugin_context="profile code",
        woven_context="[TURN STATE] compact",
    )

    assert result.baseline_tokens > result.optimized_tokens
    assert result.token_savings > 0
    assert result.savings_ratio > 0
    assert result.context_block_tokens["woven"] > 0
