from agent.replay_operational_telemetry import ReplayOperationalTelemetry


def test_replay_operational_telemetry_builds_expected_metrics():
    telemetry = ReplayOperationalTelemetry()
    telemetry.start_turn()
    telemetry.record_tool_profile("code")
    telemetry.record_tool_profile("research")
    telemetry.record_tool_surface_size(7)
    telemetry.record_artifact_capture()
    telemetry.record_duplicate_guard_hit()
    telemetry.record_context_inputs(
        kernel_context="# Kernel Memory\nkeep the chosen source of truth",
        ledger_context="[EXECUTION LEDGER]\n- patch -> wrote config.yaml",
        decision_meta={"hit_count": 1},
    )
    telemetry.record_benchmark(
        {
            "baseline_tokens": 800,
            "optimized_tokens": 260,
            "context_block_tokens": {"woven": 90},
        }
    )
    telemetry.record_weaver_result(
        content="[TURN STATE]\n- keep the active blocker\n- do not repeat the patch",
        meta={"evicted_count": 3, "stale_artifact_suppressed": 1},
    )
    telemetry.record_usage(
        input_tokens=300,
        cache_read_tokens=200,
        cache_write_tokens=25,
        cost_usd=0.015,
    )

    metrics = telemetry.build_status_metrics(
        artifact_stats={"invalidated": 2},
        episode_stats={"active": 4, "promoted": 2},
        decision_stats={"ledger_promoted_count": 3},
        ledger_tool_totals={"rehydrate_artifact": 5},
        quality_suite={"total": 4, "passed": 3},
        session_cost_usd=0.125,
        compatibility_guard_blocks=0,
        readiness_selftest_failures=0,
        background_compaction_tokens=16,
    )

    assert metrics["prompt_tokens_before"] == 800
    assert metrics["prompt_tokens_after"] == 260
    assert metrics["replay_block_tokens"] == 90
    assert metrics["artifact_count_per_turn"] == 1
    assert metrics["artifact_rehydrate_calls"] == 5
    assert metrics["duplicate_action_hits"] == 1
    assert metrics["duplicate_action_prevented"] == 1
    assert metrics["tool_surface_size"] == 7
    assert metrics["active_episode_count"] == 4
    assert metrics["continuity_failure_count"] == 0
    assert metrics["source_faithfulness_failures"] == 0
    assert metrics["kernel_memory_hit_rate"] == 1.0
    assert metrics["replay_kernel_overlap_rate"] == 1.0
    assert metrics["promoted_episode_count"] == 2
    assert metrics["promoted_ledger_count"] == 3
    assert metrics["compatibility_guard_blocks"] == 0
    assert metrics["readiness_selftest_failures"] == 0
    assert metrics["prompt_dedup_savings"] == 540
    assert metrics["tool_surface_profile_hits"] == {"code": 1, "research": 1}
    assert metrics["tool_surface_profile_switches"] == 1
    assert metrics["prompt_cache_hit_rate"] == 0.4
    assert metrics["stale_artifact_invalidations"] == 2
    assert metrics["stale_artifact_suppressed"] == 1
    assert metrics["background_compaction_tokens"] == 16
    assert metrics["context_weaver_evictions"] == 3
    assert metrics["total_cost_of_turn"] == 0.015
    assert metrics["total_cost_of_session"] == 0.125
