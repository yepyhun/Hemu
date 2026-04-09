from agent.replay_context_weaver import ReplayContextWeaver
from agent.replay_quality_fixtures import build_default_replay_quality_scenarios
from agent.replay_lens import ReplayLens
from agent.replay_quality_suite import ReplayQualityScenario, ReplayQualitySuite


def test_replay_quality_suite_reports_savings_and_continuity():
    lens = ReplayLens.from_config_dict(
        {
            "enabled": True,
            "min_messages": 4,
            "keep_last_n": 3,
            "max_recent_tool_runs": 3,
            "max_assistant_notes": 3,
        }
    )
    weaver = ReplayContextWeaver.from_dict(
        {
            "enabled": True,
            "max_chars": 420,
            "kernel_chars": 140,
            "ledger_chars": 140,
            "plugin_chars": 140,
        }
    )
    suite = ReplayQualitySuite(lens=lens, weaver=weaver)

    scenario = ReplayQualityScenario(
        name="debugging-hot-loop",
            messages=[
                {"role": "user", "content": "Investigate nginx."},
                {"role": "assistant", "content": "Starting nginx investigation and checking logs."},
                {"role": "user", "content": "Check the latest error output before changing anything."},
                {"role": "assistant", "content": ""},
                {"role": "tool", "content": ("info: boot\nwarning: config\nerror: permission denied on /var/log/nginx/error.log\n" * 120)},
                {"role": "assistant", "content": "I found the permission issue in the nginx log and traced it to file ownership."},
                {"role": "assistant", "content": "I already checked the error log and should avoid repeating the same read unless needed."},
                {"role": "user", "content": "Remember that the blocker was permissions, not config syntax."},
                {"role": "user", "content": "fix it now"},
            ],
        kernel_context="User prefers concise answers and is debugging nginx permissions.",
        ledger_context="terminal -> permission denied on /var/log/nginx/error.log",
        plugin_context="tool profile: code",
        policy_overrides={"keep_last_n": 2, "max_recent_tool_runs": 2, "max_assistant_notes": 2},
        required_markers=("nginx", "permission"),
        min_savings_ratio=0.10,
    )

    result = suite.evaluate([scenario])

    assert result["total"] == 1
    assert result["passed"] == 1
    assert result["results"][0]["continuity_hits"] == 2


def test_replay_quality_suite_default_fixtures_cover_multiple_realistic_workloads():
    lens = ReplayLens.from_config_dict(
        {
            "enabled": True,
            "min_messages": 4,
            "keep_last_n": 3,
            "max_recent_tool_runs": 3,
            "max_assistant_notes": 3,
        }
    )
    weaver = ReplayContextWeaver.from_dict(
        {
            "enabled": True,
            "max_chars": 420,
            "kernel_chars": 140,
            "ledger_chars": 140,
            "plugin_chars": 140,
        }
    )
    suite = ReplayQualitySuite(lens=lens, weaver=weaver)

    scenarios = build_default_replay_quality_scenarios()
    report = suite.evaluate_default_suite()

    assert len(scenarios) >= 3
    assert report["total"] == len(scenarios)
    assert report["passed"] == report["total"]


def test_replay_quality_suite_caches_default_fixture_report():
    lens = ReplayLens.from_config_dict(
        {
            "enabled": True,
            "min_messages": 4,
            "keep_last_n": 3,
            "max_recent_tool_runs": 3,
            "max_assistant_notes": 3,
        }
    )
    weaver = ReplayContextWeaver.from_dict(
        {
            "enabled": True,
            "max_chars": 420,
            "kernel_chars": 140,
            "ledger_chars": 140,
            "plugin_chars": 140,
        }
    )
    suite = ReplayQualitySuite(lens=lens, weaver=weaver)

    first = suite.evaluate_default_suite()
    cache_key = suite._default_suite_cache_key
    cache_value = suite._default_suite_cache_value
    second = suite.evaluate_default_suite()

    assert cache_key is not None
    assert cache_value is not None
    assert second == first
    assert second is not cache_value
