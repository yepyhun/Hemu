# Phase 14 Research

## Objective

Translate the jackpot research into one bounded Core2 build that targets the current real bottleneck: weak or partial evidence for compositional aggregate-temporal questions under a strict budget.

## What Earlier Phases Already Settled

- the next build should remain retrieval-side, not delivery-side
- generic ranking is not the main residual answer
- the dominant residual shape is compositional aggregate-temporal evidence insufficiency
- constituent-anchor expansion is a real mechanism, but only on a safe tranche
- plain current-total aggregate shapes must remain excluded for now

## Working Build Hypothesis

The next meaningful improvement is not more retrieval breadth but better **set selection**:

- pick evidence as a budgeted set rather than independent top items
- reward slot/operand coverage across the selected set
- penalize redundancy and unsafe composition
- abstain when the evidence set remains partial or incompatible

## Bounded Selector Feature Set

The initial feature set must stay small and implementation-oriented:

- `query_relevance`
- `operator_fit`
- `slot_coverage_gain`
- `supporting_fact_strength`
- `provenance_strength`
- `temporal_completeness`
- `numeric_executability`
- `redundancy_penalty`
- `token_cost`

Deferred for later unless Phase 14 proves out:

- full diversity machinery
- calibrated promotion gating
- bitemporal state remodeling

## Narrow Aggregation Safety Rules

The phase may add only the minimum explicit safety needed for honest composition:

- identity-key dedupe before aggregation
- unit compatibility checks
- scope compatibility checks
- time-window compatibility checks
- partial evidence => abstain

## Supported Target Shapes

- temporal delta / elapsed
- days total / days ago
- ratio / percentage / average
- pairwise delta / anchor compare

## Explicitly Excluded Shapes

- plain current-total count / money
- open-ended local sequence lookup
- recommendation-style unsupported prompts

## Required Observability Shape

The local proof should emit enough selector-side evidence to answer:

- did slot coverage improve?
- did the retrieved set become more executable for the operator?
- did aggregation safety reject unsafe composition cleanly?

## Stop Rule

If Phase 14 cannot show a clearer sufficiency signal on the bounded tranche, do not widen the selector or stack more research imports into the same phase.
