# Legacy Kernel Codemap

Scope: `/home/lauratom/Asztal/ai/hermes-agent-port/agent/kernel_memory*`

Purpose: identify which old Hermes kernel memory ideas are worth adapting into Core2, and which parts should remain behind because they created complexity collapse.

## High-Level Shape

The old kernel was not one subsystem but a stack of many semi-independent layers:

1. Store and record base
- `kernel_memory.py`
- `kernel_memory_store.py`
- `kernel_memory_store_*`
- `kernel_memory_records.py`
- `kernel_memory_ids.py`
- `kernel_memory_provenance.py`
- `kernel_memory_temporal.py`

2. Retrieval and routing
- `kernel_memory_retrieval.py`
- `kernel_memory_retrieval_router.py`
- `kernel_memory_query_*`
- `kernel_memory_route_priority.py`
- `kernel_memory_retrieval_cache.py`

3. Semantic and objective layer
- `kernel_memory_semantic_contract.py`
- `kernel_memory_semantic_*`
- `kernel_memory_objective_*`
- `kernel_memory_source_intent.py`
- `kernel_memory_applicability.py`

4. Canonicalization and truth maintenance
- `kernel_memory_canonicalization.py`
- `kernel_memory_merge_policy.py`
- `kernel_memory_conflicts.py`
- `kernel_memory_conflict_policy.py`
- `kernel_memory_current_state_priority.py`
- `kernel_memory_contradiction_priority.py`
- `kernel_memory_provisional_policy.py`

5. Graph and relations
- `kernel_memory_relations.py`
- `kernel_memory_graph_*`
- `kernel_memory_entity_resolution.py`
- `kernel_memory_fusion.py`
- `kernel_memory_correction_linker.py`

6. Answer and quality layer
- `kernel_memory_answer_packet.py`
- `kernel_memory_answer_synthesis.py`
- `kernel_memory_evidence_chain.py`
- `kernel_memory_evidence_quality.py`
- `kernel_memory_quality.py`
- `kernel_memory_quality_contract.py`
- `kernel_memory_memory_objects.py`

7. Maintenance and admin
- `kernel_memory_activation_maintenance.py`
- `kernel_memory_curated_maintenance.py`
- `kernel_memory_recompile.py`
- `kernel_memory_revisit.py`
- `kernel_memory_prewarm.py`
- `kernel_memory_scale_triggers.py`
- `kernel_memory_admin.py`
- `kernel_memory_backup.py`
- `kernel_memory_nightly_*`

## What Was High Value

These patterns are still worth keeping in Core2 form:

1. Compact answer packet
- Old anchor: `kernel_memory_answer_packet.py`
- Why it mattered: it separated retrieval result from final answer shape and made abstention/support/confidence explicit.
- Core2 adaptation:
  - `agent/core2_answer.py`
  - `agent/core2_types.py`

2. Direct resolved-answer fast path
- Old anchor: `kernel_memory_runtime.py`
- Why it mattered: when memory had a strong final/supported answer, it avoided unnecessary extra generation.
- Core2 adaptation:
  - `agent/core2_authoritative.py`
  - `plugins/memory/core2/__init__.py`
  - `agent/memory_manager.py`
  - `run_agent.py`

3. Bounded compare/timeline routing
- Old anchors:
  - `kernel_memory_retrieval_router.py`
  - `kernel_memory_semantic_contract.py`
  - `kernel_memory_objective_executor.py`
- Why it mattered: compare and temporal questions need tighter routing than general exploratory recall.
- Core2 adaptation:
  - `agent/core2_routing.py`
  - `agent/core2_runtime.py`

4. Explicit abstention and support discipline
- Old anchors:
  - `kernel_memory_answer_packet.py`
  - `kernel_memory_memory_objects.py`
- Why it mattered: the system could say “supported”, “cautious”, or abstain instead of pretending certainty.
- Core2 adaptation:
  - `agent/core2_answer.py`
  - `agent/core2_types.py`

## What Caused Collapse

These parts appear to have been major complexity multipliers:

1. Semantic-contract explosion
- Files:
  - `kernel_memory_semantic_contract.py`
  - `kernel_memory_semantic_domains.py`
  - `kernel_memory_semantic_lexicon.py`
  - `kernel_memory_semantic_policy.py`
- Risk:
  - too much meaning analysis before retrieval
  - too many hidden interactions
  - hard to predict behavior changes

2. Objective execution layer spread across many files
- Files:
  - `kernel_memory_objective_executor.py`
  - `kernel_memory_objective_expansion.py`
  - `kernel_memory_objective_priority.py`
  - `kernel_memory_objective_units.py`
- Risk:
  - overfit planner-on-planner behavior
  - high coupling to query interpretation and answer assembly

3. Large admin runtime
- File:
  - `kernel_memory_admin.py`
- Evidence:
  - imports many maintenance, graph, quality, retrieval, cache, benchmark, task, and recompile services
- Risk:
  - central god-object
  - too many cross-cutting dependencies

4. Full graph/quality/benchmark stack inside the kernel
- Files:
  - `kernel_memory_graph_*`
  - `kernel_memory_quality*`
  - `kernel_memory_nightly_*`
- Risk:
  - the kernel stopped being a narrow runtime and became a platform

## Core2 Decision

Core2 should stay narrower than the old kernel:

1. Keep
- plane-aware store
- bounded routing
- explicit support/confidence/abstention
- direct-answer fast path for narrow safe cases

2. Avoid
- giant semantic-contract layer
- multi-file objective engine
- admin super-runtime
- benchmark/quality platform logic embedded into core runtime

## Current Mapping

Safe old ideas already adapted into Core2:

1. Answer packet discipline
- `agent/core2_answer.py`
- `agent/core2_types.py`

2. Bounded compare/temporal routing
- `agent/core2_routing.py`
- `agent/core2_runtime.py`

3. Direct grounded answer short-circuit
- `agent/core2_authoritative.py`
- `plugins/memory/core2/__init__.py`
- `agent/memory_manager.py`
- `run_agent.py`

## Recommendation

Use this rule when borrowing from the old kernel:

- borrow patterns, not subsystems
- prefer one narrow adaptation in Core2 over importing an old multi-file layer
- if a legacy idea needs more than 2-3 new Core2 modules to fit, it is probably not a net win
