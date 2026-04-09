from __future__ import annotations

from agent.kernel_memory import KernelMemoryConfig, KernelMemoryStore
from agent.kernel_memory_contracts import build_kernel_memory_event
from agent.kernel_memory_pipeline import KernelMemoryWriteService
from agent.kernel_memory_recompile import KernelMemoryDeterministicRecompileService


def _build_fixture(config: KernelMemoryConfig) -> None:
    service = KernelMemoryWriteService(config)
    turn_event = build_kernel_memory_event(
        event_type="assistant_turn_completed",
        payload={
            "session_id": "sess-1",
            "user_message": "Laura 2026. február 22-én megsérült és most ő a fő prioritás.",
            "assistant_response": "Rendben, Laura állapotát érzékeny és kiemelt témaként kezelem.",
            "model": "minimax-m2.7",
        },
        namespace_id="bestie",
        agent_id="bestie",
        source_session_id="sess-1",
        timestamp="2026-02-23T12:00:00+00:00",
    )
    service.process_event(turn_event)

    research_event = build_kernel_memory_event(
        event_type="deep_research_completed",
        payload={
            "query": "Orbital transfer planning",
            "report": (
                "Orbital transfer planning often uses Hohmann transfers. "
                "Mars missions depend on launch windows and transfer timing.\n\n"
                "NASA planning may depend on Earth-Mars alignment and fuel constraints."
            ),
            "preset": "deep",
            "report_type": "research_report",
        },
        namespace_id="bestie",
        agent_id="bestie",
        source_session_id="sess-r1",
        timestamp="2026-02-24T12:00:00+00:00",
    )
    service.process_event(research_event)


def test_deterministic_recompile_matches_live_store(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
    )
    _build_fixture(config)

    result = KernelMemoryDeterministicRecompileService(config).run(apply=False)

    assert result["status"] == "ok"
    assert result["comparison"]["ok"] is True
    assert len(result["processed_resources"]) == 2
    assert result["truth_kinds"] == ["resource", "extract"]


def test_deterministic_recompile_apply_repairs_structural_drift(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
    )
    _build_fixture(config)
    store = KernelMemoryStore.from_config(config)
    claim = next(record for record in store.list_records("claim") if "Laura" in str(record.get("content") or ""))
    original_content = str(claim["content"])
    store._records["claim"][claim["id"]]["content"] = "BROKEN DRIFTED CLAIM"
    store._persist_derived_kind("claim")

    result = KernelMemoryDeterministicRecompileService(config).run(apply=True)
    repaired_store = KernelMemoryStore.from_config(config)
    repaired_claim = repaired_store.get_record("claim", claim["id"])

    assert result["comparison"]["ok"] is True
    assert result["classification"]["status"] == "clean"
    assert result["applied"] is not None
    assert repaired_claim is not None
    assert repaired_claim["content"] == original_content


def test_deterministic_recompile_blocks_auto_apply_when_provenance_gap_exists(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
    )
    _build_fixture(config)
    store = KernelMemoryStore.from_config(config)
    event = next(record for record in store.list_records("event") if "Laura" in str(record.get("summary") or ""))
    store._records["event"][event["id"]]["summary"] = "BROKEN EVENT DRIFT"
    store._records["event"][event["id"]]["source_ids"] = ["missing-resource"]
    store._persist_derived_kind("event")

    result = KernelMemoryDeterministicRecompileService(config).run(apply=True)
    repaired_store = KernelMemoryStore.from_config(config)
    repaired_event = repaired_store.get_record("event", event["id"])

    assert result["comparison"]["ok"] is False
    assert result["classification"]["status"] == "provenance_gap"
    assert result["classification"]["auto_apply_safe"] is False
    assert result["classification"]["provenance_gap_count"] > 0
    assert result["applied"] == {
        "status": "skipped",
        "reason": "provenance_gap",
        "reason_codes": ["derived_drift", "provenance_gap"],
    }
    assert repaired_event is not None
    assert repaired_event["summary"] == "BROKEN EVENT DRIFT"
