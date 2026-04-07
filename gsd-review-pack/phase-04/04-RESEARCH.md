# Phase 4: Proof, Benchmarks, And Hardening - Research

## User Constraints

### Locked Constraints

- The target is not MVP; the kernel must be proven and hardened to a serious bar.
- Benchmarking must measure the real Hermes-integrated path.
- The repo is brownfield; keep native runtime edits thin and modular.
- The user expects explicit next-step guidance in the GSD flow.
- The memory should feel well-connected, graph-like, and coherent rather than like isolated records.

## Phase 4 Must Deliver

- broader automated regression coverage around the Core2 contract
- a real Hermes-path proof/benchmark harness
- explicit hardening around edge cases, release-readiness, and graph/relation quality

## Current Code Reality

Phase 3 already established:
- inspectable query-family routing
- typed answer contract fields
- abstention and delivery-view discipline
- a green targeted Core2 pytest suite (`30 passed`)

Current Phase 4 gaps:
- there is no Core2-specific end-to-end proof through the full Hermes runtime path yet
- benchmark/eval harnesses are not yet modernized around Core2
- broader regression coverage is still narrow and phase-targeted
- release-readiness evidence is incomplete, especially around performance, graph-like linkage, and edge-case stability
- full `uv`/git-dependency based proof remains environment-sensitive because of the offline `tinker` path

## Existing Anchors Worth Reusing

- `tests/agent/test_memory_plugin_e2e.py` proves the right integration shape today: provider registration, tool routing, sync, prefetch, and shutdown under `MemoryManager`
- legacy benchmark seeds show the intended benchmark direction:
  - Hermes kernel E2E benchmark
  - LongMemEval subset verification
  - replay/token-savings benchmark patterns
- `pyproject.toml` already defines a `dev` extra with the pytest stack; broader regression should stay aligned with that path where possible

## Recommended Implementation Shape

### Plan 04-01

Expand the automated test surface first:
- strengthen provider-manager integration coverage for Core2
- add regression tests that prove real memory-manager and provider behavior, not just isolated runtime units
- cover graph/relation and edge-case correctness that current phase tests do not fully stress

### Plan 04-02

Build Hermes-path proof and benchmark harnesses second:
- use Hermes runtime entrypoints and provider wiring
- establish deterministic local proof gates first
- add a clean seam for benchmark/eval slices such as LongMemEval-style verification

### Plan 04-03

Harden and package release evidence last:
- cover performance/correctness edge cases
- ensure graph-like linkage quality and abstention safety survive harder scenarios
- document warnings and environment-sensitive proof gates explicitly rather than burying them

## Testing Guidance

- Keep `.venv/bin/python -m pytest ... -n 0` as the reliable local verification baseline while the environment remains partially offline.
- Reuse the existing targeted Core2 suite and add broader E2E/regression files around it.
- Treat benchmark scripts as proof artifacts with assertions and inspectable outputs, not as ad hoc manual commands.

## Risks And Failure Modes

- A detached benchmark harness could accidentally measure model/provider behavior rather than Hermes+Core2 behavior.
- Overfitting to deterministic local tests could miss integration regressions in the real runtime path.
- Hardening could drift into architecture churn if the phase is allowed to reopen settled Phase 1-3 decisions.
- Offline dependency limits may block some proof layers; the plan must separate “environment blocked” from “not implemented”.

## Open Questions

- Which Hermes entrypoint is the cleanest benchmark harness anchor in this repo for Core2 without adding broad runtime surgery?
- How much of the legacy LongMemEval direction can be revived immediately versus only scaffolded in this phase?
- Which graph/relation quality assertions are strongest without inventing a brand-new retrieval engine?

These are implementation choices, not blockers. The phase should make the strongest proof/hardening move that stays honest to the current codebase.
