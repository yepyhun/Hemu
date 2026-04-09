# Phase 23 Bridge Rules

## Supported Family

The bounded Phase 23 expansion supports exactly one new promptless authoritative family:

- `duration_total_from_surfaced_fragments`

This family is in scope only when all of the following are true:

- the query asks `how many ... in total`
- the requested unit is days
- the recalled packet already surfaces at least `2` first-person duration-bearing fragments
- each supporting fragment contains a parseable duration (`X days`, `X weeks`, `X-day`, `X-week`, `week-long`)
- the fragments overlap with the query focus tokens

## Authoritative Surface Contract

For the supported family, the authoritative payload may return:

- `mode = aggregate_count`
- `answer = Answer: <total> days.`

Only surfaced packet evidence may be used. No extra retrieval, index expansion, or hidden backfill is allowed.

## Safety Boundary

The Phase 23 bridge must not short-circuit when any of the following is true:

- only one duration-bearing fragment is surfaced
- the surfaced fragments are only partially aligned with the query scope
- the query is a time-window aggregate requiring missing sessions
- the query is a collection count rather than a duration total
- the query needs pairwise temporal comparison, elapsed-time reasoning, or current/previous switching

In those cases the system must continue to fallback safely instead of emitting a wrong promptless authoritative answer.

## Explicit Out Of Scope Families

The bounded Phase 23 change does not try to solve:

- `aggregate_total_time_window`
- `aggregate_count_control`
- `aggregate_percentage`
- `temporal_after`
- `temporal_elapsed_ago`
- `pairwise_first`
- `pairwise_first_abs`
- `current_previous_switch`
- `current_previous_frequency`

## Truth Conditions

Local truth for Phase 23:

- the new supported family resolves correctly in local authoritative tests
- known partial-support cases stop short-circuiting incorrectly
- existing authoritative regression tests remain green

External truth for Phase 23:

- only the unchanged fixed hard `10` paid gate may justify an improvement claim
- without that gate, the phase may claim only `local_execute_complete`
