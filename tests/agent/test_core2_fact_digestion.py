from __future__ import annotations

import json

from plugins.memory import load_memory_provider


def _init_core2(tmp_path, session_id: str = "core2-facts"):
    provider = load_memory_provider("core2")
    assert provider is not None
    provider.initialize(session_id, hermes_home=str(tmp_path), platform="cli")
    return provider


def _digested_records(runtime, fact_key: str):
    return [
        record
        for record in runtime.store.list_canonical_objects()
        if record["metadata"].get("digest_fact") and record["metadata"].get("fact_key") == fact_key
    ]


def test_remember_materializes_digested_attribute_facts(tmp_path):
    provider = _init_core2(tmp_path, session_id="core2-remember-digestion")

    stored = json.loads(
        provider.handle_tool_call(
            "core2_remember",
            {
                "content": "Current role: staff engineer. I live in Budapest.",
                "title": "profile note",
                "namespace": "personal",
                "risk_class": "standard",
                "language": "en",
            },
        )
    )
    runtime = provider.runtime
    assert runtime is not None

    current_role = _digested_records(runtime, "attribute.occupation.current")
    residence = _digested_records(runtime, "attribute.residence.current")

    assert len(current_role) == 1
    assert current_role[0]["metadata"]["canonical_value"] == "staff engineer"
    assert len(residence) == 1
    assert residence[0]["metadata"]["canonical_value"] == "Budapest"

    explained = json.loads(provider.handle_tool_call("core2_explain", {"object_id": current_role[0]["object_id"]}))
    assert any(edge["edge_type"] == "derived_from" and edge["to_id"] == stored["object_id"] for edge in explained["edges"])
    assert any(view["view_kind"] == "fact_compact" for view in explained["delivery_views"])
    assert any(index["index_kind"] == "fact_key" for index in explained["retrieval_indices"])

    provider.shutdown()


def test_sync_turn_materializes_previous_occupation_fact(tmp_path):
    provider = _init_core2(tmp_path, session_id="core2-turn-digestion")
    runtime = provider.runtime
    assert runtime is not None

    provider.sync_turn(
        "I used to work as a marketing specialist at a small startup before switching careers.",
        "Noted.",
        session_id="core2-turn-digestion",
    )

    previous_role = _digested_records(runtime, "attribute.occupation.previous")
    assert len(previous_role) == 1
    assert previous_role[0]["source_type"] == "turn_digested_fact"
    assert previous_role[0]["metadata"]["digest_turn_id"].startswith("turn-")

    provider.shutdown()


def test_collection_total_update_materializes_generic_count_fact(tmp_path):
    provider = _init_core2(tmp_path, session_id="core2-collection-total")
    runtime = provider.runtime
    assert runtime is not None

    json.loads(
        provider.handle_tool_call(
            "core2_remember",
            {
                "content": "I was thinking of organizing my vintage vinyl records by genre. I have a total of 24 records in that collection.",
                "title": "record collection",
                "namespace": "personal",
                "risk_class": "standard",
                "language": "en",
            },
        )
    )

    provider.sync_turn(
        "I just added a new record to my collection.",
        "Nice addition.",
        session_id="core2-collection-total",
    )

    totals = _digested_records(runtime, "aggregate.collection.total.current")
    active = [record for record in totals if record["state_status"] == "canonical_active"]
    superseded = [record for record in totals if record["state_status"] == "superseded"]

    assert len(active) == 1
    assert active[0]["metadata"]["canonical_value"] == "25"
    assert active[0]["metadata"]["item_noun"] == "record"
    assert "vintage vinyl records" in str(active[0]["metadata"]["collection_label"]).lower()
    assert len(superseded) == 1
    assert superseded[0]["metadata"]["canonical_value"] == "24"

    provider.shutdown()


def test_write_time_fact_update_supersedes_previous_current_fact(tmp_path):
    provider = _init_core2(tmp_path, session_id="core2-fact-update")
    runtime = provider.runtime
    assert runtime is not None

    runtime.ingest_note(
        "Current role: engineer",
        title="role note",
        namespace="personal",
        risk_class="standard",
        language="en",
    )
    runtime.ingest_note(
        "Current role: staff engineer",
        title="role note update",
        namespace="personal",
        risk_class="standard",
        language="en",
    )

    records = _digested_records(runtime, "attribute.occupation.current")
    active = [record for record in records if record["state_status"] == "canonical_active"]
    superseded = [record for record in records if record["state_status"] == "superseded"]

    assert len(active) == 1
    assert active[0]["metadata"]["canonical_value"] == "staff engineer"
    assert len(superseded) == 1
    assert superseded[0]["metadata"]["canonical_value"] == "engineer"

    explained = json.loads(provider.handle_tool_call("core2_explain", {"object_id": active[0]["object_id"]}))
    assert any(edge["edge_type"] == "supersedes" and edge["to_id"] == superseded[0]["object_id"] for edge in explained["edges"])

    provider.shutdown()


def test_high_risk_remember_skips_write_time_fact_digestion(tmp_path):
    provider = _init_core2(tmp_path, session_id="core2-high-risk-digest")
    runtime = provider.runtime
    assert runtime is not None

    json.loads(
        provider.handle_tool_call(
            "core2_remember",
            {
                "content": "Current role: compliance officer.",
                "title": "legal profile",
                "namespace": "legal",
                "risk_class": "legal",
                "language": "en",
                "effective_from": "2026-01-01T00:00:00+00:00",
            },
        )
    )

    records = _digested_records(runtime, "attribute.occupation.current")
    assert records == []

    provider.shutdown()
