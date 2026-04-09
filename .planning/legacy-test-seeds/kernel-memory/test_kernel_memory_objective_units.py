from __future__ import annotations

from agent.kernel_memory import KernelMemoryConfig, KernelMemoryStore
from agent.kernel_memory_objective_units import (
    OBJECTIVE_UNIT_COMPILER_FINGERPRINT,
    compile_objective_units,
)


def test_compile_objective_units_extracts_recommendation_and_direct_attribute():
    record = {
        "id": "clm-test",
        "kind": "claim",
        "confidence": 0.91,
        "content_hash": "hash-1",
        "observed_at": "2023-02-01T10:00:00+00:00",
        "metadata": {"memory_class": "profile_preference", "session_id": "s1", "speaker_role": "user"},
    }
    projections = [
        {
            "sentence": "I love quiet tea houses for winding down.",
            "sentence_labels": ["quiet tea houses"],
            "fact_facets": {},
            "polarity": "neutral",
            "contraindications": [],
            "has_event_action": False,
            "has_preference": True,
        },
        {
            "sentence": "A Golden Retriever like Max needs a wider collar.",
            "sentence_labels": ["Max"],
            "fact_facets": {
                "descriptor_pairs": [
                    {"descriptor": "Golden Retriever", "entity": "Max"},
                ]
            },
            "polarity": "neutral",
            "contraindications": [],
            "has_event_action": False,
            "has_preference": False,
        },
    ]

    units = compile_objective_units(record=record, projections=projections)

    assert any(
        unit["unit_type"] == "recommendation_signal"
        and unit["canonical_target_key"] == "quiet tea houses"
        and unit["signal_kind"] == "prefer"
        for unit in units
    )
    assert any(
        unit["unit_type"] == "direct_attribute"
        and unit["canonical_subject_key"] == "max"
        and unit["attribute_name"] == "descriptor"
        and unit["attribute_value"] == "Golden Retriever"
        for unit in units
    )


def test_ingest_claim_persists_owner_scoped_objective_units(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(
            enabled=True,
            root_dir=tmp_path / "kernel",
            namespace="bestie",
            curated_retrieval_only=False,
        )
    )

    claim = store.ingest_claim(
        claim_type="user_preference",
        content="I love quiet tea houses for winding down.",
        metadata={
            "origin": "test",
            "memory_class": "profile_preference",
            "session_id": "session-1",
            "speaker_role": "user",
        },
        observed_at="2023-02-01T10:00:00+00:00",
    )

    objective_units = store.get_objective_units(owner_kind="claim", owner_id=claim["id"])

    assert objective_units is not None
    assert objective_units["owner_content_hash"] == claim["content_hash"]
    assert objective_units["compiler_fingerprint"] == OBJECTIVE_UNIT_COMPILER_FINGERPRINT
    assert any(
        unit["unit_type"] == "recommendation_signal" and unit["signal_kind"] == "prefer"
        for unit in objective_units["units"]
    )
    shard_path = store._objective_unit_shard_path(store._objective_unit_shard_id(objective_units))
    assert shard_path.exists()

    reloaded = KernelMemoryStore.from_config(store.config)
    listed = reloaded.list_objective_units(session_ids={"session-1"}, unit_types={"recommendation_signal"})

    assert any(record["id"] == objective_units["id"] for record in listed)


def test_compile_objective_units_extracts_duration_schedule_inventory_grounded_advice_and_numeric_name_units():
    record = {
        "id": "clm-structured",
        "kind": "claim",
        "confidence": 0.94,
        "content_hash": "hash-structured",
        "observed_at": "2023-02-01T10:00:00+00:00",
        "metadata": {"memory_class": "profile_preference", "session_id": "s1", "speaker_role": "user"},
    }
    projections = [
        {
            "sentence": "I wake up at 7:30 am on Saturday mornings.",
            "sentence_labels": [],
            "fact_facets": {},
            "polarity": "neutral",
            "contraindications": [],
            "duration_signals": [],
            "schedule_signals": [{"weekday_slot": "weekday_5", "time_value": "7:30 am"}],
            "schedule_signal_origin": "user_observed_schedule",
            "current_state_signal": True,
            "numeric_count_values": [],
            "has_event_action": False,
            "has_preference": False,
        },
        {
            "sentence": "I spent two weeks in Japan.",
            "sentence_labels": ["Japan"],
            "fact_facets": {},
            "polarity": "neutral",
            "contraindications": [],
            "duration_signals": [{"amount": 2, "unit": "week", "text": "two weeks"}],
            "schedule_signals": [],
            "current_state_signal": False,
            "numeric_count_values": [2],
            "has_event_action": True,
            "has_preference": False,
        },
        {
            "sentence": "I currently own 4 musical instruments.",
            "sentence_labels": ["musical instruments"],
            "fact_facets": {},
            "polarity": "neutral",
            "contraindications": [],
            "duration_signals": [],
            "schedule_signals": [],
            "current_state_signal": True,
            "numeric_count_values": [4],
            "has_event_action": False,
            "has_preference": False,
        },
        {
            "sentence": "Use my Suica card and TripIt app when giving Tokyo travel advice.",
            "sentence_labels": ["Suica", "TripIt", "Tokyo travel advice"],
            "fact_facets": {},
            "polarity": "neutral",
            "contraindications": [],
            "duration_signals": [],
            "schedule_signals": [],
            "current_state_signal": False,
            "numeric_count_values": [],
            "has_event_action": False,
            "has_preference": True,
        },
        {
            "sentence": "My undergraduate studies at the University of Mumbai finished with an overall percentage of 83%, equivalent to a GPA of 3.86 out of 4.0.",
            "sentence_labels": ["University of Mumbai"],
            "fact_facets": {},
            "polarity": "neutral",
            "contraindications": [],
            "duration_signals": [],
            "schedule_signals": [],
            "current_state_signal": False,
            "numeric_count_values": [],
            "numeric_measure_signals": [
                {
                    "value": 83.0,
                    "scale": 100.0,
                    "text": "83%",
                    "support_text": "overall percentage of 83%",
                    "value_type": "percent",
                },
                {
                    "value": 3.86,
                    "scale": 4.0,
                    "text": "3.86 out of 4.0",
                    "support_text": "equivalent to a GPA of 3.86 out of 4.0",
                    "value_type": "scaled",
                },
            ],
            "has_event_action": False,
            "has_preference": False,
        },
    ]

    units = compile_objective_units(record=record, projections=projections)

    assert any(unit["unit_type"] == "schedule_slot" and unit["time_value"] == "7:30 am" for unit in units)
    assert any(
        unit["unit_type"] == "schedule_slot"
        and unit["time_value"] == "7:30 am"
        and unit["schedule_signal_origin"] == "user_observed_schedule"
        for unit in units
    )
    assert any(unit["unit_type"] == "duration_unit" and unit["duration_value"] == 2 and unit["duration_unit"] == "week" for unit in units)
    assert any(unit["unit_type"] == "count_inventory" and unit["count_value"] == 4 and unit["is_current"] is True for unit in units)
    assert any(unit["unit_type"] == "grounded_advice" and "Suica" in unit["resource_values"] for unit in units)
    assert any(unit["unit_type"] == "numeric_measure" and unit["measure_value"] == 3.86 and unit["measure_scale"] == 4.0 for unit in units)
    assert any(unit["unit_type"] == "named_entity" and unit["entity_name"] == "University of Mumbai" for unit in units)


def test_compile_objective_units_skips_generic_assistant_advice_without_personal_grounding():
    record = {
        "id": "cur-generic",
        "kind": "curated_memory",
        "summary": "I'm here to provide general information, answer questions, and offer suggestions.",
        "content_hash": "hash-generic",
        "observed_at": "2023-02-01T10:00:00+00:00",
        "metadata": {"speaker_role": "assistant", "session_id": "s1"},
    }
    projections = [
        {
            "sentence": "I'm here to provide general information, answer questions, and offer suggestions.",
            "sentence_labels": ["general information", "suggestions"],
            "fact_facets": {},
            "polarity": "neutral",
            "contraindications": [],
            "duration_signals": [],
            "schedule_signals": [],
            "current_state_signal": False,
            "numeric_count_values": [],
            "has_event_action": False,
            "has_preference": True,
        }
    ]

    units = compile_objective_units(record=record, projections=projections)

    assert not any(unit["unit_type"] == "grounded_advice" for unit in units)
