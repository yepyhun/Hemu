from agent.replay_policy import ReplayPolicyRouter


def test_replay_policy_detects_exact_source_required():
    router = ReplayPolicyRouter()
    decision = router.decide(
        user_message="Give me the exact source and quote the relevant log line.",
        kernel_context="",
        ledger_context="",
    )

    assert decision.policy_name == "exact_source_required"
    assert decision.episode_fidelity == "high"


def test_replay_policy_does_not_treat_favorite_quote_as_exact_source():
    router = ReplayPolicyRouter()
    decision = router.decide(
        user_message="What is my current favorite quote?",
        kernel_context="",
        ledger_context="",
    )

    assert decision.policy_name != "exact_source_required"


def test_replay_policy_detects_debugging_hot_loop():
    router = ReplayPolicyRouter()
    decision = router.decide(
        user_message="Why is this test failing with this traceback?",
        kernel_context="",
        ledger_context="",
    )

    assert decision.policy_name == "debugging_hot_loop"
    assert decision.keep_last_n >= 20


def test_replay_policy_short_followup_reuses_previous_mode():
    router = ReplayPolicyRouter()
    first = router.decide(
        user_message="Implement the patch in the repo and update the file.",
        kernel_context="",
        ledger_context="",
    )
    second = router.decide(
        user_message="ok, continue",
        kernel_context="",
        ledger_context="",
    )

    assert first.policy_name == "code_execution_continuation"
    assert second.policy_name == "code_execution_continuation"


def test_replay_policy_detects_hungarian_reminder_as_task_management():
    router = ReplayPolicyRouter()
    decision = router.decide(
        user_message="Kérlek állíts be egy emlékeztetőt holnap 7:15-re, hogy hívjam fel Györgyöt.",
        kernel_context="",
        ledger_context="",
    )

    assert decision.policy_name == "task_management"


def test_replay_policy_explicit_task_overrides_debug_context():
    router = ReplayPolicyRouter()
    decision = router.decide(
        user_message="Állíts be egy emlékeztetőt ma estére.",
        kernel_context="Previous work was a deployment error investigation.",
        ledger_context="terminal -> error: deployment failed | blocker: permission denied",
    )

    assert decision.policy_name == "task_management"


def test_replay_policy_does_not_route_technical_branch_bug_to_task_management():
    router = ReplayPolicyRouter()
    decision = router.decide(
        user_message="Investigate the branch prediction bug in the compiler.",
        kernel_context="",
        ledger_context="",
    )

    assert decision.policy_name == "debugging_hot_loop"


def test_replay_policy_explicit_explanation_does_not_stick_to_code_mode():
    router = ReplayPolicyRouter()
    first = router.decide(
        user_message="Patch the config bug in app.py.",
        kernel_context="",
        ledger_context="",
    )
    second = router.decide(
        user_message="Just explain what happened.",
        kernel_context="",
        ledger_context="",
    )

    assert first.policy_name == "code_execution_continuation"
    assert second.policy_name == "chat_followup"
