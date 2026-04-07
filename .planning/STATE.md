---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: in_progress
stopped_at: Phase 04.5 is complete; the next step is to resume Phase 04.1 and rerun the staged live gate on top of the deterministic answer-surface contract
last_updated: "2026-04-06T23:59:00+02:00"
last_activity: 2026-04-06
progress:
  total_phases: 9
  completed_phases: 8
  total_plans: 27
  completed_plans: 26
  percent: 96
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-06)

**Core value:** If everything else degrades, Core2 must still return source-grounded, correctly scoped memory under explicit abstention and confidence rules instead of bluffing.
**Current focus:** Phase 04.5 is complete; the workflow should now resume the still-open Phase 04.1 live rerun on top of the deterministic answer surface and fail-closed gate matrix

## Current Position

Phase: 04.1
Plan: 04.1-03 pending
Status: In progress; Phase 04.5 is complete, so the remaining open work is the real staged live gate rerun and release decision in Phase 04.1
Last activity: 2026-04-06 — executed Phase 04.5, adding deterministic answer surfaces, provider-first handoff shaping, and fail-closed gate classification

Progress: [███████████████████░] 96%

## Performance Metrics

**Velocity:**

- Total plans completed: 23
- Average duration: -
- Total execution time: 0.0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 | 3 | - | - |
| 2 | 3 | - | - |
| 3 | 3 | - | - |
| 4 | 3 | - | - |
| 04.1 | 2 | - | - |
| 04.2 | 3 | - | - |
| 04.3 | 3 | - | - |
| 04.4 | 3 | - | - |
| 04.5 | 3 | - | - |

**Recent Trend:**

- Last 5 plans: 04.4-02, 04.4-03, 04.5-01, 04.5-02, 04.5-03
- Trend: Core2 now has deterministic answer surfaces and fail-closed gate classification; the remaining work is the real 04.1 live rerun rather than more structural handoff invention

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Initialization: Core2 will be built as a modular Hermes memory provider.
- Initialization: `plan7vegrehajt.md` is the primary execution spec, with `plan6.md` as governing constraints.
- Phase 1: The existing generic plugin activation path was sufficient; Core2-specific behavior now lives in isolated `agent/core2_*` modules.
- Phase 2: Core2 now has explicit planes, namespace/trust policy, temporal/versioning semantics, and local state-transition/maintenance logic.
- Phase 3: Core2 now has explicit routing, typed answer contracts, abstention behavior, delivery-view discipline, and active retrieval-contract coverage.
- Phase 4: Core2 now has manager-level E2E proof, broader hardening coverage, structured proof harnesses, and an explicit LongMemEval-10 final gate.
- Phase 04.1: The failed live gate is now decomposed into diagnosis, correctness fixes, safe latency controls, and staged rerun work instead of being treated as a vague verification task.
- Phase 04.1 execution: the replayed LongMemEval case improved from false abstention to a grounded `passed: true` result after kernel, graded-budget, judge-shortcut, and bounded-local retrieval fixes, but the live smoke gate still fails on latency.
- Phase 04.2 planning: instead of extending query-time heuristics, Core2 will move common personal/update truth-building into bounded write-time fact digestion using the existing plane/state model.
- Phase 04.2 execution: Core2 now materializes narrow typed facts at write time, supersedes changed current facts by identity, and emits fact-ready delivery views and retrieval indices.
- Phase 04.3 insertion: the next structural move is fact-first recall so query-time uses the new substrate directly instead of rediscovering the same facts from raw blobs.
- Phase 04.3 planning: covered recall will prefer fact-first retrieval primitives and compact fact artifacts, with explicit broader fallback only when fact evidence is insufficient.
- Phase 04.3 execution: covered recall now surfaces fact-first candidates for narrow durable-memory families, the authoritative path can answer from those records directly, and the new path is visible in proof artifacts through `fact_first_hit` and packet metadata.
- Phase 04.4 insertion: the paid live gate now points to a bounded final structural gap rather than generic breakage, so the next move is to model the still-uncovered durable-memory families before rerunning the external gate.
- Phase 04.4 planning: the remaining structural gap is now narrowed to preference/habit/routine, aggregate/count, and bounded temporal-summary families, to be implemented through the same write-time digestion plus fact-first recall architecture.
- Phase 04.4 execution: those three families now have explicit write-time coverage, fact-first recall, guarded structured direct answers, end-to-end contract tests, and a machine-readable gate-state artifact.
- Phase 04.5 insertion: the remaining blocker is no longer substrate coverage but the final answer-handoff contract, so deterministic provider-built answer surfaces and a machine-checkable gate matrix must be planned before the live rerun resumes.
- Phase 04.5 planning: the remaining handoff gap is now decomposed into deterministic answer-surface emission, provider-first handoff consumption, and machine-readable gate classification before 04.1 resumes.
- Phase 04.5 execution: Core2 now emits deterministic answer surfaces, the provider/runtime handoff prefers those surfaces for covered durable-memory families, and the gate stack now records fail-closed blocker taxonomy plus a frozen canary proof path.

### Roadmap Evolution

- Phase 04.1 inserted after Phase 4: LongMemEval Gate And Performance Fixes (URGENT)
- Phase 04.2 inserted after Phase 4: Write-Time Fact Digestion (URGENT)
- Phase 04.3 inserted after Phase 4: Fact-First Recall (URGENT, now complete)
- Phase 04.4 inserted after Phase 4: Uncovered Durable Memory Families (URGENT, now complete)
- Phase 04.5 inserted after Phase 4: Deterministic Answer Surface And Gate Closure (URGENT, now complete)

### Pending Todos

None yet.

### Blockers/Concerns

- Brownfield repo with large orchestrator files; keep native runtime edits thin.
- Existing untracked work exists outside `.planning/` and should not be disturbed.
- Paid LongMemEval-10 is still pending and remains the final external benchmark gate.
- Paid LongMemEval-10 and the staged live rerun are still pending; Phase 04.5 narrowed the handoff contract but did not itself claim the external gate passed.
- The current cheap canary proof is `4/5`; the remaining miss is a `single-session-assistant` case and stays in 04.1 scope until the real live rerun classifies it.
- Repo-local git identity is still unset, so atomic local commits remain blocked until `git config --local user.name/user.email` is set.
- Full `uv run --extra dev pytest ...` is still blocked in this environment by offline git dependency resolution for `tinker`.

## Session Continuity

Last session: 2026-04-06 00:00
Stopped at: Phase 04.5 executed; next step is `/gsd-execute-phase 04.1`
Resume file: None
