# Phase 4 Proof Ladder

## Goal

Make the Core2 proof story inspectable and honest: prove the real Hermes-path behavior locally, widen regression coverage, then leave the paid LongMemEval-10 run as the final external gate instead of overclaiming earlier.

## Tiers

### Tier 1: Local Contract Proof

- Status: Green
- Evidence:
  - `tests/agent/test_core2_provider_foundation.py`
  - `tests/agent/test_core2_legacy_adapted.py`
  - `tests/agent/test_core2_retrieval_routing.py`
  - `tests/agent/test_core2_answer_contract.py`
  - `tests/agent/test_core2_abstention_delivery.py`
- What it proves:
  - provider lifecycle
  - routing and answer contracts
  - abstention, delivery-view, and compact-prefetch discipline

### Tier 2: Hermes-Path Manager And Hardening Proof

- Status: Green
- Evidence:
  - `tests/agent/test_core2_memory_manager_e2e.py`
  - `tests/agent/test_core2_hardening.py`
  - `agent/core2_store.py`
- What it proves:
  - real `MemoryManager` wiring with builtin + Core2 coexistence
  - one-external-provider rule enforcement
  - noisy relation recall and mixed-history current-state behavior
  - high-risk conflict abstention under noisy legal data

### Tier 3: Structured Local Proof Harness

- Status: Green
- Evidence:
  - `agent/core2_proof_harness.py`
  - `tests/agent/test_core2_proof_harness.py`
- What it proves:
  - structured Hermes-path proof report with `modes` and per-scenario outputs
  - honest builtin-only baseline instead of fake model-only comparison
  - token/replay proof reporting
  - deterministic local LongMemEval-style subset verification

### Tier 4: External Benchmark Gate

- Status: Pending external run
- Gate:
  - Paid LongMemEval-10 through the Hermes path
- Why it remains separate:
  - this repo now has the local proof infrastructure and synthetic subset gate
  - the paid external run is still the final acceptance gate before a stronger SOTA-style claim

## Current Commands

- `PYTEST_ADDOPTS='' .venv/bin/python -m pytest -n 0 tests/agent/test_core2_plugin_loading.py tests/agent/test_core2_provider_foundation.py tests/agent/test_core2_legacy_adapted.py tests/agent/test_core2_retrieval_routing.py tests/agent/test_core2_answer_contract.py tests/agent/test_core2_abstention_delivery.py tests/agent/test_core2_memory_manager_e2e.py tests/agent/test_core2_proof_harness.py tests/agent/test_core2_hardening.py`
- `.venv/bin/python -c "from agent.core2_proof_harness import run_core2_proof_benchmark; print(run_core2_proof_benchmark().as_dict())"`
- `.venv/bin/python -c "from agent.core2_proof_harness import verify_core2_longmemeval_subset; print(verify_core2_longmemeval_subset(sample_size=2, seed=7))"`

## Final Gate

The final gate is not the local synthetic subset. The final gate is the paid LongMemEval-10 run.
