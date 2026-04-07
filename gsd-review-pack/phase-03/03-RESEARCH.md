# Phase 3: Retrieval And Answer Contracts - Research

**Researched:** 2026-04-06
**Domain:** Core2 retrieval routing and typed answer behavior on top of the Phase 2 state model
**Confidence:** HIGH

<user_constraints>
## User Constraints

### Locked Constraints
- The target is a production-grade, SOTA-aspirational memory kernel, not a thin recall wrapper.
- `plan7vegrehajt.md` is the primary execution spec; `plan6.md` remains a hard guardrail document.
- Core2 must stay modular and upstream-friendly, with business logic isolated in `agent/core2_*`.
- Accuracy, provenance, abstention, and support-tier discipline outrank convenience and token savings.
- Phase 3 must stop short of Phase 4 proof and benchmark scope.

</user_constraints>

<phase_scope>
## Phase 3 Must Deliver

The roadmap and requirements make this phase responsible for:
- `RETR-01`: query-family routing across the required retrieval families
- `RETR-02`: answer-mode differentiation and abstention behavior
- `RETR-03`: typed answers with provenance and confidence dimensions
- `RETR-04`: token-budget and retrieval-cap enforcement
- `TIME-03`: stricter temporal behavior in high-risk namespaces

Concretely, Phase 3 must replace the current one-route recall function with an explicit routing and answer-contract layer that can explain why a query took a route, what evidence it used, and when it must abstain.

</phase_scope>

<current_state>
## Current Code Reality

Phase 2 already established:
- a plane-aware Core2 store
- namespace/trust/temporal policy
- durable state transitions and maintenance loops
- active targeted pytest coverage

Current gaps relevant to Phase 3:
- `agent/core2_runtime.py` still performs one broad `search_canonical()` pass rather than route-family dispatch
- query family is not represented explicitly
- `operator` is accepted but not yet used for typed answer assembly
- answer output is still a recall packet, not the full typed answer contract from the spec
- confidence dimensions exist but remain coarse and are not tied to explicit route/evidence decisions
- token-budget discipline is only a `max_items` clamp, not a real answer contract
- delivery views exist in storage but are not yet the governing answer surface
- prefetch is still a hardcoded compact recall shortcut rather than a route-aware delivery policy

</current_state>

<non_negotiables>
## Non-Negotiable Semantics From `plan7vegrehajt.md`

- route families must be explicit and query-aware
- canonical query families must choose the route
- high-risk queries must use stricter source-first and temporal behavior
- abstention is mandatory when evidence, temporal clarity, conflict resolution, or chain completeness fail
- confidence is multi-dimensional, not one scalar
- the answer contract must expose typed fields and provenance
- delivery views render supported outputs but must not invent evidence
- token budgets and expansion limits are part of the retrieval constitution
- relation and multi-hop routes must protect completeness, not just nearest-match recall

</non_negotiables>

<recommended_structure>
## Recommended Implementation Shape

Preserve the Phase 1 and Phase 2 modular pattern and extend it rather than pushing logic into the provider:

- `agent/core2_types.py`
  - query-family identifiers
  - route-plan metadata
  - typed answer packet fields
- `agent/core2_runtime.py`
  - orchestrates route selection, retrieval execution, and answer assembly
- optional new helpers:
  - `agent/core2_routing.py` for route-family selection and bounded retrieval plans
  - `agent/core2_answer.py` for typed answer assembly and display shaping
  - `agent/core2_budget.py` if token-budget logic needs isolation
- `agent/core2_store.py`
  - adds the minimal retrieval helpers needed for route-aware search and delivery-view reads
- `plugins/memory/core2/__init__.py`
  - stays thin and only adapts the typed packet to the tool boundary

This keeps routing and answer behavior inspectable while preserving the provider seam.

</recommended_structure>

<plan_breakdown>
## Best 3-Plan Split

### Plan 03-01
Implement the retrieval routing matrix, query-family identification, and bounded route execution.

### Plan 03-02
Implement typed answer assembly with explicit support tiers, confidence metadata, and provenance payloads.

### Plan 03-03
Implement abstention, token-budget, delivery-view, and high-risk temporal enforcement, then prove the contract with active tests.

This order follows the product contract:
1. first choose the right route
2. then produce the right typed answer
3. then enforce the strict delivery and abstention laws

</plan_breakdown>

<testing_guidance>
## Testing Guidance

Most relevant active tests:
- `tests/agent/test_core2_provider_foundation.py`
- `tests/agent/test_core2_legacy_adapted.py`
- `tests/agent/test_core2_temporal_policy.py`

Most relevant new test themes for Phase 3:
- exact lookup vs factual supported vs personal recall routing
- update resolution and high-risk strict routing
- typed answer fields and grounding refs
- abstention triggers for weak evidence, conflict, unresolved recency, and incomplete chains
- token-budget and item-cap enforcement
- delivery view selection for compact, supported, and exploratory responses

Avoid Phase 4 drift:
- do not turn these tests into benchmark harnesses
- do not claim embedding superiority or large-corpus proof in this phase

</testing_guidance>

<risks>
## Risks And Failure Modes

- Leaving retrieval as one canonical search pass with cosmetic labels will fail the retrieval constitution.
- Letting answer assembly invent unsupported summaries will violate the source-grounded core value.
- Treating token budget as only `max_items` will create hidden prompt blowups later.
- Allowing compact-only output in high-risk domains will undermine the whole policy model.
- Overpromising full graph or semantic sophistication in Phase 3 will create brittle pseudo-routes instead of a clean contract.

</risks>

<open_questions>
## Open Questions

- How much relation or graph-assisted retrieval is feasible in Phase 3 using the current edge set without introducing a new retrieval engine
- Whether query-family inference should stay heuristic-first in the runtime or be partially explicit via tool args later
- Whether prefetch should always use a curated compact delivery view or remain query-family aware when risk is elevated

These are implementation choices, not blockers. The phase plan should make the smallest strong move that preserves the routing and answer contract for later hardening.

</open_questions>

---

*Phase: 03-retrieval-and-answer-contracts*
*Research completed: 2026-04-06*
