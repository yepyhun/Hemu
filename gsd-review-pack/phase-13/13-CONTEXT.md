# Phase 13: Bounded Aggregate-Temporal Retrieval Coverage Expansion

## Phase Boundary

Phase 13 is a bounded retrieval-side build. It starts from the verified `v1.6/12` map that showed the dominant residual gap is `weak_or_partial_evidence` (`15/33`) inside the frozen retrieval-dominant subset.

This phase does **not** reopen generic ranking, delivery bridging, broad family growth, or substrate replacement. It attempts one retrieval-side mechanism only: better constituent-anchor coverage for aggregate-temporal question shapes that are already supported in principle.

## Locked Decisions

### What This Phase Must Do

- freeze the Phase 12 `weak_or_partial_evidence` target slice
- define the exact supported aggregate-temporal shapes to target
- implement one bounded constituent-anchor retrieval expansion inside the existing retrieval seam
- prove the local effect on the mapped target slice before any broader rerun is considered
- end with one canonical local outcome and one explicit go/no-go verdict

### What This Phase Must Not Do

- no retrieval-ranking reintroduction
- no delivery/prompt-path work
- no new ontology/family expansion
- no comparator or judge handling changes
- no broad paid rerun inside this phase
- no widening into the `wrong_subset_selection` bucket during implementation

## Prior Evidence That Must Be Preserved

- `v1.5/11` showed the hard residual `38` is retrieval-dominant (`33/38`)
- `v1.6/12` reduced the dominant retrieval bucket to `weak_or_partial_evidence` (`15/33`)
- the carry-forward next direction is `Bounded Aggregate-Temporal Retrieval Coverage Expansion`
- the stop rule from `v1.6` forbids reopening multiple retrieval bets at once

## Required Canonical Artifacts

- `13-TARGET-SLICE-MANIFEST.json`
- `13-SHAPE-BOUNDARY.md`
- `13-LOCAL-OUTCOME.json`
- `13-VERDICT.md`

## Success Criteria

- the build stays strictly inside aggregate-temporal retrieval coverage for the frozen target slice
- local proof shows stronger constituent-anchor assembly on the target slice
- no regression is introduced in wider Core2 local regression
- the phase ends with one clear verdict on whether this was the right next build

## Anti-Loop Rule

If local proof does not show meaningful improvement on the frozen target slice, do **not** broaden the phase into subset-selection, delivery, ranking, or a paid rerun. Record the failure and stop.
