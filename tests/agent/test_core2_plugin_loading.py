"""Focused loading and registration tests for the Core2 memory provider."""

from __future__ import annotations

from agent.builtin_memory_provider import BuiltinMemoryProvider
from agent.memory_manager import MemoryManager
from agent.memory_provider import MemoryProvider
from plugins.memory import discover_memory_providers, load_memory_provider


class DummyExternalProvider(MemoryProvider):
    @property
    def name(self) -> str:
        return "dummy_external"

    def is_available(self) -> bool:
        return True

    def initialize(self, session_id: str, **kwargs) -> None:
        self._session_id = session_id

    def get_tool_schemas(self):
        return []


def test_core2_provider_loads_and_discovers():
    provider = load_memory_provider("core2")
    assert provider is not None
    assert provider.name == "core2"

    providers = discover_memory_providers()
    core2 = [item for item in providers if item[0] == "core2"]
    assert core2
    assert core2[0][2] is True


def test_core2_exposes_stable_tool_names():
    provider = load_memory_provider("core2")
    assert provider is not None
    tool_names = sorted(schema["name"] for schema in provider.get_tool_schemas())
    assert tool_names == ["core2_explain", "core2_recall", "core2_remember"]


def test_core2_registers_as_single_external_provider(tmp_path):
    manager = MemoryManager()
    manager.add_provider(BuiltinMemoryProvider())

    core2 = load_memory_provider("core2")
    assert core2 is not None
    manager.add_provider(core2)
    manager.add_provider(DummyExternalProvider())

    assert manager.provider_names == ["builtin", "core2"]

    manager.initialize_all(session_id="core2-loading", platform="cli", hermes_home=str(tmp_path))
    assert sorted(manager.get_all_tool_names()) == [
        "core2_explain",
        "core2_recall",
        "core2_remember",
    ]
    manager.shutdown_all()


def test_core2_initializes_and_shuts_down(tmp_path):
    provider = load_memory_provider("core2")
    assert provider is not None

    provider.initialize("core2-init", hermes_home=str(tmp_path), platform="cli")
    assert provider.runtime is not None
    assert (tmp_path / "core2" / "core2.db").exists()

    provider.shutdown()
    assert provider.runtime is None
