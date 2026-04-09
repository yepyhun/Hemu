# Phase 15: Pipeline Attribution Dashboard

## Phase Boundary

This phase turns the remaining jackpot observability idea into one bounded diagnostics milestone:

- per-case attribution that separates retrieval, sufficiency, reasoning/delivery, and judge-like outcomes
- a reusable local output contract for future benchmark and replay work

It does **not** build a new retrieval or delivery mechanism.

## Locked Decisions

### What This Phase Must Do

- stay observability-only
- emit one per-case attribution record instead of one aggregate result only
- separate retrieval-side failure from sufficiency failure
- distinguish downstream reasoning/delivery failure from judge-like artifact labels
- reuse existing bounded artifacts where possible instead of inventing a second trace universe

### What This Phase Must Not Do

- no retrieval selector widening
- no delivery/prompt-path work
- no bitemporal refactor
- no promotion-gate implementation
- no comparator or judge rewrite
- no broad paid rerun inside this phase
- no truth-model ownership changes

## Prior Evidence That Must Be Preserved

- `v1.5/11` already established a first-failure mapping discipline over the hard residual set
- `v1.6/12` already produced a retrieval-side gap map over the frozen retrieval-dominant subset
- `v1.8/14` added better selector-side observability at the retrieval seam
- the jackpot note identified pipeline attribution as the next highest-value bounded follow-up after selector+safety

## Required Canonical Artifacts

- `15-ATTRIBUTION-SCHEMA.md`
- `15-ATTRIBUTION-CONTRACT.json`
- `15-LOCAL-OUTCOME.json`
- `15-VERDICT.md`

## Success Criteria

- the attribution schema is explicit before implementation
- the capture path is bounded to diagnostics plumbing
- the phase produces one reusable per-case record format
- future work can distinguish retrieval, sufficiency, reasoning/delivery, and judge-like failure buckets without rereading raw outputs manually

## Anti-Loop Rule

If the attribution contract cannot be expressed cleanly in one bounded output shape, stop and record that. Do not silently widen Phase 15 into a broader evaluation refactor.
