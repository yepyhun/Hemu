# Phase 8 Bridge Boundary

## Mechanism

The bounded bridge is implemented at the **structured covered-fact eligibility seam** inside `agent/core2_authoritative.py`.

Before Phase 8:
- structured covered-fact extractors accepted only `digest_fact` items whose `metadata.retrieval_path == "fact_first"`
- hybrid-promoted `digest_fact` items with retrieval paths like `hybrid_scoped_turn` or `hybrid_scoped_raw` stayed below the authoritative path

After Phase 8:
- structured covered-fact extractors still require `digest_fact`
- they still do **not** accept plain lexical/semantic candidates
- they now additionally accept bounded bridge paths:
  - `hybrid_scoped_turn`
  - `hybrid_scoped_raw`

## In Scope

- existing covered families only
- routing/eligibility widening only
- no truth/state ownership changes
- no answer-surface style changes

## Out of Scope

- comparator softening
- new families
- lexical-path eligibility widening
- benchmark-specific wording
- substrate changes
