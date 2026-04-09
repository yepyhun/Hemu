# Seam Taxonomy

## Counts

- `no_promptless_authoritative_bridge`: `5/10`
- `answer_surface_fallback_only`: `2/10`
- `authoritative_payload_wrong`: `2/10`
- `answer_bearing_packet_not_bridged`: `1/10`

## Canonical Interpretation

- The dominant fixed-ten miss is **not** later prompt wording or provider randomness.
- The dominant miss is that the promptless authoritative bridge is absent for most cases before the LLM path begins.
- When the bridge does exist locally on this slice, it is still incorrect (`2/2` wrong), so the bounded downstream problem is now concentrated in authoritative surface/payload logic rather than generic prompt assembly.
