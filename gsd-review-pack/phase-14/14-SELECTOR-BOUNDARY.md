# Phase 14 Selector Boundary

## Targeted In This Phase

- budget-aware evidence selection for the already-supported aggregate-temporal tranche
- selector features limited to:
  - `query_relevance`
  - `operator_fit`
  - `slot_coverage_gain`
  - `supporting_fact_strength`
  - `provenance_strength`
  - `temporal_completeness`
  - `numeric_executability`
  - `redundancy_penalty`
  - `token_cost`
- narrow aggregation safety:
  - identity-key style dedupe
  - unit compatibility
  - scope compatibility
  - time-window compatibility
  - partial evidence => abstain

## Supported Shapes

- temporal delta / elapsed-from-anchor
- days total / days ago
- ratio / percentage / average
- pairwise delta / anchor compare

## Explicitly Excluded

- plain current-total count
- plain current-total money
- local sequence lookup
- full bitemporal remodeling
- promotion-gate calibration work
- delivery or answer-surface intervention

## Guardrails Preserved

- no retrieval-ranking reopen
- no delivery reopen
- no ontology growth
- no comparator or judge changes
- no broad paid rerun inside this phase
