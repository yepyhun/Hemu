# Roadmap: Hermes Core2 Memory Kernel

## Overview

This roadmap takes Hermes from its current mixed built-in/plugin memory baseline to a proof-driven Core2 kernel integrated through the existing provider boundary. The path is intentionally coarse: first establish the provider and wiring seam, then implement the memory model and invariants, then deliver retrieval and answer behavior, and finally prove the kernel through tests and end-to-end benchmark gates.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [x] **Phase 1: Core2 Provider Foundation** - Establish the new provider/module boundary and wire Core2 into Hermes safely. (completed 2026-04-06)
- [x] **Phase 2: Memory Model And State Semantics** - Implement planes, namespaces, trust classes, and lifecycle state transitions. (completed 2026-04-06)
- [x] **Phase 3: Retrieval And Answer Contracts** - Deliver query routing, evidence-aware retrieval, abstention, and typed answer behavior. (completed 2026-04-06)
- [x] **Phase 4: Proof, Benchmarks, And Hardening** - Validate the kernel through tests, runtime proofs, and end-to-end benchmark gates. (completed 2026-04-06)
- [ ] **Phase 04.1: Kernel Correctness And Live Gate Recovery (INSERTED)** - Diagnose the failed live path, fix correctness gaps, then rerun the real external gate.
- [x] **Phase 04.2: Write-Time Fact Digestion (INSERTED)** - Move more truth-building work into write-time/background digestion so recall no longer depends on raw session blobs. (completed 2026-04-06)
- [x] **Phase 04.3: Fact-First Recall (INSERTED)** - Make covered recall paths prefer the new fact substrate, with safe fallback to broader canonical retrieval. (completed 2026-04-06)
- [x] **Phase 04.4: Uncovered Durable Memory Families (INSERTED)** - Close the remaining durable-memory family gaps structurally before resuming the final live gate. (completed 2026-04-06)
- [x] **Phase 04.5: Deterministic Answer Surface And Gate Closure (INSERTED)** - Build a provider-owned answer surface and hard gate matrix so the final live rerun measures the finished Core2 handoff instead of prompt drift. (completed 2026-04-06)

## Phase Details

### Phase 1: Core2 Provider Foundation
**Goal**: Core2 exists as a real Hermes memory provider with isolated modules and thin runtime wiring.
**Depends on**: Nothing (first phase)
**Requirements**: [PROV-01, PROV-02, PROV-03]
**Success Criteria** (what must be TRUE):
  1. Hermes can load and initialize Core2 through the provider discovery/activation path.
  2. Core2-specific business logic lives in dedicated modules/provider code rather than scattered runtime patches.
  3. Existing lifecycle hooks are wired cleanly enough that later phases can build on them without redesign.
**Plans**: 3 plans

Plans:
- [x] 01-01: Define Core2 provider/module layout and runtime wiring points
- [x] 01-02: Implement provider bootstrap, config surface, and lifecycle scaffolding
- [x] 01-03: Add baseline tests for provider loading and lifecycle integration

### Phase 2: Memory Model And State Semantics
**Goal**: Core2 stores and manages the multi-plane memory model with explicit namespace, trust, temporal, and state-transition rules.
**Depends on**: Phase 1
**Requirements**: [MODEL-01, MODEL-02, MODEL-03, MODEL-04, SCOPE-01, SCOPE-02, SCOPE-03, TIME-01, TIME-02]
**Success Criteria** (what must be TRUE):
  1. The Core2 storage model separates raw archive, canonical truth, derived propositions, retrieval indices, and delivery views.
  2. Admission, promotion, rejection, demotion, forgetting, and versioning semantics behave according to the Core2 spec.
  3. Namespaces and trust classes prevent unsafe mixing of facts and claims across domain boundaries.
**Plans**: 3 plans

Plans:
- [x] 02-01: Implement plane schemas and source/provenance segmentation
- [x] 02-02: Implement namespace, trust, temporal, and update-resolution rules
- [x] 02-03: Implement state-transition logic and maintenance loops

### Phase 3: Retrieval And Answer Contracts
**Goal**: Core2 answers queries through explicit routing, evidence-aware retrieval, abstention, and typed delivery contracts.
**Depends on**: Phase 2
**Requirements**: [RETR-01, RETR-02, RETR-03, RETR-04, TIME-03]
**Success Criteria** (what must be TRUE):
  1. Query families route through the correct retrieval strategies with explicit limits and completeness rules.
  2. Answer modes differentiate exact-source, source-supported, and compact-memory behavior rather than collapsing them into one response path.
  3. The kernel abstains correctly when support, confidence, or high-risk constraints are not satisfied.
**Plans**: 3 plans

Plans:
- [x] 03-01: Implement retrieval routing matrix and query-family dispatch
- [x] 03-02: Implement typed answer contract, support tiers, and confidence metadata
- [x] 03-03: Enforce abstention, token-budget, and delivery-view rules

### Phase 4: Proof, Benchmarks, And Hardening
**Goal**: Core2 is verified through automated tests and end-to-end proof gates on the real Hermes runtime path.
**Depends on**: Phase 3
**Requirements**: [QUAL-02, QUAL-03]
**Success Criteria** (what must be TRUE):
  1. Automated coverage exists for provider lifecycle, state transitions, retrieval contracts, and integration-sensitive flows.
  2. Core2 can pass local and scaled proof gates through the actual Hermes runtime path.
  3. Benchmark and evaluation outputs are strong enough to support the SOTA-oriented acceptance bar defined in the plans.
**Plans**: 3 plans

Plans:
- [x] 04-01: Expand tests and regression coverage around Core2 behavior
- [x] 04-02: Build end-to-end proof/benchmark harnesses through Hermes runtime
- [x] 04-03: Harden performance, correctness edge cases, and release-readiness evidence

## Progress

**Execution Order:**
Phases execute in numeric order, with 04.1 currently paused while its inserted dependency phases complete: 1 → 2 → 3 → 4 → 04.1 → 04.2 → 04.3 → 04.4 → 04.5 → resume 04.1

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Core2 Provider Foundation | 3/3 | Complete    | 2026-04-06 |
| 2. Memory Model And State Semantics | 3/3 | Complete    | 2026-04-06 |
| 3. Retrieval And Answer Contracts | 3/3 | Complete    | 2026-04-06 |
| 4. Proof, Benchmarks, And Hardening | 3/3 | Complete | 2026-04-06 |
| 04.1. Kernel Correctness And Live Gate Recovery | 2/3 | In Progress | - |
| 04.2. Write-Time Fact Digestion | 3/3 | Complete | 2026-04-06 |
| 04.3. Fact-First Recall | 3/3 | Complete | 2026-04-06 |
| 04.4. Uncovered Durable Memory Families | 3/3 | Complete | 2026-04-06 |
| 04.5. Deterministic Answer Surface And Gate Closure | 3/3 | Complete | 2026-04-06 |

### Phase 04.5: Deterministic Answer Surface And Gate Closure (INSERTED)

**Goal:** Close the final gap between Core2 memory correctness and the live Hermes answer handoff by making the provider emit narrow deterministic answer surfaces and by turning the last gate into mechanically classifiable blockers.
**Depends on:** Phase 04.4
**Requirements**: [RETR-07, RETR-08, QUAL-05]
**Success Criteria** (what must be TRUE):
  1. Core2 can emit a provider-owned, answer-ready surface for covered durable-memory families without depending on a loose prompt-shaped recall blob.
  2. Remaining live-gate failures can be classified mechanically as kernel correctness, handoff/format, or latency blockers.
  3. Phase 04.1 can resume on top of this narrower handoff contract instead of accumulating more ad hoc prompt fixes.
**Plans:** 3 plans

Plans:
- [x] 04.5-01: Emit deterministic answer surfaces
- [x] 04.5-02: Prefer the answer surface in Hermes handoff
- [x] 04.5-03: Add gate matrix and hand back to 04.1

### Phase 04.4: Uncovered Durable Memory Families (INSERTED)

**Goal:** Close the still-uncovered durable-memory families exposed by the paid live gate so Core2 can answer them from structured substrate coverage rather than slow or generic query-time reasoning.
**Requirements**: [FACT-04, FACT-05, FACT-06]
**Depends on:** Phase 04.3
**Success Criteria** (what must be TRUE):
  1. Preference/habit/routine, aggregate/count, and bounded temporal-summary questions have explicit write-time Core2 fact coverage.
  2. The new families resolve through fact-first recall and structured direct-answer behavior with safe fallback instead of raw-blob-first rediscovery.
  3. Proof artifacts show the new coverage concretely enough to justify returning to the unfinished 04.1 live gate.
**Plans:** 3 plans

Plans:
- [x] 04.4-01: Extend write-time coverage for uncovered durable families
- [x] 04.4-02: Consume the new families through fact-first recall
- [x] 04.4-03: Prove the new families and hand back to 04.1

### Phase 04.3: Fact-First Recall (INSERTED)

**Goal:** Make covered recall paths use the Phase 04.2 fact substrate first so common durable-memory queries stop depending on raw-blob-first retrieval.
**Requirements**: [RETR-05, RETR-06]
**Depends on:** Phase 04.2
**Success Criteria** (what must be TRUE):
  1. Covered query families prefer fact-first candidate retrieval and compact fact artifacts before broader canonical search.
  2. When fact evidence is insufficient, Core2 falls back safely to the broader retrieval path without losing provenance, abstention, or current/previous correctness.
  3. Proof and regression artifacts can show that the fact-first path is actually active for covered cases.
**Plans:** 3 plans

Plans:
- [x] 04.3-01: Add fact-first retrieval primitives
- [x] 04.3-02: Wire runtime recall to prefer facts first
- [x] 04.3-03: Prove fact-first recall and preserve contracts

### Phase 04.1: Kernel Correctness And Live Gate Recovery (INSERTED)

**Goal:** Restore trust in the real Hermes-integrated Core2 gate by diagnosing live failure patterns, fixing correctness gaps, and only then rerunning the external evaluation.
**Requirements**: [QUAL-04]
**Depends on:** Phase 4
**Success Criteria** (what must be TRUE):
  1. The live Hermes path yields replayable evidence that identifies the dominant correctness and latency failure modes.
  2. The repaired Core2 path passes targeted regressions and a smoke gate before a larger paid sample is attempted.
  3. A staged live-gate rerun produces an explicit release recommendation grounded in real benchmark evidence.
**Plans:** 3 plans

Plans:
- [x] 04.1-01: Diagnose live failure patterns and telemetry
- [x] 04.1-02: Fix kernel correctness gaps and add safe latency controls
- [ ] 04.1-03: Re-run live gate and produce release decision

### Phase 04.2: Write-Time Fact Digestion (INSERTED)

**Goal:** Move the highest-value truth-building work for durable memory into write-time/background digestion so later recall can use typed compact facts instead of reconstructing truth from raw session blobs.
**Requirements**: [FACT-01, FACT-02, FACT-03]
**Depends on:** Phase 4
**Success Criteria** (what must be TRUE):
  1. Core2 write paths create typed compact fact records for covered durable-memory cases instead of relying on later raw-blob reconstruction.
  2. Covered facts resolve current vs previous/update semantics at write time with preserved provenance and inspectable history.
  3. Core2 materializes compact recall-ready fact artifacts that leave a clean handoff for the later fact-first recall phase.
**Plans:** 3 plans

Plans:
- [x] 04.2-01: Implement bounded write-time fact digestion
- [x] 04.2-02: Canonicalize digested facts at write time
- [x] 04.2-03: Materialize recall-ready fact views and prove the layer
