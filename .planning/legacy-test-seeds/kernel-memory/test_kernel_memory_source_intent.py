from __future__ import annotations

from agent.kernel_memory_source_intent import has_exact_source_intent, has_source_hint


def test_source_intent_detects_exact_source_query():
    assert has_exact_source_intent("Please quote the exact source for Hohmann transfer")
    assert has_source_hint("Please quote the exact source for Hohmann transfer")


def test_source_intent_does_not_treat_favorite_quote_as_exact_source():
    assert not has_exact_source_intent("What is the current favorite quote?")
    assert not has_source_hint("What is the current favorite quote?")


def test_source_intent_detects_source_without_quote_keyword():
    assert has_exact_source_intent("Mi a pontos forrás erre?")
    assert has_source_hint("Show the source for this claim")
