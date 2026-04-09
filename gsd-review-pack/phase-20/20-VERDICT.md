# Phase 20 Verdict

## Outcome
- Local proof: strong
- External fixed ten-case gate: failed

## Local proof
- `tests/agent/test_core2_query_shape_candidate_seeding.py`: `10 passed`
- `tests/agent/test_core2_aggregate_temporal_retrieval_expansion.py`: `4 passed`
- `tests/agent/test_core2_budgeted_evidence_selector.py`: `3 passed`
- `tests/agent/test_core2_*.py tests/test_run_agent_core2_authoritative.py`: `156 passed`

## Full test note
- `tests/agent -q` still reports `5` unrelated auxiliary-client environment failures.
- These are outside the Core2 seam changed in this phase.

## External gate
- Fixed representative slice: `10`
- Result: `0/10`
- `answer_surface_hit_rate`: `0.2`
- `promptless_authoritative_cases`: `2`
- dominant pattern: `prompt_miss`
- dominant family: `handoff_format`

## Attribution
- `retrieval_failure`: `8`
- `sufficiency_failure`: `1`
- `delivery_surface_failure`: `1`
- `selector_engaged_cases`: `0`
- `aggregation_safety_abstentions`: `0`

## Interpretation
The borrowed legacy query-signal primitives are locally integrated correctly, but they did not move the fixed ten-case external gate at all. The most important negative fact is not just `0/10`, but that the borrowed seam still produced `selector_engaged_cases = 0`, so the bottleneck remains upstream of this primitive family in real hard cases.

## Canonical verdict
`needs_work`

Carry-forward meaning:
- keep the forensic artifacts
- do not treat this primitive borrow as an externally validated forward path
- if any continuation happens, it should start from the fixed-ten forensic evidence, not from the local green proof alone
