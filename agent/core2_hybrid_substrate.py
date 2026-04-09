from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from agent.core2_query_shape_seeding import build_query_shape_seed_plan
from agent.core2_store import Core2Store
from agent.core2_types import (
    QUERY_FAMILY_FACTUAL_SUPPORTED,
    QUERY_FAMILY_PERSONAL_RECALL,
    QUERY_FAMILY_RELATION_MULTIHOP,
    QUERY_FAMILY_UPDATE_RESOLUTION,
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
    query_shape_operator_family: str = ""
    query_shape_seed_family: str = ""
    query_shape_signal_family: str = ""
    query_shape_slot_count: int = 0
    query_shape_seed_expansions: int = 0
    constituent_expansions: int = 0
    selector_expansions: int = 0
    selector_slot_coverage: int = 0
    aggregation_safety_abstentions: int = 0
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

        expand_constituents = self._needs_constituent_anchor_expansion(query, route_plan=route_plan)
        raw_limit = max(max_items, 8 if expand_constituents else 4)
        turn_limit = max(max_items, 8 if expand_constituents else 4)
        seed_plan = build_query_shape_seed_plan(query, route_plan=route_plan)
        seed_queries = list(seed_plan.seed_queries)
        raw_hits = self.store.search_raw_archive(
            query,
            max_items=raw_limit,
            namespace_classes=namespace_classes,
            source_first=source_first,
            exact_phrase=exact_phrase,
        )
        turn_hits: List[Dict[str, Any]] = []
        if self._allow_turn_scope(route_plan):
            turn_hits = self.store.search_turn_archive(query, max_items=turn_limit)

        seed_raw_hits, seed_turn_hits = self._search_query_shape_seed_variants(
            seed_queries,
            raw_limit=raw_limit,
            turn_limit=turn_limit,
            route_plan=route_plan,
        )
        raw_hits = self._merge_seed_hits(raw_hits, seed_raw_hits, key="raw_id")
        turn_hits = self._merge_seed_hits(turn_hits, seed_turn_hits, key="turn_id")

        trace.raw_hits = len(raw_hits)
        trace.turn_hits = len(turn_hits)
        trace.query_shape_operator_family = seed_plan.operator_family
        trace.query_shape_seed_family = seed_plan.seed_family
        trace.query_shape_signal_family = seed_plan.signal_family
        trace.query_shape_slot_count = len(seed_plan.slots)
        trace.query_shape_seed_expansions = len(seed_raw_hits) + len(seed_turn_hits)

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
            for session_id in self._session_lookup_keys(metadata):
                by_session_id.setdefault(session_id, []).append(record)

        promoted: Dict[str, Dict[str, Any]] = {}

        for raw_hit in raw_hits:
            linked_raw_records = list(by_raw_id.get(str(raw_hit.get("raw_id") or "").strip(), []))
            for record in linked_raw_records:
                candidate = dict(record)
                metadata = dict(candidate.get("metadata") or {})
                metadata["retrieval_path"] = "hybrid_scoped_raw"
                metadata["hybrid_scope"] = "raw_archive"
                metadata["hybrid_source_id"] = raw_hit.get("raw_id")
                if raw_hit.get("_seed_query"):
                    metadata["hybrid_seed_query"] = raw_hit.get("_seed_query")
                    metadata["hybrid_seed_family"] = seed_plan.seed_family
                    metadata["hybrid_operator_family"] = seed_plan.operator_family
                    if seed_plan.signal_family:
                        metadata["hybrid_signal_family"] = seed_plan.signal_family
                candidate["metadata"] = metadata
                candidate["score"] = max(float(candidate.get("score", 0.0)), float(raw_hit.get("score", 0.0)) + 1.0)
                self._upsert_promoted(promoted, candidate)
            if expand_constituents:
                session_id = self._session_id_for_hit(raw_hit) or self._session_id_for_records(linked_raw_records)
                added = self._promote_session_anchors(
                    promoted,
                    session_records=self._session_records_for_hit(by_session_id, raw_hit)
                    or self._session_records_for_records(by_session_id, linked_raw_records),
                    session_id=session_id,
                    query=query,
                    base_score=float(raw_hit.get("score", 0.0)),
                )
                trace.constituent_expansions += int(added.get("added") or 0)
                trace.selector_expansions += int(added.get("selector_expansions") or 0)
                trace.selector_slot_coverage = max(trace.selector_slot_coverage, int(added.get("slot_coverage") or 0))
                trace.aggregation_safety_abstentions += int(added.get("aggregation_safety_abstentions") or 0)

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
                if turn_hit.get("_seed_query"):
                    metadata["hybrid_seed_query"] = turn_hit.get("_seed_query")
                    metadata["hybrid_seed_family"] = seed_plan.seed_family
                    metadata["hybrid_operator_family"] = seed_plan.operator_family
                    if seed_plan.signal_family:
                        metadata["hybrid_signal_family"] = seed_plan.signal_family
                candidate["metadata"] = metadata
                boost = 3.0 if matched_via == "turn_exact" else 1.0
                candidate["score"] = max(float(candidate.get("score", 0.0)), float(turn_hit.get("score", 0.0)) + boost)
                self._upsert_promoted(promoted, candidate)
            if expand_constituents:
                added = self._promote_session_anchors(
                    promoted,
                    session_records=self._session_records_for_hit(by_session_id, turn_hit),
                    session_id=self._session_id_for_hit(turn_hit),
                    query=query,
                    base_score=float(turn_hit.get("score", 0.0)) + 1.0,
                )
                trace.constituent_expansions += int(added.get("added") or 0)
                trace.selector_expansions += int(added.get("selector_expansions") or 0)
                trace.selector_slot_coverage = max(trace.selector_slot_coverage, int(added.get("slot_coverage") or 0))
                trace.aggregation_safety_abstentions += int(added.get("aggregation_safety_abstentions") or 0)

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
        return route_plan.query_family in {QUERY_FAMILY_RELATION_MULTIHOP}

    @staticmethod
    def _needs_constituent_anchor_expansion(query: str, *, route_plan) -> bool:
        normalized_query = f" {re.sub(r'[^a-z0-9]+', ' ', str(query or '').strip().lower())} "
        if route_plan.query_family not in {
            QUERY_FAMILY_PERSONAL_RECALL,
            QUERY_FAMILY_FACTUAL_SUPPORTED,
            QUERY_FAMILY_RELATION_MULTIHOP,
            QUERY_FAMILY_UPDATE_RESOLUTION,
        }:
            return False
        aggregate_temporal_hints = (
            " average ",
            " percentage ",
            " percent ",
            " ratio ",
            " days passed ",
            " days ago ",
            " how many days ",
            " instead of ",
            " who became ",
            " more water ",
        )
        return any(hint in normalized_query for hint in aggregate_temporal_hints)

    @staticmethod
    def _session_lookup_keys(payload: Dict[str, Any]) -> List[str]:
        keys: List[str] = []
        session_id = str(payload.get("session_id") or "").strip()
        if session_id:
            keys.append(session_id)
        question_id = str(payload.get("question_id") or "").strip()
        session_index = str(payload.get("session_index") or "").strip()
        if question_id and session_index:
            keys.append(f"longmemeval:{question_id}:session:{session_index}")
        return keys

    @classmethod
    def _session_id_for_hit(cls, hit: Dict[str, Any]) -> str:
        keys = cls._session_lookup_keys(hit)
        if keys:
            return keys[0]
        return ""

    @classmethod
    def _session_records_for_hit(
        cls,
        by_session_id: Dict[str, List[Dict[str, Any]]],
        hit: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        for key in cls._session_lookup_keys(hit):
            records = by_session_id.get(key, [])
            if records:
                return records
        return []

    @classmethod
    def _session_id_for_records(cls, records: List[Dict[str, Any]]) -> str:
        for record in records:
            metadata = dict(record.get("metadata") or {})
            keys = cls._session_lookup_keys(metadata)
            if keys:
                return keys[0]
        return ""

    @classmethod
    def _session_records_for_records(
        cls,
        by_session_id: Dict[str, List[Dict[str, Any]]],
        records: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        for record in records:
            metadata = dict(record.get("metadata") or {})
            for key in cls._session_lookup_keys(metadata):
                related = by_session_id.get(key, [])
                if related:
                    return related
        return []

    def _search_query_shape_seed_variants(
        self,
        seed_queries: List[str],
        *,
        raw_limit: int,
        turn_limit: int,
        route_plan,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        if not seed_queries:
            return [], []
        raw_hits: List[Dict[str, Any]] = []
        turn_hits: List[Dict[str, Any]] = []
        for seed_query in seed_queries:
            for hit in self.store.search_raw_archive(
                seed_query,
                max_items=min(3, raw_limit),
                namespace_classes=None,
                source_first=False,
                exact_phrase=False,
            ):
                candidate = dict(hit)
                candidate["_seed_query"] = seed_query
                raw_hits.append(candidate)
            if self._allow_turn_scope(route_plan):
                for hit in self.store.search_turn_archive(seed_query, max_items=min(3, turn_limit)):
                    candidate = dict(hit)
                    candidate["_seed_query"] = seed_query
                    turn_hits.append(candidate)
        return raw_hits, turn_hits

    @staticmethod
    def _merge_seed_hits(base_hits: List[Dict[str, Any]], seed_hits: List[Dict[str, Any]], *, key: str) -> List[Dict[str, Any]]:
        merged: List[Dict[str, Any]] = [dict(hit) for hit in base_hits]
        seen = {str(hit.get(key) or "").strip() for hit in merged if str(hit.get(key) or "").strip()}
        for hit in seed_hits:
            hit_key = str(hit.get(key) or "").strip()
            if not hit_key or hit_key in seen:
                continue
            seen.add(hit_key)
            merged.append(dict(hit))
        return merged

    @staticmethod
    def _promote_session_anchors(
        promoted: Dict[str, Dict[str, Any]],
        *,
        session_records: List[Dict[str, Any]],
        session_id: str,
        query: str,
        base_score: float,
    ) -> Dict[str, int]:
        if not session_id or not session_records:
            return {
                "added": 0,
                "selector_expansions": 0,
                "slot_coverage": 0,
                "aggregation_safety_abstentions": 0,
            }
        normalized_query = f" {re.sub(r'[^a-z0-9$%]+', ' ', str(query or '').strip().lower())} "
        selector_shape = Core2HybridSubstrate._selector_shape(normalized_query)
        if not selector_shape:
            return {
                "added": 0,
                "selector_expansions": 0,
                "slot_coverage": 0,
                "aggregation_safety_abstentions": 0,
            }
        query_terms = {
            term
            for term in re.findall(r"[a-z0-9]+", str(query or "").lower())
            if len(term) >= 3 and term not in {"what", "when", "where", "which", "many", "much", "from", "with", "that", "this"}
        }
        chosen, slot_coverage, safety_abstained = Core2HybridSubstrate._select_budgeted_session_anchors(
            session_records=session_records,
            query_terms=query_terms,
            selector_shape=selector_shape,
        )
        if not chosen:
            return {
                "added": 0,
                "selector_expansions": 0,
                "slot_coverage": slot_coverage,
                "aggregation_safety_abstentions": 1 if safety_abstained else 0,
            }
        added = 0
        for offset, record in enumerate(chosen):
            candidate = dict(record)
            metadata = dict(candidate.get("metadata") or {})
            metadata["retrieval_path"] = "hybrid_scoped_turn"
            metadata["hybrid_scope"] = "session_anchor"
            metadata["hybrid_session_id"] = session_id
            metadata["hybrid_selector"] = "budgeted"
            metadata["hybrid_selector_shape"] = selector_shape
            candidate["metadata"] = metadata
            candidate["score"] = max(
                float(candidate.get("score", 0.0)),
                base_score + 0.25 - (offset * 0.05),
            )
            before = str(promoted.get(str(candidate.get("object_id") or "").strip(), {}).get("object_id") or "")
            Core2HybridSubstrate._upsert_promoted(promoted, candidate)
            after = str(promoted.get(str(candidate.get("object_id") or "").strip(), {}).get("object_id") or "")
            if after and after != before:
                added += 1
        return {
            "added": added,
            "selector_expansions": len(chosen),
            "slot_coverage": slot_coverage,
            "aggregation_safety_abstentions": 0,
        }

    @staticmethod
    def _selector_shape(normalized_query: str) -> str:
        if any(hint in normalized_query for hint in (" days passed ", " days ago ", " how many days ")):
            return "temporal_pair"
        if any(hint in normalized_query for hint in (" average ", " percentage ", " percent ", " ratio ")):
            return "numeric_pair"
        if any(hint in normalized_query for hint in (" instead of ", " more water ")):
            return "pairwise_compare"
        return ""

    @classmethod
    def _select_budgeted_session_anchors(
        cls,
        *,
        session_records: List[Dict[str, Any]],
        query_terms: Set[str],
        selector_shape: str,
    ) -> Tuple[List[Dict[str, Any]], int, bool]:
        candidates: List[Dict[str, Any]] = []
        seen: Set[str] = set()
        for record in session_records:
            prepared = cls._prepare_selector_candidate(record, query_terms=query_terms, selector_shape=selector_shape)
            if prepared is None:
                continue
            dedupe_key = str(prepared["dedupe_key"])
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            candidates.append(prepared)
        if not candidates:
            return [], 0, False

        selected: List[Dict[str, Any]] = []
        covered_slots: Set[str] = set()
        selected_units: Set[str] = set()
        selected_scopes: Set[str] = set()
        selected_windows: Set[str] = set()
        remaining_budget = 14.0

        while candidates and len(selected) < 4:
            best_index = -1
            best_score = float("-inf")
            for idx, candidate in enumerate(candidates):
                slot_gain = 0 if str(candidate["slot_key"]) in covered_slots else 1
                redundancy_penalty = 1.5 if any(str(candidate["dedupe_key"]) == str(item["dedupe_key"]) for item in selected) else 0.0
                conflict_penalty = 0.0
                if cls._would_violate_aggregation_safety(
                    candidate,
                    selector_shape=selector_shape,
                    selected_units=selected_units,
                    selected_scopes=selected_scopes,
                    selected_windows=selected_windows,
                ):
                    conflict_penalty = 3.0
                gain = (
                    float(candidate["query_relevance"])
                    + float(candidate["operator_fit"])
                    + (slot_gain * 3.0)
                    + float(candidate["supporting_fact_strength"])
                    + float(candidate["provenance_strength"])
                    + float(candidate["temporal_completeness"])
                    + float(candidate["numeric_executability"])
                    - redundancy_penalty
                    - conflict_penalty
                )
                score = gain / max(float(candidate["token_cost"]), 1.0)
                if score > best_score:
                    best_score = score
                    best_index = idx
            if best_index < 0:
                break
            chosen = candidates.pop(best_index)
            token_cost = float(chosen["token_cost"])
            if token_cost > remaining_budget and selected:
                break
            remaining_budget -= token_cost
            selected.append(chosen)
            covered_slots.add(str(chosen["slot_key"]))
            if str(chosen["unit"]):
                selected_units.add(str(chosen["unit"]))
            if str(chosen["scope"]):
                selected_scopes.add(str(chosen["scope"]))
            if str(chosen["time_window"]):
                selected_windows.add(str(chosen["time_window"]))
            if len(covered_slots) >= 2 and selector_shape in {"temporal_pair", "numeric_pair", "pairwise_compare"}:
                break

        slot_coverage = len(covered_slots)
        if slot_coverage < 2:
            return [], slot_coverage, False
        if not cls._passes_aggregation_safety(selected, selector_shape=selector_shape):
            return [], slot_coverage, True
        return [dict(item["record"]) for item in selected], slot_coverage, False

    @classmethod
    def _prepare_selector_candidate(
        cls,
        record: Dict[str, Any],
        *,
        query_terms: Set[str],
        selector_shape: str,
    ) -> Optional[Dict[str, Any]]:
        metadata = dict(record.get("metadata") or {})
        content = str(record.get("content") or "").lower()
        title = str(record.get("title") or "").lower()
        query_overlap = sum(1 for term in query_terms if term in content or term in title)
        temporal_explicit = int(any(record.get(field) for field in ("effective_from", "recorded_at", "observed_at")))
        quantitative = int(cls._looks_like_quantitative_anchor(record))
        if selector_shape == "temporal_pair" and temporal_explicit == 0:
            return None
        if selector_shape in {"numeric_pair", "pairwise_compare"} and quantitative == 0:
            return None
        supporting = 1.5 if bool(metadata.get("digest_fact")) else 0.5
        provenance = 1.0 if str(record.get("source_raw_id") or "").strip() else 0.5
        if metadata.get("digest_turn_id"):
            provenance += 0.5
        operator_fit = 1.0
        if selector_shape == "temporal_pair":
            operator_fit += temporal_explicit
        else:
            operator_fit += quantitative
        unit = str(metadata.get("unit") or cls._infer_unit(record)).strip().lower()
        scope = str(metadata.get("scope") or metadata.get("question_id") or "").strip().lower()
        time_window = str(metadata.get("time_window") or "").strip().lower()
        slot_key = cls._slot_key_for_record(record, selector_shape=selector_shape)
        dedupe_key = str(metadata.get("identity_key") or slot_key or record.get("object_id") or "").strip().lower()
        token_cost = max(1.0, len(str(record.get("content") or "")) / 80.0)
        return {
            "record": record,
            "query_relevance": float(query_overlap),
            "operator_fit": float(operator_fit),
            "supporting_fact_strength": float(supporting),
            "provenance_strength": float(provenance),
            "temporal_completeness": float(temporal_explicit),
            "numeric_executability": float(quantitative),
            "token_cost": token_cost,
            "slot_key": slot_key,
            "dedupe_key": dedupe_key,
            "unit": unit,
            "scope": scope,
            "time_window": time_window,
        }

    @staticmethod
    def _slot_key_for_record(record: Dict[str, Any], *, selector_shape: str) -> str:
        metadata = dict(record.get("metadata") or {})
        if selector_shape == "temporal_pair":
            for field in ("effective_from", "recorded_at", "observed_at"):
                value = str(record.get(field) or "").strip()
                if value:
                    return value
        return str(metadata.get("identity_key") or record.get("object_id") or record.get("content") or "").strip().lower()

    @staticmethod
    def _infer_unit(record: Dict[str, Any]) -> str:
        blob = " ".join(
            [
                str(record.get("title") or ""),
                str(record.get("content") or ""),
            ]
        ).lower()
        if "$" in blob or " usd" in blob or " dollar" in blob:
            return "money"
        if "%" in blob or " percent" in blob or " percentage" in blob:
            return "percent"
        if " day " in blob or " days " in blob:
            return "days"
        if " oz" in blob or " ounce" in blob or " ounces" in blob:
            return "ounces"
        return ""

    @staticmethod
    def _would_violate_aggregation_safety(
        candidate: Dict[str, Any],
        *,
        selector_shape: str,
        selected_units: Set[str],
        selected_scopes: Set[str],
        selected_windows: Set[str],
    ) -> bool:
        if selector_shape not in {"numeric_pair", "pairwise_compare"}:
            return False
        unit = str(candidate.get("unit") or "").strip()
        if unit and selected_units and unit not in selected_units:
            return True
        scope = str(candidate.get("scope") or "").strip()
        if scope and selected_scopes and scope not in selected_scopes:
            return True
        window = str(candidate.get("time_window") or "").strip()
        if window and selected_windows and window not in selected_windows:
            return True
        return False

    @classmethod
    def _passes_aggregation_safety(cls, selected: List[Dict[str, Any]], *, selector_shape: str) -> bool:
        if len(selected) < 2:
            return False
        if selector_shape == "temporal_pair":
            temporal = [item for item in selected if any(item["record"].get(field) for field in ("effective_from", "recorded_at", "observed_at"))]
            return len(temporal) >= 2
        units = {str(item.get("unit") or "").strip() for item in selected if str(item.get("unit") or "").strip()}
        scopes = {str(item.get("scope") or "").strip() for item in selected if str(item.get("scope") or "").strip()}
        windows = {str(item.get("time_window") or "").strip() for item in selected if str(item.get("time_window") or "").strip()}
        if len(units) > 1:
            return False
        if len(scopes) > 1:
            return False
        if len(windows) > 1:
            return False
        return all(bool(item.get("numeric_executability")) for item in selected)

    @staticmethod
    def _looks_like_quantitative_anchor(record: Dict[str, Any]) -> bool:
        blob = " ".join(
            [
                str(record.get("title") or ""),
                str(record.get("content") or ""),
                str(record.get("effective_from") or ""),
                str(record.get("recorded_at") or ""),
                str(record.get("observed_at") or ""),
            ]
        ).lower()
        if re.search(r"\d", blob):
            return True
        if any(token in blob for token in ("$", "%", "percent", "percentage", "day ", "days ", "oz", "ounce", "tablespoon")):
            return True
        if any(
            word in blob
            for word in (
                " one ",
                " two ",
                " three ",
                " four ",
                " five ",
                " six ",
                " seven ",
                " eight ",
                " nine ",
                " ten ",
                " january ",
                " february ",
                " march ",
                " april ",
                " may ",
                " june ",
                " july ",
                " august ",
                " september ",
                " october ",
                " november ",
                " december ",
            )
        ):
            return True
        return False

    @staticmethod
    def _scope_label(*, route_plan, namespace_classes: Optional[List[str]]) -> str:
        wings = ",".join(namespace_classes or ["all"])
        room = "turn+raw" if Core2HybridSubstrate._allow_turn_scope(route_plan) else "raw"
        return f"{wings}:{room}"
