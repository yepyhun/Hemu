---
phase: 01-core2-provider-foundation
plan: 03
subsystem: testing
tags: [core2, pytest, provider, lifecycle, legacy-tests]
requires:
  - phase: 01-core2-provider-foundation
    provides: real Core2 provider/runtime boundary
provides:
  - Focused Core2 plugin loading tests
  - Focused Core2 lifecycle smoke tests in active suite
  - Clear separation between active tests and legacy seed corpus
affects: [phase-2, phase-4, verification, regression]
tech-stack:
  added: []
  patterns: [focused-foundation-tests, legacy-seed-adaptation]
key-files:
  created: [tests/agent/test_core2_plugin_loading.py, tests/agent/test_core2_provider_foundation.py]
  modified: []
key-decisions:
  - "Kept active Core2 tests small and contract-focused."
  - "Preserved the copied legacy kernel-memory corpus under .planning instead of making it active immediately."
patterns-established:
  - "Adapt legacy tests selectively instead of copying whole files into active collection."
  - "Use manual smoke + compile proof when offline dependency resolution blocks pytest."
requirements-completed: [PROV-01, PROV-03]
duration: 20min
completed: 2026-04-06
---

# Phase 1: Core2 Provider Foundation Summary

**Core2 now has focused loading and lifecycle tests in the active suite, while the old kernel-memory corpus stays preserved as an uncollected legacy seed bank.**

## Performance

- **Duration:** 20 min
- **Started:** 2026-04-06T00:35:00Z
- **Completed:** 2026-04-06T00:55:00Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments
- Added `tests/agent/test_core2_plugin_loading.py` for provider discovery, tool-name stability, and registration behavior.
- Added `tests/agent/test_core2_provider_foundation.py` for foundation lifecycle behavior across remember/recall/explain, memory-write bridging, prefetch, and shutdown.
- Kept the large legacy kernel-memory corpus under `.planning/legacy-test-seeds/kernel-memory/` as reference-only material.

## Task Commits

Atomic task commits were not created because this repo currently has no local `git user.name` / `git user.email` configured.

## Files Created/Modified
- `tests/agent/test_core2_plugin_loading.py` - Focused plugin loading and registration checks
- `tests/agent/test_core2_provider_foundation.py` - Foundation lifecycle checks adapted for current Core2 contracts

## Decisions Made
- Chose small, contract-based active tests instead of wholesale importing legacy test files.
- Used compile-time checks and manual Python smoke scripts as verification fallback because offline dependency resolution blocked `pytest`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Switched verification from full pytest execution to offline-safe smoke validation**
- **Found during:** Task 2 (test execution)
- **Issue:** `uv run --extra dev pytest ...` attempted to resolve an offline git dependency (`tinker`) and failed on DNS resolution
- **Fix:** Ran `python3 -m py_compile` on new Core2 modules/tests and executed direct manual lifecycle/plugin smoke scripts using the real provider/runtime path
- **Files modified:** none
- **Verification:** `manual_core2_smoke_ok`, `manual_plugin_smoke_ok`, and `py_compile` all passed
- **Committed in:** Not committed - local git identity missing

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Verification remained meaningful, but full pytest execution still needs an online/resolved dev environment.

## Issues Encountered
- Full `uv run --extra dev pytest ...` was blocked by offline git dependency resolution for `tinker`.
- Repo-local git identity is unset, so strict per-task commits could not be created in this environment.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Core2 has an active test foothold for future foundation and semantics work.
- When networked dev dependency resolution is available, rerun the targeted pytest set to replace the manual smoke fallback.

---
*Phase: 01-core2-provider-foundation*
*Completed: 2026-04-06*
