# Phase 22 Context

## Why This Phase Exists

`v1.15/21` verified that the fixed hard ten is mostly **not** failing because the answer-bearing memory is absent, unpersisted, or globally unindexed.

The dominant remaining question is downstream:

- does the recall packet already contain enough answer-bearing structure?
- if yes, is the loss happening in answer-surface construction?
- if yes, is the loss happening in authoritative payload resolution?
- if yes, is the loss happening in prompt assembly or final handoff?

This phase exists to localize that seam without reopening upstream retrieval by inertia.

## Hard Truth To Preserve

- the same fixed ten from `v1.14/20` remains canonical
- the last external gate over that slice was still `0/10`
- `v1.15/21` ruled out source absence, gross persist/index loss, and session-local unsearchability as dominant explanations
- direct `Core2Runtime.recall()` already reaches answer-bearing sessions in `9/10`
- only `3/10` direct packets showed literal gold-answer presence, so downstream loss may still begin before final response generation

## Downstream Chain To Inspect

The concrete downstream chain to trace is:

1. `Core2Runtime.recall()`
2. `build_answer_packet(...)`
3. `build_answer_surface(...)`
4. `try_authoritative_answer(...)`
5. prompt assembly / memory handoff into the final agent path
6. final answer surface in the model response

Phase 22 is only useful if each case can be placed at one concrete failure seam in this chain.

## What Counts As Progress

This phase is only useful if it produces one of:

- a canonical downstream ledger that names the exact handoff/surface death seam per case
- a dominant downstream seam class that justifies one narrowly bounded fix
- a clean stop verdict showing that no single justified downstream fix exists yet

## Fixed Slice Policy

- use exactly the same fixed representative ten as `v1.14/20` and `v1.15/21`
- do not swap in easier cases
- do not reframe success around local-only proof
- any downstream fix direction must still be replayable against the same fixed ten later

## Black-Box Prohibition

The phase must not end in vague labels like “reasoning issue” or “prompt weirdness”.

Allowed seam labels must map to a concrete checkpoint such as:

- packet shaping miss
- answer-surface construction miss
- authoritative-payload gating miss
- prompt assembly / handoff miss
- final response surface miss

## Planning Boundary

Do not widen into:

- new upstream retrieval heuristics
- new selector logic
- new ranking experiments
- architecture migration
- broad benchmark reruns before the downstream seam is localized
