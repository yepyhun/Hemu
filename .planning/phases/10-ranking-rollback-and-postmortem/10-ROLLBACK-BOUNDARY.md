# Phase 10 Rollback Boundary

## Removed From Active Path

- `agent/core2_hybrid_substrate.py` no longer imports or uses `agent/core2_ranking.py`
- active hybrid candidate ordering no longer uses ranking signals
- active hybrid metadata no longer emits `ranking_signals`
- ranking-specific test semantics have been retired from the active suite

## Explicitly Preserved

- bounded hybrid substrate seam
- deterministic core ownership
- invariant harness
- narrow noise repair
- historical Phase 9 artifacts

## Out Of Scope

- new ranking variant
- render/comparator changes
- claim-guard work
- new borrow work
- paid rerun inside this phase

## Active-Path Truth

The hybrid path is now score-first again. The ranking borrow survives only as historical reference, not as active retrieval behavior.
