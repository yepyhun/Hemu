from __future__ import annotations

from agent.kernel_memory import KernelMemoryConfig, KernelMemoryStore
from agent.kernel_memory_namespace_policy import KernelMemoryNamespacePolicy


def test_bestie_all_scope_sees_all_namespaces(tmp_path):
    bestie_config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        retrieval_scopes=["all"],
        shared_namespaces=["shared.global"],
    )
    store = KernelMemoryStore.from_config(bestie_config)
    store.materialize_curated_memory(title="Bestie memory", summary="Main memory")
    lulu_store = KernelMemoryStore.from_config({**bestie_config.as_config_dict(), "namespace": "lulu"})
    lulu_store.materialize_curated_memory(title="Lulu memory", summary="Therapy memory")

    namespaces = KernelMemoryNamespacePolicy(bestie_config, store).resolve_retrieval_namespaces()

    assert "bestie" in namespaces
    assert "lulu" in namespaces


def test_explicit_shared_scope_preserves_boundaries(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="lulu",
        retrieval_scopes=["self", "shared", "bestie"],
        shared_namespaces=["shared.global"],
    )
    policy = KernelMemoryNamespacePolicy(config)

    namespaces = policy.resolve_retrieval_namespaces()

    assert namespaces == {"lulu", "shared.global", "bestie"}
