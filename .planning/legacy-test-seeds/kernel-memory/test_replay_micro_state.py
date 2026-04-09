from agent.replay_micro_state import ReplayMicroStateRenderer


def test_replay_micro_state_renderer_task_debug_and_code_outputs_are_specific():
    renderer = ReplayMicroStateRenderer.from_dict({"enabled": True})

    task = renderer.render(
        kind="task",
        priority_context="Continue the reminder branch",
        kernel_context="Branch A = replay benchmarks, Branch B = kernel memory cleanup.",
        ledger_context="[EXECUTION LEDGER] reminder job scheduled",
    )
    debug = renderer.render(
        kind="debug",
        priority_context="remember the last blocker",
        kernel_context="permission denied on /var/log/nginx/error.log",
        ledger_context="[EXECUTION LEDGER] apt-get update failed",
    )
    code = renderer.render(
        kind="code",
        priority_context="continue from the current code state",
        kernel_context="/home/lauratom/Asztal/ai/hermes-agent-port/agent/app.py",
        ledger_context="[EXECUTION LEDGER] patch applied to app.py",
    )
    exact = renderer.render(kind="exact_source")

    assert "Focus:" in task
    assert "replay benchmarks" in task
    assert "Blocker:" in debug
    assert "Avoid:" in debug
    assert "Patch:" in code
    assert "app.py" in code
    assert "Exact source required" in exact
    assert "verbatim" in exact
