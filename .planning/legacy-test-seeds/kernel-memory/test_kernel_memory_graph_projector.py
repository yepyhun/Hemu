from __future__ import annotations

import json

from agent.kernel_memory import KernelMemoryConfig, KernelMemoryStore
from agent.kernel_memory_graph_projector import KernelMemoryGraphProjector
from agent.kernel_memory_graph_store import KernelMemoryGraphStore


def test_kernel_memory_graph_projector_builds_snapshot(tmp_path):
    config = KernelMemoryConfig.from_dict(
        {
            "enabled": True,
            "root_dir": str(tmp_path / "kernel-memory"),
            "namespace": "bestie",
            "graph_projection_enabled": True,
            "graph_projection_backend": "neo4j",
            "graph_projection_max_nodes_per_run": 20,
            "graph_projection_max_edges_per_run": 20,
            "neo4j_uri": "bolt://localhost:7687",
        }
    )
    store = KernelMemoryStore.from_config(config)
    resource = store.ingest_resource(
        resource_type="note",
        title="Mission plan",
        content="Earth transfers to Mars.",
    )
    extract = store.ingest_extract(
        resource_id=resource["id"],
        extract_type="quote",
        content="Earth transfers to Mars.",
    )
    claim = store.ingest_claim(
        claim_type="fact",
        content="Earth transfers to Mars.",
        extract_ids=[extract["id"]],
    )
    earth = store.upsert_entity(name="Earth", entity_type="planet", claim_ids=[claim["id"]])
    mars = store.upsert_entity(name="Mars", entity_type="planet", claim_ids=[claim["id"]])
    store.upsert_relation(
        relation_type="transfers_to",
        subject_entity_id=earth["id"],
        object_entity_id=mars["id"],
        claim_ids=[claim["id"]],
        confidence=0.9,
    )
    episode = store.ingest_episode(
        title="Transfer planning window",
        summary="Earth to Mars transfer planning window.",
        claim_ids=[claim["id"]],
        entity_ids=[earth["id"], mars["id"]],
    )
    store.materialize_curated_memory(
        title="Mission summary",
        summary="Earth transfers to Mars.",
        claim_ids=[claim["id"]],
        episode_id=episode["id"],
    )

    projector = KernelMemoryGraphProjector(config, store, KernelMemoryGraphStore(config))
    result = projector.run()

    assert result["projection"]["node_count"] >= 6
    assert result["projection"]["edge_count"] >= 5
    assert result["graph_store"]["status"] == "skipped"
    assert result["graph_store"]["reason"] == "neo4j_password_missing"

    snapshot_path = config.root_dir / "state" / "graph_projection" / "latest_snapshot.json"
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    assert snapshot["projection"]["node_count"] == result["projection"]["node_count"]
    assert snapshot["graph_store"]["reason"] == "neo4j_password_missing"


def test_kernel_memory_graph_store_reports_disabled_when_projection_off(tmp_path):
    config = KernelMemoryConfig.from_dict(
        {
            "enabled": True,
            "root_dir": str(tmp_path / "kernel-memory"),
            "namespace": "bestie",
            "graph_projection_enabled": False,
        }
    )

    health = KernelMemoryGraphStore(config).health()

    assert health["status"] == "disabled"
    assert health["reason"] == "graph_projection_disabled"


def test_kernel_memory_graph_projector_ignores_future_records_in_current_snapshot(tmp_path):
    config = KernelMemoryConfig.from_dict(
        {
            "enabled": True,
            "root_dir": str(tmp_path / "kernel-memory"),
            "namespace": "bestie",
            "graph_projection_enabled": True,
            "neo4j_uri": "bolt://localhost:7687",
        }
    )
    store = KernelMemoryStore.from_config(config)
    store.materialize_curated_memory(
        title="Future plan",
        summary="This should not appear yet.",
        valid_from="2099-01-01T00:00:00+00:00",
    )

    projection = KernelMemoryGraphProjector(config, store, KernelMemoryGraphStore(config)).build_projection()

    assert not any(node["display"] == "Future plan" for node in projection["nodes"])
