# Phase 19: Query-Shape Conditioned Candidate Seeding - Context

## Phase Boundary

This phase exists to follow up the verified `v1.12/18` carry-forward, but it must do so under a stricter external truth than the original narrowing phase had:

- canonical paid hard replay: `3/38`
- `retrieval_failure`: `29/38`
- `sufficient_retrieval_cases`: `2/38`
- `answer_surface_hit_cases`: `6/38`
- `selector_engaged_cases`: `0/38`
- `aggregation_safety_abstentions`: `0/38`

So the phase must not assume that query-shape-conditioned seeding is already a proven forward path. It must first prove that a bounded decomposition-driven seeding stack can touch the real hard bucket at all.

The phase stays strictly upstream of selector choice and downstream answer delivery. It does not reopen delivery, ranking, broad retrieval redesign, bitemporal remodeling, aggregation-safety redesign, or promotion-gate work.

## Locked Questions This Phase Must Answer

### What This Phase Must Answer

- which exact frozen subset of the hard `29` retrieval-failure cases is homogeneous enough for one decomposition-and-seeding family
- what missing upstream seed objects explain that subset
- whether the missing seed is lost at query opening, candidate admission, or another even earlier seam
- what measurable artifact movement would prove that the mechanism engaged the real bottleneck

### What This Phase Must Not Pretend To Answer

- no claim of broad benchmark improvement from local proof alone
- no claim that staged retrieval or context-tree systems should be adopted wholesale
- no claim that selector tuning, delivery work, or promotion-gate work are the next moves

## Locked Decisions

### What This Phase Must Do

- preserve the canonical `29`-case upstream subset and the `21/29` carry-forward family from `v1.12/18`
- reinterpret that carry-forward under the fresh paid hard replay truth
- reduce the phase to one bounded upstream decomposition-and-seeding stack or one explicit stop rule
- explicitly formalize:
  - operator
  - arity
  - slots
  - query rewrites
  - temporal/comparison/aggregate seed families
- define success in terms of evidence movement, not only code-local correctness

### What This Phase Must Not Do

- no new paid replay inside the phase by default
- no full staged retrieval architecture
- no context-tree adoption
- no full retrieval-stack decomposition across the stack
- no selector retuning or delivery reopen

## Prior Evidence That Must Be Preserved

- `v1.10/16` proved the hard residual replay remains dominated by `retrieval_failure`
- `v1.11/17` proved the hard replay miss is upstream of selector engagement
- `v1.12/18` reduced the next move to `query_shape_conditioned_candidate_seeding` across `21/29` cases
- the fresh paid replay on the current path still stayed at `3/38` and did not show selector/safety engagement
- `v1.13` must not repeat the old mistake of treating a carry-forward as build-proof

## Required Canonical Artifacts

- `19-TARGET-SUBSET-MANIFEST.json`
- `19-OPERATOR-SLOT-SCHEMA.md`
- `19-SEEDING-SEAM-RULES.md`
- `19-SEEDING-TRANSITIONS.jsonl`
- `19-OUTCOME.json`

## Success Criteria

- one frozen target subset exists inside the verified hard `29`
- one explicit engagement criterion exists:
  - `evidence_present_cases` must move on the target subset, or
  - `sufficient_retrieval_cases` must move on the target subset, or
  - the mechanism must produce explicit upstream seed-opening traces on the target subset
- one bounded upstream decomposition-and-seeding stack is specified with explicit exclusions
- the phase ends with either:
  - a replay-worthy recommendation, or
  - a stop rule that says the seeding seam is still not the real bottleneck

## Anti-Loop Rule

Local green tests, new route notes, or prettier traces do not count as success by themselves. The phase only succeeds if it makes the hard bucket more answer-bearing on a frozen subset, or if it cleanly falsifies seeding as the next worthwhile seam.
