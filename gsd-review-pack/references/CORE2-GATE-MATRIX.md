# Core2 Gate Matrix

## Purpose

This matrix constrains how remaining live-gate misses are interpreted.

No miss may be labeled outside these classes:

- kernel correctness
- handoff/format
- judge artifact
- unknown

## Classes

### Kernel Correctness

Use this class when the kernel substrate itself is wrong or insufficient.

Required evidence:

- wrong or missing structured fact/state
- wrong supersession/conflict/currentness behavior
- wrong fact-first retrieval outcome for a covered case

Action:

- fix kernel behavior first
- rerun local proof before any paid gate

### Handoff/Format

Use this class when the kernel likely has the right structured answer, but the provider/runtime/final surface does not preserve or render it correctly.

Required evidence:

- answer surface exists or should exist
- structured support is present
- miss happens at final handoff/rendering/preservation layer

Action:

- fix answer-surface or handoff path
- rerun handmade set and golden path traces

### Judge Artifact

Use this class when the kernel and handoff appear correct, but the external benchmark judge still marks the case as failed.

Required evidence:

- local structured support is correct
- final answer is materially correct
- miss depends on evaluator interpretation, not a clear kernel regression

Action:

- record separately from kernel regression
- do not use it as sole evidence that Core2 is architecturally wrong

### Unknown

Use this class when the evidence is insufficient to classify the miss safely.

Required evidence:

- classification is ambiguous
- more than one failure mode still plausibly explains the miss

Action:

- gather more local evidence
- do not relabel optimistically

## Rerun Discipline

The paid gate may be rerun only after:

1. the handmade acceptance set is green
2. relevant golden path traces still match expected behavior
3. the current change is mapped to one of the explicit blocker classes above

If these are not satisfied, the correct next step is local clarification, not another paid rerun.

## Interpretation Note

Remote model or network delay by itself is not sufficient evidence of kernel correctness failure.

Latency may still matter for product quality, but it should not automatically be treated as proof that the Core2 substrate is wrong.

