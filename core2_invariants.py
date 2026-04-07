from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List


ALLOWED_AUTHORITATIVE_RETRIEVAL_PATHS = {
    "fact_first",
    "hybrid_scoped_turn",
    "hybrid_scoped_raw",
}


@dataclass(frozen=True)
class Core2InvariantSpec:
    invariant_id: str
    rule: str
    checker: str


def core2_invariant_specs() -> List[Core2InvariantSpec]:
    return [
        Core2InvariantSpec(
            invariant_id="INV-1",
            rule="Covered-family authoritative answers must be backed by structured answer surfaces rather than raw-only fallback when a covered fact path exists.",
            checker="check_structured_truth_precedence",
        ),
        Core2InvariantSpec(
            invariant_id="INV-2",
            rule="Deterministically resolvable current-state digest facts must not leave contradictory active canonical states for the same identity key.",
            checker="check_current_state_uniqueness",
        ),
        Core2InvariantSpec(
            invariant_id="INV-3",
            rule="Obvious tool/file error artifacts must not remain active after explicit noise repair.",
            checker="check_noise_artifact_hygiene",
        ),
    ]


def check_structured_truth_precedence(packet: Any) -> Dict[str, Any]:
    answer_surface = getattr(packet, "answer_surface", None)
    retrieval_path = str(getattr(answer_surface, "retrieval_path", "") or "").strip()
    family = str(getattr(answer_surface, "family", "") or "").strip()
    ok = answer_surface is not None and retrieval_path in ALLOWED_AUTHORITATIVE_RETRIEVAL_PATHS
    return {
        "ok": ok,
        "retrieval_path": retrieval_path,
        "family": family,
        "allowed_paths": sorted(ALLOWED_AUTHORITATIVE_RETRIEVAL_PATHS),
    }


def check_current_state_uniqueness(records: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    active_by_identity: Dict[str, List[Dict[str, Any]]] = {}
    for record in records:
        if str(record.get("state_status") or "").strip() != "canonical_active":
            continue
        metadata = dict(record.get("metadata") or {})
        if not metadata.get("digest_fact"):
            continue
        temporal_slot = str(metadata.get("temporal_slot") or "").strip().lower()
        fact_key = str(metadata.get("fact_key") or "").strip().lower()
        if temporal_slot != "current" and not fact_key.endswith(".current"):
            continue
        identity_key = str(metadata.get("identity_key") or record.get("identity_key") or "").strip()
        if not identity_key:
            continue
        active_by_identity.setdefault(identity_key, []).append(record)

    collisions: List[Dict[str, Any]] = []
    for identity_key, entries in active_by_identity.items():
        if len(entries) < 2:
            continue
        canonical_values = {
            str((entry.get("metadata") or {}).get("canonical_value") or entry.get("content") or "").strip()
            for entry in entries
        }
        if len(canonical_values) <= 1:
            continue
        collisions.append(
            {
                "identity_key": identity_key,
                "object_ids": [str(entry.get("object_id") or "") for entry in entries],
                "canonical_values": sorted(value for value in canonical_values if value),
            }
        )

    return {
        "ok": not collisions,
        "collision_count": len(collisions),
        "collisions": collisions,
    }
