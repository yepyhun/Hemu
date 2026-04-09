# Phase 20 Legacy Codemap

## Files inspected
- `/home/lauratom/Asztal/ai/hermes-agent-port/agent/kernel_memory_projection_signals.py`
- `/home/lauratom/Asztal/ai/hermes-agent-port/agent/kernel_memory_objective_units.py`

## Borrowable primitive themes

### Query and temporal signal extraction
From `kernel_memory_projection_signals.py`:
- duration-unit aliases
- schedule-signal extraction
- current-signal detection
- relative temporal anchoring helpers

Why borrowable:
- these are helper-level extractors
- they do not require the old kernel's whole projection contract

### Objective / unit / scope helper ideas
From `kernel_memory_objective_units.py`:
- objective/unit normalization patterns
- scope-term handling
- record-compilation helpers

Why not fully borrowed now:
- Phase 20 is about retrieval opening, not aggregation safety
- full objective-unit plumbing would widen the phase beyond the stop rule

## Actual Phase 20 borrow
- New Core2-native helper module:
  - `agent/core2_query_signal_primitives.py`
- Borrowed at primitive level only:
  - temporal-duration query cues
  - current/previous switch cues
  - aggregate-total cues

## Non-borrowed complexity traps
- full projection ownership logic
- legacy truth/provenance state model
- old runtime-wide semantic contracts
