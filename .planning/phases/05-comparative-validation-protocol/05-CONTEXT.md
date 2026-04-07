# Phase 5: Comparative Validation Protocol - Context

**Gathered:** 2026-04-07
**Status:** Ready for planning

## Why This Phase Exists

Milestone `v1.1` starts from a shipped and archived `v1.0` Core2 baseline plus a bounded hybrid branch that already showed a better broader paid result (`18/20`) than the earlier broader baseline (`12/20`).

The next honest step is not more implementation. It is to lock a comparison protocol so later baseline-versus-hybrid decisions are reproducible, comparable, and resistant to post-hoc story-telling.

## Inputs

- shipped baseline archive: `milestones/v1.0-ROADMAP.md`
- shipped baseline requirements archive: `milestones/v1.0-REQUIREMENTS.md`
- milestone record: `.planning/MILESTONES.md`
- hybrid broader validation artifacts:
  - `.planning/phases/04.11-hybrid-branch-broader-paid-validation/04.11-OUTCOME.json`
  - `.planning/phases/04.11-hybrid-branch-broader-paid-validation/04.11-VERIFICATION.md`
- residual stop-point closure:
  - `.planning/phases/04.12-residual-gate-closure/04.12-OUTCOME.json`
  - `.planning/phases/04.12-residual-gate-closure/04.12-VERIFICATION.md`

## Locked Decisions

- This phase locks comparison protocol only; it is not an implementation phase.
- No edits to `agent/core2_*`, `plugins/memory/core2/*`, or benchmark harness behavior are allowed as part of this phase.
- Baseline and hybrid must be compared through a frozen protocol, not fresh ad hoc reruns.
- Success, regression, and mixed verdict rules must be defined before execution.
- Retrieval-only wins must never be treated as end-to-end memory wins.
- The shipped `v1.0` baseline remains the reference point until a later milestone phase explicitly promotes a replacement.

## What This Phase Must Not Become

- hidden hybrid improvement work
- threshold-moving after seeing results
- benchmark shopping across multiple incomparable sample sets
- reopening MemPalace adoption analysis
- reopening v1 kernel family/generalization work

## Canonical References

- `.planning/PROJECT.md` — current milestone goal and constraints
- `.planning/ROADMAP.md` — current milestone phase structure
- `.planning/REQUIREMENTS.md` — active v1.1 comparison requirements
- `.planning/STATE.md` — current milestone state
- `.planning/phases/04.11-hybrid-branch-broader-paid-validation/04.11-CONTEXT.md` — reference pattern for validation-phase protocol locking
- `.planning/phases/04.11-hybrid-branch-broader-paid-validation/04.11-RESEARCH.md` — validation guardrail style

