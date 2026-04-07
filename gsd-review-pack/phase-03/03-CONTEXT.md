# Phase 3: Retrieval And Answer Contracts - Context

**Gathered:** 2026-04-06
**Status:** Ready for planning
**Source:** Project roadmap + `plan7vegrehajt.md` primary spec + `plan6.md` execution guardrails

<domain>
## Phase Boundary

Phase 3 turns the Phase 2 Core2 state model into an explicit retrieval and answer system.

This phase must implement query-family routing, route-aware retrieval behavior, typed answer packets, abstention rules, delivery-view selection, and token-budget discipline on top of the existing plane-aware Core2 runtime. It must keep the logic inside isolated `agent/core2_*` modules and preserve the thin Hermes provider boundary.

This phase does **not** deliver the full proof ladder, benchmark harnesses, scaled telemetry reporting, or broad performance hardening. Those remain in Phase 4.

</domain>

<decisions>
## Implementation Decisions

### Locked Decisions
- `plan7vegrehajt.md` is the primary Phase 3 product contract.
- `plan6.md` constrains execution style, cue-first retrieval, completeness discipline, and abstention behavior, but does not override the more concrete routing and answer semantics in `plan7vegrehajt.md`.
- Query family chooses the route; route choice must not drift based on benchmark convenience.
- `exact_source_required`, `source_supported`, `compact_memory`, and `exploratory_full` are distinct answer behaviors, not one shared response path with different labels.
- High-risk queries must use stricter routing, temporal checks, contradiction checks, and abstention behavior than standard personal/project recall.
- Delivery views may render or compress supported content, but they may not invent evidence, rewrite truth, or silently downgrade a strict mode into a compact-only answer.
- Token budgets and retrieval caps are contractual limits, not advisory defaults.
- Phase 3 may add route-plan metadata and typed answer assembly, but must not turn into a benchmark or eval phase.

### the agent's Discretion
- Exact helper module split inside `agent/core2_*`
- Whether routing lives primarily in `core2_runtime.py` or in a dedicated `core2_routing.py`
- How much of exploratory or relation-heavy routing is delivered as a bounded deterministic first pass versus deferred deeper expansion
- Whether typed answer assembly lives in a dedicated `core2_answer.py` or inside the runtime with clear isolation

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Product contract
- `plan7vegrehajt.md` - primary Core2 execution spec, including routing families, answer contract, abstention rules, and token-budget constraints
- `plan6.md` - execution constitution, cue-first retrieval guardrails, completeness rules, and anti-shortcut constraints

### Project requirements and roadmap
- `.planning/ROADMAP.md` - Phase 3 goal, requirement IDs, and success criteria
- `.planning/REQUIREMENTS.md` - `RETR-*` and `TIME-03` requirements
- `.planning/PROJECT.md` - active constraints and architectural decisions
- `.planning/STATE.md` - current project position and blockers

### Existing code and boundaries
- `plugins/memory/core2/__init__.py` - Core2 tool/provider boundary
- `agent/core2_runtime.py` - current recall path and prefetch behavior
- `agent/core2_policy.py` - current recall gating and high-risk checks
- `agent/core2_store.py` - current canonical search, delivery-view storage, and edge data
- `agent/core2_types.py` - current typed recall packet
- `agent/memory_provider.py` - provider lifecycle and prefetch contract
- `agent/memory_manager.py` - provider orchestration and prefetch aggregation

### Existing tests
- `tests/agent/test_core2_provider_foundation.py` - active provider and prefetch tests
- `tests/agent/test_core2_legacy_adapted.py` - active legacy-inspired recall tests
- `tests/agent/test_core2_temporal_policy.py` - active high-risk and temporal gating tests
- `tests/agent/test_core2_state_transitions.py` - active state/lifecycle tests

</canonical_refs>

<specifics>
## Specific Ideas

- Route families should remain explicit:
  - `lexical/source-first`
  - `semantic-first`
  - `association/graph-assisted`
  - `curated_memory_view`
- Canonical query families should be routed explicitly:
  - `exact_lookup`
  - `factual_supported`
  - `personal_recall`
  - `relation_multihop`
  - `update_resolution`
  - `high_risk_strict`
  - `exploratory_discovery`
- Typed answer output should carry at least:
  - `answer_type`
  - `operator`
  - `query_mode`
  - `canonical_value`
  - `display_value`
  - `grounding_refs`
  - `confidence_tier`
  - `abstain_reason`
  - `risk_class`
  - `support_level`
- High-risk routes should additionally surface:
  - `valid_as_of`
  - `superseded_by`
  - `conflict_refs`
- Delivery views should be explicit render targets such as:
  - `final_compact`
  - `supported_compact`
  - `exploratory_full`
  - `artifact_rehydrate`
- Abstention triggers must include weak evidence, unresolved conflict, unclear temporal resolution, incomplete multi-hop chain, and unsupported high-risk recall.

</specifics>

<deferred>
## Deferred Ideas

- Full benchmark telemetry reporting and evaluation harnesses
- Embedding-model challenger work or retrieval bake-offs
- Deep graph expansion beyond bounded Phase 3 relation routing
- Final release hardening and large-corpus collapse proof

</deferred>

---

*Phase: 03-retrieval-and-answer-contracts*
*Context gathered: 2026-04-06*
