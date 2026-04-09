# Phase 17 Selection Taxonomy

## Purpose

This taxonomy classifies the frozen `retrieval_failure` subset from `v1.10/16` without reopening delivery or broad retrieval ideation.

## Canonical Labels

### `no_answer_bearing_selection`

The active path emits a fixed recall packet, but the packet contains no answer-bearing evidence at all.

Evidence signature:
- `evidence_contains_answer = false`
- `sufficient_retrieval = false`
- `selector_engaged = false`
- `route_notes = []`

Interpretation:
- the selector layer never gets a real chance to choose among useful candidates
- the dominant miss sits before or at candidate entry into the selection packet

### `partial_constituent_packet`

The packet contains some answer-bearing evidence, but not enough constituent support to execute the operator.

Evidence signature:
- `evidence_contains_answer = true`
- `sufficient_retrieval = false`

### `anchor_priority_miss`

The packet contains answer-bearing material, but weaker anchors crowd out the anchors needed for execution.

Evidence signature:
- `evidence_contains_answer = true`
- `selector_engaged = true`
- packet still fails to become sufficient

### `wrong_subset_selection`

The packet contains useful candidate material, but the composed subset is the wrong one for the query.

Evidence signature:
- non-empty route notes or selector traces
- answer-bearing material present somewhere in the path
- final packet still misses the executable subset

## Phase 17 Result

Observed counts on the frozen subset:

- `no_answer_bearing_selection`: `29`
- `partial_constituent_packet`: `0`
- `anchor_priority_miss`: `0`
- `wrong_subset_selection`: `0`

Important nuance:

- `2` cases show `answer_surface_hit = true`, but they still carry no answer-bearing evidence and remain in `no_answer_bearing_selection`
- those cases do not justify a delivery or judge pivot; the first actionable miss is still upstream in retrieval packet formation

## Why This Matters

The selector-and-safety tranche from `v1.8` did not engage on this frozen subset. The actionable miss is therefore not “choose better among useful candidates,” but “surface any answer-bearing candidates before bounded selection can matter.”
