from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace

from agent.kernel_memory import KernelMemoryConfig, KernelMemoryStore
from agent.kernel_memory_conflicts import KernelMemoryConflictDetector
from agent.kernel_memory_query_planner import KernelMemoryRoutePlan
from agent.kernel_memory_retrieval import KernelMemoryRetriever
from agent.kernel_memory_retrieval_router import classify_evidence


def test_retrieval_preview_exposes_evidence_class_and_provenance(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        retrieval_policy_order=["curated", "source"],
    )
    store = KernelMemoryStore.from_config(config)
    store.materialize_curated_memory(
        title="Mission summary",
        summary="Mission summary for orbital planning.",
        source_ids=["doc:1"],
    )
    retriever = KernelMemoryRetriever(config, store)

    preview = retriever.preview_retrieval(
        "mission summary",
        max_records=4,
        max_chars=1200,
    )

    assert preview["retrieval"]["items"]
    first = preview["retrieval"]["items"][0]
    assert first["evidence_class"]
    assert first["evidence_provenance"]["route"] == first["route"]
    assert first["evidence_provenance"]["route_score"] == first["route_score"]
    assert preview["retrieval"]["evidence_chain"]["items"]
    assert preview["retrieval"]["evidence_chain"]["text"].startswith("Evidence chain:")


def test_retrieval_router_degrades_when_graph_route_fails(monkeypatch, tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        retrieval_policy_order=["graph", "source"],
    )
    store = KernelMemoryStore.from_config(config)
    store.ingest_document(
        document_type="note",
        title="Orbital mechanics notebook",
        content="Orbital mechanics notes mention Hohmann transfers.",
    )
    retriever = KernelMemoryRetriever(config, store)

    monkeypatch.setattr(store, "retrieve_graph_context", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("graph offline")))

    route_results = retriever.router.execute_plan(
        query="orbital mechanics",
        plan=SimpleNamespace(
            routes=[
                KernelMemoryRoutePlan(route="graph", weight=1.0, max_records=2, max_chars=600),
                KernelMemoryRoutePlan(route="source", weight=1.0, max_records=2, max_chars=600),
            ]
        ),
        namespaces=None,
        as_of=None,
        route_executor=retriever._execute_route_plan,
    )

    assert route_results["graph"]["status"] == "failed"
    assert route_results["graph"]["error"] == "graph offline"
    assert route_results["source"]["status"] == "ok"
    assert route_results["source"]["items"]
    first_item = route_results["source"]["items"][0]
    assert first_item["evidence_class"] == "direct_source"
    assert first_item["evidence_provenance"]["route"] == "source"


def test_retrieval_slot_reservation_keeps_event_core_ahead_of_curated_summary(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        curated_retrieval_only=False,
        retrieval_policy_order=["curated", "semantic", "graph", "source"],
    )
    store = KernelMemoryStore.from_config(config)
    claim = store.ingest_claim(
        claim_type="dated_fact",
        content="Laura rehab started on Wednesday after the accident.",
    )
    event = store.ingest_event(
        event_type="personal_event",
        title="Laura rehab start",
        summary="Laura rehab started on Wednesday after the accident.",
        temporal_markers=["Wednesday"],
        claim_ids=[claim["id"]],
    )
    store.materialize_curated_memory(
        title="Laura summary",
        summary="Laura is important and rehab progress matters.",
        claim_ids=[claim["id"]],
        event_ids=[event["id"]],
    )
    retriever = KernelMemoryRetriever(config, store)

    preview = retriever.preview_retrieval(
        "When did Laura rehab start?",
        max_records=4,
        max_chars=1200,
    )

    assert preview["retrieval"]["items"]
    assert preview["retrieval"]["items"][0]["kind"] == "event"


def test_route_retrieval_preserves_route_score_and_rank_metadata(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        retrieval_policy_order=["curated", "semantic"],
    )
    store = KernelMemoryStore.from_config(config)
    store.materialize_curated_memory(
        title="Laura favorite quote",
        summary="Laura's current favorite quote is the dock quote.",
        metadata={"conflict_signal": "correction"},
        supersedes="curated_old",
    )
    retriever = KernelMemoryRetriever(config, store)

    preview = retriever.preview_retrieval(
        "What is Laura's current favorite quote?",
        max_records=4,
        max_chars=1200,
    )

    first = preview["retrieval"]["items"][0]
    assert first["route_score"] > 0
    assert first["evidence_provenance"]["route_rank"] >= 1


def test_graph_route_formats_event_support_blocks(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        curated_retrieval_only=False,
        retrieval_policy_order=["graph"],
    )
    store = KernelMemoryStore.from_config(config)
    claim = store.ingest_claim(
        claim_type="dated_fact",
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
        confidence=0.92,
    )
    result = store.retrieve_graph_context(
        "When did Laura start rehab?",
        max_records=4,
        max_chars=1200,
    )

    assert result["items"]
    assert any(item["kind"] == "event" and item["route"] == "graph" for item in result["items"])
    assert "Event:" in result["text"]
    assert "Wednesday" in result["text"]


def test_graph_route_respects_preferred_kinds_when_present(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        curated_retrieval_only=False,
        retrieval_policy_order=["graph"],
    )
    store = KernelMemoryStore.from_config(config)
    claim = store.ingest_claim(
        claim_type="fact",
        content="Laura rehab changed on Wednesday and the update was logged.",
    )
    laura = store.upsert_entity(name="Laura", entity_type="cat", claim_ids=[claim["id"]])
    store.ingest_event(
        event_type="rehab_update",
        title="Laura rehab update",
        summary="Laura rehab changed on Wednesday.",
        actor_entity_id=laura["id"],
        participant_entity_ids=[laura["id"]],
        claim_ids=[claim["id"]],
        entity_ids=[laura["id"]],
        temporal_markers=["Wednesday"],
        confidence=0.92,
    )

    result = store.retrieve_graph_context(
        "What changed in Laura rehab?",
        max_records=4,
        max_chars=1200,
        preferred_kinds=["event"],
    )

    assert result["items"]
    assert all(item["kind"] == "event" for item in result["items"])


def test_item_formatter_uses_graph_event_block_for_graph_event_items(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        curated_retrieval_only=False,
        retrieval_policy_order=["graph"],
    )
    store = KernelMemoryStore.from_config(config)
    claim = store.ingest_claim(
        claim_type="dated_fact",
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
        confidence=0.92,
    )
    event = next(iter(store.list_records("event")))
    retriever = KernelMemoryRetriever(config, store)

    block = retriever._format_item_block({**event, "route": "graph"})

    assert "Event:" in block
    assert "Wednesday" in block


def test_formatter_surfaces_lineage_hints_for_current_state_queries(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
    )
    store = KernelMemoryStore.from_config(config)
    previous = store.materialize_curated_memory(
        title="Old quote",
        summary="The old favorite quote.",
    )
    current = store.materialize_curated_memory(
        title="Current quote",
        summary="The current favorite quote.",
    )
    store.annotate_lineage(
        "curated_memory",
        current["id"],
        review_of=previous["id"],
        revises=previous["id"],
        reason="test_lineage_rendering",
    )
    current = store.get_record("curated_memory", current["id"])
    assert current is not None
    retriever = KernelMemoryRetriever(config, store)

    block = retriever._format_item_block({**current, "route": "curated"})

    assert "Lineage:" in block
    assert "revises=Old quote" in block


def test_curated_retrieval_score_prefers_verified_useful_memory(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
    )
    store = KernelMemoryStore.from_config(config)
    high = store.materialize_curated_memory(
        title="Laura favorite quote",
        summary="Laura's favorite quote is the dock quote.",
        metadata={
            "verification_state": "verified",
            "quality_tier": "high",
        },
    )
    low = deepcopy(high)
    low["id"] = "cur-low-priority"
    low["content_hash"] = "cur-low-priority-hash"
    low["verification_state"] = "inferred"
    low["quality_tier"] = "low"
    low["metadata"] = {
        **(low.get("metadata") or {}),
        "verification_state": "inferred",
        "quality_tier": "low",
    }
    store._records["curated_memory"][low["id"]] = low
    store._hash_index["curated_memory"][low["content_hash"]] = low["id"]
    store._persist_derived_kind("curated_memory")
    store._persist_hash_index()
    store._apply_overlay(
        "curated_memory",
        high["id"],
        {
            "retrieval_count": 5,
            "successful_retrieval_count": 4,
            "used_in_answer_count": 4,
        },
    )
    store._apply_overlay(
        "curated_memory",
        low["id"],
        {
            "retrieval_count": 5,
            "successful_retrieval_count": 1,
            "used_in_answer_count": 0,
        },
    )

    query = "What is Laura's favorite quote?"
    query_terms = store._lexical_terms(query)
    high_score = store._curated_retrieval_score(
        store.get_record("curated_memory", high["id"]),
        query=query,
        query_terms=query_terms,
    )
    low_score = store._curated_retrieval_score(
        store.get_record("curated_memory", low["id"]),
        query=query,
        query_terms=query_terms,
    )

    assert high_score > low_score


def test_record_score_penalizes_low_value_noisy_repeat_retrieval(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
    )
    store = KernelMemoryStore.from_config(config)
    useful = store.ingest_claim(
        claim_type="fact",
        content="Laura started rehab on Wednesday.",
        metadata={
            "verification_state": "grounded",
            "quality_tier": "normal",
        },
    )
    noisy = store.ingest_claim(
        claim_type="fact",
        content="Laura started rehab on Wednesday.",
        metadata={
            "verification_state": "inferred",
            "quality_tier": "low",
        },
        source_version="v2",
    )
    store._apply_overlay(
        "claim",
        useful["id"],
        {
            "retrieval_count": 4,
            "successful_retrieval_count": 4,
            "used_in_answer_count": 3,
        },
    )
    store._apply_overlay(
        "claim",
        noisy["id"],
        {
            "retrieval_count": 8,
            "successful_retrieval_count": 1,
            "used_in_answer_count": 0,
        },
    )

    query = "Laura started rehab"
    query_terms = store._lexical_terms(query)
    useful_score = store._record_score(
        store.get_record("claim", useful["id"]),
        query=query,
        query_terms=query_terms,
    )
    noisy_score = store._record_score(
        store.get_record("claim", noisy["id"]),
        query=query,
        query_terms=query_terms,
    )

    assert useful_score > noisy_score


def test_graph_event_items_are_classified_as_graph_event_evidence():
    evidence_class = classify_evidence({"kind": "event"}, route="graph")

    assert evidence_class == "graph_event"


def test_graph_episode_items_are_classified_as_graph_episode_evidence():
    evidence_class = classify_evidence({"kind": "episode"}, route="graph")

    assert evidence_class == "graph_episode"


def test_curated_retrieval_hides_open_conflict_memories_for_normal_query(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        retrieval_policy_order=["curated"],
    )
    store = KernelMemoryStore.from_config(config)
    first = store.materialize_curated_memory(
        title="Mission summary",
        summary="Mission summary says Alpha is the canonical target.",
        source_ids=["doc:1"],
    )
    second = store.materialize_curated_memory(
        title="Mission summary",
        summary="Mission summary says Beta is the canonical target.",
        source_ids=["doc:2"],
    )
    detector = KernelMemoryConflictDetector(config, store)
    summary = detector.scan()

    normal = store.retrieve_curated_context("mission summary", max_records=4, max_chars=1200)
    explicit_conflict = store.retrieve_curated_context("What is the conflict in the mission summary?", max_records=4, max_chars=1200)

    assert summary["open"] == 1
    assert not normal["items"]
    assert {item["id"] for item in explicit_conflict["items"]} == {first["id"], second["id"]}


def test_semantic_retrieval_hides_open_conflict_events_for_normal_query(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        retrieval_policy_order=["semantic"],
    )
    store = KernelMemoryStore.from_config(config)
    claim = store.ingest_claim(claim_type="fact", content="Laura rehab timing was discussed twice.")
    laura = store.upsert_entity(name="Laura", entity_type="cat", claim_ids=[claim["id"]])
    first = store.ingest_event(
        event_type="rehab_update",
        title="Laura rehab status",
        summary="Laura rehab started on Wednesday.",
        actor_entity_id=laura["id"],
        participant_entity_ids=[laura["id"]],
        claim_ids=[claim["id"]],
        entity_ids=[laura["id"]],
        temporal_markers=["Wednesday"],
    )
    second = store.ingest_event(
        event_type="rehab_update",
        title="Laura rehab status",
        summary="Laura rehab started on Thursday.",
        actor_entity_id=laura["id"],
        participant_entity_ids=[laura["id"]],
        claim_ids=[claim["id"]],
        entity_ids=[laura["id"]],
        temporal_markers=["Thursday"],
    )
    detector = KernelMemoryConflictDetector(config, store)
    summary = detector.scan()

    normal = store.retrieve_semantic_context("When did Laura rehab start?", max_records=4, max_chars=1200)
    explicit_conflict = store.retrieve_semantic_context("What is the conflict about when Laura rehab started?", max_records=4, max_chars=1200)

    assert summary["open"] == 1
    assert not normal["items"]
    assert {item["id"] for item in explicit_conflict["items"] if item["kind"] == "event"} == {first["id"], second["id"]}
