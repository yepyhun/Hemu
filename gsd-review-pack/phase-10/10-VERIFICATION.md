# Phase 10 Verification

## Boundary Verification

- ranking is removed from the active hybrid path
- invariants and noise repair remain active
- no new mechanism was introduced during rollback

## Targeted Proof

- command:
  - `./.venv/bin/python -m pytest tests/agent/test_core2_hybrid_candidate_ordering.py tests/agent/test_core2_hybrid_substrate.py -q`
- result:
  - `7 passed in 0.36s`

## Wider Regression

- command:
  - `./.venv/bin/python -m pytest tests/agent/test_core2_*.py -q`
- result:
  - `133 passed in 14.30s`

## Canonical Regression Facts

See:
- `10-REGRESSION-FACTS.json`

## Canonical Outcome

See:
- `10-LOCAL-OUTCOME.json`
- `10-POSTMORTEM.md`
- `10-NEXT-DIRECTION.md`

## Status

Phase 10 execute is verified.

See:
- `10-UAT.md`
