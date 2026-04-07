# Phase 4: Proof, Benchmarks, And Hardening - Context

## Phase Boundary

Phase 4 begins from a Core2 kernel that already has:
- a real Hermes memory-provider integration seam
- explicit planes, trust/namespace policy, temporal/versioning behavior, and maintenance loops
- explicit query-family routing
- typed answer contracts
- abstention, delivery-view, and bounded retrieval behavior
- active targeted pytest coverage for the above

This phase is not allowed to re-argue the Core2 architecture. Its job is to prove, harden, and benchmark the implemented kernel through the real Hermes runtime path.

## Implementation Decisions

### Locked Decisions

- `plan7vegrehajt.md` remains the primary product contract for proof, benchmark, and release acceptance.
- `plan6.md` remains the guardrail document for anti-shortcut behavior, abstention discipline, and anti-Frankenstein execution style.
- Benchmarks and proof gates must run through Hermes itself, not a model-only shortcut or detached toy harness.
- Phase 4 must reuse existing Hermes provider/runtime seams and the current Core2 implementation rather than inventing a separate benchmark-only architecture.
- Proof work must distinguish:
  - local deterministic proof
  - Hermes-path integration proof
  - benchmark/eval proof
  - release-readiness hardening
- Existing targeted Core2 tests are a base, not the endpoint.
- Graph-like linkage and relation quality matter in hardening; the memory should not degrade into isolated records even if individual tests pass.

### The Agent's Discretion

- Exact benchmark dataset slice size and local proof scale can be chosen pragmatically as long as the path remains Hermes-integrated and inspectable.
- If the environment still blocks a full `uv`/git dependency path, plan around deterministic local proofs first and leave the environment-sensitive gate explicit rather than hidden.

## Canonical References

### Product contract

- `plan7vegrehajt.md`
- `plan6.md`

### Project requirements and roadmap

- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/PROJECT.md`
- `.planning/STATE.md`

### Existing code and boundaries

- `agent/memory_manager.py`
- `agent/memory_provider.py`
- `plugins/memory/core2/__init__.py`
- `agent/core2_runtime.py`
- `agent/core2_store.py`
- `agent/core2_answer.py`
- `agent/core2_routing.py`

### Existing proof and benchmark anchors

- `tests/agent/test_memory_plugin_e2e.py`
- `tests/agent/test_core2_provider_foundation.py`
- `tests/agent/test_core2_retrieval_routing.py`
- `tests/agent/test_core2_answer_contract.py`
- `tests/agent/test_core2_abstention_delivery.py`
- `.planning/legacy-test-seeds/kernel-memory/test_hermes_kernel_e2e_benchmark.py`
- `.planning/legacy-test-seeds/kernel-memory/test_hermes_longmemeval_benchmark.py`
- `.planning/legacy-test-seeds/kernel-memory/test_replay_benchmarks.py`

## Specific Ideas

- Extend the existing memory-plugin E2E pattern so Core2 is exercised through `MemoryManager`, tool routing, sync/prefetch, and provider coexistence rules.
- Build benchmark/proof harnesses that compare Hermes+Core2 behavior through real agent/runtime entrypoints, not detached object-level calls alone.
- Use a deterministic subset first for local proof, then leave a clear seam for larger benchmark/eval runs.
- Harden relation/graph behavior, abstention edge cases, and large-context retrieval boundaries before calling the kernel release-ready.

## Deferred Ideas

- Full public benchmark packaging or publishable SOTA claims; that belongs after the in-repo proof gates are genuinely stable.
- Expanding to multi-provider topologies; still out of scope for v1.
