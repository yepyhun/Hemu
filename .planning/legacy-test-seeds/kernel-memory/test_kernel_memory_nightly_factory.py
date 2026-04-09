from __future__ import annotations

from agent.kernel_memory import KernelMemoryConfig, KernelMemoryStore
from agent.kernel_memory_nightly_factory import KernelMemoryNightlyArtifactService
from agent.kernel_memory_quality import KernelMemoryQualityStore
from agent.kernel_memory_relations import RelationLifecycleService


def test_nightly_factory_builds_reranking_artifact(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        graph_relation_promote_min_observations=1,
        graph_relation_promote_min_confidence=0.5,
    )
    store = KernelMemoryStore.from_config(config)
    store.materialize_curated_memory(
        title="Nightly hot memory",
        summary="Nightly artifacts should prioritize strong curated memories.",
        metadata={"memory_class": "curated_knowledge"},
    )
    claim = store.ingest_claim(
        claim_type="fact",
        content="Earth transfers to Mars.",
    )
    earth = store.upsert_entity(name="Earth", entity_type="planet", claim_ids=[claim["id"]])
    mars = store.upsert_entity(name="Mars", entity_type="planet", claim_ids=[claim["id"]])
    store.upsert_relation(
        relation_type="transfers_to",
        subject_entity_id=earth["id"],
        object_entity_id=mars["id"],
        claim_ids=[claim["id"]],
        source_type="direct-source-supported",
        confidence=0.9,
    )

    service = KernelMemoryNightlyArtifactService(
        config,
        store,
        KernelMemoryQualityStore(config),
        RelationLifecycleService(config, store),
    )
    artifact = service.build_reranking_artifact()

    assert artifact["summary"]["curated_hotset_count"] >= 1
    assert artifact["summary"]["strong_relation_hotset_count"] >= 1


def test_nightly_factory_prefers_high_usefulness_curated_memory(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        graph_relation_promote_min_observations=1,
        graph_relation_promote_min_confidence=0.5,
    )
    store = KernelMemoryStore.from_config(config)
    weak = store.materialize_curated_memory(
        title="Weak memory",
        summary="A generic scratch note.",
        metadata={"memory_class": "curated_knowledge"},
    )
    strong = store.materialize_curated_memory(
        title="Strong memory",
        summary="A stable operational rule with verified support.",
        metadata={
            "memory_class": "curated_knowledge",
            "verified": True,
            "verification_evidence": ["tool:memory"],
        },
    )
    store.record_answer_usefulness([strong])
    store.record_answer_usefulness([strong])

    service = KernelMemoryNightlyArtifactService(
        config,
        store,
        KernelMemoryQualityStore(config),
        RelationLifecycleService(config, store),
    )
    artifact = service.build_reranking_artifact()

    assert artifact["curated_hotset"][0]["id"] == strong["id"]
    assert artifact["curated_hotset"][0]["used_in_answer_count"] >= 2
    assert artifact["curated_hotset"][0]["quality_tier"] == "high"
    assert artifact["curated_hotset"][0]["usefulness_ratio"] > 0.0
    assert artifact["curated_hotset"][0]["id"] != weak["id"] or len(artifact["curated_hotset"]) == 1


def test_nightly_factory_carries_hard_negative_summary(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        graph_relation_promote_min_observations=1,
        graph_relation_promote_min_confidence=0.5,
    )
    store = KernelMemoryStore.from_config(config)
    quality = KernelMemoryQualityStore(config)
    quality.append_run(
        run_type="hard_negative_retrieval",
        payload={
            "query_hash": "abc",
            "routes": ["graph"],
            "answer_warnings": ["insufficient_grounding"],
            "missing_facets": ["answer_anchor"],
        },
    )

    service = KernelMemoryNightlyArtifactService(
        config,
        store,
        quality,
        RelationLifecycleService(config, store),
    )
    artifact = service.build_reranking_artifact()

    summary = artifact["quality_snapshot"]["hard_negative_summary"]
    assert summary["sample_size"] == 1
    assert summary["missing_facet_counts"]["answer_anchor"] == 1
    assert summary["route_counts"]["graph"] == 1
