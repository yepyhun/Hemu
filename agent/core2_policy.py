from __future__ import annotations

from hashlib import sha1
from typing import Any, Dict, Tuple

from agent.core2_types import (
    NAMESPACE_HIGH_RISK,
    NAMESPACE_LIBRARY,
    NAMESPACE_PERSONAL,
    NAMESPACE_WORKSPACE,
    OBJECT_KIND_EVENT,
    OBJECT_KIND_SOURCE,
    OBJECT_KIND_STATE,
    STATE_CANONICAL_ACTIVE,
    STATE_PROVISIONAL,
    SUPPORT_SOURCE_SUPPORTED,
    SUPPORT_WEAK,
)


def classify_namespace(namespace: str) -> str:
    normalized = (namespace or "").strip().lower()
    if normalized in {"medical", "legal", "regulatory", "high-risk", "high_risk"}:
        return NAMESPACE_HIGH_RISK
    if normalized in {"library", "books", "papers", "articles", "research"}:
        return NAMESPACE_LIBRARY
    if normalized in {"workspace", "project", "repo", "tool", "workflow"}:
        return NAMESPACE_WORKSPACE
    return NAMESPACE_PERSONAL


def normalize_risk_class(namespace: str, risk_class: str) -> str:
    namespace_class = classify_namespace(namespace)
    normalized = (risk_class or "standard").strip().lower()
    if namespace_class == NAMESPACE_HIGH_RISK and normalized == "standard":
        return "high"
    return normalized or "standard"


def build_temporal_fields(effective_from: str | None, metadata: Dict[str, Any], now: str) -> Dict[str, str | None]:
    return {
        "observed_at": metadata.get("observed_at"),
        "source_created_at": metadata.get("source_created_at"),
        "effective_from": effective_from or metadata.get("effective_from"),
        "effective_to": metadata.get("effective_to"),
        "recorded_at": metadata.get("recorded_at") or now,
        "superseded_at": metadata.get("superseded_at"),
        "invalidated_at": metadata.get("invalidated_at"),
    }


def default_object_kind(title: str, source_type: str, metadata: Dict[str, Any]) -> str:
    explicit = (metadata.get("object_kind") or "").strip().lower()
    if explicit:
        return explicit
    title_lc = (title or "").strip().lower()
    if source_type == "document_source":
        return OBJECT_KIND_SOURCE
    if title_lc.startswith("event:"):
        return OBJECT_KIND_EVENT
    return OBJECT_KIND_STATE


def derive_support_level(namespace: str, source_type: str, temporal_fields: Dict[str, Any]) -> str:
    namespace_class = classify_namespace(namespace)
    if namespace_class == NAMESPACE_HIGH_RISK:
        if not temporal_fields.get("source_created_at") or not temporal_fields.get("effective_from"):
            return SUPPORT_WEAK
    if source_type in {"builtin_memory", "explicit_memory", "document_source"}:
        return SUPPORT_SOURCE_SUPPORTED
    return SUPPORT_WEAK


def derive_initial_state(namespace: str, metadata: Dict[str, Any], support_level: str) -> str:
    explicit = (metadata.get("state_status") or "").strip().lower()
    if explicit:
        return explicit
    if support_level == SUPPORT_WEAK and classify_namespace(namespace) == NAMESPACE_HIGH_RISK:
        return STATE_PROVISIONAL
    return STATE_CANONICAL_ACTIVE


def compute_identity_key(namespace: str, object_kind: str, title: str, content: str, metadata: Dict[str, Any]) -> str:
    explicit = metadata.get("identity_key")
    if explicit:
        return str(explicit)
    stable = "|".join(
        [
            classify_namespace(namespace),
            object_kind,
            (title or "").strip().lower(),
            (content or "").strip().lower()[:160],
        ]
    )
    return sha1(stable.encode("utf-8")).hexdigest()[:20]


def can_recall_record(record: Dict[str, Any], *, mode: str, query_risk_class: str) -> Tuple[bool, str | None]:
    state_status = record.get("state_status") or ""
    if state_status in {"rejected", "archived"}:
        return False, f"Record is not active ({state_status})."
    if record.get("invalidated_at"):
        return False, "Record is invalidated."
    if state_status == "superseded":
        return False, "Record is superseded by a newer version."

    namespace_class = record.get("namespace_class") or classify_namespace(record.get("namespace") or "")
    effective_from = record.get("effective_from")
    source_created_at = record.get("source_created_at")
    support_level = record.get("support_level") or SUPPORT_WEAK
    normalized_query_risk = (query_risk_class or "standard").strip().lower()

    if namespace_class == NAMESPACE_HIGH_RISK or normalized_query_risk in {"high", "medical", "legal"}:
        if mode not in {"exact_source_required", "source_supported"}:
            return False, "High-risk memory requires source-supported or exact-source recall."
        if not effective_from or not source_created_at:
            return False, "High-risk memory requires both effective_from and source_created_at."
        if support_level == SUPPORT_WEAK:
            return False, "High-risk memory does not have strong enough support."

    return True, None
