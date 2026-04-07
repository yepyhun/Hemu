---
phase: 03-retrieval-and-answer-contracts
plan: 01
subsystem: retrieval
tags: [core2, routing, query-family, retrieval, bounded-dispatch]
requires:
  - phase: 02-memory-model-and-state-semantics
    provides: explicit planes, policy semantics, temporal/versioning state
provides:
  - Explicit query-family and route-plan types
  - Bounded route-family dispatch for retrieval
  - Inspectable retrieval metadata on returned packets
affects: [phase-3, phase-4, testing, memory]
tech-stack:
  added: []
  patterns: [query-family-routing, bounded-retrieval, route-plan-metadata]
key-files:
  created: [agent/core2_routing.py, tests/agent/test_core2_retrieval_routing.py]
  modified: [agent/core2_types.py, agent/core2_runtime.py, agent/core2_store.py]
key-decisions:
  - "Query family now chooses the retrieval route explicitly instead of reusing one broad canonical search path."
  - "Routing remains bounded and deterministic on top of the current store/edges layer instead of pretending to be a richer engine than the code actually provides."
patterns-established:
  - "Exact and high-risk flows use stricter source-first routing."
  - "Personal and exploratory flows remain distinct and inspectable."
requirements-completed: [RETR-01]
duration: 35min
completed: 2026-04-06
---

# Phase 3 Plan 01 Summary

**Core2 now routes queries through explicit query families and bounded route plans instead of treating every recall as the same generic search.**

## Accomplishments

- Added explicit query-family, route-family, and route-plan types to the Core2 contract.
- Introduced a dedicated routing layer for exact lookup, factual supported recall, personal recall, relation multihop, update resolution, high-risk strict recall, and exploratory discovery.
- Added active routing tests proving strict, compact, temporal-aware, and graph-assisted retrieval paths remain inspectable and bounded.

## Files Created/Modified

- `agent/core2_types.py` - query family, route family, delivery-view, and route-plan typing
- `agent/core2_routing.py` - bounded routing logic and query-family dispatch
- `agent/core2_runtime.py` - route-aware recall flow and retrieval shaping
- `agent/core2_store.py` - retrieval helpers used by route-aware recall
- `tests/agent/test_core2_retrieval_routing.py` - active tests for route dispatch and bounded retrieval

## Issues Encountered

- Repo-local git identity is still unset, so no atomic commits were created.

## Next Phase Readiness

- Typed answer assembly can now consume explicit route metadata instead of inventing behavior at the provider edge.

---
*Phase: 03-retrieval-and-answer-contracts*
*Completed: 2026-04-06*
