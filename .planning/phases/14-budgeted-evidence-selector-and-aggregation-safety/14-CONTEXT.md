# Phase 14: Budgeted Evidence Selector And Aggregation Safety

## Phase Boundary

This phase turns the strongest jackpot research into one bounded retrieval-side build:

- budget-aware evidence set selection for compositional aggregate-temporal questions
- narrow aggregation safety for dedupe, compatibility, and partial-evidence abstention

It does **not** redesign the whole kernel.

## Locked Decisions

### What This Phase Must Do

- stay retrieval-side only
- keep the target limited to the dominant compositional aggregate-temporal shapes already surfaced by `v1.6/12` and `v1.7/13`
- replace itemwise pickup behavior with one bounded set-selection layer
- add explicit aggregation safety checks where composition can silently lie
- produce local observability that separates retrieval sufficiency from downstream answer-path noise

### What This Phase Must Not Do

- no retrieval-ranking reopen
- no delivery/prompt-path work
- no bitemporal refactor
- no promotion-gate overhaul
- no ontology/family growth
- no comparator or judge handling changes
- no broad paid rerun inside this phase
- no widening into plain current-total aggregate shapes during implementation

## Prior Evidence That Must Be Preserved

- `v1.5/11` showed the hard residual set is retrieval-dominant, not delivery-dominant
- `v1.6/12` mapped the dominant retrieval bucket to weak or partial aggregate-temporal evidence
- `v1.7/13` proved constituent-anchor expansion is real on a safe tranche, while plain current-total aggregates still regress if widened too early
- the jackpot note identified `budgeted evidence selection + aggregation safety` as the strongest immediate bounded follow-up

## Required Canonical Artifacts

- `14-SELECTOR-BOUNDARY.md`
- `14-TARGET-SLICE-MANIFEST.json`
- `14-LOCAL-OUTCOME.json`
- `14-VERDICT.md`

## Success Criteria

- selector feature set and target shapes are frozen before implementation
- the build improves retrieval sufficiency on the chosen tranche locally
- aggregation safety is explicit, testable, and bounded
- the phase ends with one canonical local verdict and no scope drift

## Anti-Loop Rule

If local proof does not show clearer retrieval sufficiency on the targeted tranche, stop. Do not broaden the selector into other shapes, delivery work, or benchmark reruns inside this phase.
