from __future__ import annotations

from agent.kernel_memory import KernelMemoryConfig, KernelMemoryStore
from agent.kernel_memory_graph_extraction import KernelMemoryGraphExtractionService
from agent.kernel_memory_relations import RelationLifecycleService


def test_graph_extraction_creates_source_backed_relations_with_quality_metadata(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        graph_relation_promote_min_observations=1,
        graph_relation_promote_min_confidence=0.5,
    )
    store = KernelMemoryStore.from_config(config)
    document = store.ingest_document(
        document_type="note",
        title="Orbital note",
        content="Earth transfers to Mars during orbital planning.",
    )
    claim = store.ingest_claim(
        claim_type="fact",
        content="Earth transfers to Mars during orbital planning.",
        resource_ids=[document["resource"]["id"]],
        extract_ids=document["extract_ids"][:1],
    )

    service = KernelMemoryGraphExtractionService(config, store)
    result = service.run(max_claims=10)
    relations = RelationLifecycleService(config, store).list_relations()

    assert result["created_relations"] >= 1
    relation = next(item for item in relations if claim["id"] in item.get("claim_ids", []))
    assert relation["metadata"]["source_type"] == "direct-source-supported"
    assert relation["lifecycle"]["confidence_tier"] in {"medium", "high"}
    assert relation["lifecycle"]["edge_strength"] in {"strong", "weak"}


def test_graph_extraction_can_create_repeated_cooccurrence_edges(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
    )
    store = KernelMemoryStore.from_config(config)
    store.ingest_claim(
        claim_type="fact",
        content="Earth and Mars appear together in orbital planning notes.",
    )

    service = KernelMemoryGraphExtractionService(config, store)
    result = service.run(max_claims=10)
    relations = RelationLifecycleService(config, store).list_relations(include_inactive=True)

    assert result["created_relations"] >= 1
    assert any(
        relation.get("relation_type") == "cooccurs_with"
        and (relation.get("metadata") or {}).get("source_type") == "model-inferred"
        for relation in relations
    )


def test_graph_extraction_can_create_contradiction_and_supersession_edges(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        graph_relation_promote_min_observations=1,
        graph_relation_promote_min_confidence=0.5,
    )
    store = KernelMemoryStore.from_config(config)
    store.ingest_claim(
        claim_type="fact",
        content="Old Policy conflicts with New Policy. Safe Rule replaces Legacy Rule.",
    )

    service = KernelMemoryGraphExtractionService(config, store)
    service.run(max_claims=10)
    relations = RelationLifecycleService(config, store).list_relations(include_inactive=True)
    relation_types = {relation.get("relation_type") for relation in relations}

    assert "contradicts" in relation_types
    assert "supersedes" in relation_types
