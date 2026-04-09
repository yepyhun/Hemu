# Phase 12 Research

## Objective

Turn the `33` retrieval-dominant residual cases into a concrete gap taxonomy that can justify one bounded retrieval-side next step.

## What Phase 11 Already Settled

Phase 11 answered the cross-layer question:
- the hard residual problem is not predominantly delivery

It did **not** answer the retrieval-specific question:
- what kind of retrieval failure is actually dominating inside the `33` retrieval-selection cases?

That is the purpose of Phase 12.

## Working Retrieval Gap Taxonomy

### `no_relevant_evidence`

The replayed recall packet contains no answer-bearing support and no plausible nearby evidence for the question.

### `weak_or_partial_evidence`

The replayed recall packet returns something topically related, but it is too partial or weak to support the answer.

### `wrong_subset_selection`

The system appears to retrieve some relevant memory neighborhood, but the selected compact items omit the answer-bearing part.

### `unsupported_query_family`

The question shape appears retrievable in principle, but the current retrieval/query-family formulation does not map the case into the right retrieval path.

## Why This Must Stay Diagnostic

The project already falsified:
- delivery as the dominant next build direction
- ranking borrow as a breakthrough path

So the next honest step is not another retrieval mechanism guess. It is to learn which retrieval gap shape is dominant enough to justify a bounded build.

## Required Observability Shape

Per case:
- `case_id`
- `question_type`
- `query_family`
- `route_family`
- `evidence_item_count`
- `evidence_present`
- `gap_class`
- `short_reason`
- `retrieval_hints`

## Stop Rule

If the retrieval subset does not show one clearly dominant gap class, the phase must not pretend that one retrieval build is obviously correct.
