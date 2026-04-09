# Phase 16 Research

## Objective

Turn the new pipeline attribution contract into one real replay milestone instead of leaving it as local-only plumbing.

## What Earlier Phases Already Settled

- the hard residual `38` exists and should stay frozen
- delivery is not the dominant next build direction on that set
- the selector/safety work is already in the active path
- the new attribution contract can separate retrieval, sufficiency, reasoning/delivery, and judge-like outcomes locally

## Working Milestone Hypothesis

The highest-value next step is not another kernel build but one attributed hard replay:

- same hard `38` set
- same current active path
- new per-case attribution rows
- one canonical outcome that names the dominant live bucket now

## Why Use The `08.1` Hard 38 Reference

- `08.1` preserves the canonical `3/38` hard residual set that later diagnostics used as their frozen basis
- `09` represents a failed ranking-path experiment and should not become the new replay baseline by inertia
- the question IDs are the important frozen asset; the replay should be current-code, old-set

## Bounded Replay Contract

The first version must stay small:

- one manifest
- one replay run
- one attributed status artifact
- one attributed outcome artifact
- no auxiliary dashboards or alternate samples

## Recommended Outcome Surface

Per replay:

- total cases
- pass count
- attribution label counts
- stage bucket counts
- evidence-present rate
- sufficient-retrieval rate
- answer-surface-hit rate
- selector-engaged cases
- aggregation-safety abstention count
- judge-like count

## Carry-Forward Logic

- if one attribution bucket clearly dominates, carry exactly one bounded next direction
- if no bucket dominates enough to justify a new build, carry an explicit stop rule instead

## Stop Rule

If Phase 16 starts to demand a new replay harness, a second diagnostics schema, or inline kernel changes, stop. The goal is attributed replay, not a blended replay-plus-build milestone.
