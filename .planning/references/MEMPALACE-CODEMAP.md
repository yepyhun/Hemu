# MemPalace Codemap

## Purpose

Compact, code-anchored map of the MemPalace layers relevant to Core2 adoption decisions.

This document is not a feature wishlist. It exists to support a layer-by-layer adoption matrix.

## Comparison Ontology

The shared comparison layers for Core2 vs MemPalace are:

1. Lossless raw storage / verbatim substrate
2. Ingest / chunking / routing
3. Semantic retrieval / scoped filtering / rerank
4. Wake-up / compression / bootstrap context
5. Graph / navigation
6. Temporal knowledge graph
7. Deterministic truth / state / provenance
8. Deterministic answer surface / abstention
9. Benchmark / evaluation harness
10. MCP / operator surface

## Layer Map

| Layer | MemPalace modules | What the code appears to do | Evidence strength |
|---|---|---|---|
| Lossless raw storage / verbatim substrate | `mempalace/miner.py`, `mempalace/convo_miner.py`, `mempalace/searcher.py` | Stores verbatim chunks as drawers in ChromaDB and returns exact drawer text on retrieval. | Strong |
| Ingest / chunking / routing | `mempalace/miner.py`, `mempalace/convo_miner.py`, `mempalace/normalize.py` | Reads local files or conversations, chunks them, detects rooms, and files them into the palace. | Strong |
| Semantic retrieval / scoped filtering / rerank | `mempalace/searcher.py`, `benchmarks/longmemeval_bench.py` | Semantic search over drawers with optional `wing` / `room` filters; benchmark harness also documents hybrid / rerank modes. | Strong for search, moderate for rerank |
| Wake-up / compression / bootstrap context | `mempalace/layers.py`, `mempalace/dialect.py`, `README.md`, `mempalace/mcp_server.py` | Defines L0-L3 recall stack, AAAK compression, and a wake-up/status protocol. | Moderate |
| Graph / navigation | `mempalace/palace_graph.py` | Builds a room-based navigation graph from Chroma metadata, including halls/tunnels across wings. | Strong |
| Temporal knowledge graph | `mempalace/knowledge_graph.py` | SQLite triples with temporal validity, invalidation, and entity-first queries. | Strong |
| Deterministic truth / state / provenance | No direct equivalent to Core2 hard-core axioms; partially touched by KG and protocol docs | MemPalace has temporal facts and source references, but not a Core2-style explicit deterministic truth/state boundary with stable supersession semantics. | Weak-to-moderate |
| Deterministic answer surface / abstention | No clear equivalent in source; retrieval tools return verbatim text and protocol guidance | MemPalace appears retrieval-first, not provider-owned deterministic answer-surface-first. | Weak |
| Benchmark / evaluation harness | `benchmarks/longmemeval_bench.py`, `README.md`, other benchmark scripts | Benchmark story is primarily retrieval quality, especially LongMemEval recall, with optional rerank variants. | Strong |
| MCP / operator surface | `mempalace/mcp_server.py` | Rich read/write/search/KG MCP tools and self-teaching status protocol. | Strong |

## Important Source Findings

### 1. Verbatim-first substrate

- `miner.py` explicitly says it stores verbatim chunks as drawers.
- `searcher.py` explicitly returns verbatim drawer content, not summaries.

### 2. Structured retrieval space

- `searcher.py` supports `wing` and `room` filters.
- `README.md` claims the wing/room structure materially improves retrieval.

### 3. Layered wake-up model

- `README.md` and `layers.py` define a layered memory stack:
  - L0 identity
  - L1 critical facts
  - L2 room recall
  - L3 deep search

### 4. Local graph options exist, but they are not obviously the truth kernel

- `knowledge_graph.py` is a local temporal graph with invalidation.
- `palace_graph.py` is a room/tunnel navigation layer.
- Neither alone establishes Core2-style truth/state guarantees.

### 5. Benchmark story is retrieval-first

- `benchmarks/longmemeval_bench.py` evaluates retrieval against LongMemEval corpus/answer sessions.
- This is not the same as Core2’s full answer-path correctness claim.

## Bottom Line

MemPalace is strongest as:

- a lossless raw memory substrate
- a scoped retrieval system
- a wake-up/bootstrap system
- an optional graph/navigation substrate

MemPalace is not yet proven, from the inspected source, as a drop-in replacement for:

- Core2 deterministic truth/state/provenance rules
- Core2 fail-closed answer surfaces
- Core2 abstention guarantees
