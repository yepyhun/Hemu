# Phase 16: Attributed Hard Residual Replay

## Phase Boundary

This phase applies the new `v1.9/15` attribution contract to one real frozen hard residual replay.

It must:

- reuse the existing hard `38` question set instead of inventing a new sample
- emit per-case attribution rows plus one canonical attributed replay outcome
- use the current active hybrid path exactly as it exists after the ranking rollback and later retrieval-side work
- reduce the next forward decision to one bounded build or one explicit stop rule

It must **not**:

- build a new retrieval mechanism inside this phase
- reopen ranking, delivery, bitemporal, or promotion-gate work
- redefine the hard residual set after the replay starts
- broaden into a second diagnostics framework

## Locked Decisions

### What This Phase Must Do

- freeze the replay manifest from the canonical hard residual reference
- run one bounded attributed replay over that frozen set
- produce one canonical attributed status/outcome pair
- preserve enough per-case detail to make the next build choice evidence-driven

### What This Phase Must Not Do

- no new selector changes
- no new aggregate-temporal widening
- no delivery bridge work
- no benchmark threshold-moving
- no alternate replay subsets in parallel

## Prior Evidence That Must Be Preserved

- `v1.5/11` established that the hard residual `38` is locally retrieval-dominant
- `v1.6/12` established that the dominant retrieval gap is `weak_or_partial_evidence`
- `v1.8/14` improved selector + aggregation safety on the safe aggregate-temporal tranche
- `v1.9/15` delivered the reusable attribution contract that now needs one real replay application

## Canonical Frozen Source

Use the hard `38` replay question IDs from:

- `08.1-HYBRID-RETEST-38-STATUS.json`

Reason:

- it is the canonical `3/38` hard residual reference before the failed ranking borrow regressed to `2/38`
- it preserves the same hard residual population later phases reasoned over
- it avoids smuggling the failed ranking path in as the new baseline for attribution work

## Required Canonical Artifacts

- `16-REPLAY-MANIFEST.json`
- `16-ATTRIBUTED-STATUS.json`
- `16-ATTRIBUTED-OUTCOME.json`

## Success Criteria

- the hard `38` replay scope is frozen explicitly
- the replay emits the phase-15 attribution contract per case
- the final outcome names the dominant live buckets on the current active path
- the next direction is reduced to one bounded follow-up or one explicit stop rule

## Anti-Loop Rule

If the replay completes but the attributed outcome is still mixed without one dominant actionable bucket, stop at the canonical outcome. Do not quietly open multiple new build threads from the same replay.
