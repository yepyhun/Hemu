"""Foundation lifecycle tests for the Core2 provider.

Adapted from the legacy bootstrap/runtime/store-ops/admin coverage, but kept
small and Phase-1-specific so the active suite only enforces current contracts.
"""

from __future__ import annotations

import json

from agent.builtin_memory_provider import BuiltinMemoryProvider
from agent.core2_types import Core2RecallPacket
from agent.memory_manager import MemoryManager
from plugins.memory import load_memory_provider


def test_core2_foundation_lifecycle_round_trip(tmp_path):
    manager = MemoryManager()
    manager.add_provider(BuiltinMemoryProvider())

    provider = load_memory_provider("core2")
    assert provider is not None
    manager.add_provider(provider)
    manager.initialize_all(session_id="core2-foundation", platform="cli", hermes_home=str(tmp_path))

    prompt_before = manager.build_system_prompt()
    assert "# Core2 Memory" in prompt_before
    assert "Stored objects: 0" in prompt_before

    remember_result = json.loads(
        manager.handle_tool_call(
            "core2_remember",
            {
                "content": "User prefers dark mode",
                "title": "preference",
                "namespace": "personal",
                "risk_class": "standard",
                "language": "en",
            },
        )
    )
    assert remember_result["result"] == "stored"
    object_id = remember_result["object_id"]

    prompt_after = manager.build_system_prompt()
    assert "Stored objects: 1" in prompt_after

    recall_result = json.loads(
        manager.handle_tool_call(
            "core2_recall",
            {"query": "dark mode", "mode": "source_supported", "risk_class": "standard"},
        )
    )
    assert recall_result["abstained"] is False
    assert recall_result["items"]
    assert recall_result["items"][0]["object_id"] == object_id
    assert "dark mode" in recall_result["items"][0]["content"]

    explain_result = json.loads(manager.handle_tool_call("core2_explain", {"object_id": object_id}))
    assert explain_result["object_id"] == object_id
    assert explain_result["title"] == "preference"

    manager.sync_all("What's my theme?", "You prefer dark mode.", session_id="core2-foundation")
    manager.on_memory_write("add", "user", "Timezone: US Pacific")

    timezone_result = json.loads(
        manager.handle_tool_call(
            "core2_recall",
            {"query": "US Pacific", "mode": "compact_memory", "risk_class": "standard"},
        )
    )
    assert timezone_result["abstained"] is False
    assert any("US Pacific" in item["content"] for item in timezone_result["items"])

    manager.queue_prefetch_all("dark mode", session_id="core2-foundation")
    prefetched = manager.prefetch_all("unused", session_id="core2-foundation")
    assert "# Core2 Prefetch" in prefetched
    assert "dark mode" in prefetched

    manager.shutdown_all()
    assert provider.runtime is None


def test_core2_high_risk_recall_prefers_full_payload_profile():
    provider = load_memory_provider("core2")
    assert provider is not None

    packet = Core2RecallPacket(
        query="medical note",
        mode="exact_source_required",
        query_mode="exact_source_required",
        operator=None,
        risk_class="medical",
        support_tier="exact_source",
        confidence="high",
        abstained=True,
        answer_type="exact_source",
        delivery_view="artifact_rehydrate",
        items=[],
    )

    profile = provider._resolve_tool_budget_profile(packet, requested_profile="", risk_class="medical")

    assert profile == "full"
