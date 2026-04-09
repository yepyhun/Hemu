from __future__ import annotations

from agent.kernel_memory import KernelMemoryConfig, KernelMemoryStore
from agent.kernel_memory_contracts import build_kernel_memory_event
from agent.kernel_memory_pipeline import KernelMemoryWriteService


def test_materialize_support_projections_reuses_existing_owner_projection(tmp_path, monkeypatch):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
    )
    service = KernelMemoryWriteService(config)
    store = KernelMemoryStore.from_config(config)
    claim = store.ingest_claim(
        claim_type="user_preference",
        content="I prefer concise answers.",
        metadata={"session_id": "s1", "origin": "assistant_turn_completed"},
        confidence=0.9,
    )
    existing_projection = store.get_support_projection(owner_kind="claim", owner_id=claim["id"])
    assert existing_projection is not None

    def _unexpected_compile(_record):
        raise AssertionError("compile_support_projections should not run for owners that already have a projection")

    monkeypatch.setattr("agent.kernel_memory_pipeline.compile_support_projections", _unexpected_compile)
    event = build_kernel_memory_event(
        event_type="assistant_turn_completed",
        payload={"session_id": "s1", "user_message": "x", "assistant_response": "y"},
        namespace_id="bestie",
        agent_id="bestie",
    )

    projection_ids = service._materialize_support_projections(
        store=store,
        records=[claim],
        event=event,
    )

    assert projection_ids == [existing_projection["id"]]
