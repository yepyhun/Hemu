# Phase 13 Research

## Objective

Convert the dominant `weak_or_partial_evidence` bucket from Phase 12 into one bounded retrieval build, without reopening the rest of the retrieval stack.

## What Phase 12 Already Settled

- the next build should be retrieval-side, not delivery-side
- the dominant miss shape is not generic ranking
- the largest bucket is questions that need multiple constituent facts or anchors co-retrieved before safe answer composition
- the secondary `wrong_subset_selection` bucket exists, but it is not the current build target

## Working Build Hypothesis

The current retrieval seam does not deliberately gather enough constituent anchors for aggregate-temporal questions. It retrieves a compact packet, but for some shapes the packet is too thin to support:

- aggregate totals
- elapsed-time and days-ago questions
- ratio / percentage / average questions
- pairwise relative-order questions that still require two explicit anchors

The bounded fix is therefore a **constituent-anchor retrieval expansion** for these shapes, not a new ranking system and not a new family layer.

## Supported Target Shapes

- `aggregate_total`
- `temporal_delta`
- `days_ago`
- `ratio_percentage_average`
- `pairwise_anchor_compare`

## Why This Must Stay Bounded

If the phase also touches:
- subset-selection misses
- recommendation-style unsupported families
- delivery bridge behavior
- ranking / scoring heuristics

then the resulting gain will become uninterpretable again.

## Required Observability Shape

The local outcome must record:
- frozen target slice size
- targeted shape counts
- whether constituent-anchor assembly improved
- whether answer-surface availability improved on the frozen slice
- whether wider local regression remained green

## Stop Rule

If the bounded build cannot improve the frozen target slice locally without widening scope, stop and record a `no-go` verdict instead of reopening adjacent hypotheses.
