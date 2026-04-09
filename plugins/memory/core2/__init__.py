from __future__ import annotations

import json
import os
from typing import Any, Dict, List

from agent.core2_authoritative import try_authoritative_answer
from agent.core2_types import (
    ANSWER_TYPE_EXACT_SOURCE,
    ANSWER_TYPE_EXPLORATORY_FULL,
    ANSWER_TYPE_MULTI_SOURCE_SUPPORTED,
    ANSWER_TYPE_SOURCE_SUPPORTED,
    DELIVERY_VIEW_ARTIFACT_REHYDRATE,
    DELIVERY_VIEW_EXPLORATORY_FULL,
    DELIVERY_VIEW_SUPPORTED_COMPACT,
    MODE_EXACT_SOURCE_REQUIRED,
    get_tool_budget_profile,
)
from agent.core2_runtime import Core2Runtime
from agent.memory_provider import MemoryProvider


RECALL_SCHEMA = {
    "name": "core2_recall",
    "description": (
        "Grounded memory recall over the Core2 canonical memory kernel. "
        "Use for precise facts, personal memory, source-supported recall, or exploratory synthesis."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "What to recall."},
            "mode": {
                "type": "string",
                "enum": ["auto", "exact_source_required", "source_supported", "compact_memory", "exploratory_full"],
                "description": "Recall mode. Use exact_source_required for high-risk or citation questions.",
            },
            "operator": {
                "type": "string",
                "enum": ["attribute", "count", "aggregate"],
                "description": "Force operator selection when needed.",
            },
            "risk_class": {
                "type": "string",
                "enum": ["standard", "medical", "legal", "high"],
                "description": "Tightens abstention and routing for high-risk requests.",
            },
            "max_items": {"type": "integer", "description": "Maximum retrieval items to consider (default 6)."},
        },
        "required": ["query"],
    },
}

REMEMBER_SCHEMA = {
    "name": "core2_remember",
    "description": (
        "Ingest durable knowledge into the Core2 kernel. Use for explicit preferences, notes, document facts, or curated second-brain entries."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "content": {"type": "string", "description": "Durable content to ingest."},
            "title": {"type": "string", "description": "Human-readable source title."},
            "namespace": {"type": "string", "description": "Memory namespace, e.g. personal, project, library, medical, legal."},
            "risk_class": {"type": "string", "enum": ["standard", "medical", "legal", "high"]},
            "language": {"type": "string", "description": "Language tag for the content."},
            "effective_from": {"type": "string", "description": "Optional ISO timestamp for when this became true."},
        },
        "required": ["content"],
    },
}

EXPLAIN_SCHEMA = {
    "name": "core2_explain",
    "description": "Inspect a Core2 canonical object with its source, span, and edges.",
    "parameters": {
        "type": "object",
        "properties": {
            "object_id": {"type": "string", "description": "Canonical object identifier."},
        },
        "required": ["object_id"],
    },
}


class Core2MemoryProvider(MemoryProvider):
    def __init__(self):
        self.runtime: Core2Runtime | None = None
        self._session_id = ""
        self._hermes_home = ""

    @property
    def name(self) -> str:
        return "core2"

    def is_available(self) -> bool:
        return True

    def initialize(self, session_id: str, **kwargs) -> None:
        hermes_home = str(kwargs.get("hermes_home") or self._hermes_home or "")
        if not hermes_home:
            from hermes_constants import get_hermes_home

            hermes_home = str(get_hermes_home())
        db_path = f"{hermes_home}/core2/core2.db"
        self.runtime = Core2Runtime(db_path)
        self.runtime.initialize(session_id)
        self._session_id = session_id
        self._hermes_home = hermes_home

    def system_prompt_block(self) -> str:
        count = 0
        if self.runtime:
            count = self.runtime.note_count()
        return (
            "# Core2 Memory\n"
            f"Stored objects: {count}\n"
            "Active local-first memory kernel. Prefer core2_recall for grounded recall and core2_remember for durable explicit memory. "
            "Use exact_source_required mode for medical/legal or citation-style questions."
        )

    def prefetch(self, query: str, *, session_id: str = "") -> str:
        if not self.runtime:
            return ""
        return self.runtime.consume_prefetch(session_id=session_id)

    def authoritative_answer(self, query: str, *, session_id: str = "") -> Dict[str, Any] | None:
        if not self.runtime:
            return None
        packet = self.runtime.recall(
            query,
            mode="source_supported",
            operator=None,
            risk_class="standard",
            max_items=6,
            session_id=session_id or self._session_id,
        )
        return try_authoritative_answer(query, packet)

    def queue_prefetch(self, query: str, *, session_id: str = "") -> None:
        if self.runtime:
            self.runtime.queue_prefetch(query, session_id=session_id or self._session_id)

    def sync_turn(self, user_content: str, assistant_content: str, *, session_id: str = "") -> None:
        if self.runtime:
            self.runtime.ingest_turn(user_content, assistant_content, session_id=session_id or self._session_id)

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        return [RECALL_SCHEMA, REMEMBER_SCHEMA, EXPLAIN_SCHEMA]

    @staticmethod
    def _resolve_tool_budget_profile(packet, requested_profile: str, risk_class: str) -> str:
        explicit = str(requested_profile or "").strip().lower()
        if explicit:
            return explicit
        normalized_risk = str(risk_class or "standard").strip().lower()
        if normalized_risk in {"medical", "legal", "high"}:
            return "full"
        query_mode = str(packet.query_mode or packet.mode or "").strip().lower()
        answer_type = str(packet.answer_type or "").strip().lower()
        delivery_view = str(packet.delivery_view or "").strip().lower()
        if query_mode == MODE_EXACT_SOURCE_REQUIRED:
            return "full"
        if answer_type == ANSWER_TYPE_EXACT_SOURCE:
            return "full"
        if answer_type == ANSWER_TYPE_EXPLORATORY_FULL:
            return "full"
        if delivery_view in {DELIVERY_VIEW_EXPLORATORY_FULL, DELIVERY_VIEW_ARTIFACT_REHYDRATE}:
            return "full"
        if answer_type in {ANSWER_TYPE_SOURCE_SUPPORTED, ANSWER_TYPE_MULTI_SOURCE_SUPPORTED}:
            return "supported"
        if delivery_view == DELIVERY_VIEW_SUPPORTED_COMPACT:
            return "supported"
        return "compact"

    def handle_tool_call(self, tool_name: str, args: Dict[str, Any], **kwargs) -> str:
        if not self.runtime:
            return json.dumps({"error": "Core2 runtime is not initialized."})
        if tool_name == "core2_recall":
            explicit_max_items = "max_items" in args
            requested_max_items = max(1, min(int(args.get("max_items", 6)), 12))
            requested_profile = (
                str(args.get("tool_budget_profile") or "").strip()
                or str(os.environ.get("CORE2_TOOL_BUDGET_PROFILE") or "").strip()
            )
            payload_mode = (
                str(args.get("tool_payload_mode") or "").strip()
                or str(os.environ.get("CORE2_TOOL_PAYLOAD_MODE") or "").strip()
                or "default"
            )
            risk_class = args.get("risk_class") or "standard"
            packet = self.runtime.recall(
                args.get("query", ""),
                mode=args.get("mode") or "auto",
                operator=args.get("operator"),
                risk_class=risk_class,
                max_items=requested_max_items,
                session_id=str(kwargs.get("session_id") or self._session_id or ""),
            )
            tool_budget_profile = self._resolve_tool_budget_profile(packet, requested_profile, str(risk_class))
            if explicit_max_items and not requested_profile:
                profile_cfg = get_tool_budget_profile(tool_budget_profile)
                item_limit = int(profile_cfg.get("item_limit", 0) or 0)
                if requested_max_items > 3 and item_limit and requested_max_items > item_limit:
                    tool_budget_profile = "full"
            return json.dumps(
                packet.to_dict(
                    compact=True,
                    tool_budget_profile=tool_budget_profile,
                    tool_payload_mode=payload_mode,
                ),
                ensure_ascii=False,
            )
        if tool_name == "core2_remember":
            content = args.get("content", "")
            if not content:
                return json.dumps({"error": "content is required"})
            result = self.runtime.ingest_note(
                content,
                title=args.get("title") or "explicit_memory",
                namespace=args.get("namespace") or "personal",
                risk_class=args.get("risk_class") or "standard",
                language=args.get("language") or "und",
                effective_from=args.get("effective_from"),
            )
            return json.dumps({"result": "stored", **result}, ensure_ascii=False)
        if tool_name == "core2_explain":
            object_id = args.get("object_id", "")
            if not object_id:
                return json.dumps({"error": "object_id is required"})
            return json.dumps(self.runtime.explain_object(object_id), ensure_ascii=False)
        return json.dumps({"error": f"Unknown tool: {tool_name}"})

    def on_memory_write(self, action: str, target: str, content: str) -> None:
        if not self.runtime or action == "remove":
            return
        self.runtime.ingest_note(
            content,
            title=f"builtin_{target}",
            namespace="personal" if target == "user" else "project",
            source_type="builtin_memory",
            metadata={"action": action, "target": target},
        )

    def shutdown(self) -> None:
        if self.runtime:
            self.runtime.shutdown()
            self.runtime = None


def register(ctx):
    ctx.register_memory_provider(Core2MemoryProvider())
