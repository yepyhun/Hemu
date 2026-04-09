# Phase 19 Execution Checkpoint

## Why This Checkpoint Exists

This note freezes the state that existed after `Phase 19` planning and after the paid hard `38` replay, but before `Phase 19` execute was fully proved and artifacted.

The goal is to preserve the current seam truth so later external research can be integrated without losing the already-settled facts.

## Hard Truth Already Settled

- canonical hard replay remains `3/38`
- dominant actionable live bucket remains `retrieval_failure` (`29/38`)
- `selector_engaged_cases = 0`
- `aggregation_safety_abstentions = 0`
- the shipped selector/safety slice did not visibly engage the canonical hard bucket

This phase is therefore **not** allowed to ask:

- how to improve selector ranking
- how to improve delivery
- how to reopen ranking

This phase **must** ask:

- what minimal upstream seed-opening seam could make answer-bearing candidates appear at all

## Working Interpretation

The likely seam is earlier than selector choice:

- the hard bucket is failing before selector engagement
- the missing step is likely query-shape-conditioned candidate opening or seed admission
- the mechanism must stay narrow and target only a homogeneous subset

## Canonical Slice Guidance

Slice definitions are useful **as diagnostic and experimental taxonomy**, not yet as full runtime ontology.

For this phase, slices should be used to:

- define target subsets
- define allowed seed classes
- define engagement criteria
- define stop rules

They should **not** yet be promoted into broad kernel truth objects.

Recommended slice dimensions for this phase:

- `query/operator shape`
- `seed requirement type`
- `entity/scope binding need`
- `temporal anchor need`
- `expected evidence cardinality`
- `failure seam`

## Unfinalized Execute Work Already Started

The following code-level execution work was already started but is **not yet phase-complete**:

- new module: `agent/core2_query_shape_seeding.py`
- hybrid seam wiring: `agent/core2_hybrid_substrate.py`
- runtime note wiring: `agent/core2_runtime.py`

Current intended mechanism:

- derive bounded clause-level or operator-shaped seed queries
- let those seed queries open upstream raw/turn hits before selector logic
- emit explicit trace when such seed opening occurs

## What Still Must Be Proved Before Phase 19 Can Claim Success

1. a frozen target subset must be named explicitly
2. the target subset must be homogeneous enough for one mechanism
3. the mechanism must produce one of:
   - movement in `evidence_present_cases`
   - movement in `sufficient_retrieval_cases`
   - explicit seed-opening trace on the target subset
4. if none of those move, the phase must stop cleanly rather than claim progress

## What External Research May Still Improve

External research is still welcome if it helps answer any of these:

- how to classify query/operator shapes more robustly
- how clause-level query rewriting or decomposition is usually done
- how candidate seeding is formalized in compositional or temporal QA
- how evidence sufficiency or retrieval stopping is measured
- how temporal anchors and comparison operands are opened upstream

## Next Execute Obligations

- add targeted tests for query-shape-conditioned seed opening
- verify the mechanism stays bounded
- write the missing phase artifacts:
  - `19-TARGET-SUBSET-MANIFEST.json`
  - `19-SEEDING-SEAM-RULES.md`
  - `19-SEEDING-BOUNDARY.md`
  - `19-SEEDING-TRANSITIONS.jsonl`
  - `19-OUTCOME.json`
  - `19-VERDICT.md`
  - `19-VERIFICATION.md`
