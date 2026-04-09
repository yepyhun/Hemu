# Phase 12 Gap Taxonomy

This taxonomy stays retrieval-side only. It classifies why the frozen `33` retrieval-dominant residual cases miss *before* any new runtime build is chosen.

## Classes

### `weak_or_partial_evidence`
Use this when the question needs multiple constituent facts, dates, values, or timeline anchors, but the compact recall packet appears too thin to compose the answer safely.

Typical shapes:
- aggregate totals
- elapsed-time or days-ago questions
- ratio / percentage / average questions
- pairwise relative-order questions that still depend on two explicit anchors

### `wrong_subset_selection`
Use this when the answer likely exists as a narrow durable fact or episode, but the compact recall packet selects the wrong shard or fails to include the relevant one.

Typical shapes:
- stable single fact lookups
- named place / named company reminders
- specific item reminders
- narrow pairwise ordering where one event anchor is simply missing

### `no_relevant_evidence`
Use this when the frozen case is fundamentally an abstention / unsupported fact request and the source trace does not ground the required fact at all.

Typical shapes:
- explicit abstention variants
- questions whose missing fact never appears in the memory trace

### `unsupported_query_family`
Use this when the request shape is preference-grounded open-ended recommendation or synthesis, not a currently covered hard retrieval family.

Typical shapes:
- recommendation prompts
- open-ended planning prompts that depend on preference synthesis instead of direct fact lookup

## Aggregate Reading

- `weak_or_partial_evidence`: 15
- `wrong_subset_selection`: 11
- `no_relevant_evidence`: 4
- `unsupported_query_family`: 3

Interpretation:
- the dominant miss shape is not generic delivery, and not generic ranking
- the largest residual bucket still needs better retrieval coverage for aggregate / temporal / multi-anchor questions
- unsupported recommendation-style prompts are present, but clearly not the dominant next build target
