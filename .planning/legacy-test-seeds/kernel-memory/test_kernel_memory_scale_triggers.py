from __future__ import annotations

from agent.kernel_memory import KernelMemoryConfig
from agent.kernel_memory_scale_triggers import KernelMemoryScaleTriggerEvaluator


def test_scale_triggers_flag_storage_and_broker_candidates(tmp_path):
    config = KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel", namespace="bestie")
    evaluator = KernelMemoryScaleTriggerEvaluator(config)

    result = evaluator.evaluate(
        health={
            "corpus_documents": {"documents_total": 12000},
            "queue": {"queued": 20, "failed": 0},
            "corpus_queue": {"queued": 20, "failed": 3},
            "embedding_queue": {"queued": 15, "failed": 4},
            "consolidation_queue": {"queued": 5, "failed": 3},
            "prewarm_queue": {"queued": 2, "failed": 0},
        }
    )

    assert result["storage_split_candidate"] is True
    assert result["broker_evolution_candidate"] is True
