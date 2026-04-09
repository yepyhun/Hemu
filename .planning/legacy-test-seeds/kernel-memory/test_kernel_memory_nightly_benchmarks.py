from __future__ import annotations

from agent.kernel_memory import KernelMemoryConfig, KernelMemoryStore
from agent.kernel_memory_admin import KernelMemoryGoldenSet
from agent.kernel_memory_nightly_benchmarks import KernelMemoryNightlyBenchmarkService
from agent.kernel_memory_quality import KernelMemoryQualityStore
from agent.kernel_memory_retrieval import KernelMemoryRetriever


def test_nightly_benchmarks_aggregate_golden_and_compression_metrics(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
    )
    store = KernelMemoryStore.from_config(config)
    store.materialize_curated_memory(
        title="Project task",
        summary="Migration rollback safety should remain explicit in the project task memory.",
        metadata={"memory_class": "project_task"},
    )
    quality = KernelMemoryQualityStore(config)
    retriever = KernelMemoryRetriever(config, store)
    golden = KernelMemoryGoldenSet(config, store, retriever, quality)
    golden.add_case(
        name="migration-task",
        query="migration task",
        expected_substrings=["rollback"],
    )

    service = KernelMemoryNightlyBenchmarkService(config, golden, retriever, quality)
    result = service.run(max_cases=5)

    assert result["total_cases"] == 1
    assert result["passed"] == 1
    assert result["average_compression_ratio"] >= 0.0
