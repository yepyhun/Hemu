from __future__ import annotations

from agent.kernel_memory import KernelMemoryConfig, KernelMemoryStore
from agent.kernel_memory_admin import KernelMemoryAdminService
from agent.kernel_memory_curated_maintenance import KernelMemoryCuratedMaintenanceService


def _make_store(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
    )
    return config, KernelMemoryStore.from_config(config)


def test_curated_maintenance_invalidates_curated_memory_with_only_stale_support(tmp_path):
    config, store = _make_store(tmp_path)
    claim = store.ingest_claim(
        claim_type="fact",
        content="Laura rehab changed last week.",
    )
    event = store.ingest_event(
        event_type="rehab_update",
        title="Laura rehab update",
        summary="Laura rehab changed last week.",
        claim_ids=[claim["id"]],
    )
    curated = store.materialize_curated_memory(
        title="Laura rehab memory",
        summary="Laura rehab changed last week.",
        claim_ids=[claim["id"]],
        event_ids=[event["id"]],
    )
    store.update_record_status("claim", claim["id"], status="superseded", reason="newer claim")
    store.update_record_status("event", event["id"], status="superseded", reason="newer event")

    result = KernelMemoryCuratedMaintenanceService(config, store).run()

    assert result["status"] == "ok"
    assert result["invalidated"] == 1
    refreshed = store.get_record("curated_memory", curated["id"])
    assert refreshed["status"] == "invalidated"
    assert refreshed["invalidated_at"]


def test_curated_maintenance_keeps_source_backed_curated_memory_active(tmp_path):
    config, store = _make_store(tmp_path)
    claim = store.ingest_claim(
        claim_type="fact",
        content="Laura rehab changed last week.",
    )
    curated = store.materialize_curated_memory(
        title="Laura rehab memory",
        summary="Laura rehab changed last week.",
        claim_ids=[claim["id"]],
        source_ids=["doc:laura-rehab"],
    )
    store.update_record_status("claim", claim["id"], status="superseded", reason="newer claim")

    result = KernelMemoryCuratedMaintenanceService(config, store).run()

    assert result["invalidated"] == 0
    assert store.get_record("curated_memory", curated["id"])["status"] == "active"


def test_admin_runs_curated_maintenance_and_persists_report(tmp_path):
    config, store = _make_store(tmp_path)
    claim = store.ingest_claim(claim_type="fact", content="Babylovegrowth moved to backlog.")
    curated = store.materialize_curated_memory(
        title="Babylovegrowth memory",
        summary="Babylovegrowth moved to backlog.",
        claim_ids=[claim["id"]],
    )
    store.update_record_status("claim", claim["id"], status="superseded", reason="newer claim")

    admin = KernelMemoryAdminService(config)
    result = admin.run_curated_maintenance()

    assert result["invalidated"] == 1
    assert admin.latest_curated_maintenance()["invalidated"] == 1
    assert admin.store.get_record("curated_memory", curated["id"])["status"] == "invalidated"


def test_curated_maintenance_supersedes_active_record_with_active_replacement(tmp_path):
    config, store = _make_store(tmp_path)
    old_curated = store.materialize_curated_memory(
        title="Original quote",
        summary="Old favorite quote.",
    )
    new_curated = store.materialize_curated_memory(
        title="Current quote",
        summary="New favorite quote.",
    )
    store.annotate_lineage(
        "curated_memory",
        old_curated["id"],
        resolved_by=new_curated["id"],
        reason="test_lineage_resolution",
    )

    result = KernelMemoryCuratedMaintenanceService(config, store).run()

    refreshed = store.get_record("curated_memory", old_curated["id"])
    assert result["lineage_resolved"] == 1
    assert refreshed is not None
    assert refreshed["status"] == "superseded"
    assert refreshed["superseded_by"] == new_curated["id"]
