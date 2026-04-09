# Phase 15 Attribution Schema

## Purpose

Define one bounded per-case attribution row for Core2 diagnostics without opening a second trace universe.

## Stable Per-Case Fields

- `question_id`
- `question_type`
- `passed`
- `judge`
- `failure_pattern`
- `attribution_label`
- `stage_bucket`
- `recall_route_family`
- `recall_query_family`
- `route_notes`
- `evidence_item_count`
- `evidence_contains_answer`
- `answer_surface_hit`
- `answer_surface_mode`
- `answer_surface_family`
- `promptless_authoritative`
- `selector_engaged`
- `constituent_expanded`
- `aggregation_safety_abstained`
- `recall_abstained`
- `support_confidence`
- `temporal_confidence`
- `resolution_confidence`
- `identity_confidence`
- `local_comparator`
- `local_comparator_reason`
- `sufficient_retrieval`
- `judge_like`
- `short_reason`

## Allowed Labels

- `passed`
- `retrieval_failure`
- `sufficiency_failure`
- `reasoning_failure`
- `delivery_surface_failure`
- `judge_false_positive`
- `judge_false_negative`
- `latency_abort`

## Stage Buckets

- `passed`
- `retrieval`
- `sufficiency`
- `reasoning_delivery`
- `judge_like`
- `latency`

## Classification Rules

- `latency_abort` wins first if the case stopped on latency.
- `judge_false_positive` is reserved for passed cases with no grounded evidence, no authoritative answer surface, and a positive judge verdict.
- `judge_false_negative` is reserved for `judge_artifact`.
- `retrieval_failure` is used when answer-bearing evidence never surfaced.
- `sufficiency_failure` is used when answer-bearing evidence surfaced but did not yield an authoritative surface.
- `delivery_surface_failure` is used when grounded evidence and authoritative surface existed but downstream handoff/prompt delivery still failed.
- `reasoning_failure` is the bounded residual bucket for remaining downstream misses after grounded retrieval.

## Minimal Metric Surface

- `label_counts`
- `stage_counts`
- `evidence_present_cases`
- `sufficient_retrieval_cases`
- `answer_surface_hit_cases`
- `selector_engaged_cases`
- `aggregation_safety_abstentions`
- `judge_like_cases`
- `evidence_present_rate`
- `sufficient_retrieval_rate`
- `answer_surface_hit_rate`
- `selector_engaged_rate`

## Reused Inputs

- benchmark result rows from `core2_longmemeval_benchmark.py`
- `route_plan.notes`
- bounded confidence fields already present on compact recall packets
- earlier diagnostic artifacts from `v1.5/11` and `v1.6/12`

## Explicit Non-Goals

- no retrieval selector widening
- no delivery bridge work
- no bitemporal remodeling
- no promotion-gate implementation
- no comparator or judge rewrite
