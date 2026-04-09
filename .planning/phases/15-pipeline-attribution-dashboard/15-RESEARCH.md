# Phase 15 Research

## Objective

Translate the pipeline attribution part of the jackpot research into one bounded Core2 diagnostics layer.

## What Earlier Phases Already Settled

- the main residual problem is retrieval-side, not delivery-side
- aggregate benchmark totals alone are not enough to choose the next bounded build
- per-case evidence was already useful in `v1.5/11` and `v1.6/12`
- selector-side observability now exists after `v1.8/14`

## Working Build Hypothesis

The highest-value next step is not another build mechanism but a clearer attribution contract:

- retrieval failure
- sufficiency failure
- reasoning/delivery failure
- judge-like artifact outcome

This should let future phases and reruns answer "what failed first and why?" without hand-reading mixed outputs.

## Bounded Attribution Contract

The first version must stay small and implementation-oriented:

- per-case row format
- stable failure bucket labels
- a small metric surface for sufficiency and selector behavior
- no attempt to solve all future evaluation needs in one pass

## Recommended Per-Case Labels

- `retrieval_failure`
- `sufficiency_failure`
- `reasoning_failure`
- `delivery_surface_failure`
- `judge_false_positive`
- `judge_false_negative`

## Recommended Metric Surface

Retrieval-side:

- `SupportFactRecall@B`
- `SlotRecall@B`
- `EvidenceCoverage@B`
- `TemporalCoverage@B`
- `ProvenanceCoverage@B`
- `RedundancyRate@B`
- `SelectorEfficiency`

Downstream:

- `AnswerAccuracy`
- `AnswerAccuracy|GoldRetrieved`
- `AnswerAccuracy|SufficientRetrieved`
- `GroundedAnswerRate`
- `OperatorExecutionAccuracy`
- `TemporalReasoningAccuracy`
- `AggregationSafetyErrorRate`
- `AbstentionQuality`

## Existing Reusable Inputs

- `11-CASE-TRANSITIONS.jsonl`
- `12-COVERAGE-TRANSITIONS.jsonl`
- `14-LOCAL-OUTCOME.json`
- route-plan notes from runtime
- bounded phase-local proof outcomes

## Stop Rule

If the attribution schema starts to demand a full benchmark rewrite or a new truth model, stop. Phase 15 must end with a reusable contract, not a new subsystem empire.
