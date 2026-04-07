from __future__ import annotations

import json

from plugins.memory import load_memory_provider


def _init_core2(tmp_path, session_id: str = "core2-answer"):
    provider = load_memory_provider("core2")
    assert provider is not None
    provider.initialize(session_id, hermes_home=str(tmp_path), platform="cli")
    return provider


def test_exact_answer_contract_exposes_grounding_and_mode(tmp_path):
    provider = _init_core2(tmp_path)

    json.loads(
        provider.handle_tool_call(
            "core2_remember",
            {
                "content": "Quote: We ship only with grounded release notes.",
                "title": "release quote",
                "namespace": "library",
                "risk_class": "standard",
                "language": "en",
                "effective_from": "2026-01-10T00:00:00+00:00",
            },
        )
    )

    payload = json.loads(
        provider.handle_tool_call(
            "core2_recall",
            {"query": "release quote", "mode": "exact_source_required", "risk_class": "standard"},
        )
    )

    assert payload["abstained"] is False
    assert payload["answer_type"] == "exact_source"
    assert payload["query_mode"] == "exact_source_required"
    assert payload["grounding_refs"]
    assert payload["grounding_refs"][0]["title"] == "release quote"
    assert payload["canonical_value"] == "Quote: We ship only with grounded release notes."
    assert payload["confidence_tier"] in {"high", "medium"}

    provider.shutdown()


def test_compact_answer_contract_uses_final_compact_delivery_view(tmp_path):
    provider = _init_core2(tmp_path, session_id="core2-answer-compact")
    runtime = provider.runtime
    assert runtime is not None

    stored = json.loads(
        provider.handle_tool_call(
            "core2_remember",
            {
                "content": "User prefers concise status updates and no emoji in reports.",
                "title": "status preference",
                "namespace": "personal",
                "risk_class": "standard",
                "language": "en",
            },
        )
    )

    payload = json.loads(
        provider.handle_tool_call("core2_recall", {"query": "status updates", "mode": "compact_memory"})
    )
    final_view = runtime.store.get_delivery_view(stored["object_id"], "final_compact")

    assert payload["abstained"] is False
    assert payload["answer_type"] == "compact_memory"
    assert payload["delivery_view"] == "final_compact"
    assert final_view is not None
    assert payload["display_value"] == final_view["content"]

    provider.shutdown()


def test_high_risk_answer_contract_surfaces_temporal_metadata(tmp_path):
    provider = _init_core2(tmp_path, session_id="core2-answer-risk")
    runtime = provider.runtime
    assert runtime is not None

    stored = json.loads(
        provider.handle_tool_call(
            "core2_remember",
            {
                "content": "Regulation 19 takes effect on 2026-04-01.",
                "title": "regulation 19",
                "namespace": "legal",
                "risk_class": "legal",
                "language": "en",
                "effective_from": "2026-04-01T00:00:00+00:00",
            },
        )
    )
    runtime.store.update_canonical_state(
        stored["object_id"],
        "canonical_active",
        "attach_source_time",
        metadata_patch={"source_created_at": "2026-03-20T00:00:00+00:00"},
        field_updates={
            "source_created_at": "2026-03-20T00:00:00+00:00",
            "support_level": "source_supported",
        },
    )

    payload = json.loads(
        provider.handle_tool_call(
            "core2_recall",
            {"query": "regulation 19", "mode": "source_supported", "risk_class": "legal"},
        )
    )

    assert payload["abstained"] is False
    assert payload["query_family"] == "high_risk_strict"
    assert payload["answer_type"] == "source_supported"
    assert payload["valid_as_of"] == "2026-04-01T00:00:00+00:00"
    assert payload["support_confidence"] in {"high", "medium"}
    assert payload["temporal_confidence"] in {"high", "medium"}
    assert payload["grounding_refs"][0]["source_created_at"] == "2026-03-20T00:00:00+00:00"

    provider.shutdown()
