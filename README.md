Core2 memory kernel review handoff

What this package contains:
- `agent/` - the Core2 kernel implementation
- `plugins/memory/core2/` - the plugin entrypoint and manifest
- `tests/agent/test_core2_*.py` - Core2-focused tests
- `.planning/` - current GSD state, phase docs, gate status, and verification artifacts
- `plan6.md`, `plan7vegrehajt.md` - original design intent
- `docs/veela/veela.md` - relevant external architectural reference

Suggested reading order:
1. `plan7vegrehajt.md`
2. `.planning/STATE.md`
3. `.planning/phases/04.1-longmemeval-gate-and-performance-fixes/04.1-GATE-STATUS.json`
4. `agent/core2_runtime.py`
5. `agent/core2_digestion.py`
6. `agent/core2_authoritative.py`
7. `tests/agent/test_core2_longmemeval_benchmark.py`

Current status at handoff:
- Core2 kernel and tests are included as copied snapshots.
- The original source repo remains unchanged in place.
- This folder is intended for external code review only.

What we are trying to build:
- A modular long-term memory kernel for Hermes.
- The intended model is write-time digestion plus fact-first recall, not query-time improvisation over raw chat history.
- The target is fast, grounded answers for durable-memory questions such as personal facts, preferences, habits, collection/count facts, and temporal updates.

Where we are struggling:
- The internal Core2 tests are mostly green, and several real misses were fixed by moving more structure into write-time digestion.
- The remaining pain point is the boundary between "the kernel knows it" and "the final live gate accepts that answer cleanly."
- In other words: some failures no longer look like pure storage/retrieval failures, but more like answer-surface or handoff mismatches.

What we already tried:
- Added multi-plane storage semantics and state transitions.
- Added write-time fact digestion.
- Switched covered queries toward fact-first recall.
- Added deterministic answer-surface paths for covered durable-memory families.
- Added coverage contracts and gate-status artifacts to reduce vague "maybe it works" evaluation.
- Avoided growing the system by endlessly adding topic-specific families; when we extended it, we tried to do it only via generic reusable patterns.

What we want reviewed:
- Is the current architecture actually converging, or are we still masking a deeper design mistake?
- Is the split between raw archive, canonical truth, derived facts, and answer surface sensible, or too complicated for the value it provides?
- Are we pushing enough work into write-time/background processing, or is too much truth-making still happening too late?
- Does the fact-first recall plus deterministic answer-surface approach look like a sound direction, or is there a cleaner, simpler pattern we should adopt?
- If you had to simplify this system without losing the core goal, what would you remove first?

Useful review mindset:
- Please focus more on architecture, failure mode, and design tradeoffs than on style issues.
- We are especially trying to avoid another endless loop of benchmark-specific or family-specific patching.
