# Phase 21 Decision Rubric

## Rules

1. If answer-bearing sessions are absent in the dataset, the seam is `source absence`.
2. If answer-bearing sessions exist but no canonical records survive, the seam is `ingest / persist loss`.
3. If canonical answer-bearing records exist but session-local lexical search fails, the seam is `representation / indexing mismatch`.
4. If session-local lexical search works but global direct recall misses the answer-bearing sessions, the seam is `global opening / prefilter loss`.
5. If global direct recall reaches the answer-bearing sessions but the answer still does not surface in the direct packet or the external gate still fails, the seam is `post-recall surface / handoff`.

## Phase 21 Outcome Under This Rubric

- rules `1-3`: falsified as dominant explanations
- rule `4`: residual minority case (`1/10`)
- rule `5`: dominant explanation (`9/10`)

## Canonical Next Action

Open a bounded milestone that inspects and fixes the fixed-ten full-path handoff layer:

- memory tool packet packaging
- prompt assembly around the packet
- authoritative answer surface bridging
- promptless authoritative short-circuit eligibility

## Canonical Non-Actions

- do not reopen new retrieval heuristics first
- do not reopen presence/admission/index work first
- do not import legacy retrieval machinery
