from __future__ import annotations

from agent.kernel_memory import KernelMemoryConfig
from agent.kernel_memory_retrieval_cache import KernelMemoryRetrievalCache


def test_retrieval_cache_invalidates_by_namespace_revision(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        retrieval_cache_enabled=True,
    )
    cache = KernelMemoryRetrievalCache(config)
    plan = {
        "query": "orbital mechanics",
        "normalized_query": "orbital mechanics",
        "response_mode": "source_supported",
        "budget_profile": "short_query",
        "max_records": 3,
        "max_chars": 900,
        "routes": [{"route": "curated"}],
        "fusion": {"policy": "weighted_rrf", "rrf_k": 40},
    }
    result = {
        "items": [{"id": "cur-1", "route": "curated"}],
        "text": "Hohmann transfer appears in cacheable retrieval text.",
        "routes": ["curated"],
        "response_mode": "source_supported",
        "plan": plan,
    }

    cache.put(plan=plan, namespaces={"bestie"}, result=result)
    cached = cache.get(plan=plan, namespaces={"bestie"})

    assert cached is not None
    assert cached["cache"]["status"] == "hit"

    cache.bump_namespaces({"bestie"}, reason="test")
    assert cache.get(plan=plan, namespaces={"bestie"}) is None

    pruned = cache.prune()
    assert pruned["removed"] >= 1
