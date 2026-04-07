# MemPalace Adoption Matrix

## Purpose

This matrix decides where MemPalace should be adopted, adapted, or rejected relative to the current Core2 architecture.

Verdicts:

- `adopt as-is`
- `adapt into Core2`
- `keep Core2`
- `undecided`

## Matrix

| Layer | Current Core2 approach | MemPalace approach | Verdict | Rationale | Evidence strength | Complexity risk |
|---|---|---|---|---|---|---|
| Lossless raw storage / verbatim substrate | `raw_archive` exists but is not the project’s strongest differentiator | Verbatim drawers and closet/drawer substrate are first-class | `adapt into Core2` | MemPalace’s verbatim-first storage model looks stronger than current Core2 substrate ergonomics, but should be integrated under Core2 ownership rather than replacing the whole kernel | Strong | Medium |
| Ingest / chunking / routing | Write-time digestion is strong for truth-building, but raw substrate chunking/routing is comparatively narrow | Project/file/conversation miners with room routing | `adapt into Core2` | The ingest/routing ideas are useful, but Core2 still needs its own fact/state digestion after candidate extraction | Strong | Medium |
| Semantic retrieval / scoped filtering | Core2 retrieval is now strong on covered families but still less elegant for raw scoped search | Wing/room-filtered semantic search, plus optional rerank modes | `adapt into Core2` | This is the clearest near-term upgrade area for a bounded hybrid | Strong | Medium |
| Wake-up / compression / bootstrap context | Core2 has no equally clean L0-L3 wake-up story yet | Explicit L0-L3 layering and AAAK bootstrap | `adapt into Core2` | The layering concept is valuable, but AAAK itself should not be adopted blindly before proving fit | Moderate | Medium |
| Graph / navigation | Core2 does not have an equally developed navigation graph | Palace graph over rooms/halls/tunnels | `undecided` | Promising as a secondary retrieval/navigation aid, but not yet justified as must-have | Moderate | Medium |
| Temporal knowledge graph | Core2 already has temporal state semantics in its truth model | SQLite temporal KG with invalidation/query | `adapt into Core2` | Useful as a secondary graph/evidence substrate, but must not become a second truth authority | Strong | High if misused |
| Deterministic truth / state / provenance | Core2 hard axioms: identity, provenance, temporal state, conflict, supersession | Partial overlap via source references and KG, but no equally explicit hard-core boundary | `keep Core2` | This is a Core2 strength and should remain Core2-owned | Strong | High if replaced |
| Deterministic answer surface / abstention | Provider-owned answer surface, fail-closed abstention, structured provenance | No direct equivalent found | `keep Core2` | Core2 is clearly stronger here | Strong | High if replaced |
| Benchmark / evaluation harness | Hermes-path, answer-correctness-oriented, gate classified | Retrieval-oriented benchmark story with strong recall numbers | `keep Core2` | Keep the Core2 evaluator story; MemPalace benchmarks are useful as comparative evidence, not as a replacement gate | Strong | Low |
| MCP / operator surface | Core2 currently uses Hermes/provider surfaces | Rich MemPalace MCP tools and protocol | `adapt into Core2` | Some operator ergonomics and protocol design are worth borrowing, but not the entire tool surface wholesale | Moderate | Low |

## High-Confidence Verdicts

### MemPalace stronger than current Core2

- lossless raw substrate
- scoped semantic retrieval
- wake-up / bootstrap framing

### Core2 stronger than MemPalace

- deterministic truth / state / provenance
- deterministic answer surface
- abstention discipline
- answer-correctness gate model

### Likely best hybrid seam

- MemPalace-inspired substrate + retrieval
- Core2-owned truth/state + answer/handoff

## Explicit Non-Decisions

- This matrix does **not** authorize a wholesale MemPalace replacement.
- This matrix does **not** authorize a dual truth engine.
- This matrix does **not** assume AAAK becomes mandatory.
