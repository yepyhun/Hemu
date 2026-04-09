from __future__ import annotations

from agent.decision_memory_runtime import DecisionMemoryRuntime
from agent.native_memory_mirror import sync_native_memory_entries
from agent.profile_memory_repair import repair_profile_integrity
from agent.profile_memory_types import candidate_from_profile


def _runtime(tmp_path):
    return DecisionMemoryRuntime.from_agent_config(
        {"enabled": True, "root_dir": str(tmp_path / "decision_memory"), "namespace": "test", "profile_memory_enabled": True},
        default_namespace="test",
        hermes_home=tmp_path,
    )


def test_repair_profile_integrity_obsoletes_malformed_general_fragments(tmp_path):
    runtime = _runtime(tmp_path)
    runtime.record_candidate(
        candidate_from_profile(
            kind="value",
            subject="user.preference.general.numeric",
            fact_text="User prefers 10 over 5).",
            profile_scope="user",
            profile_subject_group="general",
            profile_origin="user_explicit",
            source_ref="sess-1",
        )
    )
    runtime.record_candidate(
        candidate_from_profile(
            kind="value",
            subject="user.preference.general.remember",
            fact_text="Remember: for Tomi: Dr.",
            profile_scope="user",
            profile_subject_group="general",
            profile_origin="user_explicit",
            source_ref="sess-2",
        )
    )

    result = repair_profile_integrity(runtime=runtime, source_ref="repair-1")
    snapshot = runtime.debug_snapshot(limit=20)

    assert result["issues_found"] == 2
    assert result["records_obsoleted"] >= 2
    assert any(item["status"] == "obsolete" and item["fact_text"] == "User prefers 10 over 5)." for item in snapshot["recent"])
    assert any(item["status"] == "obsolete" and item["fact_text"] == "Remember: for Tomi: Dr." for item in snapshot["recent"])


def test_repair_profile_integrity_obsoletes_exact_age_and_duplicate_native_mirror(tmp_path):
    runtime = _runtime(tmp_path)
    runtime.record_candidate(
        candidate_from_profile(
            kind="value",
            subject="user.context.identity.age",
            fact_text="Tomi is 19 years old.",
            profile_scope="user",
            profile_subject_group="identity",
            profile_origin="user_explicit",
            source_ref="sess-age",
        )
    )
    runtime.record_candidate(
        candidate_from_profile(
            kind="value",
            subject="user.context.identity.name",
            fact_text="The user prefers to be called Tomi.",
            profile_scope="user",
            profile_subject_group="identity",
            profile_origin="user_explicit",
            source_ref="sess-name",
        )
    )
    sync_native_memory_entries(
        runtime=runtime,
        target="user",
        entries=["The user prefers to be called Tomi."],
        source_ref="native-sync",
    )

    result = repair_profile_integrity(runtime=runtime, source_ref="repair-2")
    snapshot = runtime.debug_snapshot(limit=20)

    assert result["issues_found"] == 2
    assert result["records_obsoleted"] >= 2
    assert any("exact_age_fact" in item["problems"] for item in result["issues"])
    assert any("duplicate_native_profile_mirror" in item["problems"] for item in result["issues"])
    assert any(item["status"] == "obsolete" and item["fact_text"] == "Tomi is 19 years old." for item in snapshot["recent"])
    assert any(
        item["status"] == "obsolete"
        and item["subject"].startswith("native_memory.user.")
        and item["fact_text"] == "The user prefers to be called Tomi."
        for item in snapshot["recent"]
    )
