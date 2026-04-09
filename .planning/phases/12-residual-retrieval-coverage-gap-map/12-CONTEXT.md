# Phase 12: Residual Retrieval Coverage Gap Map - Context

**Gathered:** 2026-04-08
**Status:** Planned

## Phase Boundary

Phase 12 is a retrieval-side diagnostic phase. It starts from the verified Phase 11 result that `33/38` hard residual cases fail first at `retrieval_selection`.

This phase does **not** build a new retrieval mechanism. It maps the concrete gap shapes inside that `33`-case subset so the next retrieval-side bet is chosen from evidence rather than intuition.

## Locked Decisions

### What This Phase Must Do

- freeze the `33` retrieval-dominant residual subset from Phase 11
- define a narrow retrieval-gap taxonomy
- classify each of the `33` cases into one retrieval-side gap class
- aggregate the dominant gap classes across the subset
- end with exactly one bounded retrieval-side recommendation or one explicit stop rule

### What This Phase Must Not Do

- no new runtime behavior
- no retrieval ranking reintroduction
- no delivery bridge work
- no substrate replacement work
- no comparator changes
- no family growth
- no paid rerun
- no case-by-case patching

## Prior Evidence That Must Be Preserved

- Phase 11 already falsified delivery as the dominant next build direction
- Phase 11 showed:
  - `retrieval_selection`: `33`
  - `structured_route_unavailable`: `3`
  - `delivery_prompt_path`: `2`
- therefore Phase 12 must only analyze the `33` retrieval-dominant cases

## Required Canonical Artifacts

- `12-RETRIEVAL-SUBSET-MANIFEST.json`
- `12-GAP-TAXONOMY.md`
- `12-COVERAGE-TRANSITIONS.jsonl`
- `12-OUTCOME.json`

## Success Criteria

- the `33`-case retrieval subset is frozen and auditable
- every case is assigned one retrieval-gap class
- the milestone ends with one bounded retrieval-side recommendation or one explicit stop rule

## Anti-Loop Rule

If the retrieval gap map is too mixed to justify one next build, the correct outcome is a stop rule or a narrow instrumentation recommendation, not a forced retrieval implementation.
