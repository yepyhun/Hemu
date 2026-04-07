---
phase: 02-memory-model-and-state-semantics
plan: 03
subsystem: lifecycle
tags: [core2, transitions, maintenance, supersession, archive]
requires:
  - phase: 02-memory-model-and-state-semantics
    provides: plane-aware canonical model with temporal and policy semantics
provides:
  - Explicit candidate/provisional/canonical/rejected/archived/superseded transitions
  - Local maintenance loop entrypoints
  - Active tests for non-destructive forgetting and maintenance effects
affects: [phase-3, phase-4, regression]
tech-stack:
  added: []
  patterns: [transition-log, maintenance-engine, non-destructive-forgetting]
key-files:
  created: [agent/core2_maintenance.py, tests/agent/test_core2_state_transitions.py]
  modified: [agent/core2_store.py, agent/core2_runtime.py]
key-decisions:
  - "Forgetting defaults to archive/demotion semantics rather than destructive deletion."
  - "Maintenance loops remain local deterministic routines for now, but exist as explicit Core2 mechanisms."
patterns-established:
  - "State transitions are durable and inspectable through the transition log."
  - "Maintenance logic lives in isolated Core2 modules, not in Hermes entrypoints."
requirements-completed: [TIME-02]
duration: 25min
completed: 2026-04-06
---

# Phase 2 Plan 03 Summary

**Core2 now has explicit state transitions and maintenance loops, including candidate promotion/rejection, supersession, archival, conflict handling, and stale provisional demotion.**

## Accomplishments

- Added a dedicated maintenance engine for conflict detection, supersession processing, stale provisional demotion, index rebuilds, and activation decay.
- Added explicit runtime methods for candidate extraction, promotion, rejection, conflict marking, supersession, archival, and maintenance execution.
- Added active tests for state transitions, maintenance-driven supersession, and non-destructive forgetting.

## Files Created/Modified

- `agent/core2_maintenance.py` - maintenance loop entrypoints
- `agent/core2_store.py` - transition log and durable state changes
- `agent/core2_runtime.py` - runtime transition helpers and maintenance orchestration
- `tests/agent/test_core2_state_transitions.py` - active transition and maintenance tests

## Issues Encountered

- Repo-local git identity remains unset, so atomic task commits were still not possible.

## Next Phase Readiness

- Phase 3 can now build retrieval routing and answer contracts on top of a real stateful kernel rather than a passive store.

---
*Phase: 02-memory-model-and-state-semantics*
*Completed: 2026-04-06*
