# Phase 9 Verification

## Build Verification

- Core2 now has a bounded ranking helper in `agent/core2_ranking.py`
- hybrid candidate ordering now uses bounded ranking signals in `agent/core2_hybrid_substrate.py`
- the borrow stayed within the planned seam and did not import render, claim-guard, comparator, or family-growth work

## Targeted Proof

- command:
  - `./.venv/bin/python -m pytest tests/agent/test_core2_retrieval_ranking.py tests/agent/test_core2_hybrid_substrate.py -q`
- result:
  - `7 passed in 0.35s`

## Wider Regression

- command:
  - `./.venv/bin/python -m pytest tests/agent/test_core2_*.py -q`
- result:
  - `133 passed in 12.49s`

## Canonical Outcome

See:
- `09-LOCAL-OUTCOME.json`
- `09-VERDICT.md`

## UAT

- UAT completed in `09-UAT.md`
- ranking-boundary acceptance passed
- targeted ranking proof acceptance passed
- wider regression stability passed
