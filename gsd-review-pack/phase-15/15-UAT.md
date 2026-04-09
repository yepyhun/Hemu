# Phase 15 UAT

## Scope

Validate that the pipeline attribution layer is accepted as one bounded diagnostics contract without reopening retrieval, delivery, or truth-model work.

## Acceptance Checks

- one stable per-case attribution row exists
- retrieval, sufficiency, reasoning/delivery, and judge-like outcomes are separated explicitly
- the contract reuses existing benchmark rows and route notes instead of inventing a second trace universe
- focused attribution proof stays green
- wider Core2 regression stays green
- no retrieval, delivery, bitemporal, promotion-gate, or judge rewrite drift appears

## Result

- schema artifact: `15-ATTRIBUTION-SCHEMA.md`
- machine-readable contract: `15-ATTRIBUTION-CONTRACT.json`
- canonical local outcome: `15-LOCAL-OUTCOME.json`
- focused proof: `33 passed in 6.71s`
- wider regression: `145 passed in 13.52s`

## Verdict

`pass`
