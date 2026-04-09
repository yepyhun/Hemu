from __future__ import annotations

import json
from pathlib import Path

from agent.replay_benchmark.history import persist_benchmark_report
import pytest

from agent.replay_benchmark.runner import ReplayBenchmarkConfig, ReplayBenchmarkRunner, _parse_args
from agent.replay_benchmark.reporters import render_markdown_report


def test_replay_benchmark_runner_produces_report(tmp_path):
    fixture_path = Path(__file__).resolve().parents[2] / "agent" / "replay_benchmark" / "fixtures" / "default_suite.json"
    runner = ReplayBenchmarkRunner(fixture_path=fixture_path)

    report = runner.run(ReplayBenchmarkConfig(suite="cheap", mode="optimized"))
    payload = report.as_dict()

    assert payload["total"] > 0
    assert payload["overall_score"] >= 0
    assert payload["total_baseline_tokens"] > 0
    assert payload["total_optimized_tokens"] > 0
    assert "weighted_token_savings_ratio" in payload
    assert "small_turn_score" in payload
    assert "large_turn_score" in payload
    assert "small_turn_average_savings_ratio" in payload
    assert len(payload["scenario_results"]) == payload["total"]
    assert "category_summaries" in payload


def test_replay_benchmark_runner_score_only_payload_is_json_serializable():
    fixture_path = Path(__file__).resolve().parents[2] / "agent" / "replay_benchmark" / "fixtures" / "default_suite.json"
    runner = ReplayBenchmarkRunner(fixture_path=fixture_path)

    report = runner.run(ReplayBenchmarkConfig(suite="full", mode="optimized"))
    payload = report.as_dict()
    md = render_markdown_report(report)

    assert json.loads(json.dumps(payload))["suite"] == "full"
    assert "# Replay Benchmark Report" in md


def test_replay_benchmark_runner_baseline_mode_disables_savings():
    fixture_path = Path(__file__).resolve().parents[2] / "agent" / "replay_benchmark" / "fixtures" / "default_suite.json"
    runner = ReplayBenchmarkRunner(fixture_path=fixture_path)

    report = runner.run(ReplayBenchmarkConfig(suite="cheap", mode="baseline"))
    payload = report.as_dict()

    assert payload["average_token_savings_ratio"] == 0.0
    assert payload["total_token_savings"] == 0


def test_replay_benchmark_markdown_uses_release_gate_reasons():
    fixture_path = Path(__file__).resolve().parents[2] / "agent" / "replay_benchmark" / "fixtures" / "default_suite.json"
    runner = ReplayBenchmarkRunner(fixture_path=fixture_path)

    report = runner.run(ReplayBenchmarkConfig(suite="cheap", mode="baseline"))
    md = render_markdown_report(report)

    assert "## Critical Gate" in md
    assert "reasons:" in md
    assert "## Category Summary" in md


def test_replay_benchmark_history_persists_and_tracks_previous_delta(tmp_path):
    fixture_path = Path(__file__).resolve().parents[2] / "agent" / "replay_benchmark" / "fixtures" / "default_suite.json"
    runner = ReplayBenchmarkRunner(fixture_path=fixture_path)

    first = runner.run(ReplayBenchmarkConfig(suite="cheap", mode="optimized"))
    second = runner.run(ReplayBenchmarkConfig(suite="cheap", mode="optimized"))

    first_entry = persist_benchmark_report(first, history_dir=tmp_path)
    second_entry = persist_benchmark_report(second, history_dir=tmp_path)

    assert first_entry["previous_run_id"] is None
    assert second_entry["previous_run_id"] == first_entry["run_id"]
    assert (tmp_path / "history.jsonl").exists()
    assert (tmp_path / "history.md").exists()
    assert (tmp_path / "latest-cheap-optimized.json").exists()
    assert (tmp_path / "latest-cheap-optimized.md").exists()
    scenario = second_entry["scenario_results"][0]
    assert "delta_vs_previous" in scenario


def test_replay_benchmark_reality_suite_uses_tagged_scenarios():
    fixture_path = Path(__file__).resolve().parents[2] / "agent" / "replay_benchmark" / "fixtures" / "default_suite.json"
    runner = ReplayBenchmarkRunner(fixture_path=fixture_path)

    report = runner.run(ReplayBenchmarkConfig(suite="reality", mode="optimized"))
    payload = report.as_dict()

    assert payload["total"] >= 8
    assert "coding_memory" in payload["category_summaries"]
    assert "evidence_hygiene" in payload["category_summaries"]
    assert "evidence_hygiene_score" in payload["category_summaries"]["evidence_hygiene"]
    assert payload["weighted_token_savings_ratio"] >= 0
    assert payload["small_turn_score"] >= 0
    assert payload["large_turn_score"] >= 0
    assert any(item["turn_size_class"] for item in payload["scenario_results"])
    assert any(item["assembly_mode"] for item in payload["scenario_results"])
    assert any(item["source_session"] for item in payload["scenario_results"])
    assert any(item["decision_block_tokens"] >= 0 for item in payload["scenario_results"])


def test_replay_benchmark_decision_scenario_reports_decision_metrics():
    fixture_path = Path(__file__).resolve().parents[2] / "agent" / "replay_benchmark" / "fixtures" / "default_suite.json"
    runner = ReplayBenchmarkRunner(fixture_path=fixture_path)

    report = runner.run(ReplayBenchmarkConfig(suite="full", mode="optimized", scenario_id="decision_reuse_followup"))
    payload = report.as_dict()

    assert payload["total"] == 1
    scenario = payload["scenario_results"][0]
    assert scenario["decision_block_tokens"] > 0
    assert scenario["decision_hit_rate"] >= 1.0
    assert scenario["decision_reuse_success"] is True


def test_replay_benchmark_constraint_scenario_uses_last_user_turn_for_routing():
    fixture_path = Path(__file__).resolve().parents[2] / "agent" / "replay_benchmark" / "fixtures" / "default_suite.json"
    runner = ReplayBenchmarkRunner(fixture_path=fixture_path)

    report = runner.run(ReplayBenchmarkConfig(suite="full", mode="optimized", scenario_id="constraint_blocks_wrong_retry"))
    payload = report.as_dict()

    assert payload["total"] == 1
    scenario = payload["scenario_results"][0]
    assert scenario["policy_match"] is True
    assert scenario["tool_profile_match"] is True
    assert scenario["passed"] is True


def test_replay_benchmark_obsolete_decision_scenario_does_not_inject_obsolete_subject():
    fixture_path = Path(__file__).resolve().parents[2] / "agent" / "replay_benchmark" / "fixtures" / "default_suite.json"
    runner = ReplayBenchmarkRunner(fixture_path=fixture_path)

    report = runner.run(ReplayBenchmarkConfig(suite="full", mode="optimized", scenario_id="obsolete_decision_not_injected"))
    payload = report.as_dict()

    assert payload["total"] == 1
    scenario = payload["scenario_results"][0]
    assert scenario["decision_false_positive_rate"] == 0.0
    assert scenario["passed"] is True


def test_replay_benchmark_stable_scope_precedence_prefers_specific_memory():
    fixture_path = Path(__file__).resolve().parents[2] / "agent" / "replay_benchmark" / "fixtures" / "default_suite.json"
    runner = ReplayBenchmarkRunner(fixture_path=fixture_path)

    report = runner.run(ReplayBenchmarkConfig(suite="full", mode="optimized", scenario_id="stable_scope_precedence"))
    payload = report.as_dict()

    assert payload["total"] == 1
    scenario = payload["scenario_results"][0]
    assert scenario["passed"] is True
    assert scenario["decision_hit_rate"] >= 1.0


def test_replay_benchmark_parse_compare_accepts_explicit_targets():
    config = _parse_args(["--suite", "reality", "--compare", "baseline,optimized"])

    assert config.compare is True
    assert config.suite == "reality"


def test_replay_benchmark_parse_compare_rejects_unknown_targets():
    with pytest.raises(ValueError):
        _parse_args(["--compare", "baseline,candidate"])


def test_replay_benchmark_runner_isolates_policy_state_between_scenarios(tmp_path):
    fixture = {
        "scenarios": [
            {
                "id": "first_exact_source",
                "title": "First",
                "category": "continuity",
                "report_group": "evidence_hygiene",
                "suite_tags": ["cheap"],
                "messages": [
                    {"role": "user", "content": "Quote the exact source."},
                    {"role": "assistant", "content": "I will use the exact source."},
                ],
                "required_markers": ["exact source"],
                "forbidden_markers": [],
                "expected_policy_name": "exact_source_required",
                "expected_tool_profile": "research",
                "min_savings_ratio": 0.0,
            },
            {
                "id": "second_chat_followup",
                "title": "Second",
                "category": "structural",
                "report_group": "evidence_hygiene",
                "suite_tags": ["cheap"],
                "messages": [
                    {"role": "user", "content": "continue safely"},
                    {"role": "assistant", "content": "I should keep it safe."},
                ],
                "required_markers": ["safe"],
                "forbidden_markers": [],
                "expected_policy_name": "chat_followup",
                "expected_tool_profile": "conversation",
                "min_savings_ratio": 0.0,
            },
        ]
    }
    fixture_path = tmp_path / "fixture.json"
    fixture_path.write_text(json.dumps(fixture), encoding="utf-8")
    runner = ReplayBenchmarkRunner(fixture_path=fixture_path)

    report = runner.run(ReplayBenchmarkConfig(suite="cheap", mode="optimized"))
    payload = report.as_dict()
    by_id = {item["scenario_id"]: item for item in payload["scenario_results"]}

    assert by_id["first_exact_source"]["policy_match"] is True
    assert by_id["second_chat_followup"]["policy_match"] is True
    assert by_id["second_chat_followup"]["tool_profile_match"] is True
