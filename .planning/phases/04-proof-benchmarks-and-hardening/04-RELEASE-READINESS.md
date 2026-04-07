# Phase 4 Release Readiness

## Current Readiness

Core2 is locally proofed and regression-covered enough to claim a strong internal-ready state for the Hermes-path memory kernel. It is not yet honest to claim final benchmark victory or stronger SOTA readiness until the paid LongMemEval-10 gate is run.

## Green Gates

- Targeted Core2 suite is green locally.
- MemoryManager-level Hermes-path lifecycle proof exists.
- Structured proof harness exists with inspectable `modes` and scenario outputs.
- Synthetic LongMemEval-style subset proof exists and is green locally.
- Token/replay proof reporting exists for compact-vs-baseline context comparison.
- Hardening coverage now protects noisy graph recall, mixed-history update resolution, and noisy high-risk conflict abstention.

## Remaining Blockers To Stronger Claims

- Paid LongMemEval-10 external run is still pending and remains the final gate.
- Full `uv run --extra dev pytest ...` remains environment-sensitive because of offline git dependency resolution for `tinker`.
- Repo-local git identity is still unset, so strict atomic local commits are still blocked.

## Known Limits

- The builtin-only comparison mode is only an integration-seam baseline. It is not a claim that builtin Hermes memory is the full competitor benchmark.
- Core2 still assumes the current one-external-provider architecture.
- The local LongMemEval-style subset is a deterministic proxy proof, not the final benchmark.

## Safe Claim

Safe now:
- Core2 is locally verified through the real Hermes provider/runtime seam with structured proof artifacts and broader regression coverage.

Not safe yet:
- “Final benchmark winner”
- “LongMemEval-proven”
- “Externally validated SOTA”

## Recommended Next Gates

1. Run `/gsd-verify-work 4` for user-facing acceptance.
2. Run the paid LongMemEval-10 Hermes-path evaluation.
3. Only after that, make any stronger readiness or SOTA claim.
