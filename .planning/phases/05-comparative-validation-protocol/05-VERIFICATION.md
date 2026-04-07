# Phase 5 Verification

## Goal Achievement

Phase 5 was intended to lock the baseline-versus-hybrid comparison protocol before any broader paid comparison in v1.1. That goal is met.

## Observable Truths

- A frozen machine-readable comparison manifest now exists.
- A canonical machine-readable outcome schema now exists.
- A human-readable protocol doc now exists.
- A machine-readable readiness proof now exists.
- No Core2 kernel, hybrid substrate, or benchmark harness behavior was changed as part of this phase.

## Verification Commands

- `node -e "const fs=require('fs'); const files=['.planning/phases/05-comparative-validation-protocol/05-COMPARISON-MANIFEST.json','.planning/phases/05-comparative-validation-protocol/05-CANONICAL-OUTCOME-SCHEMA.json','.planning/phases/05-comparative-validation-protocol/05-READINESS.json']; for (const f of files) JSON.parse(fs.readFileSync(f,'utf8')); console.log('JSON_OK');"`
- `test -f .planning/phases/04.1-longmemeval-gate-and-performance-fixes/04.1-GATE-STATUS-20.json && test -f .planning/phases/04.11-hybrid-branch-broader-paid-validation/04.11-OUTCOME.json && echo REFERENCES_OK`
- `node -e "const fs=require('fs'); const m=JSON.parse(fs.readFileSync('.planning/phases/05-comparative-validation-protocol/05-COMPARISON-MANIFEST.json','utf8')); const uniq=new Set(m.question_ids); if (m.sample_size_requested !== 20) throw new Error('bad sample size'); if (uniq.size !== m.question_ids.length) throw new Error('duplicate question ids'); if (!Array.isArray(m.verdict_precedence) || m.verdict_precedence.join(',') !== 'keep_baseline,mixed_hold,promote_candidate') throw new Error('bad verdict precedence'); console.log('MANIFEST_OK');"`

## Verification Results

- `JSON_OK`
- `REFERENCES_OK`
- `MANIFEST_OK`

## Required Artifacts

- `05-COMPARISON-MANIFEST.json`
- `05-PROTOCOL.md`
- `05-CANONICAL-OUTCOME-SCHEMA.json`
- `05-READINESS.json`
- `05-01-SUMMARY.md`
- `05-02-SUMMARY.md`
- `05-03-SUMMARY.md`

## Release Decision For 05

Phase 5 is ready to hand off into verification and then into Phase 6 planning/execution. The broader comparison can now run later without redefining the contract midstream.
