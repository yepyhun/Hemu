# Phase 17: Retrieval Selection Followup - Context

## Phase Boundary

This phase exists to follow up the verified `v1.10/16` attributed replay outcome:

- dominant actionable bucket: `retrieval_failure`
- dominant stage: `retrieval`
- dominant count: `29/38`

The phase must stay selection-focused. It does not reopen broad retrieval expansion, delivery, ranking, bitemporal remodeling, or promotion-gate work.

## Locked Decisions

### What This Phase Must Do

- freeze the `retrieval_failure` cases from the canonical hard replay
- classify the dominant retrieval selection miss shapes inside that bucket
- reduce the next move to one bounded retrieval-selection mechanism or one explicit stop rule

### What This Phase Must Not Do

- no new paid replay inside the phase
- no new kernel build inside the phase
- no delivery reopen
- no ranking reopen
- no broad retrieval ideation across multiple unrelated hypotheses

## Prior Evidence That Must Be Preserved

- `v1.5/11` already falsified delivery as the dominant next build direction
- `v1.6/12` showed aggregate-temporal evidence gaps and wrong subset selection as major retrieval-side buckets
- `v1.8/14` landed a bounded selector-and-safety slice locally
- `v1.10/16` showed that the hard replay is still dominated by `retrieval_failure` and that raw passes can overstate grounded progress

## Required Canonical Artifacts

- `17-SELECTION-SUBSET-MANIFEST.json`
- `17-SELECTION-TAXONOMY.md`
- `17-SELECTION-TRANSITIONS.jsonl`
- `17-OUTCOME.json`

## Success Criteria

- one frozen retrieval-selection subset exists
- one bounded selection taxonomy exists
- one dominant miss shape or one explicit stop rule is recorded
- the phase ends with one bounded carry-forward recommendation only

## Anti-Loop Rule

Do not respond to the replay by opening multiple new retrieval ideas at once. The phase succeeds only if it narrows, not widens, the next move.
