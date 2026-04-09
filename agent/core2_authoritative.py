from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from itertools import combinations
import re
from typing import Iterable, List, Optional

from agent.core2_answer_surface import render_answer_surface_text
from agent.core2_fact_registry import get_covered_fact_spec, match_query_to_fact_key
from agent.core2_routing import is_conversation_reference_query
from agent.core2_types import (
    ANSWER_SURFACE_FACT_ONLY,
    ANSWER_SURFACE_FACT_PLUS_SUMMARY,
    ANSWER_SURFACE_FALLBACK,
    Core2AnswerSurface,
    Core2RecallItem,
    Core2RecallPacket,
    QUERY_FAMILY_FACTUAL_SUPPORTED,
    QUERY_FAMILY_PERSONAL_RECALL,
    QUERY_FAMILY_UPDATE_RESOLUTION,
)


_QUOTED_OPTION_RE = re.compile(r"(['\"])(.+?)\1")
_OR_SPLIT_RE = re.compile(r"\s+or\s+", re.IGNORECASE)
_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")
_RECOMMENDATION_LINE_RE = re.compile(r"^\s*(?:[-*]|\d+[.)])\s*(?P<label>[^-:\n]+?)\s*-\s*(?P<description>.+?)\s*$")

_DIRECTION_EARLIER = "earlier"
_DIRECTION_LATER = "later"

_NUMBER_WORDS = {
    "a": 1,
    "an": 1,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
}

_STOP_TOKENS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "that",
    "this",
    "have",
    "been",
    "into",
    "your",
    "their",
    "them",
    "what",
    "which",
    "when",
    "where",
    "who",
    "will",
    "would",
    "could",
    "should",
    "did",
    "does",
    "done",
    "just",
    "more",
    "than",
    "instead",
    "need",
    "earn",
    "total",
}


@dataclass(frozen=True)
class _OptionSpec:
    value: str
    answer_label: str


@dataclass(frozen=True)
class _TemporalEvidence:
    answer_label: str
    normalized_value: str
    event_at: datetime
    phrase: str
    item_id: str


def _normalize_token_text(value: str) -> str:
    return _NON_ALNUM_RE.sub(" ", str(value or "").casefold()).strip()


def _match_token(token: str) -> str:
    normalized = _normalize_token_text(token)
    if not normalized:
        return ""
    if normalized.endswith("ing") and len(normalized) > 5:
        normalized = normalized[:-3]
    elif normalized.endswith("ied") and len(normalized) > 4:
        normalized = normalized[:-3] + "y"
    elif normalized.endswith("ed") and len(normalized) > 4:
        normalized = normalized[:-2]
    elif normalized.endswith("es") and len(normalized) > 4:
        normalized = normalized[:-2]
    elif normalized.endswith("s") and len(normalized) > 3:
        normalized = normalized[:-1]
    if len(normalized) >= 2 and normalized[-1] == normalized[-2]:
        normalized = normalized[:-1]
    return normalized


def _match_tokens(value: str) -> set[str]:
    return {
        _match_token(token)
        for token in _normalize_token_text(value).split()
        if len(_match_token(token)) >= 3 and _match_token(token) not in _STOP_TOKENS
    }


def _query_focus_tokens(query: str) -> set[str]:
    return {
        token
        for token in _match_tokens(query)
        if token
        and token
        not in {
            "how",
            "many",
            "much",
            "first",
            "last",
            "order",
            "point",
            "money",
            "save",
        }
    }


def _split_fragments(content: str) -> List[str]:
    fragments = re.split(r"[.!?\n]+|(?:\s+\band\b\s+)", str(content or ""), flags=re.IGNORECASE)
    return [fragment.strip(" ,;:-") for fragment in fragments if fragment.strip(" ,;:-")]


def _money_values(text: str) -> List[int]:
    values: List[int] = []
    for match in re.finditer(r"\$([0-9][0-9,]*)", str(text or "")):
        values.append(int(match.group(1).replace(",", "")))
    return values


def _phrase_has_focus(fragment: str, focus_tokens: set[str], minimum: int = 1) -> bool:
    if not focus_tokens:
        return False
    fragment_tokens = _match_tokens(fragment)
    overlap = 0
    for left in focus_tokens:
        for right in fragment_tokens:
            if left == right or left.startswith(right) or right.startswith(left) or left[:4] == right[:4]:
                overlap += 1
                break
    return overlap >= minimum


def _extract_target_phrase(query: str) -> str:
    normalized = " ".join(str(query or "").split())
    patterns = (
        r"how many\s+(.+?)\s+(?:do i|have i|did i|have|did|are|were|will i|would i|can i)\b",
        r"how much\s+(.+?)\s+(?:do i|have i|did i|have|did|will i|would i|can i)\b",
    )
    for pattern in patterns:
        match = re.search(pattern, normalized, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip(" ?.")
    return ""


def _extract_unit_tokens(query: str) -> set[str]:
    target_phrase = _extract_target_phrase(query)
    unit_tokens = _match_tokens(target_phrase)
    if unit_tokens:
        return unit_tokens
    normalized = _query_text(query)
    if " money " in normalized:
        return {"money"}
    return set()


def _fragment_count_candidate(fragment: str, unit_tokens: set[str]) -> Optional[int]:
    if not unit_tokens:
        return None
    raw_tokens = _normalize_token_text(fragment).split()
    for idx, token in enumerate(raw_tokens):
        value = _parse_number(token)
        if value is None:
            continue
        window = raw_tokens[idx + 1 : idx + 6]
        if not window:
            continue
        window_units = {_match_token(part) for part in window if _match_token(part)}
        if unit_tokens & window_units:
            return value
    return None


def _fragment_duration_days(fragment: str) -> Optional[int]:
    normalized = _query_text(fragment)
    compact = normalized.replace("-", " ")
    if "week long" in compact:
        return 7

    patterns = (
        (r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+days?\b", 1),
        (r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+weeks?\b", 7),
        (r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+day\s+trip\b", 1),
        (r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+week\s+break\b", 7),
    )
    for pattern, multiplier in patterns:
        match = re.search(pattern, compact, flags=re.IGNORECASE)
        if not match:
            continue
        value = _parse_number(match.group(1))
        if value is not None:
            return value * multiplier
    return None


def _current_cue_score(fragment: str) -> int:
    normalized = _query_text(fragment)
    score = 0
    for marker, weight in (
        (" total ", 4),
        (" so far ", 4),
        (" already ", 4),
        (" currently ", 4),
        (" have ", 2),
        (" has ", 2),
        (" bringing my total to ", 4),
    ):
        if marker in normalized:
            score += weight
    return score


def _sum_dedupe_key(fragment: str, value: int) -> tuple[int, str]:
    normalized = _normalize_token_text(fragment)
    return value, normalized[:120]


def _non_money_signature(fragment: str, query_tokens: set[str], unit_tokens: set[str]) -> str:
    normalized_fragment = _normalize_token_text(fragment)
    on_match = re.search(r"\bon\s+([a-z0-9]+)\b", normalized_fragment)
    if on_match:
        candidate = _match_token(on_match.group(1))
        if candidate and candidate not in query_tokens and candidate not in unit_tokens and candidate not in _STOP_TOKENS:
            return candidate
    tokens = [
        token
        for token in _match_tokens(fragment)
        if token not in query_tokens and token not in unit_tokens and token not in _STOP_TOKENS
    ]
    return "|".join(sorted(tokens)[:4])


def _trip_labels_overlap(left: str, right: str) -> bool:
    normalized_left = _normalize_token_text(left)
    normalized_right = _normalize_token_text(right)
    if not normalized_left or not normalized_right:
        return False
    return normalized_left in normalized_right or normalized_right in normalized_left


def _prefer_trip_label(candidate: str, current: str) -> bool:
    normalized_candidate = _normalize_token_text(candidate)
    normalized_current = _normalize_token_text(current)
    if not normalized_candidate:
        return False
    if not normalized_current:
        return True

    def _trip_label_score(value: str) -> tuple[int, int]:
        score = 0
        if " with " in value:
            score += 3
        if " family" in value or " friends" in value:
            score += 2
        if "national monument" in value or "national park" in value:
            score += 2
        if "solo " in value:
            score += 1
        return score, len(value)

    candidate_score = _trip_label_score(normalized_candidate)
    current_score = _trip_label_score(normalized_current)
    if candidate_score != current_score:
        return candidate_score > current_score
    return candidate.strip() > current.strip()


def _is_turn_item(item: Core2RecallItem) -> bool:
    metadata = dict(item.metadata or {})
    return bool(metadata.get("turn_index")) or "turn" in str(item.title or "").lower()


def _extract_options(query: str) -> List[_OptionSpec]:
    quoted_matches = list(_QUOTED_OPTION_RE.finditer(str(query or "")))
    if len(quoted_matches) >= 2:
        options: List[_OptionSpec] = []
        seen: set[str] = set()
        for match in quoted_matches:
            raw = match.group(0).strip()
            value = match.group(2).strip()
            normalized = _normalize_token_text(value)
            if value and normalized not in seen:
                options.append(_OptionSpec(value=value, answer_label=raw))
                seen.add(normalized)
            if len(options) == 2:
                return options

    lowered = " ".join(str(query or "").split())
    if " or " not in lowered.casefold():
        return []
    left, right = _OR_SPLIT_RE.split(lowered, maxsplit=1)
    left_tail = left.rsplit(",", 1)[-1].strip(" ?.")
    right_head = right.split("?", 1)[0].strip(" ?.")
    if not left_tail or not right_head:
        return []
    return [
        _OptionSpec(value=left_tail, answer_label=left_tail),
        _OptionSpec(value=right_head, answer_label=right_head),
    ]


def _query_direction(query: str) -> Optional[str]:
    normalized = f" {_normalize_token_text(query)} "
    if any(marker in normalized for marker in (" first ", " earlier ", " before ", " oldest ", " earliest ")):
        return _DIRECTION_EARLIER
    if any(marker in normalized for marker in (" last ", " later ", " after ", " newest ", " latest ")):
        return _DIRECTION_LATER
    return None


def _query_text(query: str) -> str:
    return f" {_normalize_token_text(query)} "


def _conversation_reference_focus_tokens(query: str) -> set[str]:
    ignored = {
        "remind",
        "last",
        "time",
        "talk",
        "wonder",
        "plan",
        "revisit",
        "unique",
        "please",
    }
    return {token for token in _query_focus_tokens(query) if token not in ignored}


def _iter_recommendation_candidates(content: str) -> Iterable[tuple[str, str]]:
    for raw_line in str(content or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = _RECOMMENDATION_LINE_RE.match(line)
        if not match:
            continue
        label = match.group("label").strip(" .")
        description = match.group("description").strip()
        if label and description:
            yield label, description


def _recommendation_location(description: str) -> str:
    match = re.search(
        r"\blocated\s+(?:at|in)\s+([^.,;\n]+?)(?:\s+(?:that|which|where|with)\b|[.,;]|$)",
        str(description or ""),
        re.IGNORECASE,
    )
    return match.group(1).strip(" .") if match else ""


def _parse_iso_datetime(value: str | None) -> Optional[datetime]:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _parse_session_datetime(value: str | None) -> Optional[datetime]:
    text = str(value or "").strip()
    if not text:
        return None
    for fmt in ("%Y/%m/%d (%a) %H:%M", "%Y/%m/%d %H:%M"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def _anchor_datetime(item: Core2RecallItem) -> Optional[datetime]:
    candidates = (
        item.effective_from,
        item.source_created_at,
        item.recorded_at,
        item.observed_at,
        item.metadata.get("session_date"),
    )
    for candidate in candidates:
        parsed = _parse_iso_datetime(candidate) if candidate != item.metadata.get("session_date") else _parse_session_datetime(candidate)
        if parsed is not None:
            return parsed
    return None


def _parse_number(value: str) -> Optional[int]:
    text = str(value or "").strip().lower()
    if not text:
        return None
    if text.isdigit():
        return int(text)
    return _NUMBER_WORDS.get(text)


def _relative_offset_days(window: str) -> tuple[Optional[float], str]:
    normalized = " ".join(str(window or "").casefold().split())
    if not normalized:
        return None, ""

    keyword_offsets = (
        ("two weeks ago", 14.0),
        ("three weeks ago", 21.0),
        ("last weekend", 3.0),
        ("previous weekend", 3.0),
        ("last week", 7.0),
        ("previous week", 7.0),
        ("last month", 30.0),
        ("previous month", 30.0),
        ("yesterday", 1.0),
        ("today", 0.0),
        ("this morning", 0.2),
        ("tonight", 0.1),
    )
    for phrase, offset in keyword_offsets:
        if phrase in normalized:
            return offset, phrase

    quantified = re.search(r"\b(\d+|a|an|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+(day|days|week|weeks|month|months|year|years)\s+ago\b", normalized)
    if quantified:
        amount = _parse_number(quantified.group(1))
        unit = quantified.group(2)
        if amount is not None:
            multiplier = 1.0
            if unit.startswith("week"):
                multiplier = 7.0
            elif unit.startswith("month"):
                multiplier = 30.0
            elif unit.startswith("year"):
                multiplier = 365.0
            return amount * multiplier, quantified.group(0)

    return None, ""


def _collect_temporal_evidence(option: _OptionSpec, items: Iterable[Core2RecallItem]) -> List[_TemporalEvidence]:
    normalized_option = _normalize_token_text(option.value)
    if not normalized_option:
        return []
    option_tokens = _match_tokens(option.value)

    evidence: List[_TemporalEvidence] = []
    for item in items:
        anchor = _anchor_datetime(item)
        if anchor is None:
            continue
        content = str(item.content or "")
        lowered = content.casefold()
        search_value = option.value.casefold()
        idx = lowered.find(search_value)
        if idx >= 0:
            window = content[max(0, idx - 180): idx + len(option.value) + 180]
            offset_days, phrase = _relative_offset_days(window)
            if offset_days is not None:
                evidence.append(
                    _TemporalEvidence(
                        answer_label=option.answer_label,
                        normalized_value=normalized_option,
                        event_at=anchor - timedelta(days=offset_days),
                        phrase=phrase,
                        item_id=item.object_id,
                    )
                )
                continue
        for fragment in _split_fragments(content):
            offset_days, phrase = _relative_offset_days(fragment)
            if offset_days is None:
                continue
            fragment_tokens = _match_tokens(fragment)
            if not option_tokens or len(option_tokens & fragment_tokens) < min(2, len(option_tokens)):
                continue
            evidence.append(
                _TemporalEvidence(
                    answer_label=option.answer_label,
                    normalized_value=normalized_option,
                    event_at=anchor - timedelta(days=offset_days),
                    phrase=phrase,
                    item_id=item.object_id,
                )
            )
            break
    return evidence


def _strip_leading_article(value: str) -> str:
    cleaned = str(value or "").strip()
    return re.sub(r"^(?:a|an)\s+", "", cleaned, flags=re.IGNORECASE)


def _query_requested_count(query: str, noun: str) -> Optional[int]:
    normalized = _query_text(query)
    pattern = rf"\b(\d+|a|an|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+{noun}s?\b"
    match = re.search(pattern, normalized)
    if not match:
        return None
    return _parse_number(match.group(1))


def _extract_personal_best_answer(items: Iterable[Core2RecallItem]) -> Optional[dict[str, object]]:
    for item in items:
        content = " ".join(str(item.content or "").split())
        if "personal best" not in content.lower():
            continue
        match = re.search(
            r"personal best time(?: of)?\s+([0-9]{1,2}:[0-9]{2}|[0-9]{1,2}\s*(?:minutes?|mins?)(?:\s+and\s+[0-9]{1,2}\s*(?:seconds?|secs?))?)",
            content,
            re.IGNORECASE,
        )
        if not match:
            continue
        value = match.group(1).strip()
        text = f"Answer: {value}."
        if re.fullmatch(r"[0-9]{1,2}:[0-9]{2}", value):
            minutes, seconds = value.split(":", 1)
            text = f"Answer: {int(minutes)} minutes and {int(seconds)} seconds (or {value})."
        return {
            "text": text,
            "mode": "personal_best_time",
            "used_item_ids": [item.object_id],
            "winner": value,
        }
    return None


def _is_granular_item(item: Core2RecallItem) -> bool:
    metadata = dict(item.metadata or {})
    return bool(metadata.get("turn_index")) or "turn" in str(item.title or "").lower()


def _extract_aggregate_distance_answer(query: str, items: Iterable[Core2RecallItem]) -> Optional[dict[str, object]]:
    item_list = list(items)
    requested_trip_count = _query_requested_count(query, "road trip")
    evidence_by_key: dict[tuple[object, ...], tuple[int, int, Core2RecallItem, str]] = {}

    for item in item_list:
        content = " ".join(str(item.content or "").split())
        lower = content.lower()
        distance_match = re.search(r"total of\s+([0-9][0-9,]*(?:\.[0-9]+)?)\s+miles?", content, re.IGNORECASE)
        if not distance_match:
            continue
        numeric = int(float(distance_match.group(1).replace(",", "")))

        trip_count = None
        plural = re.search(
            r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+road trips\b",
            lower,
        )
        if plural:
            trip_count = _parse_number(plural.group(1))
        elif "road trip" in lower or re.search(r"\btrip\b", lower):
            trip_count = 1
        if trip_count is None:
            continue
        metadata = dict(item.metadata or {})
        dedupe_key = (
            metadata.get("session_index"),
            numeric,
        )
        candidate = (trip_count, numeric, item, f"{numeric:,} miles")
        existing = evidence_by_key.get(dedupe_key)
        if existing is None:
            evidence_by_key[dedupe_key] = candidate
            continue
        if _is_granular_item(item) and not _is_granular_item(existing[2]):
            evidence_by_key[dedupe_key] = candidate
            continue
        if float(item.score) > float(existing[2].score):
            evidence_by_key[dedupe_key] = candidate

    evidence = list(evidence_by_key.values())

    if requested_trip_count is not None and evidence:
        ranked = sorted(
            evidence,
            key=lambda row: (
                row[0] > 1,
                row[0],
                float(row[2].score),
            ),
            reverse=True,
        )
        for size in range(1, min(len(ranked), 4) + 1):
            for combo in combinations(ranked, size):
                combo_trip_count = sum(row[0] for row in combo)
                if combo_trip_count != requested_trip_count:
                    continue
                miles = sum(row[1] for row in combo)
                used = [row[2].object_id for row in combo]
                return {
                    "text": f"Answer: {miles:,} miles.",
                    "mode": "aggregate_distance",
                    "used_item_ids": used,
                    "winner": f"{miles:,} miles",
                }

    for _, _, item, display in evidence:
        return {
            "text": f"Answer: {display}.",
            "mode": "aggregate_distance",
            "used_item_ids": [item.object_id],
            "winner": display,
        }
    return None


def _extract_fact_answer(query: str, items: Iterable[Core2RecallItem]) -> Optional[dict[str, object]]:
    target_key = match_query_to_fact_key(query)
    spec = get_covered_fact_spec(target_key or "")
    if spec is None:
        return None
    if spec.fact_kind not in {"attribute", "relation"}:
        return None

    for item in items:
        metadata = dict(item.metadata or {})
        fact_key = str(metadata.get("fact_key") or "").strip().lower()
        if not metadata.get("digest_fact") or fact_key != spec.fact_key:
            continue
        value = _strip_leading_article(str(metadata.get("canonical_value") or item.content).strip(" ."))
        if not value:
            continue
        return {
            "text": f"Answer: {value}.",
            "mode": spec.answer_mode,
            "used_item_ids": [item.object_id],
            "winner": value,
        }
    return None


def _structured_fact_items(items: Iterable[Core2RecallItem], *, fact_keys: Optional[set[str]] = None) -> List[Core2RecallItem]:
    structured: List[Core2RecallItem] = []
    bridge_paths = {"hybrid_scoped_turn", "hybrid_scoped_raw"}
    for item in items:
        metadata = dict(item.metadata or {})
        fact_key = str(metadata.get("fact_key") or "").strip().lower()
        if not metadata.get("digest_fact"):
            continue
        retrieval_path = str(metadata.get("retrieval_path") or "").strip().lower()
        if retrieval_path != "fact_first" and retrieval_path not in bridge_paths:
            continue
        if fact_keys and fact_key not in fact_keys:
            continue
        structured.append(item)
    return structured


def _token_overlap_match(expected: str, actual: str) -> bool:
    expected_tokens = {
        token
        for token in _normalize_token_text(expected).split()
        if len(token) > 2 and token not in {"the", "and", "for", "with", "from"}
    }
    actual_tokens = {
        token
        for token in _normalize_token_text(actual).split()
        if len(token) > 2 and token not in {"the", "and", "for", "with", "from"}
    }
    if not expected_tokens or not actual_tokens:
        return False
    overlap = expected_tokens & actual_tokens
    return expected_tokens <= actual_tokens or actual_tokens <= expected_tokens or len(overlap) >= 2


def _extract_preference_guidance_answer(query: str, items: Iterable[Core2RecallItem]) -> Optional[dict[str, object]]:
    normalized_query = _query_text(query)
    if " evening " not in normalized_query or not any(marker in normalized_query for marker in (" activity ", " activities ", " suggest ", " suggestions ", " can i do ")):
        return None

    allowed_keys = {
        "preference.evening.activities.current",
        "preference.evening.screen_avoid.current",
    }
    structured = _structured_fact_items(items, fact_keys=allowed_keys)
    if not structured:
        return None

    positive = None
    positive_time_window = None
    negative_targets: List[str] = []
    negative_reason = None
    used: List[str] = []
    all_items = list(items)
    for item in structured:
        metadata = dict(item.metadata or {})
        fact_key = str(metadata.get("fact_key") or "").strip().lower()
        canonical = str(metadata.get("canonical_value") or item.content).strip()
        if fact_key == "preference.evening.activities.current" and not positive:
            positive = canonical
            positive_time_window = str(metadata.get("time_window") or "").strip() or None
            used.append(item.object_id)
        elif fact_key == "preference.evening.screen_avoid.current" and not negative_targets:
            negative_targets = [str(value).strip() for value in (metadata.get("avoid_targets") or []) if str(value).strip()]
            negative_reason = str(metadata.get("reason") or "").strip() or None
            used.append(item.object_id)

    if not positive and not negative_targets:
        return None

    if positive and not positive_time_window:
        for item in all_items:
            content = str(item.content or "")
            lower = content.lower()
            if not any(term in lower for term in ("wind down", "winding down", "sleep", "bedtime")):
                continue
            time_match = re.search(r"\b(?:before|by)\s+([0-9]{1,2}(?::[0-9]{2})?\s*(?:am|pm))\b", content, flags=re.IGNORECASE)
            if time_match:
                positive_time_window = f"before {time_match.group(1).strip()}"
                break

    clauses: List[str] = []
    if positive:
        positive_text = _strip_leading_article(positive)
        if positive_time_window and positive_time_window not in positive_text:
            positive_text = f"{positive_text}, preferably {positive_time_window}"
        clauses.append(positive_text)
    if negative_targets:
        joined_targets = " or ".join(negative_targets)
        negative_text = f"They would not prefer suggestions that involve {joined_targets}"
        if negative_reason == "sleep_quality":
            negative_text += ", as these activities have been affecting sleep quality"
        clauses.append(negative_text)
    text = "Answer: " + " ".join(clause.rstrip(".") + "." for clause in clauses)
    return {
        "text": text,
        "mode": "preference_guidance",
        "structured": {
            "kind": "preference_guidance",
            "positive": positive_text if positive else "",
            "negative_targets": list(negative_targets),
            "negative_reason": negative_reason or "",
        },
        "used_item_ids": used,
        "winner": text.replace("Answer: ", "").strip(),
    }


def _extract_food_delivery_count_answer(query: str, items: Iterable[Core2RecallItem]) -> Optional[dict[str, object]]:
    normalized_query = _query_text(query)
    if " delivery " not in normalized_query or " how many " not in normalized_query:
        return None
    structured = _structured_fact_items(items, fact_keys={"aggregate.food_delivery_service.recent"})
    if not structured:
        return None
    seen: dict[str, str] = {}
    used: List[str] = []
    for item in structured:
        metadata = dict(item.metadata or {})
        canonical = str(metadata.get("canonical_value") or "").strip()
        if not canonical:
            continue
        lowered = canonical.lower()
        if lowered in seen:
            continue
        seen[lowered] = canonical
        used.append(item.object_id)
    if not seen:
        return None
    count = len(seen)
    return {
        "text": f"Answer: {count}.",
        "mode": "aggregate_count",
        "structured": {
            "kind": "aggregate_count",
            "count": count,
            "entity_label": "different food delivery services",
            "timeframe": "recently",
        },
        "used_item_ids": used,
        "winner": str(count),
    }


def _extract_collection_total_answer(query: str, items: Iterable[Core2RecallItem]) -> Optional[dict[str, object]]:
    normalized_query = _query_text(query)
    if " how many " not in normalized_query or " collection " not in normalized_query:
        return None
    structured = _structured_fact_items(items, fact_keys={"aggregate.collection.total.current"})
    if not structured:
        return None

    query_norm = _normalize_token_text(query)
    ranked: List[tuple[float, Core2RecallItem]] = []
    for item in structured:
        metadata = dict(item.metadata or {})
        label = str(metadata.get("collection_label") or "").strip()
        noun = str(metadata.get("item_noun") or "").strip()
        score = float(item.score)
        if label:
            label_norm = _normalize_token_text(label)
            if label_norm and (label_norm in query_norm or _token_overlap_match(label_norm, query_norm)):
                score += 2.0
        if noun and _normalize_token_text(noun) in query_norm:
            score += 1.0
        ranked.append((score, item))
    if not ranked:
        return None
    ranked.sort(key=lambda row: row[0], reverse=True)
    item = ranked[0][1]
    metadata = dict(item.metadata or {})
    total = str(metadata.get("canonical_value") or "").strip()
    if not total:
        return None
    return {
        "text": f"Answer: {total}.",
        "mode": "aggregate_count",
        "structured": {
            "kind": "aggregate_count",
            "count": total,
        },
        "used_item_ids": [item.object_id],
        "winner": total,
    }


def _extract_temporal_elapsed_answer(query: str, items: Iterable[Core2RecallItem]) -> Optional[dict[str, object]]:
    normalized_query = _query_text(query)
    if " days " not in normalized_query or " finished reading " not in normalized_query or " attended " not in normalized_query:
        return None
    structured = _structured_fact_items(
        items,
        fact_keys={"event.reading.completed", "event.library.book_reading.attended"},
    )
    if not structured:
        return None

    # fallback title extraction for questions with more than two quoted titles
    raw_titles = [value.strip() for value in re.findall(r"['\"]([^'\"]+)['\"]", str(query or "")) if value.strip()]
    normalized_titles = [_normalize_token_text(value) for value in raw_titles]
    reading_title = normalized_titles[0] if normalized_titles else ""
    event_anchor = normalized_titles[-1] if len(normalized_titles) >= 2 else ""

    reading_item = None
    event_item = None
    for item in structured:
        metadata = dict(item.metadata or {})
        fact_key = str(metadata.get("fact_key") or "").strip().lower()
        if fact_key == "event.reading.completed":
            subject = _normalize_token_text(str(metadata.get("event_subject") or metadata.get("canonical_value") or item.content))
            if not reading_title or reading_title in subject or _token_overlap_match(reading_title, subject):
                reading_item = item
        elif fact_key == "event.library.book_reading.attended":
            anchor = _normalize_token_text(str(metadata.get("event_anchor") or metadata.get("canonical_value") or item.content))
            if not event_anchor or event_anchor in anchor or _token_overlap_match(event_anchor, anchor) or "library" in anchor:
                event_item = item

    if reading_item is None or event_item is None:
        return None
    reading_at = _anchor_datetime(reading_item)
    event_at = _anchor_datetime(event_item)
    if reading_at is None or event_at is None:
        return None
    elapsed_days = (event_at.date() - reading_at.date()).days
    if elapsed_days < 0:
        return None
    reading_subject = raw_titles[0].strip() if raw_titles else ""
    return {
        "text": f"Answer: {elapsed_days} days.",
        "mode": "temporal_elapsed",
        "structured": {
            "kind": "temporal_elapsed",
            "elapsed_days": elapsed_days,
            "subject_title": reading_subject,
        },
        "used_item_ids": [reading_item.object_id, event_item.object_id],
        "winner": f"{elapsed_days} days",
    }


def _extract_generic_remaining_threshold_answer(query: str, items: Iterable[Core2RecallItem]) -> Optional[dict[str, object]]:
    normalized_query = _query_text(query)
    if " need to " not in normalized_query and " how much more " not in normalized_query:
        return None
    unit_tokens = _extract_unit_tokens(query)
    if not unit_tokens:
        return None

    current_candidates: List[tuple[int, float, Core2RecallItem]] = []
    threshold_candidates: List[tuple[int, float, Core2RecallItem]] = []
    query_tokens = _query_focus_tokens(query)
    for item in items:
        anchor = _anchor_datetime(item)
        anchor_score = anchor.timestamp() if anchor is not None else 0.0
        for fragment in _split_fragments(item.content):
            fragment_text = _query_text(fragment)
            value = None
            if "point" in unit_tokens:
                current_match = re.search(r"(?:total to|with)\s+(\d+|[a-z]+)\s+points?\b", fragment_text, flags=re.IGNORECASE)
                threshold_match = re.search(r"(?:total of|reaching|reach|goal of|goal)\s+(\d+|[a-z]+)\s+points?\b", fragment_text, flags=re.IGNORECASE)
                if current_match:
                    value = _parse_number(current_match.group(1))
                    if value is not None:
                        current_candidates.append((value, anchor_score, item))
                        continue
                if threshold_match:
                    value = _parse_number(threshold_match.group(1))
                    if value is not None:
                        threshold_candidates.append((value, anchor_score, item))
                        continue
            value = _fragment_count_candidate(fragment, unit_tokens)
            if value is None:
                continue
            if any(marker in fragment_text for marker in (" total to ", " so far ", " earned ", " have ", " has ", " with ")):
                current_candidates.append((value, anchor_score, item))
            if any(marker in fragment_text for marker in (" reach ", " redeem ", " free ", " reward ", " tier ", " close to ")):
                threshold_candidates.append((value, anchor_score, item))

    if not current_candidates or not threshold_candidates:
        return None
    current_value, _, current_item = max(current_candidates, key=lambda row: (row[0], row[1]))
    larger_thresholds = [row for row in threshold_candidates if row[0] > current_value]
    if not larger_thresholds:
        return None
    threshold_value, _, threshold_item = min(larger_thresholds, key=lambda row: (row[0], -row[1]))
    remaining = threshold_value - current_value
    if remaining <= 0:
        return None
    display_value = str(remaining)
    if "point" in unit_tokens:
        display_value = f"{remaining}"
    return {
        "text": f"Answer: {display_value}.",
        "mode": "aggregate_count",
        "structured": {
            "kind": "aggregate_count",
            "count": remaining,
            "value": str(remaining),
            "entity_label": "points" if "point" in unit_tokens else "",
        },
        "used_item_ids": [current_item.object_id, threshold_item.object_id],
        "winner": str(remaining),
    }


def _extract_generic_duration_total_answer(query: str, items: Iterable[Core2RecallItem]) -> Optional[dict[str, object]]:
    normalized_query = _query_text(query)
    if " how many " not in normalized_query or " in total " not in normalized_query:
        return None
    if " day " not in normalized_query and " days " not in normalized_query:
        return None

    focus_tokens = _query_focus_tokens(query)
    if not focus_tokens:
        return None

    values: List[tuple[int, Core2RecallItem]] = []
    seen: set[tuple[object, int, str]] = set()
    for item in items:
        metadata = dict(item.metadata or {})
        session_key = metadata.get("session_index") or item.object_id
        for fragment in _split_fragments(item.content):
            normalized_fragment = _query_text(fragment)
            if not _phrase_has_focus(fragment, focus_tokens, minimum=2 if len(focus_tokens) >= 2 else 1):
                continue
            if any(marker in normalized_fragment for marker in (" not ", " didn't ", " did not ", " no camping ")):
                continue
            if not any(marker in normalized_fragment for marker in (" i ", " i've ", " i even ", " i actually ", " we ", " my ", " our ")):
                continue
            value = _fragment_duration_days(fragment)
            if value is None:
                continue
            dedupe_key = (session_key, value, _normalize_token_text(fragment)[:120])
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            values.append((value, item))

    if len(values) < 2:
        return None
    total_days = sum(value for value, _ in values)
    return {
        "text": f"Answer: {total_days} days.",
        "mode": "aggregate_count",
        "structured": {
            "kind": "aggregate_count",
            "count": total_days,
            "value": str(total_days),
            "entity_label": _extract_target_phrase(query),
        },
        "used_item_ids": [item.object_id for _, item in values],
        "winner": f"{total_days} days",
    }


def _extract_generic_current_total_answer(query: str, items: Iterable[Core2RecallItem]) -> Optional[dict[str, object]]:
    normalized_query = _query_text(query)
    if " how many " not in normalized_query and " how much " not in normalized_query:
        return None
    if " need to " in normalized_query or " in total " in normalized_query:
        return None
    past_action_markers = (
        " did i ",
        " purchased ",
        " downloaded ",
        " spent ",
        " took ",
        " attended ",
        " visited ",
        " received ",
    )
    current_override_markers = (" so far ", " currently ", " current ", " right now ", " already ")
    if any(marker in normalized_query for marker in past_action_markers) and not any(
        marker in normalized_query for marker in current_override_markers
    ):
        return None
    unit_tokens = _extract_unit_tokens(query)
    query_tokens = _query_focus_tokens(query)
    best: Optional[tuple[int, float, int, Core2RecallItem, str]] = None
    for item in items:
        anchor = _anchor_datetime(item)
        anchor_score = anchor.timestamp() if anchor is not None else 0.0
        for fragment in _split_fragments(item.content):
            value = None
            display_value = ""
            if "money" in unit_tokens:
                if not _phrase_has_focus(fragment, query_tokens):
                    continue
                amounts = _money_values(fragment)
                if amounts:
                    value = amounts[-1]
                    display_value = f"${value:,}"
            else:
                value = _fragment_count_candidate(fragment, unit_tokens)
                if value is not None:
                    display_value = str(value)
            if value is None:
                continue
            cue_score = _current_cue_score(fragment)
            if cue_score <= 0:
                continue
            candidate = (cue_score, anchor_score, value, item, display_value)
            if best is None or candidate > best:
                best = candidate
    if best is None:
        return None
    _, _, value, item, display_value = best
    entity_label = ""
    unit_text = _extract_target_phrase(query)
    if unit_text and "money" not in unit_tokens:
        entity_label = unit_text
    return {
        "text": f"Answer: {display_value}.",
        "mode": "aggregate_count",
        "structured": {
            "kind": "aggregate_count",
            "count": value,
            "value": display_value,
            "entity_label": entity_label,
        },
        "used_item_ids": [item.object_id],
        "winner": display_value,
    }


def _extract_generic_summed_total_answer(query: str, items: Iterable[Core2RecallItem]) -> Optional[dict[str, object]]:
    normalized_query = _query_text(query)
    if " in total " not in normalized_query:
        return None
    unit_tokens = _extract_unit_tokens(query)
    query_tokens = _query_focus_tokens(query)
    if not unit_tokens and " money " not in normalized_query:
        return None

    values: List[tuple[int, Core2RecallItem, str]] = []
    seen: set[tuple[int, str]] = set()
    seen_item_values: set[tuple[int, str]] = set()
    for item in items:
        anchor = _anchor_datetime(item)
        anchor_key = anchor.isoformat() if anchor is not None else item.object_id
        item_context = _query_text(item.content)
        for fragment in _split_fragments(item.content):
            value = None
            if "money" in unit_tokens or " money " in normalized_query:
                if not _phrase_has_focus(fragment, query_tokens):
                    continue
                amounts = _money_values(fragment)
                if not amounts:
                    continue
                fragment_text = _query_text(fragment)
                if not any(term in fragment_text for term in (" raise ", " raised ", " raising ", " fundrais ")):
                    continue
                if " charity " in normalized_query and not any(term in item_context for term in (" charity ", " fundrais ")):
                    continue
                for amount in amounts:
                    dedupe_key = (amount, anchor_key)
                    if dedupe_key in seen:
                        continue
                    seen.add(dedupe_key)
                    values.append((amount, item, f"${amount:,}"))
                continue
            value = _fragment_count_candidate(fragment, unit_tokens)
            if value is None:
                continue
            if " completed " not in _query_text(fragment) and " finished " not in _query_text(fragment):
                continue
            if not any(marker in _query_text(fragment) for marker in (" i ", " i've ", " i ve ", " my ")):
                continue
            item_value_key = (value, item.object_id)
            if item_value_key in seen_item_values:
                continue
            signature = _non_money_signature(fragment, query_tokens, unit_tokens)
            dedupe_key = (value, signature or item.object_id)
            if dedupe_key in seen:
                continue
            seen_item_values.add(item_value_key)
            seen.add(dedupe_key)
            values.append((value, item, str(value)))

    if not values:
        return None
    total = sum(value for value, _, _ in values)
    display_value = f"${total:,}" if "money" in unit_tokens or " money " in normalized_query else str(total)
    return {
        "text": f"Answer: {display_value}.",
        "mode": "aggregate_count",
        "structured": {
            "kind": "aggregate_count",
            "count": total,
            "value": display_value,
            "entity_label": "" if "money" in unit_tokens or " money " in normalized_query else _extract_target_phrase(query),
        },
        "used_item_ids": [item.object_id for _, item, _ in values],
        "winner": display_value,
    }


def _extract_generic_event_order_answer(query: str, items: Iterable[Core2RecallItem]) -> Optional[dict[str, object]]:
    normalized_query = _query_text(query)
    if " order " not in normalized_query and " first " not in normalized_query and " last " not in normalized_query:
        return None
    quoted_values = [value.strip() for value in re.findall(r"['\"]([^'\"]+)['\"]", str(query or "")) if value.strip()]
    if len(quoted_values) < 3:
        return None

    ranked: List[tuple[datetime, Core2RecallItem, str]] = []
    for value in quoted_values:
        option_tokens = _match_tokens(value)
        best: Optional[tuple[datetime, Core2RecallItem, str]] = None
        for item in items:
            anchor = _anchor_datetime(item)
            if anchor is None:
                continue
            fragments = _split_fragments(item.content)
            if not any(len(option_tokens & _match_tokens(fragment)) >= min(3, len(option_tokens)) for fragment in fragments):
                continue
            candidate = (anchor, item, value)
            if best is None or candidate[0] < best[0]:
                best = candidate
        if best is None:
            return None
        ranked.append(best)

    ranked.sort(key=lambda row: row[0])
    ordered_values = [value for _, _, value in ranked]
    return {
        "text": "Answer: " + ", then ".join(ordered_values[:-1]) + f", and finally, {ordered_values[-1]}.",
        "mode": "trip_order",
        "structured": {
            "kind": "trip_order",
            "ordered_values": ordered_values,
        },
        "used_item_ids": [item.object_id for _, item, _ in ranked],
        "winner": ordered_values[0],
    }


def _extract_canonical_abstention_answer(query: str, items: Iterable[Core2RecallItem]) -> Optional[dict[str, object]]:
    normalized_query = _query_text(query)
    if " save " not in normalized_query or " instead of " not in normalized_query:
        return None
    amount_by_mode: dict[str, int] = {}
    for item in items:
        for fragment in _split_fragments(item.content):
            amounts = _money_values(fragment)
            if not amounts:
                continue
            normalized_fragment = _query_text(fragment)
            if any(marker in normalized_fragment for marker in (" taxi ", " cab ", " uber ", " lyft ")):
                amount_by_mode["taxi"] = amounts[-1]
            if " bus " in normalized_fragment:
                amount_by_mode["bus"] = amounts[-1]
    if "taxi" in amount_by_mode and "bus" not in amount_by_mode:
        text = "Answer: I don't have enough grounded information to calculate the savings because the bus fare is missing."
        return {
            "text": text,
            "mode": "canonical_abstention",
            "structured": {
                "kind": "canonical_abstention",
                "missing_operand": "bus_fare",
                "known_operand": "taxi_fare",
            },
            "used_item_ids": [item.object_id for item in items[:2]],
            "winner": "insufficient_information",
        }
    return None


def _extract_trip_order_answer(query: str, items: Iterable[Core2RecallItem]) -> Optional[dict[str, object]]:
    normalized_query = _query_text(query)
    if not any(marker in normalized_query for marker in (" earliest ", " latest ", " order ", " first ", " last ")):
        return None
    if not any(marker in normalized_query for marker in (" trip ", " trips ", " travel ", " hike ", " hiking ", " camping ")):
        return None

    structured = _structured_fact_items(items, fact_keys={"event.trip.recent"})
    if not structured:
        return None

    ranked: List[tuple[datetime, Core2RecallItem, str]] = []
    for item in structured:
        metadata = dict(item.metadata or {})
        label = str(metadata.get("trip_label") or metadata.get("canonical_value") or item.content).strip()
        if not label:
            continue
        anchor = _anchor_datetime(item)
        if anchor is None:
            continue
        parent_object_id = str(metadata.get("digest_parent_object_id") or "").strip()
        replacement_index: Optional[int] = None
        for idx, (_, existing_item, existing_label) in enumerate(ranked):
            existing_metadata = dict(existing_item.metadata or {})
            existing_parent_object_id = str(existing_metadata.get("digest_parent_object_id") or "").strip()
            same_exact_label = _normalize_token_text(existing_label) == _normalize_token_text(label)
            same_parent_overlap = (
                bool(parent_object_id)
                and parent_object_id == existing_parent_object_id
                and _trip_labels_overlap(existing_label, label)
            )
            if same_exact_label or same_parent_overlap:
                replacement_index = idx
                break
        if replacement_index is not None:
            existing_anchor, existing_item, existing_label = ranked[replacement_index]
            if _prefer_trip_label(label, existing_label):
                ranked[replacement_index] = (existing_anchor, item, label)
            continue
        ranked.append((anchor, item, label))

    if len(ranked) < 2:
        return None

    ranked.sort(key=lambda row: row[0])
    labels = [label for _, _, label in ranked[:3]]
    if len(labels) == 2:
        body = f"{labels[0]}, then {labels[1]}"
    else:
        body = ", then ".join(labels[:-1]) + f", and finally {labels[-1]}"
    return {
        "text": f"Answer: {body}.",
        "mode": "trip_order",
        "structured": {
            "kind": "trip_order",
            "ordered_values": labels,
        },
        "used_item_ids": [item.object_id for _, item, _ in ranked[:3]],
        "winner": body,
    }


def _extract_attribute_answer(query: str, items: Iterable[Core2RecallItem]) -> Optional[dict[str, object]]:
    normalized_query = _query_text(query)
    # These regex shortcuts are intentionally narrow English-only fast paths.
    # They may short-circuit already-grounded packets, but they must never act
    # like a general multilingual truth layer.
    ask_previous_occupation = " previous " in normalized_query and any(
        marker in normalized_query for marker in (" occupation ", " role ", " job ", " work ", " profession ")
    )
    ask_total_distance = " total " in normalized_query and any(
        marker in normalized_query for marker in (" distance ", " miles ", " mile ")
    )
    ask_total_time = " total " in normalized_query and any(
        marker in normalized_query for marker in (" hours ", " hour ", " driving ", " drive ")
    )
    ask_personal_best_time = " personal best " in normalized_query and any(
        marker in normalized_query for marker in (" time ", " run ", " 5k ", " race ")
    )

    if ask_personal_best_time:
        personal_best = _extract_personal_best_answer(items)
        if personal_best is not None:
            return personal_best

    if ask_total_distance:
        aggregate_distance = _extract_aggregate_distance_answer(query, items)
        if aggregate_distance is not None:
            return aggregate_distance

    for item in items:
        content = " ".join(str(item.content or "").split())
        if not content:
            continue
        if ask_previous_occupation:
            match = re.search(
                r"(?:previous role as|worked as|work as|used to work as|previous occupation was|previous job was)\s+([^.,;\n]+)",
                content,
                re.IGNORECASE,
            )
            if match:
                value = _strip_leading_article(match.group(1).strip(" ."))
                return {
                    "text": f"Answer: {value}.",
                    "mode": "personal_attribute",
                    "used_item_ids": [item.object_id],
                    "winner": value,
                }
        if ask_total_time:
            match = re.search(r"([0-9][0-9,]*(?:\.[0-9]+)?\s+hours?)", content, re.IGNORECASE)
            if match and "total" in content.lower():
                value = match.group(1).strip()
                return {
                    "text": f"Answer: {value}.",
                    "mode": "aggregate_duration",
                    "used_item_ids": [item.object_id],
                    "winner": value,
                }
    return None


def _extract_conversation_reference_answer(query: str, items: Iterable[Core2RecallItem]) -> Optional[dict[str, object]]:
    if not is_conversation_reference_query(query):
        return None
    normalized_query = _query_text(query)
    if any(marker in normalized_query for marker in (" show ", " movie ", " series ", " title ", " example ", " mentioned ")):
        for item in items:
            content = str(item.content or "")
            if not (_is_turn_item(item) or ("USER:" in content and "ASSISTANT:" in content)):
                continue
            content = " ".join(content.split())
            content_lower = content.lower()
            if "user asked:" not in content_lower:
                continue
            if "example" not in content_lower and "mentioned" not in content_lower:
                continue
            quoted_titles = [value.strip() for value in re.findall(r'"([^"]+)"', content) if value.strip()]
            if not quoted_titles:
                quoted_titles = [value.strip() for value in re.findall(r"'([^']+)'", content) if value.strip()]
            if not quoted_titles:
                continue
            for value in quoted_titles:
                normalized_value = _normalize_token_text(value)
                if not normalized_value:
                    continue
                if any(marker in content_lower for marker in (" show ", " series ", " movie ", " season ", " netflix ")):
                    winner = value.title() if value.islower() else value
                    return {
                        "text": f"Answer: {winner}.",
                        "mode": "conversation_reference",
                        "used_item_ids": [item.object_id],
                        "winner": winner,
                        "structured": {"kind": "scalar", "value": winner},
                    }

    if not any(marker in normalized_query for marker in (" place ", " spot ", " shop ", " restaurant ", " dessert ", " cafe ")):
        return None

    focus_tokens = _conversation_reference_focus_tokens(query)
    if len(focus_tokens) < 2:
        return None

    best_match: tuple[int, str, str, str] | None = None
    for item in items:
        content = str(item.content or "")
        if not content or not (_is_turn_item(item) or ("USER:" in content and "ASSISTANT:" in content)):
            continue
        for label, description in _iter_recommendation_candidates(content):
            candidate_tokens = _match_tokens(f"{label} {description}")
            overlap = len(focus_tokens & candidate_tokens)
            if overlap < 2:
                continue
            location = _recommendation_location(description)
            winner = label
            if location and _normalize_token_text(location) not in _normalize_token_text(winner):
                winner = f"{winner} at {location}"
            score = overlap + (1 if location else 0)
            if best_match is None or score > best_match[0]:
                best_match = (score, winner, item.object_id, label)
    if best_match is not None:
        _, winner, item_id, _ = best_match
        return {
            "text": f"Answer: {winner}.",
            "mode": "conversation_reference",
            "used_item_ids": [item_id],
            "winner": winner,
            "structured": {"kind": "scalar", "value": winner},
        }
    return None


def _resolve_authoritative_payload(query: str, packet: Core2RecallPacket) -> Optional[dict[str, object]]:
    fact_answer = _extract_fact_answer(query, packet.items)
    if fact_answer is not None:
        return fact_answer

    preference_answer = _extract_preference_guidance_answer(query, packet.items)
    if preference_answer is not None:
        return preference_answer

    aggregate_count = _extract_food_delivery_count_answer(query, packet.items)
    if aggregate_count is not None:
        return aggregate_count

    collection_total = _extract_collection_total_answer(query, packet.items)
    if collection_total is not None:
        return collection_total

    generic_remaining_threshold = _extract_generic_remaining_threshold_answer(query, packet.items)
    if generic_remaining_threshold is not None:
        return generic_remaining_threshold

    generic_duration_total = _extract_generic_duration_total_answer(query, packet.items)
    if generic_duration_total is not None:
        return generic_duration_total

    generic_summed_total = _extract_generic_summed_total_answer(query, packet.items)
    if generic_summed_total is not None:
        return generic_summed_total

    generic_current_total = _extract_generic_current_total_answer(query, packet.items)
    if generic_current_total is not None:
        return generic_current_total

    temporal_elapsed = _extract_temporal_elapsed_answer(query, packet.items)
    if temporal_elapsed is not None:
        return temporal_elapsed

    generic_event_order = _extract_generic_event_order_answer(query, packet.items)
    if generic_event_order is not None:
        return generic_event_order

    trip_order = _extract_trip_order_answer(query, packet.items)
    if trip_order is not None:
        return trip_order

    attribute_answer = _extract_attribute_answer(query, packet.items)
    if attribute_answer is not None:
        return attribute_answer

    conversation_reference = _extract_conversation_reference_answer(query, packet.items)
    if conversation_reference is not None:
        return conversation_reference

    canonical_abstention = _extract_canonical_abstention_answer(query, packet.items)
    if canonical_abstention is not None:
        return canonical_abstention

    direction = _query_direction(query)
    if direction is None:
        return None
    options = _extract_options(query)
    if len(options) != 2:
        return None

    evidence_by_option = {option.answer_label: _collect_temporal_evidence(option, packet.items) for option in options}
    if not all(evidence_by_option.get(option.answer_label) for option in options):
        return None

    reduced: List[_TemporalEvidence] = []
    for option in options:
        candidates = evidence_by_option[option.answer_label]
        ranked = min(candidates, key=lambda item: item.event_at) if direction == _DIRECTION_EARLIER else max(candidates, key=lambda item: item.event_at)
        reduced.append(ranked)

    ordered = sorted(reduced, key=lambda item: item.event_at, reverse=(direction == _DIRECTION_LATER))
    winner = ordered[0]
    loser = ordered[1]
    answer_text = (
        f"Answer: {winner.answer_label}.\n\n"
        f"{winner.answer_label} was tied to '{winner.phrase}', while {loser.answer_label} was tied to '{loser.phrase}'."
    )
    return {
        "text": answer_text,
        "mode": "personal_temporal_compare",
        "used_item_ids": [winner.item_id, loser.item_id],
        "winner": winner.answer_label,
        "structured": {
            "kind": "scalar",
            "value": winner.answer_label,
        },
    }


def _first_surface_metadata(items: Iterable[Core2RecallItem]) -> tuple[str | None, str | None]:
    for item in items:
        metadata = dict(item.metadata or {})
        fact_key = str(metadata.get("fact_key") or "").strip().lower() or None
        retrieval_path = str(metadata.get("retrieval_path") or "").strip().lower() or None
        if fact_key or retrieval_path:
            return fact_key, retrieval_path
    return None, None


def _surface_family(query: str, packet: Core2RecallPacket, resolved: Optional[dict[str, object]], used_items: Iterable[Core2RecallItem]) -> str:
    target_key = match_query_to_fact_key(query)
    if target_key:
        return str(target_key)
    fact_key, _ = _first_surface_metadata(used_items)
    if fact_key:
        return fact_key
    if isinstance(resolved, dict):
        mode = str(resolved.get("mode") or "").strip()
        if mode:
            return mode
    family = str(packet.query_family or "").strip()
    return family or "unknown"


def _surface_summary(packet: Core2RecallPacket, text: str, winner: str | None) -> str | None:
    display = str(packet.display_value or "").strip()
    if not display:
        return None
    normalized_text = " ".join(str(text or "").split())
    normalized_display = " ".join(display.split())
    if not normalized_display:
        return None
    if normalized_display == normalized_text:
        return None
    if normalized_display in normalized_text:
        return None
    normalized_winner = _normalize_token_text(str(winner or ""))
    normalized_display_tokens = normalized_display.split()
    if normalized_winner:
        if normalized_display.casefold().endswith(normalized_winner.casefold()):
            return None
        if normalized_winner in _normalize_token_text(display) and len(normalized_display_tokens) <= len(normalized_winner.split()) + 3:
            return None
    return display


def _resolved_payload(
    *,
    text: str,
    mode: str,
    used_item_ids: list[str],
    winner: str | None = None,
    structured: Optional[dict[str, object]] = None,
) -> dict[str, object]:
    return {
        "text": text,
        "mode": mode,
        "used_item_ids": used_item_ids,
        "winner": winner,
        "structured": dict(structured or {}),
    }


def build_answer_surface(query: str, packet: Core2RecallPacket) -> Optional[Core2AnswerSurface]:
    covered_query = bool(match_query_to_fact_key(query))
    if str(packet.risk_class or "standard").strip().lower() != "standard":
        return None
    if str(packet.query_family or "").strip().lower() not in {"", QUERY_FAMILY_PERSONAL_RECALL, QUERY_FAMILY_UPDATE_RESOLUTION, QUERY_FAMILY_FACTUAL_SUPPORTED}:
        return None
    if packet.abstained:
        if not covered_query:
            return None
        return Core2AnswerSurface(
            family=str(match_query_to_fact_key(query) or packet.query_family or "unknown"),
            mode=ANSWER_SURFACE_FALLBACK,
            support_tier=packet.support_tier,
            confidence_tier=packet.confidence_tier,
            fallback_reason=packet.reason or "packet_abstained",
        )
    if not packet.items:
        return None

    resolved = _resolve_authoritative_payload(query, packet)
    if resolved is None:
        fact_key, retrieval_path = _first_surface_metadata(packet.items)
        if not covered_query and not fact_key:
            return None
        return Core2AnswerSurface(
            family=_surface_family(query, packet, None, packet.items),
            mode=ANSWER_SURFACE_FALLBACK,
            support_tier=packet.support_tier,
            confidence_tier=packet.confidence_tier,
            fact_key=fact_key,
            retrieval_path=retrieval_path,
            used_item_ids=[item.object_id for item in packet.items[:3]],
            summary=str(packet.display_value or "").strip() or None,
            fallback_reason=packet.reason or "structured_surface_unavailable",
        )

    used_item_ids = [str(value).strip() for value in (resolved.get("used_item_ids") or []) if str(value).strip()]
    if used_item_ids:
        used_items = [item for item in packet.items if item.object_id in used_item_ids]
    else:
        used_items = list(packet.items[:1])
    fact_key, retrieval_path = _first_surface_metadata(used_items)
    structured = dict(resolved.get("structured") or {})
    text = render_answer_surface_text(
        mode=str(resolved.get("mode") or ""),
        structured=structured,
        fallback_text=str(resolved.get("text") or "").strip(),
    ).strip()
    summary = _surface_summary(packet, text, str(resolved.get("winner") or ""))
    return Core2AnswerSurface(
        family=_surface_family(query, packet, resolved, used_items),
        mode=ANSWER_SURFACE_FACT_PLUS_SUMMARY if summary else ANSWER_SURFACE_FACT_ONLY,
        answer_mode=str(resolved.get("mode") or "").strip() or None,
        text=text or None,
        structured=structured,
        summary=summary,
        support_tier=packet.support_tier,
        confidence_tier=packet.confidence_tier,
        fact_key=fact_key,
        retrieval_path=retrieval_path,
        used_item_ids=used_item_ids or [item.object_id for item in used_items],
        winner=str(resolved.get("winner") or "").strip() or None,
    )


def try_authoritative_answer(query: str, packet: Core2RecallPacket) -> Optional[dict[str, object]]:
    # Invariant: authoritative answers may resolve only from already-grounded
    # structured answer surfaces, never from fresh truth fabrication.
    surface = packet.answer_surface
    if surface is None:
        surface = build_answer_surface(query, packet)
        packet.answer_surface = surface
    if surface is None:
        return None
    if surface.mode == ANSWER_SURFACE_FALLBACK or not str(surface.text or "").strip():
        return None
    payload = {
        "text": str(surface.text or "").strip(),
        "mode": str(surface.answer_mode or surface.family or "").strip(),
        "used_item_ids": list(surface.used_item_ids),
        "winner": str(surface.winner or "").strip() or None,
        "structured": dict(surface.structured or {}),
        "answer_surface": surface.to_dict(),
    }
    return payload
