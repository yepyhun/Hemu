# Hemu — A Distilled Long-Term Memory Kernel

> **⚠️ Public review repository — not an MVP, not a release.** This is a snapshot of the kernel architecture and planning documents, shared for external review and discussion.

> *What if your AI agent actually remembered things correctly — not just approximately, not just recently, but with provenance, temporal validity, and the ability to say "I don't know" when it should?*

**Hemu** is an experimental long-term memory kernel for AI agents. It is a complete ground-up rewrite — not a wrapper, not an integration layer, not another vector store with a thin API on top. It is a minimal, disciplined memory engine that knows the difference between *what was true*, *what is true now*, and *what it cannot reliably answer*.

Built primarily for [Hermes Agent](https://github.com/NousResearch/hermes-agent), but designed modular enough to plug into any agent runtime.

---

## Why This Exists

Most agent memory systems start clean and become unmaintainable fast. You add chat history. Then semantic search. Then a knowledge graph. Then a summary cache. Then a conflict resolver. Then a fallback for when the resolver is wrong. Before long you have a Frankenstein stack of partial solutions, each half-working, patched together until no one can reason about what the agent actually *believes*.

The previous version of this system hit exactly that wall — ~30,000 lines across 70+ modules. Unfixable.

**Hemu is the compression.** Not a union of those ideas. A distillation of what was actually worth keeping, into ~6,800 lines across 13 modules.

---

## The Core Idea

Hemu synthesizes ideas from four research directions in memory systems:

| Inspiration | What we took |
|---|---|
| [**Mem0**](https://github.com/mem0ai/mem0) | Extract / consolidate / retrieve separation; local-first persistence |
| [**MemU**](https://github.com/Bai-YT/MemoryOS) | Write-time intelligence, query-time stays cheap and fast |
| [**PLUR**](https://plurresearch.com/) | Engram-style atomic memory units; hit/miss/feedback loops; temporal validity gates |
| [**CatRAG**](https://github.com/kwunhang/CatRAG) | Query-aware routing; completeness discipline — not just nearest-match retrieval |
| [**Graphiti**](https://github.com/getzep/graphiti) | Temporal knowledge graph design; bi-temporal edge modeling; entity resolution across sessions |

On top of these, Hemu adds a **bitemporal truth model** (when did this happen vs. when did the system learn it), explicit **supersession and conflict tracking**, and **knowledge graph-inspired activation** — memory units decay in relevance over time, and strong evidence promotes them back.

The result is something closer to how a second brain actually works than a chat log with embeddings.

---

## What Makes It Different

### 1. Truth flows in one direction

```
Raw Archive → Canonical Truth → Derived Propositions → Retrieval Indices → Delivery Views
```

No circular reads. No "query the raw archive as a fallback." Each plane has a defined job and is not allowed to do the job of the plane above it.

### 2. Routing is decided by the *question*, not the data

Seven query families — `exact_lookup`, `factual_supported`, `personal_recall`, `relation_multihop`, `update_resolution`, `high_risk_strict`, `exploratory_discovery` — each gets its own retrieval strategy, evidence requirements, and abstention policy. The router decides upfront. It does not try everything and pick the best-looking result.

### 3. Token savings are not a trade-off against accuracy

This is the part that actually matters for second-brain usage.

Most memory systems that claim token efficiency get there by **compressing truth** — shorter answers, fewer grounding refs, less evidence. Hemu gets there through **write-time intelligence**: the expensive understanding happens at ingestion time, in the background, asynchronously. By query time, the kernel hands back a structured typed answer — `canonical_value`, `grounding_refs`, `support_level`, `confidence_tier` — instead of a raw evidence blob that the LLM has to synthesize again.

In compact mode on short personal recall queries: **≥60% token savings** vs. replay-heavy baselines.  
In long synthesis scenarios: **≥90% savings**.  
Accuracy: higher, not lower — because the kernel knows when to abstain.

### 4. Tool-calling becomes cache-stable

One of the biggest hidden token costs in agentic systems is tool schema churn: sending the full tool list with every turn to maintain continuity. Hemu uses stable `tool_profile` objects and artifact-first rehydration — the agent refers to an artifact ID instead of re-serializing the full tool output into the prompt on every turn.

### 5. It knows when to say "I don't know"

Abstention is not a fallback. It is a first-class output. High-risk namespaces (medical, legal) have mandatory abstention policies. If temporal validity is unclear, if there's an unresolved conflict, if the evidence chain for a multi-hop query is incomplete — the kernel says so explicitly, rather than hallucinating confidence.

---

## Architecture at a Glance

```
core2_store.py          ← SQLite persistence, 5-plane schema, BM25-style search
core2_types.py          ← All constants, data classes, budget profiles (the "type constitution")
core2_routing.py        ← Query family classification and route plan selection
core2_policy.py         ← Namespace, risk class, support level, state classification
core2_digestion.py      ← Write-time fact extraction from conversation turns
core2_fact_registry.py  ← Covered fact families and canonical identity tracking
core2_authoritative.py  ← Structured answer surface construction
core2_runtime.py        ← Main orchestrator — retrieval, scoring, abstention
core2_answer.py         ← Typed answer packet assembly
core2_maintenance.py    ← Background dedupe, conflict detection, decay
```

**~6,800 lines. 13 modules. One person can hold it in their head.**

---

## Current Status

The kernel has completed **7 hardening phases** (04.1 → 04.7):

| Phase | What happened | Status |
|---|---|---|
| 04.1 | LongMemEval gate baseline + performance fixes | ✅ |
| 04.2 | Write-time fact digestion | ✅ |
| 04.3 | Fact-first recall routing | ✅ |
| 04.4 | Uncovered durable memory families | ✅ |
| 04.5 | Deterministic answer surface + gate closure | ✅ |
| 04.6 | Core axioms, handmade acceptance set, gate matrix | ✅ |
| 04.7 | Authoritative gate compatibility (promptless answers) | ✅ |

**Phase 04.7 results:**
- `38 passed` in local test suite
- `5/5` canary cases green
- Promptless authoritative path: **0 LLM API calls, 100% answer surface hit rate**

**Next:** Full paid LongMemEval rerun (Phase 04.1 resumed).

---

## Honest Open Questions

This is not a finished product. These are the real open questions:

1. **Are 5 canonical object types enough at scale?** (`entity`, `event`, `state`, `measure`, `source`) — Proven up to ~1k document corpus. 5k-scale is the next proof obligation.
2. **When does the proposition/claim layer become necessary?** Explicitly deferred — but complex relation and multi-hop queries will force this decision.
3. **Which local embedding model wins on commodity hardware?** Default: Jina-v5-class. Challengers: `BAAI/bge-m3`, `intfloat/multilingual-e5-large`.
4. **Is the bitemporal model deep enough for legal/medical corpora?** Two-axis model (`event time` + `system time`) is in. Deeper versioning is an open question.
5. **38 tests + 5/5 canary: is that enough to justify the next paid rerun?** That is the active question.

---

## Suggested Reading Order

| Document | Purpose |
|---|---|
| [`plan7vegrehajt_EN.md`](./plan7vegrehajt_EN.md) | Full product contract — what the kernel must be, and what it must never become |
| [`plan6_EN.md`](./plan6_EN.md) | Anti-loop constitution — how to avoid the Frankenstein trap |
| [`core2_types.py`](./core2_types.py) | The type system — understand budget profiles and answer contracts first |
| [`core2_routing.py`](./core2_routing.py) | 229 lines — the clearest entry point into how routing decisions work |
| [`core2_runtime.py`](./core2_runtime.py) | The main orchestrator — follow one query through the system |

---

## Repository Structure

```
core2_*.py              ← Kernel modules
agent/                  ← Same, in agent/ subdirectory layout
tests/                  ← Full test suite
plugins/                ← Hermes provider plugin seam
.planning/              ← Phase plans, verification reports, gate artifacts
  phases/04.6-*/        ← Core axioms, handmade benchmark, glossary, gate matrix
  phases/04.7-*/        ← Authoritative gate compatibility
plan6_EN.md             ← Anti-loop execution constitution (English translation)
plan7vegrehajt_EN.md    ← Unified execution spec (English translation)
```

---

*This is a read-only public review mirror — not an MVP, not a release candidate. Primary development is in the main Hermes agent fork.*  
*No API keys or secrets are present in this repository.*
