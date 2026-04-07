# Phase 7 Stop Rule

## What Phase 7 Allows Next

One next build step is allowed:

- a bounded implementation phase focused on the **authoritative eligibility bridge for already-covered families**

## What Phase 7 Explicitly Forbids

The next step must **not** become any of the following:

- a hand-picked benchmark patch sprint
- a new family-enumeration phase
- a comparator-softening phase
- a substrate rewrite round
- a fresh paid rerun before local falsification

## Falsification Rule

Stop pursuing the chosen hypothesis if the representative local slice does **not** show a material increase in authoritative-route eligibility.

In practice, that means:
- no meaningful route shift on the frozen prompt-miss slice
- or the route shift only appears after adding soft matching / special-case logic

If either happens, the hypothesis is not breakthrough territory and should not be stretched into another loop.

## Next Build Handoff

The next concrete build phase should be framed as:

### Candidate Next Phase

`Authoritative Eligibility Bridge`

Goal:
- test whether hybrid retrieval gains can be promoted into the existing deterministic answer path for already-covered families

Local proof first:
- frozen prompt-miss slice
- route-eligibility instrumentation
- no paid rerun until the bridge shows real movement

## Why This Stop Rule Matters

Without this stop rule, the project will naturally drift into:
- `+1/+2` benchmark pepecselés
- residual-case chasing
- false hope from tiny movement

Phase 7 exists specifically to prevent that drift.
