# Downstream Protocol

1. Seed exactly the fixed representative ten from `v1.14/20`.
2. For each case, capture direct `Core2Runtime.recall(...)` output.
3. Record whether `packet_contains_answer` is already true.
4. Record whether `build_answer_surface(...)` yields:
   - no surface
   - fallback surface
   - structured surface with text
5. Record whether `try_authoritative_answer(...)` yields a bounded payload.
6. Run `AIAgent.run_conversation(...)` with a fake OpenAI-like response object only to observe:
   - whether promptless authoritative short-circuit happens (`api_calls == 0`)
   - what the initial prompt contains when the LLM path is used
7. Assign exactly one downstream seam label per case.

This protocol is downstream-only. It does not reopen upstream retrieval, ranking, or architecture questions.
