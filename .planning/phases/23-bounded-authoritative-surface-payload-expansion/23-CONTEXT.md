# Phase 23 Context

## Why This Phase Exists

`v1.16/22` already localized the dominant downstream miss on the fixed hard ten.

The verified seam is no longer generic “prompt weirdness”.
It is now narrower:

- missing promptless authoritative bridge coverage
- weak answer-surface bridging
- wrong authoritative payload shaping on the few cases that already short-circuit

This phase exists to convert that verified seam into one bounded implementation pass instead of another forensic loop.

## Hard Truth To Preserve

- the same fixed ten from `v1.14/20`, `v1.15/21`, and `v1.16/22` remains canonical
- `v1.16/22` seam counts were:
  - `5/10` `no_promptless_authoritative_bridge`
  - `2/10` `answer_surface_fallback_only`
  - `2/10` `authoritative_payload_wrong`
  - `1/10` `answer_bearing_packet_not_bridged`
- `v1.15/21` already ruled out source absence, gross persistence/index loss, and session-local unsearchability as dominant explanations
- the next build must therefore stay downstream of recall

## Exact Build Target

The build target is one bounded downstream expansion:

1. identify which already recalled packet shapes may short-circuit into authoritative answers
2. widen promptless authoritative bridge coverage only for those supported families
3. tighten authoritative payload shaping so supported families return the correct answer text
4. preserve fallback behavior outside the supported family boundary

## What Counts As Success

This phase is only useful if it produces all of:

- one explicit authoritative surface contract for supported families
- one bounded implementation that expands bridge coverage and/or payload correctness
- local proof that the supported families still short-circuit safely
- one honest fixed-ten external verdict: improved, unchanged, or regressed

## Fixed Slice Policy

- use exactly the same fixed representative ten
- do not soften the gate by switching to easier cases
- do not claim success from local proof alone
- the fixed-ten paid replay remains the external truth gate

## Black-Box Prohibition

The phase must not end in vague wording like:

- “better answer formatting”
- “stronger prompting”
- “more robust handoff”

The implementation target must stay concrete:

- bridge eligibility
- answer-surface family coverage
- authoritative payload correctness

## Planning Boundary

Do not widen into:

- new upstream retrieval heuristics
- new memory admission/indexing work
- full prompt assembly redesign
- architecture migration
- ranking or selector reopening
