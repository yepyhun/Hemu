---
phase: 04-proof-benchmarks-and-hardening
plan: 01
subsystem: testing
tags: [core2, tests, e2e, hardening, regression]
requires:
  - phase: 03-retrieval-and-answer-contracts
    provides: routing, answer contracts, abstention, delivery-view discipline
provides:
  - MemoryManager-level Core2 E2E coverage
  - Noisy-edge hardening regression coverage
  - Broader local Core2 regression command set
affects: [phase-4, testing, proof, release]
tech-stack:
  added: []
  patterns: [manager-e2e, regression-hardening, legacy-test-adaptation]
key-files:
  created: [tests/agent/test_core2_memory_manager_e2e.py, tests/agent/test_core2_hardening.py]
  modified: [agent/core2_store.py]
key-decisions:
  - "Phase 4 reuses legacy E2E structure where it still fits, but adapts it to the actual Core2 provider seam instead of reviving obsolete kernel APIs."
  - "Hardening assertions should target noisy relation recall and mixed-history update resolution at the store/runtime seam, not only idealized happy paths."
patterns-established:
  - "Core2 now has explicit manager-level lifecycle proof in the active suite."
  - "Graph-like linkage quality and noisy current-state behavior are explicit regression targets."
requirements-completed: [QUAL-02]
duration: 40min
completed: 2026-04-06
---

# Phase 4 Plan 01 Summary

**Core2 now has active MemoryManager-level E2E coverage and hardening regressions instead of relying only on narrow contract tests.**

## Accomplishments

- Added a real `MemoryManager` Core2 E2E test adapted from the earlier plugin lifecycle pattern.
- Added hardening regressions for noisy relation recall, mixed-history update resolution, and noisy high-risk conflict abstention.
- Tightened canonical search normalization in `agent/core2_store.py` so noisy stopwords and punctuation do not dominate relation/update queries.

## Files Created/Modified

- `tests/agent/test_core2_memory_manager_e2e.py` - manager-level Hermes-path lifecycle proof
- `tests/agent/test_core2_hardening.py` - noisy-edge hardening regressions
- `agent/core2_store.py` - stopword and punctuation-aware canonical search normalization

## Issues Encountered

- The first hardening run exposed a real recall-quality bug: stopword-heavy noisy records could outrank the intended graph/update records.
- Repo-local git identity is still unset, so no atomic commits were created.

## Next Phase Readiness

- Core2 is ready for structured proof harness work and honest release-readiness documentation.

---
*Phase: 04-proof-benchmarks-and-hardening*
*Completed: 2026-04-06*
