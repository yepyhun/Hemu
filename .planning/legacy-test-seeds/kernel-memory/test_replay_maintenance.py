from agent.replay_maintenance import (
    collect_invalidation_paths,
    should_trigger_context_maintenance,
    evaluate_replay_maintenance,
)


def test_collect_invalidation_paths_for_write_file():
    paths = collect_invalidation_paths("write_file", {"path": "/workspace/app.py"})
    assert paths == ["/workspace/app.py"]


def test_collect_invalidation_paths_for_terminal_write_command():
    paths = collect_invalidation_paths(
        "terminal",
        {
            "command": "mv /workspace/old.py /workspace/new.py",
            "workdir": "/workspace",
        },
    )
    assert "/workspace/old.py" in paths
    assert "/workspace/new.py" in paths


def test_should_trigger_context_maintenance():
    assert should_trigger_context_maintenance(5000, 4000) is True
    assert should_trigger_context_maintenance(3000, 4000) is False


def test_evaluate_replay_maintenance_collects_multiple_reasons():
    decision = evaluate_replay_maintenance(
        approx_tokens=1000,
        threshold_tokens=900,
        stale_artifacts=4,
        duplicate_actions=3,
        total_artifacts=12,
    )

    assert decision.should_compact is True
    assert "context_pressure" in decision.reasons
    assert "stale_artifact_pressure" in decision.reasons
    assert "duplicate_pressure" in decision.reasons
    assert "artifact_volume_pressure" in decision.reasons
