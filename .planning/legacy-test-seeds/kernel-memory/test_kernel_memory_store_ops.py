from __future__ import annotations

from agent.kernel_memory import KernelMemoryConfig, KernelMemoryStore


def _make_store(tmp_path):
    return KernelMemoryStore.from_config(
        KernelMemoryConfig(
            enabled=True,
            root_dir=tmp_path / "kernel",
            namespace="bestie",
        )
    )


def test_merge_entity_rewrites_dependent_references(tmp_path):
    store = _make_store(tmp_path)
    claim = store.ingest_claim(
        claim_type="fact",
        content="Rachel started ukulele lessons with Tomi.",
    )
    duplicate = store.upsert_entity(name="Rachel", entity_type="person", claim_ids=[claim["id"]])
    canonical = store.upsert_entity(
        name="Rachel Canonical",
        entity_type="person",
        claim_ids=[claim["id"]],
        metadata={"source": "manual"},
    )
    relation = store.upsert_relation(
        relation_type="started_activity",
        subject_entity_id=duplicate["id"],
        object_entity_id=canonical["id"],
        claim_ids=[claim["id"]],
    )
    event = store.ingest_event(
        event_type="started_activity",
        title="Rachel started ukulele lessons",
        summary="Rachel started ukulele lessons with Tomi.",
        actor_entity_id=duplicate["id"],
        participant_entity_ids=[duplicate["id"], canonical["id"]],
        counterparty_entity_ids=[duplicate["id"]],
        object_entity_ids=[duplicate["id"]],
        entity_ids=[duplicate["id"], canonical["id"]],
        relation_ids=[relation["id"]],
        claim_ids=[claim["id"]],
    )
    episode = store.ingest_episode(
        title="Rachel learning arc",
        summary="Episode linking Rachel to the new activity.",
        entity_ids=[duplicate["id"]],
        relation_ids=[relation["id"]],
        event_ids=[event["id"]],
        claim_ids=[claim["id"]],
    )
    curated = store.materialize_curated_memory(
        title="Rachel memory",
        summary="Rachel is now tied to the canonical memory object.",
        entity_ids=[duplicate["id"]],
        relation_ids=[relation["id"]],
        event_ids=[event["id"]],
        claim_ids=[claim["id"]],
    )

    result = store.merge_records(
        "entity",
        duplicate["id"],
        canonical["id"],
        reason="duplicate canonicalization",
    )

    assert result["status"] == "merged"

    merged_relation = store.get_record("relation", relation["id"])
    assert merged_relation is not None
    assert merged_relation["subject_entity_id"] == canonical["id"]
    assert merged_relation["object_entity_id"] == canonical["id"]

    merged_event = store.get_record("event", event["id"])
    assert merged_event is not None
    assert merged_event["actor_entity_id"] == canonical["id"]
    assert merged_event["entity_ids"] == [canonical["id"]]
    assert merged_event["participant_entity_ids"] == [canonical["id"]]
    assert merged_event["counterparty_entity_ids"] == [canonical["id"]]
    assert merged_event["object_entity_ids"] == [canonical["id"]]

    merged_episode = store.get_record("episode", episode["id"])
    assert merged_episode is not None
    assert merged_episode["entity_ids"] == [canonical["id"]]

    merged_curated = store.get_record("curated_memory", curated["id"])
    assert merged_curated is not None
    assert merged_curated["entity_ids"] == [canonical["id"]]


def test_merge_claim_rewrites_claim_id_dependencies(tmp_path):
    store = _make_store(tmp_path)
    duplicate = store.ingest_claim(
        claim_type="fact",
        content="Laura prefers concise summaries.",
    )
    canonical = store.ingest_claim(
        claim_type="fact",
        content="Laura prefers concise summaries.",
        metadata={"source": "manual"},
        source_version="v2",
    )
    entity = store.upsert_entity(
        name="Laura",
        entity_type="person",
        claim_ids=[duplicate["id"]],
    )
    relation = store.upsert_relation(
        relation_type="prefers",
        subject_entity_id=entity["id"],
        object_entity_id=entity["id"],
        claim_ids=[duplicate["id"]],
    )
    event = store.ingest_event(
        event_type="preference_update",
        title="Laura prefers concise summaries",
        summary="Preference claim points at Laura.",
        claim_ids=[duplicate["id"]],
        entity_ids=[entity["id"]],
        relation_ids=[relation["id"]],
    )
    episode = store.ingest_episode(
        title="Preference episode",
        summary="Episode tracks the concise preference.",
        claim_ids=[duplicate["id"]],
        entity_ids=[entity["id"]],
        relation_ids=[relation["id"]],
        event_ids=[event["id"]],
    )
    curated = store.materialize_curated_memory(
        title="Preference memory",
        summary="Laura likes concise summaries.",
        claim_ids=[duplicate["id"]],
        entity_ids=[entity["id"]],
        relation_ids=[relation["id"]],
        event_ids=[event["id"]],
    )

    result = store.merge_records(
        "claim",
        duplicate["id"],
        canonical["id"],
        reason="duplicate canonicalization",
    )

    assert result["status"] == "merged"
    assert store.get_record("entity", entity["id"])["claim_ids"] == [canonical["id"]]
    assert store.get_record("relation", relation["id"])["claim_ids"] == [canonical["id"]]
    assert store.get_record("event", event["id"])["claim_ids"] == [canonical["id"]]
    assert store.get_record("episode", episode["id"])["claim_ids"] == [canonical["id"]]
    assert store.get_record("curated_memory", curated["id"])["claim_ids"] == [canonical["id"]]


def test_merge_curated_memory_rewrites_association_endpoints(tmp_path):
    store = _make_store(tmp_path)
    left = store.materialize_curated_memory(
        title="Original",
        summary="Original curated record.",
    )
    right = store.materialize_curated_memory(
        title="Canonical",
        summary="Canonical curated record.",
    )
    peer = store.materialize_curated_memory(
        title="Peer",
        summary="Peer curated record.",
    )
    association = store.upsert_association(
        left_object_kind="curated_memory",
        left_object_id=left["id"],
        right_object_kind="curated_memory",
        right_object_id=peer["id"],
        association_origin="answer_pack_coaccess",
        successful=True,
    )

    result = store.merge_records(
        "curated_memory",
        left["id"],
        right["id"],
        reason="duplicate canonicalization",
    )

    assert result["status"] == "merged"
    merged_association = store.get_record("association", association["id"])
    assert merged_association is not None
    endpoints = {
        (merged_association["left_object_kind"], merged_association["left_object_id"]),
        (merged_association["right_object_kind"], merged_association["right_object_id"]),
    }
    assert ("curated_memory", right["id"]) in endpoints
    assert ("curated_memory", peer["id"]) in endpoints


def test_merge_claim_rewrites_same_kind_lineage_references(tmp_path):
    store = _make_store(tmp_path)
    source = store.ingest_claim(
        claim_type="fact",
        content="Old deployment rule.",
    )
    target = store.ingest_claim(
        claim_type="fact",
        content="Old deployment rule.",
        metadata={"source": "manual"},
        source_version="v2",
    )
    revision = store.ingest_claim(
        claim_type="fact",
        content="New deployment rule.",
        metadata={"conflict_signal": "correction"},
    )
    store.annotate_lineage(
        "claim",
        revision["id"],
        review_of=source["id"],
        revises=source["id"],
        reason="test_lineage",
    )
    store.annotate_lineage(
        "claim",
        source["id"],
        resolved_by=revision["id"],
        reason="test_lineage",
    )

    result = store.merge_records(
        "claim",
        source["id"],
        target["id"],
        reason="duplicate canonicalization",
    )

    assert result["status"] == "merged"
    merged_revision = store.get_record("claim", revision["id"])
    assert merged_revision is not None
    assert merged_revision["review_of"] == target["id"]
    assert merged_revision["revises"] == target["id"]
