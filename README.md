# Hemu — Core2 Memory Kernel Review Mirror

> Public review mirror of the current Core2 memory-kernel branch.  
> Not a release build, not a standalone product, and not the main development repo.

This repository is a curated mirror of the **Hemu / Hermes Core2** memory-kernel work: the current core modules, the related Core2 tests, and the GSD planning / verification trail that explains what was built, what worked, what failed, and why.

The point of this repo is **reviewability**, not polish. It is here so someone can inspect:
- the current core files
- the milestone / phase history
- the benchmark-facing decisions
- the architectural dead ends that were explicitly rolled back

No secrets or API keys are included here.

---

## What Core2 Is

Core2 is a **deterministic memory kernel** for durable facts and temporal state inside an agent runtime.

The main design goal is not “better retrieval” in isolation. The goal is:
- stable memory objects
- provenance and source traceability
- current / previous / superseded state
- conflict handling
- fail-closed answer behavior
- explicit abstention when support is insufficient

The intended user experience is that the system remembers in the background and keeps itself consistent, instead of re-reasoning from raw history every time.

---

## What The Project Learned So Far

The development history matters here because the repo is not just a code dump; it is a trail of hypotheses that were tried and measured.

### v1.0

Established the shipped baseline:
- deterministic kernel path
- paid Hermes-path `10/10` baseline acceptance

### v1.1

Tested the bounded hybrid branch against the baseline on a broader frozen set:
- baseline: `31/70`
- hybrid: `32/70`
- verdict: directionally better, but not enough for automatic promotion

### v1.2

Tried the next bounded breakthrough ideas:
- authoritative eligibility bridge
- invariants / acceptance harness
- narrow noise repair

Result:
- useful hardening
- no decisive breakthrough on the hard residual failures

### v1.3

Tried a bounded retrieval-ranking borrow inside the hybrid seam.

Locally:
- green

On the separate hard residual replay:
- the ranking-borrow branch scored `2/38` against an earlier `3/38` reference point

### v1.4

Rolled the failed ranking path back out of the active hybrid route and wrote the postmortem instead of pretending the experiment was still promising.

Current carry-forward recommendation:
- **Covered-Family Prompt Delivery Bridge**

There is currently **no active milestone** in the mirrored planning state.

---

## What Seems To Work

From the current milestone history and local proof work, the project has reasonably solid evidence for:

- deterministic fact/state handling in covered cases
- provenance-aware memory objects
- supersession / conflict-aware state transitions
- fail-closed answer behavior and abstention contracts
- bounded hybrid retrieval seam
- explicit invariants and acceptance-style hardening

---

## Where It Is Still Blocked

The main unresolved issue is not “can it store facts at all?”

The harder problem is this:

- improvements in retrieval or internal structure do not reliably become better final answers
- the remaining hard failures are still dominated by **prompt-path / delivery-path misses**
- some ideas are locally correct and still not globally decisive

In other words: the project has already learned several things that are **not** the breakthrough.

That is why the planning trail is included here. The negative results matter.

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
- `core2_ranking.py`
- `core2_routing.py`
- `core2_runtime.py`
- `core2_store.py`
- `core2_types.py`

### Current Core2 tests

See [`tests/agent/`](./tests/agent/) for the mirrored `test_core2_*` suite.

### GSD / planning artifacts

There are two planning mirrors here:

- [`gsd-review-pack/`](./gsd-review-pack/)  
  Curated public review pack with mirrored core-state, phase snapshots, references, and milestone archives.

- [`.planning/`](./.planning/)  
  A fuller mirrored planning tree copied from the source project for people who want the raw state and milestone history.

---

## Suggested Reading Order

If you want the shortest path to understanding the current state, read this order:

1. [`gsd-review-pack/core-state/PROJECT.md`](./gsd-review-pack/core-state/PROJECT.md)
2. [`gsd-review-pack/core-state/STATE.md`](./gsd-review-pack/core-state/STATE.md)
3. [`gsd-review-pack/references/CORE2-AXIOMS.md`](./gsd-review-pack/references/CORE2-AXIOMS.md)
4. [`gsd-review-pack/phase-06/06-VERIFICATION.md`](./gsd-review-pack/phase-06/06-VERIFICATION.md)
5. [`gsd-review-pack/phase-09/09-VERIFICATION.md`](./gsd-review-pack/phase-09/09-VERIFICATION.md)
6. [`gsd-review-pack/phase-10/10-POSTMORTEM.md`](./gsd-review-pack/phase-10/10-POSTMORTEM.md)
7. [`agent/core2_runtime.py`](./agent/core2_runtime.py)
8. [`agent/core2_authoritative.py`](./agent/core2_authoritative.py)
9. [`agent/core2_store.py`](./agent/core2_store.py)

If you want the shortest summary:

- baseline exists
- hybrid helped a bit
- several plausible ideas were tried
- ranking was falsified and rolled back
- the likely remaining leverage is in prompt/delivery-path use of already-covered memory

---

## What Feedback Is Most Useful

The most useful review is not “cool idea” or “graphs are nice”.

The useful feedback is:

- do the deterministic boundaries make sense?
- is the provenance / temporal / supersession model coherent?
- does the planning trail show good experimental discipline, or just benchmark-chasing?
- is the current carry-forward direction plausible, or is the real bottleneck somewhere else?

Especially valuable:
- criticism of the current bottleneck diagnosis
- places where the deterministic core is too large or too small
- places where the project is confusing local proof with end-to-end proof

---

## Current Status

As mirrored here:

- latest completed milestone: **v1.4 Ranking Rollback And Postmortem**
- active milestone: **none**
- current carry-forward recommendation: **Covered-Family Prompt Delivery Bridge**

This is therefore a **review checkpoint**, not a celebration repo.

---

## Reviewer Note: Concrete Experiment Details

_For Nathan and any reviewer who wants actual dataset samples plus evaluation details rather than only architecture prose._

This section is mainly for reviewers who want actual sample questions and a more concrete explanation of how the evaluation was run.

### What We Actually Evaluate

The important point is that the project is **not** treating this as a raw retrieval benchmark.

The main benchmark-facing path goes through the full Core2 / Hermes runtime flow:

1. write-time digestion turns raw interactions into memory objects
2. query routing chooses a route family
3. retrieval gathers bounded evidence
4. the kernel either produces a structured/authoritative answer path or falls back
5. a judge model checks the final answer against the benchmark answer

So the thing being tested is closer to:

**memory kernel + retrieval + answer delivery path**

not just “did BM25 or embeddings find something relevant?”

### Main Evaluation Stages So Far

#### 1. Broader baseline vs hybrid comparison

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
