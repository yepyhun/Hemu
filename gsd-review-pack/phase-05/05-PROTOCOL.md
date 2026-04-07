# Phase 5 Protocol

## Frozen Comparison Contract

- Comparable set: exact frozen `20` question ids from the prior broader validation slice
- Benchmark mode: `core2`
- Benchmark-fast: enabled
- Variants:
  - baseline: `CORE2_HYBRID_SUBSTRATE_MODE=off`
  - hybrid: `CORE2_HYBRID_SUBSTRATE_MODE=on`
- Canonical source-of-truth artifact for the future comparison: `06-COMPARISON-OUTCOME.json`

## Why This Contract Exists

The milestone is now about deciding whether the bounded hybrid branch should replace the shipped v1.0 baseline as the default path. That decision becomes untrustworthy if the runs are ad hoc, if the sample changes after seeing results, or if the human-readable summaries overrule the machine-readable evidence.

This protocol exists to stop that drift before Phase 6 spends more paid evaluation budget.

## Local Prerequisites

Before Phase 6 runs the paid comparison, both runtime modes must pass their locked local proof commands:

- baseline:
  - `CORE2_HYBRID_SUBSTRATE_MODE=off ./.venv/bin/python -m pytest tests/agent/test_core2_handmade_acceptance.py tests/agent/test_core2_generic_surface_generalization.py tests/agent/test_core2_answer_contract.py -q`
- hybrid:
  - `CORE2_HYBRID_SUBSTRATE_MODE=on ./.venv/bin/python -m pytest tests/agent/test_core2_hybrid_substrate.py tests/agent/test_core2_retrieval_routing.py tests/agent/test_core2_generic_surface_generalization.py tests/agent/test_core2_handmade_acceptance.py -q`

## Verdict Thresholds

### Promote Candidate

The hybrid can only be proposed as the new default candidate if all of the following are true:

- no kernel regressions are visible
- no truth/state regressions are visible
- pass-rate delta vs baseline is at least `+0.10`
- answer-surface-hit-rate delta vs baseline is at least `+0.10`

### Keep Baseline

The baseline remains the default if either of the following is true:

- any kernel regression appears
- hybrid pass-rate delta is non-positive

### Mixed / Hold

Anything that is neither a clear promotion nor a clear regression is `mixed_hold`.

## Verdict Precedence

Apply verdicts in this order:

1. `keep_baseline`
2. `mixed_hold`
3. `promote_candidate`

This prevents a small upside from hiding a regression.

## Canonical Artifact Rule

- Raw run artifacts may exist for each variant.
- Variant-specific canonical outcome artifacts may exist for each variant.
- The single comparison truth source is `06-COMPARISON-OUTCOME.json`.
- Human-readable summaries must derive their claims from that comparison artifact.

## Anti-Loop Rules

- Do not change Core2 kernel logic during the comparison phase.
- Do not widen the hybrid seam during the comparison phase.
- Do not replace the frozen question set after seeing any partial result.
- Do not change thresholds after the run.
- Do not reinterpret retrieval wins as end-to-end wins.

## Next Use

Phase 6 must execute baseline and hybrid under this exact contract or explicitly stop and replan.
