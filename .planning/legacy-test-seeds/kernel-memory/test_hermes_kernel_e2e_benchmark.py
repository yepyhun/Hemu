from __future__ import annotations

from agent.hermes_kernel_e2e_benchmark import run_hermes_kernel_e2e_benchmark


def test_hermes_kernel_e2e_benchmark_shows_custom_outperforming_native():
    report = run_hermes_kernel_e2e_benchmark()
    payload = report.as_dict()

    assert payload["modes"]["custom"]["total"] == 4
    assert payload["modes"]["custom"]["passed"] == 4
    assert payload["modes"]["native"]["total"] == 4
    assert payload["modes"]["native"]["passed"] == 1

    scenarios = {(item["mode"], item["scenario_id"]): item for item in payload["scenarios"]}

    assert scenarios[("custom", "S1")]["storage_plane"] == "decision_profile_memory"
    assert scenarios[("custom", "S1")]["final_answer_correct"] is True
    assert scenarios[("native", "S1")]["write_success"] is False
    assert scenarios[("native", "S1")]["final_answer_correct"] is False

    assert scenarios[("custom", "S3")]["storage_plane"] == "mixed"
    assert scenarios[("custom", "S4")]["storage_plane"] == "kernel_memory"
    assert scenarios[("custom", "S4")]["prompt_markers_present"] is True
    assert scenarios[("native", "S4")]["prompt_markers_present"] is False
