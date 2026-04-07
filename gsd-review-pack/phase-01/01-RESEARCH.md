# Phase 1: Core2 Provider Foundation - Research

**Researched:** 2026-04-06
**Domain:** Hermes memory provider foundation in an existing brownfield agent runtime
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Core2 must remain an external memory provider plugin under `plugins/memory/core2/`, not a scattered patch set.
- Native Hermes files should receive only thin wiring changes needed to activate and lifecycle-manage Core2.
- Phase 1 must start from the already-present Core2 stub and make `agent.core2_runtime.Core2Runtime` real and stable.
- Core2 must honor the existing `MemoryProvider` and `MemoryManager` contract.
- Phase 1 must add baseline tests for provider loading, runtime initialization, and lifecycle integration.
- Legacy kernel-memory tests under `.planning/legacy-test-seeds/kernel-memory/` are reference material, not directly activated tests.

### the agent's Discretion
- Exact internal module split between `agent/` and `plugins/memory/core2/`
- Initial local storage layout
- Test adaptation strategy from the legacy seed corpus

### Deferred Ideas (OUT OF SCOPE)
- Full multi-plane semantics
- Retrieval routing and answer contracts
- Benchmark/proof ladder execution

</user_constraints>

<research_summary>
## Summary

The repo already contains the correct architectural seam for Core2: `MemoryProvider`, `MemoryManager`, plugin discovery, runtime activation, and memory setup UX. Phase 1 should not redesign these seams. The safest standard approach is to turn the existing Core2 stub into a stable provider package with a small local runtime, explicit storage path handling, deterministic tool schemas, and test coverage proving lifecycle correctness.

The strongest immediate issue is concrete, not theoretical: `plugins/memory/core2/__init__.py` imports `agent.core2_runtime.Core2Runtime`, but `agent/core2_runtime.py` is currently absent. That means the current Core2 provider is structurally present but not foundation-complete. Phase 1 should therefore prioritize import/runtime integrity, provider activation, and test-backed wiring over adding more kernel semantics.

**Primary recommendation:** Treat Phase 1 as “make the stub real and testable” rather than “invent Core2 architecture from scratch.”
</research_summary>

<standard_stack>
## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib `sqlite3` | stdlib | local-first persistence for foundation and testable runtime state | already used successfully in existing memory plugin tests; no extra dependency burden |
| Existing Hermes `MemoryProvider` contract | repo-native | lifecycle/API boundary for external memory | already consumed by runtime, CLI, and tests |
| Existing Hermes plugin layout | repo-native | provider discovery and metadata | avoids bespoke activation paths |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pytest` | repo-existing | provider and lifecycle tests | baseline and integration tests |
| existing SQLite plugin test patterns | repo-existing | E2E reference pattern | when proving provider lifecycle and recall/write behavior |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| stdlib local persistence for Phase 1 | external DB or vector DB immediately | adds dependency and setup complexity too early |
| plugin/provider boundary | direct runtime embedding in `run_agent.py` | increases merge debt and violates brownfield constraints |

**Installation:**
```bash
source venv/bin/activate
pytest tests/agent/test_memory_provider.py tests/agent/test_memory_plugin_e2e.py
```
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Recommended Project Structure
```text
plugins/memory/core2/
├── __init__.py          # provider registration + tool schemas
├── plugin.yaml          # provider metadata

agent/
├── core2_runtime.py     # runtime entry and session-facing API
├── core2_store.py       # local persistence primitives
├── core2_types.py       # packet/object/state dataclasses or typed structs
└── core2_paths.py       # Hermes-home-aware path helpers (optional)
```

### Pattern 1: Thin Provider, Explicit Runtime
**What:** Keep `plugins/memory/core2/__init__.py` focused on the provider interface and delegate real work to a runtime object.
**When to use:** Always, because the provider contract is stable but the kernel internals will evolve quickly.

### Pattern 2: Local-First Runtime With Incremental Semantics
**What:** Use a simple durable local store in Phase 1 that can later back richer planes without changing the provider API.
**When to use:** Foundation work where correctness of lifecycle and persistence matters more than full semantic richness.

### Anti-Patterns to Avoid
- **Provider as god object:** putting storage, routing, ingestion, and answer synthesis all into `plugins/memory/core2/__init__.py`
- **Runtime-patch sprawl:** scattering Core2-specific business logic across `run_agent.py`, `gateway/run.py`, and CLI files
- **Legacy test dump into active suite:** copying old tests directly into `tests/agent/` before adapting them to current contracts
</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| provider activation path | custom Core2 loader | existing plugin discovery/loading in `plugins/memory/__init__.py` | runtime already expects this seam |
| memory lifecycle orchestration | bespoke Core2 manager | existing `agent/memory_manager.py` | avoids duplicate routing logic |
| baseline lifecycle test style | brand new bespoke harness | adapt `tests/agent/test_memory_plugin_e2e.py` and legacy seeds | proven local pattern already exists |

**Key insight:** Phase 1 wins by exploiting existing Hermes abstractions, not by bypassing them.
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Provider stub without executable runtime
**What goes wrong:** The plugin exists structurally but imports missing runtime modules and fails at activation.
**Why it happens:** Planning outruns foundation wiring.
**How to avoid:** Make import integrity and initialization tests first-class acceptance criteria.
**Warning signs:** `ImportError`, provider loads in discovery metadata but not at runtime.

### Pitfall 2: Foundation phase accidentally expands into full kernel semantics
**What goes wrong:** Phase 1 balloons into planes, routing, and evidence logic before the boundary is stable.
**Why it happens:** The product spec is ambitious and easy to over-pull into the first batch.
**How to avoid:** Keep Phase 1 limited to provider/runtime/storage scaffolding and lifecycle proof.
**Warning signs:** Plans start adding retrieval policy matrices or full truth models.

### Pitfall 3: Brownfield runtime regressions from deep edits
**What goes wrong:** Memory foundation work destabilizes unrelated CLI/gateway behavior.
**Why it happens:** Orchestrator files are large and cross-cutting.
**How to avoid:** Restrict runtime changes to thin activation/wiring edits and verify with targeted tests.
**Warning signs:** large diffs in `run_agent.py` or `gateway/run.py` that contain business logic, not wiring.
</common_pitfalls>

<code_examples>
## Code Examples

Verified repo patterns from local sources:

### Provider lifecycle contract
```python
class MemoryProvider(ABC):
    @abstractmethod
    def initialize(self, session_id: str, **kwargs) -> None: ...
    def prefetch(self, query: str, *, session_id: str = "") -> str: ...
    def queue_prefetch(self, query: str, *, session_id: str = "") -> None: ...
    def sync_turn(self, user_content: str, assistant_content: str, *, session_id: str = "") -> None: ...
    @abstractmethod
    def get_tool_schemas(self) -> List[Dict[str, Any]]: ...
```

### Manager registration rule
```python
if not is_builtin:
    if self._has_external:
        logger.warning(...)
        return
    self._has_external = True
```

### Real plugin E2E test style
```python
mgr = MemoryManager()
builtin = BuiltinMemoryProvider()
sqlite_mem = SQLiteMemoryProvider()
mgr.add_provider(builtin)
mgr.add_provider(sqlite_mem)
mgr.initialize_all(session_id=\"test-session-1\", platform=\"cli\")
```
</code_examples>

<sota_updates>
## State of the Art (2024-2025)

For this phase, “state of the art” means architectural discipline rather than external library churn:

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| scattered backend-specific memory code | unified provider/manager seam | already present in current repo | Core2 should plug into the seam, not recreate old sprawl |
| implicit memory wiring | explicit plugin/provider contract | already present in current repo | makes Phase 1 mostly an integration-hardening problem |

**New tools/patterns to consider:**
- Local SQLite-backed or similarly simple durable state for the foundation phase
- Dataclass/typed packet layer for recall results and ingest outcomes so later phases do not mutate public payload shape chaotically

**Deprecated/outdated:**
- Treating provider stubs as “good enough” without runtime-import proof
- Copying huge legacy test sets directly into active collection without adaptation
</sota_updates>

<open_questions>
## Open Questions

1. **Where exactly should Core2 internal modules live?**
   - What we know: provider boundary should remain under `plugins/memory/core2/`
   - What's unclear: whether runtime/store/types belong under `agent/` or provider-local submodules
   - Recommendation: choose the split that keeps import paths stable and business logic isolated from orchestrators

2. **How much persistence semantics should Phase 1 include?**
   - What we know: local-first durable initialization is required
   - What's unclear: whether Phase 1 stops at basic state tables or introduces early canonical-object schema
   - Recommendation: implement only what is needed to make provider/runtime lifecycle real and future-proof, not the full plane model
</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- `plugins/memory/core2/__init__.py` — existing Core2 provider stub
- `plugins/memory/core2/plugin.yaml` — existing Core2 metadata
- `agent/memory_provider.py` — provider contract
- `agent/memory_manager.py` — manager orchestration
- `run_agent.py` — activation and lifecycle hook locations
- `tests/agent/test_memory_provider.py` — interface and manager tests
- `tests/agent/test_memory_plugin_e2e.py` — real-plugin local integration pattern
- `plan7vegrehajt.md` / `plan6.md` — governing product and invariant docs

### Secondary (MEDIUM confidence)
- `.planning/codebase/ARCHITECTURE.md`
- `.planning/codebase/STRUCTURE.md`
- `.planning/codebase/CONCERNS.md`
- `.planning/legacy-test-seeds/kernel-memory/*`

### Tertiary (LOW confidence - needs validation)
- None for this phase; the planning surface is already driven by repo-local and user-provided canonical docs.
</sources>

<metadata>
## Metadata

**Research scope:**
- Core technology: Hermes external memory provider foundation
- Ecosystem: provider discovery, manager lifecycle, setup/runtime activation, test harness patterns
- Patterns: thin provider, explicit runtime, local-first durable bootstrap
- Pitfalls: import breakage, scope explosion, brownfield regressions

**Confidence breakdown:**
- Standard stack: HIGH - driven by current repo architecture
- Architecture: HIGH - direct repo evidence
- Pitfalls: HIGH - visible from current code and stub state
- Code examples: HIGH - local source-based

**Research date:** 2026-04-06
**Valid until:** 2026-05-06
</metadata>

---

*Phase: 01-core2-provider-foundation*
*Research completed: 2026-04-06*
*Ready for planning: yes*
