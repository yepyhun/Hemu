# Retrieval Selector And Temporal Kernel Notes

This note captures externally researched directions that appear highly relevant to the current Core2 bottlenecks.

It is a reference note, not yet an accepted implementation plan.

## Why This Matters Now

The current verified residual analysis says:

- the dominant remaining problem is retrieval-side, not delivery-side
- within retrieval, the main bucket is weak or partial evidence for compositional questions
- Phase 13 showed that bounded constituent-anchor expansion is a real mechanism, but only for a safe tranche

The strongest research-backed next ideas therefore are the ones that:

- improve evidence selection under a strict token budget
- make aggregation safer
- separate retrieval failure from downstream reasoning or judge noise

## Highest-Value Immediate Directions

### 1. Budgeted Evidence Selection

The strongest immediate match is a budgeted evidence selector that chooses a jointly sufficient evidence set instead of naïve top-k retrieval.

Recommended evidence-item feature set:

- `query_relevance`
- `operator_fit`
- `slot_coverage_gain`
- `supporting_fact_strength`
- `provenance_strength`
- `temporal_completeness`
- `entity_binding_quality`
- `numeric_executability`
- `diversity_gain`
- `redundancy_penalty`
- `conflict_penalty`
- `token_cost`

Recommended selection objective:

```text
Gain(e | S, q) =
  α * query_relevance
+ β * operator_fit
+ γ * slot_coverage_gain
+ δ * provenance_strength
+ ε * temporal_completeness
+ ζ * numeric_executability
+ η * diversity_gain
- λ * redundancy_penalty
- μ * conflict_penalty
```

Selection rule:

```text
choose e* = argmax Gain(e | S, q) / token_cost(e)
subject to total_token_cost(S) <= B
```

This points toward a budgeted submodular / maximum-coverage style selector rather than plain ranking.

### 2. Aggregation Safety

Current-total and aggregate-like questions remain fragile. The research strongly supports adding explicit aggregation safety rules:

- identity-key dedupe before aggregation
- unit compatibility checks
- scope compatibility checks
- time-window compatibility checks
- partial evidence => abstain

This is especially relevant for:

- `count`
- `sum`
- `difference`
- `average`
- `temporal_delta`

### 3. Pipeline Attribution Metrics

A useful benchmark/dashboard split should measure these layers separately:

- retrieval
- sufficiency
- reasoning
- delivery
- judge artifact

Recommended retrieval-side metrics:

- `SupportFactRecall@B`
- `SlotRecall@B`
- `EvidenceCoverage@B`
- `TemporalCoverage@B`
- `ProvenanceCoverage@B`
- `RedundancyRate@B`
- `SelectorEfficiency`

Recommended downstream metrics:

- `AnswerAccuracy`
- `AnswerAccuracy | GoldRetrieved`
- `AnswerAccuracy | SufficientRetrieved`
- `GroundedAnswerRate`
- `OperatorExecutionAccuracy`
- `TemporalReasoningAccuracy`
- `AggregationSafetyErrorRate`
- `AbstentionQuality`

Recommended diagnostic labels per case:

- `retrieval_failure`
- `sufficiency_failure`
- `reasoning_failure`
- `delivery_surface_failure`
- `judge_false_positive`
- `judge_false_negative`

## Valuable, But Not Immediate

### Bitemporal + Supersession Core

This looks like the right long-term formal core for:

- `current`
- `previous`
- `superseded`
- `conflicting`

Suggested minimal fact fields:

- `entity_id`
- `relation_type`
- `value_normalized`
- `identity_key`
- `valid_from`
- `valid_to`
- `recorded_at`
- `source_id`
- `source_created_at`
- `support_level`
- `status`
- `supersedes_fact_id`
- `conflict_group_id`

Useful later extension:

- explicit edge table for `supersedes`, `conflicts_with`, `derived_from`, `supports`

This is likely correct architecturally, but broader than the next bounded step.

### Promotion Gate / Selective Prediction

A calibrated promotion gate is still valuable, but it is not the highest-leverage next move while retrieval coverage remains the dominant bottleneck.

Recommended shape later:

1. hard filters
   - temporal consistency
   - unit/scope compatibility
   - dedupe pass
   - no unresolved conflict
2. calibrated correctness score
3. risk-specific thresholds
4. abstain by default

## Recommended Practical Order

If turning this research into Core2 work, the most sensible order is:

1. evidence selector + slot/operator coverage logic
2. aggregation safety rules
3. benchmark attribution dashboard
4. later: bitemporal kernel tightening
5. later: calibrated promotion gate

## Main Warning

Do **not** import this whole stack at once.

The value here is not in widening the project with many new subsystems. The value is in using these ideas to define one bounded next build at a time.
