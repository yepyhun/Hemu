# Phase 11 Research

## Objective

Determine the smallest diagnostic artifact set that can falsify the current carry-forward recommendation before another mechanism is built.

## What The Existing Evidence Already Says

- retrieval-side interventions have already had their chance:
  - bounded hybrid substrate improved broader comparison only slightly
  - ranking borrow did not survive the hard residual replay
- hardening-side interventions also had their chance:
  - invariants and noise repair were worth keeping, but did not move the hard residual count
- the dominant named residual bucket is still `prompt_miss`

This is enough to justify a diagnostic milestone, but **not** enough to justify building a delivery bridge yet.

## Working Hypothesis

The remaining uncertainty is no longer "is the architecture good in theory?" It is "where does each hard residual case actually fail first?"

The only honest way to answer that is a per-case map that separates:

- retrieval/selection miss
- structured route unavailable
- delivery/prompt-path miss
- handoff-format miss
- judge artifact

## Why This Phase Must Stay Diagnostic

The project has already spent several bounded bets on plausible mechanisms:

- authoritative eligibility bridge
- invariants + acceptance harness
- narrow noise repair
- retrieval ranking borrow

Those bets were not random, but enough of them failed on the hard residual slice that the next step must be diagnosis first, not another intuition-first build.

## Canonical Buckets

### Retrieval/Selection Miss

The needed support is not present in the retrieved evidence bundle, or the selected evidence bundle is clearly insufficient before delivery even begins.

### Structured Route Unavailable

The evidence exists, but there is no available covered-family structured route that can plausibly own the answer.

### Delivery/Prompt-Path Miss

Evidence is present and a covered route is available, but the final answer path does not convert that into a correct answer or fail-closed abstention.

### Handoff-Format Miss

The answer path reaches the right region, but the emitted structure/format causes the miss.

### Judge Artifact

The result appears semantically acceptable or bounded by benchmark ambiguity, but the miss is dominated by evaluator behavior rather than a clear kernel failure.

## Required Observability Shape

The smallest useful artifact is a per-case transition ledger:

- `case_id`
- `query_family`
- `evidence_present`
- `covered_route_available`
- `selected_candidate_ids`
- `answer_surface_hit`
- `promptless_authoritative`
- `first_failure_stage`
- `failure_bucket`
- `previous_verdict`
- `new_verdict`
- `short_reason`

## Stop Rule

If the per-case map does not show one clearly dominant bucket, the milestone must end with `mixed/no-single-bottleneck` and must not force a build phase out of weak evidence.
