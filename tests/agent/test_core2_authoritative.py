from __future__ import annotations

import json

from agent.core2_authoritative import build_answer_surface, try_authoritative_answer
from agent.core2_longmemeval_benchmark import DEFAULT_DATASET, _seed_core2_kernel
from agent.core2_runtime import Core2Runtime
from agent.core2_types import Core2RecallItem, Core2RecallPacket
from plugins.memory import load_memory_provider


def test_try_authoritative_answer_resolves_temporal_compare(tmp_path):
    entries = json.loads(DEFAULT_DATASET.read_text(encoding="utf-8"))
    entry = next(item for item in entries if item.get("question_id") == "gpt4_2d58bcd6")
    (tmp_path / "memories").mkdir(parents=True, exist_ok=True)
    _seed_core2_kernel(tmp_path, entry, oracle_only=False)

    runtime = Core2Runtime(str(tmp_path / "core2" / "core2.db"))
    runtime.initialize("authoritative-compare")
    packet = runtime.recall(str(entry["question"]), mode="source_supported", operator=None, risk_class="standard", max_items=6)

    resolved = try_authoritative_answer(str(entry["question"]), packet)

    assert resolved is not None
    assert resolved["winner"] == "'The Hate U Give'"
    assert str(resolved["text"]) == "Answer: 'The Hate U Give'."
    assert resolved["answer_surface"]["family"] == "personal_temporal_compare"


def test_core2_provider_authoritative_answer_uses_runtime(tmp_path):
    provider = load_memory_provider("core2")
    assert provider is not None
    provider.initialize("provider-authoritative", hermes_home=str(tmp_path), platform="cli")

    runtime = provider.runtime
    assert runtime is not None
    runtime.ingest_note(
        'I just finished "The Hate U Give" two weeks ago for book club.',
        title="reading log 1",
        namespace="personal",
        risk_class="standard",
        language="en",
        effective_from="2023-05-30T12:42:00+00:00",
        source_type="document_source",
    )
    runtime.ingest_note(
        'I finished "The Nightingale" last weekend and loved it.',
        title="reading log 2",
        namespace="personal",
        risk_class="standard",
        language="en",
        effective_from="2023-05-30T12:42:00+00:00",
        source_type="document_source",
    )

    resolved = provider.authoritative_answer(
        "Which book did I finish reading first, 'The Hate U Give' or 'The Nightingale'?"
    )

    assert resolved is not None
    assert resolved["winner"] == "'The Hate U Give'"
    assert str(resolved["text"]).startswith("Answer: 'The Hate U Give'")

    provider.shutdown()


def test_try_authoritative_answer_extracts_previous_occupation():
    provider = load_memory_provider("core2")
    assert provider is not None
    runtime = Core2Runtime(":memory:")
    runtime.initialize("occupation-authoritative")
    runtime.ingest_note(
        "I used to work as a marketing specialist at a small startup before switching careers.",
        title="career note",
        namespace="personal",
        risk_class="standard",
        language="en",
        effective_from="2023-05-24T23:58:00+00:00",
        source_type="document_source",
        metadata={"turn_index": 1},
    )
    packet = runtime.recall("What was my previous occupation?", mode="source_supported", operator=None, risk_class="standard", max_items=6)

    resolved = try_authoritative_answer("What was my previous occupation?", packet)

    assert resolved is not None
    assert resolved["winner"] == "marketing specialist at a small startup before switching careers"
    assert str(resolved["text"]).startswith("Answer: marketing specialist")

    runtime.shutdown()


def test_provider_authoritative_answer_extracts_residence_from_fact_record(tmp_path):
    provider = load_memory_provider("core2")
    assert provider is not None
    provider.initialize("provider-authoritative-residence", hermes_home=str(tmp_path), platform="cli")

    json.loads(
        provider.handle_tool_call(
            "core2_remember",
            {
                "content": "I live in Budapest.",
                "title": "profile note",
                "namespace": "personal",
                "risk_class": "standard",
                "language": "en",
            },
        )
    )

    resolved = provider.authoritative_answer("Where do I live?")

    assert resolved is not None
    assert resolved["winner"] == "Budapest"
    assert str(resolved["text"]) == "Answer: Budapest."
    assert resolved["answer_surface"]["mode"] == "fact_only"
    assert resolved["answer_surface"]["retrieval_path"] == "fact_first"

    provider.shutdown()


def test_runtime_recall_attaches_answer_surface_for_fact_first_attribute():
    runtime = Core2Runtime(":memory:")
    runtime.initialize("answer-surface-attribute")
    runtime.ingest_note(
        "I live in Budapest.",
        title="profile note",
        namespace="personal",
        risk_class="standard",
        language="en",
        source_type="document_source",
    )

    packet = runtime.recall("Where do I live?", mode="source_supported", operator=None, risk_class="standard", max_items=6)

    assert packet.answer_surface is not None
    surface = packet.answer_surface.to_dict()
    assert surface["mode"] == "fact_only"
    assert surface["text"] == "Answer: Budapest."
    assert surface["retrieval_path"] == "fact_first"

    runtime.shutdown()


def test_provider_recall_tool_includes_answer_surface_for_structured_attribute(tmp_path):
    provider = load_memory_provider("core2")
    assert provider is not None
    provider.initialize("provider-recall-surface", hermes_home=str(tmp_path), platform="cli")

    json.loads(
        provider.handle_tool_call(
            "core2_remember",
            {
                "content": "I live in Budapest.",
                "title": "profile note",
                "namespace": "personal",
                "risk_class": "standard",
                "language": "en",
            },
        )
    )

    payload = json.loads(
        provider.handle_tool_call(
            "core2_recall",
            {"query": "Where do I live?", "mode": "source_supported", "risk_class": "standard"},
        )
    )

    assert payload["answer_surface"]["mode"] == "fact_only"
    assert payload["answer_surface"]["text"] == "Answer: Budapest."
    assert payload["answer_surface"]["retrieval_path"] == "fact_first"

    provider.shutdown()


def test_build_answer_surface_returns_fail_closed_fallback_when_direct_answer_is_not_available():
    packet = Core2RecallPacket(
        query="How many different types of food delivery services have I used recently?",
        mode="source_supported",
        operator=None,
        risk_class="standard",
        support_tier="source_supported",
        confidence="high",
        abstained=False,
        query_family="personal_recall",
        route_family="curated_memory_view",
        display_value="Recent food delivery services include Domino's.",
        items=[
            Core2RecallItem(
                object_id="obj-1",
                plane="canonical_truth",
                object_kind="entity",
                title="Recent food delivery service",
                namespace="personal",
                namespace_class="personal",
                risk_class="standard",
                source_type="digested_fact",
                support_level="source_supported",
                state_status="canonical_active",
                content="Recent food delivery service: Domino's",
                snippet="Recent food delivery service: Domino's",
                metadata={
                    "digest_fact": True,
                    "fact_key": "aggregate.food_delivery_service.recent",
                    "canonical_value": "Domino's",
                },
            )
        ],
    )

    surface = build_answer_surface(
        "How many different types of food delivery services have I used recently?",
        packet,
    )

    assert surface is not None
    assert surface.mode == "fallback"
    assert surface.fallback_reason == "structured_surface_unavailable"


def test_try_authoritative_answer_extracts_personal_best_time():
    runtime = Core2Runtime(":memory:")
    runtime.initialize("personal-best-authoritative")
    runtime.ingest_note(
        "I'm training for another charity 5K run coming up and I'm hoping to beat my personal best time of 25:50 this time around.",
        title="running note",
        namespace="personal",
        risk_class="standard",
        language="en",
        source_type="document_source",
    )

    packet = runtime.recall(
        "What was my personal best time in the charity 5K run?",
        mode="source_supported",
        operator=None,
        risk_class="standard",
        max_items=6,
    )
    resolved = try_authoritative_answer("What was my personal best time in the charity 5K run?", packet)

    assert resolved is not None
    assert resolved["winner"] == "25:50"
    assert resolved["mode"] == "personal_best_time"
    assert "25 minutes and 50 seconds" in str(resolved["text"])

    runtime.shutdown()


def test_try_authoritative_answer_sums_road_trip_distance_with_requested_count():
    runtime = Core2Runtime(":memory:")
    runtime.initialize("roadtrip-authoritative")
    runtime.ingest_note(
        "Since I've covered a total of 1,800 miles on my recent three road trips, including a solo trip to Durango, a weekend trip to Breckenridge, and a family trip to Santa Fe, I'm comfortable with the drive.",
        title="road trip summary",
        namespace="personal",
        risk_class="standard",
        language="en",
        source_type="document_source",
    )
    runtime.ingest_note(
        "I just got back from an amazing 4-day trip to Yellowstone National Park with my family last month, where we covered a total of 1,200 miles.",
        title="yellowstone trip",
        namespace="personal",
        risk_class="standard",
        language="en",
        source_type="document_source",
    )

    packet = runtime.recall(
        "What is the total distance I covered in my four road trips?",
        mode="source_supported",
        operator=None,
        risk_class="standard",
        max_items=6,
    )
    resolved = try_authoritative_answer("What is the total distance I covered in my four road trips?", packet)

    assert resolved is not None
    assert resolved["winner"] == "3,000 miles"
    assert resolved["mode"] == "aggregate_distance"
    assert len(resolved["used_item_ids"]) == 2


def test_try_authoritative_answer_dedupes_session_and_turn_aggregate_evidence():
    runtime = Core2Runtime(":memory:")
    runtime.initialize("roadtrip-dedupe")
    runtime.ingest_note(
        "Session Date: 2023/05/23 USER: I'm planning a road trip. Since I've covered a total of 1,800 miles on my recent three road trips, I'm comfortable with the drive.",
        title="LongMemEval session 18",
        namespace="personal",
        risk_class="standard",
        language="en",
        source_type="document_source",
        metadata={"session_index": 18},
    )
    runtime.ingest_note(
        "User asked: I'm glad I could fit in Maroon Lake. Since I've covered a total of 1,800 miles on my recent three road trips, I'm comfortable with the drive.",
        title="LongMemEval turn 18.5",
        namespace="personal",
        risk_class="standard",
        language="en",
        source_type="document_source",
        metadata={"session_index": 18, "turn_index": 5},
    )
    runtime.ingest_note(
        "User asked: I just got back from an amazing 4-day trip to Yellowstone National Park with my family last month, where we covered a total of 1,200 miles.",
        title="LongMemEval turn 29.1",
        namespace="personal",
        risk_class="standard",
        language="en",
        source_type="document_source",
        metadata={"session_index": 29, "turn_index": 1},
    )

    packet = runtime.recall(
        "What is the total distance I covered in my four road trips?",
        mode="source_supported",
        operator=None,
        risk_class="standard",
        max_items=6,
    )
    resolved = try_authoritative_answer("What is the total distance I covered in my four road trips?", packet)

    assert resolved is not None
    assert resolved["winner"] == "3,000 miles"
    assert len(resolved["used_item_ids"]) == 2

    runtime.shutdown()


def test_try_authoritative_answer_sums_social_media_break_days_from_surfaced_sessions(tmp_path):
    entries = json.loads(DEFAULT_DATASET.read_text(encoding="utf-8"))
    entry = next(item for item in entries if item.get("question_id") == "6cb6f249")
    (tmp_path / "memories").mkdir(parents=True, exist_ok=True)
    _seed_core2_kernel(tmp_path, entry, oracle_only=False)

    runtime = Core2Runtime(str(tmp_path / "core2" / "core2.db"))
    runtime.initialize("social-media-break-total")
    packet = runtime.recall(str(entry["question"]), mode="source_supported", operator=None, risk_class="standard", max_items=12)

    resolved = try_authoritative_answer(str(entry["question"]), packet)

    assert resolved is not None
    assert resolved["winner"] == "17 days"
    assert resolved["mode"] == "aggregate_count"
    assert len(resolved["used_item_ids"]) >= 2

    runtime.shutdown()


def test_try_authoritative_answer_does_not_short_circuit_partial_camping_duration_query(tmp_path):
    entries = json.loads(DEFAULT_DATASET.read_text(encoding="utf-8"))
    entry = next(item for item in entries if item.get("question_id") == "b5ef892d")
    (tmp_path / "memories").mkdir(parents=True, exist_ok=True)
    _seed_core2_kernel(tmp_path, entry, oracle_only=False)

    runtime = Core2Runtime(str(tmp_path / "core2" / "core2.db"))
    runtime.initialize("camping-partial-duration")
    packet = runtime.recall(str(entry["question"]), mode="source_supported", operator=None, risk_class="standard", max_items=12)

    resolved = try_authoritative_answer(str(entry["question"]), packet)

    assert resolved is None

    runtime.shutdown()


def test_try_authoritative_answer_does_not_short_circuit_partial_music_collection_query(tmp_path):
    entries = json.loads(DEFAULT_DATASET.read_text(encoding="utf-8"))
    entry = next(item for item in entries if item.get("question_id") == "bf659f65")
    (tmp_path / "memories").mkdir(parents=True, exist_ok=True)
    _seed_core2_kernel(tmp_path, entry, oracle_only=False)

    runtime = Core2Runtime(str(tmp_path / "core2" / "core2.db"))
    runtime.initialize("music-collection-partial")
    packet = runtime.recall(str(entry["question"]), mode="source_supported", operator=None, risk_class="standard", max_items=12)

    resolved = try_authoritative_answer(str(entry["question"]), packet)

    assert resolved is None

    runtime.shutdown()


def test_try_authoritative_answer_does_not_use_english_aggregate_fast_path_for_non_english_query():
    runtime = Core2Runtime(":memory:")
    runtime.initialize("roadtrip-non-english-query")
    runtime.ingest_note(
        "Since I've covered a total of 1,800 miles on my recent three road trips, including a solo trip to Durango, a weekend trip to Breckenridge, and a family trip to Santa Fe, I'm comfortable with the drive.",
        title="road trip summary",
        namespace="personal",
        risk_class="standard",
        language="en",
        source_type="document_source",
    )
    runtime.ingest_note(
        "I just got back from an amazing 4-day trip to Yellowstone National Park with my family last month, where we covered a total of 1,200 miles.",
        title="yellowstone trip",
        namespace="personal",
        risk_class="standard",
        language="en",
        source_type="document_source",
    )

    packet = runtime.recall(
        "我的四次公路旅行总共开了多少英里？",
        mode="source_supported",
        operator=None,
        risk_class="standard",
        max_items=6,
    )
    resolved = try_authoritative_answer("我的四次公路旅行总共开了多少英里？", packet)

    assert resolved is None

    runtime.shutdown()


def test_new_family_fast_paths_require_structured_fact_first_metadata():
    packet = Core2RecallPacket(
        query="How many different types of food delivery services have I used recently?",
        mode="source_supported",
        operator=None,
        risk_class="standard",
        support_tier="source_supported",
        confidence="high",
        abstained=False,
        query_family="personal_recall",
        route_family="curated_memory_view",
        items=[
            Core2RecallItem(
                object_id="obj-1",
                plane="canonical_truth",
                object_kind="entity",
                title="Recent food delivery service",
                namespace="personal",
                namespace_class="personal",
                risk_class="standard",
                source_type="digested_fact",
                support_level="source_supported",
                state_status="canonical_active",
                content="Recent food delivery service: Domino's",
                snippet="Recent food delivery service: Domino's",
                metadata={
                    "digest_fact": True,
                    "fact_key": "aggregate.food_delivery_service.recent",
                    "canonical_value": "Domino's",
                },
            )
        ],
    )

    resolved = try_authoritative_answer(
        "How many different types of food delivery services have I used recently?",
        packet,
    )

    assert resolved is None


def test_previous_occupation_query_ignores_work_noise_and_prefers_real_role():
    runtime = Core2Runtime(":memory:")
    runtime.initialize("occupation-noise")
    runtime.ingest_note(
        "Building work and practical completion are discussed in detail in this legal note.",
        title="legal memo",
        namespace="personal",
        risk_class="standard",
        language="en",
        source_type="document_source",
    )
    runtime.ingest_note(
        "I used to work as a marketing specialist at a small startup before switching careers.",
        title="career note",
        namespace="personal",
        risk_class="standard",
        language="en",
        source_type="document_source",
        metadata={"turn_index": 1},
    )

    packet = runtime.recall("What was my previous occupation?", mode="source_supported", operator=None, risk_class="standard", max_items=6)
    resolved = try_authoritative_answer("What was my previous occupation?", packet)

    assert packet.items[0].title == "Previous occupation"
    assert packet.items[0].metadata.get("fact_key") == "attribute.occupation.previous"
    assert packet.items[0].metadata.get("retrieval_path") == "fact_first"
    assert resolved is not None
    assert resolved["winner"].startswith("marketing specialist")

    runtime.shutdown()
