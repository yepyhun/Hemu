from __future__ import annotations

from agent.decision_memory_render import DecisionMemoryRenderer
from agent.decision_memory_types import DecisionEntry


def _entry(entry_id: str, kind: str, subject: str, fact_text: str, *, bucket: str = "directive") -> DecisionEntry:
    return DecisionEntry(
        id=entry_id,
        namespace="test",
        scope_type="project",
        scope_key="project",
        kind=kind,
        subject=subject,
        fact_text=fact_text,
        normalized_text=fact_text.casefold(),
        status="active",
        confidence=0.9,
        importance=80,
        source_type="test",
        source_ref="config.yaml",
        memory_bucket=bucket,
        authority_class="verified_runtime",
        source_anchor_path="config.yaml",
        source_anchor_snippet="source of truth = config.yaml",
        source_anchor_kind="file",
        first_seen_at="2026-04-02T00:00:00+00:00",
        last_seen_at="2026-04-02T00:00:00+00:00",
        resolved_at=None,
        obsolete_at=None,
        replaced_by=None,
        access_count=0,
        hit_count=0,
        miss_count=0,
        feedback_positive=0,
        feedback_negative=0,
        temporal_valid_from=None,
        temporal_valid_until=None,
        supersedes_subjects_json="[]",
        metadata_json="{}",
    )


def test_decision_memory_render_outputs_bounded_strip():
    renderer = DecisionMemoryRenderer.from_dict({})
    text, meta = renderer.render(
        [
            _entry("a", "constraint", "runtime.provider_model", "Do not use qwen with OpenAI Codex auth.", bucket="constraint"),
            _entry("b", "decision", "config.terminal.cwd.authority", "config.yaml is the authority for terminal cwd."),
        ],
        token_budget=70,
        max_entries=2,
    )

    assert text.startswith("# Decision Memory")
    assert "STABLE CONSTRAINTS" in text
    assert "runtime.provider_model" in text
    assert meta["count"] >= 1


def test_decision_memory_render_groups_buckets_and_anchors():
    renderer = DecisionMemoryRenderer.from_dict({"enabled": True})
    text, meta = renderer.render(
        [
            _entry("a", "constraint", "artifact.stale", "Do not trust stale artifact output.", bucket="constraint"),
            _entry("b", "decision", "config.source", "config.yaml is the source of truth.", bucket="directive"),
            _entry("c", "decision", "tool.uv", "Consider uv for this repo.", bucket="consider"),
        ],
        token_budget=260,
        max_entries=6,
    )

    assert "STABLE CONSTRAINTS" in text
    assert "STABLE DIRECTIVES" in text
    assert "CONSIDER" in text
    assert "[anchor:config.yaml" in text
    assert meta["constraints"] == 1
    assert meta["directives"] == 1
    assert meta["consider"] == 1
