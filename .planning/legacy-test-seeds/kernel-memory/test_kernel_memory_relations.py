from __future__ import annotations

from agent.kernel_memory import KernelMemoryConfig, KernelMemoryStore
from agent.kernel_memory_relations import RelationLifecycleService


def _build_relation_fixture(store: KernelMemoryStore):
    resource = store.ingest_resource(
        resource_type="note",
        title="Mars mission notes",
        content="NASA plans a Mars mission with SpaceX launch support.",
    )
    extract = store.ingest_extract(
        resource_id=resource["id"],
        extract_type="paragraph",
        sequence=0,
        content="NASA may collaborate with SpaceX on a future Mars mission.",
    )
    claim_a = store.ingest_claim(
        claim_type="fact",
        content="NASA may collaborate with SpaceX on a future Mars mission.",
        extract_ids=[extract["id"]],
        resource_ids=[resource["id"]],
    )
    claim_b = store.ingest_claim(
        claim_type="fact",
        content="SpaceX launch support is relevant to NASA Mars planning.",
        extract_ids=[extract["id"]],
        resource_ids=[resource["id"]],
    )
    nasa = store.upsert_entity(
        name="NASA",
        entity_type="organization",
        claim_ids=[claim_a["id"], claim_b["id"]],
        extract_ids=[extract["id"]],
        resource_ids=[resource["id"]],
    )
    spacex = store.upsert_entity(
        name="SpaceX",
        entity_type="organization",
        claim_ids=[claim_a["id"], claim_b["id"]],
        extract_ids=[extract["id"]],
        resource_ids=[resource["id"]],
    )
    return nasa, spacex, claim_a, claim_b


def test_relation_observations_promote_and_inspect_support_chain(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(
            enabled=True,
            root_dir=tmp_path / "kernel",
            namespace="bestie",
            graph_relation_promote_min_observations=2,
            graph_relation_promote_min_confidence=0.6,
        )
    )
    nasa, spacex, claim_a, claim_b = _build_relation_fixture(store)

    relation = store.upsert_relation(
        relation_type="collaborates_with",
        subject_entity_id=nasa["id"],
        object_entity_id=spacex["id"],
        claim_ids=[claim_a["id"]],
        confidence=0.8,
    )
    assert relation["lifecycle"]["state"] == "candidate"

    relation = store.upsert_relation(
        relation_type="collaborates_with",
        subject_entity_id=nasa["id"],
        object_entity_id=spacex["id"],
        claim_ids=[claim_b["id"]],
        confidence=0.8,
    )

    assert relation["lifecycle"]["state"] == "promoted"
    inspected = store.inspect_record("relation", relation["id"])
    assert inspected["related"]["subject_entity"]["name"] == "NASA"
    assert inspected["related"]["object_entity"]["name"] == "SpaceX"
    assert len(inspected["related"]["claims"]) == 2


def test_relation_maintenance_decays_stale_promoted_relations(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        graph_relation_promote_min_observations=1,
        graph_relation_promote_min_confidence=0.5,
        graph_relation_decay_after_seconds=1,
        graph_relation_decay_confidence_floor=0.3,
    )
    store = KernelMemoryStore.from_config(config)
    nasa, spacex, claim_a, _ = _build_relation_fixture(store)

    relation = store.upsert_relation(
        relation_type="collaborates_with",
        subject_entity_id=nasa["id"],
        object_entity_id=spacex["id"],
        claim_ids=[claim_a["id"]],
        confidence=0.9,
        observed_at="2025-01-01T00:00:00+00:00",
    )
    assert relation["lifecycle"]["state"] == "promoted"

    service = RelationLifecycleService(config, store)
    result = service.run_maintenance(now="2026-01-01T00:00:00+00:00")

    updated = store.get_record("relation", relation["id"])
    assert result["decayed"] == 1
    assert updated is not None
    assert updated["lifecycle"]["state"] == "decayed"
    assert updated["confidence"] >= 0.3


def test_graph_route_can_surface_promoted_relations(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(
            enabled=True,
            root_dir=tmp_path / "kernel",
            namespace="bestie",
            graph_relation_promote_min_observations=1,
            graph_relation_promote_min_confidence=0.5,
            retrieval_policy_order=["graph"],
        )
    )
    nasa, spacex, claim_a, _ = _build_relation_fixture(store)
    store.upsert_relation(
        relation_type="collaborates_with",
        subject_entity_id=nasa["id"],
        object_entity_id=spacex["id"],
        claim_ids=[claim_a["id"]],
        confidence=0.9,
    )

    result = store.retrieve_context_by_policy(
        "How do NASA and SpaceX collaborate?",
        max_records=3,
        max_chars=800,
        route_order=["graph"],
    )

    assert result["routes"] == ["graph"]
    assert "Relation: NASA -[collaborates_with]-> SpaceX" in result["text"]
