from types import SimpleNamespace

from agent.kernel_memory import KernelMemoryConfig, KernelMemoryStore
from agent.replay_kernel_promotion import ReplayKernelPromotionBridge


def test_replay_kernel_promotion_materializes_curated_memory(tmp_path):
    config = KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel", namespace="bestie")
    store = KernelMemoryStore.from_config(config)
    runtime = SimpleNamespace(store=store)
    bridge = ReplayKernelPromotionBridge.from_dict(
        {
            "enabled": True,
            "min_lifecycle_states": ["active", "reinforced"],
            "min_access_count": 1,
        }
    )

    episode = {
        "episode_id": "ep_123",
        "goal": "Fix nginx permissions",
        "summary": "I investigated nginx and confirmed the blocker was file permissions.",
        "fidelity": "high",
        "lifecycle_state": "reinforced",
        "access_count": 2,
        "files_touched_json": '["/var/log/nginx/error.log"]',
        "artifact_refs_json": "[]",
    }

    promoted = bridge.promote_episode(
        kernel_runtime=runtime,
        episode=episode,
        session_id="sess-1",
        turn_id="turn-2",
        logger=SimpleNamespace(debug=lambda *args, **kwargs: None),
    )

    assert promoted is not None
    curated = store.list_curated_memories()
    claims = store.list_records("claim")
    events = store.list_records("event")
    episodes = store.list_records("episode")
    associations = store.list_records("association")
    assert curated
    assert curated[0]["metadata"]["origin"] == "replay_episode_promotion"
    assert claims
    assert events
    assert episodes
    assert curated[0]["event_ids"]
    assert associations
    assert curated[0]["verification_state"] in {"source_backed", "verified"}
    assert curated[0]["quality_tier"] in {"high", "normal"}


def test_replay_kernel_promotion_materializes_correction_signal(tmp_path):
    config = KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel", namespace="bestie")
    store = KernelMemoryStore.from_config(config)
    runtime = SimpleNamespace(store=store)
    bridge = ReplayKernelPromotionBridge.from_dict(
        {
            "enabled": True,
            "min_lifecycle_states": ["active", "reinforced"],
            "min_access_count": 1,
        }
    )

    episode = {
        "episode_id": "ep_fix",
        "goal": "Correct deployment rule",
        "summary": "We corrected the deployment rule and replaced the old rollback sequence with a safer one.",
        "fidelity": "high",
        "lifecycle_state": "reinforced",
        "access_count": 3,
        "files_touched_json": "[]",
        "artifact_refs_json": "[]",
    }

    promoted = bridge.promote_episode(
        kernel_runtime=runtime,
        episode=episode,
        session_id="sess-1",
        turn_id="turn-3",
        logger=SimpleNamespace(debug=lambda *args, **kwargs: None),
    )

    assert promoted is not None
    events = store.list_records("event")
    claims = store.list_records("claim")
    assert any(event["event_type"] == "superseded" for event in events)
    correction_event = next(event for event in events if event["event_type"] == "superseded")
    assert correction_event["event_status"] == "superseded"
    assert correction_event["metadata"]["conflict_signal"] == "correction"
    assert any(claim["metadata"].get("conflict_signal") == "correction" for claim in claims)


def test_replay_kernel_promotion_links_correction_lineage(tmp_path):
    config = KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel", namespace="bestie")
    store = KernelMemoryStore.from_config(config)
    runtime = SimpleNamespace(store=store)
    bridge = ReplayKernelPromotionBridge.from_dict(
        {
            "enabled": True,
            "min_lifecycle_states": ["active", "reinforced"],
            "min_access_count": 1,
        }
    )

    original = {
        "episode_id": "ep_old",
        "goal": "Deployment rule baseline",
        "summary": "The deployment rule uses the old rollback sequence for production releases.",
        "fidelity": "high",
        "lifecycle_state": "reinforced",
        "access_count": 2,
        "files_touched_json": "[]",
        "artifact_refs_json": "[]",
    }
    corrected = {
        "episode_id": "ep_new",
        "goal": "Correct deployment rule",
        "summary": "We corrected the deployment rule and replaced the old rollback sequence with a safer one.",
        "fidelity": "high",
        "lifecycle_state": "reinforced",
        "access_count": 3,
        "files_touched_json": "[]",
        "artifact_refs_json": "[]",
    }

    bridge.promote_episode(
        kernel_runtime=runtime,
        episode=original,
        session_id="sess-1",
        turn_id="turn-1",
        logger=SimpleNamespace(debug=lambda *args, **kwargs: None),
    )
    bridge.promote_episode(
        kernel_runtime=runtime,
        episode=corrected,
        session_id="sess-1",
        turn_id="turn-2",
        logger=SimpleNamespace(debug=lambda *args, **kwargs: None),
    )

    claims = store.list_records("claim")
    events = store.list_records("event")
    curated = store.list_curated_memories(status=None)

    old_claim = next(record for record in claims if "old rollback sequence" in str(record.get("content") or ""))
    new_claim = next(
        record
        for record in claims
        if record.get("metadata", {}).get("conflict_signal") == "correction"
    )
    assert old_claim["status"] == "superseded"
    assert old_claim["superseded_by"] == new_claim["id"]
    assert new_claim["supersedes"] == old_claim["id"]
    assert new_claim["review_of"] == old_claim["id"]
    assert new_claim["revises"] == old_claim["id"]
    assert old_claim["resolved_by"] == new_claim["id"]

    old_event = next(
        record
        for record in events
        if record.get("event_type") != "superseded"
        and "old rollback sequence" in str(record.get("summary") or "")
    )
    new_event = next(record for record in events if record.get("event_type") == "superseded")
    assert old_event["status"] == "superseded"
    assert old_event["superseded_by"] == new_event["id"]
    assert new_event["supersedes"] == old_event["id"]
    assert new_event["review_of"] == old_event["id"]
    assert new_event["revises"] == old_event["id"]
    assert old_event["resolved_by"] == new_event["id"]

    old_curated = next(
        record
        for record in curated
        if "old rollback sequence" in str(record.get("summary") or "")
        and record["status"] == "superseded"
    )
    new_curated = next(
        record
        for record in curated
        if record["status"] == "active" and "safer one" in str(record.get("summary") or "")
    )
    assert old_curated["superseded_by"] == new_curated["id"]
    assert new_curated["supersedes"] == old_curated["id"]
    assert new_curated["review_of"] == old_curated["id"]
    assert new_curated["revises"] == old_curated["id"]
    assert old_curated["resolved_by"] == new_curated["id"]

    new_episode = next(
        record
        for record in store.list_records("episode")
        if record["id"] == new_curated["episode_id"]
    )
    old_episode = next(
        record
        for record in store.list_records("episode")
        if record["id"] == old_curated["episode_id"]
    )
    assert new_episode["review_of"] == old_episode["id"]
    assert new_episode["revises"] == old_episode["id"]
    assert old_episode["resolved_by"] == new_episode["id"]


def test_replay_kernel_promotion_uses_fidelity_and_access_for_quality_contract(tmp_path):
    config = KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel", namespace="bestie")
    store = KernelMemoryStore.from_config(config)
    runtime = SimpleNamespace(store=store)
    bridge = ReplayKernelPromotionBridge.from_dict(
        {
            "enabled": True,
            "min_lifecycle_states": ["active", "reinforced"],
            "min_access_count": 1,
            "min_confidence": 0.78,
        }
    )

    episode = {
        "episode_id": "ep_trust",
        "goal": "Stabilize deployment rule",
        "summary": "We confirmed the safer deployment sequence after repeated testing.",
        "fidelity": "high",
        "lifecycle_state": "reinforced",
        "access_count": 3,
        "files_touched_json": "[]",
        "artifact_refs_json": "[]",
    }

    promoted = bridge.promote_episode(
        kernel_runtime=runtime,
        episode=episode,
        session_id="sess-1",
        turn_id="turn-4",
        logger=SimpleNamespace(debug=lambda *args, **kwargs: None),
    )

    assert promoted is not None
    refreshed = store.get_record("curated_memory", promoted["id"])
    assert refreshed is not None
    assert refreshed["verification_state"] == "verified"
    assert refreshed["quality_tier"] == "high"
    assert refreshed["confidence"] >= 0.88


def test_replay_kernel_promotion_builds_graph_relations_and_entity_links(tmp_path):
    config = KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel", namespace="bestie")
    store = KernelMemoryStore.from_config(config)
    runtime = SimpleNamespace(store=store)
    bridge = ReplayKernelPromotionBridge.from_dict(
        {
            "enabled": True,
            "min_lifecycle_states": ["active", "reinforced"],
            "min_access_count": 1,
        }
    )

    episode = {
        "episode_id": "ep_graph",
        "goal": "Track Laura support incident",
        "summary": "Laura supports Tomi while the rehab update stayed active on Wednesday.",
        "fidelity": "high",
        "lifecycle_state": "reinforced",
        "access_count": 2,
        "files_touched_json": "[]",
        "artifact_refs_json": "[]",
    }

    promoted = bridge.promote_episode(
        kernel_runtime=runtime,
        episode=episode,
        session_id="sess-1",
        turn_id="turn-5",
        logger=SimpleNamespace(debug=lambda *args, **kwargs: None),
    )

    assert promoted is not None
    relations = store.list_records("relation")
    episodes = store.list_records("episode")
    curated = store.get_record("curated_memory", promoted["id"])
    assert any(relation["relation_type"] == "supports" for relation in relations)
    assert episodes[0]["relation_ids"]
    assert curated is not None
    assert curated["entity_ids"]
    assert curated["relation_ids"]
