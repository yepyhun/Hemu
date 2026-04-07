# Core2 Golden Paths

## Purpose

These are tiny canonical success traces used for debugging and review.

They are not exhaustive tests. They are reference specimens that show what a known-good path looks like end to end.

## Golden Path 1: Updated Personal Attribute

1. Ingest old attribute fact
2. Ingest newer attribute fact
3. Digestion produces structured candidate(s)
4. Canonical state marks the newer fact as `current` and the older one as `previous` or `superseded`
5. Fact-first recall selects the `current` fact
6. Answer surface renders the current value
7. History remains inspectable

Expected kernel truth:

- currentness is explicit
- overwrite is not silent
- answer comes from structured state, not raw re-reasoning

## Golden Path 2: Collection Count Update

1. Ingest baseline collection total
2. Ingest item-added event
3. Digestion produces structured update candidate(s)
4. Canonical update logic materializes the new current total
5. Fact-first recall selects the current total artifact
6. Answer surface renders the updated total

Expected kernel truth:

- update is deterministic
- provenance remains inspectable
- total does not require a broad raw-history rescan

