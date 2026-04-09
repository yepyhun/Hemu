from __future__ import annotations

from pathlib import Path

from agent.kernel_memory import KernelMemoryConfig, KernelMemoryStore
from agent.kernel_memory_backup import KernelMemoryBackupService


def test_backup_service_creates_verifiable_snapshot_and_restores_runtime(tmp_path):
    config = KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel", namespace="bestie")
    store = KernelMemoryStore.from_config(config)
    store.materialize_curated_memory(
        title="Restorable memory",
        summary="Kernel memory backups should restore the durable runtime.",
    )
    marker = config.root_dir / "state" / "ops" / "marker.txt"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("before\n", encoding="utf-8")

    service = KernelMemoryBackupService(config)
    backup = service.create_backup(label="baseline")
    marker.write_text("after\n", encoding="utf-8")

    restored = service.restore_backup(str(backup["backup_path"]))

    assert backup["verification_ok"] is True
    assert restored["status"] == "restored"
    assert marker.read_text(encoding="utf-8") == "before\n"


def test_backup_service_detects_manifest_mismatch(tmp_path):
    config = KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel", namespace="bestie")
    marker = config.root_dir / "state" / "ops" / "marker.txt"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("original\n", encoding="utf-8")
    service = KernelMemoryBackupService(config)

    backup = service.create_backup(label="corrupt-me")
    backup_marker = (
        Path(str(backup["backup_path"])) / "data" / "state" / "ops" / "marker.txt"
    )
    backup_marker.write_text("corrupted\n", encoding="utf-8")

    verification = service.verify_backup(str(backup["backup_path"]))

    assert verification["verification_ok"] is False
    assert "state/ops/marker.txt" in verification["mismatched_files"]


def test_backup_service_tracks_backup_first_migrations(tmp_path):
    config = KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel", namespace="bestie")
    store = KernelMemoryStore.from_config(config)
    store.materialize_curated_memory(
        title="Migration memory",
        summary="Backup-first migration discipline must leave a journal trail.",
    )
    service = KernelMemoryBackupService(config)

    started = service.begin_migration(name="layout-v2", summary="Repack runtime layout")
    completed = service.complete_migration(started["migration_id"], notes="Finished successfully")
    entries = service.list_migrations(limit=5)

    assert started["status"] == "in_progress"
    assert completed["status"] == "completed"
    assert entries and entries[0]["migration_id"] == started["migration_id"]


def test_backup_service_restores_graph_projection_snapshot(tmp_path):
    config = KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel", namespace="bestie")
    snapshot_path = config.root_dir / "state" / "graph_projection" / "latest_snapshot.json"
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text('{"status":"ok","projection":{"node_count":3,"edge_count":2}}', encoding="utf-8")
    service = KernelMemoryBackupService(config)

    backup = service.create_backup(label="graph-snapshot")
    snapshot_path.write_text('{"status":"mutated"}', encoding="utf-8")

    restored = service.restore_backup(str(backup["backup_path"]))

    assert restored["status"] == "restored"
    assert '"node_count":3' in snapshot_path.read_text(encoding="utf-8")
