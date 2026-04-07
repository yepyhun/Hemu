# Hybrid Substrate Interface

## Purpose

Phase 04.10 adds a bounded MemPalace-inspired retrieval seam without changing Core2 truth/state or answer ownership.

This interface is intentionally tiny.

## Upward Contract

The hybrid substrate may only surface:

- canonical Core2 objects already owned by `core2_canonical_truth`
- retrieval annotations in item metadata
- narrow route notes that say whether hybrid raw/turn scope participated

It may not surface:

- a second truth object model
- MemPalace-specific palace/room/graph concepts above the seam
- answer text
- abstention decisions
- independent judge/comparator logic

## Stable Retrieval Annotations

Allowed metadata emitted upward:

- `retrieval_path`
- `hybrid_scope`
- `hybrid_source_id`
- `hybrid_turn_id`
- `hybrid_session_id`

Current values:

- `retrieval_path = hybrid_scoped_raw`
- `retrieval_path = hybrid_scoped_turn`
- `hybrid_scope = raw_archive | turn_exact | session_scope`

## Runtime Switch

The hybrid substrate is controlled by:

- `CORE2_HYBRID_SUBSTRATE_MODE=on`
- `CORE2_HYBRID_SUBSTRATE_MODE=shadow`
- `CORE2_HYBRID_SUBSTRATE_MODE=off`

Semantics:

- `on`: hybrid results may enter retrieval ranking
- `shadow`: hybrid traces run, but canonical retrieval remains authoritative
- `off`: hybrid path is fully disabled

## Ownership Boundary

Core2 still owns:

- truth/state/provenance
- fact digestion
- deterministic answer surface
- abstention
- gate semantics

The hybrid seam only owns:

- bounded raw/verbatim search over existing Core2 storage
- bounded scoped retrieval promotion back into canonical objects
