from __future__ import annotations

import json

from plugins.memory import load_memory_provider


def _init_core2(tmp_path, session_id: str = "core2-abstention"):
    provider = load_memory_provider("core2")
    assert provider is not None
    provider.initialize(session_id, hermes_home=str(tmp_path), platform="cli")
    return provider


def test_high_risk_conflict_forces_abstention(tmp_path):
    provider = _init_core2(tmp_path)
    runtime = provider.runtime
    assert runtime is not None

    left = runtime.ingest_note(
        "Regulation 21 requires approval from Board A.",
        title="regulation 21",
        namespace="legal",
        risk_class="legal",
        language="en",
        effective_from="2026-05-01T00:00:00+00:00",
        metadata={"source_created_at": "2026-04-20T00:00:00+00:00"},
    )
    right = runtime.ingest_note(
        "Regulation 21 requires approval from Board B.",
        title="regulation 21",
        namespace="legal",
        risk_class="legal",
        language="en",
        effective_from="2026-05-01T00:00:00+00:00",
        metadata={"source_created_at": "2026-04-21T00:00:00+00:00"},
    )
    runtime.store.update_canonical_state(
        left["object_id"],
        left["state_status"],
        "attach_source_time",
        metadata_patch={"source_created_at": "2026-04-20T00:00:00+00:00"},
        field_updates={"source_created_at": "2026-04-20T00:00:00+00:00", "support_level": "source_supported"},
    )
    runtime.store.update_canonical_state(
        right["object_id"],
        right["state_status"],
        "attach_source_time",
        metadata_patch={"source_created_at": "2026-04-21T00:00:00+00:00"},
        field_updates={"source_created_at": "2026-04-21T00:00:00+00:00", "support_level": "source_supported"},
    )
    assert runtime.mark_conflict(left["object_id"], right["object_id"], reason="regulation_conflict")

    payload = json.loads(
        provider.handle_tool_call(
            "core2_recall",
            {"query": "regulation 21", "mode": "source_supported", "risk_class": "legal"},
        )
    )

    assert payload["abstained"] is True
    assert "conflict" in (payload["abstain_reason"] or "").lower()
    assert payload["conflict_refs"]

    provider.shutdown()


def test_exploratory_route_stays_bounded(tmp_path):
    provider = _init_core2(tmp_path, session_id="core2-abstention-explore")

    for idx in range(12):
        json.loads(
            provider.handle_tool_call(
                "core2_remember",
                {
                    "content": f"Orbital theme note {idx} covers transfer windows and mission timing.",
                    "title": f"orbital-theme-{idx}",
                    "namespace": "library",
                    "risk_class": "standard",
                    "language": "en",
                },
            )
        )

    payload = json.loads(
        provider.handle_tool_call(
            "core2_recall",
            {"query": "explore orbital transfer themes", "mode": "exploratory_full", "max_items": 50},
        )
    )

    assert payload["abstained"] is False
    assert payload["query_family"] == "exploratory_discovery"
    assert payload["delivery_view"] == "exploratory_full"
    assert payload["route_plan"]["retrieval_cap"] == 8
    assert payload["retrieved_item_count"] <= 8

    provider.shutdown()


def test_prefetch_uses_compact_delivery_contract(tmp_path):
    provider = _init_core2(tmp_path, session_id="core2-abstention-prefetch")

    json.loads(
        provider.handle_tool_call(
            "core2_remember",
            {
                "content": "The user prefers compact release summaries with only the active deployment facts included.",
                "title": "release summary policy",
                "namespace": "personal",
                "risk_class": "standard",
                "language": "en",
            },
        )
    )

    provider.queue_prefetch("release summaries", session_id="core2-abstention-prefetch")
    prefetched = provider.prefetch("unused", session_id="core2-abstention-prefetch")

    assert "# Core2 Prefetch" in prefetched
    assert "release summary policy:" in prefetched
    assert "compact release summaries" in prefetched

    provider.shutdown()
