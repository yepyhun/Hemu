from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Tuple


_SCOPE_PRIORITY = {
    ("hybrid_scoped_turn", "turn_exact"): 7.0,
    ("hybrid_scoped_turn", "session_scope"): 4.0,
    ("hybrid_scoped_raw", "raw_archive"): 2.0,
}

_SOURCE_AUTHORITY = {
    "turn_digested_fact": 4.0,
    "digested_fact": 3.5,
    "explicit_memory": 3.0,
    "document_source": 2.5,
    "builtin_memory": 2.0,
}

_STATE_PRIORITY = {
    "canonical_active": 2.0,
    "provisional": 0.5,
    "candidate": 0.0,
    "conflicted": -1.0,
    "superseded": -3.0,
    "rejected": -5.0,
    "archived": -5.0,
}

_SUPPORT_PRIORITY = {
    "exact_source": 4.0,
    "multi_source_supported": 3.0,
    "source_supported": 2.0,
    "inferred_supported": 1.0,
    "weak_support": -1.0,
    "none": -2.0,
}


def hybrid_ranking_key(candidate: Dict[str, Any]) -> Tuple[float, float, float]:
    metadata = dict(candidate.get("metadata") or {})
    path = str(metadata.get("retrieval_path") or "").strip().lower()
    scope = str(metadata.get("hybrid_scope") or "").strip().lower()
    source_type = str(candidate.get("source_type") or "").strip().lower()
    state_status = str(candidate.get("state_status") or "").strip().lower()
    support_level = str(candidate.get("support_level") or "").strip().lower()

    base_score = float(candidate.get("score", 0.0))
    ranking_score = (
        base_score
        + _SCOPE_PRIORITY.get((path, scope), 0.0)
        + _SOURCE_AUTHORITY.get(source_type, 0.0)
        + _STATE_PRIORITY.get(state_status, 0.0)
        + _SUPPORT_PRIORITY.get(support_level, 0.0)
    )
    freshness_score = _freshness_score(candidate)
    return (ranking_score, freshness_score, base_score)


def explain_hybrid_ranking(candidate: Dict[str, Any]) -> Dict[str, float]:
    metadata = dict(candidate.get("metadata") or {})
    path = str(metadata.get("retrieval_path") or "").strip().lower()
    scope = str(metadata.get("hybrid_scope") or "").strip().lower()
    source_type = str(candidate.get("source_type") or "").strip().lower()
    state_status = str(candidate.get("state_status") or "").strip().lower()
    support_level = str(candidate.get("support_level") or "").strip().lower()
    base_score = float(candidate.get("score", 0.0))
    scope_score = _SCOPE_PRIORITY.get((path, scope), 0.0)
    authority_score = _SOURCE_AUTHORITY.get(source_type, 0.0)
    status_score = _STATE_PRIORITY.get(state_status, 0.0)
    support_score = _SUPPORT_PRIORITY.get(support_level, 0.0)
    freshness_score = _freshness_score(candidate)
    return {
        "base": base_score,
        "scope": scope_score,
        "authority": authority_score,
        "status": status_score,
        "support": support_score,
        "freshness": freshness_score,
        "total": base_score + scope_score + authority_score + status_score + support_score,
    }


def _freshness_score(candidate: Dict[str, Any]) -> float:
    timestamp = (
        candidate.get("updated_at")
        or candidate.get("recorded_at")
        or candidate.get("effective_from")
        or candidate.get("source_created_at")
        or candidate.get("created_at")
    )
    if not timestamp:
        return 0.0
    parsed = _parse_iso(str(timestamp))
    if parsed is None:
        return 0.0
    age_days = max(0.0, (datetime.now(timezone.utc) - parsed).total_seconds() / 86400.0)
    return max(0.0, 2.0 - min(2.0, age_days / 30.0))


def _parse_iso(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
