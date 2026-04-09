# Phase 21 Lifecycle Labels

## Checkpoint Labels

- `source_session_present`
  - The dataset entry contains answer-bearing session IDs and they map into haystack positions.

- `persisted_answer_records_present`
  - After `_seed_core2_kernel`, canonical records exist with `metadata.session_index` inside the mapped answer positions.

- `session_local_hit`
  - `search_session_records(...)` returns at least one result for an answer-bearing session.

- `global_answer_session_hit`
  - `Core2Runtime.recall(...)` returns at least one item whose `metadata.session_index` is an answer-bearing position.

- `direct_packet_answer_surface`
  - The direct recall packet contains the literal gold answer according to `_packet_contains_answer(...)`.

## Seam Labels

- `persist_or_metadata_loss`
  - The answer-bearing session exists in the dataset, but no canonical record survives in the mapped answer positions.

- `representation_or_query_mismatch`
  - Canonical records exist in answer-bearing sessions, but even session-local lexical search cannot surface them.

- `global_opening_or_prefilter_loss`
  - Session-local search works, but global direct recall does not reach any answer-bearing session.

- `handoff_or_surface_loss`
  - Global direct recall reaches answer-bearing sessions, but the direct recall packet still does not contain the literal gold answer.

- `answer_surface_present`
  - The direct recall packet already contains the literal gold answer.
  - If the paid external run still fails, the remaining seam is downstream of direct recall.

## External Failure Labels Reused From `v1.14/20`

- `prompt_miss`
- `handoff_format_miss`

These are treated as end-to-end truth labels, not as replacements for the local lifecycle labels above.
