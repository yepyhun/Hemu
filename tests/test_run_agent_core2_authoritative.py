from __future__ import annotations


class _FakeMemoryManager:
    def __init__(self):
        self.synced: list[tuple[str, str]] = []
        self.prefetched: list[str] = []

    def prefetch_all(self, query: str, *, session_id: str = "") -> str:
        self.prefetched.append(query)
        return ""

    def authoritative_answer(self, query: str, *, session_id: str = ""):
        return {"text": "Answer: 'The Hate U Give'.", "mode": "personal_temporal_compare"}

    def sync_all(self, user_content: str, assistant_content: str, *, session_id: str = "") -> None:
        self.synced.append((user_content, assistant_content))

    def queue_prefetch_all(self, query: str, *, session_id: str = "") -> None:
        self.prefetched.append(f"queued:{query}")


def test_run_conversation_short_circuits_for_authoritative_memory_answer(monkeypatch):
    from run_agent import AIAgent

    def _boom(*args, **kwargs):
        raise AssertionError("LLM path should not be used for authoritative memory answer")

    monkeypatch.setattr("run_agent.OpenAI", lambda **kwargs: object())
    monkeypatch.setattr("run_agent.get_tool_definitions", lambda *args, **kwargs: [])
    monkeypatch.setattr("run_agent.handle_function_call", lambda *args, **kwargs: "{}")
    monkeypatch.setattr("run_agent.AIAgent._interruptible_api_call", _boom)
    monkeypatch.setattr("run_agent.AIAgent._interruptible_streaming_api_call", _boom)

    agent = AIAgent(
        model="test-model",
        api_key="test-key",
        base_url="http://localhost:8080/v1",
        platform="cli",
        max_iterations=3,
        quiet_mode=True,
        skip_memory=True,
        persist_session=False,
    )
    manager = _FakeMemoryManager()
    agent._memory_manager = manager

    result = agent.run_conversation("Which book did I finish reading first?")

    assert result["final_response"] == "Answer: 'The Hate U Give'."
    assert result["api_calls"] == 0
    assert manager.synced == [("Which book did I finish reading first?", "Answer: 'The Hate U Give'.")]
