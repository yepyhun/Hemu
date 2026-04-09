# Phase 21 Seam Taxonomy

## Disproven As Dominant Seams

- `source absence`
  - falsified on `10/10`
  - every fixed-ten case has answer-bearing dataset sessions

- `gross ingest / persist loss`
  - falsified on `10/10`
  - every fixed-ten case has canonical records in the mapped answer-bearing session positions

- `session-local unsearchability`
  - falsified on `10/10`
  - every fixed-ten case has positive `search_session_records(...)` hits on the answer-bearing sessions

## Residual Seams

- `global_opening_or_prefilter_loss`
  - `1/10`
  - case: `c4ea545c`
  - answer-bearing sessions persist and are locally searchable, but direct global recall still misses them

## Dominant Seam Family

- `post-recall surface / handoff insufficiency`
  - `9/10`
  - composition:
    - `handoff_or_surface_loss`: `6`
    - `answer_surface_present` but external gate still fails: `3`

This means the fixed ten is no longer best explained by “the memory is not there” or “it never gets indexed”.
The majority story is:

1. answer-bearing memory is present
2. it is locally searchable
3. direct runtime recall often reaches the right sessions
4. the full authoritative path still fails to surface or use it correctly

## Diagnostic Gotcha

- The dataset uses string `answer_session_ids`
- seeded Core2 memory keeps only numeric `session_index`

This is not the dominant user-facing seam, but it is a real diagnostic mismatch that future forensic tooling should preserve explicitly.
