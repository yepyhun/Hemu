# Phase 10 UAT

## Scope Acceptance

### 1. Ranking is removed from the active hybrid path
- Result: PASS
- Evidence:
  - `agent/core2_hybrid_substrate.py` no longer imports or uses `agent/core2_ranking.py`
  - `10-LOCAL-OUTCOME.json` records `ranking_active_in_hybrid_path: false`

### 2. Earlier hardening remains intact
- Result: PASS
- Evidence:
  - `10-LOCAL-OUTCOME.json` records preserved hardening: invariants, noise repair, bounded hybrid substrate
  - wider Core2 regression stayed green

### 3. Rollback is locally proven and regression-safe
- Result: PASS
- Evidence:
  - targeted rollback proof: `7 passed in 0.36s`
  - wider regression: `133 passed in 14.30s`

### 4. Canonical postmortem exists and is honest
- Result: PASS
- Evidence:
  - `10-REGRESSION-FACTS.json` records the `3/38 -> 2/38` regression
  - `10-POSTMORTEM.md` explicitly concludes that ranking borrow is not the breakthrough path

### 5. The phase ends with exactly one bounded next direction
- Result: PASS
- Evidence:
  - `10-NEXT-DIRECTION.md` names only `Covered-Family Prompt Delivery Bridge`

## UAT Verdict

Phase 10 is accepted. The ranking borrow has been retired from the active hybrid path, the rollback is locally verified, and the milestone now carries one bounded next-direction recommendation only.
