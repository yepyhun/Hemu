from __future__ import annotations

import json

from agent.kernel_memory import KernelMemoryConfig, KernelMemoryStore
from agent.kernel_memory_corpus import (
    KernelMemoryChunker,
    KernelMemoryCorpusIngestQueue,
    KernelMemoryCorpusIngestWorker,
)


def test_kernel_memory_config_defaults_to_visible_home_memory(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("HERMES_MEMORY_ROOT", raising=False)

    config = KernelMemoryConfig(enabled=True)

    assert config.root_dir == tmp_path / "memory"


def test_chunker_prefers_paragraph_boundaries():
    chunker = KernelMemoryChunker(target_chars=120, overlap_chars=20, min_chars=40)

    chunks = chunker.chunk_text(
        "\n\n".join(
            [
                "Paragraph one talks about orbital mechanics and transfer windows in low earth orbit.",
                "Paragraph two explains Hohmann transfers and why they reduce delta-v requirements.",
                "Paragraph three captures caveats, phasing constraints, and mission timing details.",
            ]
        )
    )

    assert len(chunks) >= 2
    assert all(chunk.content for chunk in chunks)
    assert chunks[0].sequence == 0
    assert chunks[-1].span_end >= chunks[-1].span_start


def test_ingest_document_registers_corpus_and_chunks(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(
            enabled=True,
            root_dir=tmp_path / "kernel",
            namespace="research",
            document_chunk_target_chars=120,
            document_chunk_overlap_chars=20,
            document_chunk_min_chars=40,
        )
    )

    result = store.ingest_document(
        document_type="paper",
        title="Orbital Mechanics Notes",
        uri="file:///orbital-mechanics.txt",
        content="\n\n".join(
            [
                "Orbital mechanics uses transfer windows, inclination changes, and delta-v planning.",
                "Hohmann transfers are fuel efficient for many two-impulse orbit changes.",
                "Mission planners still need to account for phasing and operational constraints.",
            ]
        ),
        metadata={"topic": "space"},
    )

    documents = store.list_corpus_documents()
    stats = store.corpus_stats()
    extracts = store.list_records("extract")

    assert result["chunk_count"] >= 2
    assert len(documents) == 1
    assert documents[0]["resource_id"] == result["resource"]["id"]
    assert stats["documents_total"] == 1
    assert len(extracts) == result["chunk_count"]
    assert all(extract["metadata"]["document_id"] == documents[0]["document_id"] for extract in extracts)


def test_exact_source_required_routes_only_to_source_records(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(
            enabled=True,
            root_dir=tmp_path / "kernel",
            namespace="bestie",
            retrieval_policy_order=["curated", "semantic", "graph", "source"],
        )
    )
    store.materialize_curated_memory(
        title="Curated summary",
        summary="Hohmann transfers are a standard orbital maneuver.",
    )
    document = store.ingest_document(
        document_type="note",
        title="Flight dynamics notes",
        content="Hohmann transfers reduce fuel usage for many orbital transfers.",
    )

    result = store.retrieve_context_by_policy(
        "Please quote the source about Hohmann transfers",
        max_records=3,
        max_chars=600,
    )

    assert document["extract_ids"]
    assert result["response_mode"] == "exact_source_required"
    assert result["routes"] == ["source"]
    assert result["items"]
    assert all(item["kind"] in {"resource", "extract"} for item in result["items"])
    assert "Route: source" in result["text"]


def test_quote_domain_query_does_not_force_exact_source_mode(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(
            enabled=True,
            root_dir=tmp_path / "kernel",
            namespace="bestie",
            retrieval_policy_order=["curated", "semantic", "graph", "source"],
        )
    )

    assert store.classify_query_response_mode("What is the current favorite quote?") == "source_supported"


def test_corpus_ingest_queue_processes_background_jobs(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        corpus_ingest_max_jobs_per_cycle=2,
        document_chunk_target_chars=120,
        document_chunk_overlap_chars=20,
        document_chunk_min_chars=40,
    )
    queue = KernelMemoryCorpusIngestQueue(config)
    queued = queue.enqueue(
        namespace="bestie",
        document_type="note",
        title="Queued note",
        content="\n\n".join(
            [
                "A queued document about orbital transfers and delta-v planning.",
                "It should be chunked in the background daemon path.",
            ]
        ),
        metadata={"source": "queue"},
    )

    worker = KernelMemoryCorpusIngestWorker(config)
    result = worker.process_once()
    store = KernelMemoryStore.from_config(config)

    assert queued["status"] == "queued"
    assert result["processed"] == 1
    assert result["failed"] == 0
    assert result["queue"]["processed"] == 1
    assert store.corpus_stats()["documents_total"] == 1
    assert store.list_corpus_documents()[0]["title"] == "Queued note"


def test_corpus_ingest_queue_retries_and_requeues_failed_jobs(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        corpus_ingest_max_retries=1,
    )
    queue = KernelMemoryCorpusIngestQueue(config)
    queued = queue.enqueue(
        namespace="bestie",
        document_type="note",
        title="Broken note",
        content="will fail",
    )
    job_path = queue.list_outbox()[0]
    job_payload = json.loads(job_path.read_text(encoding="utf-8"))
    job_payload["content"] = ""
    job_path.write_text(json.dumps(job_payload, ensure_ascii=False, sort_keys=True), encoding="utf-8")

    worker = KernelMemoryCorpusIngestWorker(config, max_delivery_attempts=1)
    first = worker.process_once()

    assert first["failed"] == 1
    failed_jobs = queue.list_jobs("failed")
    assert failed_jobs and failed_jobs[0]["job_id"] == queued["job_id"]

    replayed = queue.requeue_job(queued["job_id"], source_bucket="failed")
    assert replayed["status"] == "queued"
