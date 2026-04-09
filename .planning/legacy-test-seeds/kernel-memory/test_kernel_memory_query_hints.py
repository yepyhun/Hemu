from __future__ import annotations

from agent.kernel_memory_query_hints import (
    has_conflict_hint,
    has_current_state_hint,
    has_resolution_hint,
)


def test_query_hints_detect_current_state_queries_in_multiple_locales():
    assert has_current_state_hint("What is the current favorite quote?")
    assert has_current_state_hint("Mi az aktuális állapot?")


def test_query_hints_detect_conflict_queries_in_multiple_locales():
    assert has_conflict_hint("What changed and what conflicts with the old state?")
    assert has_conflict_hint("Mi az ellentmondás a korábbi állapothoz képest?")


def test_query_hints_detect_resolution_queries_in_multiple_locales():
    assert has_resolution_hint("What resolved the issue?")
    assert has_resolution_hint("Mi oldotta meg a problémát?")
