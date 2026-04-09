# Phase 22 Research

## Reusable Inputs

### Phase 21 artifacts

- `21-LIFECYCLE-PROTOCOL.md`
- `21-LIFECYCLE-LABELS.md`
- `21-LIFECYCLE-LEDGER.jsonl`
- `21-SEAM-TAXONOMY.md`
- `21-OUTCOME.json`
- `21-VERDICT.md`

These establish:

- the canonical fixed-ten hard slice
- that answer-bearing memory is mostly present and locally reachable
- that the next justified seam is downstream of direct recall

### Existing benchmark attribution

- `agent/core2_longmemeval_benchmark.py::_failure_pattern`

This already distinguishes:

- `grounding_handoff_miss`
- `prompt_miss`
- `retrieval_or_reasoning_miss`
- abstention variants

Phase 22 should refine that downstream of direct recall rather than inventing a separate abstract vocabulary.

### Core2 downstream code seam

The main relevant code path is:

- `agent/core2_runtime.py::Core2Runtime.recall`
- `agent/core2_authoritative.py::build_answer_surface`
- `agent/core2_authoritative.py::_resolve_authoritative_payload`
- `agent/core2_authoritative.py::try_authoritative_answer`

This is enough context for a bounded downstream forensic phase without reopening other stacks.

## Working Hypothesis

The most likely dominant miss class is no longer “memory not found”.

The most likely dominant miss class is one of:

- the recall packet is structurally grounded but too weakly surfaced for authoritative answering
- the answer surface falls back too often even when the packet is locally useful
- the authoritative payload resolver is too narrow for the real fixed-ten questions
- the final prompt/handoff path drops or dilutes usable answer-surface evidence

## Planning Guardrail

Do not turn this into:

- a general delivery overhaul
- another upstream retrieval build
- a new benchmark campaign before the seam is localized
- a legacy import exercise

The phase ends with one bounded downstream fix direction or one explicit stop verdict.
