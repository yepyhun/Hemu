from __future__ import annotations

from agent.kernel_memory import KernelMemoryConfig, KernelMemoryStore


def _store(tmp_path):
    return KernelMemoryStore.from_config(
        KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel", namespace="bestie")
    )


def test_association_expansion_brings_related_truth_record_into_context(tmp_path):
    store = _store(tmp_path)
    primary = store.materialize_curated_memory(
        title="Laura rehab progress",
        summary="Laura rehab progress and gait recovery updates remain important.",
        metadata={"memory_class": "project_task"},
    )
    related = store.materialize_curated_memory(
        title="Sensitive pet handling",
        summary="Handle pet recovery context carefully and empathetically.",
        metadata={"memory_class": "profile_preference"},
    )
    store.record_co_access(
        [primary, related],
        association_origin="profile_decision_pairing",
        successful=True,
    )
    store.record_co_access(
        [primary, related],
        association_origin="profile_decision_pairing",
        successful=True,
    )

    result = store.retrieve_context_by_policy(
        "gait rehab progress",
        max_records=3,
        max_chars=1200,
    )

    assert result["items"]
    assert any(item["id"] == related["id"] and item.get("route") == "association" for item in result["items"])
    assert "association" in result["routes"]


def test_activation_lifecycle_warms_up_with_repeated_successful_retrieval(tmp_path):
    store = _store(tmp_path)
    memory = store.materialize_curated_memory(
        title="Scheduler rule",
        summary="Only promise reminders when a scheduler tool is actually available.",
        metadata={"memory_class": "project_task"},
        confidence=0.85,
    )

    initial = store.get_record("curated_memory", memory["id"])
    assert initial is not None
    assert initial["activation_state"] in {"provisional", "fading", "active_warm"}

    store.retrieve_curated_context("scheduler reminders rule", max_records=2, max_chars=600)
    store.retrieve_curated_context("scheduler reminders rule", max_records=2, max_chars=600)
    store.retrieve_curated_context("scheduler reminders rule", max_records=2, max_chars=600)

    updated = store.get_record("curated_memory", memory["id"])
    assert updated is not None
    assert updated["retrieval_count"] >= 2
    assert updated["successful_retrieval_count"] >= 2
    assert updated["activation_state"] in {"active_warm", "active_hot"}


def test_generic_association_does_not_promote_zero_match_noise(tmp_path):
    store = _store(tmp_path)
    primary = store.materialize_curated_memory(
        title="Orbital planning",
        summary="Orbital planning and transfer windows remain important.",
        metadata={"memory_class": "project_task"},
    )
    unrelated = store.materialize_curated_memory(
        title="Cat empathy reminder",
        summary="Handle sensitive pet recovery context carefully and empathetically.",
        metadata={"memory_class": "profile_preference"},
    )
    store.record_co_access(
        [primary, unrelated],
        association_origin="retrieval_coaccess",
        successful=True,
    )
    store.record_co_access(
        [primary, unrelated],
        association_origin="retrieval_coaccess",
        successful=True,
    )

    result = store.retrieve_context_by_policy(
        "orbital transfer windows",
        max_records=3,
        max_chars=1200,
    )

    assert result["items"]
    assert all(item["id"] != unrelated["id"] or item.get("route") != "association" for item in result["items"])
