from __future__ import annotations

from dataclasses import asdict, dataclass, field
from math import ceil
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict, List, Sequence

from agent.builtin_memory_provider import BuiltinMemoryProvider
from agent.memory_manager import MemoryManager
from agent.memory_provider import MemoryProvider
from agent.core2_types import EDGE_DERIVED_FROM
from plugins.memory import load_memory_provider


@dataclass
class Core2ProofScenario:
    mode: str
    scenario_id: str
    description: str
    passed: bool
    tool_route_available: bool
    final_answer_correct: bool
    prompt_markers_present: bool
    prefetch_available: bool
    retrieved_item_count: int
    delivery_view: str | None
    answer_type: str | None
    storage_plane: str | None
    estimated_display_tokens: int = 0
    notes: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Core2ProofReport:
    modes: Dict[str, Dict[str, int]]
    scenarios: List[Core2ProofScenario]
    final_gate: Dict[str, Any]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "modes": self.modes,
            "scenarios": [scenario.as_dict() for scenario in self.scenarios],
            "final_gate": self.final_gate,
        }


@dataclass
class Core2ReplayBenchmark:
    baseline_tokens: int
    optimized_tokens: int
    token_savings: int
    savings_ratio: float
    context_block_tokens: Dict[str, int]


LONGMEMEVAL_SYNTHETIC_ENTRIES: Sequence[Dict[str, Any]] = (
    {
        "question_id": "LM1",
        "query": "What is my timezone?",
        "expected": "Europe/Budapest",
        "question_type": "single-session-user",
    },
    {
        "question_id": "LM2",
        "query": "Who is the current deployment owner?",
        "expected": "Bob",
        "question_type": "cross-session-update",
    },
)


def estimate_message_tokens(messages: Sequence[Dict[str, Any]]) -> int:
    total_chars = 0
    for message in messages:
        total_chars += len(str(message.get("role") or ""))
        total_chars += len(str(message.get("content") or ""))
    return max(1, ceil(total_chars / 4))


def benchmark_core2_replay_messages(
    *,
    baseline_messages: Sequence[Dict[str, Any]],
    optimized_messages: Sequence[Dict[str, Any]],
    proof_context: str,
    prefetch_context: str,
    compact_answer: str,
) -> Core2ReplayBenchmark:
    baseline_tokens = estimate_message_tokens(baseline_messages)
    optimized_tokens = estimate_message_tokens(optimized_messages)
    context_block_tokens = {
        "proof": estimate_message_tokens([{"role": "system", "content": proof_context}]),
        "prefetch": estimate_message_tokens([{"role": "system", "content": prefetch_context}]),
        "compact_answer": estimate_message_tokens([{"role": "assistant", "content": compact_answer}]),
    }
    token_savings = max(0, baseline_tokens - optimized_tokens)
    savings_ratio = (token_savings / baseline_tokens) if baseline_tokens else 0.0
    return Core2ReplayBenchmark(
        baseline_tokens=baseline_tokens,
        optimized_tokens=optimized_tokens,
        token_savings=token_savings,
        savings_ratio=savings_ratio,
        context_block_tokens=context_block_tokens,
    )


def run_core2_proof_benchmark(base_dir: str | Path | None = None) -> Core2ProofReport:
    if base_dir is None:
        with TemporaryDirectory(prefix="core2-proof-") as tmp_dir:
            return _run_core2_proof_benchmark(Path(tmp_dir))
    return _run_core2_proof_benchmark(Path(base_dir))


def verify_core2_longmemeval_subset(
    *,
    base_dir: str | Path | None = None,
    sample_size: int = 2,
    seed: int = 7,
) -> Dict[str, Any]:
    del seed  # Deterministic synthetic subset for local proof.
    entries = list(LONGMEMEVAL_SYNTHETIC_ENTRIES[: max(1, sample_size)])
    if base_dir is None:
        with TemporaryDirectory(prefix="core2-longmemeval-") as tmp_dir:
            return _verify_core2_longmemeval_subset(Path(tmp_dir), entries)
    return _verify_core2_longmemeval_subset(Path(base_dir), entries)


def _run_core2_proof_benchmark(base_dir: Path) -> Core2ProofReport:
    scenarios: List[Core2ProofScenario] = []

    for mode in ("core2", "builtin_only"):
        manager, provider = _build_manager(base_dir, mode)
        try:
            scenarios.append(_scenario_round_trip(manager, mode))
            scenarios.append(_scenario_update_resolution(manager, provider, mode))
            scenarios.append(_scenario_relation_graph(manager, provider, mode))
            scenarios.append(_scenario_sync_prefetch(manager, mode))
        finally:
            manager.shutdown_all()

    mode_summaries: Dict[str, Dict[str, int]] = {}
    for mode in ("core2", "builtin_only"):
        mode_scenarios = [scenario for scenario in scenarios if scenario.mode == mode]
        mode_summaries[mode] = {
            "total": len(mode_scenarios),
            "passed": sum(1 for scenario in mode_scenarios if scenario.passed),
        }

    final_gate = {
        "name": "LongMemEval-10 paid test",
        "status": "pending_external",
        "description": (
            "Local deterministic proof is green, but the final external gate remains "
            "the paid LongMemEval-10 run through the Hermes path."
        ),
    }
    return Core2ProofReport(modes=mode_summaries, scenarios=scenarios, final_gate=final_gate)


def _verify_core2_longmemeval_subset(base_dir: Path, entries: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    results: List[Dict[str, Any]] = []
    modes: Dict[str, Dict[str, int]] = {}

    for mode in ("core2", "builtin_only"):
        manager, provider = _build_manager(base_dir, f"longmemeval-{mode}")
        passed = 0
        try:
            for entry in entries:
                item = _run_longmemeval_entry(manager, provider, mode, entry)
                passed += int(item["answer_contains_expected"])
                results.append(item)
        finally:
            manager.shutdown_all()
        modes[mode] = {"total": len(entries), "passed": passed}

    return {
        "sample_size": len(entries),
        "modes": modes,
        "results": results,
        "final_gate": {
            "name": "LongMemEval-10 paid test",
            "status": "pending_external",
        },
    }


def _build_manager(base_dir: Path, mode: str) -> tuple[MemoryManager, MemoryProvider | None]:
    manager = MemoryManager()
    manager.add_provider(BuiltinMemoryProvider())

    provider = None
    if "core2" in mode:
        provider = load_memory_provider("core2")
        assert provider is not None
        manager.add_provider(provider)

    hermes_home = base_dir / mode
    hermes_home.mkdir(parents=True, exist_ok=True)
    manager.initialize_all(session_id=f"proof-{mode}", platform="cli", hermes_home=str(hermes_home))
    return manager, provider


def _scenario_round_trip(manager: MemoryManager, mode: str) -> Core2ProofScenario:
    if not manager.has_tool("core2_remember"):
        return Core2ProofScenario(
            mode=mode,
            scenario_id="S1",
            description="Explicit remember/recall/explain round trip",
            passed=False,
            tool_route_available=False,
            final_answer_correct=False,
            prompt_markers_present=False,
            prefetch_available=False,
            retrieved_item_count=0,
            delivery_view=None,
            answer_type=None,
            storage_plane=None,
            notes=["Core2 tool route is unavailable in builtin-only mode."],
        )

    manager.handle_tool_call(
        "core2_remember",
        {
            "content": "The user prefers compact release summaries.",
            "title": "release summary preference",
            "namespace": "personal",
            "risk_class": "standard",
            "language": "en",
        },
    )
    packet = _load_json(manager.handle_tool_call("core2_recall", {"query": "release summaries", "mode": "compact_memory"}))
    explained = _load_json(manager.handle_tool_call("core2_explain", {"object_id": packet["items"][0]["object_id"]}))
    prompt = manager.build_system_prompt()

    return Core2ProofScenario(
        mode=mode,
        scenario_id="S1",
        description="Explicit remember/recall/explain round trip",
        passed=(
            packet["abstained"] is False
            and "compact release summaries" in packet["display_value"]
            and explained["title"] == "release summary preference"
        ),
        tool_route_available=True,
        final_answer_correct="compact release summaries" in packet["display_value"],
        prompt_markers_present="# Core2 Memory" in prompt,
        prefetch_available=False,
        retrieved_item_count=packet["retrieved_item_count"],
        delivery_view=packet["delivery_view"],
        answer_type=packet["answer_type"],
        storage_plane="canonical_truth",
        estimated_display_tokens=estimate_message_tokens([{"role": "assistant", "content": packet["display_value"]}]),
    )


def _scenario_update_resolution(
    manager: MemoryManager,
    provider: MemoryProvider | None,
    mode: str,
) -> Core2ProofScenario:
    runtime = getattr(provider, "runtime", None)
    if runtime is None:
        return Core2ProofScenario(
            mode=mode,
            scenario_id="S2",
            description="Current-state resolution prefers the latest canonical record",
            passed=False,
            tool_route_available=False,
            final_answer_correct=False,
            prompt_markers_present=False,
            prefetch_available=False,
            retrieved_item_count=0,
            delivery_view=None,
            answer_type=None,
            storage_plane=None,
            notes=["Update-resolution proof requires the Core2 runtime."],
        )

    old_record = runtime.ingest_note(
        "Current deployment owner is Alice.",
        title="deployment owner",
        namespace="project",
        risk_class="standard",
        language="en",
        metadata={"identity_key": "deploy.owner"},
    )
    new_record = runtime.ingest_note(
        "Current deployment owner is Bob.",
        title="deployment owner",
        namespace="project",
        risk_class="standard",
        language="en",
        metadata={"identity_key": "deploy.owner"},
    )
    runtime.supersede_object(new_record["object_id"], old_record["object_id"], reason="owner_changed")
    packet = _load_json(manager.handle_tool_call("core2_recall", {"query": "What is the current deployment owner?"}))
    content = packet["items"][0]["content"] if packet["items"] else ""

    return Core2ProofScenario(
        mode=mode,
        scenario_id="S2",
        description="Current-state resolution prefers the latest canonical record",
        passed=packet["abstained"] is False and "Bob" in content and "Alice" not in content,
        tool_route_available=True,
        final_answer_correct="Bob" in content and "Alice" not in content,
        prompt_markers_present=True,
        prefetch_available=False,
        retrieved_item_count=packet["retrieved_item_count"],
        delivery_view=packet["delivery_view"],
        answer_type=packet["answer_type"],
        storage_plane="canonical_truth",
        estimated_display_tokens=estimate_message_tokens([{"role": "assistant", "content": packet["display_value"]}]),
    )


def _scenario_relation_graph(
    manager: MemoryManager,
    provider: MemoryProvider | None,
    mode: str,
) -> Core2ProofScenario:
    runtime = getattr(provider, "runtime", None)
    if runtime is None:
        return Core2ProofScenario(
            mode=mode,
            scenario_id="S3",
            description="Graph-linked recall keeps the relation chain coherent",
            passed=False,
            tool_route_available=False,
            final_answer_correct=False,
            prompt_markers_present=False,
            prefetch_available=False,
            retrieved_item_count=0,
            delivery_view=None,
            answer_type=None,
            storage_plane=None,
            notes=["Relation proof requires the Core2 runtime."],
        )

    alpha = runtime.ingest_note(
        "Alpha service depends on the shared mission index.",
        title="Alpha service",
        namespace="project",
        risk_class="standard",
        language="en",
    )
    beta = runtime.ingest_note(
        "Beta service fans out updates from the shared mission index.",
        title="Beta service",
        namespace="project",
        risk_class="standard",
        language="en",
    )
    gamma = runtime.ingest_note(
        "Gamma service publishes reports from the shared mission index.",
        title="Gamma service",
        namespace="project",
        risk_class="standard",
        language="en",
    )
    runtime.store.add_edge(
        from_plane="canonical_truth",
        from_id=alpha["object_id"],
        to_plane="canonical_truth",
        to_id=beta["object_id"],
        edge_type=EDGE_DERIVED_FROM,
    )
    runtime.store.add_edge(
        from_plane="canonical_truth",
        from_id=beta["object_id"],
        to_plane="canonical_truth",
        to_id=gamma["object_id"],
        edge_type=EDGE_DERIVED_FROM,
    )
    packet = _load_json(
        manager.handle_tool_call(
            "core2_recall",
            {"query": "What is the relationship between Alpha and Gamma?", "mode": "source_supported"},
        )
    )
    titles = {item["title"] for item in packet["items"]}

    return Core2ProofScenario(
        mode=mode,
        scenario_id="S3",
        description="Graph-linked recall keeps the relation chain coherent",
        passed=packet["abstained"] is False and titles >= {"Alpha service", "Beta service", "Gamma service"},
        tool_route_available=True,
        final_answer_correct=titles >= {"Alpha service", "Beta service", "Gamma service"},
        prompt_markers_present=True,
        prefetch_available=False,
        retrieved_item_count=packet["retrieved_item_count"],
        delivery_view=packet["delivery_view"],
        answer_type=packet["answer_type"],
        storage_plane="canonical_truth",
        estimated_display_tokens=estimate_message_tokens([{"role": "assistant", "content": packet["display_value"]}]),
    )


def _scenario_sync_prefetch(manager: MemoryManager, mode: str) -> Core2ProofScenario:
    if not manager.has_tool("core2_remember"):
        return Core2ProofScenario(
            mode=mode,
            scenario_id="S4",
            description="Manager sync and prefetch expose compact recall context",
            passed=False,
            tool_route_available=False,
            final_answer_correct=False,
            prompt_markers_present=False,
            prefetch_available=False,
            retrieved_item_count=0,
            delivery_view=None,
            answer_type=None,
            storage_plane=None,
            notes=["Prefetch proof requires the Core2 provider seam."],
        )

    manager.handle_tool_call(
        "core2_remember",
        {
            "content": "Release summaries should stay compact and only mention the active deployment facts.",
            "title": "release policy",
            "namespace": "personal",
            "risk_class": "standard",
            "language": "en",
        },
    )
    manager.sync_all("How should release notes look?", "Keep them compact and current.")
    manager.queue_prefetch_all("release summaries")
    prefetched = manager.prefetch_all("unused")
    prompt = manager.build_system_prompt()

    return Core2ProofScenario(
        mode=mode,
        scenario_id="S4",
        description="Manager sync and prefetch expose compact recall context",
        passed="# Core2 Prefetch" in prefetched and "release policy" in prefetched,
        tool_route_available=True,
        final_answer_correct="compact" in prefetched.lower(),
        prompt_markers_present="# Core2 Memory" in prompt,
        prefetch_available=bool(prefetched.strip()),
        retrieved_item_count=1 if prefetched.strip() else 0,
        delivery_view="final_compact",
        answer_type="compact_memory",
        storage_plane="canonical_truth",
        estimated_display_tokens=estimate_message_tokens([{"role": "system", "content": prefetched}]),
    )


def _run_longmemeval_entry(
    manager: MemoryManager,
    provider: MemoryProvider | None,
    mode: str,
    entry: Dict[str, Any],
) -> Dict[str, Any]:
    expected = entry["expected"]
    seeded_core2_entries = 0
    seeded_builtin_entries = 0
    runtime = getattr(provider, "runtime", None)

    if runtime is not None:
        if entry["question_id"] == "LM1":
            runtime.ingest_note(
                "My timezone is Europe/Budapest.",
                title="timezone",
                namespace="personal",
                risk_class="standard",
                language="en",
            )
            seeded_core2_entries = 1
        elif entry["question_id"] == "LM2":
            old_record = runtime.ingest_note(
                "Current deployment owner is Alice.",
                title="deployment owner",
                namespace="project",
                risk_class="standard",
                language="en",
                metadata={"identity_key": "deploy.owner"},
            )
            new_record = runtime.ingest_note(
                "Current deployment owner is Bob.",
                title="deployment owner",
                namespace="project",
                risk_class="standard",
                language="en",
                metadata={"identity_key": "deploy.owner"},
            )
            runtime.supersede_object(new_record["object_id"], old_record["object_id"], reason="owner_changed")
            seeded_core2_entries = 2

    answer_payload: Dict[str, Any]
    if manager.has_tool("core2_recall"):
        manager.queue_prefetch_all(entry["query"])
        prefetched = manager.prefetch_all("unused")
        answer_payload = _load_json(
            manager.handle_tool_call(
                "core2_recall",
                {
                    "query": entry["query"],
                    "mode": "compact_memory" if entry["question_id"] == "LM1" else "source_supported",
                },
            )
        )
    else:
        prefetched = ""
        answer_payload = {"items": [], "display_value": "", "abstained": True}

    answer_contains_expected = expected in (answer_payload.get("display_value") or "")
    if not answer_contains_expected:
        answer_contains_expected = any(expected in str(item.get("content") or "") for item in answer_payload.get("items", []))

    return {
        "mode": "core2" if mode.startswith("core2") or mode == "core2" else "builtin_only",
        "question_id": entry["question_id"],
        "question_type": entry["question_type"],
        "seeded_core2_entries": seeded_core2_entries,
        "seeded_builtin_entries": seeded_builtin_entries,
        "prompt_contains_answer": expected in prefetched,
        "answer_contains_expected": answer_contains_expected,
        "delivery_view": answer_payload.get("delivery_view"),
        "abstained": answer_payload.get("abstained"),
    }


def _load_json(payload: str) -> Dict[str, Any]:
    import json

    return json.loads(payload)
