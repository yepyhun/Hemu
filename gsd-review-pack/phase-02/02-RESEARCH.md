# Phase 2: Memory Model And State Semantics - Research

**Researched:** 2026-04-06
**Domain:** Core2 multi-plane state model on top of the Phase 1 Hermes provider foundation
**Confidence:** HIGH

<user_constraints>
## User Constraints

### Locked Constraints
- The target is a production-grade, SOTA-competitive memory kernel, not an MVP note store.
- `plan7vegrehajt.md` is the primary execution spec; `plan6.md` remains a hard guardrail document.
- Core2 must stay modular and upstream-friendly, with business logic isolated in `agent/core2_*`.
- Local-first persistence is mandatory.
- Accuracy, provenance, and abstention discipline outrank speed and token savings.
- Benchmark and eval work are not planning substitutes and do not belong in this phase.

</user_constraints>

<phase_scope>
## Phase 2 Must Deliver

The roadmap and requirements make this phase responsible for:
- `MODEL-01..04`: multi-plane storage separation
- `SCOPE-01..03`: namespace classes and trust-aware segmentation
- `TIME-01..02`: temporal/versioning semantics and update resolution

Concretely, Phase 2 must convert the current single-table/single-object foundation into a plane-aware kernel model with executable admission, promotion, demotion, supersession, and maintenance semantics.

</phase_scope>

<current_state>
## Current Code Reality

Phase 1 already established:
- a working Core2 provider
- a local SQLite store
- a runtime that can ingest notes, persist turns, recall simple matches, and explain stored objects
- active Core2 foundation tests

Current gaps relevant to Phase 2:
- storage is still effectively a flat note bucket
- there is no explicit separation between `raw_archive`, `canonical_truth`, and `derived_propositions`
- namespace and risk rules are only lightly carried through ingestion fields, not enforced as policy
- temporal/versioning fields are incomplete relative to the spec
- no explicit maintenance loop or state-transition engine exists yet

</current_state>

<non_negotiables>
## Non-Negotiable Semantics From `plan7vegrehajt.md`

- `raw_archive` is the evidence base and must preserve source pointers and timestamps
- `canonical_truth` is the primary truth layer
- `derived_propositions` is explicitly derived and must not become primary truth
- `retrieval_indices` and `delivery_views` are operational layers, not truth storage
- namespaces must remain distinct (`personal`, `workspace`, `library`, `high-risk`)
- high-risk content requires stricter support, temporal visibility, and conflict handling
- minimal bitemporal support is mandatory
- versioning edges such as `supersedes`, `corrects`, `conflicts_with`, and `derived_from` are required
- forgetting should default to demotion/supersession, not destructive deletion
- maintenance loops must include dedupe, merge proposal, conflict detection, supersession, stale provisional demotion, derived rebuild, and activation decay

</non_negotiables>

<recommended_structure>
## Recommended Implementation Shape

Keep the Phase 1 modular pattern and extend it rather than reinventing it:

- `agent/core2_types.py`
  - typed plane/object/edge/state enums or dataclasses
- `agent/core2_store.py`
  - durable schema, migrations, and low-level persistence
- `agent/core2_runtime.py`
  - session-facing API and orchestration over store/policy/maintenance
- optional new helpers:
  - `agent/core2_schema.py` for plane/object constants and row shapes
  - `agent/core2_policy.py` for namespace/trust/admission gates
  - `agent/core2_maintenance.py` for demotion/supersession/decay loops

This preserves the anti-Frankenstein rule and keeps runtime entrypoints thin.

</recommended_structure>

<plan_breakdown>
## Best 3-Plan Split

### Plan 02-01
Implement plane schemas and provenance/source segmentation.

### Plan 02-02
Implement namespace, trust, temporal, and update-resolution rules on top of those schemas.

### Plan 02-03
Implement state-transition logic and maintenance loops, then prove the new semantics with active tests adapted from the legacy corpus where relevant.

This order follows the spec:
1. first define what exists
2. then define what is allowed and how it changes over time
3. then operationalize those transitions and maintenance loops

</plan_breakdown>

<testing_guidance>
## Testing Guidance

Most relevant active tests:
- `tests/agent/test_core2_provider_foundation.py`
- `tests/agent/test_core2_legacy_adapted.py`

Most relevant seed patterns for later adaptation:
- namespace policy
- canonicalization / conflicts
- current-state priority
- contradiction priority
- evidence chain
- memory object lifecycle

Avoid pulling benchmark, graph-heavy, or retrieval-contract seed tests into this phase; those belong later.

</testing_guidance>

<risks>
## Risks And Failure Modes

- Reusing the flat Phase 1 note table too long will make later retrieval and answer contracts brittle.
- Pushing policy logic into the provider file will recreate the old Hermes sprawl.
- Letting `derived_propositions` masquerade as canonical truth will violate the product laws.
- Mixing high-risk and low-risk handling too early at query-time instead of at data semantics time will cause unsafe shortcuts in Phase 3.

</risks>

<open_questions>
## Open Questions

- Whether `derived_propositions` in Phase 2 should be fully persisted or introduced as an explicitly limited scaffold
- How much `retrieval_indices` schema should be materialized now versus stubbed for Phase 3
- Whether activation decay belongs fully in Phase 2 or only its durable state model does

These are implementation choices, not blockers. The phase plan should make the minimum strong move that preserves the spec and avoids later rewrites.

</open_questions>

---

*Phase: 02-memory-model-and-state-semantics*
*Research completed: 2026-04-06*
