from __future__ import annotations

import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple

from agent.core2_answer import build_answer_packet
from agent.core2_authoritative import build_answer_surface
from agent.core2_digestion import digest_memory_content, digest_turn_content
from agent.core2_fact_registry import get_covered_fact_spec
from agent.core2_fact_registry import match_query_to_fact_keys
from agent.core2_hybrid_substrate import Core2HybridSubstrate
from agent.core2_maintenance import Core2MaintenanceEngine
from agent.core2_policy import can_recall_record, classify_namespace
from agent.core2_routing import build_route_plan, is_conversation_reference_query
from agent.core2_store import Core2Store
from agent.core2_types import (
    EDGE_DERIVED_FROM,
    Core2RecallItem,
    Core2RecallPacket,
    PLANE_CANONICAL_TRUTH,
    MODE_EXACT_SOURCE_REQUIRED,
    QUERY_FAMILY_EXACT_LOOKUP,
    QUERY_FAMILY_EXPLORATORY_DISCOVERY,
    QUERY_FAMILY_HIGH_RISK_STRICT,
    QUERY_FAMILY_PERSONAL_RECALL,
    QUERY_FAMILY_RELATION_MULTIHOP,
    QUERY_FAMILY_UPDATE_RESOLUTION,
    SUPPORT_EXACT_SOURCE,
    SUPPORT_NONE,
    SUPPORT_SOURCE_SUPPORTED,
    SUPPORT_WEAK,
)


class Core2Runtime:
    """Plane-aware local-first runtime for the Core2 provider."""

    def __init__(self, db_path: str, *, hybrid_substrate_mode: str | None = None):
        self.db_path = str(Path(db_path))
        self.store = Core2Store(self.db_path)
        self.hybrid_substrate = Core2HybridSubstrate(
            self.store,
            mode=hybrid_substrate_mode
            or str(os.environ.get("CORE2_HYBRID_SUBSTRATE_MODE") or "on"),
        )
        self.maintenance = Core2MaintenanceEngine(self.store)
        self._prefetch_cache: Dict[str, str] = {}
        self._session_id = ""

    def initialize(self, session_id: str) -> None:
        self.store.connect()
        self._session_id = session_id

    def note_count(self) -> int:
        return self.store.note_count()

    def plane_counts(self) -> Dict[str, int]:
        return self.store.plane_counts()

    def consume_prefetch(self, *, session_id: str = "") -> str:
        key = session_id or self._session_id
        return self._prefetch_cache.pop(key, "")

    def queue_prefetch(self, query: str, *, session_id: str = "") -> None:
        key = session_id or self._session_id
        packet = self.recall(
            query,
            mode="compact_memory",
            operator=None,
            risk_class="standard",
            max_items=3,
        )
        if packet.abstained or not packet.items:
            self._prefetch_cache[key] = ""
            return
        surface = packet.answer_surface.to_dict() if packet.answer_surface else None
        if (
            surface
            and str(surface.get("mode") or "").strip().lower() != "fallback"
            and str(surface.get("text") or "").strip()
        ):
            lines = ["# Core2 Answer Surface", str(surface.get("text") or "").strip()]
            summary = str(surface.get("summary") or "").strip()
            if summary:
                lines.append(summary)
        else:
            lines = ["# Core2 Prefetch"]
            if packet.display_value:
                lines.append(packet.display_value)
            for item in packet.items[:2]:
                lines.append(f"- [{item.namespace}] {item.title}: {item.snippet}")
        self._prefetch_cache[key] = "\n".join(lines)

    def ingest_turn(
        self, user_content: str, assistant_content: str, *, session_id: str = ""
    ) -> Dict[str, Any]:
        key = session_id or self._session_id
        turn = self.store.add_turn(
            session_id=key,
            user_content=user_content,
            assistant_content=assistant_content,
        )
        self._materialize_turn_facts(
            user_content=user_content,
            assistant_content=assistant_content,
            session_id=key,
            turn=turn,
        )
        return turn

    def recall(
        self,
        query: str,
        *,
        mode: str = "auto",
        operator: Optional[str] = None,
        risk_class: str = "standard",
        max_items: int = 6,
    ) -> Core2RecallPacket:
        normalized_query = (
            f" {re.sub(r'[^a-z0-9]+', ' ', str(query or '').casefold()).strip()} "
        )
        if max_items < 8 and any(
            marker in normalized_query
            for marker in (
                " in total ",
                " order ",
                " instead of ",
                " first ",
                " last ",
                " need to ",
            )
        ):
            max_items = 8
        max_items = max(1, min(int(max_items), 12))
        route_plan = build_route_plan(
            query,
            mode=mode,
            operator=operator,
            risk_class=risk_class,
            max_items=max_items,
        )
        results = self._retrieve_candidates(query, route_plan=route_plan)
        if not results:
            return self._abstain_packet(
                query,
                operator=operator,
                risk_class=risk_class,
                route_plan=route_plan,
                reason="No stored Core2 notes matched the query.",
            )

        items, abstain_reason = self._filter_and_shape_items(
            results,
            query=query,
            route_plan=route_plan,
            risk_class=risk_class,
        )
        if not items:
            return self._abstain_packet(
                query,
                operator=operator,
                risk_class=risk_class,
                route_plan=route_plan,
                reason=abstain_reason
                or "No active Core2 records satisfied the recall policy.",
            )

        conflict_refs = sorted(
            {ref for item in items for ref in item.metadata.get("conflict_refs", [])}
        )

        if route_plan.query_family == QUERY_FAMILY_RELATION_MULTIHOP and len(items) < 2:
            return self._abstain_packet(
                query,
                operator=operator,
                risk_class=risk_class,
                route_plan=route_plan,
                reason="Relation route requires a complete evidence chain; only one grounded node was found.",
            )
        if (
            route_plan.query_family
            in {QUERY_FAMILY_HIGH_RISK_STRICT, QUERY_FAMILY_UPDATE_RESOLUTION}
            and conflict_refs
        ):
            return self._abstain_packet(
                query,
                operator=operator,
                risk_class=risk_class,
                route_plan=route_plan,
                reason="Strict route encountered unresolved conflict markers.",
                conflict_refs=conflict_refs,
            )
        if route_plan.query_family == QUERY_FAMILY_EXACT_LOOKUP:
            top = items[0]
            normalized_query = " ".join(query.strip().lower().split())
            haystack = f"{top.title} {top.content}".lower()
            if normalized_query not in haystack and top.score < 3.0:
                return self._abstain_packet(
                    query,
                    operator=operator,
                    risk_class=risk_class,
                    route_plan=route_plan,
                    reason="Exact lookup requires precise evidence, but only loose matches were found.",
                )

        support_tier = self._support_tier_for_route(route_plan.query_mode, items)
        (
            support_confidence,
            temporal_confidence,
            resolution_confidence,
            identity_confidence,
        ) = self._confidence_dimensions(items, route_plan=route_plan)
        confidence = self._overall_confidence(
            support_confidence=support_confidence,
            temporal_confidence=temporal_confidence,
            resolution_confidence=resolution_confidence,
            identity_confidence=identity_confidence,
        )
        top = items[0]

        packet = build_answer_packet(
            query=query,
            operator=operator,
            risk_class=risk_class,
            route_plan=route_plan,
            items=items,
            support_tier=support_tier,
            confidence=confidence,
            support_confidence=support_confidence,
            temporal_confidence=temporal_confidence,
            resolution_confidence=resolution_confidence,
            identity_confidence=identity_confidence,
            abstained=False,
            reason=None,
            delivery_resolver=self._resolve_delivery_view,
            valid_as_of=top.effective_from or top.source_created_at or top.recorded_at,
            superseded_by=top.metadata.get("superseded_by"),
            conflict_refs=conflict_refs,
        )
        packet.answer_surface = build_answer_surface(query, packet)
        return packet

    def ingest_note(
        self,
        content: str,
        *,
        title: str,
        namespace: str,
        risk_class: str = "standard",
        language: str = "und",
        effective_from: Optional[str] = None,
        source_type: str = "explicit_memory",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload = dict(metadata or {})
        object_kind = payload.pop("object_kind", None)
        state_status = payload.pop("state_status", None)
        stored = self.store.add_memory(
            content=content,
            title=title,
            namespace=namespace,
            risk_class=risk_class,
            language=language,
            source_type=source_type,
            effective_from=effective_from,
            metadata=payload,
            object_kind=object_kind,
            state_status=state_status,
        )
        if source_type not in {
            "digested_fact",
            "turn_digested_fact",
            "extract_candidate",
        }:
            self._materialize_memory_facts(
                content=content,
                title=title,
                namespace=namespace,
                risk_class=risk_class,
                language=language,
                source_record=stored,
            )
        return stored

    def ingest_proposition(
        self,
        claim_text: str,
        *,
        title: str,
        namespace: str,
        risk_class: str = "standard",
        language: str = "und",
        source_object_ids: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return self.store.add_proposition(
            claim_text=claim_text,
            title=title,
            namespace=namespace,
            risk_class=risk_class,
            language=language,
            source_object_ids=source_object_ids or [],
            metadata=metadata,
        )

    def record_candidate_extract(
        self,
        content: str,
        *,
        title: str,
        namespace: str,
        risk_class: str = "standard",
        language: str = "und",
        source_type: str = "extract_candidate",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload = dict(metadata or {})
        payload["state_status"] = "candidate"
        return self.ingest_note(
            content,
            title=title,
            namespace=namespace,
            risk_class=risk_class,
            language=language,
            source_type=source_type,
            metadata=payload,
        )

    def promote_candidate(
        self, object_id: str, *, reason: str = "candidate_promoted"
    ) -> bool:
        return self.store.update_canonical_state(object_id, "canonical_active", reason)

    def reject_candidate(
        self, object_id: str, *, reason: str = "candidate_rejected"
    ) -> bool:
        return self.store.update_canonical_state(object_id, "rejected", reason)

    def archive_object(self, object_id: str, *, reason: str = "archived") -> bool:
        return self.store.archive_object(object_id, reason)

    def supersede_object(
        self, new_object_id: str, old_object_id: str, *, reason: str = "superseded"
    ) -> bool:
        return self.store.supersede_object(new_object_id, old_object_id, reason)

    def mark_conflict(
        self, left_object_id: str, right_object_id: str, *, reason: str = "conflict"
    ) -> bool:
        return self.store.mark_conflict(left_object_id, right_object_id, reason)

    def run_maintenance(
        self, *, now: str | None = None, stale_days: int = 30
    ) -> Dict[str, Any]:
        return self.maintenance.run_all(now=now, stale_days=stale_days)

    def explain_object(self, object_id: str) -> Dict[str, Any]:
        record = self.store.get_canonical_object(object_id)
        if record is None:
            return {"error": f"Core2 object not found: {object_id}"}
        return {
            **record,
            "source_record": self.store.get_raw_archive(record["source_raw_id"]),
            "edges": self.store.get_edges(object_id),
            "delivery_views": self.store.get_delivery_views(object_id),
            "retrieval_indices": self.store.get_retrieval_indices(object_id),
            "transitions": self.store.get_transitions(object_id),
        }

    def shutdown(self) -> None:
        self.store.close()

    def _should_digest(self, *, namespace: str, risk_class: str) -> bool:
        namespace_class = classify_namespace(namespace)
        normalized_risk = str(risk_class or "").strip().lower()
        return namespace_class in {"personal", "workspace"} and normalized_risk in {
            "",
            "standard",
        }

    def _materialize_memory_facts(
        self,
        *,
        content: str,
        title: str,
        namespace: str,
        risk_class: str,
        language: str,
        source_record: Dict[str, Any],
    ) -> None:
        if not self._should_digest(namespace=namespace, risk_class=risk_class):
            return
        candidates = digest_memory_content(content)
        if not candidates:
            return
        for candidate in candidates:
            metadata = dict(candidate.metadata)
            metadata.update(
                {
                    "digest_origin": "remember",
                    "digest_parent_object_id": source_record["object_id"],
                    "digest_source_raw_id": source_record["source_raw_id"],
                    "fact_title": candidate.title,
                    "observed_at": source_record.get("observed_at"),
                    "source_created_at": source_record.get("source_created_at"),
                    "effective_from": source_record.get("effective_from"),
                    "recorded_at": source_record.get("recorded_at"),
                }
            )
            fact_record = self._upsert_digested_fact(
                title=candidate.title,
                content=candidate.content,
                namespace=namespace,
                risk_class=risk_class,
                language=language,
                metadata=metadata,
                source_type="digested_fact",
                object_kind=candidate.object_kind,
            )
            self.store.add_edge(
                from_plane=PLANE_CANONICAL_TRUTH,
                from_id=fact_record["object_id"],
                to_plane=PLANE_CANONICAL_TRUTH,
                to_id=source_record["object_id"],
                edge_type=EDGE_DERIVED_FROM,
                metadata={"origin": "write_time_digestion"},
            )
            derived_total = self._maybe_materialize_collection_total_update(
                fact_record=fact_record,
                namespace=namespace,
                risk_class=risk_class,
                language=language,
                parent_metadata=metadata,
            )
            if derived_total is not None:
                self.store.begin_transaction()
                try:
                    self.store.add_edge(
                        from_plane=PLANE_CANONICAL_TRUTH,
                        from_id=derived_total["object_id"],
                        to_plane=PLANE_CANONICAL_TRUTH,
                        to_id=fact_record["object_id"],
                        edge_type=EDGE_DERIVED_FROM,
                        metadata={"origin": "write_time_collection_update"},
                    )
                    self.store.commit()
                except Exception:
                    self.store.rollback()
                    raise

    def _materialize_turn_facts(
        self,
        *,
        user_content: str,
        assistant_content: str,
        session_id: str,
        turn: Dict[str, Any],
    ) -> None:
        if not user_content.strip():
            return
        candidates = digest_turn_content(user_content, assistant_content)
        if not candidates:
            return
        for candidate in candidates:
            metadata = dict(candidate.metadata)
            metadata.update(
                {
                    "digest_origin": "turn",
                    "digest_turn_id": turn["turn_id"],
                    "session_id": session_id,
                    "observed_at": turn["created_at"],
                    "source_created_at": turn["created_at"],
                    "effective_from": turn["created_at"],
                    "recorded_at": turn["created_at"],
                    "fact_title": candidate.title,
                }
            )
            fact_record = self._upsert_digested_fact(
                title=candidate.title,
                content=candidate.content,
                namespace="personal",
                risk_class="standard",
                language="en",
                metadata=metadata,
                source_type="turn_digested_fact",
                object_kind=candidate.object_kind,
            )
            self._maybe_materialize_collection_total_update(
                fact_record=fact_record,
                namespace="personal",
                risk_class="standard",
                language="en",
                parent_metadata=metadata,
            )

    def _maybe_materialize_collection_total_update(
        self,
        *,
        fact_record: Dict[str, Any],
        namespace: str,
        risk_class: str,
        language: str,
        parent_metadata: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        metadata = dict(fact_record.get("metadata") or {})
        if (
            str(metadata.get("fact_key") or "").strip().lower()
            != "event.collection.item_added"
        ):
            return None
        delta = int(metadata.get("delta") or 0)
        if delta <= 0:
            return None

        for record in self.store.list_canonical_objects():
            record_metadata = dict(record.get("metadata") or {})
            if (
                str(record_metadata.get("fact_key") or "").strip().lower()
                != "aggregate.collection.total.current"
            ):
                continue
            if (
                str(record_metadata.get("last_update_event_id") or "").strip()
                == str(fact_record.get("object_id") or "").strip()
            ):
                return record

        existing = self._find_collection_total_record(
            collection_label=str(metadata.get("collection_label") or "").strip(),
            item_noun=str(metadata.get("item_noun") or "").strip().lower(),
            namespace=namespace,
        )
        if existing is None:
            return None

        try:
            previous_total = int(
                str(existing.get("metadata", {}).get("canonical_value") or "").strip()
            )
        except ValueError:
            return None

        spec = get_covered_fact_spec("aggregate.collection.total.current")
        if spec is None:
            return None

        existing_metadata = dict(existing.get("metadata") or {})
        collection_label = str(
            existing_metadata.get("collection_label")
            or metadata.get("collection_label")
            or ""
        ).strip()
        item_noun = (
            str(existing_metadata.get("item_noun") or metadata.get("item_noun") or "")
            .strip()
            .lower()
        )
        new_total = previous_total + delta
        derived_metadata = dict(spec.extra_metadata)
        derived_metadata.update(
            {
                "digest_fact": True,
                "fact_kind": spec.fact_kind,
                "fact_key": spec.fact_key,
                "collection_label": collection_label,
                "item_noun": item_noun,
                "aggregate_count": new_total,
                "identity_key": str(
                    existing_metadata.get("identity_key")
                    or f"digest:{spec.fact_key}:{collection_label}"
                ),
                "canonical_value": str(new_total),
                "last_update_event_id": fact_record.get("object_id"),
                "keywords": f"{spec.keywords} {collection_label.lower()} {item_noun}".strip(),
                "digest_origin": metadata.get("digest_origin"),
                "digest_parent_object_id": metadata.get("digest_parent_object_id"),
                "digest_turn_id": metadata.get("digest_turn_id"),
                "observed_at": parent_metadata.get("observed_at"),
                "source_created_at": parent_metadata.get("source_created_at"),
                "effective_from": parent_metadata.get("effective_from"),
                "recorded_at": parent_metadata.get("recorded_at"),
            }
        )
        return self._upsert_digested_fact(
            title=spec.title,
            content=f"{spec.title}: {new_total} ({collection_label})",
            namespace=namespace,
            risk_class=risk_class,
            language=language,
            metadata=derived_metadata,
            source_type="digested_fact",
            object_kind=spec.object_kind,
        )

    def _find_collection_total_record(
        self, *, collection_label: str, item_noun: str, namespace: str
    ) -> Optional[Dict[str, Any]]:
        label_norm = str(collection_label or "").strip().lower()
        noun_norm = str(item_noun or "").strip().lower()
        matches: List[Dict[str, Any]] = []
        for record in self.store.list_canonical_objects(include_inactive=False):
            metadata = dict(record.get("metadata") or {})
            if not metadata.get("digest_fact"):
                continue
            if (
                str(metadata.get("fact_key") or "").strip().lower()
                != "aggregate.collection.total.current"
            ):
                continue
            if record.get("namespace") != namespace:
                continue
            record_label = str(metadata.get("collection_label") or "").strip().lower()
            record_noun = str(metadata.get("item_noun") or "").strip().lower()
            if (
                label_norm
                and record_label
                and (label_norm in record_label or record_label in label_norm)
            ):
                matches.append(record)
                continue
            if noun_norm and record_noun == noun_norm:
                matches.append(record)
        if label_norm:
            return matches[0] if matches else None
        return matches[0] if len(matches) == 1 else None

    def _upsert_digested_fact(
        self,
        *,
        title: str,
        content: str,
        namespace: str,
        risk_class: str,
        language: str,
        metadata: Dict[str, Any],
        source_type: str,
        object_kind: str,
    ) -> Dict[str, Any]:
        identity_key = str(metadata.get("identity_key") or "").strip()
        canonical_value = str(metadata.get("canonical_value") or "").strip().lower()
        if identity_key:
            existing_records = self.store.find_canonical_by_identity_key(identity_key)
            for existing in existing_records:
                existing_value = (
                    str(existing.get("metadata", {}).get("canonical_value") or "")
                    .strip()
                    .lower()
                )
                if (
                    existing["state_status"] == "canonical_active"
                    and existing_value == canonical_value
                ):
                    return existing

        stored = self.store.add_memory(
            content=content,
            title=title,
            namespace=namespace,
            risk_class=risk_class,
            language=language,
            source_type=source_type,
            effective_from=str(metadata.get("effective_from") or "").strip() or None,
            metadata=metadata,
            object_kind=object_kind,
            state_status="canonical_active",
        )

        if identity_key:
            for existing in self.store.find_canonical_by_identity_key(identity_key):
                if existing["object_id"] == stored["object_id"]:
                    continue
                if existing["state_status"] != "canonical_active":
                    continue
                existing_value = (
                    str(existing.get("metadata", {}).get("canonical_value") or "")
                    .strip()
                    .lower()
                )
                if existing_value == canonical_value:
                    continue
                self.store.supersede_object(
                    stored["object_id"],
                    existing["object_id"],
                    reason="write_time_fact_update",
                )
        return self.store.get_canonical_object(stored["object_id"]) or stored

    def _retrieve_candidates(self, query: str, *, route_plan) -> List[Dict[str, Any]]:
        # Invariant: covered personal/update queries should hit the write-time fact substrate first.
        # Broader canonical retrieval remains mandatory fallback, not a removed path.
        namespace_classes: Optional[List[str]] = None
        source_first = False
        exact_phrase = False
        if route_plan.query_family == QUERY_FAMILY_PERSONAL_RECALL:
            namespace_classes = ["personal", "workspace"]
        elif route_plan.query_family == QUERY_FAMILY_HIGH_RISK_STRICT:
            namespace_classes = ["high_risk"]
            source_first = True
            exact_phrase = True
        elif route_plan.query_family in {
            QUERY_FAMILY_EXACT_LOOKUP,
            QUERY_FAMILY_UPDATE_RESOLUTION,
        }:
            source_first = True
            exact_phrase = True

        fact_results = self._retrieve_fact_first_candidates(
            query,
            route_plan=route_plan,
            namespace_classes=namespace_classes,
        )
        if fact_results:
            route_plan.notes.append("fact_first_hit")
        elif self._fact_first_keys_for_query(query, route_plan=route_plan):
            route_plan.notes.append("fact_first_fallback")

        hybrid_results: List[Dict[str, Any]] = []
        hybrid_trace: Dict[str, Any] = {}
        if self.hybrid_substrate.enabled:
            hybrid_results, hybrid_trace = self.hybrid_substrate.search(
                query,
                route_plan=route_plan,
                max_items=route_plan.retrieval_cap,
                namespace_classes=namespace_classes,
                source_first=source_first,
                exact_phrase=exact_phrase,
            )
            if int(hybrid_trace.get("raw_hits") or 0) > 0:
                route_plan.notes.append("hybrid_raw_hit")
            if int(hybrid_trace.get("turn_hits") or 0) > 0:
                route_plan.notes.append("hybrid_turn_hit")
            if str(hybrid_trace.get("query_shape_operator_family") or "").strip():
                route_plan.notes.append("hybrid_query_shape_schema")
            if str(hybrid_trace.get("query_shape_signal_family") or "").strip():
                route_plan.notes.append("hybrid_query_signal_primitive")
            if int(hybrid_trace.get("query_shape_seed_expansions") or 0) > 0:
                route_plan.notes.append("hybrid_query_shape_seed")
            if int(hybrid_trace.get("constituent_expansions") or 0) > 0:
                route_plan.notes.append("hybrid_constituent_expand")
            if int(hybrid_trace.get("selector_expansions") or 0) > 0:
                route_plan.notes.append("hybrid_budgeted_selector")
            if int(hybrid_trace.get("aggregation_safety_abstentions") or 0) > 0:
                route_plan.notes.append("hybrid_aggregation_safety_abstain")
            if self.hybrid_substrate.shadow_only:
                route_plan.notes.append("hybrid_shadow_only")

        lexical_results = self.store.search_canonical(
            query,
            max_items=route_plan.retrieval_cap,
            namespace_classes=namespace_classes,
            source_first=source_first,
            exact_phrase=exact_phrase,
        )
        results = lexical_results

        if hybrid_results and not self.hybrid_substrate.shadow_only:
            results = self._merge_ranked_candidates(
                hybrid_results, lexical_results, limit=route_plan.retrieval_cap
            )

        if fact_results:
            merged: List[Dict[str, Any]] = []
            seen_ids = set()
            for record in fact_results + results:
                object_id = str(record.get("object_id") or "")
                if not object_id or object_id in seen_ids:
                    continue
                seen_ids.add(object_id)
                merged.append(record)
                if len(merged) >= route_plan.retrieval_cap:
                    break
            results = merged

        if (
            route_plan.query_family == QUERY_FAMILY_PERSONAL_RECALL
            and is_conversation_reference_query(query)
        ):
            route_plan.notes.append("conversation_reference_expand")
            results = self._expand_conversation_reference_candidates(
                results, query=query, limit=max(route_plan.retrieval_cap * 3, 8)
            )

        if route_plan.query_family in {
            QUERY_FAMILY_RELATION_MULTIHOP,
            QUERY_FAMILY_EXPLORATORY_DISCOVERY,
        }:
            expanded = list(results)
            for seed in results[:2]:
                for related in self.store.get_related_records(
                    seed["object_id"],
                    max_hops=max(1, route_plan.graph_hops),
                    limit=route_plan.retrieval_cap,
                ):
                    if any(
                        existing["object_id"] == related["object_id"]
                        for existing in expanded
                    ):
                        continue
                    related["score"] = float(seed.get("score", 0.0)) - 0.25
                    expanded.append(related)
                    if len(expanded) >= route_plan.retrieval_cap:
                        break
                if len(expanded) >= route_plan.retrieval_cap:
                    break
            results = expanded[: route_plan.retrieval_cap]

        return results

    @staticmethod
    def _merge_ranked_candidates(
        primary: List[Dict[str, Any]],
        secondary: List[Dict[str, Any]],
        *,
        limit: int,
    ) -> List[Dict[str, Any]]:
        best_by_id: Dict[str, Dict[str, Any]] = {}
        for record in list(primary):
            object_id = str(record.get("object_id") or "")
            if not object_id:
                continue
            best_by_id[object_id] = dict(record)

        for record in list(secondary):
            object_id = str(record.get("object_id") or "")
            if not object_id:
                continue
            current = best_by_id.get(object_id)
            if current is None:
                best_by_id[object_id] = dict(record)
                continue
            current["score"] = max(
                float(current.get("score", 0.0)), float(record.get("score", 0.0))
            )

        merged = sorted(
            best_by_id.values(),
            key=lambda item: (
                float(item.get("score", 0.0)),
                item.get("updated_at") or "",
            ),
            reverse=True,
        )
        return merged[:limit]

    def _expand_conversation_reference_candidates(
        self,
        results: List[Dict[str, Any]],
        *,
        query: str,
        limit: int,
    ) -> List[Dict[str, Any]]:
        if not results:
            return results
        candidate_sessions: List[int] = []
        for record in results[:3]:
            metadata = dict(record.get("metadata") or {})
            session_index = metadata.get("session_index")
            if (
                isinstance(session_index, int)
                and session_index not in candidate_sessions
            ):
                candidate_sessions.append(session_index)
        if not candidate_sessions:
            return results

        expanded = list(results)
        seen_ids = {str(record.get("object_id") or "") for record in expanded}
        for session_index in candidate_sessions:
            for candidate in self.store.search_session_records(
                session_index, query, max_items=limit, turns_only=True
            ):
                object_id = str(candidate.get("object_id") or "")
                if not object_id or object_id in seen_ids:
                    continue
                seen_ids.add(object_id)
                expanded.append(candidate)
                if len(expanded) >= limit:
                    break
            if len(expanded) >= limit:
                break
        return expanded

    def _retrieve_fact_first_candidates(
        self,
        query: str,
        *,
        route_plan,
        namespace_classes: Optional[List[str]],
    ) -> List[Dict[str, Any]]:
        fact_keys = self._fact_first_keys_for_query(query, route_plan=route_plan)
        if not fact_keys:
            return []

        records = self.store.search_digested_facts(
            query,
            max_items=route_plan.retrieval_cap,
            fact_keys=fact_keys,
            namespace_classes=namespace_classes,
        )
        annotated: List[Dict[str, Any]] = []
        for record in records:
            candidate = dict(record)
            metadata = dict(candidate.get("metadata") or {})
            metadata["retrieval_path"] = "fact_first"
            metadata["retrieval_fact_keys"] = list(fact_keys)
            if fact_keys:
                metadata["retrieval_fact_key"] = fact_keys[0]
            candidate["metadata"] = metadata
            annotated.append(candidate)
        return annotated

    @staticmethod
    def _fact_first_keys_for_query(query: str, *, route_plan) -> List[str]:
        if route_plan.query_family not in {
            QUERY_FAMILY_PERSONAL_RECALL,
            QUERY_FAMILY_UPDATE_RESOLUTION,
        }:
            return []
        return match_query_to_fact_keys(query)

    def _filter_and_shape_items(
        self,
        results: List[Dict[str, Any]],
        *,
        query: str,
        route_plan,
        risk_class: str,
    ) -> Tuple[List[Core2RecallItem], Optional[str]]:
        allowed: List[Dict[str, Any]] = []
        abstain_reason = None
        for record in results:
            is_allowed, reason = can_recall_record(
                record, mode=route_plan.query_mode, query_risk_class=risk_class
            )
            if is_allowed:
                allowed.append(record)
            elif abstain_reason is None:
                abstain_reason = reason

        if route_plan.query_family == QUERY_FAMILY_UPDATE_RESOLUTION:
            allowed = self._resolve_current_records(allowed)
            if not allowed and abstain_reason is None:
                abstain_reason = "Update-resolution route could not identify a current canonical record."
            allowed = self._prioritize_personal_records(allowed, query=query)
        elif route_plan.query_family == QUERY_FAMILY_PERSONAL_RECALL:
            allowed = self._prioritize_personal_records(allowed, query=query)

        items = [
            self._record_to_item(record)
            for record in allowed[: route_plan.retrieval_cap]
        ]
        return items, abstain_reason

    @staticmethod
    def _prioritize_personal_records(
        records: List[Dict[str, Any]], *, query: str
    ) -> List[Dict[str, Any]]:
        if not records:
            return records
        normalized_query = (
            f" {re.sub(r'[^a-z0-9]+', ' ', (query or '').strip().lower())} "
        )
        temporal_compare = any(
            hint in normalized_query
            for hint in (
                " first ",
                " last ",
                " before ",
                " after ",
                " earlier ",
                " later ",
                " order ",
                " finished ",
            )
        )
        quoted_entities = [
            str(value).strip().lower()
            for value in re.findall(r"['\"]([^'\"]+)['\"]", str(query or ""))
            if str(value).strip()
        ]
        query_terms = {
            term
            for term in re.findall(r"[a-z0-9]+", str(query or "").lower())
            if len(term) >= 3
            and term
            not in {
                "what",
                "when",
                "where",
                "which",
                "many",
                "much",
                "your",
                "with",
                "from",
            }
        }
        conversation_reference = is_conversation_reference_query(query)

        def _record_rank(record: Dict[str, Any]) -> tuple[Any, ...]:
            metadata = dict(record.get("metadata") or {})
            temporal_explicit = any(
                record.get(field)
                for field in (
                    "effective_from",
                    "source_created_at",
                    "recorded_at",
                    "observed_at",
                )
            )
            fact_first_signal = int(metadata.get("retrieval_path") == "fact_first")
            digested_fact_signal = int(bool(metadata.get("digest_fact")))
            granular = (
                bool(metadata.get("turn_index"))
                or "turn" in str(record.get("title") or "").lower()
            )
            content = str(record.get("content") or "")
            content_lower = content.lower()
            title = str(record.get("title") or "").lower()
            entity_mentions = sum(
                1
                for entity in quoted_entities
                if entity in content_lower or entity in title
            )
            term_overlap = sum(
                1 for term in query_terms if term in content_lower or term in title
            )
            shorter = -min(len(content), 4000)
            finished_signal = int(
                "finish" in content_lower or "finish" in title or "read" in title
            )
            example_signal = int(
                "example" in content_lower
                or "mentioned" in content_lower
                or "user asked:" in content_lower
            )
            media_signal = int(
                any(
                    marker in content_lower
                    for marker in (
                        " show ",
                        " series ",
                        " movie ",
                        " season ",
                        " netflix ",
                    )
                )
            )
            attribute_signal = int(
                any(
                    marker in content_lower
                    for marker in (
                        "worked as",
                        "work as",
                        "role as",
                        "previous role",
                        "used to work",
                        "total of",
                        "combined",
                    )
                )
            )
            return (
                fact_first_signal,
                digested_fact_signal,
                term_overlap + (2 if conversation_reference and granular else 0),
                example_signal if conversation_reference else 0,
                media_signal if conversation_reference else 0,
                entity_mentions,
                attribute_signal,
                int(granular),
                int(temporal_explicit),
                finished_signal if temporal_compare else 0,
                shorter,
                float(record.get("score", 0.0)),
                record.get("effective_from") or "",
                record.get("recorded_at") or "",
                record.get("updated_at") or "",
            )

        ranked = list(records)
        ranked.sort(key=_record_rank, reverse=True)
        return ranked

    def _resolve_current_records(
        self, records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        if not records:
            return []
        by_identity: Dict[str, List[Dict[str, Any]]] = {}
        for record in records:
            by_identity.setdefault(record["identity_key"], []).append(record)

        resolved: List[Dict[str, Any]] = []
        for group in by_identity.values():
            group.sort(
                key=lambda record: (
                    record.get("effective_from") or "",
                    record.get("recorded_at") or "",
                    record.get("updated_at") or "",
                    float(record.get("score", 0.0)),
                ),
                reverse=True,
            )
            resolved.append(group[0])
        resolved.sort(
            key=lambda record: (
                float(record.get("score", 0.0)),
                record.get("updated_at") or "",
            ),
            reverse=True,
        )
        return resolved

    def _record_to_item(self, record: Dict[str, Any]) -> Core2RecallItem:
        return Core2RecallItem(
            object_id=record["object_id"],
            plane=PLANE_CANONICAL_TRUTH,
            object_kind=record["object_kind"],
            title=record["title"],
            namespace=record["namespace"],
            namespace_class=record["namespace_class"],
            risk_class=record["risk_class"],
            source_type=record["source_type"],
            support_level=record["support_level"],
            state_status=record["state_status"],
            content=record["content"],
            snippet=record["content"][:180].strip(),
            source_raw_id=record["source_raw_id"],
            observed_at=record["observed_at"],
            source_created_at=record["source_created_at"],
            effective_from=record["effective_from"],
            effective_to=record["effective_to"],
            recorded_at=record["recorded_at"],
            superseded_at=record["superseded_at"],
            invalidated_at=record["invalidated_at"],
            created_at=record["created_at"],
            metadata=record["metadata"],
            score=float(record.get("score", 0.0)),
        )

    def _support_tier_for_route(
        self, query_mode: str, items: List[Core2RecallItem]
    ) -> str:
        if query_mode == "compact_memory":
            return "compact_memory"
        if query_mode == MODE_EXACT_SOURCE_REQUIRED:
            return SUPPORT_EXACT_SOURCE
        if any(item.support_level == SUPPORT_WEAK for item in items):
            return SUPPORT_WEAK
        return SUPPORT_SOURCE_SUPPORTED

    def _confidence_dimensions(
        self, items: List[Core2RecallItem], *, route_plan
    ) -> Tuple[str, str, str, str]:
        support_confidence = (
            "high"
            if all(item.support_level != SUPPORT_WEAK for item in items)
            else "medium"
        )
        temporal_confidence = (
            "high" if all(item.recorded_at for item in items) else "medium"
        )
        if route_plan.temporal_strict and not all(
            item.effective_from and item.source_created_at for item in items
        ):
            temporal_confidence = "low"

        conflict_present = any(
            item.metadata.get("conflict_refs") or item.state_status == "conflicted"
            for item in items
        )
        provisional_present = any(item.state_status == "provisional" for item in items)
        multiple_identities = (
            len({item.metadata.get("identity_key", item.object_id) for item in items})
            > 1
        )

        resolution_confidence = "low" if conflict_present else "high"
        identity_confidence = (
            "medium" if provisional_present or multiple_identities else "high"
        )
        return (
            support_confidence,
            temporal_confidence,
            resolution_confidence,
            identity_confidence,
        )

    def _overall_confidence(
        self,
        *,
        support_confidence: str,
        temporal_confidence: str,
        resolution_confidence: str,
        identity_confidence: str,
    ) -> str:
        ordered = [
            support_confidence,
            temporal_confidence,
            resolution_confidence,
            identity_confidence,
        ]
        if all(value == "high" for value in ordered):
            return "high"
        if any(value == "low" for value in ordered):
            return "low"
        return "medium"

    def _resolve_delivery_view(self, object_id: str, view_kind: str) -> str:
        view = self.store.get_delivery_view(object_id, view_kind)
        if view:
            return view["content"]
        if view_kind == "final_compact":
            fallback = self.store.get_delivery_view(object_id, "supported_compact")
            if fallback:
                return fallback["content"]
        if view_kind == "supported_compact":
            fallback = self.store.get_delivery_view(object_id, "final_compact")
            if fallback:
                return fallback["content"]
        record = self.store.get_canonical_object(object_id)
        return record["content"] if record else ""

    def _abstain_packet(
        self,
        query: str,
        *,
        operator: Optional[str],
        risk_class: str,
        route_plan,
        reason: str,
        conflict_refs: Optional[List[str]] = None,
    ) -> Core2RecallPacket:
        packet = build_answer_packet(
            query=query,
            operator=operator,
            risk_class=risk_class,
            route_plan=route_plan,
            items=[],
            support_tier=SUPPORT_NONE,
            confidence="low",
            support_confidence="low",
            temporal_confidence="low" if route_plan.temporal_strict else "medium",
            resolution_confidence="low",
            identity_confidence="low",
            abstained=True,
            reason=reason,
            delivery_resolver=self._resolve_delivery_view,
            conflict_refs=conflict_refs or [],
        )
        packet.answer_surface = build_answer_surface(query, packet)
        return packet
