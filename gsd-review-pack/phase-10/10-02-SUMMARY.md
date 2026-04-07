# 10-02 Summary

Removed ranking from the active hybrid candidate-ordering path.

Implementation:
- `agent/core2_hybrid_substrate.py` no longer imports or uses ranking helpers
- ranking-specific tests were replaced with rollback-proof candidate-ordering checks

Proof:
- targeted rollback proof: `7 passed in 0.36s`
- wider Core2 regression: `133 passed in 14.30s`

Canonical local outcome:
- `10-LOCAL-OUTCOME.json`
