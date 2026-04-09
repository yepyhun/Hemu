# Phase 20 Research

## Reusable Inputs

### Old Hermes: likely borrowable primitives

- `agent/kernel_memory_projection_signals.py`
  - query hint terms
  - current-signal extraction
  - schedule-slot extraction
  - alias-driven query scope hints

- `agent/kernel_memory_objective_units.py`
  - temporal-label filtering
  - objective/unit normalization helpers
  - scope-like label shaping

These look borrowable because they are primitive-level helpers rather than whole-runtime ownership systems.

## Likely Complexity Traps

- whole legacy projection pipeline
- whole legacy truth/provenance universe
- any borrow that requires restoring the old kernel's full semantic contract

## External Systems

### MemPalace

Useful as a contrast model only:

- maybe the current system loses too much signal before retrieval
- maybe more verbatim or less aggressive admission loss matters

But Phase 20 must not become:

- a new architecture
- a store-everything rewrite
- a platform swap

### Mem0 / others

Good mostly as memory-layer and retrieval/rerank references, but not obvious drop-in fixes for the current upstream opening seam.

## Working Hypothesis

The strongest next bet is not a full import.

The strongest next bet is:

- codemap the old Hermes primitive helpers
- choose one primitive family that plausibly improves upstream candidate opening
- test it against a fixed representative `10`-case replay

## Planning Guardrail

If the codemap does not reveal one clean primitive borrow, the correct output of this phase is a stop verdict, not another speculative build.
