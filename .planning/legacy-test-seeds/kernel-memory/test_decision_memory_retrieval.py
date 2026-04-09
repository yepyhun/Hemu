from __future__ import annotations

from agent.decision_memory_retrieval import DecisionMemoryRetriever
from agent.decision_memory_store import DecisionMemoryStore
from agent.decision_memory_types import DecisionCandidate


def test_decision_memory_retrieval_prefers_session_scoped_hits(tmp_path):
    store = DecisionMemoryStore.from_env_config(
        {"enabled": True, "root_dir": str(tmp_path / "decision_memory"), "namespace": "test"},
        hermes_home=tmp_path,
        default_namespace="test",
    )
    store.upsert_candidate(
        DecisionCandidate(
            kind="decision",
            subject="config.terminal.cwd.authority",
            fact_text="config.yaml is the authority for terminal cwd.",
            scope_type="project",
            scope_key="test",
        )
    )
    store.upsert_candidate(
        DecisionCandidate(
            kind="decision",
            subject="config.terminal.cwd.authority",
            fact_text="Use /workspace/project as cwd for this session.",
            scope_type="session",
            scope_key="sess",
            importance=90,
        )
    )
    retriever = DecisionMemoryRetriever.from_dict({}, store=store)

    result = retriever.retrieve(
        namespace="test",
        user_message="continue using the chosen cwd from config.yaml",
        recent_user_turns=["use the configured working directory"],
        session_id="sess",
        policy_name="code_execution_continuation",
    )

    assert result.entries
    assert result.entries[0].scope_type == "session"
    assert result.hit_count >= 1


def test_decision_memory_retrieval_skips_obsolete_by_default(tmp_path):
    store = DecisionMemoryStore.from_env_config(
        {"enabled": True, "root_dir": str(tmp_path / "decision_memory"), "namespace": "test"},
        hermes_home=tmp_path,
        default_namespace="test",
    )
    store.upsert_candidate(
        DecisionCandidate(
            kind="obsolete",
            subject="file.app_py.db_url_source",
            fact_text="localhost literal source is obsolete.",
            scope_type="file",
            scope_key="app.py",
            status="obsolete",
        )
    )
    retriever = DecisionMemoryRetriever.from_dict({}, store=store)

    result = retriever.retrieve(
        namespace="test",
        user_message="continue with the current config source",
        recent_user_turns=[],
        session_id="sess",
        policy_name="code_execution_continuation",
    )

    assert result.entries == ()


def test_decision_memory_retrieval_prefers_specific_scope_and_authority(tmp_path):
    store = DecisionMemoryStore.from_env_config(
        {"enabled": True, "root_dir": str(tmp_path / "decision_memory"), "namespace": "test"},
        hermes_home=tmp_path,
        default_namespace="test",
    )
    store.upsert_candidate(
        DecisionCandidate(
            kind="decision",
            subject="cron.delivery.visibility",
            fact_text="Use silent reminder delivery.",
            scope_type="global",
            scope_key="global",
            source_type="assistant_inferred",
            authority_class="assistant_inferred",
        )
    )
    store.upsert_candidate(
        DecisionCandidate(
            kind="decision",
            subject="cron.delivery.visibility",
            fact_text="Discord reminders must ping the user explicitly.",
            scope_type="session",
            scope_key="sess",
            source_type="user_instruction",
            authority_class="user_explicit",
        )
    )
    retriever = DecisionMemoryRetriever.from_dict({}, store=store)

    result = retriever.retrieve(
        namespace="test",
        user_message="continue the reminder delivery behavior",
        recent_user_turns=["keep the Discord reminder ping behavior"],
        session_id="sess",
        policy_name="task_management",
    )

    assert result.entries
    assert result.entries[0].scope_type == "session"
    assert "ping" in result.entries[0].fact_text
