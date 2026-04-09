# Plan 11-02 Summary

The frozen hard residual `38` set was replayed locally through Core2 seeding plus recall, without reopening the paid benchmark loop.

Canonical output:
- `11-CASE-TRANSITIONS.jsonl`

Observed bucket counts:
- `retrieval_selection`: `33`
- `structured_route_unavailable`: `3`
- `delivery_prompt_path`: `2`

Non-retrieval cases:
- `80ec1f4f` → `delivery_prompt_path`
- `bf659f65` → `delivery_prompt_path`
- `76d63226` → `structured_route_unavailable`
- `dccbc061` → `structured_route_unavailable`
- `71017276` → `structured_route_unavailable`

The diagnostic result is therefore strongly upstream: the hard residual slice is dominated by retrieval/selection misses, not by a dominant delivery-path bottleneck.
