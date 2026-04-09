from __future__ import annotations

from agent.kernel_memory_semantic_lexicon import analyze_semantics


def test_semantic_lexicon_uses_word_boundaries_for_conflict_terms():
    signals = analyze_semantics("The collector said this was wrongly tagged but not actually wrong.")

    labels = signals.labels("conflict")
    assert "wrongly" not in labels
    assert "wrong" in labels


def test_semantic_lexicon_supports_multilingual_preference_and_rule_markers():
    signals = analyze_semantics(
        "Laura érzékeny téma, és mindig figyeljek rá. Tomi kedvenc idézete fontos."
    )

    assert signals.has("preference")
    assert signals.has("rule")


def test_semantic_lexicon_extracts_correction_parse_for_not_this_instead_pattern():
    signals = analyze_semantics(
        "Ez nem a kedvenc idézetem, helyette inkább az, hogy "
        "\"Egyik szél sem jó annak a hajósnak, aki nem tudja melyik kikötőbe tart.\""
    )

    assert signals.has("correction")
    assert signals.correction_parse is not None
    assert signals.correction_parse.mode in {"quoted_replacement", "connector_replacement"}
    assert signals.correction_parse.new_value is not None


def test_semantic_lexicon_extracts_quoted_values():
    signals = analyze_semantics(
        'A kedvenc idézetem: "Egyik szél sem jó annak a hajósnak, aki nem tudja melyik kikötőbe tart."'
    )

    assert signals.quoted_values
    assert "Egyik szél sem jó annak a hajósnak" in signals.quoted_values[0]


def test_semantic_lexicon_extracts_event_actions_across_locales():
    signals = analyze_semantics(
        "Laura megsérült, később pedig időpontot is beütemeztek neki."
    )

    assert "injure" in signals.event_actions
    assert "schedule" in signals.event_actions
