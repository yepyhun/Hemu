from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from plugins.memory import load_memory_provider


def _init_core2(tmp_path, session_id: str = "core2-plane"):
    provider = load_memory_provider("core2")
    assert provider is not None
    provider.initialize(session_id, hermes_home=str(tmp_path), platform="cli")
    return provider


def _db_path(tmp_path) -> Path:
    return Path(tmp_path) / "core2" / "core2.db"


def test_core2_stores_raw_and_canonical_planes_separately(tmp_path):
    provider = _init_core2(tmp_path)

    stored = json.loads(
        provider.handle_tool_call(
            "core2_remember",
            {
                "content": "Project Atlas uses a staged rollout process.",
                "title": "atlas rollout",
                "namespace": "project",
                "risk_class": "standard",
                "language": "en",
            },
        )
    )
    object_id = stored["object_id"]
    explained = json.loads(provider.handle_tool_call("core2_explain", {"object_id": object_id}))

    assert explained["plane"] == "canonical_truth"
    assert explained["source_record"]["plane"] == "raw_archive"
    assert explained["source_record"]["raw_id"] == explained["source_raw_id"]

    provider.shutdown()

    conn = sqlite3.connect(_db_path(tmp_path))
    try:
        raw_count = conn.execute("SELECT COUNT(*) FROM core2_raw_archive").fetchone()[0]
        canonical_count = conn.execute("SELECT COUNT(*) FROM core2_canonical_truth").fetchone()[0]
        index_count = conn.execute("SELECT COUNT(*) FROM core2_retrieval_indices").fetchone()[0]
        view_count = conn.execute("SELECT COUNT(*) FROM core2_delivery_views").fetchone()[0]
    finally:
        conn.close()

    assert raw_count == 1
    assert canonical_count == 1
    assert index_count >= 1
    assert view_count >= 1


def test_core2_propositions_live_in_the_derived_plane(tmp_path):
    provider = _init_core2(tmp_path, session_id="core2-proposition")
    runtime = provider.runtime
    assert runtime is not None

    canonical = runtime.ingest_note(
        "The release checklist includes a staging approval.",
        title="release checklist",
        namespace="project",
        risk_class="standard",
        language="en",
    )
    proposition = runtime.ingest_proposition(
        "The project requires staging approval before release.",
        title="release rule",
        namespace="project",
        risk_class="standard",
        language="en",
        source_object_ids=[canonical["object_id"]],
    )

    assert proposition["plane"] == "derived_propositions"

    provider.shutdown()

    conn = sqlite3.connect(_db_path(tmp_path))
    try:
        canonical_count = conn.execute("SELECT COUNT(*) FROM core2_canonical_truth").fetchone()[0]
        proposition_count = conn.execute("SELECT COUNT(*) FROM core2_derived_propositions").fetchone()[0]
    finally:
        conn.close()

    assert canonical_count == 1
    assert proposition_count == 1


def test_core2_explain_includes_delivery_views_and_transitions(tmp_path):
    provider = _init_core2(tmp_path, session_id="core2-explain-plane")

    stored = json.loads(
        provider.handle_tool_call(
            "core2_remember",
            {
                "content": "The user prefers concise summaries.",
                "title": "summary preference",
                "namespace": "personal",
                "risk_class": "standard",
                "language": "en",
            },
        )
    )

    explained = json.loads(provider.handle_tool_call("core2_explain", {"object_id": stored["object_id"]}))

    assert explained["delivery_views"]
    assert explained["transitions"]
    assert explained["transitions"][0]["to_state"] == "canonical_active"

    provider.shutdown()
