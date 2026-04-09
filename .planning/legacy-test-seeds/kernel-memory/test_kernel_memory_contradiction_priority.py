from __future__ import annotations

from agent.kernel_memory_contradiction_priority import (
    contradiction_priority_adjustment,
    contradiction_signals,
)


def test_contradiction_priority_boosts_contradiction_edge_for_conflict_query():
    item = {
        "kind": "relation",
        "relation_type": "contradicts",
        "metadata": {},
    }

    signals = contradiction_signals(item)
    adjustment = contradiction_priority_adjustment(item, query="What is the conflict here?")

    assert "contradiction_edge" in signals
    assert adjustment >= 6


def test_contradiction_priority_boosts_superseded_resolution_for_resolution_query():
    item = {
        "kind": "event",
        "event_type": "superseded",
        "event_status": "superseded",
        "metadata": {"conflict_signal": "correction"},
    }

    adjustment = contradiction_priority_adjustment(
        item,
        query="What was corrected and what superseded the old state?",
    )

    assert adjustment >= 4
