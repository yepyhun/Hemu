from __future__ import annotations

import json

from agent.builtin_memory_provider import BuiltinMemoryProvider
from agent.memory_manager import MemoryManager
from agent.memory_provider import MemoryProvider
from plugins.memory import load_memory_provider


class DummyMemoryProvider(MemoryProvider):
    @property
    def name(self) -> str:
        return "dummy_memory"

    def is_available(self) -> bool:
        return True

    def initialize(self, session_id: str, **kwargs) -> None:
        del session_id, kwargs

    def system_prompt_block(self) -> str:
        return ""

    def prefetch(self, query: str, *, session_id: str = "") -> str:
        del query, session_id
        return ""

    def sync_turn(self, user_content: str, assistant_content: str, *, session_id: str = "") -> None:
        del user_content, assistant_content, session_id

    def get_tool_schemas(self):
        return [{"name": "dummy_recall", "parameters": {"type": "object", "properties": {}}}]

    def handle_tool_call(self, tool_name: str, args: dict, **kwargs) -> str:
        del tool_name, args, kwargs
        return json.dumps({"result": "noop"})

    def shutdown(self) -> None:
        return None


def test_core2_memory_manager_full_lifecycle(tmp_path):
    manager = MemoryManager()
    manager.add_provider(BuiltinMemoryProvider())

    provider = load_memory_provider("core2")
    assert provider is not None
    manager.add_provider(provider)
    manager.initialize_all(session_id="core2-manager-e2e", platform="cli", hermes_home=str(tmp_path))

    assert manager.provider_names == ["builtin", "core2"]
    assert manager.get_all_tool_names() == {"core2_recall", "core2_remember", "core2_explain"}
    assert manager.has_tool("core2_remember")
    assert not manager.has_tool("memory")

    stored = json.loads(
        manager.handle_tool_call(
            "core2_remember",
            {
                "content": "The user prefers compact release summaries with only current deployment facts.",
                "title": "release summary preference",
                "namespace": "personal",
                "risk_class": "standard",
                "language": "en",
            },
        )
    )
    assert stored["result"] == "stored"

    recalled = json.loads(
        manager.handle_tool_call(
            "core2_recall",
            {"query": "release summaries", "mode": "compact_memory", "risk_class": "standard"},
        )
    )
    assert recalled["abstained"] is False
    assert recalled["items"]
    assert "compact release summaries" in recalled["display_value"]

    explained = json.loads(manager.handle_tool_call("core2_explain", {"object_id": stored["object_id"]}))
    assert explained["object_id"] == stored["object_id"]
    assert explained["delivery_views"]

    manager.sync_all("How should release notes look?", "Keep them compact and current.", session_id="core2-manager-e2e")
    manager.handle_tool_call(
        "core2_remember",
        {
            "content": "I live in Budapest.",
            "title": "profile note",
            "namespace": "personal",
            "risk_class": "standard",
            "language": "en",
        },
    )
    manager.queue_prefetch_all("Where do I live?", session_id="core2-manager-e2e")
    prefetched = manager.prefetch_all("unused", session_id="core2-manager-e2e")

    assert "# Core2 Answer Surface" in prefetched
    assert "Answer: Budapest." in prefetched

    prompt = manager.build_system_prompt()
    assert "# Core2 Memory" in prompt
    assert "Stored objects:" in prompt

    manager.shutdown_all()
    assert provider.runtime is None


def test_core2_manager_rejects_second_external_provider(tmp_path):
    manager = MemoryManager()
    manager.add_provider(BuiltinMemoryProvider())

    provider = load_memory_provider("core2")
    assert provider is not None
    manager.add_provider(provider)
    manager.add_provider(DummyMemoryProvider())
    manager.initialize_all(session_id="core2-one-external", platform="cli", hermes_home=str(tmp_path))

    assert manager.provider_names == ["builtin", "core2"]
    assert manager.has_tool("core2_recall")
    assert not manager.has_tool("dummy_recall")

    manager.shutdown_all()
