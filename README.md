# Hemu — Core2 Memory Kernel Review Mirror

> Public review mirror of the current Core2 memory-kernel branch.  
> Not a release build, not a standalone product, and not the main development repo.

This repository is a curated mirror of the current **Hemu / Hermes Core2** work as of the latest mirrored planning state. It contains:
- the current Core2 modules
- the current Core2 tests
- the GSD planning and verification trail
- milestone and phase artifacts through the latest bounded benchmark-facing work
- the latest post-v1.17 cleanup pass on the live Core2 runtime path

The point of this repo is **reviewability**, not polish. It is here so someone can inspect:
- the current kernel code
- the experimental trail and benchmark gates
- the verified bottleneck shifts over time
- which ideas were kept bounded, which were rolled back, and which remain active

No secrets or API keys are included here.

---

## What Core2 Is

Core2 is a **deterministic memory kernel** for durable facts and temporal state inside an agent runtime.

The target is not generic “better retrieval.” The target is:
- stable memory objects
- provenance and source traceability
- temporal and factual consistency
- explicit state transitions
- grounded answer surfaces
- fail-closed behavior when support is not good enough

The intended user experience is that the system remembers in the background and answers from structured memory evidence rather than re-deriving everything from raw history every time.

---

## What The Project Learned So Far

The development history matters here because this repo is not just a code dump; it is a trail of bounded hypotheses that were tried and measured.

### v1.0

Established the shipped deterministic baseline:
- paid Hermes-path `10/10` baseline acceptance

### v1.1 to v1.4

Tested the bounded hybrid branch and several early bridge/ranking ideas:
- broader frozen comparison: baseline `31/70`, bounded hybrid `32/70`
- authoritative-eligibility bridge and hardening were locally useful
- a bounded retrieval-ranking borrow stayed locally green but regressed on the hard residual replay (`3/38 -> 2/38`)
- the ranking path was then explicitly rolled back and postmortemed

### v1.5 to v1.12

Switched to stricter diagnostics on the frozen hard residual set:
- the real hard replay truth was retrieval-dominant, not delivery-dominant
- later bounded work localized the main active family to upstream candidate-pool and query-shape misses
- selector tuning and broad delivery work were intentionally not reopened by inertia

### v1.13 to v1.14

Tried bounded upstream seeding and then a compromise legacy-primitive borrow:
- Phase 19 turned query-shape-conditioned candidate seeding into one bounded build
- a random paid hard gate stayed flat at `0/5`
- Phase 20 used a fixed representative hard ten plus narrow legacy query-signal borrow
- strong local proof, but the fixed external ten stayed `0/10`

### v1.15

Moved one layer deeper than heuristics:
- proved the fixed hard ten is not primarily blocked by source absence
- not primarily blocked by gross persist/index loss
- not primarily blocked by session-local unsearchability
- dominant seam moved downstream to post-recall answer surface / handoff

### v1.16

Localized the downstream seam more precisely on the same fixed ten:
- dominant miss was missing promptless authoritative bridge
- where a bridge existed, some payloads were still wrong
- result was forensic narrowing, not benchmark improvement

### v1.17

Applied one bounded downstream fix:
- expanded the authoritative surface/payload bridge narrowly
- improved the fixed paid hard ten from `0/10` to `1/10`
- still not enough for a strong claim
- current verified external status remains **needs work**

### Post-v1.17 cleanup pass

After the bounded v1.17 change, the live Core2 path was cleaned up further without reframing the benchmark result:
- repaired session-scoped recall handoff across plugin -> runtime -> hybrid substrate
- removed benchmark-coupled session lookup leakage from the live runtime path
- added an explicit `authoritative_payload` contract onto the recall packet so runtime, answer-surface, and plugin authoritative reply all share the same structured payload
- tightened the answer-surface bridge so it consumes cached payload instead of recomputing a parallel answer shape
- repaired the local `code-review-graph` workflow so untracked `agent/core2_*` files are indexed during full graph builds

This pass was done because review feedback correctly pointed out that several parts of Core2 were only half-wired: modules were relying on implicit contracts and ad hoc payload rebuilding instead of one shared producer-consumer path.

---

## What Seems To Work

From the current milestone history and local proof work, the project has solid or at least bounded evidence for:

- deterministic fact/state handling in covered cases
- provenance-aware memory objects
- fail-closed answer behavior and abstention contracts
- bounded hybrid retrieval and answer-surface seams
- explicit invariants and acceptance-style hardening
- a now-explicit authoritative payload contract in the live recall path
- session-scoped plugin/runtime/hybrid retrieval handoff instead of benchmark-shaped fallback keys
- useful forensic narrowing from phase-to-phase instead of silent scope drift

---

## Where It Is Still Blocked

The main unresolved issue is not “can it store facts?”

The hard part is that improvements in one internal seam do not reliably become better final answers on the frozen hard slices.

As of the latest mirrored state:
- the fixed paid hard ten improved only to `1/10`
- the dominant blocker is still **handoff / authoritative payload format**
- residual misses still include `retrieval_failure` and `sufficiency_failure`
- the latest cleanup pass improved local contract correctness and code hygiene, but did not claim a new external benchmark jump

In other words:
- several layers are now better understood
- some local improvements are real
- but the end-to-end benchmark bottleneck is still not solved

That is why the planning trail is included here. The negative results matter, and the bounded wins matter too.

---

## What Is In This Mirror

### Current core modules

Both the repo root and [`agent/`](./agent/) contain the current mirrored Core2 files, including:

- `core2_answer.py`
- `core2_answer_surface.py`
- `core2_authoritative.py`
- `core2_digestion.py`
- `core2_fact_registry.py`
- `core2_hybrid_substrate.py`
- `core2_invariants.py`
- `core2_longmemeval_benchmark.py`
- `core2_maintenance.py`
- `core2_noise_repair.py`
- `core2_policy.py`
- `core2_proof_harness.py`
- `core2_query_shape_seeding.py`
- `core2_query_signal_primitives.py`
- `core2_ranking.py`
- `core2_routing.py`
- `core2_runtime.py`
- `core2_store.py`
- `core2_types.py`

### Current Core2 tests

See [`tests/agent/`](./tests/agent/) for the mirrored `test_core2_*` suite and [`tests/`](./tests/) for the current benchmark-facing authoritative runner test coverage.

### GSD / planning artifacts

There are two planning mirrors here:

- [`gsd-review-pack/`](./gsd-review-pack/)  
  Curated review pack with mirrored core-state, milestone snapshots, phase artifacts, and selected references.

- [`.planning/`](./.planning/)  
  A fuller mirrored planning tree copied from the source project for people who want the raw state, milestone history, and exact phase artifacts.

---

## Suggested Reading Order

If you want the shortest path to understanding the current state, read this order:

1. [`gsd-review-pack/core-state/PROJECT.md`](./gsd-review-pack/core-state/PROJECT.md)
2. [`gsd-review-pack/core-state/STATE.md`](./gsd-review-pack/core-state/STATE.md)
3. [`gsd-review-pack/core-state/ROADMAP.md`](./gsd-review-pack/core-state/ROADMAP.md)
4. [`gsd-review-pack/core-state/REQUIREMENTS.md`](./gsd-review-pack/core-state/REQUIREMENTS.md)
5. [`gsd-review-pack/phase-21/21-VERIFICATION.md`](./gsd-review-pack/phase-21/21-VERIFICATION.md)
6. [`gsd-review-pack/phase-22/22-VERIFICATION.md`](./gsd-review-pack/phase-22/22-VERIFICATION.md)
7. [`gsd-review-pack/phase-23/23-VERDICT.md`](./gsd-review-pack/phase-23/23-VERDICT.md)
8. [`agent/core2_runtime.py`](./agent/core2_runtime.py)
9. [`agent/core2_authoritative.py`](./agent/core2_authoritative.py)
10. [`agent/core2_longmemeval_benchmark.py`](./agent/core2_longmemeval_benchmark.py)

If you want the shortest summary:

- the deterministic baseline exists
- bounded hybridization gave only small gains
- several plausible retrieval-side ideas were falsified or narrowed
- the current hard slice is mostly blocked downstream at authoritative handoff/payload
- the latest bounded downstream fix improved the fixed hard ten only from `0/10` to `1/10`
- the current code mirror also includes a follow-up cleanup pass that reduced live benchmark leakage and replaced some half-wired payload rebuilding with one explicit packet contract

---

## What Feedback Is Most Useful

The most useful review is not “nice idea.”

The useful feedback is:

- do the deterministic boundaries make sense?
- is the provenance / temporal / answer-surface model coherent?
- does the planning trail show good experimental discipline?
- is the current handoff/payload diagnosis the right bottleneck?
- are the benchmark gates honest enough for external review?

Especially valuable:
- criticism of the current bottleneck diagnosis
- places where the deterministic core is too large or too small
- places where the project is confusing local proof with end-to-end proof
- better ideas for authoritative payload shaping or handoff contracts

---

## Current Status

As mirrored here:

- current planning mirror: **v1.17 / Phase 23**
- current code mirror: **v1.17 plus post-v1.17 cleanup pass**
- planning status in the mirrored GSD tree: **execute complete, ready for verify**
- latest fixed paid hard-ten result: **`1/10`**
- dominant blocker: **handoff-format / authoritative payload**
- latest local cleanup pass:
  - explicit `authoritative_payload` on `Core2RecallPacket`
  - session-scoped recall forwarding through plugin/runtime/hybrid substrate
  - graph tooling fixed to index untracked Core2 files during full builds

This is therefore a **current review checkpoint** with the latest benchmark-facing truth, not a polished release snapshot.

---

## Reviewer Note: Concrete Experiment Details

For reviewers who want actual benchmark-facing details rather than only architecture prose:

### What We Actually Evaluate

The project is not treating this as a raw retrieval benchmark.

The benchmark-facing path goes through the full Core2 / Hermes runtime flow:

1. write-time digestion turns raw interactions into memory objects
2. query routing chooses a route family
3. retrieval gathers bounded evidence
4. answer-surface / authoritative logic tries to produce a grounded answer
5. the final response is judged against the benchmark answer

So the thing being tested is closer to:

**memory kernel + retrieval + answer-surface / handoff path**

not just “did search find a relevant string?”

### Main Evaluation Stages So Far

#### 1. Broader baseline vs bounded hybrid comparison

Frozen broader set:
- `70` questions

Result:
- baseline: `31/70`
- bounded hybrid: `32/70`

Interpretation:
- hybrid looked directionally better
- but not by enough to count as a decisive promotion win

#### 2. Hard residual replay

After that, the project focused on a hard residual set of `38` previously failing questions.

That set became the main “does this actually move the hard failures?” check.

Important reference points on that **separate hard residual replay**:
- after bounded hardening (`v1.2` reference state): `3/38`
- after bounded retrieval-ranking borrow (`v1.3` branch state): `2/38`

So the ranking result was **not** “the whole hybrid regressed.”
It means:
- on the broader frozen comparison, hybrid was still slightly better (`32/70` vs `31/70`)
- but on the hard residual `38` replay, the ranking-borrow variant underperformed the earlier `3/38` reference and landed at `2/38`

That is why the ranking path was rolled back in `v1.4`.

### Sample Questions From The Data

Representative examples from the benchmark dataset:

1. `multi-session`
   - “How much will I save by taking the train from the airport to my hotel instead of a taxi?”
   - expected answer: `$50`

2. `single-session-assistant`
   - “I'm planning to visit the Vatican again and I was wondering if you could remind me of the name of that famous deli near the Vatican that serves the best cured meats and cheeses?”
   - expected answer: `Roscioli`

3. `single-session-preference`
   - “I've got some free time tonight, any documentary recommendations?”
   - expected behavior: use prior viewing preferences, not generic recommendation text

4. `temporal-reasoning`
   - “How many weeks ago did I meet up with my aunt and receive the crystal chandelier?”
   - expected answer: `4`

5. `multi-session`
   - “What is the total number of episodes I've listened to from 'How I Built This' and 'My Favorite Murder'?”
   - expected answer: `27`

6. `multi-session`
   - “How many different museums or galleries did I visit in the month of February?”
   - expected answer: `2`

These examples are useful because they show the spread of the problem:
- scalar facts
- temporal reasoning
- preference-conditioned answers
- multi-session aggregation
- entity recall

### What The Failure Taxonomy Looks Like

The project does not treat every miss as “the kernel is bad.”

The failure buckets are separated roughly like this:

- `prompt_miss`
  - the final prompt/delivery path did not use the available memory well enough
- `handoff_format_miss`
  - the answer path was structurally close, but the delivery shape still failed the benchmark/judge
- `judge_artifact`
  - the remaining miss looks more like evaluation/judge behavior than a true kernel miss

The most important current fact is this:

the hard residual set is still dominated by **`prompt_miss`**, not by retrieval-ranking problems.

That is why the current carry-forward direction is **Covered-Family Prompt Delivery Bridge**, not another retrieval experiment.

### Why The Ranking Rollback Matters

The ranking borrow was not removed because it was ugly or because the code was broken.

It was removed because:
- it was locally green
- it was architecturally plausible
- and it still regressed the hard residual replay

That is an important part of the evaluation philosophy here:

**local proof is necessary, but broader hard-residual evidence wins**

---

*Primary development remains in the main Hermes fork. This repository is a public review mirror of the current Core2 kernel state and its associated planning/verification history.*
