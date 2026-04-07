# Phase 9 Context

## Phase

**09: Retrieval Ranking Borrow**

## Why This Phase Exists

The hybrid branch remains directionally better than the archived baseline, but the gain is still trapped below the final answer path often enough that the broader residual set remains mostly unchanged.

Locked evidence:

- broader comparison: baseline `31/70`, hybrid `32/70`
- dominant residual bucket: `prompt_miss / judge: unknown`
- `08` residual replay: `3/38`
- `08.1` residual replay: `3/38`

This falsifies the authoritative-eligibility bridge and the invariants/noise-repair import as the main remaining breakthrough mechanism.

## Chosen Mechanism

Borrow only a bounded retrieval-ranking layer from the legacy stack into the hybrid path.

Approved signal families:

- scope precedence
- authority
- status
- quality
- freshness
- token-budget-aware compact selection

## Explicitly Out Of Scope

- no new family coverage
- no comparator growth
- no answer-render rewrite
- no claim-guard work
- no substrate reopen
- no truth-model changes
- no broad benchmark rerun inside this phase

## Success Shape

The phase is successful only if the ranking borrow can be shown locally to improve candidate ordering in a way that plausibly attacks the large `prompt_miss` bucket without widening deterministic-core ownership.

## Failure Shape

The phase fails if it turns into general scoring-tuning, per-case rescue logic, or mixed-in render/claim work.
