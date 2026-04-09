from __future__ import annotations

from agent.decision_memory_store import DecisionMemoryStore
from agent.decision_memory_types import DecisionCandidate


def _store(tmp_path):
    return DecisionMemoryStore.from_env_config(
        {"enabled": True, "root_dir": str(tmp_path / "decision_memory"), "namespace": "test"},
        hermes_home=tmp_path,
        default_namespace="test",
    )


def test_decision_memory_store_upserts_and_dedupes(tmp_path):
    store = _store(tmp_path)
    first = store.upsert_candidate(
        DecisionCandidate(
            kind="decision",
            subject="config.terminal.cwd.authority",
            fact_text="config.yaml is the authority for terminal cwd.",
            scope_type="project",
            scope_key="project",
        )
    )
    second = store.upsert_candidate(
        DecisionCandidate(
            kind="decision",
            subject="config.terminal.cwd.authority",
            fact_text="config.yaml is the authority for terminal cwd.",
            scope_type="project",
            scope_key="project",
            confidence=0.95,
        )
    )

    assert first is not None
    assert second is not None
    assert first.id == second.id
    assert second.confidence >= first.confidence
    assert store.session_stats()["total"] == 1


def test_decision_memory_store_subject_transition_and_query(tmp_path):
    store = _store(tmp_path)
    store.upsert_candidate(
        DecisionCandidate(
            kind="unknown",
            subject="tool.apt.libpq_dev",
            fact_text="Package has no installation candidate.",
            scope_type="session",
            scope_key="sess",
        )
    )
    changed = store.transition_subject(
        namespace="test",
        subject="tool.apt.libpq_dev",
        scope_type="session",
        scope_key="sess",
        from_statuses=("active",),
        to_status="resolved",
        event_type="resolved",
    )
    rows = store.subject_entries(subject="tool.apt.libpq_dev", namespace="test", statuses=("resolved",))

    assert changed == 1
    assert rows
    assert rows[0].status == "resolved"


def test_decision_memory_store_tracks_bucket_and_authority(tmp_path):
    store = _store(tmp_path)
    entry = store.upsert_candidate(
        DecisionCandidate(
            kind="decision",
            subject="config.source",
            fact_text="config.yaml is the source of truth.",
            scope_type="project",
            scope_key="project",
            memory_bucket="directive",
            authority_class="verified_runtime",
            source_anchor_path="config.yaml",
            source_anchor_snippet="source of truth = config.yaml",
            source_anchor_kind="file",
        )
    )

    assert entry is not None
    assert entry.memory_bucket == "directive"
    assert entry.authority_class == "verified_runtime"
    assert entry.source_anchor_path == "config.yaml"
