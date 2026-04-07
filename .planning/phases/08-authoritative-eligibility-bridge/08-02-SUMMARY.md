# 08-02 Summary

Implemented the bounded authoritative-eligibility bridge by allowing structured covered-fact extractors to accept `hybrid_scoped_turn` and `hybrid_scoped_raw` digested facts in addition to `fact_first`.

Proof:
- targeted bridge suite + related local suites: `28 passed`
- full `tests/agent/test_core2_*.py`: `125 passed`
