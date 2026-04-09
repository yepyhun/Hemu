from __future__ import annotations

from agent.kernel_memory import KernelMemoryConfig, KernelMemoryStore
from agent.kernel_memory_conflicts import KernelMemoryConflictDetector


def test_conflict_detector_flags_divergent_curated_memories(tmp_path):
    config = KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel", namespace="bestie")
    store = KernelMemoryStore.from_config(config)
    store.materialize_curated_memory(title="User preference: coffee", summary="Strongly prefers black coffee.")
    store.materialize_curated_memory(title="User preference: coffee", summary="Recently prefers latte instead.")
    detector = KernelMemoryConflictDetector(config, store)

    result = detector.scan()

    assert result["open"] == 1
    assert result["conflicts"][0]["record_count"] == 2


def test_conflict_detector_flags_divergent_events_with_same_identity(tmp_path):
    config = KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel", namespace="bestie")
    store = KernelMemoryStore.from_config(config)
    claim = store.ingest_claim(claim_type="fact", content="Laura rehab changed over time.")
    laura = store.upsert_entity(name="Laura", entity_type="cat", claim_ids=[claim["id"]])
    store.ingest_event(
        event_type="rehab_update",
        title="Laura rehab status",
        summary="Laura rehab started on Wednesday.",
        actor_entity_id=laura["id"],
        participant_entity_ids=[laura["id"]],
        claim_ids=[claim["id"]],
        entity_ids=[laura["id"]],
        temporal_markers=["Wednesday"],
    )
    store.ingest_event(
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

    result = detector.scan()

    event_conflicts = [item for item in result["conflicts"] if item.get("object_kind") == "event"]
    assert event_conflicts
    assert event_conflicts[0]["reason"] == "divergent_event_state"
    assert event_conflicts[0]["record_count"] == 2
