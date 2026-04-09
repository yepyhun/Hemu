# Phase 12 UAT

## Scope

Validate that Phase 12 produced a canonical retrieval-side coverage map for the frozen `33` retrieval-dominant residual cases without changing runtime behavior.

## Acceptance Checks

- The subset manifest exists and freezes exactly `33` case ids from the Phase 11 retrieval-dominant bucket.
- The coverage ledger exists and records exactly `33` per-case classifications.
- The taxonomy uses only the four planned retrieval-side classes:
  - `weak_or_partial_evidence`
  - `wrong_subset_selection`
  - `no_relevant_evidence`
  - `unsupported_query_family`
- The outcome artifact records one dominant class and exactly one bounded next direction.
- The dominant class is retrieval-side and does not drift back into delivery or ranking narratives.
- No runtime code, benchmark prompt, or paid rerun was introduced during the phase.

## Result

- `pass`
- Frozen subset confirmed: `33` cases
- Coverage ledger confirmed: `33` rows
- Dominant class: `weak_or_partial_evidence` (`15/33`)
- Secondary class: `wrong_subset_selection` (`11/33`)
- Canonical next direction: `Bounded Aggregate-Temporal Retrieval Coverage Expansion`
