# Phase 20 Case Ledger Schema

Each line in `20-FORENSIC-LEDGER.jsonl` uses this schema:

```json
{
  "question_id": "string",
  "question": "string",
  "baseline_failure_type": "retrieval_failure|sufficiency_failure|delivery_surface_failure|judge_artifact|passed",
  "shape_family": "string",
  "primitive_family": "legacy_query_signal_primitives",
  "local_expected_signal_family": "string",
  "post_borrow_route_note_present": true,
  "post_borrow_signal_family": "string",
  "post_borrow_failure_type": "string",
  "post_borrow_stage": "string",
  "passed": false,
  "notes": "string"
}
```

## Required interpretation fields
- `baseline_failure_type`: frozen from the hard-38 attribution baseline.
- `shape_family`: why this case is in the representative ten.
- `local_expected_signal_family`: which borrowed primitive should engage, if any.
- `post_borrow_route_note_present`: whether the runtime emitted `hybrid_query_signal_primitive`.
- `post_borrow_failure_type`: the external replay attribution after the borrow.

## Ledger purpose
- keep per-case forensic depth without changing the benchmark slice
- separate local engagement evidence from external pass/fail
- make negative results reusable later
