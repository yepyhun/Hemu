from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Dict, Iterable, List, Mapping


@dataclass(frozen=True)
class CoveredFactSpec:
    fact_key: str
    title: str
    fact_kind: str
    keywords: str
    extraction_patterns: tuple[str, ...]
    extra_metadata: Mapping[str, Any]
    answer_mode: str
    object_kind: str = "state"


_OCCUPATION_QUERY_MARKERS = (
    " occupation ",
    " role ",
    " job ",
    " profession ",
    " work ",
)
_PREVIOUS_QUERY_MARKERS = (" previous ", " former ", " prior ", " used to ")
_RESIDENCE_QUERY_MARKERS = (
    " where do i live ",
    " where i live ",
    " residence ",
    " home ",
)
_TIMEZONE_QUERY_MARKERS = (" timezone ", " time zone ", " tz ")
_MANAGER_QUERY_MARKERS = (" manager ",)
_TEAM_QUERY_MARKERS = (" team ",)
_EVENING_ACTIVITY_QUERY_MARKERS = (
    " evening ",
    " activity ",
    " activities ",
    " suggest ",
    " suggestions ",
    " can i do ",
)
_FOOD_DELIVERY_QUERY_MARKERS = (
    " food delivery ",
    " delivery service ",
    " delivery services ",
    " dominos ",
    " domino s ",
    " domino",
    " uber eats ",
    " doordash ",
    " grubhub ",
)
_COLLECTION_QUERY_MARKERS = (" collection ", " inventory ", " catalog ", " catalogue ")
_TEMPORAL_ELAPSED_QUERY_MARKERS = (
    " how many days ",
    " days had passed ",
    " finished reading ",
    " attended ",
    " local library ",
    " book reading event ",
)
_TRIP_QUERY_MARKERS = (
    " trip ",
    " trips ",
    " road trip ",
    " travel ",
    " hike ",
    " hiking ",
    " camping ",
)
_ORDER_QUERY_MARKERS = (
    " earliest ",
    " latest ",
    " order ",
    " first ",
    " last ",
    " before ",
    " after ",
)


COVERED_FACT_SPECS: Dict[str, CoveredFactSpec] = {
    "attribute.occupation.current": CoveredFactSpec(
        fact_key="attribute.occupation.current",
        title="Current occupation",
        fact_kind="attribute",
        keywords="occupation current role job profession work",
        extraction_patterns=(
            r"\bcurrent (?:role|occupation|job|profession)(?:\s+is|:)\s*([^.!?\n]+)",
            r"\bi work as\s+([^.!?\n]+)",
            r"\bmy (?:role|occupation|job)\s+is\s+([^.!?\n]+)",
        ),
        extra_metadata={
            "attribute_key": "occupation",
            "temporal_slot": "current",
            "value_aliases": ["role", "occupation", "job", "profession"],
        },
        answer_mode="personal_attribute",
    ),
    "attribute.occupation.previous": CoveredFactSpec(
        fact_key="attribute.occupation.previous",
        title="Previous occupation",
        fact_kind="attribute",
        keywords="occupation previous former prior role job profession work",
        extraction_patterns=(
            r"\bprevious (?:role|occupation|job|profession)(?:\s+was|:)\s*([^.!?\n]+)",
            r"\bi used to work as\s+([^.!?\n]+)",
            r"\bi previously worked as\s+([^.!?\n]+)",
        ),
        extra_metadata={
            "attribute_key": "occupation",
            "temporal_slot": "previous",
            "value_aliases": ["role", "occupation", "job", "profession"],
        },
        answer_mode="personal_attribute",
    ),
    "attribute.residence.current": CoveredFactSpec(
        fact_key="attribute.residence.current",
        title="Current residence",
        fact_kind="attribute",
        keywords="residence location city live current home",
        extraction_patterns=(
            r"\bi live in\s+([^.!?\n]+)",
            r"\bi currently live in\s+([^.!?\n]+)",
            r"\bi reside in\s+([^.!?\n]+)",
            r"\bi'm living in\s+([^.!?\n]+)",
            r"\bi'm currently living in\s+([^.!?\n]+)",
        ),
        extra_metadata={
            "attribute_key": "residence",
            "temporal_slot": "current",
            "value_aliases": ["residence", "location", "city", "home"],
        },
        answer_mode="personal_residence",
    ),
    "attribute.timezone.current": CoveredFactSpec(
        fact_key="attribute.timezone.current",
        title="Current timezone",
        fact_kind="attribute",
        keywords="timezone tz current region offset",
        extraction_patterns=(r"\btimezone\s*:\s*([^.!?\n]+)",),
        extra_metadata={
            "attribute_key": "timezone",
            "temporal_slot": "current",
            "value_aliases": ["timezone", "tz", "time zone", "offset"],
        },
        answer_mode="personal_timezone",
    ),
    "relation.manager.current": CoveredFactSpec(
        fact_key="relation.manager.current",
        title="Current manager",
        fact_kind="relation",
        keywords="manager relation reporting line current",
        extraction_patterns=(r"\bmy manager is\s+([^.!?\n]+)",),
        extra_metadata={
            "relation_type": "manager",
            "temporal_slot": "current",
        },
        answer_mode="personal_relation",
        object_kind="entity",
    ),
    "relation.team.current": CoveredFactSpec(
        fact_key="relation.team.current",
        title="Current team",
        fact_kind="relation",
        keywords="team relation current group squad",
        extraction_patterns=(r"\bi am on the\s+([^.!?\n]+?)\s+team\b",),
        extra_metadata={
            "relation_type": "team",
            "temporal_slot": "current",
        },
        answer_mode="personal_relation",
        object_kind="entity",
    ),
    "preference.evening.activities.current": CoveredFactSpec(
        fact_key="preference.evening.activities.current",
        title="Evening activity preference",
        fact_kind="preference",
        keywords="preference evening activities relaxing calm before 9 30 routine",
        extraction_patterns=(),
        extra_metadata={
            "preference_topic": "evening_activities",
            "preference_polarity": "positive",
        },
        answer_mode="preference_guidance",
    ),
    "preference.evening.screen_avoid.current": CoveredFactSpec(
        fact_key="preference.evening.screen_avoid.current",
        title="Evening screen avoidance",
        fact_kind="preference",
        keywords="preference evening avoid phone tv television sleep quality",
        extraction_patterns=(),
        extra_metadata={
            "preference_topic": "evening_activities",
            "preference_polarity": "negative",
        },
        answer_mode="preference_guidance",
    ),
    "aggregate.food_delivery_service.recent": CoveredFactSpec(
        fact_key="aggregate.food_delivery_service.recent",
        title="Recent food delivery service",
        fact_kind="aggregate_member",
        keywords="aggregate count food delivery service recent dominos uber eats doordash grubhub",
        extraction_patterns=(),
        extra_metadata={
            "aggregate_group": "food_delivery_service",
            "temporal_slot": "recent",
        },
        answer_mode="aggregate_count",
        object_kind="entity",
    ),
    "aggregate.collection.total.current": CoveredFactSpec(
        fact_key="aggregate.collection.total.current",
        title="Current collection total",
        fact_kind="aggregate_total",
        keywords="aggregate count collection inventory catalog total current have own added removed",
        extraction_patterns=(),
        extra_metadata={
            "aggregate_group": "collection_total",
            "temporal_slot": "current",
        },
        answer_mode="aggregate_count",
        object_kind="entity",
    ),
    "event.collection.item_added": CoveredFactSpec(
        fact_key="event.collection.item_added",
        title="Collection item added",
        fact_kind="event",
        keywords="collection inventory catalog added new item acquired",
        extraction_patterns=(),
        extra_metadata={
            "event_type": "collection_item_added",
        },
        answer_mode="collection_update",
        object_kind="event",
    ),
    "event.reading.completed": CoveredFactSpec(
        fact_key="event.reading.completed",
        title="Completed reading event",
        fact_kind="event",
        keywords="event completed reading book finish finished reading timeline",
        extraction_patterns=(),
        extra_metadata={
            "event_type": "reading_completed",
        },
        answer_mode="temporal_elapsed",
        object_kind="event",
    ),
    "event.library.book_reading.attended": CoveredFactSpec(
        fact_key="event.library.book_reading.attended",
        title="Library reading event attendance",
        fact_kind="event",
        keywords="event attended local library reading author discussion thriller",
        extraction_patterns=(),
        extra_metadata={
            "event_type": "library_reading_attended",
        },
        answer_mode="temporal_elapsed",
        object_kind="event",
    ),
    "event.trip.recent": CoveredFactSpec(
        fact_key="event.trip.recent",
        title="Recent trip event",
        fact_kind="event",
        keywords="event trip travel hike camping road trip recent timeline order earliest latest",
        extraction_patterns=(),
        extra_metadata={
            "event_type": "recent_trip",
        },
        answer_mode="trip_order",
        object_kind="event",
    ),
}


def iter_covered_fact_specs() -> Iterable[CoveredFactSpec]:
    return COVERED_FACT_SPECS.values()


def get_covered_fact_spec(fact_key: str) -> CoveredFactSpec | None:
    return COVERED_FACT_SPECS.get(str(fact_key or "").strip().lower())


def normalize_query_text(query: str) -> str:
    return f" {re.sub(r'[^a-z0-9]+', ' ', str(query or '').strip().lower())} "


def _has_any(normalized_query: str, markers: tuple[str, ...]) -> bool:
    return any(marker in normalized_query for marker in markers)


def match_query_to_fact_keys(query: str) -> List[str]:
    normalized_query = normalize_query_text(query)

    if _has_any(normalized_query, _TEMPORAL_ELAPSED_QUERY_MARKERS):
        return [
            "event.reading.completed",
            "event.library.book_reading.attended",
        ]
    if _has_any(normalized_query, _TRIP_QUERY_MARKERS) and _has_any(
        normalized_query, _ORDER_QUERY_MARKERS
    ):
        return ["event.trip.recent"]
    if " how many " in normalized_query and _has_any(
        normalized_query, _COLLECTION_QUERY_MARKERS
    ):
        return ["aggregate.collection.total.current"]
    if " evening " in normalized_query and _has_any(
        normalized_query, _EVENING_ACTIVITY_QUERY_MARKERS
    ):
        return [
            "preference.evening.activities.current",
            "preference.evening.screen_avoid.current",
        ]
    if _has_any(normalized_query, _FOOD_DELIVERY_QUERY_MARKERS) or (
        " how many " in normalized_query and " delivery " in normalized_query
    ):
        return ["aggregate.food_delivery_service.recent"]
    if _has_any(normalized_query, _TIMEZONE_QUERY_MARKERS):
        return ["attribute.timezone.current"]
    if _has_any(normalized_query, _RESIDENCE_QUERY_MARKERS) and not _has_any(
        normalized_query, _TEAM_QUERY_MARKERS + _MANAGER_QUERY_MARKERS
    ):
        return ["attribute.residence.current"]
    if _has_any(normalized_query, _MANAGER_QUERY_MARKERS):
        return ["relation.manager.current"]
    if _has_any(normalized_query, _TEAM_QUERY_MARKERS):
        return ["relation.team.current"]
    if _has_any(normalized_query, _OCCUPATION_QUERY_MARKERS):
        if _has_any(normalized_query, _PREVIOUS_QUERY_MARKERS):
            return ["attribute.occupation.previous"]
        return ["attribute.occupation.current"]
    return []


def match_query_to_fact_key(query: str) -> str | None:
    keys = match_query_to_fact_keys(query)
    return keys[0] if keys else None
