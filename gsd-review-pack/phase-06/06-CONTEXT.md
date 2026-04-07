# Phase 6: Baseline Versus Hybrid Evaluation - Context

## Why This Phase Exists

Phase 5 established the comparison protocol discipline for v1.1. The next honest step is to run the shipped baseline and the bounded hybrid candidate under a serious, explicitly frozen broader comparison set and record the result in canonical machine-readable artifacts.

This phase exists to produce the comparison evidence. It does not exist to improve either branch mid-comparison.

## Inputs

- `.planning/phases/05-comparative-validation-protocol/05-COMPARISON-MANIFEST.json`
- `.planning/phases/05-comparative-validation-protocol/05-PROTOCOL.md`
- `.planning/phases/05-comparative-validation-protocol/05-CANONICAL-OUTCOME-SCHEMA.json`
- `.planning/phases/05-comparative-validation-protocol/05-READINESS.json`
- `.planning/phases/04.1-longmemeval-gate-and-performance-fixes/04.1-GATE-STATUS-20.json`
- `.planning/phases/04.11-hybrid-branch-broader-paid-validation/04.11-OUTCOME.json`
- `.planning/phases/06-baseline-versus-hybrid-evaluation/06-BASELINE-STATUS.json` — exploratory `20`-sample baseline raw artifact, now superseded
- `.planning/phases/06-baseline-versus-hybrid-evaluation/06-HYBRID-STATUS.json` — exploratory `20`-sample hybrid raw artifact, now superseded

## Locked Decisions

- This phase executes a stricter broader comparison than the exploratory `20`-sample attempt.
- The baseline run must use `CORE2_HYBRID_SUBSTRATE_MODE=off`.
- The hybrid run must use `CORE2_HYBRID_SUBSTRATE_MODE=on`.
- Both variants must use the exact same frozen `70` question ids.
- Thresholds and verdict precedence must be frozen before execution and are not editable after execution starts.
- The canonical comparison truth source must be `06-COMPARISON-OUTCOME.json`.
- Prose summaries may explain the result but may not overrule the machine-readable comparison artifact.
- The earlier exploratory `20`-sample raw status files are not valid final evidence for this phase.

## What This Phase Must Not Become

- hidden implementation work
- kernel or hybrid seam tweaking
- threshold-moving after seeing results
- changing the sample set
- retrieval-only storytelling presented as full memory improvement

## Canonical References

- `.planning/phases/05-comparative-validation-protocol/05-COMPARISON-MANIFEST.json` — frozen variant/runtime/sample/threshold contract
- `.planning/phases/05-comparative-validation-protocol/05-PROTOCOL.md` — human-readable execution rules
- `.planning/phases/05-comparative-validation-protocol/05-CANONICAL-OUTCOME-SCHEMA.json` — required artifact shapes for baseline/hybrid/comparison outputs
- `scripts/run_core2_longmemeval_subset.py` — real Hermes-path comparison runner
