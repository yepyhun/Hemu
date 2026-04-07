# Phase 10: Ranking Rollback And Postmortem - Context

**Gathered:** 2026-04-07
**Status:** Ready for planning

## Phase Boundary

This phase rolls back the bounded retrieval-ranking borrow from the active hybrid path after the fresh paid residual replay regressed from `3/38` to `2/38`. It does not introduce a new retrieval mechanism, a new benchmark loop, or any replacement ranking scheme.

The deliverable is a clean rollback, a canonical postmortem, and exactly one bounded next-direction recommendation.

## Implementation Decisions

### Locked
- The ranking borrow is treated as a falsified breakthrough path on the hard residual `38` set.
- Rollback means removing ranking influence from the active hybrid retrieval path, not deleting the historical artifacts or pretending the work never happened.
- Invariants, acceptance harness, and noise repair stay in place.
- No new paid rerun happens inside this phase.
- The postmortem must end with one bounded next-direction recommendation, not a menu of speculative options.

### Explicitly Out Of Scope
- New borrow work
- New family growth
- Comparator or render rewrites
- Claim-guard work
- New benchmark subsets or paid confirmation loops
- Reopening MemPalace adoption or substrate ownership

## Canonical References

### Milestone and roadmap state
- `.planning/PROJECT.md` — active milestone framing and requirements
- `.planning/ROADMAP.md` — Phase 10 scope
- `.planning/REQUIREMENTS.md` — active requirement IDs
- `.planning/STATE.md` — current milestone/phase state

### Ranking borrow and regression evidence
- `.planning/phases/09-retrieval-ranking-borrow/09-VERIFICATION.md` — local proof for the ranking borrow
- `.planning/phases/09-retrieval-ranking-borrow/09-HYBRID-RETEST-38-STATUS.json` — broader residual replay that regressed from `3/38` to `2/38`
- `.planning/phases/08.1-invariant-harness-and-noise-repair-import/08.1-HYBRID-RETEST-38-STATUS.json` — prior hard residual reference point

### Code ownership
- `agent/core2_ranking.py` — bounded ranking helper to be retired from active path
- `agent/core2_hybrid_substrate.py` — active hybrid ordering seam
- `tests/agent/test_core2_retrieval_ranking.py` — ranking-specific tests to be retired or repurposed

## Specific Ideas

- Preserve a clear historical record that ranking borrow was locally green but broader residual-negative.
- Prefer a rollback that is easy to reason about over a clever partial disable.
- Capture the dominant residual fact explicitly: `prompt_miss` remained the largest bucket before and after ranking.

## Deferred Ideas

- Any further retrieval-ranking experimentation
- Any handoff/render work
- Any new benchmark-driven forward build

---

*Phase: 10-ranking-rollback-and-postmortem*
*Context gathered: 2026-04-07*
