# Legacy Kernel Memory Test Seeds

These files were copied from:

- `/home/lauratom/Asztal/ai/hermes-agent-port/tests/agent/`

Copy date:

- `2026-04-06`

Purpose:

- Preserve the previous Hermes kernel/memory/replay test corpus as a reference set.
- Reuse assertions, fixtures, invariants, and scenario coverage during Core2 development.
- Avoid rewriting useful test ideas from zero.

Important:

- These are not active Core2 tests yet.
- They live under `.planning/` on purpose so `pytest` does not automatically collect and fail on legacy imports/contracts.
- Some files will be directly reusable with small edits; others will only serve as design/reference material.

Recommended reuse path:

1. When a Core2 module becomes stable, copy or adapt only the relevant legacy tests into `tests/agent/`.
2. Rewrite imports and contracts to match Core2 module boundaries.
3. Keep only tests that still express valid invariants for the new architecture.
4. Drop tests that encode obsolete implementation details from the older kernel.

Broad legacy buckets present here:

- `test_kernel_memory_*` — old kernel memory behavior and policies
- `test_decision_memory_*` — decision-memory extraction/render/retrieval flows
- `test_profile_memory_*` — profile-memory flows
- `test_native_memory_*` — native memory sync/reconciliation
- `test_replay_*` — replay/memory assembly and runtime behaviors
- benchmark/policy suites — useful for proof and eval inspiration
