from __future__ import annotations

from agent.kernel_memory_ops_policy import KernelMemoryOpsPolicy


def test_ops_policy_marks_degraded_when_validation_or_failed_events_exist():
    result = KernelMemoryOpsPolicy().evaluate(
        {
            "acceptance_ok": True,
            "failed_events": 2,
            "golden_set": {"failed": 0},
            "validation_suite": {"failed": 1},
            "embedding_provider": {"ok": True},
        }
    )

    assert result["status"] == "degraded"
    assert "failed_events_present" in result["warnings"]
    assert "validation_suite_failed" in result["warnings"]
    assert "backup_missing" in result["warnings"]
    assert "review_and_replay_failed_events" in result["auto_actions"]
    assert result["incident_summary"]["total"] >= 2


def test_ops_policy_marks_halted_when_source_of_truth_integrity_fails():
    result = KernelMemoryOpsPolicy().evaluate(
        {
            "acceptance_ok": False,
            "failed_events": 0,
            "golden_set": {"failed": 0},
            "validation_suite": {"failed": 0},
            "embedding_provider": {"ok": True},
        }
    )

    assert result["status"] == "halted"
    assert result["retrieval_mode"] == "halted"
    assert result["human_intervention_required"] is True


def test_ops_policy_flags_failed_backup_verification_and_migration():
    result = KernelMemoryOpsPolicy().evaluate(
        {
            "acceptance_ok": True,
            "failed_events": 0,
            "golden_set": {"failed": 0},
            "validation_suite": {"failed": 0, "leakage_failures": 0},
            "embedding_provider": {"ok": True},
            "backup": {"status": "failed", "verification_ok": False},
            "migration": {"status": "failed", "migration_id": "mig-1"},
        }
    )

    assert result["status"] == "degraded"
    assert "backup_verification_failed" in result["warnings"]
    assert "migration_failed" in result["warnings"]


def test_ops_policy_degrades_when_graph_projection_is_unavailable():
    result = KernelMemoryOpsPolicy().evaluate(
        {
            "acceptance_ok": True,
            "failed_events": 0,
            "golden_set": {"failed": 0},
            "validation_suite": {"failed": 0, "leakage_failures": 0},
            "embedding_provider": {"ok": True},
            "backup": {"status": "verified", "verification_ok": True},
            "graph_projection": {
                "graph_store": {
                    "enabled": True,
                    "status": "disabled",
                    "reason": "neo4j_password_missing",
                }
            },
        }
    )

    assert result["status"] == "degraded"
    assert "graph_projection_degraded" in result["warnings"]
    assert "run_graph_projection_backfill" in result["auto_actions"]


def test_ops_policy_distinguishes_provenance_gap_from_repairable_drift():
    result = KernelMemoryOpsPolicy().evaluate(
        {
            "acceptance_ok": True,
            "failed_events": 0,
            "golden_set": {"failed": 0},
            "validation_suite": {"failed": 0, "leakage_failures": 0},
            "embedding_provider": {"ok": True},
            "backup": {"status": "verified", "verification_ok": True},
            "deterministic_recompile": {
                "ok": False,
                "classification_status": "provenance_gap",
                "provenance_gap_count": 2,
                "truth_input_gap_count": 0,
            },
        }
    )

    assert result["status"] == "degraded"
    assert "deterministic_recompile_provenance_gap" in result["warnings"]
    assert "deterministic_recompile_drift" not in result["warnings"]
