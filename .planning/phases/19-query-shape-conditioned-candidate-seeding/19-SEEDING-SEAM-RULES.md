# Phase 19 Seeding Seam Rules

## Engagement Criteria

For Phase 19, a decomposition-and-seeding stack counts as engaged only if at least one of these happens on the frozen target slice or its representative local proofs:

1. `evidence_present_cases` moves upward
2. `sufficient_retrieval_cases` moves upward
3. explicit seed-opening traces appear for the expected operator-slot family

## Immediate Falsification

The phase should be treated as not engaged if:

- operator family is never detected
- seed family stays not applicable on the supposed target shape
- seed queries do not open new raw/turn hits
- local proof only adds notes without opening candidates

## Allowed Upstream Moves

- operator-family detection
- bounded slot extraction
- bounded clause rewrites
- bounded temporal anchor seeds
- bounded pairwise comparison seeds
- bounded aggregate operand seeds

## Forbidden Moves

- selector retuning
- delivery reopen
- ranking reopen
- full staged retrieval
- context-tree adoption
- bitemporal/state refactor
- aggregation-safety redesign
- calibrated override-gate work

## Replay Recommendation Rule

Phase 19 may recommend a paid replay only if:

- the stack stays bounded
- at least two representative operator families show local seed-opening proof
- route-note / trace contract remains explicit
- no wider Core2 regressions are introduced
