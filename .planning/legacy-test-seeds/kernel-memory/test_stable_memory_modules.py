from __future__ import annotations

from agent.decision_memory_types import DecisionEntry
from agent.stable_memory_buckets import classify_memory_bucket
from agent.stable_memory_feedback import quality_score
from agent.stable_memory_guardrails import should_admit_stable_memory
from agent.stable_memory_scope import scope_precedence_score


def _entry(**overrides):
    payload = {
        "id": "dec_test",
        "namespace": "test",
        "scope_type": "project",
        "scope_key": "benchmark",
        "kind": "decision",
        "subject": "config.source",
        "fact_text": "config.yaml is the source of truth.",
        "normalized_text": "config.yaml is the source of truth.",
        "status": "active",
        "confidence": 0.9,
        "importance": 80,
        "source_type": "runtime_normalization",
        "source_ref": "config.yaml",
        "memory_bucket": "directive",
        "authority_class": "verified_runtime",
        "source_anchor_path": "config.yaml",
        "source_anchor_snippet": "source of truth = config.yaml",
        "source_anchor_kind": "file",
        "first_seen_at": "2026-04-02T00:00:00+00:00",
        "last_seen_at": "2026-04-02T00:00:00+00:00",
        "resolved_at": None,
        "obsolete_at": None,
        "replaced_by": None,
        "access_count": 0,
        "hit_count": 3,
        "miss_count": 0,
        "feedback_positive": 2,
        "feedback_negative": 0,
        "temporal_valid_from": None,
        "temporal_valid_until": None,
        "supersedes_subjects_json": "[]",
        "metadata_json": "{}",
    }
    payload.update(overrides)
    return DecisionEntry(**payload)


def test_stable_memory_bucket_classification_detects_constraints():
    assert classify_memory_bucket(kind="decision", fact_text="Do not trust the stale artifact.") == "constraint"
    assert classify_memory_bucket(kind="decision", fact_text="Consider using uv for this repo.") == "consider"
    assert classify_memory_bucket(kind="decision", fact_text="Use config.yaml as the source of truth.") == "directive"


def test_stable_memory_guardrails_rejects_secret_like_content():
    decision = should_admit_stable_memory(fact_text="password = hunter2-super-secret-value")

    assert decision.allowed is False
    assert decision.reason == "secret_detected"


def test_stable_memory_guardrails_allows_plain_language_at_home_phrase():
    decision = should_admit_stable_memory(
        fact_text="On February 22, 2026, Laura suffered a spinal injury at home and was paralyzed in her hind legs."
    )

    assert decision.allowed is True
    assert decision.reason == "allowed"


def test_stable_memory_guardrails_rejects_actual_stacktrace_line():
    decision = should_admit_stable_memory(
        fact_text="Traceback\n  at App.run (/srv/app.py:42)\n  at main (/srv/main.py:11)"
    )

    assert decision.allowed is False
    assert decision.reason == "stacktrace_like"


def test_stable_memory_scope_precedence_prefers_specific_scope():
    exact = scope_precedence_score(current_scope="project:hermes-agent-port", candidate_scope="project:hermes-agent-port")
    global_scope = scope_precedence_score(current_scope="project:hermes-agent-port", candidate_scope="global")

    assert exact.score > global_scope.score
    assert exact.level == "exact"


def test_stable_memory_quality_prefers_grounded_high_authority_entry():
    grounded = _entry()
    weak = _entry(
        authority_class="assistant_inferred",
        source_anchor_path="",
        source_anchor_snippet="",
        feedback_positive=0,
        hit_count=0,
        miss_count=2,
        confidence=0.55,
    )

    assert quality_score(grounded) > quality_score(weak)
