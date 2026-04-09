from __future__ import annotations

from agent.kernel_memory_bilingual import detect_language, expand_query_terms, normalize_query


def test_bilingual_normalizer_expands_hungarian_query():
    normalized = normalize_query("könyv összefoglaló")

    assert "book" in normalized
    assert "summary" in normalized


def test_detect_language_handles_mixed_content():
    assert detect_language("Magyar summary with book notes") == "mixed"


def test_bilingual_normalizer_does_not_cross_contaminate_quote_and_source_terms():
    normalized = normalize_query("What is the current favorite quote?")

    assert "idézet" in normalized
    assert "forrás" not in normalized
    assert "medical" not in normalized


def test_bilingual_term_expansion_keeps_source_and_quote_groups_separate():
    quote_terms = set(expand_query_terms("favorite quote"))
    source_terms = set(expand_query_terms("exact source"))

    assert "idézet" in quote_terms
    assert "forrás" not in quote_terms
    assert "forrás" in source_terms
    assert "idézet" not in source_terms
