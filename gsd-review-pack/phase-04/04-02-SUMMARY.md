---
phase: 04-proof-benchmarks-and-hardening
plan: 02
subsystem: proof-harness
tags: [core2, proof, benchmark, longmemeval, token-reporting]
requires:
  - phase: 04-proof-benchmarks-and-hardening
    provides: manager-level E2E coverage and harder regression proof
provides:
  - Structured Core2 proof harness
  - Local LongMemEval-style subset verification
  - Token/replay proof reporting
affects: [phase-4, proof, benchmarks, release]
tech-stack:
  added: []
  patterns: [structured-report, hermes-path-proof, benchmark-seed-revival]
key-files:
  created: [agent/core2_proof_harness.py, tests/agent/test_core2_proof_harness.py, .planning/phases/04-proof-benchmarks-and-hardening/04-PROOF-LADDER.md]
  modified: []
key-decisions:
  - "The structured report keeps a builtin-only baseline for seam comparison, but does not pretend that this is the final external benchmark."
  - "The local LongMemEval-style subset is a deterministic proxy gate, while the paid LongMemEval-10 run remains the final external gate."
patterns-established:
  - "Proof artifacts must be inspectable as structured data, not only console prose."
  - "Benchmark revival should adapt legacy report shapes without forcing obsolete KernelMemory assumptions into Core2."
requirements-completed: [QUAL-03]
duration: 35min
completed: 2026-04-06
---

# Phase 4 Plan 02 Summary

**Core2 now has a structured Hermes-path proof harness, a local LongMemEval-style subset gate, and token/replay proof reporting.**

## Accomplishments

- Added `agent/core2_proof_harness.py` with an inspectable `as_dict()` report format.
- Revived useful legacy benchmark ideas:
  - scenario-based proof reporting
  - mode summaries
  - LongMemEval-style subset verification
  - token/replay savings reporting
- Wrote the Phase 4 proof ladder so the local proof tiers and the pending external gate are explicit.

## Files Created/Modified

- `agent/core2_proof_harness.py` - structured proof, subset verification, token reporting
- `tests/agent/test_core2_proof_harness.py` - active proof harness verification
- `.planning/phases/04-proof-benchmarks-and-hardening/04-PROOF-LADDER.md` - explicit proof tiers and final gate

## Issues Encountered

- The repo no longer contains the old benchmark implementation modules, so only the reusable test/report patterns were revived, not the obsolete code itself.
- Repo-local git identity is still unset, so no atomic commits were created.

## Next Phase Readiness

- Release-readiness can now refer to concrete local proof artifacts instead of promises.

---
*Phase: 04-proof-benchmarks-and-hardening*
*Completed: 2026-04-06*
