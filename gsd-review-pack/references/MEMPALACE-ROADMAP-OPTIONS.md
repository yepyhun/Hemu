# MemPalace Roadmap Options

## Purpose

Bound the post-04.9 options so future work does not drift into assumed migration or hybrid sprawl.

## Option A: Core2-First Borrowing

### What it is

Keep Core2 architecture intact and borrow only the smallest MemPalace-inspired ideas:

- scoped retrieval filters
- verbatim substrate improvements
- wake-up layering concepts

### When justified

- If the main expected gains come from retrieval ergonomics rather than architectural replacement
- If we want to preserve maximal Core2 stability

### Expected upside

- Lowest complexity
- Lowest risk of dual-engine confusion
- Good chance of practical retrieval gains

### Forbidden moves

- no substrate rewrite in one jump
- no graph-first redesign
- no AAAK-first redesign

## Option B: Bounded Hybrid Substrate

### What it is

Replace or rebuild the raw storage/retrieval substrate under Core2 while leaving truth/state/answer layers Core2-owned.

### When justified

- If 04.9 confirms the largest gap is still storage/retrieval quality
- If the team wants a meaningful upgrade without abandoning Core2’s hard core

### Expected upside

- Highest likely benefit-to-risk ratio
- Preserves the Core2 deterministic core
- Uses MemPalace where it appears strongest

### Forbidden moves

- no second truth engine
- no wholesale MemPalace protocol takeover
- no evaluation story swap

## Option C: Bounded Layer Replacement

### What it is

Replace exactly one layer, with an explicit owner transfer, and prove it.

Example candidates:

- wake-up/bootstrap layer
- retrieval layer
- navigation layer

### When justified

- If one MemPalace layer is clearly better and cleanly separable
- If a full hybrid substrate is too large right now

### Expected upside

- Clear experiment
- Easier rollback

### Forbidden moves

- no ambiguous ownership
- no “while we’re here” multi-layer rewrite

## Non-Recommended Option: Wholesale Replacement

### Why not recommended now

- Current evidence says MemPalace is strongest in retrieval/substrate, not as a proven drop-in replacement for Core2 truth/state/answer guarantees.
- It would overfit to the strongest visible MemPalace traits while discarding Core2’s clearest strengths.

## Recommended Next Move

Recommended branch after 04.9:

- `Option B: Bounded Hybrid Substrate`

Reason:

- It captures the clearest MemPalace advantages
- It preserves the Core2 hard deterministic core
- It avoids both blind replacement and tiny low-leverage borrowing

## Stop Rules

- Do not insert 04.10+ automatically.
- If the bounded hybrid substrate cannot be described without ownership ambiguity, fall back to Option A.
- If new evidence suggests the current Core2 baseline should be re-measured first, run the broader paid rerun before inserting the next implementation phase.
