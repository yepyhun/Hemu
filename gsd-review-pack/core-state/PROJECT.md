# Hermes Core2 Memory Kernel

## What This Is

Hermes Core2 is a new modular memory kernel for Hermes Agent, implemented inside the existing brownfield repo as a first-class memory provider rather than an ad hoc patch set. It aims to replace the current weak-memory path with a source-grounded, retrieval-disciplined, benchmarkable kernel that can serve personal memory, workspace/project memory, library knowledge, and high-risk domains under explicit trust and evidence rules.

The immediate audience is Hermes itself and the user operating Hermes as a serious second-brain and agent runtime. The target is not an MVP memory stub, but a production-grade kernel with clear proof gates and upstream-friendly wiring.

## Core Value

If everything else degrades, Core2 must still return source-grounded, correctly scoped memory under explicit abstention and confidence rules instead of bluffing.

## Requirements

### Validated

- ✓ Hermes already supports a modular agent/runtime split with tool registry, toolsets, CLI, and gateway entry points — existing
- ✓ Hermes already has a memory provider abstraction with lifecycle hooks and plugin discovery under `plugins/memory/` — existing
- ✓ Hermes already has built-in persistent curated memory plus external provider plumbing — existing
- ✓ Hermes already has broad automated coverage across agent, gateway, ACP/MCP, and memory-provider flows — existing
- ✓ Phase 1 established Core2 as a loadable Hermes memory provider with isolated `agent/core2_*` modules, stable lifecycle wiring, and active foundation tests — Phase 1
- ✓ Phase 2 established explicit planes, namespace/trust policy, temporal/versioning semantics, and local state-transition/maintenance logic — Phase 2
- ✓ Phase 3 established explicit routing, typed answer contracts, abstention behavior, delivery-view discipline, and active retrieval-contract tests — Phase 3
- ✓ Phase 4 established manager-level E2E proof, broader hardening regressions, structured proof harnesses, and honest release-readiness evidence — Phase 4
- ✓ Phase 04.2 established bounded write-time fact digestion, current/previous fact canonicalization, and compact recall-ready fact artifacts — Phase 04.2
- ✓ Phase 04.3 established fact-first recall for covered durable-memory queries with inspectable fallback behavior and aligned authoritative answers — Phase 04.3
- ✓ Phase 04.4 established structural coverage for the previously missing durable-memory families: preference/habit/routine, aggregate/count, and bounded temporal-summary — Phase 04.4
- ✓ Phase 04.5 established deterministic provider-owned answer surfaces, provider-first handoff shaping, and fail-closed machine-readable gate classification — Phase 04.5

### Active

- [ ] Run the paid LongMemEval-10 Hermes-path evaluation as the final external benchmark gate before making a stronger benchmark or SOTA claim.

### Out of Scope

- Rewriting the whole Hermes runtime outside the memory boundary — the repo already has the right abstraction seam, so Core2 should integrate through providers and thin native wiring.
- Model-only or direct-API benchmarking outside Hermes runtime flow — the benchmark target is the real Hermes kernel path, not a disconnected baseline.
- Multiple simultaneously active external memory kernels in the first delivery — current Hermes provider architecture assumes one external provider at a time.

## Context

This is a brownfield initialization inside `/home/lauratom/Asztal/ai/hermes-agent-core2`. The codebase already contains a large multi-platform agent system with CLI, gateway transports, a self-registering tool architecture, and a modular memory-provider contract in `agent/memory_provider.py` and `plugins/memory/`.

The architectural target is driven primarily by `plan7vegrehajt.md`, with `plan6.md` acting as the constitution of hard laws, invariants, anti-loop rules, and proof standards. The desired outcome is a SOTA-competitive memory kernel for Hermes, not a partial experiment or placeholder implementation.

The codebase map in `.planning/codebase/` shows the safe integration path clearly: keep Core2 logic in isolated modules, minimize business logic in `run_agent.py` and `gateway/run.py`, preserve lifecycle hooks, and extend tests around provider behavior, compression, delegation, and gateway/session flows.

## Constraints

- **Architecture**: Keep Core2 modular and upstream-friendly — isolate business logic in new modules/providers and keep native Hermes files limited to thin wiring.
- **Correctness**: Source-grounded truth and retrieval discipline are mandatory — unsupported claims must abstain rather than guess.
- **Benchmarking**: Proof and evaluation must run through the full Hermes kernel/memory/runtime path — not raw model APIs.
- **Compatibility**: Preserve existing CLI, gateway, and provider lifecycle behavior where possible — Hermes is already multi-entry-point and regression-sensitive.
- **Quality**: Verification is required, not optional — plan checking, verifier usage, and proof ladders are part of the project definition.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Build Core2 as a modular Hermes memory provider, not as scattered runtime patches | The repo already exposes a provider/plugin boundary and this minimizes merge debt | Validated in Phase 1 |
| Use `plan7vegrehajt.md` as the primary execution spec | It is the most complete product and systems contract for Core2 | Used for initialization and Phase 1 execution |
| Use `plan7vegrehajt.md` as the primary Phase 2 product contract, with `plan6.md` as execution guardrails | Plan 7 gives the concrete planes/temporal/state model; plan 6 constrains anti-shortcut execution behavior | Applied in Phase 2 |
| Make query family, answer type, and delivery view explicit Core2 contract data | Retrieval and answer behavior must be inspectable inside Core2, not improvised at the provider edge | Validated in Phase 3 |
| Keep the paid LongMemEval-10 run as the final external gate | Local proof can be green without pretending the final benchmark already happened | Applied in Phase 4 |
| Stop extending query-time heuristics and move common durable-memory truth-building into write-time digestion | Phase 04.1 exposed a structural raw-blob bottleneck; more surface heuristics would repeat the old kernel failure mode | Applied in Phase 04.2 |
| Make covered recall fact-first with safe raw fallback | After Phase 04.2, the missing architectural step is to consume the new fact substrate directly instead of hoping broad canonical search will surface it first | Validated in Phase 04.3 |
| Model the still-uncovered durable-memory families before returning to the final live gate | The paid gate now points to a bounded structural coverage gap, not a reason to keep patching 04.1 blindly | Validated in Phase 04.4 |
| Narrow the final answer handoff to a deterministic provider-owned surface before resuming the live gate | The dominant remaining failure family is prompt drift/handoff mismatch, not missing memory families, so the next structural move is to tighten the provider-to-answer boundary | Validated in Phase 04.5 |
| Keep the final gate fail-closed and machine-readable, including `unknown` and a frozen canary set | The project was drifting toward prose-only “almost done” judgments; mechanical blocker classification keeps the finish line explicit | Applied in Phase 04.5 |
| Use coarse phase granularity with parallel execution | The project is large but conceptually divisible into a few coherent milestones | Validated by roadmap and Phase 1 planning |
| Keep planning docs tracked in git | This is substantial architectural work and should remain visible and reviewable | Applied locally; commit still blocked by missing repo-local git identity |
| Skip domain research for init, but keep researcher/plan-check/verifier enabled for phase work | The user already provided the governing design documents, but execution quality gates still matter | Applied during initialization and Phase 1 |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-06 after Phase 04.5 execution*
