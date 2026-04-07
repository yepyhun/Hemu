from __future__ import annotations

import json

from agent.core2_types import EDGE_DERIVED_FROM
from plugins.memory import load_memory_provider


def _init_core2(tmp_path, session_id: str = "core2-hardening"):
    provider = load_memory_provider("core2")
    assert provider is not None
    provider.initialize(session_id, hermes_home=str(tmp_path), platform="cli")
    return provider


def test_relation_graph_recall_survives_noise_and_keeps_chain(tmp_path):
    provider = _init_core2(tmp_path, session_id="core2-hardening-graph")
    runtime = provider.runtime
    assert runtime is not None

    alpha = runtime.ingest_note(
        "Alpha service depends on the shared mission index.",
        title="Alpha service",
        namespace="project",
        risk_class="standard",
        language="en",
    )
    beta = runtime.ingest_note(
        "Beta service fans out updates from the shared mission index.",
        title="Beta service",
        namespace="project",
        risk_class="standard",
        language="en",
    )
    gamma = runtime.ingest_note(
        "Gamma service publishes reports from the shared mission index.",
        title="Gamma service",
        namespace="project",
        risk_class="standard",
        language="en",
    )
    runtime.store.add_edge(
        from_plane="canonical_truth",
        from_id=alpha["object_id"],
        to_plane="canonical_truth",
        to_id=beta["object_id"],
        edge_type=EDGE_DERIVED_FROM,
    )
    runtime.store.add_edge(
        from_plane="canonical_truth",
        from_id=beta["object_id"],
        to_plane="canonical_truth",
        to_id=gamma["object_id"],
        edge_type=EDGE_DERIVED_FROM,
    )

    for idx in range(8):
        runtime.ingest_note(
            f"Noise note {idx} mentions unrelated mission chores and archive cleanup.",
            title=f"noise-{idx}",
            namespace="library",
            risk_class="standard",
            language="en",
        )

    payload = json.loads(
        provider.handle_tool_call(
            "core2_recall",
            {"query": "What is the relationship between Alpha and Gamma?", "mode": "source_supported"},
        )
    )

    assert payload["abstained"] is False
    assert payload["route_family"] == "association/graph-assisted"
    assert payload["retrieved_item_count"] >= 3
    assert {item["title"] for item in payload["items"]} >= {"Alpha service", "Beta service", "Gamma service"}

    provider.shutdown()


def test_update_resolution_stays_on_latest_record_with_noise(tmp_path):
    provider = _init_core2(tmp_path, session_id="core2-hardening-update")
    runtime = provider.runtime
    assert runtime is not None

    old_record = runtime.ingest_note(
        "Current deployment owner is Alice.",
        title="deployment owner",
        namespace="project",
        risk_class="standard",
        language="en",
        metadata={"identity_key": "deploy.owner"},
    )
    mid_record = runtime.ingest_note(
        "Current deployment owner is Charlie.",
        title="deployment owner",
        namespace="project",
        risk_class="standard",
        language="en",
        metadata={"identity_key": "deploy.owner"},
    )
    new_record = runtime.ingest_note(
        "Current deployment owner is Bob.",
        title="deployment owner",
        namespace="project",
        risk_class="standard",
        language="en",
        metadata={"identity_key": "deploy.owner"},
    )
    runtime.supersede_object(mid_record["object_id"], old_record["object_id"], reason="owner_changed")
    runtime.supersede_object(new_record["object_id"], mid_record["object_id"], reason="owner_changed")

    for idx in range(4):
        runtime.ingest_note(
            f"Deployment checklist owner item {idx} is still pending review.",
            title=f"deployment checklist {idx}",
            namespace="project",
            risk_class="standard",
            language="en",
        )

    payload = json.loads(provider.handle_tool_call("core2_recall", {"query": "What is the current deployment owner?"}))

    assert payload["abstained"] is False
    assert payload["query_family"] == "update_resolution"
    assert payload["items"][0]["object_id"] == new_record["object_id"]
    assert "Bob" in payload["items"][0]["content"]
    assert all("Alice" not in item["content"] for item in payload["items"])

    provider.shutdown()


def test_high_risk_conflict_still_abstains_with_noise(tmp_path):
    provider = _init_core2(tmp_path, session_id="core2-hardening-conflict")
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
    runtime.mark_conflict(left["object_id"], right["object_id"], reason="regulation_conflict")

    for idx in range(6):
        runtime.ingest_note(
            f"Unrelated legal archive note {idx} references older paperwork only.",
            title=f"legal-noise-{idx}",
            namespace="legal",
            risk_class="legal",
            language="en",
        )

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
