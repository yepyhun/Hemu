from __future__ import annotations

from agent.kernel_memory import KernelMemoryConfig, KernelMemoryStore
from agent.kernel_memory_prewarm import KernelMemoryRetrievalPrewarmService
from agent.kernel_memory_retrieval import KernelMemoryRetriever


def test_prewarm_service_warms_cache_and_reuses_existing_entry(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        hybrid_retrieval_enabled=True,
        embedding_index_enabled=True,
        embedding_provider="deterministic",
    )
    store = KernelMemoryStore.from_config(config)
    store.materialize_curated_memory(
        title="Prewarm note",
        summary="Kernel memory prewarm should cache orbital mechanics recall.",
    )
    service = KernelMemoryRetrievalPrewarmService(
        config,
        store,
        KernelMemoryRetriever(config, store),
    )

    queued = service.enqueue_query("orbital mechanics", namespaces={"bestie"})
    first = service.process_queue(max_jobs=1)
    second = service.prewarm_query("orbital mechanics", namespaces={"bestie"})

    assert queued["status"] == "queued"
    assert first["processed"] == 1
    assert first["cache_writes"] == 1
    assert second["status"] == "cached"
    assert service.cache.stats()["entries"] >= 1
