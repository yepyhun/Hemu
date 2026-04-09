# Packet And Handoff Comparator

- Fixed ten cases: `10`
- Direct packets with answer-bearing evidence: `2`
- Cases with any answer-surface text: `2`
- Cases with authoritative payload text: `2`
- Cases that short-circuit before the LLM path: `2`
- Non-short-circuit initial prompts containing surfaced answer text: `0`

## Meaning

- For non-short-circuit cases, the initial prompt contains only the generic Hermes/Core2 system block and the user question.
- There is no grounded packet-to-prompt handoff material present before tool use.
- So the first downstream actionable seam is not generic prompt wording; it is the missing promptless authoritative bridge from recall packet to answer surface/payload.

## Wrong Promptless Cases

- `b5ef892d` -> expected `8 days.`, local promptless payload `Answer: 1 days.`
- `bf659f65` -> expected `3`, local promptless payload `Answer: 1 music albums or EPs.`
