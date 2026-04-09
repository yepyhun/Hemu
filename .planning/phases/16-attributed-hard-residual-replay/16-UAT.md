# Phase 16 UAT

## Scope

Validate that the attributed hard residual replay is accepted as one bounded diagnostic truth point over the frozen hard `38` set without reopening retrieval, delivery, ranking, or truth-model work inside the same phase.

## Acceptance Checks

- one frozen replay manifest exists for the canonical hard `38`
- one standard gate status artifact and one per-case attributed status artifact exist for the same replay
- the replay stayed on the current active path instead of reopening historical branches
- the phase-15 attribution contract was reused without introducing a second diagnostics schema
- the canonical outcome names one dominant actionable bucket or an explicit stop rule
- the raw replay result is distinguished from attributed grounded passes so judge-false-positive wins are not silently counted as grounded progress
- no new retrieval, delivery, ranking, bitemporal, or promotion-gate edits were required to finish the replay phase

## Result

- replay manifest: `16-REPLAY-MANIFEST.json`
- gate status artifact: `16-GATE-STATUS.json`
- attributed status artifact: `16-ATTRIBUTED-STATUS.json`
- canonical attributed outcome: `16-ATTRIBUTED-OUTCOME.json`
- raw replay result: `3/38`
- attributed grounded passes: `1/38`
- judge-false-positive passes inside the raw replay result: `2`
- dominant actionable bucket: `retrieval_failure` / `retrieval` with `29/38`

## Verdict

`pass`
