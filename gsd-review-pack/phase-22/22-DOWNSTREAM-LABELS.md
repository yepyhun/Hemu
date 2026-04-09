# Downstream Labels

- `authoritative_payload_wrong`
  A bounded authoritative payload exists and short-circuits the agent path, but the payload does not match the dataset answer.

- `answer_surface_fallback_only`
  Recall produces items and an answer-surface family, but only fail-closed fallback material is available; no bounded authoritative payload resolves.

- `answer_bearing_packet_not_bridged`
  The direct recall packet already contains answer-bearing evidence, but no authoritative surface/payload is built from it.

- `no_promptless_authoritative_bridge`
  Recall returns non-abstaining items, but no answer surface text and no authoritative payload are produced, so the agent falls through to the normal LLM path with no grounded bridge.
