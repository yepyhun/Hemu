# Phase 13 Shape Boundary

## Targeted In This Tranche

- temporal delta / elapsed-from-anchor questions
- day-total / days-ago questions
- ratio / percentage / average questions
- pairwise delta / anchor-compare questions

## Explicitly Excluded In This Tranche

- plain current-total count questions
- plain current-total money questions
- local sequence lookup shapes like the chess-line question

## Why The Boundary Was Tightened

The first execution pass showed that letting constituent-anchor expansion fire on plain current-total queries regressed already-covered aggregate surfaces. The safe bounded cut for Phase 13 is therefore:

- keep the expansion for compositional temporal and ratio-like questions where multiple anchors must be assembled
- leave plain current-total aggregate questions untouched until a later phase can solve them without regressing current good behavior

## Guardrails Preserved

- no ranking reopen
- no delivery reopen
- no family/ontology growth
- no benchmark rerun inside this phase
- no change to deterministic answer-surface ownership
