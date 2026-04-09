from __future__ import annotations

from agent.decision_memory_lifecycle import DecisionMemoryLifecycle
from agent.decision_memory_store import DecisionMemoryStore
from agent.decision_memory_types import DecisionCandidate


def _lifecycle(tmp_path):
    store = DecisionMemoryStore.from_env_config(
        {"enabled": True, "root_dir": str(tmp_path / "decision_memory"), "namespace": "test"},
        hermes_home=tmp_path,
        default_namespace="test",
    )
    return store, DecisionMemoryLifecycle(store)


def test_decision_lifecycle_resolves_subject_and_records_resolved_entry(tmp_path):
    store, lifecycle = _lifecycle(tmp_path)
    store.upsert_candidate(
        DecisionCandidate(
            kind="unknown",
            subject="tool.apt.libpq_dev",
            fact_text="Package has no installation candidate.",
            scope_type="session",
            scope_key="sess",
        )
    )

    updated = lifecycle.resolve_subject(
        namespace="test",
        subject="tool.apt.libpq_dev",
        scope_type="session",
        scope_key="sess",
        fact_text="Resolved via apt cache refresh workaround.",
    )
    rows = store.subject_entries(subject="tool.apt.libpq_dev", namespace="test", statuses=("resolved",))

    assert updated == 1
    assert len(rows) >= 1
    assert any(row.kind == "resolved" for row in rows)


def test_decision_lifecycle_obsoletes_subject(tmp_path):
    store, lifecycle = _lifecycle(tmp_path)
    store.upsert_candidate(
        DecisionCandidate(
            kind="decision",
            subject="file.app_py.db_url_source",
            fact_text="db_url came from localhost literal.",
            scope_type="file",
            scope_key="app.py",
        )
    )

    updated = lifecycle.obsolete_subject(
        namespace="test",
        subject="file.app_py.db_url_source",
        scope_type="file",
        scope_key="app.py",
        reason="Replaced by env-based DB source.",
    )
    rows = store.subject_entries(subject="file.app_py.db_url_source", namespace="test", statuses=("obsolete",))

    assert updated == 1
    assert rows
    assert any(row.kind == "obsolete" for row in rows)

