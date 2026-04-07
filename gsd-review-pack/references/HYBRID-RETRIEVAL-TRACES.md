# Hybrid Retrieval Traces

## Trace 1: Verbatim Turn Context

Query:

`Which trip involved my cousin from Portland?`

Off:

- top item: `Recent trip event: day hike to Mount Tam with Rowan`
- retrieval path: none
- notes: curated-memory route only

Shadow:

- top item: `Recent trip event: day hike to Mount Tam with Rowan`
- retrieval path: none
- notes include `hybrid_raw_hit`, `hybrid_turn_hit`, `hybrid_shadow_only`

On:

- top item: `Recent trip event: day hike to Muir Woods with Maya`
- retrieval path: `hybrid_scoped_turn`
- notes include `hybrid_raw_hit`, `hybrid_turn_hit`

Meaning:

- the new seam can recover a correct canonical object from lossless turn text
- the rollback/shadow switch works
- truth ownership still remains with canonical Core2 objects

## Trace 2: Raw Archive Scope

Query:

`Where does the backup drill runbook live?`

Off:

- top item: canonical note content
- retrieval path: none

On:

- top item: same canonical note content
- retrieval path: `hybrid_scoped_raw`
- notes include `hybrid_raw_hit`

Meaning:

- the raw-archive seam is callable and visible
- answer ownership does not move out of Core2
- the new substrate can be introduced without a second answer layer
