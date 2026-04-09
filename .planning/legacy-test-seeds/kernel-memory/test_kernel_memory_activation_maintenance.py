from __future__ import annotations

from agent.kernel_memory import KernelMemoryConfig, KernelMemoryStore
from agent.kernel_memory_activation_maintenance import (
    KernelMemoryActivationMaintenanceService,
)
from agent.kernel_memory_admin import KernelMemoryAdminService


def test_activation_maintenance_archives_stale_provisional_claim(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        activation_maintenance_enabled=True,
        activation_maintenance_provisional_grace_days=7,
    )
    store = KernelMemoryStore.from_config(config)
    claim = store.ingest_claim(
        claim_type="fact",
        content="A low-support one-off memory should not stay hot forever.",
        confidence=0.61,
    )
    assert claim["activation_state"] == "provisional"
    store._apply_overlay(
        "claim",
        claim["id"],
        {
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:00+00:00",
        },
    )
    store._persist_derived_kind("claim")

    service = KernelMemoryActivationMaintenanceService(config, store)
    result = service.run(now="2026-02-01T00:00:00+00:00")

    updated = store.get_record("claim", claim["id"])
    assert result["archived"] == 1
    assert updated is not None
    assert updated["status"] == "archived"
    assert updated["invalidated_at"]


def test_activation_maintenance_recomputes_hot_record_state(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        activation_maintenance_enabled=True,
    )
    store = KernelMemoryStore.from_config(config)
    claim = store.ingest_claim(
        claim_type="preference",
        content="Always keep answers direct and exact.",
        metadata={"explicit_user_memory": True},
        confidence=0.92,
    )
    store._apply_overlay(
        "claim",
        claim["id"],
        {
            "derivation_count": 4,
            "retrieval_count": 6,
            "successful_retrieval_count": 5,
            "last_retrieved_at": "2026-02-01T00:00:00+00:00",
            "last_successful_retrieved_at": "2026-02-01T00:00:00+00:00",
            "activation_state": "active_warm",
            "activation_score": 0.42,
        },
    )
    store._persist_derived_kind("claim")

    service = KernelMemoryActivationMaintenanceService(config, store)
    result = service.run(now="2026-02-02T00:00:00+00:00")

    updated = store.get_record("claim", claim["id"])
    assert result["activation_updates"] == 1
    assert updated is not None
    assert updated["activation_state"] == "active_hot"
    assert updated["activation_score"] > 0.82


def test_admin_service_exposes_activation_maintenance(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        activation_maintenance_enabled=True,
    )
    admin = KernelMemoryAdminService(config)

    result = admin.run_activation_maintenance()

    assert result["status"] == "ok"
    assert "evaluated_at" in result


def test_activation_maintenance_demotes_stale_low_value_record(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        activation_maintenance_enabled=True,
        activation_maintenance_stale_after_days=30,
    )
    store = KernelMemoryStore.from_config(config)
    claim = store.ingest_claim(
        claim_type="fact",
        content="A noisy memory kept surfacing but never helped.",
        confidence=0.89,
    )
    store._apply_overlay(
        "claim",
        claim["id"],
        {
            "retrieval_count": 6,
            "successful_retrieval_count": 1,
            "used_in_answer_count": 0,
            "last_retrieved_at": "2026-01-01T00:00:00+00:00",
            "last_successful_retrieved_at": "2026-01-01T00:00:00+00:00",
            "activation_state": "active_hot",
            "activation_score": 0.93,
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:00+00:00",
        },
    )
    store._persist_derived_kind("claim")

    result = KernelMemoryActivationMaintenanceService(config, store).run(now="2026-03-01T00:00:00+00:00")

    updated = store.get_record("claim", claim["id"])
    assert result["activation_updates"] == 1
    assert updated is not None
    assert updated["activation_state"] in {"fading", "dormant"}
    assert updated["activation_score"] <= 0.34


def test_activation_maintenance_resolves_active_record_from_lineage(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        activation_maintenance_enabled=True,
    )
    store = KernelMemoryStore.from_config(config)
    old_claim = store.ingest_claim(
        claim_type="fact",
        content="Old operational rule.",
        confidence=0.9,
    )
    new_claim = store.ingest_claim(
        claim_type="fact",
        content="New operational rule.",
        confidence=0.95,
    )
    store.annotate_lineage(
        "claim",
        old_claim["id"],
        resolved_by=new_claim["id"],
        reason="test_lineage_resolution",
    )

    result = KernelMemoryActivationMaintenanceService(config, store).run()

    updated = store.get_record("claim", old_claim["id"])
    assert result["lineage_resolved"] == 1
    assert updated is not None
    assert updated["status"] == "resolved"
    assert updated["invalidated_at"]
