from __future__ import annotations

import json

from plugins.memory import load_memory_provider


def _init_core2(tmp_path, session_id: str = "core2-temporal"):
    provider = load_memory_provider("core2")
    assert provider is not None
    provider.initialize(session_id, hermes_home=str(tmp_path), platform="cli")
    return provider


def test_high_risk_memory_abstains_without_required_temporal_fields(tmp_path):
    provider = _init_core2(tmp_path)

    stored = json.loads(
        provider.handle_tool_call(
            "core2_remember",
            {
                "content": "Ibuprofen dosing guidance changed recently.",
                "title": "ibuprofen guidance",
                "namespace": "medical",
                "risk_class": "medical",
                "language": "en",
            },
        )
    )
    assert stored["namespace_class"] == "high_risk"

    payload = json.loads(
        provider.handle_tool_call(
            "core2_recall",
            {"query": "ibuprofen guidance", "mode": "compact_memory", "risk_class": "medical"},
        )
    )

    assert payload["abstained"] is True
    assert "High-risk memory requires source-supported or exact-source recall." in payload["reason"]

    provider.shutdown()


def test_high_risk_memory_can_be_recalled_when_temporally_grounded(tmp_path):
    provider = _init_core2(tmp_path, session_id="core2-high-risk")

    stored = json.loads(
        provider.handle_tool_call(
            "core2_remember",
            {
                "content": "Regulation 12 applies from 2026-01-01.",
                "title": "regulation 12",
                "namespace": "legal",
                "risk_class": "legal",
                "language": "en",
                "effective_from": "2026-01-01T00:00:00+00:00",
            },
        )
    )
    runtime = provider.runtime
    assert runtime is not None
    runtime.store.update_canonical_state(
        stored["object_id"],
        "canonical_active",
        "attach_source_time",
        metadata_patch={"source_created_at": "2026-01-02T00:00:00+00:00"},
        field_updates={
            "source_created_at": "2026-01-02T00:00:00+00:00",
            "support_level": "source_supported",
        },
    )

    payload = json.loads(
        provider.handle_tool_call(
            "core2_recall",
            {"query": "regulation 12", "mode": "source_supported", "risk_class": "legal"},
        )
    )

    assert payload["abstained"] is False
    assert payload["items"][0]["namespace_class"] == "high_risk"
    assert payload["items"][0]["effective_from"] == "2026-01-01T00:00:00+00:00"

    provider.shutdown()


def test_superseded_record_drops_out_of_current_recall(tmp_path):
    provider = _init_core2(tmp_path, session_id="core2-current-state")
    runtime = provider.runtime
    assert runtime is not None

    old_record = runtime.ingest_note(
        "Current role: engineer",
        title="current role",
        namespace="personal",
        risk_class="standard",
        language="en",
        metadata={"identity_key": "role.current"},
    )
    new_record = runtime.ingest_note(
        "Current role: staff engineer",
        title="current role",
        namespace="personal",
        risk_class="standard",
        language="en",
        metadata={"identity_key": "role.current"},
    )

    assert runtime.supersede_object(new_record["object_id"], old_record["object_id"], reason="role_updated")

    payload = json.loads(
        provider.handle_tool_call(
            "core2_recall",
            {"query": "current role", "mode": "compact_memory", "tool_budget_profile": "full"},
        )
    )
    old_explained = json.loads(provider.handle_tool_call("core2_explain", {"object_id": old_record["object_id"]}))

    assert payload["abstained"] is False
    assert payload["items"][0]["metadata"].get("fact_key") == "attribute.occupation.current"
    assert payload["items"][0]["metadata"].get("retrieval_path") == "fact_first"
    assert all(item["object_id"] != old_record["object_id"] for item in payload["items"])
    assert old_explained["state_status"] == "superseded"
    assert old_explained["metadata"]["superseded_by"] == new_record["object_id"]

    provider.shutdown()


def test_conflict_markers_are_visible_on_explain(tmp_path):
    provider = _init_core2(tmp_path, session_id="core2-conflict")
    runtime = provider.runtime
    assert runtime is not None

    left = runtime.ingest_note(
        "The rollout owner is Alice.",
        title="rollout owner",
        namespace="project",
        risk_class="standard",
        language="en",
        metadata={"identity_key": "owner.rollout"},
    )
    right = runtime.ingest_note(
        "The rollout owner is Bob.",
        title="rollout owner",
        namespace="project",
        risk_class="standard",
        language="en",
        metadata={"identity_key": "owner.rollout"},
    )

    assert runtime.mark_conflict(left["object_id"], right["object_id"], reason="owner_conflict")

    explained = json.loads(provider.handle_tool_call("core2_explain", {"object_id": left["object_id"]}))

    assert right["object_id"] in explained["metadata"]["conflict_refs"]
    assert any(edge["edge_type"] == "conflicts_with" for edge in explained["edges"])

    provider.shutdown()
