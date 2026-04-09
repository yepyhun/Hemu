from __future__ import annotations

import json
from unittest.mock import MagicMock

import run_agent
from pathlib import Path
from tempfile import TemporaryDirectory

from agent.hermes_longmemeval_benchmark import (
    DEFAULT_BENCHMARK_BASE_URL,
    DEFAULT_BENCHMARK_MODEL,
    DEFAULT_BENCHMARK_PROVIDER,
    DEFAULT_DATASET,
    _seed_custom_kernel,
    _session_event_timestamp,
    run_hermes_longmemeval_generation,
    verify_hermes_longmemeval_subset,
)
from agent.kernel_memory import KernelMemoryConfig, KernelMemoryStore


def test_verify_hermes_longmemeval_subset_custom_kernel_reaches_prompt():
    report = verify_hermes_longmemeval_subset(sample_size=2, seed=7)

    assert report["sample_size"] == 2
    assert report["modes"]["custom"]["total"] == 2
    assert report["modes"]["native"]["total"] == 2
    assert report["modes"]["custom"]["passed"] >= 1

    results = {(item["mode"], item["question_id"]): item for item in report["results"]}
    custom_items = [item for item in report["results"] if item["mode"] == "custom"]
    native_items = [item for item in report["results"] if item["mode"] == "native"]

    assert all(item["seeded_kernel_entries"] > 0 for item in custom_items)
    assert all(item["seeded_native_entries"] >= 0 for item in native_items)
    assert any(item["prompt_contains_answer"] for item in custom_items)


def test_run_generation_uses_explicit_cometapi_provider(monkeypatch):
    captured: dict[str, object] = {}

    class FakeAgent:
        def __init__(self, **kwargs):
            captured.update(kwargs)
            self._cleanup_task_resources = lambda task_id: None
            self._persist_session = lambda messages, history=None: None
            self._save_trajectory = lambda messages, user_message, completed: None
            self._save_session_log = lambda messages: None

        def _interruptible_api_call(self, api_kwargs):
            return MagicMock()

        def run_conversation(self, user_message):
            return {"final_response": "ok"}

    monkeypatch.setattr(run_agent, "AIAgent", FakeAgent)
    monkeypatch.setattr(run_agent, "get_tool_definitions", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(run_agent, "check_toolset_requirements", lambda *_args, **_kwargs: {})

    result = run_hermes_longmemeval_generation(
        entry={
            "question_id": "q1",
            "question": "Who is the user?",
            "answer": "Tomi",
            "haystack_dates": ["2026-01-01"],
            "haystack_sessions": [[{"role": "user", "content": "My name is Tomi."}]],
            "question_type": "single-session-user",
        },
        mode="custom",
        model=DEFAULT_BENCHMARK_MODEL,
        base_url=DEFAULT_BENCHMARK_BASE_URL,
        api_key="test-key",
        provider=DEFAULT_BENCHMARK_PROVIDER,
    )

    assert captured["provider"] == DEFAULT_BENCHMARK_PROVIDER
    assert captured["base_url"] == DEFAULT_BENCHMARK_BASE_URL
    assert captured["model"] == DEFAULT_BENCHMARK_MODEL
    assert result.provider == DEFAULT_BENCHMARK_PROVIDER
    assert result.base_url == DEFAULT_BENCHMARK_BASE_URL
    assert result.model == DEFAULT_BENCHMARK_MODEL


def test_session_event_timestamp_parses_benchmark_session_datetime():
    stamped = _session_event_timestamp("2023/01/17 (Tue) 18:10", offset_minutes=2)

    assert stamped is not None
    assert stamped.startswith("2023-01-17T18:12:")


def test_seed_custom_kernel_links_continuation_money_claim_into_event():
    entries = json.loads(Path(DEFAULT_DATASET).read_text(encoding="utf-8"))
    entry = next(item for item in entries if item["question_id"] == "36b9f61e")

    with TemporaryDirectory() as tmp_dir:
        home = Path(tmp_dir)
        _seed_custom_kernel(home, entry, oracle_only=True)
        store = KernelMemoryStore.from_config(
            KernelMemoryConfig(
                enabled=True,
                root_dir=home / "state" / "kernel_memory",
                namespace="longmemeval",
            )
        )

        gown_event = next(
            event
            for event in store.list_records("event")
            if "evening gown" in str(event.get("summary") or "").lower()
        )
        linked_claims = [
            store.get_record("claim", claim_id)
            for claim_id in gown_event.get("claim_ids") or []
        ]

        assert any(claim and "$800" in str(claim.get("content") or "") for claim in linked_claims)
