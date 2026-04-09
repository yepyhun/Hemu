# Phase 19 Operator-Slot Schema

## Purpose

Phase 19 upgrades the old `query_shape_conditioned_candidate_seeding` idea into one bounded decomposition-and-seeding stack.

The stack is allowed to classify only four operator families.

## Operator Families

### `temporal_elapsed`

- arity: `pair`
- required slots:
  - `anchor_earlier`
  - `anchor_later`
- dominant constraints:
  - temporal anchoring
  - ordered pair
- seed family:
  - `temporal_anchor_pair`

Typical shapes:

- `between X and Y`
- `after X`
- `how many days`
- `how long`
- `days ago`

### `aggregate_numeric`

- arity: `pair` or bounded `set`
- required slots:
  - `operand_left`
  - `operand_right`
  - or one bounded `operand_set`
- dominant constraints:
  - numeric executability
  - scope compatibility
- seed family:
  - `aggregate_operand_seed`

Typical shapes:

- `percentage`
- `percent`
- `ratio`
- `average`
- `total`

### `current_previous`

- arity: `pair`
- required slots:
  - `previous_fact`
  - `current_fact`
- dominant constraints:
  - temporal ordering
  - same identity family
- seed family:
  - `previous_current_seed`

Typical shapes:

- `previous`
- `current vs previous`
- change / earlier-validity comparisons

### `pairwise_compare`

- arity: `pair`
- required slots:
  - `operand_left`
  - `operand_right`
- dominant constraints:
  - comparison alignment
  - ordered event or value pair
- seed family:
  - `pairwise_seed`

Typical shapes:

- `which came first`
- `first A or B`
- bounded `more/less` comparisons

## What This Schema Explicitly Does Not Cover

- open-ended graph walking
- full semantic parsing
- count-distinct set construction beyond bounded operand seeds
- full retrieval-stack decomposition
- downstream delivery

## Execute Contract

Phase 19 succeeds only if this schema causes measurable upstream engagement on the frozen target slice:

- more answer-bearing evidence
- or more sufficient retrieval
- or explicit seed-opening traces on representative target families
