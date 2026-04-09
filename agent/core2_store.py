from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from agent.core2_policy import (
    build_temporal_fields,
    classify_namespace,
    compute_identity_key,
    default_object_kind,
    derive_initial_state,
    derive_support_level,
    normalize_risk_class,
)
from agent.core2_types import (
    EDGE_CONFLICTS_WITH,
    EDGE_DERIVED_FROM,
    EDGE_SUPERSEDES,
    INACTIVE_STATE_STATUSES,
    PLANE_CANONICAL_TRUTH,
    PLANE_DELIVERY_VIEWS,
    PLANE_DERIVED_PROPOSITIONS,
    PLANE_RAW_ARCHIVE,
    PLANE_RETRIEVAL_INDICES,
)


SEARCH_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "between",
    "by",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "me",
    "my",
    "of",
    "on",
    "or",
    "the",
    "their",
    "there",
    "these",
    "this",
    "to",
    "what",
    "when",
    "where",
    "who",
    "why",
}

SEARCH_SYNONYMS = {
    "occupation": ("role", "job", "work", "profession", "career"),
    "role": ("occupation", "job", "work", "position"),
    "job": ("occupation", "role", "work", "position"),
    "previous": ("former", "prior"),
    "current": ("latest", "present"),
    "distance": ("miles", "mile", "trip", "road", "travel"),
    "miles": ("distance", "mile"),
    "hours": ("hour", "driving", "drive"),
    "driving": ("drive", "hours", "road"),
    "total": ("combined", "sum"),
    "combined": ("total", "sum"),
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(payload: str | None) -> Dict[str, Any]:
    if not payload:
        return {}
    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError:
        return {"raw_metadata_json": payload}
    return parsed if isinstance(parsed, dict) else {"value": parsed}


def _dump_json(payload: Dict[str, Any]) -> str:
    return json.dumps(payload or {}, ensure_ascii=False, sort_keys=True)


def _normalize_search_tokens(text: str) -> List[str]:
    return re.findall(r"[a-z0-9_./:-]+", (text or "").strip().lower())


def _select_search_terms(raw_tokens: List[str]) -> List[str]:
    for minimum in (3, 2, 1):
        terms = [
            term
            for term in raw_tokens
            if term
            and term not in SEARCH_STOPWORDS
            and (len(term) >= minimum or term.isdigit())
        ]
        if terms:
            return terms
    return []


def _expand_search_terms(terms: List[str]) -> List[str]:
    expanded: List[str] = []
    seen = set(terms)
    for term in terms:
        for synonym in SEARCH_SYNONYMS.get(term, ()):
            if synonym not in seen:
                expanded.append(synonym)
                seen.add(synonym)
    return expanded


def _upsert_row(
    conn: sqlite3.Connection,
    *,
    select_sql: str,
    select_params: tuple[Any, ...],
    update_sql: str,
    update_params: tuple[Any, ...],
    insert_sql: str,
    insert_params: tuple[Any, ...],
) -> None:
    existing = conn.execute(select_sql, select_params).fetchone()
    if existing:
        conn.execute(update_sql, update_params + (existing[0],))
        return
    conn.execute(insert_sql, insert_params)


class Core2Store:
    """Local-first plane-aware persistence layer for Core2."""

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None

    def connect(self) -> None:
        if self._conn is not None:
            return
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._migrate()
        self._migrate_phase1_notes()

    def _require_connection(self) -> None:
        """Raise RuntimeError if database connection not established."""
        if self._conn is None:
            raise RuntimeError(
                "Database connection not established. Call connect() first."
            )

    def begin_transaction(self) -> None:
        """Begin a transaction for atomic operations."""
        self._require_connection()
        self._conn.execute("BEGIN TRANSACTION")

    def commit(self) -> None:
        """Commit the current transaction."""
        self._require_connection()
        self._conn.commit()

    def rollback(self) -> None:
        """Rollback the current transaction."""
        self._require_connection()
        self._conn.rollback()

    def _table_exists(self, table_name: str) -> bool:
        self._require_connection()
        row = self._conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table_name,),
        ).fetchone()
        return row is not None

    def _migrate(self) -> None:
        self._require_connection()
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS core2_raw_archive (
                raw_id TEXT PRIMARY KEY,
                namespace TEXT NOT NULL,
                namespace_class TEXT NOT NULL,
                risk_class TEXT NOT NULL,
                language TEXT NOT NULL,
                source_type TEXT NOT NULL,
                source_uri TEXT,
                checksum TEXT NOT NULL,
                content TEXT NOT NULL,
                observed_at TEXT,
                source_created_at TEXT,
                recorded_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                metadata_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS core2_canonical_truth (
                object_id TEXT PRIMARY KEY,
                object_kind TEXT NOT NULL,
                title TEXT NOT NULL,
                namespace TEXT NOT NULL,
                namespace_class TEXT NOT NULL,
                risk_class TEXT NOT NULL,
                language TEXT NOT NULL,
                source_type TEXT NOT NULL,
                source_raw_id TEXT NOT NULL REFERENCES core2_raw_archive(raw_id),
                identity_key TEXT NOT NULL,
                content TEXT NOT NULL,
                support_level TEXT NOT NULL,
                state_status TEXT NOT NULL,
                observed_at TEXT,
                source_created_at TEXT,
                effective_from TEXT,
                effective_to TEXT,
                recorded_at TEXT NOT NULL,
                superseded_at TEXT,
                invalidated_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS core2_derived_propositions (
                proposition_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                namespace TEXT NOT NULL,
                namespace_class TEXT NOT NULL,
                risk_class TEXT NOT NULL,
                language TEXT NOT NULL,
                claim_text TEXT NOT NULL,
                subject TEXT,
                predicate TEXT,
                object_or_value TEXT,
                modality TEXT,
                source_object_ids_json TEXT NOT NULL,
                effective_from TEXT,
                effective_to TEXT,
                recorded_at TEXT NOT NULL,
                state_status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS core2_retrieval_indices (
                index_id TEXT PRIMARY KEY,
                plane_name TEXT NOT NULL,
                record_id TEXT NOT NULL,
                index_kind TEXT NOT NULL,
                index_key TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS core2_delivery_views (
                view_id TEXT PRIMARY KEY,
                plane_name TEXT NOT NULL,
                record_id TEXT NOT NULL,
                view_kind TEXT NOT NULL,
                content TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS core2_edges (
                edge_id TEXT PRIMARY KEY,
                from_plane TEXT NOT NULL,
                from_id TEXT NOT NULL,
                to_plane TEXT NOT NULL,
                to_id TEXT NOT NULL,
                edge_type TEXT NOT NULL,
                created_at TEXT NOT NULL,
                metadata_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS core2_transitions (
                transition_id TEXT PRIMARY KEY,
                plane_name TEXT NOT NULL,
                record_id TEXT NOT NULL,
                from_state TEXT,
                to_state TEXT NOT NULL,
                reason TEXT NOT NULL,
                created_at TEXT NOT NULL,
                metadata_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS core2_turns (
                turn_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                user_content TEXT NOT NULL,
                assistant_content TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        self._conn.commit()

    def _migrate_phase1_notes(self) -> None:
        self._require_connection()
        if not self._table_exists("core2_notes"):
            return
        existing = self._conn.execute(
            "SELECT COUNT(*) AS count FROM core2_canonical_truth"
        ).fetchone()
        if existing and int(existing["count"]) > 0:
            return

        legacy_rows = self._conn.execute(
            """
            SELECT object_id, title, namespace, risk_class, language, source_type,
                   content, effective_from, created_at, updated_at, metadata_json
            FROM core2_notes
            ORDER BY created_at ASC
            """
        ).fetchall()
        for row in legacy_rows:
            metadata = _load_json(row["metadata_json"])
            temporal = build_temporal_fields(
                row["effective_from"], metadata, row["created_at"]
            )
            namespace_class = classify_namespace(row["namespace"])
            support_level = derive_support_level(
                row["namespace"], row["source_type"], temporal
            )
            raw_id = f"raw-{row['object_id']}"
            self._insert_raw_archive(
                raw_id=raw_id,
                namespace=row["namespace"],
                namespace_class=namespace_class,
                risk_class=normalize_risk_class(row["namespace"], row["risk_class"]),
                language=row["language"],
                source_type=row["source_type"],
                content=row["content"],
                observed_at=temporal["observed_at"],
                source_created_at=temporal["source_created_at"],
                recorded_at=temporal["recorded_at"] or row["created_at"],
                created_at=row["created_at"],
                metadata=metadata,
            )
            object_kind = default_object_kind(
                row["title"], row["source_type"], metadata
            )
            self._insert_canonical_truth(
                object_id=row["object_id"],
                object_kind=object_kind,
                title=row["title"],
                namespace=row["namespace"],
                namespace_class=namespace_class,
                risk_class=normalize_risk_class(row["namespace"], row["risk_class"]),
                language=row["language"],
                source_type=row["source_type"],
                source_raw_id=raw_id,
                identity_key=compute_identity_key(
                    row["namespace"],
                    object_kind,
                    row["title"],
                    row["content"],
                    metadata,
                ),
                content=row["content"],
                support_level=support_level,
                state_status=derive_initial_state(
                    row["namespace"], metadata, support_level
                ),
                observed_at=temporal["observed_at"],
                source_created_at=temporal["source_created_at"],
                effective_from=temporal["effective_from"],
                effective_to=temporal["effective_to"],
                recorded_at=temporal["recorded_at"] or row["created_at"],
                superseded_at=temporal["superseded_at"],
                invalidated_at=temporal["invalidated_at"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                metadata=metadata,
            )
            self.rebuild_indices_for_object(row["object_id"])
        self._conn.commit()

    def close(self) -> None:
        if self._conn is None:
            return
        self._conn.close()
        self._conn = None

    def note_count(self) -> int:
        self._require_connection()
        row = self._conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM core2_canonical_truth
            WHERE state_status NOT IN ('rejected', 'archived')
            """
        ).fetchone()
        return int(row["count"]) if row else 0

    def plane_counts(self) -> Dict[str, int]:
        self._require_connection()
        tables = {
            PLANE_RAW_ARCHIVE: "core2_raw_archive",
            PLANE_CANONICAL_TRUTH: "core2_canonical_truth",
            PLANE_DERIVED_PROPOSITIONS: "core2_derived_propositions",
            PLANE_RETRIEVAL_INDICES: "core2_retrieval_indices",
            PLANE_DELIVERY_VIEWS: "core2_delivery_views",
        }
        counts = {}
        for plane, table in tables.items():
            row = self._conn.execute(
                f"SELECT COUNT(*) AS count FROM {table}"
            ).fetchone()
            counts[plane] = int(row["count"]) if row else 0
        return counts

    def _insert_raw_archive(
        self,
        *,
        raw_id: str,
        namespace: str,
        namespace_class: str,
        risk_class: str,
        language: str,
        source_type: str,
        content: str,
        observed_at: str | None,
        source_created_at: str | None,
        recorded_at: str,
        created_at: str,
        metadata: Dict[str, Any],
    ) -> None:
        self._require_connection()
        checksum = f"sha1:{uuid4().hex[:12]}"
        self._conn.execute(
            """
            INSERT INTO core2_raw_archive (
                raw_id, namespace, namespace_class, risk_class, language, source_type,
                source_uri, checksum, content, observed_at, source_created_at,
                recorded_at, created_at, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                raw_id,
                namespace,
                namespace_class,
                risk_class,
                language,
                source_type,
                metadata.get("source_uri"),
                checksum,
                content,
                observed_at,
                source_created_at,
                recorded_at,
                created_at,
                _dump_json(metadata),
            ),
        )

    def _insert_canonical_truth(
        self,
        *,
        object_id: str,
        object_kind: str,
        title: str,
        namespace: str,
        namespace_class: str,
        risk_class: str,
        language: str,
        source_type: str,
        source_raw_id: str,
        identity_key: str,
        content: str,
        support_level: str,
        state_status: str,
        observed_at: str | None,
        source_created_at: str | None,
        effective_from: str | None,
        effective_to: str | None,
        recorded_at: str,
        superseded_at: str | None,
        invalidated_at: str | None,
        created_at: str,
        updated_at: str,
        metadata: Dict[str, Any],
    ) -> None:
        self._require_connection()
        self._conn.execute(
            """
            INSERT INTO core2_canonical_truth (
                object_id, object_kind, title, namespace, namespace_class, risk_class, language,
                source_type, source_raw_id, identity_key, content, support_level, state_status,
                observed_at, source_created_at, effective_from, effective_to, recorded_at,
                superseded_at, invalidated_at, created_at, updated_at, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                object_id,
                object_kind,
                title,
                namespace,
                namespace_class,
                risk_class,
                language,
                source_type,
                source_raw_id,
                identity_key,
                content,
                support_level,
                state_status,
                observed_at,
                source_created_at,
                effective_from,
                effective_to,
                recorded_at,
                superseded_at,
                invalidated_at,
                created_at,
                updated_at,
                _dump_json(metadata),
            ),
        )

    def add_memory(
        self,
        *,
        content: str,
        title: str,
        namespace: str,
        risk_class: str,
        language: str,
        source_type: str,
        effective_from: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        object_kind: Optional[str] = None,
        state_status: Optional[str] = None,
    ) -> Dict[str, Any]:
        self._require_connection()
        payload = dict(metadata or {})
        now = utc_now_iso()
        namespace_class = classify_namespace(namespace)
        normalized_risk = normalize_risk_class(namespace, risk_class)
        temporal = build_temporal_fields(effective_from, payload, now)
        object_kind = object_kind or default_object_kind(title, source_type, payload)
        support_level = derive_support_level(namespace, source_type, temporal)
        state_status = state_status or derive_initial_state(
            namespace, payload, support_level
        )

        object_id = f"core2-{uuid4().hex[:12]}"
        raw_id = f"raw-{uuid4().hex[:12]}"
        recorded_at = temporal["recorded_at"] or now

        self._insert_raw_archive(
            raw_id=raw_id,
            namespace=namespace,
            namespace_class=namespace_class,
            risk_class=normalized_risk,
            language=language,
            source_type=source_type,
            content=content,
            observed_at=temporal["observed_at"],
            source_created_at=temporal["source_created_at"],
            recorded_at=recorded_at,
            created_at=now,
            metadata=payload,
        )
        self._insert_canonical_truth(
            object_id=object_id,
            object_kind=object_kind,
            title=title,
            namespace=namespace,
            namespace_class=namespace_class,
            risk_class=normalized_risk,
            language=language,
            source_type=source_type,
            source_raw_id=raw_id,
            identity_key=compute_identity_key(
                namespace, object_kind, title, content, payload
            ),
            content=content,
            support_level=support_level,
            state_status=state_status,
            observed_at=temporal["observed_at"],
            source_created_at=temporal["source_created_at"],
            effective_from=temporal["effective_from"],
            effective_to=temporal["effective_to"],
            recorded_at=recorded_at,
            superseded_at=temporal["superseded_at"],
            invalidated_at=temporal["invalidated_at"],
            created_at=now,
            updated_at=now,
            metadata=payload,
        )
        self.record_transition(object_id, None, state_status, "ingest")
        self.rebuild_indices_for_object(object_id)
        self._conn.commit()
        return self.get_canonical_object(object_id) or {"object_id": object_id}

    def add_proposition(
        self,
        *,
        claim_text: str,
        title: str,
        namespace: str,
        risk_class: str,
        language: str = "und",
        source_object_ids: Optional[List[str]] = None,
        subject: str | None = None,
        predicate: str | None = None,
        object_or_value: str | None = None,
        modality: str | None = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        self._require_connection()
        payload = dict(metadata or {})
        proposition_id = f"prop-{uuid4().hex[:12]}"
        now = utc_now_iso()
        namespace_class = classify_namespace(namespace)
        normalized_risk = normalize_risk_class(namespace, risk_class)
        state_status = payload.get("state_status") or "derived_active"
        self._conn.execute(
            """
            INSERT INTO core2_derived_propositions (
                proposition_id, title, namespace, namespace_class, risk_class, language,
                claim_text, subject, predicate, object_or_value, modality,
                source_object_ids_json, effective_from, effective_to, recorded_at,
                state_status, created_at, updated_at, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                proposition_id,
                title,
                namespace,
                namespace_class,
                normalized_risk,
                language,
                claim_text,
                subject,
                predicate,
                object_or_value,
                modality,
                json.dumps(source_object_ids or []),
                payload.get("effective_from"),
                payload.get("effective_to"),
                payload.get("recorded_at") or now,
                state_status,
                now,
                now,
                _dump_json(payload),
            ),
        )
        for source_object_id in source_object_ids or []:
            self.add_edge(
                from_plane=PLANE_DERIVED_PROPOSITIONS,
                from_id=proposition_id,
                to_plane=PLANE_CANONICAL_TRUTH,
                to_id=source_object_id,
                edge_type=EDGE_DERIVED_FROM,
                metadata={"reason": "derived_proposition"},
                commit=False,
            )
        self._conn.commit()
        return self.get_proposition(proposition_id) or {
            "proposition_id": proposition_id
        }

    def get_raw_archive(self, raw_id: str) -> Optional[Dict[str, Any]]:
        self._require_connection()
        row = self._conn.execute(
            "SELECT * FROM core2_raw_archive WHERE raw_id = ?", (raw_id,)
        ).fetchone()
        if row is None:
            return None
        metadata = _load_json(row["metadata_json"])
        return {
            "raw_id": row["raw_id"],
            "plane": PLANE_RAW_ARCHIVE,
            "namespace": row["namespace"],
            "namespace_class": row["namespace_class"],
            "risk_class": row["risk_class"],
            "language": row["language"],
            "source_type": row["source_type"],
            "source_uri": row["source_uri"],
            "checksum": row["checksum"],
            "content": row["content"],
            "observed_at": row["observed_at"],
            "source_created_at": row["source_created_at"],
            "recorded_at": row["recorded_at"],
            "created_at": row["created_at"],
            "metadata": metadata,
        }

    def search_raw_archive(
        self,
        query: str,
        *,
        max_items: int,
        namespace_classes: Optional[List[str]] = None,
        source_first: bool = False,
        exact_phrase: bool = False,
    ) -> List[Dict[str, Any]]:
        self._require_connection()
        raw_tokens = _normalize_search_tokens(query)
        cleaned = " ".join(raw_tokens)
        if not cleaned:
            return []
        terms = _select_search_terms(raw_tokens)
        if not terms:
            return []
        expanded_terms = _expand_search_terms(terms)
        namespace_filter = set(namespace_classes or [])

        rows = self._conn.execute(
            """
            SELECT * FROM core2_raw_archive
            ORDER BY created_at DESC
            """
        ).fetchall()

        ranked: List[Dict[str, Any]] = []
        for row in rows:
            if namespace_filter and row["namespace_class"] not in namespace_filter:
                continue
            metadata = _load_json(row["metadata_json"])
            haystack = " ".join(
                [
                    row["namespace"],
                    row["namespace_class"],
                    row["source_type"],
                    row["content"],
                    str(metadata.get("keywords") or ""),
                ]
            ).lower()
            haystack_tokens = _normalize_search_tokens(haystack)
            if not haystack_tokens:
                continue
            normalized_haystack = " ".join(haystack_tokens)
            token_counts: Dict[str, int] = {}
            for token in haystack_tokens:
                token_counts[token] = token_counts.get(token, 0) + 1
            base_hits = sum(min(token_counts.get(term, 0), 2) for term in terms)
            expanded_hits = sum(
                min(token_counts.get(term, 0), 2) for term in expanded_terms
            )
            score = (base_hits * 2.0) + (expanded_hits * 0.5)
            if score <= 0:
                continue
            if (
                (source_first or exact_phrase)
                and len(terms) >= 2
                and base_hits <= 0
                and expanded_hits < 2
            ):
                continue
            if exact_phrase and cleaned in normalized_haystack:
                score += 5.0
            if source_first and row["source_type"] in {
                "document_source",
                "explicit_memory",
                "builtin_memory",
            }:
                score += 0.8
            if metadata.get("session_id"):
                score += 0.2
            ranked.append(
                {
                    "raw_id": row["raw_id"],
                    "namespace": row["namespace"],
                    "namespace_class": row["namespace_class"],
                    "risk_class": row["risk_class"],
                    "language": row["language"],
                    "source_type": row["source_type"],
                    "content": row["content"],
                    "observed_at": row["observed_at"],
                    "source_created_at": row["source_created_at"],
                    "recorded_at": row["recorded_at"],
                    "created_at": row["created_at"],
                    "metadata": metadata,
                    "score": float(score),
                }
            )

        ranked.sort(
            key=lambda item: (
                float(item.get("score", 0.0)),
                item.get("created_at") or "",
            ),
            reverse=True,
        )
        return ranked[:max_items]

    def _row_to_canonical(self, row: sqlite3.Row) -> Dict[str, Any]:
        metadata = _load_json(row["metadata_json"])
        return {
            "object_id": row["object_id"],
            "plane": PLANE_CANONICAL_TRUTH,
            "object_kind": row["object_kind"],
            "title": row["title"],
            "namespace": row["namespace"],
            "namespace_class": row["namespace_class"],
            "risk_class": row["risk_class"],
            "language": row["language"],
            "source_type": row["source_type"],
            "source_raw_id": row["source_raw_id"],
            "identity_key": row["identity_key"],
            "content": row["content"],
            "support_level": row["support_level"],
            "state_status": row["state_status"],
            "observed_at": row["observed_at"],
            "source_created_at": row["source_created_at"],
            "effective_from": row["effective_from"],
            "effective_to": row["effective_to"],
            "recorded_at": row["recorded_at"],
            "superseded_at": row["superseded_at"],
            "invalidated_at": row["invalidated_at"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "metadata": metadata,
        }

    def get_canonical_object(self, object_id: str) -> Optional[Dict[str, Any]]:
        self._require_connection()
        row = self._conn.execute(
            "SELECT * FROM core2_canonical_truth WHERE object_id = ?", (object_id,)
        ).fetchone()
        if row is None:
            return None
        return self._row_to_canonical(row)

    def get_proposition(self, proposition_id: str) -> Optional[Dict[str, Any]]:
        self._require_connection()
        row = self._conn.execute(
            "SELECT * FROM core2_derived_propositions WHERE proposition_id = ?",
            (proposition_id,),
        ).fetchone()
        if row is None:
            return None
        return {
            "proposition_id": row["proposition_id"],
            "plane": PLANE_DERIVED_PROPOSITIONS,
            "title": row["title"],
            "namespace": row["namespace"],
            "namespace_class": row["namespace_class"],
            "risk_class": row["risk_class"],
            "language": row["language"],
            "claim_text": row["claim_text"],
            "subject": row["subject"],
            "predicate": row["predicate"],
            "object_or_value": row["object_or_value"],
            "modality": row["modality"],
            "source_object_ids": json.loads(row["source_object_ids_json"] or "[]"),
            "effective_from": row["effective_from"],
            "effective_to": row["effective_to"],
            "recorded_at": row["recorded_at"],
            "state_status": row["state_status"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "metadata": _load_json(row["metadata_json"]),
        }

    def list_canonical_objects(
        self, *, include_inactive: bool = True
    ) -> List[Dict[str, Any]]:
        self._require_connection()
        sql = "SELECT * FROM core2_canonical_truth"
        params: tuple[Any, ...] = ()
        if not include_inactive:
            sql += " WHERE state_status NOT IN ('rejected', 'archived', 'superseded')"
        sql += " ORDER BY updated_at DESC"
        rows = self._conn.execute(sql, params).fetchall()
        return [self._row_to_canonical(row) for row in rows]

    def search_session_records(
        self,
        session_index: int,
        query: str,
        *,
        max_items: int,
        turns_only: bool = True,
    ) -> List[Dict[str, Any]]:
        records = self.list_canonical_objects(include_inactive=False)
        scoped: List[Dict[str, Any]] = []
        for record in records:
            metadata = dict(record.get("metadata") or {})
            if metadata.get("session_index") != session_index:
                continue
            if turns_only and not metadata.get("turn_index"):
                continue
            scoped.append(record)
        if not scoped:
            return []

        raw_tokens = _normalize_search_tokens(query)
        cleaned = " ".join(raw_tokens)
        if not cleaned:
            return []
        terms = _select_search_terms(raw_tokens)
        if not terms:
            return []
        expanded_terms = _expand_search_terms(terms)

        ranked: List[Dict[str, Any]] = []
        for record in scoped:
            haystack = " ".join(
                [
                    record["title"],
                    record["namespace"],
                    record["namespace_class"],
                    record["source_type"],
                    record["content"],
                    record["metadata"].get("keywords", ""),
                ]
            ).lower()
            haystack_tokens = _normalize_search_tokens(haystack)
            if not haystack_tokens:
                continue
            token_counts: Dict[str, int] = {}
            for token in haystack_tokens:
                token_counts[token] = token_counts.get(token, 0) + 1
            base_hits = sum(min(token_counts.get(term, 0), 2) for term in terms)
            expanded_hits = sum(
                min(token_counts.get(term, 0), 2) for term in expanded_terms
            )
            score = (base_hits * 2.0) + (expanded_hits * 0.5)
            if score <= 0:
                continue
            if record.get("metadata", {}).get("turn_index"):
                score += 0.6
            candidate = dict(record)
            candidate["score"] = max(float(candidate.get("score", 0.0)), float(score))
            ranked.append(candidate)

        ranked.sort(
            key=lambda item: (
                float(item.get("score", 0.0)),
                item.get("updated_at") or "",
            ),
            reverse=True,
        )
        return ranked[:max_items]

    def search_turn_archive(
        self,
        query: str,
        *,
        max_items: int,
        session_id: str | None = None,
    ) -> List[Dict[str, Any]]:
        self._require_connection()
        raw_tokens = _normalize_search_tokens(query)
        cleaned = " ".join(raw_tokens)
        if not cleaned:
            return []
        terms = _select_search_terms(raw_tokens)
        if not terms:
            return []
        expanded_terms = _expand_search_terms(terms)

        if session_id:
            rows = self._conn.execute(
                """
                SELECT * FROM core2_turns
                WHERE session_id = ?
                ORDER BY created_at DESC
                """,
                (session_id,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                """
                SELECT * FROM core2_turns
                ORDER BY created_at DESC
                """
            ).fetchall()

        ranked: List[Dict[str, Any]] = []
        for row in rows:
            haystack = f"{row['user_content']} {row['assistant_content']}".lower()
            haystack_tokens = _normalize_search_tokens(haystack)
            if not haystack_tokens:
                continue
            normalized_haystack = " ".join(haystack_tokens)
            token_counts: Dict[str, int] = {}
            for token in haystack_tokens:
                token_counts[token] = token_counts.get(token, 0) + 1
            base_hits = sum(min(token_counts.get(term, 0), 2) for term in terms)
            expanded_hits = sum(
                min(token_counts.get(term, 0), 2) for term in expanded_terms
            )
            score = (base_hits * 2.0) + (expanded_hits * 0.5)
            if score <= 0:
                continue
            if cleaned in normalized_haystack:
                score += 4.0
            user_tokens = set(_normalize_search_tokens(str(row["user_content"] or "")))
            score += 0.4 * len(user_tokens.intersection(set(terms)))
            ranked.append(
                {
                    "turn_id": row["turn_id"],
                    "session_id": row["session_id"],
                    "user_content": row["user_content"],
                    "assistant_content": row["assistant_content"],
                    "created_at": row["created_at"],
                    "score": float(score),
                }
            )

        ranked.sort(
            key=lambda item: (
                float(item.get("score", 0.0)),
                item.get("created_at") or "",
            ),
            reverse=True,
        )
        return ranked[:max_items]

    def list_records(
        self, plane_name: str, *, include_inactive: bool = True
    ) -> List[Dict[str, Any]]:
        if plane_name == PLANE_CANONICAL_TRUTH:
            return self.list_canonical_objects(include_inactive=include_inactive)
        if plane_name == PLANE_DERIVED_PROPOSITIONS:
            self._require_connection()
            rows = self._conn.execute(
                "SELECT proposition_id FROM core2_derived_propositions ORDER BY updated_at DESC"
            ).fetchall()
            return [
                self.get_proposition(row["proposition_id"])
                for row in rows
                if self.get_proposition(row["proposition_id"])
            ]
        raise ValueError(f"Unsupported plane for list_records: {plane_name}")

    def search_canonical(
        self,
        query: str,
        *,
        max_items: int,
        namespace_classes: Optional[List[str]] = None,
        source_first: bool = False,
        exact_phrase: bool = False,
    ) -> List[Dict[str, Any]]:
        self._require_connection()
        raw_tokens = _normalize_search_tokens(query)
        cleaned = " ".join(raw_tokens)
        if not cleaned:
            return []
        terms = _select_search_terms(raw_tokens)
        if not terms:
            return []
        expanded_terms = _expand_search_terms(terms)

        rows = self._conn.execute(
            """
            SELECT * FROM core2_canonical_truth
            WHERE state_status NOT IN ('rejected', 'archived')
            ORDER BY updated_at DESC
            """
        ).fetchall()

        ranked: List[Dict[str, Any]] = []
        for row in rows:
            record = self._row_to_canonical(row)
            if namespace_classes and record["namespace_class"] not in set(
                namespace_classes
            ):
                continue
            haystack = " ".join(
                [
                    record["title"],
                    record["namespace"],
                    record["namespace_class"],
                    record["source_type"],
                    record["content"],
                    record["metadata"].get("keywords", ""),
                ]
            ).lower()
            haystack_tokens = _normalize_search_tokens(haystack)
            normalized_haystack = " ".join(haystack_tokens)
            token_counts: Dict[str, int] = {}
            for token in haystack_tokens:
                token_counts[token] = token_counts.get(token, 0) + 1
            base_hits = sum(min(token_counts.get(term, 0), 2) for term in terms)
            expanded_hits = sum(
                min(token_counts.get(term, 0), 2) for term in expanded_terms
            )
            score = (base_hits * 2.0) + (expanded_hits * 0.5)
            if score <= 0:
                continue
            if (
                (source_first or exact_phrase)
                and len(terms) >= 2
                and base_hits <= 0
                and expanded_hits < 2
            ):
                continue
            if exact_phrase and cleaned in normalized_haystack:
                score += 6
            if cleaned == (record["title"] or "").strip().lower():
                score += 8
            if source_first and record["support_level"] != "weak_support":
                score += 1.5
            if source_first and record["source_type"] in {
                "document_source",
                "explicit_memory",
                "builtin_memory",
            }:
                score += 1.0
            content_length = len(str(record.get("content") or ""))
            if content_length > 1800:
                score -= 0.8
            elif content_length < 360:
                score += 0.4
            metadata = dict(record.get("metadata") or {})
            if metadata.get("turn_index"):
                score += 0.4
            if record["state_status"] == "provisional":
                score -= 0.5
            if record["state_status"] == "superseded":
                score -= 3.0
            if record.get("metadata", {}).get("conflict_refs"):
                score -= 1.0
            record["score"] = float(score)
            ranked.append(record)

        ranked.sort(key=lambda item: (item["score"], item["updated_at"]), reverse=True)
        return ranked[:max_items]

    def add_edge(
        self,
        *,
        from_plane: str,
        from_id: str,
        to_plane: str,
        to_id: str,
        edge_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        commit: bool = True,
    ) -> str:
        self._require_connection()
        if self._edge_exists(from_id, to_id, edge_type):
            return ""
        edge_id = f"edge-{uuid4().hex[:12]}"
        self._conn.execute(
            """
            INSERT INTO core2_edges (edge_id, from_plane, from_id, to_plane, to_id, edge_type, created_at, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                edge_id,
                from_plane,
                from_id,
                to_plane,
                to_id,
                edge_type,
                utc_now_iso(),
                _dump_json(metadata or {}),
            ),
        )
        if commit:
            self._conn.commit()
        return edge_id

    def _edge_exists(self, from_id: str, to_id: str, edge_type: str) -> bool:
        self._require_connection()
        row = self._conn.execute(
            """
            SELECT edge_id FROM core2_edges
            WHERE from_id = ? AND to_id = ? AND edge_type = ?
            """,
            (from_id, to_id, edge_type),
        ).fetchone()
        return row is not None

    def get_edges(self, record_id: str) -> List[Dict[str, Any]]:
        self._require_connection()
        rows = self._conn.execute(
            """
            SELECT * FROM core2_edges
            WHERE from_id = ? OR to_id = ?
            ORDER BY created_at ASC
            """,
            (record_id, record_id),
        ).fetchall()
        return [
            {
                "edge_id": row["edge_id"],
                "from_plane": row["from_plane"],
                "from_id": row["from_id"],
                "to_plane": row["to_plane"],
                "to_id": row["to_id"],
                "edge_type": row["edge_type"],
                "created_at": row["created_at"],
                "metadata": _load_json(row["metadata_json"]),
            }
            for row in rows
        ]

    def get_delivery_views(self, record_id: str) -> List[Dict[str, Any]]:
        self._require_connection()
        rows = self._conn.execute(
            "SELECT * FROM core2_delivery_views WHERE record_id = ? ORDER BY updated_at DESC",
            (record_id,),
        ).fetchall()
        return [
            {
                "view_id": row["view_id"],
                "plane": row["plane_name"],
                "record_id": row["record_id"],
                "view_kind": row["view_kind"],
                "content": row["content"],
                "payload": _load_json(row["payload_json"]),
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]

    def get_delivery_view(
        self, record_id: str, view_kind: str
    ) -> Optional[Dict[str, Any]]:
        for view in self.get_delivery_views(record_id):
            if view["view_kind"] == view_kind:
                return view
        return None

    def get_retrieval_indices(self, record_id: str) -> List[Dict[str, Any]]:
        self._require_connection()
        rows = self._conn.execute(
            """
            SELECT * FROM core2_retrieval_indices
            WHERE record_id = ?
            ORDER BY index_kind ASC, updated_at DESC
            """,
            (record_id,),
        ).fetchall()
        return [
            {
                "index_id": row["index_id"],
                "plane": row["plane_name"],
                "record_id": row["record_id"],
                "index_kind": row["index_kind"],
                "index_key": row["index_key"],
                "payload": _load_json(row["payload_json"]),
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]

    def search_digested_facts(
        self,
        query: str,
        *,
        max_items: int,
        fact_keys: List[str],
        namespace_classes: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        if not fact_keys:
            return []

        requested_keys = {
            str(value).strip().lower() for value in fact_keys if str(value).strip()
        }
        if not requested_keys:
            return []

        raw_tokens = _normalize_search_tokens(query)
        terms = _select_search_terms(raw_tokens)
        normalized_query = " ".join(raw_tokens)
        namespace_filter = set(namespace_classes or [])

        ranked: List[Dict[str, Any]] = []
        for record in self.list_canonical_objects(include_inactive=False):
            metadata = dict(record.get("metadata") or {})
            if not metadata.get("digest_fact"):
                continue
            fact_key = str(metadata.get("fact_key") or "").strip().lower()
            if fact_key not in requested_keys:
                continue
            if namespace_filter and record["namespace_class"] not in namespace_filter:
                continue

            keywords = _normalize_search_tokens(str(metadata.get("keywords") or ""))
            aliases = _normalize_search_tokens(
                " ".join(str(value) for value in metadata.get("value_aliases", []))
            )
            canonical_value = str(metadata.get("canonical_value") or "").strip().lower()

            score = 8.0
            if metadata.get("temporal_slot") == "current":
                score += 0.4
            if record["state_status"] == "canonical_active":
                score += 0.5
            if canonical_value and canonical_value in normalized_query:
                score += 2.0

            overlap_terms = set(terms)
            score += 0.6 * len(overlap_terms.intersection(set(keywords)))
            score += 0.8 * len(overlap_terms.intersection(set(aliases)))

            candidate = dict(record)
            candidate["metadata"] = metadata
            candidate["score"] = float(score)
            ranked.append(candidate)

        ranked.sort(
            key=lambda item: (
                float(item.get("score", 0.0)),
                item.get("updated_at") or "",
            ),
            reverse=True,
        )
        return ranked[:max_items]

    def record_transition(
        self,
        record_id: str,
        from_state: str | None,
        to_state: str,
        reason: str,
        *,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        self._require_connection()
        transition_id = f"txn-{uuid4().hex[:12]}"
        self._conn.execute(
            """
            INSERT INTO core2_transitions (transition_id, plane_name, record_id, from_state, to_state, reason, created_at, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                transition_id,
                PLANE_CANONICAL_TRUTH,
                record_id,
                from_state,
                to_state,
                reason,
                utc_now_iso(),
                _dump_json(metadata or {}),
            ),
        )
        return transition_id

    def get_transitions(self, record_id: str) -> List[Dict[str, Any]]:
        self._require_connection()
        rows = self._conn.execute(
            "SELECT * FROM core2_transitions WHERE record_id = ? ORDER BY created_at ASC",
            (record_id,),
        ).fetchall()
        return [
            {
                "transition_id": row["transition_id"],
                "from_state": row["from_state"],
                "to_state": row["to_state"],
                "reason": row["reason"],
                "created_at": row["created_at"],
                "metadata": _load_json(row["metadata_json"]),
            }
            for row in rows
        ]

    def update_canonical_state(
        self,
        object_id: str,
        to_state: str,
        reason: str,
        *,
        metadata_patch: Optional[Dict[str, Any]] = None,
        field_updates: Optional[Dict[str, Any]] = None,
    ) -> bool:
        self._require_connection()
        record = self.get_canonical_object(object_id)
        if record is None:
            return False

        now = utc_now_iso()
        metadata = dict(record["metadata"])
        metadata.update(metadata_patch or {})
        updates = {
            "state_status": to_state,
            "updated_at": now,
            "metadata_json": _dump_json(metadata),
        }
        updates.update(field_updates or {})
        assignments = ", ".join(f"{column} = ?" for column in updates)
        values = list(updates.values()) + [object_id]
        self._conn.execute(
            f"UPDATE core2_canonical_truth SET {assignments} WHERE object_id = ?",
            values,
        )
        self.record_transition(
            object_id,
            record["state_status"],
            to_state,
            reason,
            metadata=metadata_patch or {},
        )
        self.rebuild_indices_for_object(object_id)
        self._conn.commit()
        return True

    def supersede_object(
        self, new_object_id: str, old_object_id: str, reason: str
    ) -> bool:
        self._require_connection()
        new_record = self.get_canonical_object(new_object_id)
        old_record = self.get_canonical_object(old_object_id)
        if new_record is None or old_record is None:
            return False
        if old_record["state_status"] == "superseded":
            return False

        now = utc_now_iso()
        old_metadata = dict(old_record["metadata"])
        old_metadata["superseded_by"] = new_object_id
        self.update_canonical_state(
            old_object_id,
            "superseded",
            reason,
            metadata_patch=old_metadata,
            field_updates={"superseded_at": now},
        )

        new_metadata = dict(new_record["metadata"])
        supersedes = list(new_metadata.get("supersedes_refs", []))
        if old_object_id not in supersedes:
            supersedes.append(old_object_id)
        self.update_canonical_state(
            new_object_id,
            new_record["state_status"],
            "register_supersession",
            metadata_patch={**new_metadata, "supersedes_refs": supersedes},
        )
        self.add_edge(
            from_plane=PLANE_CANONICAL_TRUTH,
            from_id=new_object_id,
            to_plane=PLANE_CANONICAL_TRUTH,
            to_id=old_object_id,
            edge_type=EDGE_SUPERSEDES,
            metadata={"reason": reason},
            commit=False,
        )
        self._conn.commit()
        return True

    def mark_conflict(
        self, left_object_id: str, right_object_id: str, reason: str
    ) -> bool:
        self._require_connection()
        left = self.get_canonical_object(left_object_id)
        right = self.get_canonical_object(right_object_id)
        if left is None or right is None:
            return False
        created = False
        for src, dst in (
            (left_object_id, right_object_id),
            (right_object_id, left_object_id),
        ):
            edge_id = self.add_edge(
                from_plane=PLANE_CANONICAL_TRUTH,
                from_id=src,
                to_plane=PLANE_CANONICAL_TRUTH,
                to_id=dst,
                edge_type=EDGE_CONFLICTS_WITH,
                metadata={"reason": reason},
                commit=False,
            )
            created = created or bool(edge_id)

        for object_id, other_id, record in (
            (left_object_id, right_object_id, left),
            (right_object_id, left_object_id, right),
        ):
            refs = list(record["metadata"].get("conflict_refs", []))
            if other_id not in refs:
                refs.append(other_id)
                self.update_canonical_state(
                    object_id,
                    "conflicted"
                    if record["state_status"] not in INACTIVE_STATE_STATUSES
                    else record["state_status"],
                    "conflict_marked",
                    metadata_patch={**record["metadata"], "conflict_refs": refs},
                )
        self._conn.commit()
        return created

    def archive_object(self, object_id: str, reason: str) -> bool:
        return self.update_canonical_state(object_id, "archived", reason)

    def archive_stale_provisionals(
        self, *, now: str | None = None, stale_days: int = 30
    ) -> int:
        self._require_connection()
        reference_time = datetime.fromisoformat(
            (now or utc_now_iso()).replace("Z", "+00:00")
        )
        cutoff = reference_time - timedelta(days=stale_days)
        rows = self._conn.execute(
            """
            SELECT object_id, recorded_at FROM core2_canonical_truth
            WHERE state_status = 'provisional'
            """
        ).fetchall()
        archived = 0
        for row in rows:
            recorded_at = row["recorded_at"]
            try:
                recorded_time = datetime.fromisoformat(
                    str(recorded_at).replace("Z", "+00:00")
                )
            except ValueError:
                continue
            if recorded_time <= cutoff:
                if self.update_canonical_state(
                    row["object_id"], "archived", "stale_provisional_demotion"
                ):
                    archived += 1
        return archived

    def rebuild_indices_for_object(self, object_id: str) -> None:
        self._require_connection()
        record = self.get_canonical_object(object_id)
        if record is None:
            return
        now = utc_now_iso()
        metadata = dict(record.get("metadata") or {})
        lexical_key = " ".join(
            [
                record["title"],
                record["namespace"],
                record["namespace_class"],
                record["content"],
            ]
        ).strip()
        index_specs = {
            "lexical": {
                "index_key": lexical_key,
                "payload": {
                    "support_level": record["support_level"],
                    "state_status": record["state_status"],
                },
            }
        }
        fact_key = str(metadata.get("fact_key") or "").strip()
        canonical_value = str(metadata.get("canonical_value") or "").strip()
        if fact_key:
            index_specs["fact_key"] = {
                "index_key": " ".join(
                    [
                        fact_key,
                        canonical_value,
                        " ".join(
                            str(alias).strip()
                            for alias in list(metadata.get("value_aliases") or [])
                            if str(alias).strip()
                        ),
                    ]
                ).strip(),
                "payload": {
                    "fact_kind": metadata.get("fact_kind"),
                    "fact_key": fact_key,
                    "canonical_value": canonical_value,
                    "state_status": record["state_status"],
                },
            }
        for index_kind, spec in index_specs.items():
            payload_json = _dump_json(spec["payload"])
            _upsert_row(
                self._conn,
                select_sql="""
                SELECT index_id FROM core2_retrieval_indices
                WHERE plane_name = ? AND record_id = ? AND index_kind = ?
                """,
                select_params=(PLANE_CANONICAL_TRUTH, object_id, index_kind),
                update_sql="""
                UPDATE core2_retrieval_indices
                SET index_key = ?, payload_json = ?, updated_at = ?
                WHERE index_id = ?
                """,
                update_params=(spec["index_key"], payload_json, now),
                insert_sql="""
                INSERT INTO core2_retrieval_indices (index_id, plane_name, record_id, index_kind, index_key, payload_json, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                insert_params=(
                    f"idx-{uuid4().hex[:12]}",
                    PLANE_CANONICAL_TRUTH,
                    object_id,
                    index_kind,
                    spec["index_key"],
                    payload_json,
                    now,
                ),
            )

        view_specs = {
            "supported_compact": (
                record["content"][:180].strip(),
                {"title": record["title"], "support_level": record["support_level"]},
            ),
            "final_compact": (
                f"{record['title']}: {record['content'][:140].strip()}",
                {"title": record["title"], "state_status": record["state_status"]},
            ),
            "exploratory_full": (
                record["content"][:420].strip(),
                {"title": record["title"], "namespace": record["namespace"]},
            ),
            "artifact_rehydrate": (
                record["content"],
                {"title": record["title"], "source_raw_id": record["source_raw_id"]},
            ),
        }
        if fact_key:
            fact_title = str(record["title"] or fact_key).strip()
            fact_content = canonical_value or record["content"][:160].strip()
            view_specs["fact_compact"] = (
                f"{fact_title}: {fact_content}".strip(": "),
                {
                    "fact_kind": metadata.get("fact_kind"),
                    "fact_key": fact_key,
                    "canonical_value": canonical_value,
                    "temporal_slot": metadata.get("temporal_slot"),
                },
            )
        for view_kind, (view_content, payload_obj) in view_specs.items():
            payload_json = _dump_json(payload_obj)
            _upsert_row(
                self._conn,
                select_sql="""
                SELECT view_id FROM core2_delivery_views
                WHERE plane_name = ? AND record_id = ? AND view_kind = ?
                """,
                select_params=(PLANE_CANONICAL_TRUTH, object_id, view_kind),
                update_sql="""
                UPDATE core2_delivery_views
                SET content = ?, payload_json = ?, updated_at = ?
                WHERE view_id = ?
                """,
                update_params=(view_content, payload_json, now),
                insert_sql="""
                INSERT INTO core2_delivery_views (view_id, plane_name, record_id, view_kind, content, payload_json, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                insert_params=(
                    f"view-{uuid4().hex[:12]}",
                    PLANE_CANONICAL_TRUTH,
                    object_id,
                    view_kind,
                    view_content,
                    payload_json,
                    now,
                ),
            )

    def apply_activation_decay(self) -> int:
        self._require_connection()
        updated = 0
        for record in self.list_canonical_objects(include_inactive=False):
            activation_score = record["metadata"].get("activation_score")
            if activation_score is None:
                continue
            new_score = max(0.0, float(activation_score) - 0.1)
            metadata = dict(record["metadata"])
            metadata["activation_score"] = round(new_score, 3)
            if self.update_canonical_state(
                record["object_id"],
                record["state_status"],
                "activation_decay",
                metadata_patch=metadata,
            ):
                updated += 1
        return updated

    def find_identity_clusters(
        self, *, include_inactive: bool = True
    ) -> List[List[Dict[str, Any]]]:
        clusters: Dict[str, List[Dict[str, Any]]] = {}
        for record in self.list_canonical_objects(include_inactive=include_inactive):
            clusters.setdefault(record["identity_key"], []).append(record)
        return [records for records in clusters.values() if records]

    def add_turn(
        self, *, session_id: str, user_content: str, assistant_content: str
    ) -> Dict[str, Any]:
        self._require_connection()
        turn_id = f"turn-{uuid4().hex[:12]}"
        created_at = utc_now_iso()
        self._conn.execute(
            """
            INSERT INTO core2_turns (turn_id, session_id, user_content, assistant_content, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (turn_id, session_id, user_content, assistant_content, created_at),
        )
        self._conn.commit()
        return {"turn_id": turn_id, "created_at": created_at}

    def find_canonical_by_identity_key(
        self, identity_key: str, *, include_inactive: bool = True
    ) -> List[Dict[str, Any]]:
        self._require_connection()
        sql = "SELECT * FROM core2_canonical_truth WHERE identity_key = ?"
        params: tuple[Any, ...] = (identity_key,)
        if not include_inactive:
            sql += " AND state_status NOT IN ('rejected', 'archived', 'superseded')"
        sql += " ORDER BY updated_at DESC"
        rows = self._conn.execute(sql, params).fetchall()
        return [self._row_to_canonical(row) for row in rows]

    def get_related_records(
        self, object_id: str, *, max_hops: int = 1, limit: int = 4
    ) -> List[Dict[str, Any]]:
        related: List[Dict[str, Any]] = []
        seen = {object_id}
        frontier = [object_id]
        hops = 0
        while frontier and hops < max_hops and len(related) < limit:
            next_frontier: List[str] = []
            for current in frontier:
                for edge in self.get_edges(current):
                    neighbor = (
                        edge["to_id"] if edge["from_id"] == current else edge["from_id"]
                    )
                    if neighbor in seen:
                        continue
                    seen.add(neighbor)
                    record = self.get_canonical_object(neighbor)
                    if record is None:
                        continue
                    related.append(record)
                    next_frontier.append(neighbor)
                    if len(related) >= limit:
                        break
                if len(related) >= limit:
                    break
            frontier = next_frontier
            hops += 1
        return related
