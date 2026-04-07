# Phase 9 Ranking Boundary

## Mechanism

The bounded borrow is implemented at the **hybrid candidate ordering seam** inside `agent/core2_hybrid_substrate.py`, using a small helper module in `agent/core2_ranking.py`.

Imported signal families:

- scope precedence
- authority
- status
- support/quality proxy
- freshness
- token-budget-aware compact top-N selection

## In Scope

- hybrid candidate ordering only
- bounded legacy ranking ideas adapted into Core2-native code
- local ranking proofs

## Out of Scope

- comparator changes
- answer render rewrites
- memory claim guard
- family growth
- truth-state ownership changes
- broad benchmark rerun inside this phase
