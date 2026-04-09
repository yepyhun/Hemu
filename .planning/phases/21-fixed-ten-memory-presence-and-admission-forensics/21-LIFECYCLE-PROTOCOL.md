# Phase 21 Lifecycle Protocol

## Fixed Slice

- Source manifest: `../20-ten-case-retrieval-opening-forensics-and-primitive-borrow/20-TEN-CASE-MANIFEST.json`
- Dataset: `/home/lauratom/LongMemEval/data/longmemeval_s_cleaned.json`
- External truth source: `../20-ten-case-retrieval-opening-forensics-and-primitive-borrow/20-TEN-CASE-ATTRIBUTION-STATUS.json`

## Goal

Determine where answer-bearing memory dies on the fixed hard `10` before any new heuristic build is allowed.

## Checkpoints

1. `source_presence`
   - Confirm the dataset entry has `answer_session_ids`.
   - Map those string session IDs into seeded numeric `session_index` positions via:
     `enumerate(entry["haystack_session_ids"], start=1)`.

2. `persisted_presence`
   - Seed Core2 with `_seed_core2_kernel(home, entry, oracle_only=False)`.
   - Inspect `Core2Store.list_canonical_objects(include_inactive=False)`.
   - Count records whose `metadata.session_index` falls inside the mapped answer positions.

3. `session_local_surface`
   - For each mapped answer position, run:
     `search_session_records(session_index, question, max_items=5, turns_only=False)`.
   - This is the nearest lexical check that bypasses global competition.

4. `direct_runtime_recall`
   - Run `Core2Runtime.recall(question, max_items=6)`.
   - Record whether any returned item belongs to an answer-bearing session.
   - Record whether the direct packet contains the literal gold answer using `_packet_contains_answer(...)`.

5. `external_handoff_truth`
   - Compare the direct recall results against the fixed-ten paid gate from `v1.14/20`.
   - Use the paid artifact failure patterns as the authority for end-to-end outcome.

## Operational Notes

- The dataset stores answer-bearing sessions as string IDs such as `answer_a4204937_1`.
- The current Core2 benchmark seeding path stores only numeric `session_index` in memory metadata.
- This is a diagnostic gotcha: answer-session provenance is preserved by position, not by original session ID string.

## Falsification Rules

- If a case has mapped answer positions and persisted canonical records there, then `source absence` and `gross ingest loss` are falsified for that case.
- If session-local search returns hits on answer positions, then `unindexed / unsearchable within source session` is falsified for that case.
- If direct runtime recall reaches answer positions, then `dominant global admission/prefilter loss` is weakened for that case.
- If direct runtime recall reaches answer positions but the literal gold answer still does not surface in the packet or the paid gate still fails, then the seam moves downstream to `surface / handoff / prompt packaging`.

## Canonical Decision Rule

The next milestone must target the earliest checkpoint that still explains the majority of the fixed `10`.
