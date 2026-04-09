# Phase 18 Research

## Objective

Find the smallest upstream-of-selector miss taxonomy that can explain why the hard replay subset never surfaces answer-bearing candidates.

## What Phase 17 Already Settled

- the hard residual replay did not produce a breakthrough
- `retrieval_failure` remains the dominant actionable bucket on the frozen hard `38`
- the `retrieval_failure` subset is selection-homogeneous: `29/29` are `no_answer_bearing_selection`
- the current selector layer never engaged on that subset

## Working Pre-Selector Candidate-Pool Taxonomy

### `query_shape_not_opened`

The active path never opens the right operator, slot, or comparison shape, so answer-bearing candidates are never requested from the upstream pool.

### `entity_scope_binding_miss`

The right answer-bearing evidence likely exists in the broader state, but upstream binding points at the wrong entity, scope, identity cluster, or validity window.

### `temporal_anchor_seed_miss`

The upstream pool never seeds the earlier/later or paired anchors needed to make a temporal, ratio, or compare question answer-bearing.

### `admission_rule_miss`

Relevant facts are present but the upstream candidate-pool rules do not admit them into the pool because the current seam expects the wrong evidence form.

### `unsupported_upstream_shape`

The query shape is genuinely outside the current upstream candidate-pool seam and should end in an explicit stop rule rather than silent broadening.

## Why This Must Stay Diagnostic

The previous milestones already ruled out delivery, ranking, and selector retuning as dominant next moves. This phase exists to identify which upstream miss shape actually dominates before any new build is promoted.

## Research Slice To Reuse

The strongest reusable jackpot research remains:

1. operator + slot decomposition as a diagnostic lens
2. evidence sufficiency / constituent-fact thinking as a diagnostic lens
3. temporal anchor and aggregation safety ideas only where they explain why the candidate pool stays empty

These are lenses for classification here, not a license to implement the full jackpot stack inside this phase.

## Most Relevant Jackpot Carry-Over Into This Phase

The re-read of the jackpot note reinforces three concrete upstream lenses that matter **before** selector engagement:

1. `operator_fit` + `slot_coverage_gain`
   - strongest match for `query_shape_not_opened`
   - use this to test whether the active path never opens the right operator / operand shape at all

2. `entity_binding_quality`
   - strongest match for `entity_scope_binding_miss`
   - use this to test whether the upstream seam points at the wrong entity, scope, identity cluster, or validity window

3. `temporal_completeness` + `numeric_executability`
   - strongest match for `temporal_anchor_seed_miss` and some `admission_rule_miss` cases
   - use this to test whether the pool never admits the paired anchors or executable numeric facts needed to make the query answer-bearing

What the re-read does **not** justify here:

- no full selector rewrite
- no full bitemporal refactor
- no promotion-gate work
- no broad aggregation-safety expansion outside explaining candidate-pool admission failure

## Stop Rule

If the upstream taxonomy does not produce one clearly dominant actionable miss shape, do not promote a new build from this phase.
