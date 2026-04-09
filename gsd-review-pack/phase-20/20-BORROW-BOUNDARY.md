# Phase 20 Borrow Boundary

## What Phase 20 adds
- one narrow helper family: `legacy_query_signal_primitives`
- Core2-native translation layer, not direct legacy import
- new signal families:
  - `legacy_temporal_duration`
  - `legacy_current_conflict`
  - `legacy_aggregate_total`

## Where it is wired
- `agent/core2_query_signal_primitives.py`
- `agent/core2_query_shape_seeding.py`
- `agent/core2_hybrid_substrate.py`
- `agent/core2_runtime.py`

## What it does not do
- does not change the Core2 truth model
- does not reopen ranking
- does not add new selector logic
- does not add MemPalace-style storage or hierarchy
- does not import the old Hermes projection engine

## Success condition
- the fixed ten-case replay must move materially

## Failure condition
- local proof may still be green
- but if the fixed ten-case replay does not move, the borrow remains a bounded negative result rather than a retained active improvement
