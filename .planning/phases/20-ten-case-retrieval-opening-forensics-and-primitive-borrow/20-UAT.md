# Phase 20 UAT

## Scope

Verify that `Phase 20` completed the promised bounded ten-case forensic-plus-borrow milestone honestly:
- freeze one representative fixed `10`-case hard slice
- codemap narrow legacy primitives only
- borrow at most one primitive family
- replay the same fixed `10`
- end with one canonical verdict even if that verdict is negative

## Acceptance Checks

- a fixed representative `10`-case manifest exists
- a borrow-boundary artifact exists and keeps the phase narrow
- a legacy codemap exists and names only helper-level primitives as borrowable
- the borrowed primitive family is integrated cleanly and proven locally
- the same fixed `10`-case replay was run externally to completion
- the phase records one canonical external verdict without inflating local proof into benchmark success

## Result

- fixed representative `10`-case manifest: present
- borrow boundary and legacy codemap: present
- borrowed primitive family: `legacy_query_signal_primitives`
- local proof:
  - `10 passed`
  - `4 passed`
  - `3 passed`
  - `156 passed`
- external fixed-ten replay:
  - `0/10`
  - `retrieval_failure: 8`
  - `sufficiency_failure: 1`
  - `delivery_surface_failure: 1`
  - `selector_engaged_cases = 0`
- canonical verdict recorded: yes, `needs_work`

## Verdict

Verified.

The phase contract was satisfied:
- the forensic slice was frozen
- the borrow stayed narrow
- the external replay completed on the fixed slice
- the negative result was recorded honestly

This is a verified negative milestone outcome, not a positive benchmark improvement.
