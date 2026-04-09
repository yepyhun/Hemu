# Phase 19 Research

## Objective

Find the smallest upstream decomposition-and-seeding stack that could plausibly change the hard residual bucket, while rejecting another locally-correct but externally-irrelevant build.

## What The Paid Hard Replay Already Settled

- the current active path still ends at `3/38`
- the dominant live bucket is still `retrieval_failure` (`29/38`)
- `selector_engaged_cases = 0`
- `aggregation_safety_abstentions = 0`
- the shipped selector/safety slice did not visibly engage this hard bucket

This means the current question is not "how should the selector choose better?" but "what bounded upstream decomposition-and-seeding stack could make answer-bearing candidates appear at all?"

## Working Seam Taxonomy For This Phase

### `query_opening_miss`

The active path never opens the operator, comparison, or aggregation shape needed to request the right seed class.

### `temporal_or_compare_seed_miss`

The path opens the query partially, but does not seed the earlier/later, paired-anchor, or compare operands needed to create answer-bearing candidates.

### `aggregate_constituent_seed_miss`

The path does not seed the constituent facts required for a count/sum/ratio style question even though the broader memory likely contains pieces of them.

### `earlier_than_seeding`

The missing thing is not candidate seeding at all; it is absent from storage, absent from indexing, or filtered before any realistic seeding logic could help.

This label is critical because the phase must be allowed to stop cleanly instead of forcing a seeding build where the seam is wrong.

## Research Upgrade From The New External Blocks

The new external research tightened one conclusion sharply:

- the immediate live seam is not generic selector math
- it is decomposition-driven upstream opening

So this phase is now allowed to adopt a **bounded operator-slot schema** and a **bounded rewrite family** as part of the same upstream seeding stack.

What the research strongly supports for this phase:

- question decomposition
- operator classification
- arity and slot schema
- clause-level query rewrites
- temporal anchor seeds
- paired operand seeds
- sufficiency-style engagement checks

What the research does **not** justify importing into this phase:

- full bitemporal/state semantics
- truth-discovery weighting
- aggregation-safety redesign
- calibrated override gates
- benchmark redesign beyond existing observability

## What Phase 13 And 14 Actually Proved

`v1.7/13` proved a bounded constituent-anchor expansion can work locally on a safe compositional tranche.

`v1.8/14` proved a bounded selector-and-safety slice can work locally and stay narrow.

What they did **not** prove:

- that the canonical hard `38` is reachable by those mechanisms
- that the current hard replay candidate pool even enters those seams

So this phase must treat those milestones as local capability proofs, not as direct evidence that the hard replay should now improve.

## Narrow External Borrow That Is Allowed

### From OpenViking

- staged admission as a pattern
- retrieval trajectory observability as a pattern

### From ByteRover/Cipher

- pre-curated context objects as a pattern
- structured upstream staging as a pattern

What these external systems do **not** justify here:

- no full hierarchical retrieval adoption
- no full context-tree adoption
- no platform rewrite

The only allowed borrow is this minimal idea:

query shape may open a specialized upstream seed class before the general selector runs.

## Reusable Jackpot Lenses

The strongest jackpot lenses for this phase now become:

1. `operator` + `arity` + `slot schema`
   - use this to define what the query is actually asking for before seeding

2. `query rewrite family`
   - use this to create bounded clause-level, anchor-level, and paired-operand seed queries

3. `temporal_completeness` + `numeric_executability`
   - use this to detect missing paired anchors or aggregate constituents

4. `entity_binding_quality`
   - use this only to separate true seeding misses from cases that are really binding misses

These are diagnostic and bounding lenses here, not a license to import the full jackpot stack.

## Research Verdict

The phase should only promote one decomposition-and-seeding stack if it can answer all three questions:

1. which target subset is homogeneous
2. what operator/slot plus seed-family combination explains it
3. what artifact movement would prove engagement on that subset

If any of those stay vague, the phase should stop rather than ship another elegant but irrelevant retrieval-side improvement.

## Stop Rule

If the target subset cannot be reduced to one explicit operator/slot family with one measurable engagement criterion, do not promote a seeding build from this phase.
