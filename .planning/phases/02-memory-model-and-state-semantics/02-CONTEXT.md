# Phase 2: Memory Model And State Semantics - Context

**Gathered:** 2026-04-06
**Status:** Ready for planning
**Source:** Project roadmap + `plan7vegrehajt.md` primary spec + `plan6.md` execution guardrails

<domain>
## Phase Boundary

Phase 2 turns the Phase 1 Core2 foundation into a real multi-plane state model.

This phase must define and persist the Core2 memory planes, source/provenance segmentation, namespace classes, trust classes, temporal/versioning fields, and state-transition rules. It must make these semantics executable inside the isolated `agent/core2_*` modules without pushing business logic into Hermes runtime entrypoints.

This phase does **not** deliver the full retrieval constitution, typed answer contract, benchmark harnesses, or paid-eval proof ladder. Those stay in later phases.

</domain>

<decisions>
## Implementation Decisions

### Locked Decisions
- `plan7vegrehajt.md` is the primary Phase 2 product contract.
- `plan6.md` constrains execution style, anti-Frankenstein boundaries, and adopted invariants, but does not override the more concrete Phase 2 product semantics in `plan7vegrehajt.md`.
- The phase must implement the explicit planes `raw_archive`, `canonical_truth`, `derived_propositions`, `retrieval_indices`, and `delivery_views` as distinct concerns rather than one flat note bucket.
- Local-first, inspectable persistence remains mandatory.
- Source lineage, provenance, and temporal metadata are first-class fields, not optional extras.
- Minimal bitemporal handling is required: event/effectivity time and system/record time.
- Namespace and trust policy must be enforced in storage/runtime semantics before Phase 3 retrieval logic.
- Phase 2 may prepare proposition support as a controlled placeholder, but it must not let the derived layer become primary truth.
- Background digestion and maintenance loops belong to Core2 modules, not to `run_agent.py` or other broad Hermes entrypoint files.

### the agent's Discretion
- Exact table layout and helper module split inside `agent/core2_*`
- Whether plane semantics live in `core2_store.py` alone or are separated into additional `core2_schema.py`, `core2_policy.py`, and `core2_maintenance.py` modules
- How much of `derived_propositions` is executable in Phase 2 versus explicitly scaffolded for later activation

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Product contract
- `plan7vegrehajt.md` — primary Core2 execution spec, including planes, namespace classes, temporal/versioning contract, and maintenance loops
- `plan6.md` — execution constitution, anti-Frankenstein constraints, and adopted invariants

### Project requirements and roadmap
- `.planning/ROADMAP.md` — Phase 2 goal, requirement IDs, and success criteria
- `.planning/REQUIREMENTS.md` — `MODEL-*`, `SCOPE-*`, and `TIME-*` requirements
- `.planning/PROJECT.md` — active constraints and architectural decisions
- `.planning/STATE.md` — current project position and blockers

### Existing code and boundaries
- `agent/memory_provider.py` — external provider lifecycle contract
- `agent/memory_manager.py` — builtin + single external provider orchestration
- `plugins/memory/core2/__init__.py` — Core2 provider boundary
- `agent/core2_runtime.py` — Phase 1 runtime entry
- `agent/core2_store.py` — Phase 1 local persistence
- `agent/core2_types.py` — Phase 1 typed packets

### Existing tests and seeds
- `tests/agent/test_core2_provider_foundation.py` — active foundation lifecycle tests
- `tests/agent/test_core2_legacy_adapted.py` — active legacy-inspired foundation tests
- `.planning/legacy-test-seeds/kernel-memory/README.md` — preserved seed corpus

</canonical_refs>

<specifics>
## Specific Ideas

- `raw_archive` should carry original artifact/span/source anchors, checksums, timestamps, and namespace.
- `canonical_truth` should hold the primary structured objects (`entity`, `event`, `state`, `measure`, `source`) with stable IDs and source lineage.
- `derived_propositions` should remain explicitly marked as derived, not canonical truth.
- Phase 2 should introduce versioning edges such as `supersedes`, `corrects`, `conflicts_with`, and `derived_from`.
- High-risk namespaces require stricter temporal completeness and conflict visibility even before final answer-contract work lands in Phase 3.

</specifics>

<deferred>
## Deferred Ideas

- Query-family routing and retrieval policy matrix
- Final typed answer packets and delivery rendering
- Embedding-model challenger evaluation and benchmark gates
- End-to-end proof ladder and scaled benchmark automation

</deferred>

---

*Phase: 02-memory-model-and-state-semantics*
*Context gathered: 2026-04-06*
