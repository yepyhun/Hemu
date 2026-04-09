# Phase 17 Research

## Objective

Turn the verified `retrieval_failure` bucket into one selection-focused follow-up instead of another broad retrieval milestone.

## What Phase 16 Already Settled

- the hard residual replay did not produce a breakthrough
- `retrieval_failure` is still dominant on the frozen hard `38`
- two of the three raw passes are judge-false-positive cases, so grounded progress must stay strict

## Working Retrieval-Selection Taxonomy

### `wrong_subset_selection`

Relevant evidence exists in principle, but the recalled packet is composed from the wrong constituents or wrong anchors.

### `partial_constituent_packet`

Some answer-bearing evidence is present, but the selected packet is incomplete for the query operator or comparison shape.

### `anchor_priority_miss`

The retrieval packet prefers weaker or less useful anchors over the anchors that would make the question executable.

### `no_answer_bearing_selection`

The active path selects a packet that contains no answer-bearing evidence at all.

## Why This Must Stay Diagnostic

The previous phases already proved that broad “maybe retrieval in general” reasoning is too loose. This phase should identify which miss shape actually dominates before any new build is promoted.

## Selector Research Slice To Reuse

The most relevant research carry-forward is still:

1. evidence selector + slot/operator coverage logic
2. aggregation safety rules

But in this phase they are used only as diagnostic lenses, not as a build commitment.

## Stop Rule

If the selection taxonomy does not produce one clearly dominant actionable miss shape, do not promote a new build from this phase.
