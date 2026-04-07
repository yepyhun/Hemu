from __future__ import annotations

from agent.core2_authoritative import try_authoritative_answer
from agent.core2_runtime import Core2Runtime


def _digested_records(runtime: Core2Runtime, fact_key: str):
    return [
        record
        for record in runtime.store.list_canonical_objects()
        if record["metadata"].get("digest_fact") and record["metadata"].get("fact_key") == fact_key
    ]


def test_preference_family_contract_is_wired_end_to_end():
    runtime = Core2Runtime(":memory:")
    runtime.initialize("preference-family-contract")
    runtime.ingest_note(
        "I prefer relaxing activities that can be done in the evening, preferably before 9:30 pm.",
        title="evening preference",
        namespace="personal",
        risk_class="standard",
        language="en",
        effective_from="2023-05-30T19:00:00+00:00",
    )
    runtime.ingest_note(
        "Using my phone or watching TV in the evening has been affecting my sleep quality, so I want to avoid that at night.",
        title="sleep routine",
        namespace="personal",
        risk_class="standard",
        language="en",
        effective_from="2023-05-30T20:00:00+00:00",
    )

    positive = _digested_records(runtime, "preference.evening.activities.current")
    negative = _digested_records(runtime, "preference.evening.screen_avoid.current")
    assert len(positive) == 1
    assert len(negative) == 1

    query = "Can you suggest some activities that I can do in the evening?"
    packet = runtime.recall(query, mode="source_supported", operator=None, risk_class="standard", max_items=6)

    assert packet.abstained is False
    assert "fact_first_hit" in list(packet.route_plan.get("notes") or [])
    fact_keys = {str(item.metadata.get("fact_key") or "") for item in packet.items}
    assert "preference.evening.activities.current" in fact_keys
    assert "preference.evening.screen_avoid.current" in fact_keys

    resolved = try_authoritative_answer(query, packet)
    assert resolved is not None
    assert "relaxing activities in the evening before 9:30 pm" in str(resolved["text"]).lower()
    assert "watching tv" in str(resolved["text"]).lower()

    runtime.shutdown()


def test_aggregate_family_contract_is_wired_end_to_end():
    runtime = Core2Runtime(":memory:")
    runtime.initialize("aggregate-family-contract")
    for content, title in (
        ("I've been relying on food delivery services a lot lately - I had Domino's Pizza three times last week!", "delivery 1"),
        ("Uber Eats has been my backup when I don't feel like cooking.", "delivery 2"),
        ("I ordered through DoorDash again after work this week.", "delivery 3"),
    ):
        runtime.ingest_note(
            content,
            title=title,
            namespace="personal",
            risk_class="standard",
            language="en",
            effective_from="2023-05-30T18:00:00+00:00",
        )

    members = _digested_records(runtime, "aggregate.food_delivery_service.recent")
    assert {record["metadata"]["canonical_value"] for record in members} == {"Domino's", "Uber Eats", "DoorDash"}

    query = "How many different types of food delivery services have I used recently?"
    packet = runtime.recall(query, mode="source_supported", operator=None, risk_class="standard", max_items=6)

    assert packet.abstained is False
    assert "fact_first_hit" in list(packet.route_plan.get("notes") or [])
    aggregate_items = [item for item in packet.items if item.metadata.get("fact_key") == "aggregate.food_delivery_service.recent"]
    assert len(aggregate_items) >= 3
    assert packet.items[0].metadata.get("fact_key") == "aggregate.food_delivery_service.recent"

    resolved = try_authoritative_answer(query, packet)
    assert resolved is not None
    assert resolved["winner"] == "3"
    assert str(resolved["text"]) == "Answer: 3."

    runtime.shutdown()


def test_temporal_family_contract_is_wired_end_to_end():
    runtime = Core2Runtime(":memory:")
    runtime.initialize("temporal-family-contract")
    runtime.ingest_note(
        'I just finished reading "The Seven Husbands of Evelyn Hugo" in my online book club.',
        title="reading completion",
        namespace="personal",
        risk_class="standard",
        language="en",
        effective_from="2023-01-23T18:00:00+00:00",
    )
    runtime.ingest_note(
        'I attended the book reading event at the local library, where the author of "The Silent Patient" was discussing the latest thriller novel.',
        title="library event",
        namespace="personal",
        risk_class="standard",
        language="en",
        effective_from="2023-02-10T18:44:00+00:00",
    )

    reading = _digested_records(runtime, "event.reading.completed")
    attended = _digested_records(runtime, "event.library.book_reading.attended")
    assert len(reading) == 1
    assert len(attended) == 1

    query = "How many days had passed since I finished reading 'The Seven Husbands of Evelyn Hugo' when I attended the book reading event at the local library, where the author of 'The Silent Patient' is discussing her latest thriller novel?"
    packet = runtime.recall(query, mode="source_supported", operator=None, risk_class="standard", max_items=6)

    assert packet.abstained is False
    assert "fact_first_hit" in list(packet.route_plan.get("notes") or [])
    fact_keys = {str(item.metadata.get("fact_key") or "") for item in packet.items}
    assert "event.reading.completed" in fact_keys
    assert "event.library.book_reading.attended" in fact_keys

    resolved = try_authoritative_answer(query, packet)
    assert resolved is not None
    assert resolved["winner"] == "18 days"
    assert str(resolved["text"]) == "Answer: 18 days."

    runtime.shutdown()
