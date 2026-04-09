# Phase 23 Research

## Reusable Inputs

### Phase 22 artifacts

- `22-DOWNSTREAM-LEDGER.jsonl`
- `22-SEAM-TAXONOMY.md`
- `22-PACKET-HANDOFF-COMPARATOR.md`
- `22-OUTCOME.json`
- `22-VERDICT.md`

These establish:

- the dominant downstream seam is authoritative bridge / payload related
- the next justified move is implementation, not more localization

### Existing Core2 authoritative seam

The bounded code seam remains:

- `agent/core2_authoritative.py::build_answer_surface`
- `agent/core2_authoritative.py::_resolve_authoritative_payload`
- `agent/core2_authoritative.py::try_authoritative_answer`
- `run_agent.py` authoritative short-circuit path

This is enough context for the next bounded build.

### Existing authoritative tests

Current tests already cover:

- temporal compare authoritative short-circuit
- previous occupation extraction
- personal best time extraction
- bounded numeric aggregation
- end-to-end CLI short-circuit behavior

Phase 23 should expand supported-family coverage and payload correctness without breaking these existing families.

## Working Hypothesis

The most likely highest-leverage fix is not “more prompting”.

The highest-leverage fix is:

- expanding the conditions under which already grounded recall packets qualify for promptless authoritative answering
- improving the mapping from structured recall evidence into final authoritative payload text

That means the smallest plausible winning move is a bounded family expansion inside the authoritative path, not a general downstream rewrite.

## Planning Guardrail

Do not turn this into:

- another forensic-only milestone
- a broad answer-generation overhaul
- a new upstream retrieval project
- a benchmark-first tuning loop without local proof

The phase ends with one bounded downstream build and one honest fixed-ten gate result.
