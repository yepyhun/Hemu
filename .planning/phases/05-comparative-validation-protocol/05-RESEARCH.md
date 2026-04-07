# Phase 5: Comparative Validation Protocol - Research

## User Constraints

- Keep the workflow anti-loop and explicit.
- Avoid hidden implementation during planning/validation phases.
- Preserve the shipped `v1.0` baseline as a stable reference.
- Keep model/runtime guidance explicit in the state and next-step output.

## What This Phase Actually Authorizes

Phase 5 authorizes only:

1. a frozen comparison manifest
2. a canonical artifact shape for baseline and hybrid outcomes
3. a reproducibility proof that the comparison protocol can be executed mechanically later

It does **not** authorize:

- changing the kernel
- changing the hybrid substrate
- changing benchmark semantics
- widening sample scope after seeing results

## Recommended Planning Shape

This phase should decompose into:

1. protocol lock
2. canonical artifact and diff schema
3. dry-run / reproducibility proof

That gives the next phase (`6`) an execution path that is mostly mechanical.

## Testing Guidance

- prove that the frozen manifest is explicit enough to rerun later without ambiguity
- prove that baseline and hybrid outcomes will land in the same canonical schema
- prove that later verdicting can be derived from machine-readable artifacts rather than prose summaries

## Risks And Failure Modes

- hidden drift in sample set, runtime mode, or status-path conventions
- comparing baseline and hybrid under different assumptions
- declaring “better retrieval” as “better memory”
- treating this planning phase as permission to start editing the system again

## Open Questions

- What exact broader sample should be the locked comparison set?
- Which metrics are necessary for the later default-selection verdict, and which are just noise?
- What exact precedence should later verdicts follow if one metric improves but another regresses?

