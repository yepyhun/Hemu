# Phase 18 Candidate-Pool Taxonomy

## Scope

This taxonomy classifies the frozen `29`-case `no_answer_bearing_selection` subset from `v1.11/17`.

It stays strictly upstream-of-selector:

- no delivery labels
- no ranking labels
- no judge labels
- no broad retrieval redesign claims

## Atomic Upstream Labels

### `temporal_anchor_seed_miss` (`11`)

The query needs paired temporal or numeric anchors to become answer-bearing, but the active path never seeds those anchors into the upstream candidate pool.

Typical shapes:

- `days between`
- `how long`
- `days ago`
- `total amount`
- `percentage`
- `average`

### `query_shape_not_opened` (`10`)

The active path never opens the right operator or comparison shape early enough to request the candidate forms that would make the query answer-bearing.

Typical shapes:

- `which happened first`
- `previous vs current`
- `more or less`
- `count distinct`
- anchored item lookup like `last month`

### `entity_scope_binding_miss` (`3`)

The likely answer-bearing evidence is direct and factual, but upstream binding points at the wrong entity, scope, or identity cluster before the pool is built.

Typical shapes:

- direct attribute lookup
- cross-entity comparison

### `unsupported_upstream_shape` (`3`)

The query is outside the current authoritative candidate-pool seam and should not trigger silent broadening.

Typical shapes:

- open-ended recommendations
- suggestion-style answers rather than authoritative factual recall

### `admission_rule_miss` (`2`)

Relevant prior material exists, but the current upstream rules do not admit that evidence form into the canonical answer-bearing pool.

Typical shapes:

- sequence-specific game state recall
- generated creative artifact recall

## Actionable Family Reduction

The top two atomic labels share one bounded upstream seam:

- `temporal_anchor_seed_miss` (`11`)
- `query_shape_not_opened` (`10`)

Combined actionable family:

- `query_shape_conditioned_candidate_seeding` (`21/29`)

Meaning:

The active path fails to open the right query shape early enough to seed answer-bearing temporal, comparison, or numeric candidates into the pool.

## Residual Non-Dominant Families

- `entity_scope_binding_followup` (`3`)
- `stop_rule_or_non_authoritative_path` (`5`)

These remain explicit but are not the dominant next build seam from this phase.
