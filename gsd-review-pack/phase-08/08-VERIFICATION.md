# Phase 8 Verification

## Build Verification

- bounded bridge implemented at the structured covered-fact eligibility seam
- bridge remains limited to:
  - `fact_first`
  - `hybrid_scoped_turn`
  - `hybrid_scoped_raw`
- plain lexical/semantic structured paths remain blocked

## Local Proof

- targeted proof command:
  - `./.venv/bin/python -m pytest tests/agent/test_core2_authoritative_eligibility_bridge.py tests/agent/test_core2_generic_surface_generalization.py tests/agent/test_core2_hybrid_substrate.py tests/agent/test_core2_handmade_acceptance.py -q`
- result:
  - `28 passed in 6.54s`

## Wider Regression

- regression command:
  - `./.venv/bin/python -m pytest tests/agent/test_core2_*.py -q`
- result:
  - `125 passed in 12.37s`

## Canonical Outcome

See:
- `08-LOCAL-OUTCOME.json`
- `08-VERDICT.md`
- `08-NEXT-STEP.md`

## UAT

- UAT completed in `08-UAT.md`
- representative bridge behavior passed
- wider regression stability passed
