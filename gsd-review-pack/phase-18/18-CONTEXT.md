# Phase 18: Pre-Selector Candidate Pool Followup - Context

## Phase Boundary

This phase exists to follow up the verified `v1.11/17` result:

- frozen hard replay retrieval subset: `29`
- dominant selection taxonomy label: `no_answer_bearing_selection` on `29/29`
- `selector_engaged = 0` on the subset

The phase must stay upstream of selector engagement. It does not reopen delivery, ranking, broad retrieval expansion, bitemporal remodeling, or promotion-gate work.

## Locked Decisions

### What This Phase Must Do

- preserve the canonical `29`-case pre-selector subset from the verified selection follow-up
- classify the dominant upstream miss shapes that prevent answer-bearing candidates from entering the pool at all
- reduce the next move to one bounded pre-selector mechanism or one explicit stop rule

### What This Phase Must Not Do

- no new paid replay inside the phase
- no new selector retuning inside the phase
- no delivery reopen
- no ranking reopen
- no broad operator-slot redesign across the whole stack

## Prior Evidence That Must Be Preserved

- `v1.10/16` proved the hard residual replay remains dominated by `retrieval_failure`
- `v1.11/17` proved the failure subset is upstream of selector engagement, not a selector-choice problem
- `v1.8/14` already landed a bounded selector-and-safety slice locally, so this phase must not drift back into the same seam
- the hard replay raw passes overstate grounded progress, so carry-forward decisions must stay strict

## Required Canonical Artifacts

- `18-CANDIDATE-POOL-SUBSET-MANIFEST.json`
- `18-CANDIDATE-POOL-TAXONOMY.md`
- `18-CANDIDATE-POOL-TRANSITIONS.jsonl`
- `18-OUTCOME.json`

## Success Criteria

- one frozen pre-selector subset exists
- one bounded upstream taxonomy exists
- one dominant upstream miss shape or one explicit stop rule is recorded
- the phase ends with one bounded carry-forward recommendation only

## Anti-Loop Rule

Do not respond to the hard replay by reopening the full retrieval stack. The phase succeeds only if it narrows the next move to one upstream candidate-pool mechanism or stops cleanly.
