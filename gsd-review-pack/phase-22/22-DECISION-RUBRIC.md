# Decision Rubric

If the dominant count is `no_promptless_authoritative_bridge` or `answer_surface_fallback_only`, the next allowed action is:

- one bounded implementation phase to expand authoritative answer-surface / payload coverage for the dominant fixed-ten families

If the dominant count is `authoritative_payload_wrong`, the next allowed action is:

- one bounded implementation phase to repair payload computation correctness before any broader replay

If no single downstream family dominates, the next allowed action is:

- explicit stop verdict

This phase forbids carrying forward multiple speculative downstream fixes at once.
