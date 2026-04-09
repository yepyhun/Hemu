from __future__ import annotations

from agent.kernel_memory import KernelMemoryConfig, KernelMemoryStore
from agent.kernel_memory_consolidation import KernelMemoryConsolidationService


def test_consolidation_cycle_creates_resource_backed_curated_memory(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        consolidation_enabled=True,
    )
    store = KernelMemoryStore.from_config(config)
    document = store.ingest_document(
        document_type="note",
        title="Orbital notebook",
        content=(
            "Hohmann transfer windows reduce delta-v requirements for many orbital maneuvers.\n\n"
            "Mission planners still need to account for phasing constraints."
        ),
    )
    extract_id = document["extract_ids"][0]
    store.ingest_claim(
        claim_type="fact",
        content="Hohmann transfer windows reduce delta-v requirements.",
        extract_ids=[extract_id],
        resource_ids=[document["resource"]["id"]],
    )

    service = KernelMemoryConsolidationService(config, store)
    result = service.run_cycle(max_resources=10, max_jobs=10)
    curated = [
        record
        for record in store.list_curated_memories()
        if (record.get("metadata") or {}).get("memory_class") == "consolidated.resource"
    ]

    assert result["processing"]["created"] == 1
    assert len(curated) == 1
    assert curated[0]["source_ids"] == [document["resource"]["id"]]
    assert curated[0]["metadata"]["consolidation_policy_version"] == "consolidation-v1"


def test_consolidation_cycle_is_idempotent_for_same_evidence(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        consolidation_enabled=True,
    )
    store = KernelMemoryStore.from_config(config)
    document = store.ingest_document(
        document_type="note",
        title="Mars notebook",
        content="Mars launch windows depend on orbital timing and transfer constraints.",
    )
    store.ingest_claim(
        claim_type="fact",
        content="Mars launch windows depend on orbital timing.",
        resource_ids=[document["resource"]["id"]],
        extract_ids=document["extract_ids"][:1],
    )

    service = KernelMemoryConsolidationService(config, store)
    first = service.run_cycle(max_resources=10, max_jobs=10)
    second = service.run_cycle(max_resources=10, max_jobs=10)
    curated = [
        record
        for record in store.list_curated_memories()
        if (record.get("metadata") or {}).get("memory_class") == "consolidated.resource"
    ]

    assert first["processing"]["created"] == 1
    assert second["processing"]["created"] == 0
    assert len(curated) == 1


def test_consolidation_supersedes_older_resource_summary_when_evidence_changes(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        consolidation_enabled=True,
    )
    store = KernelMemoryStore.from_config(config)
    document = store.ingest_document(
        document_type="note",
        title="Research note",
        content="Initial orbital research note.",
    )
    first_claim = store.ingest_claim(
        claim_type="fact",
        content="Initial orbital research note.",
        resource_ids=[document["resource"]["id"]],
        extract_ids=document["extract_ids"][:1],
    )
    service = KernelMemoryConsolidationService(config, store)
    service.run_cycle(max_resources=10, max_jobs=10)
    original = [
        record
        for record in store.list_curated_memories()
        if (record.get("metadata") or {}).get("memory_class") == "consolidated.resource"
    ][0]

    store.ingest_claim(
        claim_type="fact",
        content="Updated orbital research introduces transfer-window caveats.",
        resource_ids=[document["resource"]["id"]],
        extract_ids=document["extract_ids"][:1],
        metadata={"revision": "v2"},
    )
    result = service.run_cycle(max_resources=10, max_jobs=10)
    curated = [
        record
        for record in store.list_curated_memories(status="")
        if document["resource"]["id"] in (record.get("source_ids") or [])
        and (record.get("metadata") or {}).get("memory_class") == "consolidated.resource"
    ]
    active = [record for record in curated if record.get("status") == "active"]
    superseded = [record for record in curated if record.get("status") == "superseded"]

    assert first_claim["id"] in original["claim_ids"]
    assert result["processing"]["created"] == 1
    assert result["processing"]["superseded"] >= 1
    assert len(active) == 1
    assert len(superseded) >= 1


def test_list_curated_memories_status_blank_includes_superseded_records(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        consolidation_enabled=True,
    )
    store = KernelMemoryStore.from_config(config)
    original = store.materialize_curated_memory(
        title="Original",
        summary="Original summary.",
        metadata={"memory_class": "consolidated.resource"},
        source_ids=["res-1"],
    )
    replacement = store.supersede_curated_memory(
        original["id"],
        title="Replacement",
        summary="Replacement summary.",
        metadata={"memory_class": "consolidated.resource"},
    )

    all_records = store.list_curated_memories(status="")
    active_records = store.list_curated_memories()

    assert any(record["id"] == original["id"] and record["status"] == "superseded" for record in all_records)
    assert any(record["id"] == replacement["id"] and record["status"] == "active" for record in all_records)
    assert all(record["status"] == "active" for record in active_records)


def test_consolidation_candidate_carries_quality_and_usefulness_signal(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        consolidation_enabled=True,
    )
    store = KernelMemoryStore.from_config(config)
    document = store.ingest_document(
        document_type="note",
        title="Scheduler note",
        content="Only promise reminders when a scheduler tool is actually available.",
    )
    claim = store.ingest_claim(
        claim_type="operational_rule",
        content="Only promise reminders when a scheduler tool is actually available.",
        resource_ids=[document["resource"]["id"]],
        extract_ids=document["extract_ids"][:1],
        metadata={"verified": True, "verification_evidence": ["tool:memory"]},
    )
    store.record_answer_usefulness([claim])

    service = KernelMemoryConsolidationService(config, store)
    candidate = service._candidate_for_resource(document["resource"]["id"])

    assert candidate is not None
    assert candidate.score >= 0.45
    assert candidate.metadata["consolidation_avg_usefulness"] > 0.0
