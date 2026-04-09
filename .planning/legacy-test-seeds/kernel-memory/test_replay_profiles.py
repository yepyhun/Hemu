from agent.replay_profiles import resolve_replay_profile


def test_replay_profile_applies_balanced_defaults():
    cfg = {}
    report = resolve_replay_profile(cfg)

    assert report.profile_name == "balanced"
    assert cfg["replay_lens"]["keep_last_n"] == 18
    assert cfg["replay_context_weaver"]["enabled"] is True


def test_replay_profile_reports_drift():
    cfg = {
        "replay_profile": "balanced",
        "replay_lens": {"keep_last_n": 99},
    }
    report = resolve_replay_profile(cfg)

    assert "replay_lens.keep_last_n" in report.drift
