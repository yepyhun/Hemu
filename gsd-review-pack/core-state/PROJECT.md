# Hermes Core2 Memory Kernel

## What This Is

Hermes Core2 is a deterministic memory kernel for durable user facts, temporal state, and fail-closed answer delivery. It is not just a retrieval layer: the core value is stable fact identity, provenance, supersession/conflict handling, abstention, and provider-owned authoritative answers.

## Core Value

Build a memory system that is honest, deterministic where it matters, and strong enough to support real long-horizon recall without collapsing into benchmark-only tuning.

## Current State

`v1.0` is the archived shipped baseline. `v1.1` established the bounded hybrid branch, measured it honestly against the baseline on a frozen broader set, and reduced the forward work to one leverage bet: an authoritative-eligibility bridge for already-covered families. `v1.2` verified that bridge locally and added bounded hardening through explicit invariants and narrow noise repair. `v1.3` completed a bounded retrieval-ranking borrow for the hybrid path, but the fresh paid residual replay regressed from `3/38` to `2/38`. `v1.4` retired that ranking path from the active hybrid route and recorded a canonical postmortem. There is currently no active milestone.

## Current Milestone

No active milestone.

**Next milestone should decide whether to pursue the carried-forward `Covered-Family Prompt Delivery Bridge` recommendation or another single bounded mechanism.**

## Requirements

### Validated

- `QUAL-04` archived in `v1.0` — paid `10/10` Hermes-path baseline accepted
- `REL-01` validated in `v1.1/05` — comparison protocol locked before broader evaluation
- `QUAL-11` validated in `v1.1/06` — frozen `70`-sample baseline vs hybrid comparison completed honestly
- `QUAL-12` validated in `v1.1/06` — canonical comparison outcome recorded without threshold-moving
- `QUAL-13` validated in `v1.1/07` — breakthrough search reduced to one bounded next direction
- `FUT-13` validated in `v1.1/07` — dominant blocked path mapped at mechanism level
- `FUT-14` validated in `v1.1/07` — explicit stop rule prevents reopening micro-benchmark loops
- `RETR-12` validated in `v1.2/08` — already-covered family evidence now crosses the bounded authoritative eligibility bridge
- `QUAL-14` validated in `v1.2/08` — bounded falsification slice shows route-shift without comparator softening or benchmark phrasing changes
- `REL-03` validated in `v1.2/08` — rollback simplicity and deterministic-core ownership remain intact
- `QUAL-15` validated in `v1.2/08.1` — Core2 now encodes a bounded invariant catalog and repeatable acceptance checks instead of relying on benchmark results alone
- `REL-04` validated in `v1.2/08.1` — explicit noise repair rejects obvious tool/file error artifacts without widening the truth model
- `RETR-13` validated in `v1.3/09` — bounded retrieval-ranking signals now influence hybrid candidate ordering
- `QUAL-16` validated in `v1.3/09` — ranking borrow stayed inside the planned seam without comparator, family, or truth-model growth
- `REL-05` validated in `v1.3/09` — the hybrid ranking borrow remains reversible and locally measurable

### Active

- none; waiting for the next milestone definition

### Out of Scope

- New broad benchmark comparison phases until the local bridge hypothesis is built and falsified
- Wholesale substrate replacement or reopening the MemPalace adoption decision
- New family spam, comparator growth, or benchmark-specific wording patches

## Context

The main lesson from `v1.1` was that the bounded hybrid branch was directionally better than the baseline, but the gain did not cross into the authoritative answer path often enough. `v1.2` closed that local bridge hypothesis cleanly on a bounded falsification slice and then hardened the path with explicit invariants and narrow noise repair. `v1.3` translated the next bounded bet into code: better candidate ordering now exists locally as a ranking borrow inside the hybrid retrieval seam, without reopening the substrate or truth model. The fresh paid replay on the hard residual `38` showed that this was not the breakthrough: the result regressed from `3/38` to `2/38`, with `prompt_miss` still dominating. `v1.4` retired that failed ranking path cleanly and left one bounded carry-forward recommendation: `Covered-Family Prompt Delivery Bridge`.

## Constraints

- Keep the deterministic core contract intact
- Do not reopen broad benchmark loops casually; any future rerun should belong to a fresh milestone decision
- Prefer one bounded high-leverage mechanism over many small case-wise fixes
- Keep the hybrid branch reversible if the ranking borrow fails
- Do not preserve ranking borrow in the active path just because it was locally green; broader residual evidence wins

## Key Decisions

- `v1.0` remains the archived shipped baseline and reference point
- `v1.1` selected the hybrid branch as the pragmatic forward path while keeping the broader comparison verdict honest (`mixed_hold`)
- `v1.2` was a bounded build milestone around authoritative eligibility for already-covered families plus local hardening imports
- `v1.3` used retrieval-ranking borrow as the next bounded forward direction rather than reopening multiple borrow threads at once
- `v1.3/09` landed the ranking borrow locally and left the next broader check for a later milestone, not as an inline continuation
- `v1.4` starts from the broader residual replay truth: ranking borrow did not improve the hard `38` set and should be rolled back from the active path before any new forward bet
- `v1.4/10` completed that rollback and recorded `Covered-Family Prompt Delivery Bridge` as the single carried-forward recommendation

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

*Last updated: 2026-04-08 after completing milestone v1.4*
