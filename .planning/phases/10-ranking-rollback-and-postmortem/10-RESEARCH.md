# Phase 10 Research

## Question

How should Core2 retire the failed ranking borrow cleanly after the hard residual replay regressed from `3/38` to `2/38`, while preserving useful hardening and leaving one bounded next step?

## Findings

### 1. The ranking borrow was locally valid but broader-residual negative

Phase 9 proved that the ranking borrow stayed within its intended seam and passed local targeted tests plus wider regression. That was enough to justify trying it on the hard residual set, but not enough to keep it active after the broader replay regressed.

Practical consequence:
- local green is not sufficient justification to keep a mechanism on the active path
- broader residual evidence wins

### 2. The regression did not change the dominant residual shape

The hard `38` replay after ranking ended at `2/38` with the same dominant structure:
- `prompt_miss` still overwhelms the bucket
- `handoff_format_miss` remains smaller
- `judge_artifact` remains small

Practical consequence:
- ranking is not the main blocked mechanism
- this phase should not mutate into ranking refinement

### 3. The earlier hardening imports are still useful

The invariant harness and narrow noise repair did not produce breakthrough gains on the hard residual set, but they remain valuable as constraints and hygiene. There is no evidence they caused the residual regression, and removing them would only reduce clarity.

Practical consequence:
- keep invariants
- keep noise repair
- only roll back ranking

### 4. The phase must end with one bounded next recommendation

Without a single forced recommendation, this phase would degrade into a postmortem that reopens multiple follow-up bets. That would recreate the same loop the project has been trying to avoid.

Practical consequence:
- the final artifact must contain one next-direction recommendation
- all other ideas should be explicitly parked or rejected

## Recommended Planning Shape

1. Lock canonical regression facts and rollback boundary
2. Remove ranking from active wiring and prove local stability
3. Write postmortem and single next-direction recommendation

## Guardrails

- No partial “shadow keepalive” ranking path in the active route
- No new paid rerun in this phase
- No softening of residual interpretation
- No bundling of additional borrow ideas into the rollback
