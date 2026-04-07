# Phase 10 Postmortem

## What We Tried

Phase 9 imported a bounded retrieval-ranking borrow into the hybrid candidate-ordering seam. The borrow was intentionally narrow: scope, authority, status, support proxy, freshness, and token-budget-aware selection only.

## Why It Looked Plausible

- the hard residual set remained dominated by `prompt_miss`
- ranking was the strongest untried retrieval-side lever after the eligibility bridge and noise-repair imports failed to move the residual set
- the local seam was easy to bound and measure

## What Happened

The fresh paid replay on the hard residual `38` set regressed:

- before ranking borrow: `3/38`
- after ranking borrow: `2/38`

Residual shape stayed effectively the same:

- `prompt_miss`: `29 -> 30`
- `handoff_format_miss`: `4 -> 4`
- `judge_artifact`: `2 -> 2`
- promptless/answer-surface profile: unchanged

## Conclusion

Ranking borrow was locally valid but broader-residual negative. It is not the breakthrough path. Keeping it active would only preserve a falsified mechanism on the forward branch.

## Correct Action

Roll ranking back out of the active hybrid path, keep the earlier hardening work, and carry forward only one next-direction recommendation.
