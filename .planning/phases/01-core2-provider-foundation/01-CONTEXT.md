# Phase 1: Core2 Provider Foundation - Context

**Gathered:** 2026-04-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 1 establishes Core2 as a real Hermes memory provider with isolated modules and thin runtime wiring. It does not deliver the full multi-plane kernel yet; it delivers a stable foundation that can load, initialize, expose tools, persist local state, and participate correctly in the existing Hermes memory lifecycle.

</domain>

<decisions>
## Implementation Decisions

### Provider boundary
- **D-01:** Core2 must remain an external memory provider plugin under `plugins/memory/core2/`, not a scattered patch set across unrelated runtime files.
- **D-02:** Native Hermes files such as `run_agent.py` and `gateway/run.py` should receive only thin wiring changes needed to activate and lifecycle-manage Core2.

### Existing stub handling
- **D-03:** Phase 1 must start from the already-present `plugins/memory/core2/__init__.py` and `plugin.yaml` rather than replacing them blindly.
- **D-04:** The current Core2 provider stub references `agent.core2_runtime.Core2Runtime`; Phase 1 must make that import path real and stable.

### Runtime contract
- **D-05:** Core2 must honor the existing `MemoryProvider` and `MemoryManager` contract: initialize, prefetch, queue_prefetch, sync_turn, tool schemas, tool dispatch, on_memory_write, shutdown.
- **D-06:** Profile-aware local storage must use Hermes home paths rather than raw `~/.hermes` assumptions wherever possible.

### Quality and proof posture
- **D-07:** Phase 1 must add baseline tests for provider loading, runtime initialization, and lifecycle integration before broader kernel semantics are implemented.
- **D-08:** Legacy kernel-memory tests copied into `.planning/legacy-test-seeds/kernel-memory/` are reference material for reuse, not active tests to collect directly.

### the agent's Discretion
- Exact internal module split inside `agent/core2_*` or adjacent provider-local modules
- SQLite/schema layout for the initial local state as long as it supports later planes cleanly
- Whether certain foundation helpers live under `agent/` or `plugins/memory/core2/`, provided the provider boundary stays coherent

</decisions>

<specifics>
## Specific Ideas

- The project already contains `plugins/memory/core2/__init__.py` and `plugins/memory/core2/plugin.yaml`, so the practical goal is to turn the stub into a reliable canonical entry point.
- `plan7vegrehajt.md` is the primary execution spec; this phase only lays the groundwork for later memory planes, routing, and answer contracts.
- The repo already has memory-related tests in `tests/agent/test_memory_provider.py` and `tests/agent/test_memory_plugin_e2e.py`, plus a large legacy seed corpus under `.planning/legacy-test-seeds/kernel-memory/`.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project contract
- `.planning/PROJECT.md` — Core value, constraints, and brownfield integration rules
- `.planning/REQUIREMENTS.md` — Phase 1 requirement IDs `PROV-01`, `PROV-02`, `PROV-03`
- `.planning/ROADMAP.md` — Phase 1 goal, success criteria, and planned sub-work
- `.planning/STATE.md` — Current position and active blockers

### Core2 specification
- `plan7vegrehajt.md` — Primary execution spec for Core2 product scope, hard laws, and later batch boundaries
- `plan6.md` — Core2 execution constitution and proof/anti-loop constraints

### Existing architecture and code
- `AGENTS.md` — Repo-specific engineering constraints and file dependency chain
- `.planning/codebase/ARCHITECTURE.md` — Brownfield architectural boundary and memory integration seam
- `.planning/codebase/STRUCTURE.md` — Relevant directories and integration hotspots
- `.planning/codebase/CONCERNS.md` — Runtime pressure points and memory-surface risks
- `agent/memory_provider.py` — Abstract provider contract
- `agent/memory_manager.py` — Registration, tool routing, and lifecycle orchestration
- `plugins/memory/__init__.py` — Memory plugin discovery/loading path
- `plugins/memory/core2/__init__.py` — Existing Core2 stub provider
- `plugins/memory/core2/plugin.yaml` — Existing Core2 metadata
- `run_agent.py` — External memory provider activation and lifecycle hooks
- `hermes_cli/memory_setup.py` — Provider setup/discovery UX

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `agent/memory_provider.py`: already defines the exact lifecycle seam Core2 must honor
- `agent/memory_manager.py`: already manages builtin + one external provider and tool routing
- `tests/agent/test_memory_provider.py`: baseline interface and manager behavior tests
- `tests/agent/test_memory_plugin_e2e.py`: pattern for a real plugin lifecycle test with local SQLite

### Established Patterns
- Provider plugins live under `plugins/memory/<name>/` with `plugin.yaml` metadata
- Tool schemas are JSON-schema style and routed through the manager/provider boundary
- Hermes home/profile awareness is a project-wide requirement for persistent state

### Integration Points
- Provider discovery/loading in `plugins/memory/__init__.py`
- Runtime activation in `run_agent.py`
- Provider config/setup surfaces in `hermes_cli/memory_setup.py` and config
- Agent/gateway shutdown and lifecycle calls already wired around the memory manager

</code_context>

<deferred>
## Deferred Ideas

- Full multi-plane storage semantics (`raw_archive`, `canonical_truth`, `derived_propositions`, `retrieval_indices`, `delivery_views`) — Phase 2
- Retrieval routing, abstention, typed answer contract, and token-budget discipline — Phase 3
- End-to-end proof ladder, benchmark harnesses, and scaling validation — Phase 4

</deferred>

---

*Phase: 01-core2-provider-foundation*
*Context gathered: 2026-04-06*
