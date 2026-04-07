# Phase 7 Blocked Path Map

## Canonical Input

Source of truth:
- `.planning/phases/06-baseline-versus-hybrid-evaluation/06-COMPARISON-OUTCOME.json`
- `.planning/phases/06-baseline-versus-hybrid-evaluation/06-BASELINE-OUTCOME.json`
- `.planning/phases/06-baseline-versus-hybrid-evaluation/06-HYBRID-OUTCOME.json`

Locked facts:
- baseline: `31/70`
- hybrid: `32/70`
- verdict: `mixed_hold`
- answer-surface hit rate: unchanged
- promptless authoritative cases: unchanged

## Residual Structure

The residuals do **not** look like broad hybrid regression.

They break down into three mechanism classes:

1. `prompt_miss / judge: unknown`
   - unchanged across branches: `30`
   - baseline-only resolved by hybrid: `3`
   - hybrid-only newly missed: `2`
   - dominant residual family by far

2. `handoff_format_miss / no_local_comparator`
   - unchanged across branches: `4`
   - stable, branch-independent ceiling gap

3. `judge_artifact / unknown`
   - unchanged across branches: `2`
   - explicit stop-point noise, not a breakthrough target

## What The Delta Actually Means

The hybrid branch did improve something real, but the gain remained mostly trapped below the final answer path.

Evidence:
- `+1/70` pass-rate movement
- no increase in promptless-authoritative cases
- no increase in answer-surface hit rate
- the dominant residual cluster stayed in the same `prompt_miss / unknown` lane

This means the main bottleneck is **not** "hybrid retrieval gives nothing useful".

The main bottleneck is more likely:
- improved hybrid evidence is not being promoted into the existing authoritative / local-comparable answer path often enough

## Primary Blocked Mechanism

### Authoritative Eligibility Dead Zone

For many already-covered families, the hybrid branch appears capable of surfacing slightly better lower-layer evidence, but that evidence does not cross into the final deterministic answer path.

So the system remains in the same prompt-driven route, and the result is still:
- `prompt_miss`
- `judge: unknown`

This is the most likely explanation for why the hybrid branch moved directionally but did not compound into a more material benchmark gain.

## Secondary Mechanisms

### Stable Comparator Coverage Gap

The `4` unchanged `no_local_comparator` cases matter, but they are not the main hybrid-specific bottleneck:
- they existed in both branches
- they cap out at a small bounded gain
- fixing them would be cleanup, not a breakthrough

### Judge Artifact Stop-Point

The `2` unchanged judge-artifact abstention cases remain explicit stop-points:
- they are not proof of kernel regression
- they are not a good target for breakthrough work

## Implication

The highest-leverage next move is **not**:
- more per-question tuning
- more new families
- broad comparator growth
- another small paid rerun

The highest-leverage next move is to test whether hybrid-retrieval improvements can be promoted into the existing authoritative path for already-covered families.
