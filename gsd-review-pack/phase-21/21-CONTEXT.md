# Phase 21 Context

## Why This Phase Exists

`v1.14/20` gave a clean negative result:
- the fixed representative `10`-case external gate stayed at `0/10`
- `retrieval_failure` still dominated
- `selector_engaged_cases = 0`
- the narrow primitive borrow was locally sound but externally inert

That means another heuristic retrieval tweak is not justified yet. The next milestone has to prove where answer-bearing memory dies across the lifecycle of the fixed hard slice.

## Hard Truth To Preserve

- strong local proof is not enough
- only the fixed hard slice external truth can justify stronger forward claims
- Phase 21 is forensic-first, not feature-first
- old Hermes may be used only as a diagnostic oracle, not as a borrow commitment

## Lifecycle To Inspect

For each fixed hard case, inspect these checkpoints:
- source episode / raw memory presence
- ingestion / extraction
- normalization
- persisted fact or record presence
- retrieval index presence
- admission / prefilter survival
- runtime evidence surface
- handoff / answer-format loss

## What Counts As Progress

This phase is only useful if it produces one of:
- a canonical lifecycle ledger that names the exact death seam per case
- a dominant seam class that justifies one narrowly bounded next build
- a clean stop verdict showing that no justified next build exists yet

## Fixed Slice Policy

The fixed representative `10` from Phase 20 remains the canonical slice.  
No expansion to `38` inside this phase.

## Diagnostic Comparator Policy

Old Hermes is allowed only for:
- side-by-side presence checks
- indexing / retrieval contrasts
- proving that a seam is Core2-specific rather than universally absent

It is not allowed for:
- direct runtime import
- architecture rollback
- “it works there, so copy it” reasoning
