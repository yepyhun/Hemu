from __future__ import annotations

from agent.core2_proof_harness import (
    benchmark_core2_replay_messages,
    estimate_message_tokens,
    run_core2_proof_benchmark,
    verify_core2_longmemeval_subset,
)


def test_run_core2_proof_benchmark_reports_green_core2_and_honest_baseline(tmp_path):
    report = run_core2_proof_benchmark(tmp_path)
    payload = report.as_dict()

    assert payload["modes"]["core2"]["total"] == 4
    assert payload["modes"]["core2"]["passed"] == 4
    assert payload["modes"]["builtin_only"]["total"] == 4
    assert payload["modes"]["builtin_only"]["passed"] == 0

    scenarios = {(item["mode"], item["scenario_id"]): item for item in payload["scenarios"]}

    assert scenarios[("core2", "S1")]["storage_plane"] == "canonical_truth"
    assert scenarios[("core2", "S1")]["final_answer_correct"] is True
    assert scenarios[("builtin_only", "S1")]["tool_route_available"] is False
    assert scenarios[("builtin_only", "S1")]["passed"] is False

    assert scenarios[("core2", "S3")]["final_answer_correct"] is True
    assert scenarios[("core2", "S4")]["prefetch_available"] is True

    assert payload["final_gate"]["name"] == "LongMemEval-10 paid test"
    assert payload["final_gate"]["status"] == "pending_external"


def test_verify_core2_longmemeval_subset_reaches_expected_answers(tmp_path):
    report = verify_core2_longmemeval_subset(base_dir=tmp_path, sample_size=2, seed=7)

    assert report["sample_size"] == 2
    assert report["modes"]["core2"]["total"] == 2
    assert report["modes"]["builtin_only"]["total"] == 2
    assert report["modes"]["core2"]["passed"] == 2

    results = {(item["mode"], item["question_id"]): item for item in report["results"]}
    core2_items = [item for item in report["results"] if item["mode"] == "core2"]
    baseline_items = [item for item in report["results"] if item["mode"] == "builtin_only"]

    assert all(item["seeded_core2_entries"] > 0 for item in core2_items)
    assert all(item["seeded_builtin_entries"] == 0 for item in baseline_items)
    assert any(item["prompt_contains_answer"] for item in core2_items)
    assert results[("core2", "LM2")]["answer_contains_expected"] is True
    assert report["final_gate"]["status"] == "pending_external"


def test_benchmark_core2_replay_messages_reports_savings():
    baseline = [
        {"role": "user", "content": "x" * 400},
        {"role": "assistant", "content": "y" * 400},
    ]
    optimized = [
        {"role": "system", "content": "[CORE2 PREFETCH] compact"},
        {"role": "user", "content": "follow-up"},
    ]

    result = benchmark_core2_replay_messages(
        baseline_messages=baseline,
        optimized_messages=optimized,
        proof_context="stable Core2 proof context",
        prefetch_context="[CORE2 PREFETCH] compact",
        compact_answer="deployment owner: Bob",
    )

    assert estimate_message_tokens(baseline) > 0
    assert result.baseline_tokens > result.optimized_tokens
    assert result.token_savings > 0
    assert result.savings_ratio > 0
    assert result.context_block_tokens["compact_answer"] > 0
