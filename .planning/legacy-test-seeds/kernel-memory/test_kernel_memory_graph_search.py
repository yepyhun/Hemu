from __future__ import annotations

from agent.kernel_memory import KernelMemoryConfig, KernelMemoryStore
from agent.kernel_memory_graph_search import KernelMemoryGraphSearch


def test_graph_search_prefers_source_backed_relation_neighbors(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        graph_relation_promote_min_observations=1,
        graph_relation_promote_min_confidence=0.5,
    )
    store = KernelMemoryStore.from_config(config)
    claim = store.ingest_claim(
        claim_type="fact",
        content="Earth transfers to Mars using a Hohmann transfer.",
    )
    earth = store.upsert_entity(name="Earth", entity_type="planet", claim_ids=[claim["id"]])
    mars = store.upsert_entity(name="Mars", entity_type="planet", claim_ids=[claim["id"]])
    hohmann = store.upsert_entity(name="Hohmann transfer", entity_type="concept", claim_ids=[claim["id"]])
    store.upsert_relation(
        relation_type="transfers_to",
        subject_entity_id=earth["id"],
        object_entity_id=mars["id"],
        claim_ids=[claim["id"]],
        confidence=0.9,
        source_type="direct-source-supported",
    )
    store.upsert_relation(
        relation_type="uses",
        subject_entity_id=earth["id"],
        object_entity_id=hohmann["id"],
        claim_ids=[claim["id"]],
        confidence=0.8,
        source_type="direct-source-supported",
    )

    ranked = KernelMemoryGraphSearch(store).rank(
        "How does Earth transfer to Mars?",
        max_records=4,
    )

    assert ranked
    assert ranked[0]["kind"] in {"relation", "entity"}
    assert any(record["kind"] == "relation" for record in ranked[:2])


def test_graph_search_is_bounded_by_requested_max_records(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        graph_relation_promote_min_observations=1,
        graph_relation_promote_min_confidence=0.5,
    )
    store = KernelMemoryStore.from_config(config)
    claim = store.ingest_claim(claim_type="fact", content="Alpha connects to Beta and Gamma.")
    alpha = store.upsert_entity(name="Alpha", entity_type="node", claim_ids=[claim["id"]])
    beta = store.upsert_entity(name="Beta", entity_type="node", claim_ids=[claim["id"]])
    gamma = store.upsert_entity(name="Gamma", entity_type="node", claim_ids=[claim["id"]])
    delta = store.upsert_entity(name="Delta", entity_type="node", claim_ids=[claim["id"]])
    store.upsert_relation(
        relation_type="connects",
        subject_entity_id=alpha["id"],
        object_entity_id=beta["id"],
        claim_ids=[claim["id"]],
        confidence=0.9,
        source_type="direct-source-supported",
    )
    store.upsert_relation(
        relation_type="connects",
        subject_entity_id=alpha["id"],
        object_entity_id=gamma["id"],
        claim_ids=[claim["id"]],
        confidence=0.9,
        source_type="direct-source-supported",
    )
    store.upsert_relation(
        relation_type="connects",
        subject_entity_id=gamma["id"],
        object_entity_id=delta["id"],
        claim_ids=[claim["id"]],
        confidence=0.7,
        source_type="direct-source-supported",
    )

    ranked = KernelMemoryGraphSearch(store).rank(
        "Alpha connects",
        max_records=2,
    )

    assert len(ranked) == 2


def test_graph_search_exposes_score_tiers_and_respects_edge_budget(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        graph_relation_promote_min_observations=1,
        graph_relation_promote_min_confidence=0.5,
        graph_search_seed_limit=4,
        graph_search_edge_limit=1,
    )
    store = KernelMemoryStore.from_config(config)
    claim = store.ingest_claim(claim_type="fact", content="Alpha connects to Beta and Gamma.")
    alpha = store.upsert_entity(name="Alpha", entity_type="node", claim_ids=[claim["id"]])
    beta = store.upsert_entity(name="Beta", entity_type="node", claim_ids=[claim["id"]])
    gamma = store.upsert_entity(name="Gamma", entity_type="node", claim_ids=[claim["id"]])
    strong = store.upsert_relation(
        relation_type="connects",
        subject_entity_id=alpha["id"],
        object_entity_id=beta["id"],
        claim_ids=[claim["id"]],
        confidence=0.95,
        source_type="direct-source-supported",
    )
    store.upsert_relation(
        relation_type="connects",
        subject_entity_id=alpha["id"],
        object_entity_id=gamma["id"],
        claim_ids=[claim["id"]],
        confidence=0.6,
        source_type="model-inferred",
    )

    ranked = KernelMemoryGraphSearch(store).rank("Alpha connects", max_records=4)
    strong_result = next(record for record in ranked if record["id"] == strong["id"])

    assert strong_result["graph_score_tier"] in {"source_backed_strong", "source_backed"}
    assert strong_result["graph_frontier_role"] in {"solution", "bridge"}
    assert sum(1 for record in ranked if record["kind"] == "relation") <= 1


def test_graph_search_respects_max_hops_when_expanding_from_seed(tmp_path):
    base_config = {
        "enabled": True,
        "namespace": "bestie",
        "graph_relation_promote_min_observations": 1,
        "graph_relation_promote_min_confidence": 0.5,
        "graph_search_seed_limit": 4,
        "graph_search_edge_limit": 8,
    }
    shallow_store = KernelMemoryStore.from_config(
        KernelMemoryConfig(root_dir=tmp_path / "kernel-shallow", graph_search_max_hops=1, **base_config)
    )
    deep_store = KernelMemoryStore.from_config(
        KernelMemoryConfig(root_dir=tmp_path / "kernel-deep", graph_search_max_hops=3, **base_config)
    )
    for store in (shallow_store, deep_store):
        claim = store.ingest_claim(
            claim_type="fact",
            content="Alpha connects to Beta, Beta to Gamma, Gamma to Delta.",
        )
        alpha = store.upsert_entity(name="Alpha", entity_type="node", claim_ids=[claim["id"]])
        beta = store.upsert_entity(name="Beta", entity_type="node", claim_ids=[claim["id"]])
        gamma = store.upsert_entity(name="Gamma", entity_type="node", claim_ids=[claim["id"]])
        delta = store.upsert_entity(name="Delta", entity_type="node", claim_ids=[claim["id"]])
        store.upsert_relation(
            relation_type="connects",
            subject_entity_id=alpha["id"],
            object_entity_id=beta["id"],
            claim_ids=[claim["id"]],
            confidence=0.95,
            source_type="direct-source-supported",
        )
        store.upsert_relation(
            relation_type="connects",
            subject_entity_id=beta["id"],
            object_entity_id=gamma["id"],
            claim_ids=[claim["id"]],
            confidence=0.9,
            source_type="direct-source-supported",
        )
        store.upsert_relation(
            relation_type="connects",
            subject_entity_id=gamma["id"],
            object_entity_id=delta["id"],
            claim_ids=[claim["id"]],
            confidence=0.85,
            source_type="direct-source-supported",
        )

    shallow_ranked = KernelMemoryGraphSearch(shallow_store).rank("Alpha", max_records=10)
    deep_ranked = KernelMemoryGraphSearch(deep_store).rank("Alpha", max_records=10)

    shallow_ids = {record["id"] for record in shallow_ranked}
    deep_names = {record.get("name") for record in deep_ranked if record.get("kind") == "entity"}

    assert len(deep_ranked) >= len(shallow_ranked)
    assert "Delta" not in {record.get("name") for record in shallow_ranked if record.get("kind") == "entity"}
    assert "Delta" in deep_names
    assert shallow_ids <= {record["id"] for record in deep_ranked}


def test_graph_search_can_surface_event_nodes_with_temporal_context(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        graph_relation_promote_min_observations=1,
        graph_relation_promote_min_confidence=0.5,
    )
    store = KernelMemoryStore.from_config(config)
    claim = store.ingest_claim(
        claim_type="fact",
        content="Laura started rehab on Wednesday after the accident.",
    )
    laura = store.upsert_entity(name="Laura", entity_type="cat", claim_ids=[claim["id"]])
    store.ingest_event(
        event_type="rehab_start",
        title="Laura rehab start",
        summary="Laura started rehab on Wednesday after the accident.",
        actor_entity_id=laura["id"],
        participant_entity_ids=[laura["id"]],
        claim_ids=[claim["id"]],
        entity_ids=[laura["id"]],
        temporal_markers=["Wednesday"],
        confidence=0.9,
    )

    ranked = KernelMemoryGraphSearch(store).rank(
        "When did Laura start rehab?",
        max_records=4,
    )

    assert any(record["kind"] == "event" for record in ranked)
    event = next(record for record in ranked if record["kind"] == "event")
    assert event["graph_frontier_role"] in {"solution", "bridge"}


def test_graph_search_filters_relation_without_live_claim_support(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        graph_relation_promote_min_observations=1,
        graph_relation_promote_min_confidence=0.5,
    )
    store = KernelMemoryStore.from_config(config)
    claim = store.ingest_claim(
        claim_type="fact",
        content="Earth transfers to Mars.",
    )
    earth = store.upsert_entity(name="Earth", entity_type="planet", claim_ids=[claim["id"]])
    mars = store.upsert_entity(name="Mars", entity_type="planet", claim_ids=[claim["id"]])
    relation = store.upsert_relation(
        relation_type="transfers_to",
        subject_entity_id=earth["id"],
        object_entity_id=mars["id"],
        claim_ids=[claim["id"]],
        confidence=0.9,
        source_type="direct-source-supported",
    )
    store.update_record_status("claim", claim["id"], status="superseded", reason="test cleanup")

    ranked = KernelMemoryGraphSearch(store).rank(
        "How does Earth transfer to Mars?",
        max_records=4,
    )

    assert relation["id"] not in {record["id"] for record in ranked}


def test_graph_search_hides_contradiction_edges_for_normal_queries(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        graph_relation_promote_min_observations=1,
        graph_relation_promote_min_confidence=0.5,
    )
    store = KernelMemoryStore.from_config(config)
    claim = store.ingest_claim(
        claim_type="fact",
        content="Old policy conflicts with New policy.",
    )
    old = store.upsert_entity(name="Old policy", entity_type="policy", claim_ids=[claim["id"]])
    new = store.upsert_entity(name="New policy", entity_type="policy", claim_ids=[claim["id"]])
    contradiction = store.upsert_relation(
        relation_type="contradicts",
        subject_entity_id=old["id"],
        object_entity_id=new["id"],
        claim_ids=[claim["id"]],
        confidence=0.92,
        source_type="direct-source-supported",
    )

    normal_ranked = KernelMemoryGraphSearch(store).rank(
        "What is the new policy?",
        max_records=6,
    )
    conflict_ranked = KernelMemoryGraphSearch(store).rank(
        "What is the conflict between the old and new policy?",
        max_records=6,
    )

    assert contradiction["id"] not in {record["id"] for record in normal_ranked}
    assert contradiction["id"] in {record["id"] for record in conflict_ranked}


def test_graph_search_can_surface_episode_nodes(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        graph_relation_promote_min_observations=1,
        graph_relation_promote_min_confidence=0.5,
    )
    store = KernelMemoryStore.from_config(config)
    claim = store.ingest_claim(
        claim_type="fact",
        content="Laura rehab started on Wednesday and continued with daily exercises.",
    )
    laura = store.upsert_entity(name="Laura", entity_type="cat", claim_ids=[claim["id"]])
    event = store.ingest_event(
        event_type="rehab_progress",
        title="Laura rehab progress",
        summary="Laura rehab started on Wednesday and continued with daily exercises.",
        actor_entity_id=laura["id"],
        participant_entity_ids=[laura["id"]],
        claim_ids=[claim["id"]],
        entity_ids=[laura["id"]],
        temporal_markers=["Wednesday"],
        confidence=0.9,
    )
    store.ingest_episode(
        title="Laura rehab episode",
        summary="Laura rehab progressed across multiple exercises.",
        claim_ids=[claim["id"]],
        entity_ids=[laura["id"]],
        event_ids=[event["id"]],
        confidence=0.88,
    )

    ranked = KernelMemoryGraphSearch(store).rank(
        "Give me the Laura rehab episode",
        max_records=5,
    )

    assert any(record["kind"] == "episode" for record in ranked)


def test_graph_search_prefers_event_nodes_for_temporal_query_when_preferred(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        graph_relation_promote_min_observations=1,
        graph_relation_promote_min_confidence=0.5,
    )
    store = KernelMemoryStore.from_config(config)
    claim = store.ingest_claim(
        claim_type="fact",
        content="Laura rehab changed on Wednesday and Laura supports Tomi.",
    )
    laura = store.upsert_entity(name="Laura", entity_type="cat", claim_ids=[claim["id"]])
    tomi = store.upsert_entity(name="Tomi", entity_type="person", claim_ids=[claim["id"]])
    store.upsert_relation(
        relation_type="supports",
        subject_entity_id=laura["id"],
        object_entity_id=tomi["id"],
        claim_ids=[claim["id"]],
        confidence=0.93,
        source_type="direct-source-supported",
    )
    event = store.ingest_event(
        event_type="rehab_update",
        title="Laura rehab update",
        summary="Laura rehab changed on Wednesday.",
        actor_entity_id=laura["id"],
        participant_entity_ids=[laura["id"]],
        claim_ids=[claim["id"]],
        entity_ids=[laura["id"]],
        temporal_markers=["Wednesday"],
        confidence=0.88,
    )

    ranked = KernelMemoryGraphSearch(store).rank(
        "What changed for Laura on Wednesday?",
        max_records=4,
        preferred_kinds=["event"],
    )

    assert ranked
    assert ranked[0]["kind"] == "event"
    assert ranked[0]["id"] == event["id"]


def test_graph_search_penalizes_generic_hubs_when_specific_event_exists(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        graph_relation_promote_min_observations=1,
        graph_relation_promote_min_confidence=0.5,
        graph_search_edge_limit=16,
    )
    store = KernelMemoryStore.from_config(config)
    anchor_claim = store.ingest_claim(
        claim_type="fact",
        content="Project hub touches many unrelated things while Laura rehab changed on Wednesday.",
    )
    hub = store.upsert_entity(name="Project hub", entity_type="topic", claim_ids=[anchor_claim["id"]])
    laura = store.upsert_entity(name="Laura", entity_type="cat", claim_ids=[anchor_claim["id"]])
    for index in range(5):
        node = store.upsert_entity(name=f"Node {index}", entity_type="topic", claim_ids=[anchor_claim["id"]])
        store.upsert_relation(
            relation_type="mentions",
            subject_entity_id=hub["id"],
            object_entity_id=node["id"],
            claim_ids=[anchor_claim["id"]],
            confidence=0.82,
            source_type="direct-source-supported",
        )
    event = store.ingest_event(
        event_type="rehab_update",
        title="Laura rehab update",
        summary="Laura rehab changed on Wednesday.",
        actor_entity_id=laura["id"],
        participant_entity_ids=[laura["id"]],
        claim_ids=[anchor_claim["id"]],
        entity_ids=[laura["id"]],
        temporal_markers=["Wednesday"],
        confidence=0.9,
    )

    ranked = KernelMemoryGraphSearch(store).rank(
        "What changed for Laura on Wednesday?",
        max_records=5,
        preferred_kinds=["event"],
    )

    ranked_ids = [record["id"] for record in ranked]
    assert event["id"] in ranked_ids[:2]
    assert hub["id"] not in ranked_ids[:2]
