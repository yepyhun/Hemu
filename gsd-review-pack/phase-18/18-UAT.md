# Phase 18 UAT

## Scope

Validate that the pre-selector candidate-pool follow-up phase is accepted as one bounded upstream-of-selector narrowing step over the verified `no_answer_bearing_selection` subset, without reopening selector retuning, delivery, ranking, or broader retrieval redesign.

## Acceptance Checks

- one frozen pre-selector subset manifest exists for the canonical `29`-case subset from `v1.11/17`
- one bounded upstream candidate-pool taxonomy exists and classifies every subset case
- one canonical outcome exists and reduces the phase to one carry-forward recommendation or one explicit stop rule
- the phase proves whether the dominant next seam sits before selector engagement
- the phase does not reopen delivery, ranking, bitemporal, promotion-gate, or broad retrieval ideation

## Result

- subset manifest: `18-CANDIDATE-POOL-SUBSET-MANIFEST.json`
- taxonomy artifact: `18-CANDIDATE-POOL-TAXONOMY.md`
- per-case ledger: `18-CANDIDATE-POOL-TRANSITIONS.jsonl`
- canonical outcome: `18-OUTCOME.json`
- dominant actionable family: `query_shape_conditioned_candidate_seeding` (`21/29`)
- selector engaged cases: `0`
- carry-forward recommendation: `query_shape_conditioned_candidate_seeding`

## Verdict

`pass`
