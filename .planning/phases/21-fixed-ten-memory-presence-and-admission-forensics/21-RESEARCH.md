# Phase 21 Research

## Reusable Inputs

### Phase 20 artifacts
- `20-TEN-CASE-MANIFEST.json`
- `20-FORENSIC-LEDGER.jsonl`
- `20-TEN-CASE-GATE-STATUS.json`
- `20-TEN-CASE-ATTRIBUTION-STATUS.json`

These establish:
- the canonical fixed hard slice
- baseline failure labels
- the fact that the last narrow borrow produced `0/10`

### Existing attribution contract
- `v1.9/15`
- `v1.10/16`

These remain the right bounded evaluation frame:
- retrieval
- sufficiency
- reasoning/delivery
- judge-like

### Old Hermes as oracle only
Potentially useful comparison targets:
- raw memory presence
- normalized representation
- index visibility
- recall contrast on the same question

## Working Hypothesis

The dominant hard failures are likely caused by one of these upstream seam classes:
- `absent_in_source_or_memory`
- `present_but_not_extracted`
- `extracted_but_not_normalized_usefully`
- `normalized_but_not_persisted_or_not_indexed`
- `indexed_but_filtered_out_before_candidate_opening`
- `surfaced_but_lost_in_handoff`

Phase 21 should decide which of these actually dominates the fixed ten.

## Planning Guardrail

Do not widen into:
- new retrieval heuristics
- new selector logic
- new delivery heuristics
- broad benchmark reruns
- full-legacy comparison campaigns

The phase ends with seam-localization, not with a speculative “fix”.
