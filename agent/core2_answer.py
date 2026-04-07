from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from agent.core2_types import (
    ANSWER_TYPE_ABSTAIN,
    ANSWER_TYPE_COMPACT_MEMORY,
    ANSWER_TYPE_EXACT_SOURCE,
    ANSWER_TYPE_EXPLORATORY_FULL,
    ANSWER_TYPE_MULTI_SOURCE_SUPPORTED,
    ANSWER_TYPE_SOURCE_SUPPORTED,
    Core2GroundingRef,
    Core2RecallItem,
    Core2RecallPacket,
    Core2RoutePlan,
    DELIVERY_VIEW_ARTIFACT_REHYDRATE,
    DELIVERY_VIEW_EXPLORATORY_FULL,
    DELIVERY_VIEW_FINAL_COMPACT,
    DELIVERY_VIEW_SUPPORTED_COMPACT,
    MODE_COMPACT_MEMORY,
    MODE_EXACT_SOURCE_REQUIRED,
    MODE_EXPLORATORY_FULL,
    QUERY_FAMILY_HIGH_RISK_STRICT,
    QUERY_FAMILY_RELATION_MULTIHOP,
    SUPPORT_EXACT_SOURCE,
    SUPPORT_NONE,
    SUPPORT_SOURCE_SUPPORTED,
)


TOKEN_BUDGETS = {
    DELIVERY_VIEW_FINAL_COMPACT: 240,
    DELIVERY_VIEW_SUPPORTED_COMPACT: 420,
    DELIVERY_VIEW_EXPLORATORY_FULL: 900,
    DELIVERY_VIEW_ARTIFACT_REHYDRATE: 1200,
}


def grounding_refs_from_items(items: Iterable[Core2RecallItem]) -> List[Dict[str, Any]]:
    refs: List[Dict[str, Any]] = []
    for item in items:
        refs.append(
            Core2GroundingRef(
                object_id=item.object_id,
                raw_id=item.source_raw_id,
                title=item.title,
                source_type=item.source_type,
                support_level=item.support_level,
                state_status=item.state_status,
                namespace=item.namespace,
                effective_from=item.effective_from,
                source_created_at=item.source_created_at,
                observed_at=item.observed_at,
            ).to_dict()
        )
    return refs


def determine_answer_type(route_plan: Core2RoutePlan, *, items: List[Core2RecallItem], support_tier: str, abstained: bool) -> str:
    if abstained:
        return ANSWER_TYPE_ABSTAIN
    if route_plan.query_mode == MODE_EXACT_SOURCE_REQUIRED or support_tier == SUPPORT_EXACT_SOURCE:
        return ANSWER_TYPE_EXACT_SOURCE
    if route_plan.query_mode == MODE_EXPLORATORY_FULL or route_plan.delivery_view == DELIVERY_VIEW_EXPLORATORY_FULL:
        return ANSWER_TYPE_EXPLORATORY_FULL
    if route_plan.query_family == QUERY_FAMILY_RELATION_MULTIHOP and len(items) > 1:
        return ANSWER_TYPE_MULTI_SOURCE_SUPPORTED
    if route_plan.query_mode == MODE_COMPACT_MEMORY or route_plan.delivery_view == DELIVERY_VIEW_FINAL_COMPACT:
        return ANSWER_TYPE_COMPACT_MEMORY
    return ANSWER_TYPE_SOURCE_SUPPORTED


def canonical_value_for_items(items: List[Core2RecallItem], operator: Optional[str]) -> Any:
    if operator == "count":
        return len(items)
    if operator == "aggregate":
        return [item.content for item in items]
    if not items:
        return None
    return items[0].content


def _clip_text(text: str, budget: int) -> str:
    cleaned = " ".join((text or "").split())
    if len(cleaned) <= budget:
        return cleaned
    if budget <= 3:
        return cleaned[:budget]
    return cleaned[: budget - 3].rstrip() + "..."


def render_display_value(
    route_plan: Core2RoutePlan,
    *,
    items: List[Core2RecallItem],
    delivery_resolver,
) -> str:
    if not items:
        return ""

    budget = TOKEN_BUDGETS.get(route_plan.delivery_view, 320)
    if route_plan.delivery_view == DELIVERY_VIEW_EXPLORATORY_FULL:
        lines: List[str] = []
        for item in items:
            lines.append(f"- [{item.namespace}] {item.title}: {_clip_text(item.content, 140)}")
        return _clip_text("\n".join(lines), budget)

    primary = items[0]
    resolved = delivery_resolver(primary.object_id, route_plan.delivery_view)
    if resolved:
        return _clip_text(resolved, budget)

    if route_plan.delivery_view == DELIVERY_VIEW_FINAL_COMPACT:
        return _clip_text(f"{primary.title}: {primary.snippet}", budget)
    if route_plan.delivery_view == DELIVERY_VIEW_SUPPORTED_COMPACT:
        return _clip_text(f"{primary.title}: {primary.content}", budget)
    return _clip_text(primary.content, budget)


def confidence_tier_from_dimensions(*, support_confidence: str, temporal_confidence: str, resolution_confidence: str, identity_confidence: str, abstained: bool) -> str:
    if abstained:
        return "abstain"
    ordered = [support_confidence, temporal_confidence, resolution_confidence, identity_confidence]
    if all(value == "high" for value in ordered):
        return "high"
    if any(value == "low" for value in ordered):
        return "low"
    return "medium"


def build_answer_packet(
    *,
    query: str,
    operator: Optional[str],
    risk_class: str,
    route_plan: Core2RoutePlan,
    items: List[Core2RecallItem],
    support_tier: str,
    confidence: str,
    support_confidence: str,
    temporal_confidence: str,
    resolution_confidence: str,
    identity_confidence: str,
    abstained: bool,
    reason: Optional[str],
    delivery_resolver,
    valid_as_of: Optional[str] = None,
    superseded_by: Optional[str] = None,
    conflict_refs: Optional[List[str]] = None,
) -> Core2RecallPacket:
    answer_type = determine_answer_type(route_plan, items=items, support_tier=support_tier, abstained=abstained)
    display_value = "" if abstained else render_display_value(route_plan, items=items, delivery_resolver=delivery_resolver)
    grounding_refs = grounding_refs_from_items(items)
    confidence_tier = confidence_tier_from_dimensions(
        support_confidence=support_confidence,
        temporal_confidence=temporal_confidence,
        resolution_confidence=resolution_confidence,
        identity_confidence=identity_confidence,
        abstained=abstained,
    )

    if route_plan.query_family == QUERY_FAMILY_HIGH_RISK_STRICT and valid_as_of is None and items:
        valid_as_of = items[0].effective_from or items[0].source_created_at or items[0].recorded_at

    return Core2RecallPacket(
        query=query,
        mode=route_plan.query_mode,
        query_mode=route_plan.query_mode,
        operator=operator,
        risk_class=risk_class,
        query_family=route_plan.query_family,
        route_family=route_plan.route_family,
        route_plan=route_plan.to_dict(),
        answer_type=answer_type,
        canonical_value=None if abstained else canonical_value_for_items(items, operator),
        display_value=display_value,
        grounding_refs=grounding_refs,
        support_tier=support_tier if not abstained else SUPPORT_NONE,
        confidence=confidence,
        confidence_tier=confidence_tier,
        abstained=abstained,
        items=items,
        reason=reason,
        support_confidence=support_confidence,
        temporal_confidence=temporal_confidence,
        resolution_confidence=resolution_confidence,
        identity_confidence=identity_confidence,
        delivery_view=route_plan.delivery_view,
        token_budget=TOKEN_BUDGETS.get(route_plan.delivery_view, 320),
        retrieved_item_count=len(items),
        valid_as_of=valid_as_of,
        superseded_by=superseded_by,
        conflict_refs=conflict_refs or [],
    )
