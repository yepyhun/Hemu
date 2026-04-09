from __future__ import annotations

from agent.replay_intent import detect_replay_intent


def test_replay_intent_detects_hungarian_task_management():
    decision = detect_replay_intent("Kérlek állíts be egy emlékeztetőt holnap reggelre.")

    assert decision.explicit_intent == "task_management"


def test_replay_intent_detects_debugging_hot_loop():
    decision = detect_replay_intent("Why is this test failing with a traceback?")

    assert decision.explicit_intent == "debugging_hot_loop"


def test_replay_intent_detects_exact_source_requirement():
    decision = detect_replay_intent("Mutasd a pontos forrást szó szerint.")

    assert decision.explicit_intent == "exact_source_required"
