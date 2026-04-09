from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

_NOISY_PREFIXES = (
    "what",
    "which",
    "how many",
    "how much",
    "how much time",
    "how long",
    "do i",
    "did i",
    "for the",
    "is the",
    "was the",
)

_DURATION_UNITS = ("day", "days", "week", "weeks", "month", "months", "year", "years", "hour", "hours", "minute", "minutes")


@dataclass(frozen=True)
class LegacySignalSeedBundle:
    signal_family: str = ""
    seed_queries: List[str] = field(default_factory=list)

    @property
    def applicable(self) -> bool:
        return bool(self.signal_family and self.seed_queries)


def build_legacy_temporal_duration_bundle(query: str) -> LegacySignalSeedBundle:
    normalized = " ".join(str(query or "").strip().split())
    lowered = normalized.lower()
    seeds: List[str] = []

    unit_pattern = "|".join(_DURATION_UNITS)
    match = re.search(rf"\bhow many\s+(?:{unit_pattern})\s+ago did i\s+(.+?)(?:\?|$)", normalized, flags=re.IGNORECASE)
    if match:
        seeds.append(_clean_seed_text(match.group(1)))

    match = re.search(r"\bhow long was i\s+(.+?)\s+for(?:\?|$)", normalized, flags=re.IGNORECASE)
    if match:
        seeds.append(_clean_seed_text(match.group(1)))

    match = re.search(r"\bhow much time do i\s+(.+?)\s+every day(?:\?|$)", normalized, flags=re.IGNORECASE)
    if match:
        seeds.append(_clean_seed_text(match.group(1)))

    if not seeds and not any(token in lowered for token in (" ago ", " how long ", " every day")):
        return LegacySignalSeedBundle()
    return LegacySignalSeedBundle(signal_family="legacy_temporal_duration", seed_queries=_dedupe_seed_queries(seeds))


def build_legacy_current_conflict_bundle(query: str) -> LegacySignalSeedBundle:
    normalized = " ".join(str(query or "").strip().split())
    lowered = normalized.lower()
    seeds: List[str] = []

    match = re.search(r"\bfor the\s+(.+?),\s+did i switch to\s+.+?(?:\?|$)", normalized, flags=re.IGNORECASE)
    if match:
        focus = _clean_seed_text(match.group(1))
        if focus:
            seeds.extend([focus, f"previous {focus}", f"latest {focus}"])

    match = re.search(r"\bdo i\s+(.+?)\s+more frequently than i did previously(?:\?|$)", normalized, flags=re.IGNORECASE)
    if match:
        focus = _clean_seed_text(match.group(1))
        if focus:
            seeds.extend([focus, f"previous {focus}", f"latest {focus}"])

    if not seeds and not any(token in lowered for token in ("switch", "switched", "changed", "change", "previously", "previous", "more", "less")):
        return LegacySignalSeedBundle()
    return LegacySignalSeedBundle(signal_family="legacy_current_conflict", seed_queries=_dedupe_seed_queries(seeds))


def build_legacy_aggregate_total_bundle(query: str) -> LegacySignalSeedBundle:
    normalized = " ".join(str(query or "").strip().split())
    lowered = normalized.lower()
    seeds: List[str] = []

    match = re.search(r"\bhow many\s+\w+\s+did i\s+(.+?)\s+in total(?:\?|$)", normalized, flags=re.IGNORECASE)
    if match:
        seeds.append(_clean_seed_text(match.group(1)))

    match = re.search(r"\bhow many\s+\w+\s+did i\s+(.+?)\s+this year(?:\?|$)", normalized, flags=re.IGNORECASE)
    if match:
        seeds.append(_clean_seed_text(match.group(1)))

    if not seeds and " total " not in f" {lowered} ":
        return LegacySignalSeedBundle()
    return LegacySignalSeedBundle(signal_family="legacy_aggregate_total", seed_queries=_dedupe_seed_queries(seeds))


def _clean_seed_text(value: str) -> str:
    cleaned = " ".join(str(value or "").strip().split())
    cleaned = re.sub(r"^[^A-Za-z0-9]+|[^A-Za-z0-9]+$", "", cleaned)
    lowered = cleaned.lower()
    for noisy in sorted(_NOISY_PREFIXES, key=len, reverse=True):
        if lowered.startswith(noisy + " "):
            cleaned = cleaned[len(noisy) :].strip()
            lowered = cleaned.lower()
    cleaned = re.sub(r"\b(?:in total|this year|every day|per day)\b", "", cleaned, flags=re.IGNORECASE)
    return " ".join(cleaned.strip(" ,.?;:()[]{}").split())


def _dedupe_seed_queries(seeds: List[str]) -> List[str]:
    deduped: List[str] = []
    seen = set()
    for seed in seeds:
        cleaned = " ".join(str(seed or "").strip().split())
        if len(cleaned) < 3:
            continue
        normalized = cleaned.casefold()
        if normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(cleaned)
    return deduped[:4]
