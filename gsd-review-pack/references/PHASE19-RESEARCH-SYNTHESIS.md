# Phase 19 Research Synthesis

## Purpose

This file ingests externally gathered research blocks before they are promoted into GSD planning.

It exists to keep:

- raw external study takeaways
- current leverage for Core2
- freshness bias
- strict usefulness scoring

separate from official phase truth until the research is synthesized.

---

## Block 01 — Evidence Selection / Decomposition / Sufficiency / Temporal Anchoring

### Input Summary

This block covered five research questions:

1. budgeted evidence-set selection in compositional QA
2. operator and operand-slot recognition
3. query rewriting / candidate seeding when the full query fails
4. retrieval sufficiency rather than mere relevance
5. temporal anchoring for before/after/elapsed questions

### Freshest High-Signal Studies

Prefer these first when weighting the block:

- `RTQA` (Gong et al., 2025)
- `Gu & Hopkins` selective prediction survey (2023)
- `Hybrid Hierarchical Retrieval` (Arivazhagan et al., 2023)
- `SF-TQA` (Ding et al., 2022)
- `DPP multi-answer retrieval` (Nandigam et al., 2022)

Use these as foundational rather than fresh:

- `HotpotQA` (Yang et al., 2018)
- `Allen interval algebra`
- `TimeML`

### Strongest Reusable Takeaways

#### 1. Budgeted evidence-set selection is real, but not a full drop-in recipe

The strongest formalism is:

- budgeted maximum coverage
- monotone submodular maximization under a budget
- diversity-aware reranking via `MMR`, `xQuAD`, or `DPP`

This gives real mathematical backing for:

- selecting evidence as a set
- modeling slot/support/temporal/provenance coverage
- using greedy marginal gain per cost

But this block does **not** provide one universally accepted end-to-end recipe for:

- token-budgeted sufficient evidence selection for open-text memory QA

#### 2. Question decomposition plus operator/slot schema is probably upstream-critical

The strongest pattern across the block is:

- decompose the question
- detect operator
- infer arity and slots
- retrieve slot-specific evidence

This is highly relevant to the current Core2 wall because the hard `38` still fails before selector engagement on most cases.

#### 3. Query rewriting / candidate seeding is a real literature-backed direction

This block strongly supports:

- clause decomposition
- anchor extraction
- sub-question generation
- staged retrieval around those seeds

This is the most directly relevant research support for the current `Phase 19` seam.

#### 4. Retrieval sufficiency is not solved by one canonical metric

Best practice emerging from the block:

- support-fact coverage
- slot coverage
- operator executability
- temporal completeness
- abstention when sufficiency is not met

This means we should not search for one magic benchmark number.

#### 5. Temporal reasoning has a strong formal backbone

The best formal core is:

- Allen-style interval relations
- TimeML-style event/time separation
- modern temporal QA decomposition on top

This is important because many residual misses are temporal or comparison-shaped.

### Most Relevant To Current Core2 Bottleneck

For the current live wall, the highest-leverage parts of this block are:

1. `question decomposition + operator/slot schema`
2. `query rewriting / candidate seeding`
3. `temporal anchoring primitives`
4. `retrieval sufficiency as support/slot/executability, not relevance`

The least immediately novel part for current work is:

5. `budgeted selector math`

Reason:

- Core2 already imported part of the selector/safety line
- the canonical hard `38` showed `selector_engaged_cases = 0`
- so the immediate missing seam is earlier than selector choice

### What This Block Does NOT Yet Solve

This block does **not** give us:

- a drop-in open-text operator classifier
- a drop-in universal retrieval sufficiency metric
- a drop-in clause-level seeding algorithm for our exact residual bucket
- a full end-to-end SOTA recipe

### Phase 19 Impact

This block strengthens `Phase 19`, but does not automatically finish it.

What it justifies:

- keeping `Phase 19` focused on upstream seed opening
- making operator/slot/schema explicit
- allowing clause-level rewrites and temporal anchor seeds
- judging engagement by sufficiency-style movement, not pretty local traces

What it does **not** justify:

- broad staged retrieval rewrite
- delivery reopen
- ranking reopen
- claiming the problem is solved

### Strict Usefulness Score

`6.5/10`

Why not higher:

- it does not solve the problem end-to-end
- it does not contain a full drop-in algorithm for our exact bottleneck
- it still requires system design choices and adaptation

Why not lower:

- it sharply reduces the search space
- it gives real mathematical and QA structure
- it strongly supports the current upstream seam diagnosis
- it provides a practical bridge from theory to implementable spec

### Provisional Verdict

This is a **strong research block**, but not a silver bullet.

Best interpretation:

- not “this solved Core2”
- but “this finally gives a serious formal backbone for the right class of next experiments”

---

## Block 02 — State Semantics / Temporal Windows / Truth Discovery

### Input Summary

This block covered three research questions:

1. strongest formal model for `current / previous / superseded / conflicting`
2. modeling temporal validity windows and derived states
3. truth discovery / source trust weighting under conflicting sources or repeated mentions

### Freshness Verdict

This area did **not** improve mainly by finding fresher papers.

The strongest reusable cores are still mostly:

- older foundational temporal / state formalisms
- older but still strong truth-discovery algorithms

So the right interpretation is:

- freshness is not the main win here
- formal reusability is the main win here

### Strongest Reusable Takeaways

#### 1. Bitemporal fact model plus explicit supersession/conflict graph is the strongest state core

The block provides a near-buildable state semantics core:

- bitemporal fact rows
- explicit `supersedes` / `conflicts_with` edges
- derived `current` / `previous` / `superseded` / `conflicting` states

This is much closer to a reusable kernel primitive than the first research block.

#### 2. TMS / ATMS is a strong support/justification layer, but not the whole temporal state model

This is a useful complement for:

- provenance
- derivation tracing
- invalidation
- explainability

But it should not replace the temporal model itself.

#### 3. CATD / Bayesian truth-discovery families are plausible trust-weighting cores

This block gives real algorithmic candidates for:

- source trust weighting
- claim aggregation
- support scoring

CATD looks especially practical for single-truth relations.

### Comparison Against Block 01

#### Where Block 02 is better

- more drop-in
- more schema-level
- more rule-level
- more buildable tomorrow

#### Where Block 02 is worse for the current live wall

- less directly aimed at the current hard-`38` retrieval bottleneck
- less helpful for `Phase 19` upstream seed-opening than Block 01

So the improvement is **real**, but on a different axis:

- Block 01 was better for the **current retrieval wall**
- Block 02 is better for the **durable kernel semantics**

### Most Relevant To Current Core2 Bottleneck

Immediate `Phase 19` leverage:

- low to medium

Longer-horizon Core2 leverage:

- high

Reason:

- current live failure is still mostly upstream retrieval failure before selector engagement
- this block does not solve that directly
- but it gives a much stronger foundation for future state semantics and source-trust logic

### What This Block Does NOT Yet Solve

This block does **not** give us:

- a retrieval fix for the hard `38`
- a direct answer-bearing candidate opening mechanism
- a guaranteed near-term benchmark jump

### Strict Usefulness Score

`7/10`

Why this is an improvement over Block 01:

- stronger formal artifacts
- more reusable schema and derivation rules
- more directly buildable state/trust core

Why it is still not higher:

- it does not solve the current live bottleneck
- it does not provide a retrieval breakthrough
- the strongest parts are mostly foundational rather than new

### Provisional Verdict

This block is a **better reusable core block** than Block 01, but not a better **immediate Phase 19 block**.

Best interpretation:

- yes, there was real improvement
- but the improvement is in buildable kernel semantics, not in current hard-residual breakthrough power

---

## Block 03 — Aggregation Safety / Dedupe / Compatibility / Abstention

### Input Summary

This block covered three research areas:

1. double counting / dedupe / partial-evidence aggregation failures
2. unit / scope / time compatibility before aggregation
3. principled abstention under incomplete evidence

### Freshness Verdict

Again, the strongest cores here are mostly older but still strong foundations:

- record linkage
- OLAP summarizability
- incomplete-data / certain-answers semantics

So, like Block 02:

- freshness is not the main win
- formal and operational reusability is the win

### Strongest Reusable Takeaways

#### 1. Record linkage gives a real dedupe core

The strongest reusable choices are:

- Fellegi–Sunter-style probabilistic linkage
- Bayesian bipartite matching when stricter one-to-one linkage is needed

This is highly relevant for:

- event dedupe
- fact dedupe
- duplicate suppression before count/sum

#### 2. Summarizability is the strongest “do not aggregate wrongly” formal backbone

This is the clearest reusable core in the block:

- strictness / disjointness
- completeness
- homogeneity / compatibility

This provides an explicit policy language for when aggregation is valid at all.

#### 3. Unit / scope / time compatibility should be treated as a composite gate

This block strongly supports a rule system of the form:

- unit compatibility
- scope / grain compatibility
- time-window compatibility

rather than searching for one magical paper that solves all three together.

#### 4. Certain-answers / range semantics is the strongest abstention formalism

This is arguably the sharpest formal stop condition found so far for aggregation:

- if lower bound equals upper bound, exact answer is safe
- otherwise abstain or return an interval

This is extremely strong as a principled safety core.

### Comparison Against Earlier Blocks

#### Where Block 03 is better

- more operational than Block 01
- more directly runtime-enforceable than Block 02
- clearer stop conditions
- stronger aggregation-safety core than anything seen earlier

#### Where Block 03 is worse for the current live wall

- like Block 02, it does not directly solve the current upstream retrieval-opening bottleneck
- the paid hard replay already showed `aggregation_safety_abstentions = 0`, so this is not the seam currently dominating the hard `38`

### Most Relevant To Current Core2 Bottleneck

Immediate `Phase 19` leverage:

- low

Longer-horizon kernel leverage:

- very high

Reason:

- current live failure is still upstream retrieval failure before selector engagement
- this block mainly strengthens safe execution after evidence has already been found

### What This Block Does NOT Yet Solve

This block does **not** give us:

- a retrieval-opening fix
- a direct answer-bearing candidate seeding mechanism
- a near-term hard-`38` breakthrough by itself

### Strict Usefulness Score

`7.5/10`

Why this is stronger than Blocks 01 and 02:

- most complete reusable subsystem core so far
- strongest formal stop condition so far
- clearer runtime policy implications

Why it is still not higher:

- it does not resolve the current active bottleneck
- it is subsystem-level, not full-system
- it still needs system integration and relation-policy design

### Provisional Verdict

This is probably the **strongest research block so far as a reusable subsystem core**.

Best interpretation:

- not “this solves Core2 now”
- but “this gives a very serious aggregation-safety kernel we can build later with unusually little conceptual ambiguity”

---

## Block 04 — Calibrated Abstention / Override Gate / Support-Fact Evaluation

### Input Summary

This block covered four research areas:

1. calibrated selective prediction / abstention in NLP
2. when a heuristic path may enter or override a deterministic path
3. pipeline error attribution across retrieval / sufficiency / reasoning / judge-like failures
4. support-fact-based diagnostic benchmarking instead of pure pass/fail

### Freshness Verdict

This block is fresher than Blocks 02 and 03.

Fresh high-signal items here include:

- `Gu & Hopkins` selective prediction survey (2023)
- `ARES` (2024)
- `RAGAs` (2024)
- `CKGC` as supporting calibration evidence (2024)

Foundational but older items still matter:

- `Guo et al.` temperature scaling (2017)
- `HotpotQA` (2018)
- `FEVER` (2018)

### Strongest Reusable Takeaways

#### 1. Selective prediction gives a clean abstention formalism

This is the sharpest reusable formalism in the block:

- explicit answer vs abstain decision
- risk–coverage evaluation
- thresholdable selection function

This is highly reusable for:

- authoritative answer gating
- abstain-by-default policies
- risk-tiered answer release

#### 2. Temperature scaling makes thresholding materially more trustworthy

This is not a full decision policy by itself, but it is a very practical core:

- simple
- proven
- easy to reuse where raw confidence exists

#### 3. Hybrid override gating still lacks one dominant drop-in paper

The strongest result here is still a synthesis:

- calibrated correctness
- agreement/conflict checks
- provenance/grounding floor
- risk-specific threshold
- abstain-by-default

So this block helps a lot, but not by yielding one fully pre-packaged override algorithm.

#### 4. Support-fact-conditioned evaluation is the strongest benchmarking takeaway

This is the clearest way to avoid opaque pass/fail evaluation:

- support-fact recall / precision
- evidence-conditioned answer accuracy
- judge false-positive / false-negative tracking

This is especially strong because it matches our existing attribution direction.

### Comparison Against Earlier Blocks

#### Where Block 04 is better

- fresher than Blocks 02 and 03
- strongest evaluation/gating block so far
- strongest benchmarking-diagnostics block so far
- partially validates the direction already taken in the attribution work

#### Where Block 04 is weaker for the current live wall

- like Blocks 02 and 03, it does not directly solve the current upstream retrieval-opening bottleneck
- part of its value is confirmatory because Core2 already imported a bounded attribution dashboard

### Most Relevant To Current Core2 Bottleneck

Immediate `Phase 19` leverage:

- low to medium

Longer-horizon kernel leverage:

- high

Reason:

- it greatly improves how safely and clearly we decide, abstain, and evaluate
- but it does not directly make answer-bearing candidates appear in the hard retrieval-failure bucket

### What This Block Does NOT Yet Solve

This block does **not** give us:

- a direct retrieval breakthrough
- a full drop-in override policy for our exact hybrid seam
- a unified benchmark standard that simultaneously solves support facts, operand slots, sufficiency, and judge artifacts

### Strict Usefulness Score

`7.5/10`

Why this is strong:

- freshest of the strong non-retrieval blocks
- strong formal core for abstention and evaluation
- closest thing so far to a rigorous benchmark/gating subsystem

Why it is still not higher:

- it does not solve the current dominant bottleneck
- the override gate still requires synthesis rather than direct adoption
- some value is confirmatory rather than newly unlocking

### Provisional Verdict

This is the **strongest evaluation/gating research block so far**.

Best interpretation:

- not “this solves the kernel”
- but “this gives a serious formal backbone for when to answer, when to abstain, and how to diagnose failures cleanly”
