---
phase: 04-proof-benchmarks-and-hardening
verified: 2026-04-06T12:59:30+02:00
status: passed
score: 3/3 must-haves verified
---

# Phase 4: Proof, Benchmarks, And Hardening Verification Report

**Phase Goal:** Core2 is verified through automated tests and end-to-end proof gates on the real Hermes runtime path.
**Verified:** 2026-04-06T12:59:30+02:00
**Status:** passed

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Core2 now has broader automated proof across the real Hermes provider/runtime seam, not only narrow store-level contracts | ✓ VERIFIED | `tests/agent/test_core2_memory_manager_e2e.py`, `tests/agent/test_core2_hardening.py`, and `agent/core2_store.py` prove manager-level lifecycle, noisy graph recall, mixed-history update resolution, and noisy conflict abstention |
| 2 | Core2 now has an inspectable structured proof harness and local benchmark-style slices that stay on the Hermes path | ✓ VERIFIED | `agent/core2_proof_harness.py` and `tests/agent/test_core2_proof_harness.py` prove structured scenario reports, token/replay proof reporting, and a local LongMemEval-style subset |
| 3 | Phase 4 now has an explicit proof ladder and honest release-readiness evidence, with the paid LongMemEval-10 run preserved as the final external gate | ✓ VERIFIED | `.planning/phases/04-proof-benchmarks-and-hardening/04-PROOF-LADDER.md` and `.planning/phases/04-proof-benchmarks-and-hardening/04-RELEASE-READINESS.md` keep local proof green while blocking stronger claims on the pending paid run |

### Required Artifacts

| Artifact | Status | Notes |
|----------|--------|-------|
| `tests/agent/test_core2_memory_manager_e2e.py` | ✓ Present | Manager-level Hermes-path proof |
| `tests/agent/test_core2_hardening.py` | ✓ Present | Noisy graph/update/conflict regressions |
| `agent/core2_proof_harness.py` | ✓ Present | Structured proof harness and subset gate |
| `tests/agent/test_core2_proof_harness.py` | ✓ Present | Active harness verification |
| `04-PROOF-LADDER.md` | ✓ Present | Proof tiers and final external gate |
| `04-RELEASE-READINESS.md` | ✓ Present | Honest local-ready vs external-ready evidence |

### Requirements Coverage

| Requirement | Result |
|-------------|--------|
| `QUAL-02` | ✓ Covered |
| `QUAL-03` | ✓ Covered |

## Verification Commands

- `python3 -m py_compile agent/core2_proof_harness.py agent/core2_store.py tests/agent/test_core2_memory_manager_e2e.py tests/agent/test_core2_proof_harness.py tests/agent/test_core2_hardening.py`
- `PYTEST_ADDOPTS='' .venv/bin/python -m pytest -n 0 tests/agent/test_core2_plugin_loading.py tests/agent/test_core2_provider_foundation.py tests/agent/test_core2_legacy_adapted.py tests/agent/test_core2_retrieval_routing.py tests/agent/test_core2_answer_contract.py tests/agent/test_core2_abstention_delivery.py tests/agent/test_core2_memory_manager_e2e.py tests/agent/test_core2_proof_harness.py tests/agent/test_core2_hardening.py`
- `.venv/bin/python -c "from agent.core2_proof_harness import run_core2_proof_benchmark; print(run_core2_proof_benchmark().as_dict())"`
- `.venv/bin/python -c "from agent.core2_proof_harness import verify_core2_longmemeval_subset; print(verify_core2_longmemeval_subset(sample_size=2, seed=7))"`

## Verification Results

- Targeted Core2 suite: `30 passed in 0.11s`
- Structured proof harness:
  - `core2`: 4/4 passed
  - `builtin_only`: 0/4 passed
- Local LongMemEval-style subset:
  - `core2`: 2/2 passed
  - `builtin_only`: 0/2 passed

## Gaps Summary

**No local Phase 4 gaps found.** The remaining gate is external: the paid LongMemEval-10 run.

## Warnings

- The paid LongMemEval-10 run is still pending and remains the final external gate before a stronger benchmark/SOTA claim.
- Repo-local git identity is still unset, so strict atomic commits were not created.
- Full `uv run --extra dev pytest ...` remains environment-sensitive because of the offline `tinker` dependency path, but the active `.venv` verification path is green.

---
*Verified: 2026-04-06T12:59:30+02:00*
*Verifier: the agent (local verification fallback)*
