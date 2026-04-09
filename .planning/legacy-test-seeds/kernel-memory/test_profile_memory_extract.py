from __future__ import annotations

from agent.profile_memory_extract import extract_profile_candidates


def test_extract_profile_candidates_skips_low_signal_or_truncated_fragments():
    text = "Remember that for Tomi: Dr. Prefer 10 over 5)."
    candidates = extract_profile_candidates(user_message=text, source_ref="sess-1")
    assert candidates == []
