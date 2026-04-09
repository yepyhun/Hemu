from __future__ import annotations

from agent.kernel_memory_task_temporal import (
    infer_temporal_context,
    query_is_temporal_follow_up,
    query_targets_task_context,
)


def test_task_temporal_detects_multilingual_follow_up_queries():
    assert query_is_temporal_follow_up("mi van még?", primary_language="hu")
    assert query_is_temporal_follow_up("what else is there?", primary_language="en")


def test_task_temporal_detects_task_context_across_locales():
    assert query_targets_task_context("mi a feladatom ma", primary_language="hu")
    assert query_targets_task_context("what reminder do I have today", primary_language="en")


def test_task_temporal_infers_relative_windows_from_locale_pack_terms():
    tomorrow = infer_temporal_context("mik a holnapi teendőim?", primary_language="hu")
    today = infer_temporal_context("what tasks do I have today?", primary_language="en")

    assert tomorrow is not None
    assert tomorrow.label == "tomorrow"
    assert today is not None
    assert today.label == "today"
