from __future__ import annotations

from agent.kernel_memory import KernelMemoryConfig, KernelMemoryStore
from agent.kernel_memory_quality import KernelMemoryQualityStore
from agent.kernel_memory_retrieval import KernelMemoryRetriever
from agent.kernel_memory_validation import KernelMemoryValidationSuite


def test_validation_suite_runs_domain_and_stability_checks(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        validation_suite_enabled=True,
        validation_suite_stability_runs=2,
    )
    store = KernelMemoryStore.from_config(config)
    store.ingest_document(
        document_type="note",
        title="Medical recall",
        content="Dosage adjustments should always preserve the exact source note.",
    )
    quality = KernelMemoryQualityStore(config)
    suite = KernelMemoryValidationSuite(config, KernelMemoryRetriever(config, store), quality)
    suite.add_case(
        name="medical-source",
        domain="medical",
        query="source note dosage adjustments",
        expected_substrings=["exact source note"],
        expected_response_mode="exact_source_required",
        tags=["leakage"],
    )

    result = suite.run()

    assert result["total_cases"] == 1
    assert result["passed"] == 1
    assert result["stability_failures"] == 0
    assert result["by_tag"]["leakage"]["passed"] == 1
    assert quality.read_snapshot()["last_validation_suite"]["passed"] == 1
