# Plan 18-02 Summary

Each frozen case was classified into one upstream candidate-pool miss shape.

Counts:
- `temporal_anchor_seed_miss`: `11`
- `query_shape_not_opened`: `10`
- `entity_scope_binding_miss`: `3`
- `unsupported_upstream_shape`: `3`
- `admission_rule_miss`: `2`

This shows there is no single runaway atomic label, but there is one dominant actionable family:

- `query_shape_conditioned_candidate_seeding`: `21/29`
