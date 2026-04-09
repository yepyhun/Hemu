# Phase 11 First-Failure Rules

These rules define the local, upstream-first classification used for the frozen hard residual `38` set.

## Rule Order

Classify a case by the first rule that matches.

1. `retrieval_selection`
2. `structured_route_unavailable`
3. `delivery_prompt_path`

## Rule Definitions

### `retrieval_selection`

Use this when the local replay does not expose answer-bearing support in the compact recall packet.

Operationally:
- `evidence_present = false`

Interpretation:
- the case is failing before any authoritative delivery decision can matter
- downstream benchmark labels like `prompt_miss` are treated as secondary symptoms here

### `structured_route_unavailable`

Use this when answer-bearing evidence is present, but no authoritative answer surface is available.

Operationally:
- `evidence_present = true`
- `answer_surface_hit = false`

Interpretation:
- the system has relevant support, but it still cannot convert that support into a covered authoritative route

### `delivery_prompt_path`

Use this when answer-bearing evidence is present and a structured authoritative answer surface exists, but the broader benchmark history still shows the case in the hard residual set.

Operationally:
- `evidence_present = true`
- `answer_surface_hit = true`

Interpretation:
- retrieval and structured routing look locally good enough
- any remaining miss is downstream: delivery, handoff, or judge behavior

## Deliberate Limitation

This map is intentionally local and upstream-first. It does **not** try to re-judge the benchmark case or replace prior paid evaluation. It exists to locate the first plausible failure seam before another mechanism is built.
