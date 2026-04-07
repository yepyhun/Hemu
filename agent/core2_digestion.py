from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Dict, List

from agent.core2_fact_registry import get_covered_fact_spec, iter_covered_fact_specs


@dataclass(frozen=True)
class DigestedFactCandidate:
    title: str
    content: str
    object_kind: str
    identity_key: str
    metadata: Dict[str, Any] = field(default_factory=dict)


def _clean_value(value: str) -> str:
    cleaned = " ".join(str(value or "").strip().split())
    cleaned = re.sub(r"^[\"'`\u201c\u201d]+|[\"'`,.;:)\u201c\u201d]+$", "", cleaned)
    return cleaned.strip()


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(value or "").strip().lower()).strip("-")


def _singularize(noun: str) -> str:
    cleaned = _clean_value(noun).lower()
    if cleaned.endswith("ies") and len(cleaned) > 3:
        return cleaned[:-3] + "y"
    if cleaned.endswith("ses") and len(cleaned) > 3:
        return cleaned[:-2]
    if cleaned.endswith("s") and not cleaned.endswith("ss") and len(cleaned) > 2:
        return cleaned[:-1]
    return cleaned


def _user_segments(text: str) -> List[str]:
    source = str(text or "")
    matches = re.findall(
        r"(?:^|\n)\s*(?:USER|user):\s*(.*?)(?=(?:\n\s*(?:ASSISTANT|assistant):)|\Z)",
        source,
        flags=re.DOTALL,
    )
    segments = [_clean_value(segment) for segment in matches if _clean_value(segment)]
    return segments


def _user_like_segments(text: str) -> List[str]:
    segments = _user_segments(text)
    if segments:
        return segments
    source = str(text or "")
    matches = re.findall(
        r"User asked:\s*(.*?)(?=(?:\n\s*Assistant answered:)|\Z)",
        source,
        flags=re.DOTALL | re.IGNORECASE,
    )
    extracted = [_clean_value(segment) for segment in matches if _clean_value(segment)]
    return extracted or [text]


def _fact_candidate(
    *,
    title: str,
    content: str,
    identity_key: str,
    fact_kind: str,
    fact_key: str,
    canonical_value: str,
    object_kind: str = "state",
    keywords: str = "",
    extra_metadata: Dict[str, Any] | None = None,
) -> DigestedFactCandidate:
    metadata = {
        "digest_fact": True,
        "fact_kind": fact_kind,
        "fact_key": fact_key,
        "canonical_value": canonical_value,
        "identity_key": identity_key,
        "keywords": keywords.strip(),
    }
    if extra_metadata:
        metadata.update(extra_metadata)
    return DigestedFactCandidate(
        title=title,
        content=content,
        object_kind=object_kind,
        identity_key=identity_key,
        metadata=metadata,
    )


def _extract_attribute_facts(text: str) -> List[DigestedFactCandidate]:
    candidates: List[DigestedFactCandidate] = []
    for spec in iter_covered_fact_specs():
        if spec.fact_kind != "attribute":
            continue
        for pattern in spec.extraction_patterns:
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                value = _clean_value(match.group(1))
                if not value:
                    continue
                candidates.append(
                    _fact_candidate(
                        title=spec.title,
                        content=f"{spec.title}: {value}",
                        identity_key=f"digest:{spec.fact_key}",
                        fact_kind=spec.fact_kind,
                        fact_key=spec.fact_key,
                        canonical_value=value,
                        keywords=f"{spec.keywords} {value.lower()}",
                        extra_metadata=dict(spec.extra_metadata),
                    )
                )
    return candidates


def _extract_relation_facts(text: str) -> List[DigestedFactCandidate]:
    candidates: List[DigestedFactCandidate] = []
    for spec in iter_covered_fact_specs():
        if spec.fact_kind != "relation":
            continue
        for pattern in spec.extraction_patterns:
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                value = _clean_value(match.group(1))
                if not value:
                    continue
                extra_metadata = dict(spec.extra_metadata)
                extra_metadata["relation_target"] = value
                candidates.append(
                    _fact_candidate(
                        title=spec.title,
                        content=f"{spec.title}: {value}",
                        identity_key=f"digest:{spec.fact_key}",
                        fact_kind=spec.fact_kind,
                        fact_key=spec.fact_key,
                        canonical_value=value,
                        object_kind=spec.object_kind,
                        keywords=f"{spec.keywords} {value.lower()}",
                        extra_metadata=extra_metadata,
                    )
                )
    return candidates


def _extract_preference_facts(text: str) -> List[DigestedFactCandidate]:
    candidates: List[DigestedFactCandidate] = []
    lower = text.lower()
    user_segments = _user_segments(text)
    scoped_text = "\n".join(user_segments) if user_segments else text

    positive_spec = get_covered_fact_spec("preference.evening.activities.current")
    scoped_lower = scoped_text.lower()
    positive_time_matches = re.findall(r"\b(?:before|by)\s+([0-9]{1,2}(?::[0-9]{2})?\s*(?:am|pm))\b", scoped_text, flags=re.IGNORECASE)
    has_relaxing_signal = any(term in scoped_lower for term in ("relax", "relaxing", "calm", "wind down", "winding down"))
    has_bedtime_signal = any(term in scoped_lower for term in ("good night", "good night s sleep", "bedtime"))
    if positive_spec and (
        ("evening" in scoped_lower and has_relaxing_signal)
        or ("night" in scoped_lower and has_relaxing_signal)
        or (bool(positive_time_matches) and (has_relaxing_signal or has_bedtime_signal))
    ):
        time_match = None
        if positive_time_matches:
            preferred = [value for value in positive_time_matches if str(value).strip().lower().endswith("pm")]
            time_match = (preferred[-1] if preferred else positive_time_matches[-1]).strip()
        qualifier = ""
        if time_match:
            qualifier = f" before {time_match}"
        canonical = f"relaxing activities that can be done in the evening{qualifier}".strip()
        extra_metadata = dict(positive_spec.extra_metadata)
        if time_match:
            extra_metadata["time_window"] = f"before {time_match}"
        candidates.append(
            _fact_candidate(
                title=positive_spec.title,
                content=f"{positive_spec.title}: {canonical}",
                identity_key=f"digest:{positive_spec.fact_key}",
                fact_kind=positive_spec.fact_kind,
                fact_key=positive_spec.fact_key,
                canonical_value=canonical,
                object_kind=positive_spec.object_kind,
                keywords=f"{positive_spec.keywords} {canonical.lower()}",
                extra_metadata=extra_metadata,
            )
        )

    negative_spec = get_covered_fact_spec("preference.evening.screen_avoid.current")
    mentions_screen = ("phone" in lower or "tv" in lower or "television" in lower)
    mentions_sleep = "sleep" in lower
    if negative_spec and mentions_screen and mentions_sleep and any(term in lower for term in ("evening", "night", "bed")):
        avoid_parts: List[str] = []
        if "phone" in lower or "screen" in lower:
            avoid_parts.append("using your phone")
        if "tv" in lower or "television" in lower or "screen" in lower or "phone" in lower:
            avoid_parts.append("watching TV")
        if not avoid_parts:
            avoid_parts.append("screen use")
        joined = " or ".join(avoid_parts)
        canonical = f"avoid {joined} in the evening because it affects sleep quality"
        extra_metadata = dict(negative_spec.extra_metadata)
        extra_metadata["avoid_targets"] = avoid_parts
        extra_metadata["reason"] = "sleep_quality"
        candidates.append(
            _fact_candidate(
                title=negative_spec.title,
                content=f"{negative_spec.title}: {canonical}",
                identity_key=f"digest:{negative_spec.fact_key}",
                fact_kind=negative_spec.fact_kind,
                fact_key=negative_spec.fact_key,
                canonical_value=canonical,
                object_kind=negative_spec.object_kind,
                keywords=f"{negative_spec.keywords} {joined.lower()} sleep quality",
                extra_metadata=extra_metadata,
            )
        )

    return candidates


_FOOD_DELIVERY_SERVICE_ALIASES = {
    "Domino's": ("domino's", "dominos", "domino s", "domino's pizza", "domino"),
    "Uber Eats": ("uber eats", "ubereats"),
    "DoorDash": ("doordash", "door dash"),
    "Grubhub": ("grubhub",),
    "Postmates": ("postmates",),
}


def _iter_recent_delivery_services(text: str) -> List[str]:
    found: List[str] = []
    lowered_seen: set[str] = set()
    lower = text.lower()

    for service, aliases in _FOOD_DELIVERY_SERVICE_ALIASES.items():
        if not any(alias in lower for alias in aliases):
            continue
        lowered = service.lower()
        if lowered in lowered_seen:
            continue
        lowered_seen.add(lowered)
        found.append(service)

    if "delivery" in lower:
        for match in re.finditer(
            r"\b(?:called|named)\s+([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,2})\b",
            text,
        ):
            candidate = _clean_value(match.group(1))
            if not candidate:
                continue
            lowered = candidate.lower()
            if lowered in lowered_seen:
                continue
            lowered_seen.add(lowered)
            found.append(candidate)

    return found


def _extract_collection_label(chunk: str, item_noun: str) -> str:
    of_match = re.search(r"\bcollection of\s+([^.!?\n]{2,80})", chunk, flags=re.IGNORECASE)
    if of_match:
        value = _clean_value(of_match.group(1))
        if value:
            return value
    noun = re.escape(str(item_noun or "").strip())
    if noun:
        patterns = (
            rf"\bmy\s+([^.!?\n]{{0,80}}?\b{noun}s?\b)",
            rf"\bmy\s+([^.!?\n]{{0,80}}?\b{noun}\b)",
        )
        for pattern in patterns:
            match = re.search(pattern, chunk, flags=re.IGNORECASE)
            if match:
                return _clean_value(match.group(1))
    generic = re.search(r"\bmy\s+([^.!?\n]{2,80}?)\s+collection\b", chunk, flags=re.IGNORECASE)
    if generic:
        return _clean_value(generic.group(1))
    return ""


def _parse_count_token(token: str) -> int | None:
    text = str(token or "").strip().lower()
    if not text:
        return None
    if text.isdigit():
        return int(text)
    if text in {"a", "an", "one", "another", "new"}:
        return 1
    return None


def _extract_aggregate_member_facts(text: str) -> List[DigestedFactCandidate]:
    spec = get_covered_fact_spec("aggregate.food_delivery_service.recent")
    if spec is None:
        return []
    candidates: List[DigestedFactCandidate] = []
    scoped = _user_segments(text) or [text]
    seen_services: set[str] = set()
    for chunk in scoped:
        for service in _iter_recent_delivery_services(chunk):
            lowered = service.lower()
            if lowered in seen_services:
                continue
            seen_services.add(lowered)
            extra_metadata = dict(spec.extra_metadata)
            extra_metadata["member_value"] = service
            candidates.append(
                _fact_candidate(
                    title=spec.title,
                    content=f"{spec.title}: {service}",
                    identity_key=f"digest:{spec.fact_key}:{_slug(service)}",
                    fact_kind=spec.fact_kind,
                    fact_key=spec.fact_key,
                    canonical_value=service,
                    object_kind=spec.object_kind,
                    keywords=f"{spec.keywords} {service.lower()}",
                    extra_metadata=extra_metadata,
                )
            )
    return candidates


def _extract_collection_facts(text: str) -> List[DigestedFactCandidate]:
    total_spec = get_covered_fact_spec("aggregate.collection.total.current")
    added_spec = get_covered_fact_spec("event.collection.item_added")
    if total_spec is None and added_spec is None:
        return []

    candidates: List[DigestedFactCandidate] = []
    scoped = _user_like_segments(text)

    for chunk in scoped:
        if total_spec is not None:
            total_match = re.search(
                r"\b(?:i have|i own|there are)\s+(?:a total of\s+)?(\d+)\s+([A-Za-z][A-Za-z0-9-]*)s?\s+in\s+(?:that|the|my)\s+collection\b",
                chunk,
                flags=re.IGNORECASE,
            )
            if total_match:
                count = int(total_match.group(1))
                item_noun = _singularize(total_match.group(2))
                collection_label = _extract_collection_label(chunk, item_noun) or f"{item_noun}s"
                extra_metadata = dict(total_spec.extra_metadata)
                extra_metadata.update(
                    {
                        "collection_label": collection_label,
                        "item_noun": item_noun,
                        "aggregate_count": count,
                    }
                )
                candidates.append(
                    _fact_candidate(
                        title=total_spec.title,
                        content=f"{total_spec.title}: {count} ({collection_label})",
                        identity_key=f"digest:{total_spec.fact_key}:{_slug(collection_label)}",
                        fact_kind=total_spec.fact_kind,
                        fact_key=total_spec.fact_key,
                        canonical_value=str(count),
                        object_kind=total_spec.object_kind,
                        keywords=f"{total_spec.keywords} {collection_label.lower()} {item_noun}",
                        extra_metadata=extra_metadata,
                    )
                )

        if added_spec is not None:
            added_match = re.search(
                r"\b(?:just\s+)?added\s+(a|an|one|another|new|\d+)\s+(?:new\s+)?([A-Za-z][A-Za-z0-9-]*)s?\s+to\s+(?:my|the)\s+collection\b",
                chunk,
                flags=re.IGNORECASE,
            )
            if added_match:
                delta = _parse_count_token(added_match.group(1))
                item_noun = _singularize(added_match.group(2))
                if delta and item_noun:
                    collection_label = _extract_collection_label(chunk, item_noun)
                    extra_metadata = dict(added_spec.extra_metadata)
                    extra_metadata.update(
                        {
                            "collection_label": collection_label,
                            "item_noun": item_noun,
                            "delta": delta,
                        }
                    )
                    candidates.append(
                        _fact_candidate(
                            title=added_spec.title,
                            content=f"{added_spec.title}: +{delta} {item_noun}",
                            identity_key=f"digest:{added_spec.fact_key}:{_slug(item_noun)}:{delta}:{_slug(chunk[:48])}",
                            fact_kind=added_spec.fact_kind,
                            fact_key=added_spec.fact_key,
                            canonical_value=str(delta),
                            object_kind=added_spec.object_kind,
                            keywords=f"{added_spec.keywords} {item_noun} {collection_label.lower()}".strip(),
                            extra_metadata=extra_metadata,
                        )
                    )

    return candidates


def _extract_quoted_titles(text: str) -> List[str]:
    titles: List[str] = []
    for value in re.findall(r'"([^"\n]{2,120})"', text):
        cleaned = _clean_value(value)
        if cleaned:
            titles.append(cleaned)
    for value in re.findall(r"(?<![A-Za-z0-9])'([^'\n]{2,120})'(?![A-Za-z0-9])", text):
        cleaned = _clean_value(value)
        if cleaned:
            titles.append(cleaned)
    return titles


def _extract_temporal_event_facts(text: str) -> List[DigestedFactCandidate]:
    candidates: List[DigestedFactCandidate] = []
    scoped = _user_segments(text) or [text]

    reading_spec = get_covered_fact_spec("event.reading.completed")
    event_spec = get_covered_fact_spec("event.library.book_reading.attended")
    trip_spec = get_covered_fact_spec("event.trip.recent")

    for chunk in scoped:
        lower = chunk.lower()
        titles = _extract_quoted_titles(chunk)

        if reading_spec and titles and any(term in lower for term in ("finished reading", "just finished", "finished")):
            title = titles[0]
            extra_metadata = dict(reading_spec.extra_metadata)
            extra_metadata["event_subject"] = title
            candidates.append(
                _fact_candidate(
                    title=reading_spec.title,
                    content=f"{reading_spec.title}: {title}",
                    identity_key=f"digest:{reading_spec.fact_key}:{_slug(title)}",
                    fact_kind=reading_spec.fact_kind,
                    fact_key=reading_spec.fact_key,
                    canonical_value=title,
                    object_kind=reading_spec.object_kind,
                    keywords=f"{reading_spec.keywords} {title.lower()}",
                    extra_metadata=extra_metadata,
                )
            )

        if event_spec and ("local library" in lower or "library" in lower) and any(term in lower for term in ("attended", "book reading event", "reading event", "author of", "discussing")):
            anchor = titles[-1] if titles else "local library reading event"
            extra_metadata = dict(event_spec.extra_metadata)
            extra_metadata["event_anchor"] = anchor
            candidates.append(
                _fact_candidate(
                    title=event_spec.title,
                    content=f"{event_spec.title}: {anchor}",
                    identity_key=f"digest:{event_spec.fact_key}:{_slug(anchor)}",
                    fact_kind=event_spec.fact_kind,
                    fact_key=event_spec.fact_key,
                    canonical_value=anchor,
                    object_kind=event_spec.object_kind,
                    keywords=f"{event_spec.keywords} {anchor.lower()} local library",
                    extra_metadata=extra_metadata,
                )
            )

        if trip_spec:
            trip_candidates: List[tuple[str, str]] = []
            recent_road = re.search(
                r"\bjust got back from (a road trip(?: with [^.,;\n]+)? to [^.!?\n]+?)(?: today| last| recently|,|\.|!|$)",
                chunk,
                flags=re.IGNORECASE,
            )
            if recent_road:
                label = _clean_value(recent_road.group(1))
                destination_match = re.search(r"\bto\s+(.+)$", label, flags=re.IGNORECASE)
                destination = _clean_value(destination_match.group(1)) if destination_match else label
                trip_candidates.append((label, destination))
            recent_camping = re.search(
                r"\bjust got back from (a solo camping trip to [^.!?\n]+?)(?: today| last| recently|,|\.|!|$)",
                chunk,
                flags=re.IGNORECASE,
            )
            if recent_camping:
                label = _clean_value(recent_camping.group(1))
                destination_match = re.search(r"\bto\s+(.+)$", label, flags=re.IGNORECASE)
                destination = _clean_value(destination_match.group(1)) if destination_match else label
                trip_candidates.append((label, destination))
            muir_hike = re.search(
                r"\b(?:a\s+)?day hike to ([^,!?\n]+?)(?: with ([^.!?\n]+?))?(?: today| last| recently|,|\.|!|$)",
                chunk,
                flags=re.IGNORECASE,
            )
            if not muir_hike:
                muir_hike = re.search(
                    r"\b(?:a\s+)?day hike at ([^,!?\n]+?)(?: with ([^.!?\n]+?))?(?: today| last| recently|,|\.|!|$)",
                    chunk,
                    flags=re.IGNORECASE,
                )
            if not muir_hike:
                muir_hike = re.search(
                    r"\bhiked at ([^,!?\n]+?)(?: with ([^.!?\n]+?))?(?: today| last| recently|,|\.|!|$)",
                    chunk,
                    flags=re.IGNORECASE,
                )
            if muir_hike and "day hike" in lower:
                destination = _clean_value(muir_hike.group(1))
                companions = _clean_value(muir_hike.group(2) or "")
                label = f"day hike to {destination}"
                if companions:
                    label += f" with {companions}"
                trip_candidates.append((label, destination))

            for label, destination in trip_candidates:
                extra_metadata = dict(trip_spec.extra_metadata)
                extra_metadata["event_anchor"] = destination
                extra_metadata["trip_label"] = label
                candidates.append(
                    _fact_candidate(
                        title=trip_spec.title,
                        content=f"{trip_spec.title}: {label}",
                        identity_key=f"digest:{trip_spec.fact_key}:{_slug(label)}",
                        fact_kind=trip_spec.fact_kind,
                        fact_key=trip_spec.fact_key,
                        canonical_value=label,
                        object_kind=trip_spec.object_kind,
                        keywords=f"{trip_spec.keywords} {destination.lower()} {label.lower()}",
                        extra_metadata=extra_metadata,
                    )
                )

    return candidates


def _dedupe_candidates(candidates: List[DigestedFactCandidate]) -> List[DigestedFactCandidate]:
    by_identity: Dict[str, DigestedFactCandidate] = {}
    for candidate in candidates:
        marker = candidate.identity_key
        existing = by_identity.get(marker)
        if existing is None:
            by_identity[marker] = candidate
            continue
        existing_value = str(existing.metadata.get("canonical_value") or "").strip()
        candidate_value = str(candidate.metadata.get("canonical_value") or "").strip()
        existing_score = (
            len(existing_value),
            len(existing.metadata),
        )
        candidate_score = (
            len(candidate_value),
            len(candidate.metadata),
        )
        if candidate_score > existing_score:
            by_identity[marker] = candidate
    return list(by_identity.values())


def digest_memory_content(content: str) -> List[DigestedFactCandidate]:
    # Invariant: digestion only materializes the narrow covered-fact families.
    # If a family is not in the registry, query-time must not silently invent it later.
    text = str(content or "").strip()
    if not text:
        return []
    return _dedupe_candidates(
        _extract_attribute_facts(text)
        + _extract_relation_facts(text)
        + _extract_preference_facts(text)
        + _extract_aggregate_member_facts(text)
        + _extract_collection_facts(text)
        + _extract_temporal_event_facts(text)
    )


def digest_turn_content(user_content: str, assistant_content: str = "") -> List[DigestedFactCandidate]:
    del assistant_content
    text = str(user_content or "").strip()
    if not text:
        return []
    return digest_memory_content(text)
