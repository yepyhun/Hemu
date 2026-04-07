from __future__ import annotations

from agent.core2_hybrid_substrate import Core2HybridSubstrate


def _candidate(
    object_id: str,
    *,
    score: float,
    retrieval_path: str,
    hybrid_scope: str,
    source_type: str = "turn_digested_fact",
    support_level: str = "source_supported",
    state_status: str = "canonical_active",
    updated_at: str = "2026-04-07T20:00:00+00:00",
):
    return {
        "object_id": object_id,
        "score": score,
        "source_type": source_type,
        "support_level": support_level,
        "state_status": state_status,
        "updated_at": updated_at,
        "metadata": {
            "retrieval_path": retrieval_path,
            "hybrid_scope": hybrid_scope,
        },
    }


def test_hybrid_candidate_ordering_prefers_higher_score():
    raw = _candidate("raw", score=10.0, retrieval_path="hybrid_scoped_raw", hybrid_scope="raw_archive")
    turn = _candidate("turn", score=8.0, retrieval_path="hybrid_scoped_turn", hybrid_scope="turn_exact")

    ranked = sorted([raw, turn], key=lambda item: float(item.get("score", 0.0)), reverse=True)
    assert [item["object_id"] for item in ranked] == ["raw", "turn"]


def test_hybrid_upsert_promoted_keeps_first_candidate_when_scores_tie():
    weak = _candidate(
        "shared",
        score=9.0,
        retrieval_path="hybrid_scoped_turn",
        hybrid_scope="turn_exact",
        support_level="weak_support",
        state_status="provisional",
    )
    strong = _candidate(
        "shared",
        score=9.0,
        retrieval_path="hybrid_scoped_turn",
        hybrid_scope="turn_exact",
        support_level="source_supported",
        state_status="canonical_active",
    )

    promoted = {}
    Core2HybridSubstrate._upsert_promoted(promoted, weak)
    Core2HybridSubstrate._upsert_promoted(promoted, strong)

    chosen = promoted["shared"]
    assert chosen["metadata"]["retrieval_path"] == "hybrid_scoped_turn"
    assert "ranking_signals" not in chosen["metadata"]
    assert chosen["support_level"] == "weak_support"


def test_hybrid_upsert_promoted_uses_higher_score_only():
    promoted = {}
    raw = _candidate("shared", score=10.0, retrieval_path="hybrid_scoped_raw", hybrid_scope="raw_archive")
    turn = _candidate("shared", score=8.0, retrieval_path="hybrid_scoped_turn", hybrid_scope="turn_exact")

    Core2HybridSubstrate._upsert_promoted(promoted, raw)
    Core2HybridSubstrate._upsert_promoted(promoted, turn)

    chosen = promoted["shared"]
    assert chosen["metadata"]["retrieval_path"] == "hybrid_scoped_raw"
    assert chosen["metadata"]["hybrid_scope"] == "raw_archive"
    assert "ranking_signals" not in chosen["metadata"]


def test_hybrid_upsert_promoted_ignores_freshness_when_scores_tie():
    older = _candidate(
        "shared",
        score=9.0,
        retrieval_path="hybrid_scoped_turn",
        hybrid_scope="turn_exact",
        updated_at="2025-01-01T00:00:00+00:00",
    )
    newer = _candidate(
        "shared",
        score=9.0,
        retrieval_path="hybrid_scoped_turn",
        hybrid_scope="turn_exact",
        updated_at="2026-04-07T20:00:00+00:00",
    )

    promoted = {}
    Core2HybridSubstrate._upsert_promoted(promoted, older)
    Core2HybridSubstrate._upsert_promoted(promoted, newer)

    chosen = promoted["shared"]
    assert chosen["updated_at"] == "2025-01-01T00:00:00+00:00"
