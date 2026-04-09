from __future__ import annotations

from agent.kernel_memory import KernelMemoryConfig, KernelMemoryStore
from agent.kernel_memory_admin import KernelMemoryAdminService


def test_kernel_memory_store_supports_episode_records_and_lineage(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
    )
    store = KernelMemoryStore.from_config(config)
    resource = store.ingest_resource(
        resource_type="note",
        title="Launch diary",
        content="Launch window moved from March to April.",
    )
    extract = store.ingest_extract(
        resource_id=resource["id"],
        content="Launch window moved from March to April.",
    )
    claim = store.ingest_claim(
        claim_type="fact",
        content="Launch window moved from March to April.",
        extract_ids=[extract["id"]],
        resource_ids=[resource["id"]],
    )
    entity = store.upsert_entity(
        name="Launch window",
        entity_type="schedule",
        claim_ids=[claim["id"]],
        resource_ids=[resource["id"]],
    )
    relation = store.upsert_relation(
        relation_type="moves_to",
        subject_entity_id=entity["id"],
        object_entity_id=entity["id"],
        claim_ids=[claim["id"]],
        confidence=0.9,
    )

    episode = store.ingest_episode(
        title="Launch reschedule",
        summary="Mission launch shifted into a later window.",
        starts_at="2026-03-01T00:00:00+00:00",
        ends_at="2026-04-01T00:00:00+00:00",
        claim_ids=[claim["id"]],
        entity_ids=[entity["id"]],
        relation_ids=[relation["id"]],
    )
    lineage = store.trace_resource_lineage(resource["id"])

    assert episode["kind"] == "episode"
    assert lineage["episodes"]
    assert lineage["episodes"][0]["id"] == episode["id"]


def test_kernel_memory_store_retrieves_temporal_views_with_as_of(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel", namespace="bestie")
    )
    old_memory = store.materialize_curated_memory(
        title="Mission owner",
        summary="Alice owns the mission.",
        valid_from="2026-01-01T00:00:00+00:00",
        valid_to="2026-02-01T00:00:00+00:00",
    )
    new_memory = store.materialize_curated_memory(
        title="Mission owner",
        summary="Bob owns the mission.",
        valid_from="2026-02-01T00:00:00+00:00",
        supersedes=old_memory["id"],
    )

    january = store.retrieve_curated_context(
        "mission owner",
        as_of="2026-01-15T00:00:00+00:00",
    )
    march = store.retrieve_curated_context(
        "mission owner",
        as_of="2026-03-15T00:00:00+00:00",
    )
    now_view = store.retrieve_curated_context("mission owner")

    assert "Alice owns the mission." in january["text"]
    assert "Bob owns the mission." not in january["text"]
    assert "Bob owns the mission." in march["text"]
    assert "Alice owns the mission." not in now_view["text"]
    assert new_memory["supersedes"] == old_memory["id"]


def test_admin_preview_retrieval_exposes_as_of_plan(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
    )
    store = KernelMemoryStore.from_config(config)
    store.materialize_curated_memory(
        title="Program status",
        summary="The program was delayed in January.",
        valid_from="2026-01-01T00:00:00+00:00",
        valid_to="2026-02-01T00:00:00+00:00",
    )
    store.materialize_curated_memory(
        title="Program status",
        summary="The program recovered in February.",
        valid_from="2026-02-01T00:00:00+00:00",
    )
    admin = KernelMemoryAdminService(config)

    preview = admin.preview_retrieval(
        "program status",
        as_of="2026-01-15T00:00:00+00:00",
    )

    assert preview["plan"]["as_of"] == "2026-01-15T00:00:00+00:00"
    assert "delayed in January" in preview["retrieval"]["text"]


def test_kernel_memory_store_hides_future_records_from_default_now_view(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel", namespace="bestie")
    )
    store.materialize_curated_memory(
        title="Future launch",
        summary="The launch happens next year.",
        valid_from="2099-01-01T00:00:00+00:00",
    )

    now_view = store.retrieve_curated_context("launch")
    future_view = store.retrieve_curated_context(
        "launch",
        as_of="2099-01-02T00:00:00+00:00",
    )

    assert "next year" not in now_view["text"]
    assert "next year" in future_view["text"]
