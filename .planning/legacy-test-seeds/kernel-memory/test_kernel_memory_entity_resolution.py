from __future__ import annotations

from agent.kernel_memory_entity_resolution import resolve_sentence_entities


def test_entity_resolution_filters_pronoun_like_non_entities():
    resolved = resolve_sentence_entities("Ez nem a kedvenc idézetem.", speaker_role="user")

    assert resolved.actor_label == "user"
    assert resolved.counterparty_labels == ()


def test_entity_resolution_filters_ack_and_verbish_tokens():
    resolved = resolve_sentence_entities(
        "Javítottam, Laura helyett ezt kezelem kedvenc idézetként.",
        speaker_role="assistant",
    )

    assert resolved.actor_label == "Laura"


def test_entity_resolution_does_not_treat_value_clause_text_as_entity():
    resolved = resolve_sentence_entities(
        'A kedvenc idézetem inkább az, hogy Egyik szél sem jó annak a hajósnak.',
        speaker_role="user",
    )

    assert resolved.actor_label == "user"


def test_entity_resolution_keeps_user_as_actor_and_detects_named_object_phrase():
    resolved = resolve_sentence_entities(
        "I'm actually thinking of using my new Instant Pot to make some soups.",
        speaker_role="user",
    )

    assert resolved.actor_label == "user"
    assert "Instant Pot" in resolved.object_labels
