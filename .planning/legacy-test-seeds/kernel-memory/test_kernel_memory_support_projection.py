from __future__ import annotations

from agent.kernel_memory_support_projection import compile_support_projections


def test_compile_support_projections_for_claim_uses_structured_fields(monkeypatch):
    def _unexpected(*args, **kwargs):
        raise AssertionError("heavy sentence analysis should not run for claim projections")

    monkeypatch.setattr("agent.kernel_memory_support_projection.analyze_semantics", _unexpected, raising=False)
    monkeypatch.setattr("agent.kernel_memory_support_projection.extract_applicability_contract", _unexpected, raising=False)
    record = {
        "kind": "claim",
        "claim_type": "user_preference",
        "content": "I prefer concise answers.",
        "polarity": "neutral",
        "contraindications": [],
        "fact_facets": {"preference_statement": True},
        "metadata": {
            "speaker_role": "user",
            "semantic_categories": ["preference"],
        },
    }

    projections = compile_support_projections(record)

    assert len(projections) == 1
    assert projections[0]["has_preference"] is True
    assert projections[0]["fact_facets"] == {"preference_statement": True}


def test_compile_support_projections_extracts_schedule_duration_and_counts():
    record = {
        "kind": "claim",
        "claim_type": "user_fact",
        "content": "I wake up at 7:30 am on Saturday mornings and spent two weeks in Japan.",
        "polarity": "neutral",
        "contraindications": [],
        "fact_facets": {},
        "metadata": {
            "speaker_role": "user",
            "primary_language": "en",
        },
    }

    projections = compile_support_projections(record)

    assert len(projections) == 1
    assert projections[0]["schedule_signals"]
    assert any(slot["weekday_slot"] == "weekday_5" for slot in projections[0]["schedule_signals"])
    assert any(slot["time_value"] == "7:30 am" for slot in projections[0]["schedule_signals"])
    assert any(signal["amount"] == 2 and signal["unit"] == "week" for signal in projections[0]["duration_signals"])
    assert 2 in projections[0]["numeric_count_values"]
    assert projections[0]["schedule_signal_origin"] == "user_observed_schedule"


def test_compile_support_projections_marks_user_schedule_preference_origin():
    record = {
        "kind": "claim",
        "claim_type": "operational_rule",
        "content": "Also, what time should I start my jog, considering I like to wake up at 7:30 am on Saturdays?",
        "polarity": "neutral",
        "contraindications": [],
        "fact_facets": {},
        "metadata": {
            "speaker_role": "user",
            "primary_language": "en",
        },
    }

    projections = compile_support_projections(record)

    assert len(projections) == 1
    assert any(slot["weekday_slot"] == "weekday_5" for slot in projections[0]["schedule_signals"])
    assert any(slot["time_value"] == "7:30 am" for slot in projections[0]["schedule_signals"])
    assert projections[0]["schedule_signal_origin"] == "user_declared_target_schedule"


def test_compile_support_projections_for_extract_uses_lightweight_path(monkeypatch):
    def _unexpected(*args, **kwargs):
        raise AssertionError("heavy semantic analysis should not run for extract projections")

    monkeypatch.setattr("agent.kernel_memory_support_projection.analyze_semantics", _unexpected, raising=False)
    monkeypatch.setattr("agent.kernel_memory_support_projection.extract_applicability_contract", _unexpected, raising=False)
    record = {
        "kind": "extract",
        "content": "I wake up at 7:30 am on Saturday mornings and spent two weeks in Japan.",
        "metadata": {
            "speaker_role": "user",
            "primary_language": "en",
        },
    }

    projections = compile_support_projections(record)

    assert len(projections) == 1
    assert projections[0]["schedule_signals"]
    assert projections[0]["duration_signals"]
    assert projections[0]["has_event_action"] is False
    assert projections[0]["has_preference"] is False
