from __future__ import annotations

from copy import deepcopy

from agent.kernel_memory import KernelMemoryConfig, KernelMemoryStore
from agent.kernel_memory_admin import KernelMemoryAdminService
from agent.kernel_memory_canonicalization import KernelMemoryCanonicalizationService


def _make_store(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
    )
    return config, KernelMemoryStore.from_config(config)


def test_canonicalization_service_merges_claim_to_curated_duplicate_chain(tmp_path):
    config, store = _make_store(tmp_path)
    claim_a = store.ingest_claim(
        claim_type="fact",
        content="Tomi studies orbital mechanics.",
        source_version="v1",
    )
    claim_b = store.ingest_claim(
        claim_type="fact",
        content="Tomi studies orbital mechanics.",
        source_version="v2",
        metadata={"source": "duplicate"},
    )
    subject = store.upsert_entity(name="Tomi", entity_type="person", claim_ids=[claim_a["id"], claim_b["id"]])
    topic = store.upsert_entity(name="Orbital Mechanics", entity_type="topic", claim_ids=[claim_a["id"], claim_b["id"]])

    relation_a = store.upsert_relation(
        relation_type="studies",
        subject_entity_id=subject["id"],
        object_entity_id=topic["id"],
        claim_ids=[claim_a["id"]],
    )
    relation_b = deepcopy(relation_a)
    relation_b["id"] = "rel-duplicate"
    relation_b["content_hash"] = "rel-duplicate-hash"
    relation_b["claim_ids"] = [claim_b["id"]]
    store._records["relation"][relation_b["id"]] = relation_b
    store._hash_index["relation"][relation_b["content_hash"]] = relation_b["id"]
    store._persist_derived_kind("relation")
    store._persist_hash_index()
    event_a = store.ingest_event(
        event_type="started_activity",
        title="Tomi studies orbital mechanics",
        summary="Tomi is studying orbital mechanics.",
        claim_ids=[claim_a["id"]],
        entity_ids=[subject["id"], topic["id"]],
        relation_ids=[relation_a["id"]],
    )
    event_b = deepcopy(event_a)
    event_b["id"] = "evt-duplicate"
    event_b["content_hash"] = "evt-duplicate-hash"
    event_b["claim_ids"] = [claim_b["id"]]
    event_b["relation_ids"] = [relation_b["id"]]
    store._records["event"][event_b["id"]] = event_b
    store._hash_index["event"][event_b["content_hash"]] = event_b["id"]
    store._persist_derived_kind("event")
    store._persist_hash_index()
    episode_a = store.ingest_episode(
        title="Orbital study arc",
        summary="Episode for studying orbital mechanics.",
        claim_ids=[claim_a["id"]],
        entity_ids=[subject["id"], topic["id"]],
        relation_ids=[relation_a["id"]],
        event_ids=[event_a["id"]],
    )
    episode_b = deepcopy(episode_a)
    episode_b["id"] = "eps-duplicate"
    episode_b["content_hash"] = "eps-duplicate-hash"
    episode_b["claim_ids"] = [claim_b["id"]]
    episode_b["relation_ids"] = [relation_b["id"]]
    episode_b["event_ids"] = [event_b["id"]]
    store._records["episode"][episode_b["id"]] = episode_b
    store._hash_index["episode"][episode_b["content_hash"]] = episode_b["id"]
    store._persist_derived_kind("episode")
    store._persist_hash_index()
    curated_a = store.materialize_curated_memory(
        title="Orbital study memory",
        summary="Tomi is studying orbital mechanics.",
        claim_ids=[claim_a["id"]],
        entity_ids=[subject["id"], topic["id"]],
        relation_ids=[relation_a["id"]],
        event_ids=[event_a["id"]],
        episode_id=episode_a["id"],
    )
    curated_b = deepcopy(curated_a)
    curated_b["id"] = "cur-duplicate"
    curated_b["content_hash"] = "cur-duplicate-hash"
    curated_b["claim_ids"] = [claim_b["id"]]
    curated_b["relation_ids"] = [relation_b["id"]]
    curated_b["event_ids"] = [event_b["id"]]
    curated_b["episode_id"] = episode_b["id"]
    store._records["curated_memory"][curated_b["id"]] = curated_b
    store._hash_index["curated_memory"][curated_b["content_hash"]] = curated_b["id"]
    store._persist_derived_kind("curated_memory")
    store._persist_hash_index()

    result = KernelMemoryCanonicalizationService(config, store).run()

    assert result["status"] == "ok"
    assert result["merged_by_kind"]["claim"] == 1
    assert result["merged_by_kind"]["relation"] == 1
    assert result["merged_by_kind"]["event"] == 1
    assert result["merged_by_kind"]["episode"] == 1
    assert result["merged_by_kind"]["curated_memory"] == 1

    active_claims = [record for record in store.list_records("claim") if record["status"] == "active"]
    active_relations = [record for record in store.list_records("relation") if record["status"] == "active"]
    active_events = [record for record in store.list_records("event") if record["status"] == "active"]
    active_episodes = [record for record in store.list_records("episode") if record["status"] == "active"]
    active_curated = [record for record in store.list_records("curated_memory") if record["status"] == "active"]

    assert len(active_claims) == 1
    assert len(active_relations) == 1
    assert len(active_events) == 1
    assert len(active_episodes) == 1
    assert len(active_curated) == 1

    canonical_claim = active_claims[0]
    canonical_relation = active_relations[0]
    canonical_event = active_events[0]
    canonical_episode = active_episodes[0]
    canonical_curated = active_curated[0]

    assert canonical_relation["claim_ids"] == [canonical_claim["id"]]
    assert canonical_event["claim_ids"] == [canonical_claim["id"]]
    assert canonical_event["relation_ids"] == [canonical_relation["id"]]
    assert canonical_episode["claim_ids"] == [canonical_claim["id"]]
    assert canonical_episode["relation_ids"] == [canonical_relation["id"]]
    assert canonical_episode["event_ids"] == [canonical_event["id"]]
    assert canonical_curated["claim_ids"] == [canonical_claim["id"]]
    assert canonical_curated["relation_ids"] == [canonical_relation["id"]]
    assert canonical_curated["event_ids"] == [canonical_event["id"]]
    assert canonical_curated["episode_id"] == canonical_episode["id"]


def test_canonicalization_service_merges_duplicate_entity_cluster(tmp_path):
    config, store = _make_store(tmp_path)
    claim = store.ingest_claim(
        claim_type="fact",
        content="Laura and Rachel are collaborators.",
    )
    canonical = store.upsert_entity(name="Rachel", entity_type="person", claim_ids=[claim["id"]])
    duplicate = deepcopy(canonical)
    duplicate["id"] = "ent-duplicate"
    duplicate["content_hash"] = "hash-duplicate"
    duplicate["metadata"] = {"seeded_duplicate": True}
    store._records["entity"][duplicate["id"]] = duplicate
    store._hash_index["entity"][duplicate["content_hash"]] = duplicate["id"]
    store._persist_derived_kind("entity")
    store._persist_hash_index()

    relation = store.upsert_relation(
        relation_type="collaborates_with",
        subject_entity_id=duplicate["id"],
        object_entity_id=canonical["id"],
        claim_ids=[claim["id"]],
    )
    event = store.ingest_event(
        event_type="collaboration",
        title="Rachel collaborates",
        summary="Rachel collaborates with Laura.",
        actor_entity_id=duplicate["id"],
        entity_ids=[duplicate["id"], canonical["id"]],
        claim_ids=[claim["id"]],
        relation_ids=[relation["id"]],
    )

    result = KernelMemoryCanonicalizationService(config, store).run()

    assert result["merged_by_kind"]["entity"] == 1
    active_entities = [record for record in store.list_records("entity") if record["status"] == "active"]
    assert len(active_entities) == 1
    canonical_id = active_entities[0]["id"]
    merged_relation = store.get_record("relation", relation["id"])
    merged_event = store.get_record("event", event["id"])
    assert merged_relation["subject_entity_id"] == canonical_id
    assert merged_relation["object_entity_id"] == canonical_id
    assert merged_event["actor_entity_id"] == canonical_id
    assert merged_event["entity_ids"] == [canonical_id]


def test_admin_runs_canonicalization_and_persists_latest_report(tmp_path):
    config, store = _make_store(tmp_path)
    first = store.ingest_claim(claim_type="fact", content="BabyLoveGrowth is worth revisiting.", source_version="v1")
    store.ingest_claim(claim_type="fact", content="BabyLoveGrowth is worth revisiting.", source_version="v2")

    admin = KernelMemoryAdminService(config)
    result = admin.run_canonicalization_maintenance()

    assert result["status"] == "ok"
    assert result["merged_by_kind"]["claim"] == 1
    latest = admin.latest_canonicalization()
    assert latest["merged_by_kind"]["claim"] == 1
