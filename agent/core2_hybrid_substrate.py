from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from agent.core2_store import Core2Store
from agent.core2_types import (
    QUERY_FAMILY_FACTUAL_SUPPORTED,
    QUERY_FAMILY_PERSONAL_RECALL,
    QUERY_FAMILY_RELATION_MULTIHOP,
    ROUTE_FAMILY_CURATED_MEMORY,
    ROUTE_FAMILY_SEMANTIC_FIRST,
)


def normalize_hybrid_substrate_mode(value: str | None) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"", "on", "true", "1", "yes"}:
        return "on"
    if normalized in {"shadow", "shadow_only"}:
        return "shadow"
    return "off"


@dataclass
class Core2HybridTrace:
    mode: str
    scope: str
    raw_hits: int = 0
    turn_hits: int = 0
    promoted_object_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class Core2HybridSubstrate:
    """Bounded MemPalace-inspired retrieval seam over existing Core2 storage."""

    def __init__(self, store: Core2Store, *, mode: str | None = None):
        self.store = store
        self.mode = normalize_hybrid_substrate_mode(mode)

    @property
    def enabled(self) -> bool:
        return self.mode != "off"

    @property
    def shadow_only(self) -> bool:
        return self.mode == "shadow"

    def search(
        self,
        query: str,
        *,
        route_plan,
        max_items: int,
        namespace_classes: Optional[List[str]],
        source_first: bool,
        exact_phrase: bool,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        trace = Core2HybridTrace(
            mode=self.mode,
            scope=self._scope_label(route_plan=route_plan, namespace_classes=namespace_classes),
        )
        if not self.enabled:
            return [], trace.to_dict()

        raw_hits = self.store.search_raw_archive(
            query,
            max_items=max(max_items, 4),
            namespace_classes=namespace_classes,
            source_first=source_first,
            exact_phrase=exact_phrase,
        )
        turn_hits: List[Dict[str, Any]] = []
        if self._allow_turn_scope(route_plan):
            turn_hits = self.store.search_turn_archive(query, max_items=max(max_items, 4))

        trace.raw_hits = len(raw_hits)
        trace.turn_hits = len(turn_hits)

        active_records = self.store.list_canonical_objects(include_inactive=False)
        by_raw_id: Dict[str, List[Dict[str, Any]]] = {}
        by_turn_id: Dict[str, List[Dict[str, Any]]] = {}
        by_session_id: Dict[str, List[Dict[str, Any]]] = {}
        for record in active_records:
            raw_id = str(record.get("source_raw_id") or "").strip()
            if raw_id:
                by_raw_id.setdefault(raw_id, []).append(record)
            metadata = dict(record.get("metadata") or {})
            turn_id = str(metadata.get("digest_turn_id") or "").strip()
            if turn_id:
                by_turn_id.setdefault(turn_id, []).append(record)
            session_id = str(metadata.get("session_id") or "").strip()
            if session_id:
                by_session_id.setdefault(session_id, []).append(record)

        promoted: Dict[str, Dict[str, Any]] = {}

        for raw_hit in raw_hits:
            for record in by_raw_id.get(str(raw_hit.get("raw_id") or "").strip(), []):
                candidate = dict(record)
                metadata = dict(candidate.get("metadata") or {})
                metadata["retrieval_path"] = "hybrid_scoped_raw"
                metadata["hybrid_scope"] = "raw_archive"
                metadata["hybrid_source_id"] = raw_hit.get("raw_id")
                candidate["metadata"] = metadata
                candidate["score"] = max(float(candidate.get("score", 0.0)), float(raw_hit.get("score", 0.0)) + 1.0)
                self._upsert_promoted(promoted, candidate)

        for turn_hit in turn_hits:
            linked = list(by_turn_id.get(str(turn_hit.get("turn_id") or "").strip(), []))
            matched_via = "turn_exact"
            if not linked and self._allow_session_fallback(route_plan):
                matched_via = "session_scope"
                linked = list(by_session_id.get(str(turn_hit.get("session_id") or "").strip(), []))[:2]
            for record in linked:
                candidate = dict(record)
                metadata = dict(candidate.get("metadata") or {})
                metadata["retrieval_path"] = "hybrid_scoped_turn"
                metadata["hybrid_scope"] = matched_via
                metadata["hybrid_turn_id"] = turn_hit.get("turn_id")
                metadata["hybrid_session_id"] = turn_hit.get("session_id")
                candidate["metadata"] = metadata
                boost = 3.0 if matched_via == "turn_exact" else 1.0
                candidate["score"] = max(float(candidate.get("score", 0.0)), float(turn_hit.get("score", 0.0)) + boost)
                self._upsert_promoted(promoted, candidate)

        ranked = sorted(
            promoted.values(),
            key=lambda item: float(item.get("score", 0.0)),
            reverse=True,
        )[:max_items]
        trace.promoted_object_ids = [str(item.get("object_id") or "") for item in ranked if str(item.get("object_id") or "")]
        return ranked, trace.to_dict()

    @staticmethod
    def _upsert_promoted(promoted: Dict[str, Dict[str, Any]], candidate: Dict[str, Any]) -> None:
        object_id = str(candidate.get("object_id") or "").strip()
        if not object_id:
            return
        current = promoted.get(object_id)
        if current is None:
            promoted[object_id] = candidate
            return

        if float(candidate.get("score", 0.0)) > float(current.get("score", 0.0)):
            promoted[object_id] = candidate

    @staticmethod
    def _allow_turn_scope(route_plan) -> bool:
        return route_plan.route_family in {ROUTE_FAMILY_CURATED_MEMORY, ROUTE_FAMILY_SEMANTIC_FIRST} or route_plan.query_family in {
            QUERY_FAMILY_PERSONAL_RECALL,
            QUERY_FAMILY_FACTUAL_SUPPORTED,
        }

    @staticmethod
    def _allow_session_fallback(route_plan) -> bool:
        return route_plan.query_family in {QUERY_FAMILY_PERSONAL_RECALL, QUERY_FAMILY_RELATION_MULTIHOP}

    @staticmethod
    def _scope_label(*, route_plan, namespace_classes: Optional[List[str]]) -> str:
        wings = ",".join(namespace_classes or ["all"])
        room = "turn+raw" if Core2HybridSubstrate._allow_turn_scope(route_plan) else "raw"
        return f"{wings}:{room}"
