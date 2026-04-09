from __future__ import annotations

import logging

from agent.kernel_memory import KernelMemoryConfig, KernelMemoryStore
from agent.kernel_memory_embeddings import KernelMemoryEmbeddingIndexService
from agent.kernel_memory_retrieval import KernelMemoryRetriever
from agent.kernel_memory_runtime import KernelMemoryRuntime


def test_embedding_index_discovers_and_indexes_extracts(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        hybrid_retrieval_enabled=True,
        embedding_index_enabled=True,
        embedding_provider="deterministic",
    )
    store = KernelMemoryStore.from_config(config)
    document = store.ingest_document(
        document_type="note",
        title="Orbital notebook",
        content="Hohmann transfer windows help orbital mission planning.",
    )
    assert document["extract_ids"]

    service = KernelMemoryEmbeddingIndexService(config, store)
    discovery = service.discover_missing()
    processing = service.process_queue(max_jobs=8)
    stats = service.index.stats()

    assert discovery["queued"] >= 1
    assert processing["processed"] >= 1
    assert stats["rows"] >= 1
    assert stats["by_kind"]["extract"] >= 1


def test_hybrid_retriever_can_return_indexed_extract_without_claims(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        retrieval_policy_order=["semantic"],
        hybrid_retrieval_enabled=True,
        embedding_index_enabled=True,
        embedding_provider="deterministic",
    )
    store = KernelMemoryStore.from_config(config)
    store.ingest_document(
        document_type="note",
        title="Mars notes",
        content="Ares mission planning depends on launch windows and transfer timing.",
    )
    retriever = KernelMemoryRetriever(config, store)
    retriever.embeddings.run_cycle(max_jobs=8, discover_limit=20)

    result = retriever.retrieve_context_by_policy(
        "launch windows and transfer timing",
        max_records=2,
        max_chars=500,
        namespaces={"bestie"},
        route_order=["semantic"],
    )

    assert result["routes"] == ["semantic"]
    assert result["items"]
    assert any(item.get("retrieval_method") == "vector" for item in result["items"])
    assert "launch windows" in result["text"]


def test_runtime_hybrid_retrieval_falls_back_cleanly_when_provider_unavailable(tmp_path):
    runtime = KernelMemoryRuntime.from_agent_config(
        {
            "enabled": True,
            "root_dir": str(tmp_path / "kernel"),
            "hybrid_retrieval_enabled": True,
            "embedding_index_enabled": True,
            "embedding_provider": "openai_compatible",
            "embedding_base_url": "http://127.0.0.1:9/v1",
            "retrieval_policy_order": ["semantic"],
            "retrieval_min_query_chars": 3,
        },
        skip_memory=False,
        logger=logging.getLogger("test.kernel_memory_runtime"),
    )
    assert runtime.store is not None
    runtime.store.materialize_curated_memory(
        title="Fallback note",
        summary="Lexical fallback should still work when the embedding provider is unavailable.",
    )

    context = runtime.retrieve_turn_context(
        "embedding provider unavailable fallback",
        logger=logging.getLogger("test.kernel_memory_runtime"),
    )

    assert "Lexical fallback should still work" in context
