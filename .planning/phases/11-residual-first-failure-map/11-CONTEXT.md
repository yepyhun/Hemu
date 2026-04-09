# Phase 11: Residual First-Failure Map - Context

**Gathered:** 2026-04-08
**Status:** Planned

## Phase Boundary

Phase 11 is a diagnostic-only phase for the frozen hard residual `38` set. It must classify the first true failure point per case and decide whether there is one dominant bottleneck worth building against next.

This phase does **not** implement a new mechanism. It exists to prevent another premature build bet after several bounded hypotheses already failed to deliver a breakthrough on the hard residual slice.

## Locked Decisions

### What This Phase Must Do

- freeze the exact hard residual `38` case manifest used for diagnosis
- define a canonical per-case observability schema
- classify the first true failure point for each case
- aggregate the dominant buckets across the full set
- end with one canonical verdict:
  - `delivery-dominant`
  - `retrieval-dominant`
  - `handoff-dominant`
  - `judge-dominant`
  - `mixed/no-single-bottleneck`
- carry forward at most one bounded next-direction recommendation or one explicit stop rule

### What This Phase Must Not Do

- no new runtime behavior
- no delivery bridge implementation
- no new retrieval/ranking work
- no comparator changes
- no family growth
- no broad or paid benchmark rerun
- no per-case benchmark patching

## Prior Evidence That Must Be Preserved

- `v1.1/06` broader frozen comparison:
  - baseline `31/70`
  - hybrid `32/70`
  - verdict remained honest: directionally better, not enough for automatic promotion
- `v1.2/08` authoritative eligibility bridge showed local route-shift, but did not deliver a hard residual breakthrough
- `v1.2/08.1` invariants + narrow noise repair improved hardening quality, but did not improve the hard residual `38` replay
- `v1.3/09` ranking borrow was locally green, but the later paid residual replay regressed from `3/38` to `2/38`
- `v1.4/10` rolled ranking back and left `Covered-Family Prompt Delivery Bridge` as a carry-forward recommendation only, not as a committed build

## Required Canonical Artifacts

- `11-RESIDUAL-MANIFEST.json`
- `11-CASE-TRANSITIONS.jsonl`
- `11-FIRST-FAILURE-RULES.md`
- `11-OUTCOME.json`

## Success Criteria

- the phase produces a complete per-case first-failure map for the frozen `38`
- bucket definitions are explicit enough that a later reader can audit why each case was classified the way it was
- the milestone ends with one clear next-direction recommendation or stop rule

## Anti-Loop Rule

If the phase cannot classify cases cleanly enough to support one dominant verdict, the correct outcome is `mixed/no-single-bottleneck`, not a speculative new build.
