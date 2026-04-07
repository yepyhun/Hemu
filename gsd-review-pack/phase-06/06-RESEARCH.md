# Phase 6: Baseline Versus Hybrid Evaluation - Research

## User Constraints

- No hidden implementation during comparison.
- No threshold changes after results are seen.
- No changing the sample after the broader contract is frozen.
- Keep the result machine-readable and decision-ready for Phase 7.

## What This Phase Actually Authorizes

Phase 6 authorizes only:

1. defining and freezing the serious broader `70`-sample comparison manifest for this phase
2. running the baseline variant under that frozen manifest
3. running the hybrid variant under the same frozen manifest
4. producing canonical baseline, hybrid, and comparison outcome artifacts
5. classifying residual risk without opening a new fix loop

It does **not** authorize:

- changing `agent/core2_*`
- changing the benchmark harness
- changing the hybrid seam
- changing question ids, thresholds, or verdict precedence after execution starts

## Recommended Evaluation Shape

Use the Phase 5 protocol discipline and schema as the source of truth for how this phase behaves, but upgrade the execution scope to a frozen `70`-sample comparison contract before any paid run.

1. freeze the `70`-sample execution manifest for Phase 6
2. prove the baseline local prerequisite and run the baseline branch
3. prove the hybrid local prerequisite and run the hybrid branch
4. normalize both outcomes into the locked schema
5. compute deltas and classify the result into a canonical comparison artifact

## Risks And Failure Modes

- baseline and hybrid accidentally run under different conditions
- the exploratory `20`-sample raw files accidentally get treated as final evidence
- summaries drift away from the canonical comparison artifact
- a mixed result gets overclaimed as promotion
- a regression gets hidden behind retrieval-style gains

## Open Questions

- The only planning-time question left is the exact frozen `70`-sample selection method; once fixed, it must not move.
