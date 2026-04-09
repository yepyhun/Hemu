from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


PLANE_RAW_ARCHIVE = "raw_archive"
PLANE_CANONICAL_TRUTH = "canonical_truth"
PLANE_DERIVED_PROPOSITIONS = "derived_propositions"
PLANE_RETRIEVAL_INDICES = "retrieval_indices"
PLANE_DELIVERY_VIEWS = "delivery_views"

VALID_PLANES = {
    PLANE_RAW_ARCHIVE,
    PLANE_CANONICAL_TRUTH,
    PLANE_DERIVED_PROPOSITIONS,
    PLANE_RETRIEVAL_INDICES,
    PLANE_DELIVERY_VIEWS,
}

OBJECT_KIND_ENTITY = "entity"
OBJECT_KIND_EVENT = "event"
OBJECT_KIND_STATE = "state"
OBJECT_KIND_MEASURE = "measure"
OBJECT_KIND_SOURCE = "source"

VALID_OBJECT_KINDS = {
    OBJECT_KIND_ENTITY,
    OBJECT_KIND_EVENT,
    OBJECT_KIND_STATE,
    OBJECT_KIND_MEASURE,
    OBJECT_KIND_SOURCE,
}

STATE_CANDIDATE = "candidate"
STATE_PROVISIONAL = "provisional"
STATE_CANONICAL_ACTIVE = "canonical_active"
STATE_CONFLICTED = "conflicted"
STATE_SUPERSEDED = "superseded"
STATE_REJECTED = "rejected"
STATE_ARCHIVED = "archived"

ACTIVE_STATE_STATUSES = {STATE_CANDIDATE, STATE_PROVISIONAL, STATE_CANONICAL_ACTIVE, STATE_CONFLICTED}
INACTIVE_STATE_STATUSES = {STATE_SUPERSEDED, STATE_REJECTED, STATE_ARCHIVED}

EDGE_SUPERSEDES = "supersedes"
EDGE_CORRECTS = "corrects"
EDGE_CONFLICTS_WITH = "conflicts_with"
EDGE_DERIVED_FROM = "derived_from"

VALID_EDGE_TYPES = {
    EDGE_SUPERSEDES,
    EDGE_CORRECTS,
    EDGE_CONFLICTS_WITH,
    EDGE_DERIVED_FROM,
}

SUPPORT_EXACT_SOURCE = "exact_source"
SUPPORT_SOURCE_SUPPORTED = "source_supported"
SUPPORT_MULTI_SOURCE = "multi_source_supported"
SUPPORT_INFERRED = "inferred_supported"
SUPPORT_WEAK = "weak_support"
SUPPORT_NONE = "none"

MODE_AUTO = "auto"
MODE_EXACT_SOURCE_REQUIRED = "exact_source_required"
MODE_SOURCE_SUPPORTED = "source_supported"
MODE_COMPACT_MEMORY = "compact_memory"
MODE_EXPLORATORY_FULL = "exploratory_full"

VALID_QUERY_MODES = {
    MODE_AUTO,
    MODE_EXACT_SOURCE_REQUIRED,
    MODE_SOURCE_SUPPORTED,
    MODE_COMPACT_MEMORY,
    MODE_EXPLORATORY_FULL,
}

QUERY_FAMILY_EXACT_LOOKUP = "exact_lookup"
QUERY_FAMILY_FACTUAL_SUPPORTED = "factual_supported"
QUERY_FAMILY_PERSONAL_RECALL = "personal_recall"
QUERY_FAMILY_RELATION_MULTIHOP = "relation_multihop"
QUERY_FAMILY_UPDATE_RESOLUTION = "update_resolution"
QUERY_FAMILY_HIGH_RISK_STRICT = "high_risk_strict"
QUERY_FAMILY_EXPLORATORY_DISCOVERY = "exploratory_discovery"

ROUTE_FAMILY_SOURCE_FIRST = "lexical/source-first"
ROUTE_FAMILY_SEMANTIC_FIRST = "semantic-first"
ROUTE_FAMILY_ASSOCIATION_GRAPH = "association/graph-assisted"
ROUTE_FAMILY_CURATED_MEMORY = "curated_memory_view"

ANSWER_TYPE_EXACT_SOURCE = "exact_source"
ANSWER_TYPE_SOURCE_SUPPORTED = "source_supported"
ANSWER_TYPE_COMPACT_MEMORY = "compact_memory"
ANSWER_TYPE_EXPLORATORY_FULL = "exploratory_full"
ANSWER_TYPE_MULTI_SOURCE_SUPPORTED = "multi_source_supported"
ANSWER_TYPE_ABSTAIN = "abstain"

DELIVERY_VIEW_FINAL_COMPACT = "final_compact"
DELIVERY_VIEW_SUPPORTED_COMPACT = "supported_compact"
DELIVERY_VIEW_EXPLORATORY_FULL = "exploratory_full"
DELIVERY_VIEW_ARTIFACT_REHYDRATE = "artifact_rehydrate"

NAMESPACE_PERSONAL = "personal"
NAMESPACE_WORKSPACE = "workspace"
NAMESPACE_LIBRARY = "library"
NAMESPACE_HIGH_RISK = "high_risk"

VALID_NAMESPACE_CLASSES = {
    NAMESPACE_PERSONAL,
    NAMESPACE_WORKSPACE,
    NAMESPACE_LIBRARY,
    NAMESPACE_HIGH_RISK,
}

TOOL_BUDGET_PROFILE_MINIMAL = "minimal"
TOOL_BUDGET_PROFILE_COMPACT = "compact"
TOOL_BUDGET_PROFILE_SUPPORTED = "supported"
TOOL_BUDGET_PROFILE_FULL = "full"

ANSWER_SURFACE_FACT_ONLY = "fact_only"
ANSWER_SURFACE_FACT_PLUS_SUMMARY = "fact_plus_summary"
ANSWER_SURFACE_FALLBACK = "fallback"

ANSWER_SURFACE_TEXT_LIMIT = 220
ANSWER_SURFACE_SUMMARY_LIMIT = 160

DEFAULT_TOOL_BUDGET_PROFILE = TOOL_BUDGET_PROFILE_COMPACT
TOOL_PAYLOAD_MODE_DEFAULT = "default"
TOOL_PAYLOAD_MODE_LEAN = "lean"

TOOL_BUDGET_PROFILES: Dict[str, Dict[str, int | bool]] = {
    TOOL_BUDGET_PROFILE_MINIMAL: {
        "content_limit": 140,
        "snippet_limit": 96,
        "display_limit": 160,
        "item_limit": 2,
        "grounding_limit": 2,
        "compact_metadata": 1,
    },
    TOOL_BUDGET_PROFILE_COMPACT: {
        "content_limit": 220,
        "snippet_limit": 180,
        "display_limit": 240,
        "item_limit": 3,
        "grounding_limit": 3,
        "compact_metadata": 1,
    },
    TOOL_BUDGET_PROFILE_SUPPORTED: {
        "content_limit": 320,
        "snippet_limit": 220,
        "display_limit": 320,
        "item_limit": 3,
        "grounding_limit": 3,
        "compact_metadata": 1,
    },
    TOOL_BUDGET_PROFILE_FULL: {
        "content_limit": 0,
        "snippet_limit": 0,
        "display_limit": 0,
        "item_limit": 0,
        "grounding_limit": 0,
        "compact_metadata": 0,
    },
}


def get_tool_budget_profile(name: str | None) -> Dict[str, int | bool]:
    key = str(name or DEFAULT_TOOL_BUDGET_PROFILE).strip().lower() or DEFAULT_TOOL_BUDGET_PROFILE
    return TOOL_BUDGET_PROFILES.get(key, TOOL_BUDGET_PROFILES[DEFAULT_TOOL_BUDGET_PROFILE])


def _clip_tool_text(value: str, limit: int) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    if limit <= 3:
        return text[:limit]
    return text[: limit - 3].rstrip() + "..."


def _compact_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    keep = {
        "identity_key",
        "conflict_refs",
        "dataset",
        "session_id",
        "turn_index",
        "session_date",
    }
    compact: Dict[str, Any] = {}
    for key, value in (metadata or {}).items():
        if key in keep and value not in (None, "", [], {}):
            compact[key] = value
    return compact


def _payload_mode(value: str | None) -> str:
    normalized = str(value or TOOL_PAYLOAD_MODE_DEFAULT).strip().lower()
    return normalized or TOOL_PAYLOAD_MODE_DEFAULT


@dataclass
class Core2GroundingRef:
    object_id: str
    raw_id: str | None
    title: str
    source_type: str
    support_level: str
    state_status: str
    namespace: str
    effective_from: str | None = None
    source_created_at: str | None = None
    observed_at: str | None = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Core2RoutePlan:
    query_family: str
    route_family: str
    query_mode: str
    retrieval_cap: int
    delivery_view: str
    strict_grounding: bool = False
    temporal_strict: bool = False
    completeness_required: bool = False
    graph_hops: int = 0
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Core2RecallItem:
    object_id: str
    plane: str
    object_kind: str
    title: str
    namespace: str
    namespace_class: str
    risk_class: str
    source_type: str
    support_level: str
    state_status: str
    content: str
    snippet: str
    source_raw_id: str | None = None
    observed_at: str | None = None
    source_created_at: str | None = None
    effective_from: str | None = None
    effective_to: str | None = None
    recorded_at: str | None = None
    superseded_at: str | None = None
    invalidated_at: str | None = None
    created_at: str | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_tool_dict(
        self,
        profile: str = DEFAULT_TOOL_BUDGET_PROFILE,
        payload_mode: str = TOOL_PAYLOAD_MODE_DEFAULT,
    ) -> Dict[str, Any]:
        cfg = get_tool_budget_profile(profile)
        mode = _payload_mode(payload_mode)
        if mode == TOOL_PAYLOAD_MODE_LEAN:
            payload = {
                "object_id": self.object_id,
                "title": self.title,
                "content": self.content,
                "snippet": self.snippet,
                "support_level": self.support_level,
                "state_status": self.state_status,
                "effective_from": self.effective_from,
                "source_created_at": self.source_created_at,
                "metadata": self.metadata,
                "score": self.score,
            }
        else:
            payload = asdict(self)
        content_limit = int(cfg.get("content_limit", 0) or 0)
        snippet_limit = int(cfg.get("snippet_limit", 0) or 0)
        if content_limit > 0:
            payload["content"] = _clip_tool_text(self.content, content_limit)
        if snippet_limit > 0:
            payload["snippet"] = _clip_tool_text(self.snippet, snippet_limit)
        payload["metadata"] = _compact_metadata(self.metadata) if bool(cfg.get("compact_metadata", True)) else dict(self.metadata)
        payload["score"] = round(float(self.score), 3)
        return payload


@dataclass
class Core2AnswerSurface:
    family: str
    mode: str
    answer_mode: str | None = None
    text: str | None = None
    structured: Dict[str, Any] = field(default_factory=dict)
    summary: str | None = None
    support_tier: str | None = None
    confidence_tier: str | None = None
    fact_key: str | None = None
    retrieval_path: str | None = None
    used_item_ids: List[str] = field(default_factory=list)
    winner: str | None = None
    fallback_reason: str | None = None

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        if isinstance(payload.get("text"), str):
            payload["text"] = _clip_tool_text(payload["text"], ANSWER_SURFACE_TEXT_LIMIT)
        if isinstance(payload.get("summary"), str):
            payload["summary"] = _clip_tool_text(payload["summary"], ANSWER_SURFACE_SUMMARY_LIMIT)
        return payload


@dataclass
class Core2RecallPacket:
    query: str
    mode: str
    operator: str | None
    risk_class: str
    support_tier: str
    confidence: str
    abstained: bool
    query_family: str | None = None
    route_family: str | None = None
    route_plan: Dict[str, Any] | None = None
    answer_type: str | None = None
    query_mode: str | None = None
    canonical_value: Any = None
    display_value: str | None = None
    grounding_refs: List[Dict[str, Any]] = field(default_factory=list)
    confidence_tier: str | None = None
    delivery_view: str | None = None
    token_budget: int | None = None
    retrieved_item_count: int | None = None
    valid_as_of: str | None = None
    superseded_by: str | None = None
    conflict_refs: List[str] = field(default_factory=list)
    items: List[Core2RecallItem] = field(default_factory=list)
    answer_surface: Core2AnswerSurface | None = None
    authoritative_payload: Dict[str, Any] | None = None
    reason: str | None = None
    support_confidence: str | None = None
    temporal_confidence: str | None = None
    resolution_confidence: str | None = None
    identity_confidence: str | None = None

    def to_dict(
        self,
        *,
        compact: bool = False,
        tool_budget_profile: str | None = None,
        tool_payload_mode: str = TOOL_PAYLOAD_MODE_DEFAULT,
    ) -> Dict[str, Any]:
        canonical_value = self.canonical_value
        display_value = self.display_value
        grounding_refs = list(self.grounding_refs)
        profile_name = tool_budget_profile or (DEFAULT_TOOL_BUDGET_PROFILE if compact else None)
        payload_mode = _payload_mode(tool_payload_mode)
        if profile_name:
            cfg = get_tool_budget_profile(profile_name)
            item_limit = int(cfg.get("item_limit", 0) or 0)
            grounding_limit = int(cfg.get("grounding_limit", 0) or 0)
            items = [item.to_tool_dict(profile_name, payload_mode=payload_mode) for item in self.items]
            if item_limit > 0:
                items = items[:item_limit]
            if grounding_limit > 0:
                grounding_refs = grounding_refs[:grounding_limit]
            display_limit = int(cfg.get("display_limit", 0) or 0)
            if isinstance(display_value, str):
                display_value = _clip_tool_text(display_value, display_limit) if display_limit > 0 else display_value
            if isinstance(canonical_value, str):
                canonical_value = display_value or (_clip_tool_text(canonical_value, display_limit) if display_limit > 0 else canonical_value)
        else:
            items = [item.to_dict() for item in self.items]
        answer_surface = self.answer_surface.to_dict() if self.answer_surface else None
        payload = {
            "query": self.query,
            "mode": self.mode,
            "query_mode": self.query_mode or self.mode,
            "operator": self.operator,
            "risk_class": self.risk_class,
            "query_family": self.query_family,
            "route_family": self.route_family,
            "route_plan": self.route_plan,
            "answer_type": self.answer_type,
            "canonical_value": canonical_value,
            "display_value": display_value,
            "grounding_refs": grounding_refs,
            "support_tier": self.support_tier,
            "confidence": self.confidence,
            "confidence_tier": self.confidence_tier or self.confidence,
            "abstained": self.abstained,
            "reason": self.reason,
            "abstain_reason": self.reason,
            "delivery_view": self.delivery_view,
            "token_budget": self.token_budget,
            "retrieved_item_count": self.retrieved_item_count if self.retrieved_item_count is not None else len(self.items),
            "valid_as_of": self.valid_as_of,
            "superseded_by": self.superseded_by,
            "conflict_refs": self.conflict_refs,
            "support_confidence": self.support_confidence,
            "temporal_confidence": self.temporal_confidence,
            "resolution_confidence": self.resolution_confidence,
            "identity_confidence": self.identity_confidence,
            "items": items,
            "answer_surface": answer_surface,
        }
        if self.authoritative_payload:
            payload["authoritative_payload"] = dict(self.authoritative_payload)
        if payload_mode == TOOL_PAYLOAD_MODE_LEAN:
            lean_payload = {
                "query": payload["query"],
                "mode": payload["mode"],
                "support_tier": payload["support_tier"],
                "abstained": payload["abstained"],
                "reason": payload["reason"],
                "items": payload["items"],
            }
            if answer_surface:
                lean_payload["answer_surface"] = answer_surface
            if self.authoritative_payload:
                lean_payload["authoritative_payload"] = {
                    "text": str(self.authoritative_payload.get("text") or "").strip(),
                    "mode": str(self.authoritative_payload.get("mode") or "").strip(),
                    "winner": self.authoritative_payload.get("winner"),
                }
            if not payload["items"]:
                lean_payload["canonical_value"] = payload["canonical_value"]
                lean_payload["display_value"] = payload["display_value"]
            else:
                lean_payload["retrieved_item_count"] = payload["retrieved_item_count"]
            if grounding_refs:
                lean_payload["grounding_refs"] = [
                    {
                        "object_id": ref.get("object_id"),
                        "title": ref.get("title"),
                        "raw_id": ref.get("raw_id"),
                    }
                    for ref in grounding_refs
                ]
            return lean_payload
        return payload
