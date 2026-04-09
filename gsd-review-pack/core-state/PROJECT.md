# Hermes Core2 Memory Kernel

## What This Is

Hermes Core2 is a deterministic memory kernel for durable user facts, temporal state, and fail-closed answer delivery. It is not just a retrieval layer: the core value is stable fact identity, provenance, supersession/conflict handling, abstention, and provider-owned authoritative answers.

## Core Value

Build a memory system that is honest, deterministic where it matters, and strong enough to support real long-horizon recall without collapsing into benchmark-only tuning.

## Current State

`v1.0` is the archived shipped baseline. `v1.1` established the bounded hybrid branch, measured it honestly against the baseline on a frozen broader set, and reduced the forward work to one leverage bet: an authoritative-eligibility bridge for already-covered families. `v1.2` verified that bridge locally and added bounded hardening through explicit invariants and narrow noise repair. `v1.3` completed a bounded retrieval-ranking borrow for the hybrid path, but the fresh paid residual replay regressed from `3/38` to `2/38`. `v1.4` retired that ranking path from the active hybrid route and recorded a canonical postmortem. `v1.5` then forced a stricter diagnostic phase over the frozen hard residual `38` set and showed that the dominant next problem is not delivery but retrieval/selection coverage. `v1.6` converted that retrieval-dominant verdict into a verified coverage map: the hard residual bucket is led by weak or partial aggregate-temporal evidence gaps, with wrong subset selection as the second bucket. `v1.7` shipped a bounded constituent-anchor retrieval expansion against the safe compositional tranche of that bucket and explicitly left plain current-total aggregates excluded after first-pass regressions. `v1.8` shipped a bounded budgeted evidence selector plus narrow aggregation safety for the same retrieval-side problem family. `v1.9` completed the next bounded jackpot slice: a reusable pipeline attribution contract inside the existing benchmark plumbing. `v1.10/16` then applied that contract to one real frozen hard residual replay, and the result was honest but harsh: the raw replay stayed at `3/38`, only `1/38` counts as an attributed grounded pass, and the dominant actionable bucket remains `retrieval_failure`. `v1.11` reduced the next move further: the hard replay miss is upstream of selector engagement, so the bounded carry-forward is now pre-selector candidate-pool work. `v1.12` completed that narrowing and proved that the dominant remaining actionable family is `query_shape_conditioned_candidate_seeding` across `21/29` hard residual cases. `v1.13` then turned that carry-forward into one bounded upstream build, with narrow inspiration from staged retrieval/context-tree systems but without reopening broad retrieval redesign, but the paid random hard gate still returned `0/5`. `v1.14/20` then took a different compromise route: a fixed representative ten-case forensic slice plus one narrow legacy query-signal primitive borrow. That produced strong local proof but a negative fixed external gate (`0/10`). `v1.15/21` went one layer deeper and verified that the fixed-ten hard slice is not primarily blocked by source absence, gross persistence/index loss, or session-local unsearchability: the dominant seam is now downstream, in post-recall answer surface / handoff loss, with only one residual global opening miss. `v1.16/22` then localized that downstream seam more precisely: the dominant miss is missing promptless authoritative bridging, and the few local promptless-authoritative cases are currently wrong, so the next bounded direction is authoritative answer-surface / payload expansion rather than upstream retrieval reopening.

## Current Milestone

`v1.17 Bounded Authoritative Surface Payload Expansion` starts directly from the verified `v1.16/22` downstream seam: answer-bearing packets exist often enough, but they are not being turned into correct promptless authoritative surfaces. The milestone is intentionally bounded to bridge coverage and payload correctness on the same fixed hard slice.

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

- `HAND-02` active in `v1.17/23` — the fixed hard slice must receive one bounded authoritative bridge/payload fix rather than another generic downstream forensic pass
- `QUAL-27` active in `v1.17/23` — the milestone must stay downstream-only and must not reopen upstream retrieval, ranking, selector, or architecture work without new contrary evidence
- `FUT-27` active in `v1.17/23` — the milestone must end with one honest fixed-ten external verdict: improved, unchanged, or regressed

### Newly Validated In `v1.16/22`

- `HAND-01` validated in `v1.16/22` — the fixed hard slice is now traced at packet, surface, payload, and handoff checkpoints rather than only broad downstream symptom labels
- `QUAL-26` validated in `v1.16/22` — the phase stayed downstream-forensic-first and did not reopen upstream retrieval heuristics
- `FUT-26` validated in `v1.16/22` — the milestone now ends with one canonical carry-forward direction: `bounded_authoritative_surface_payload_expansion`

### Newly Validated In `v1.15/21`

- `RETR-21` validated in `v1.15/21` — the fixed hard slice is now localized deeply enough to rule out source absence, gross persist/index loss, and session-local unsearchability as dominant explanations
- `QUAL-25` validated in `v1.15/21` — the milestone stayed forensic-first and did not widen into another heuristic retrieval build
- `FUT-25` validated in `v1.15/21` — the phase ends with one canonical carry-forward direction: `fixed_ten_handoff_surface_forensics`

### Newly Validated In `v1.14/20`

- `RETR-20` — validated negatively: the fixed ten-case seam was frozen and traced, and the resulting evidence shows the bottleneck remains upstream retrieval opening
- `QUAL-24` — validated: only one narrow primitive family was borrowed and the boundary remained intact
- `FUT-24` — validated negatively: the milestone ended with one canonical verdict, and that verdict is that the bounded primitive borrow did not move the fixed ten-case replay

### Newly Archived In `v1.14/20`

- `RETR-20`
- `QUAL-24`
- `FUT-24`

### Newly Archived In `v1.13/19`

- `v1.13/19` delivered a bounded decomposition-and-seeding stack with strong local proof but no external movement claim
- the follow-up random paid hard sample stayed at `0/5`, so the phase is archived as locally informative but externally non-advancing

### Newly Validated In `v1.13/19`

- `RETR-19` validated in `v1.13/19` — the upstream candidate pool now opens bounded query-shape-conditioned seed families locally before selector engagement on the target slice
- `QUAL-23` validated in `v1.13/19` — the phase stayed strictly upstream-of-selector without reopening ranking, delivery, or broad retrieval redesign
- `FUT-23` validated in `v1.13/19` — the milestone now ends with one canonical verdict: the bounded seeding mechanism is `go_local_replay_worthy` without claiming external benchmark movement

### Newly Validated In `v1.12/18`

- `RETR-18` validated in `v1.12/18` — the verified pre-selector subset is now reduced to one dominant actionable upstream family rather than generic selector tuning
- `QUAL-22` validated in `v1.12/18` — the phase stayed strictly upstream-of-selector without reopening delivery, ranking, or broad retrieval ideation
- `FUT-22` validated in `v1.12/18` — the milestone now ends with one canonical carry-forward recommendation: `query_shape_conditioned_candidate_seeding`

### Newly Validated In `v1.11/17`

- `RETR-17` validated in `v1.11/17` — the attributed `retrieval_failure` bucket is now classified into one bounded selection taxonomy
- `QUAL-21` validated in `v1.11/17` — the phase reduced the next retrieval-side move to one bounded pre-selector follow-up without reopening unrelated layers
- `FUT-21` validated in `v1.11/17` — the milestone now ends with one canonical carry-forward build recommendation rather than multiple retrieval bets

### Previously Validated In `v1.10/16`

- `OBS-05` validated in `v1.10/16` — the phase-15 attribution contract now exists on one real frozen hard residual replay artifact
- `QUAL-20` validated in `v1.10/16` — one canonical attributed replay outcome now names the dominant live failure bucket on the hard residual set
- `FUT-20` validated in `v1.10/16` — the next build choice is reduced to one bounded follow-up informed by attributed replay rather than competing hypotheses

### Previously Validated In `v1.9/15`

- `OBS-04` validated in `v1.9/15` — Core2 now emits a bounded per-case attribution record that separates retrieval, sufficiency, reasoning/delivery, and judge-like outcomes
- `REL-08` validated in `v1.9/15` — the milestone stayed bounded to observability and evaluation plumbing
- `FUT-19` validated in `v1.9/15` — one canonical diagnostic contract now exists for future phases

### Out of Scope

- New broad benchmark comparison phases until the local bridge hypothesis is built and falsified
- Wholesale substrate replacement or reopening the MemPalace adoption decision
- New family spam, comparator growth, or benchmark-specific wording patches

## Context

The main lesson from `v1.1` was that the bounded hybrid branch was directionally better than the baseline, but the gain did not cross into the authoritative answer path often enough. `v1.2` closed that local bridge hypothesis cleanly on a bounded falsification slice and then hardened the path with explicit invariants and narrow noise repair. `v1.3` translated the next bounded bet into code: better candidate ordering now existed locally as a ranking borrow inside the hybrid retrieval seam, without reopening the substrate or truth model. The fresh paid replay on the hard residual `38` showed that this was not the breakthrough: the result regressed from `3/38` to `2/38`, with `prompt_miss` still dominating. `v1.4` retired that failed ranking path cleanly. `v1.5/11` then mapped the first true failure point per residual case and showed that `33/38` fail upstream in retrieval/selection, with only `2/38` looking delivery-like. `v1.6` answered that narrower retrieval question locally: the dominant residual gap is weak or partial aggregate-temporal evidence (`15/33`), followed by wrong subset selection (`11/33`).

The current state after `v1.7` is cleaner than before the build: one real retrieval-side mechanism shipped, one explicit exclusion list preserved, and no active milestone competing for ownership. The next step should stay bounded and explicit rather than widening Phase 13 retroactively.

The new research note changes the shape of the next move: rather than another ad hoc retrieval expansion, the stronger bounded bet is now a selector-layer improvement with explicit aggregation safety. This is still retrieval-side, still compositional, and still narrow enough to avoid replaying the old project's complexity collapse.

`v1.8/14` verified that this selector-layer move is locally real: complementary temporal anchors can now be selected as a bounded set, incompatible numeric composition abstains safely, and the observability surface is better than before. The phase still does not claim broad benchmark victory or coverage of plain current-total aggregates.

The strongest remaining jackpot slice after `v1.8` was not another retrieval build but a better diagnostics layer. `v1.9/15` delivered that layer locally, so the next milestone should apply it to a real frozen replay before opening another kernel build.

`v1.10/16` completed that replay. The main value is not a better score, but a harder truth: the current active path still fails upstream in retrieval on most hard residual cases, and two of the three raw passes are not grounded wins but judge-false-positive artifacts. `v1.11/17` tightened that further: on the attributed `retrieval_failure` subset, the active path never even reaches selector engagement. `v1.12/18` then resolved the next narrowing step: the top two upstream miss shapes collapse into one bounded actionable family, `query_shape_conditioned_candidate_seeding`, while entity/scope binding and unsupported/non-authoritative shapes remain secondary residuals.

The new milestone should not widen into a full external-system borrow. The useful external analogies are narrower: staged retrieval from OpenViking and context-tree/pre-curation from ByteRover/Cipher both point toward one missing seam in Core2, namely query-shape-conditioned upstream seed admission before selector logic runs. That is the bounded build target for `v1.13`, not a generic platform rewrite.

## Constraints

- Keep the deterministic core contract intact
- Do not reopen broad benchmark loops casually; any future rerun should follow a diagnostic verdict, not precede it
- Prefer one bounded high-leverage mechanism over many small case-wise fixes
- Keep the hybrid branch reversible if a later build hypothesis fails
- Do not let a carry-forward recommendation harden into a build plan without per-case evidence that the bottleneck really sits there
- Do not reopen the delivery-bridge path from the current evidence; the local first-failure map falsified it as the dominant next bet
- Do not open multiple retrieval hypotheses at once; the milestone must end with one bounded next build or one stop rule
- Do not treat raw replay passes as grounded wins when the attribution layer labels them as judge-false-positive cases
- Do not widen into full operator-slot decomposition, bitemporal refactors, or promotion-gate work before the upstream candidate-pool seam is mapped
- Do not widen the next milestone into full staged retrieval or context-tree adoption; only borrow the minimal seeding pattern needed for the verified hard residual family

## Key Decisions

- `v1.0` remains the archived shipped baseline and reference point
- `v1.1` selected the hybrid branch as the pragmatic forward path while keeping the broader comparison verdict honest (`mixed_hold`)
- `v1.2` was a bounded build milestone around authoritative eligibility for already-covered families plus local hardening imports
- `v1.3` used retrieval-ranking borrow as the next bounded forward direction rather than reopening multiple borrow threads at once
- `v1.3/09` landed the ranking borrow locally and left the next broader check for a later milestone, not as an inline continuation
- `v1.4` starts from the broader residual replay truth: ranking borrow did not improve the hard `38` set and should be rolled back from the active path before any new forward bet
- `v1.4/10` completed that rollback and recorded `Covered-Family Prompt Delivery Bridge` as the single carried-forward recommendation
- `v1.5` will not treat that recommendation as a build commitment until a first-failure map shows that delivery is actually the dominant bottleneck
- `v1.5/11` completed that map and falsified delivery as the dominant next build direction; the carry-forward recommendation is now `Residual Retrieval Coverage Gap Map`
- `v1.6` started from the retrieval-dominant verdict and completed the explicit gap map before any new retrieval build was promoted
- `v1.7` starts from the verified Phase 12 map and promotes only the dominant aggregate-temporal retrieval gap into a bounded build milestone
- `v1.7/13` executed a constituent-anchor retrieval expansion that now reaches real seeded temporal / ratio / pairwise cases while explicitly excluding plain current-total aggregate shapes from this tranche
- `v1.7` is now archived; the next milestone should be chosen explicitly rather than silently widening the aggregate-temporal tranche
- `v1.8` chooses `budgeted evidence selector + aggregation safety` as the next bounded milestone instead of silently spreading the jackpot research across multiple phases
- `v1.8/14` verified the bounded selector-and-safety build locally and kept the phase out of bitemporal, promotion-gate, ranking, and delivery side-tracks
- `v1.8` is now archived; the next milestone should be chosen explicitly rather than broadening the selector milestone after the fact
- `v1.9` chose the pipeline attribution dashboard as the next bounded milestone instead of jumping straight into bitemporal or promotion-gate work
- `v1.9/15` completed and verified the bounded attribution contract, so future benchmark and replay work can attribute failures without rereading mixed raw outputs manually
- `v1.10` starts by applying that attribution contract to one real frozen hard residual replay before promoting any new build hypothesis
- `v1.10/16` completed that replay and showed one dominant actionable bucket: `retrieval_failure` on the hard residual `38`, with only one attributed grounded pass in the raw `3/38` result
- `v1.11` starts by turning that replay truth into one bounded retrieval-selection follow-up rather than reopening broader retrieval expansion
- `v1.11/17` showed the miss is upstream of selector engagement; the canonical carry-forward is now `pre_selector_candidate_pool_followup`
- `v1.12` starts by turning that carry-forward into one bounded upstream retrieval milestone and keeping all downstream layers frozen
- `v1.12/18` completed that upstream narrowing and reduced the next build to one bounded family: `query_shape_conditioned_candidate_seeding`
- `v1.13` starts by turning that bounded family into one upstream candidate-seeding build while keeping the borrow surface narrow: staged admission patterns are allowed, but full external retrieval architectures are not
- `v1.15` starts from the conclusion that more heuristic retrieval tweaks are not justified until the system proves where answer-bearing memory dies across the fixed hard slice lifecycle
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

*Last updated: 2026-04-08 after starting milestone v1.14*
