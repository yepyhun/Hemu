# Core2 Axioms

## Purpose

This document defines the smallest hard deterministic core that Core2 claims as v1 kernel behavior.

It is intentionally narrower than “all memory intelligence.” Raw language understanding, broad semantic reasoning, and benchmark judging are outside this hard core unless explicitly stated otherwise.

## Hard Deterministic Core

### AX-01: Stable Fact Identity

Every covered durable-memory record that Core2 treats as first-class memory must have a stable typed identity:

- fact family/type
- fact key or equivalent stable selector
- inspectable payload shape

Core2 must not claim deterministic handling for an object that has no stable structured identity.

### AX-02: Provenance

Every structured fact used as durable truth must preserve source lineage:

- where it came from
- which source memory object or event produced it
- enough metadata to explain why the kernel believes it exists

### AX-03: Temporal State

For covered durable-memory facts, Core2 must represent state explicitly rather than hiding overwrite behavior in prose:

- `current`
- `previous`
- `superseded`

### AX-04: Conflict Is First-Class

When two claims cannot be safely merged by the kernel’s deterministic rules, the result must be represented as conflict or unresolved state, not silently collapsed into one “truth.”

### AX-05: Deterministic Supersession

When a newer covered fact validly replaces an older one under explicit kernel rules, the transition must be deterministic and inspectable.

### AX-06: Fact-First Recall For Covered Families

For covered durable-memory families, recall must prefer the structured fact substrate before broader raw-style retrieval.

### AX-07: Fail-Closed Answer Surface

If Core2 emits a deterministic answer surface for a covered case, it must be grounded in structured kernel objects.

If the structured base is insufficient, Core2 must fall back or abstain instead of pretending it resolved the answer deterministically.

### AX-08: Abstention

If the structured support is insufficient for a safe answer, the kernel must abstain or explicitly fall back; it must not bluff.

## Explicitly Outside The Hard Core

These may still exist in the system, but they are not claimed as deterministic kernel guarantees:

- raw text -> fact candidate extraction
- broad semantic matching
- relation/graph proposal
- summarization
- fuzzy ranking for weak matches
- final stylistic phrasing
- external benchmark judge behavior

## Boundary Rule

The hard deterministic boundary begins after candidate extraction.

Core2 does not claim to fully formalize arbitrary natural-language understanding in v1. It does claim deterministic handling once a covered structured candidate or fact exists inside the kernel substrate.

