# Core2 Memory Kernel — Review Repository

> **What is this?**
> This is the public review mirror of an experimental, local-first long-term memory kernel built for the [Hermes Agent](https://github.com/NousResearch/hermes-agent) architecture. It is a complete rewrite of a previous 30,000-line memory system — distilled down to ~6,800 lines across 13 focused modules.

---

## The Concept

Most agent memory systems eventually become Frankenstein stacks: layers of half-working partial solutions, patched together until they are unmaintainable.

Core2 is the attempt to avoid that.

The core idea is simple: **truth flows in one direction, through five clean planes.**

```
Raw Archive → Canonical Truth → Derived Propositions → Retrieval Indices → Delivery Views
```

Every memory write knows its place. Every query knows what it is allowed to touch. Token budgets are hard-coded into the type system, not bolted on later. Retrieval routing is decided upfront by the query's *family*, not by the most recent benchmark quirk.

The result is a kernel that is:
- **~5× smaller** than its predecessor
- **Bounded by design** — no infinite loops, hard retrieval caps, token budget profiles
- **Multilingual-neutral** — no English cue lists in the core; locale adapters only
- **Local-first** — SQLite, zero devops, runs on a laptop
- **Truth-disciplined** — provenance, temporal validity, and explicit supersession are first-class citizens, not afterthoughts

---

## Where We Are Now

The kernel has gone through **7 hardening phases** (04.1 → 04.7).

### Phase 04.6 — Core Axioms & Handmade Acceptance ✅

The goal here was to stop depending entirely on the paid external evaluator (LongMemEval) to tell us whether we are moving in the right direction.

**What was built:**
- `CORE2-AXIOMS.md` — a short, explicit list of what the kernel guarantees *deterministically* (structured state, supersession, conflict, abstention, covered fact-first behavior)
- `CORE2-HANDMADE-BENCH.md` + `CORE2-HANDMADE-BENCH.json` — 8–12 real hand-written memory cases with explicit expected outcomes, no LLM judging required
- `CORE2-GOLDEN-PATHS.md` — reference traces showing the happy path from memory ingest to answer surface
- `CORE2-GLOSSARY.md` — a tiny vocabulary so terms like `family`, `candidate`, `answer surface`, and `handoff miss` don't drift across sessions
- `CORE2-GATE-MATRIX.md` — a fail-closed classification of every remaining miss: `kernel correctness` / `handoff/format` / `judge artifact` / `unknown`

The phase closed with all four new requirements green (`AX-01`, `AX-02`, `QUAL-06`, `QUAL-07`).

### Phase 04.7 — Authoritative Gate Compatibility ✅

After 04.6 established the axiom layer, there was still a narrow remaining issue: the kernel was producing correct *promptless authoritative answers* (direct short-circuit answers from structured memory, with zero LLM API calls), but the external evaluator was misclassifying some of these as `judge: unknown` instead of counting them as passes.

**What was built:**
- A deterministic local comparator for promptless authoritative answers — strict, no "close enough" soft matching
- Explicit tagging of short-circuit cases in run artifacts so they cannot be confused with ordinary prompt misses
- Fail-closed handling of ambiguous judge responses

**Verification results:**
- `38 passed` in local test suite
- `5/5` canary cases green
- Promptless authoritative path confirmed: **0 API calls, 100% answer surface hit rate**

The previously failing preference and trip-order canary cases now pass under strict local comparison rather than soft evaluator ambiguity.

**Next step:** Resume Phase 04.1 for the next full paid LongMemEval rerun.

---

## What to Look At

If you want to understand the kernel, this is the recommended reading order:

| What | Where |
|---|---|
| The product contract (what this is and is not) | [`plan7vegrehajt_EN.md`](./plan7vegrehajt_EN.md) |
| The anti-loop and anti-Frankenstein guardrails | [`plan6_EN.md`](./plan6_EN.md) |
| Type system, constants, budget profiles | [`core2_types.py`](./core2_types.py) |
| SQLite persistence + BM25-style search | [`core2_store.py`](./core2_store.py) |
| Query routing decisions | [`core2_routing.py`](./core2_routing.py) |
| Namespace, risk, state classification | [`core2_policy.py`](./core2_policy.py) |
| Write-time fact digestion | [`core2_digestion.py`](./core2_digestion.py) |
| Authoritative answer surface | [`core2_authoritative.py`](./core2_authoritative.py) |
| Main orchestrator | [`core2_runtime.py`](./core2_runtime.py) |

---

## Key Design Decisions — Open Questions

If you are reading this as a reviewer or potential contributor, these are the honest open questions:

1. **Are 5 canonical object types enough at scale?** (`entity`, `event`, `state`, `measure`, `source`) — Strong hypothesis, not yet proven at 5k-book corpus size.
2. **When does the proposition/claim layer become necessary?** It is explicitly deferred — but relation and multi-hop queries will force this decision eventually.
3. **Which local embedding model wins on this hardware?** Default is Jina-v5-class; `BAAI/bge-m3` and `intfloat/multilingual-e5-large` are the defined challengers.
4. **Is the bitemporal model deep enough?** The minimal two-axis model (`event time` + `system time`) is in place. Deeper versioning may be needed for legal/medical corpora at scale.
5. **Is 38 passing tests + 5/5 canary enough to justify the next paid rerun?** That is the active question going into Phase 04.1.

---

## Repository Structure

```
core2_*.py          ← The kernel modules (copied from main repo)
agent/              ← Same files, agent/ subdirectory structure
tests/              ← Full test suite
plugins/            ← Hermes provider plugin seam
.planning/          ← Phase plans, verifications, gate artifacts
plan6_EN.md         ← Anti-loop execution constitution (English)
plan7vegrehajt_EN.md← Unified execution spec (English)
```

---

*This repository is a read-only review mirror. The primary development happens in the main Hermes agent fork.*
