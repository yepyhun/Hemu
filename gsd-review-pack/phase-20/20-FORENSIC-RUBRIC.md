# Phase 20 Forensic Rubric

## Goal
Use a fixed representative ten-case slice to determine whether one narrow primitive borrow changes upstream candidate opening on real hard failures.

## Slice policy
- The slice is fixed in `20-TEN-CASE-MANIFEST.json`.
- No case swaps after the replay starts.
- The ten are intentionally mixed:
  - aggregate total
  - aggregate percentage
  - temporal after / ago
  - pairwise first
  - current vs previous / switch
  - one delivery-like control

## Borrow policy
- Allowed:
  - query-signal helpers
  - temporal/current aliases
  - aggregate-total signal extraction
- Forbidden:
  - whole legacy projection pipeline
  - whole legacy truth / provenance model
  - architecture change inspired by MemPalace
  - selector / delivery / ranking reopen

## Local proof criteria
- Targeted tests covering the primitive family must pass.
- Core2-wide regression must pass.
- Unrelated non-Core2 environment failures do not block the phase, but must be called out explicitly.

## External replay criteria
- Run exactly the fixed ten.
- Compare against the baseline failure labels in the manifest.
- Success means material movement on the fixed ten, not just local green tests.

## Interpretation rules
- `0/N` pass movement: the primitive borrow did not help externally.
- Improvement only in route notes or trace metadata does not count.
- `selector_engaged_cases = 0` with no retrieval movement means the bottleneck is still upstream of the borrowed seam.
- If only the control case moves and the retrieval cases do not, treat that as non-success for the stated phase goal.

## Stop rule
- If the fixed ten does not improve materially, record a negative external verdict and stop.
