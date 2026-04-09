from __future__ import annotations

from agent.kernel_memory_current_state_priority import (
    current_state_priority_adjustment,
    current_state_signals,
    is_current_state_query,
)


def test_current_state_priority_detects_current_queries():
    assert is_current_state_query("What is the current favorite quote?")
    assert is_current_state_query("Mi az aktuális állapot?")


def test_current_state_priority_boosts_active_replacement_records():
    item = {
        "status": "active",
        "supersedes": "clm_old",
        "metadata": {"conflict_signal": "correction"},
        "updated_at": "2099-01-01T00:00:00+00:00",
    }

    signals = current_state_signals(item)
    bonus = current_state_priority_adjustment(item, query="What is the current favorite quote?")

    assert "replacement" in signals
    assert "active" in signals
    assert bonus >= 7
