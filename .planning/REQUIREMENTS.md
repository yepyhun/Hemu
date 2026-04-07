# Requirements: Hermes Core2 Memory Kernel

**Defined:** 2026-04-06
**Core Value:** If everything else degrades, Core2 must still return source-grounded, correctly scoped memory under explicit abstention and confidence rules instead of bluffing.

## v1 Requirements

### Provider Foundation

- [x] **PROV-01**: Hermes can load a Core2 memory provider through the existing provider discovery and activation path.
- [x] **PROV-02**: Core2 integrates through thin wiring in native Hermes runtime files and keeps kernel logic isolated in dedicated modules.
- [x] **PROV-03**: Core2 respects existing provider lifecycle hooks including initialization, per-turn processing, pre-compress extraction, delegation observation, and shutdown.

### Memory Model

- [x] **MODEL-01**: Core2 persists and manages the `raw_archive` plane for raw observations and source artifacts.
- [x] **MODEL-02**: Core2 maintains a `canonical_truth` plane for source-grounded stable facts with provenance.
- [x] **MODEL-03**: Core2 maintains a `derived_propositions` plane for derived claims separated from canonical truth.
- [x] **MODEL-04**: Core2 maintains `retrieval_indices` and `delivery_views` as distinct operational planes instead of collapsing storage and delivery concerns.

### Write-Time Digestion

- [x] **FACT-01**: Core2 digests durable remember inputs and turn-ingested conversations into typed, compact fact records during write-time or background processing rather than leaving common truth extraction to query-time raw blob parsing.
- [x] **FACT-02**: Core2 resolves current vs previous/update semantics for covered fact types during digestion while preserving provenance and explicit supersession history.
- [x] **FACT-03**: Core2 materializes compact delivery-ready or retrieval-ready fact artifacts from the digested canonical layer so later recall can prefer those structures over raw blobs for common durable-memory queries.
- [x] **FACT-04**: Core2 models stable preferences, habits, and routines as typed durable-memory facts with positive/negative guidance and bounded temporal qualifiers instead of relying on generic query-time suggestion behavior.
- [x] **FACT-05**: Core2 models aggregate and count-style durable-memory answers through structured summary or membership artifacts so common totals and distinct counts do not depend on raw-history rescans or ad hoc heuristics.
- [x] **FACT-06**: Core2 models bounded temporal-summary and event-anchor facts so common elapsed-time and before/after durable-memory questions do not require rebuilding timeline meaning from raw session text each time.

### Scope And Trust

- [x] **SCOPE-01**: Core2 enforces namespace classes including personal/second-brain, workspace/project, library/books, and high-risk domains.
- [x] **SCOPE-02**: Core2 enforces trust classes and prevents unsafe mixing of claims across trust boundaries.
- [x] **SCOPE-03**: Core2 applies explicit admission, promotion, rejection, demotion, and forgetting rules to memory state transitions.

### Retrieval And Answers

- [x] **RETR-01**: Core2 supports routing across query families such as exact lookup, factual supported recall, personal recall, relation multihop, update resolution, and exploratory discovery.
- [x] **RETR-02**: Core2 supports answer modes including exact-source-required, source-supported, and compact-memory behavior with abstention when support is insufficient.
- [x] **RETR-03**: Core2 returns typed answers with support tiers, confidence dimensions, and explicit provenance metadata.
- [x] **RETR-04**: Core2 enforces token-budget rules and retrieval caps appropriate to answer mode.
- [x] **RETR-05**: For covered durable-memory query families, Core2 prefers the write-time digested fact substrate and compact fact artifacts before broader canonical/raw-style retrieval.
- [x] **RETR-06**: When fact-first retrieval is insufficient, Core2 falls back to broader canonical retrieval without weakening provenance, abstention, or current/previous resolution discipline.
- [x] **RETR-07**: For covered durable-memory families, Core2 emits a deterministic provider-owned answer surface with explicit family classification, structured answer content, and inspectable provenance/support metadata instead of handing the final path a loose recall blob.
- [x] **RETR-08**: Hermes consumes the Core2 answer surface as the preferred first-pass handoff for covered durable-memory answers, while keeping explicit fallback when the provider surface is absent or insufficient.

### Temporal And Versioning

- [x] **TIME-01**: Core2 stores mandatory temporal metadata for memory records and supports query-time temporal semantics.
- [x] **TIME-02**: Core2 handles versioning/update-resolution without silently overwriting conflicting history.
- [x] **TIME-03**: Core2 applies stricter temporal behavior in high-risk namespaces.

### Verification And Proof

- [x] **QUAL-01**: Core2 includes automated tests for provider lifecycle behavior, memory state transitions, and retrieval contracts.
- [x] **QUAL-02**: Core2 can be exercised end to end through the Hermes runtime for local proof, scaling proof, latency proof, and token proof checkpoints.
- [x] **QUAL-03**: Core2 benchmark/eval flows avoid raw model-only shortcuts and measure the real Hermes-integrated path.
- [ ] **QUAL-04**: Core2 turns failed live-gate behavior into replayable correctness evidence, fixes the discovered gaps, and can then complete a staged paid LongMemEval gate with an explicit release decision based on the full Hermes-integrated path.
- [x] **QUAL-05**: Core2 records machine-readable live-gate status that classifies remaining failures into stable blocker families such as kernel correctness, handoff/format, and latency so the final rerun is guided by explicit evidence rather than ambiguous summaries.

## v2 Requirements

### Future Expansion

- **FUT-01**: Support additional proposition-layer sophistication beyond the minimal claim layer when v1 invariants are stable.
- **FUT-02**: Extend multilingual canonicalization and duplicate handling beyond the initial v1 implementation envelope.
- **FUT-03**: Consider broader multi-provider or hybrid-provider topologies only after single-provider Core2 is stable.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Full Hermes runtime redesign | The project goal is a modular kernel integrated into existing Hermes boundaries |
| Model-only benchmark harness disconnected from Hermes | Would not prove the real kernel behavior the user cares about |
| Simultaneous multiple external memory providers in v1 | Conflicts with current provider architecture and would expand scope sharply |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| PROV-01 | Phase 1 | Complete |
| PROV-02 | Phase 1 | Complete |
| PROV-03 | Phase 1 | Complete |
| MODEL-01 | Phase 2 | Complete |
| MODEL-02 | Phase 2 | Complete |
| MODEL-03 | Phase 2 | Complete |
| MODEL-04 | Phase 2 | Complete |
| FACT-01 | Phase 04.2 | Complete |
| FACT-02 | Phase 04.2 | Complete |
| FACT-03 | Phase 04.2 | Complete |
| FACT-04 | Phase 04.4 | Complete |
| FACT-05 | Phase 04.4 | Complete |
| FACT-06 | Phase 04.4 | Complete |
| SCOPE-01 | Phase 2 | Complete |
| SCOPE-02 | Phase 2 | Complete |
| SCOPE-03 | Phase 2 | Complete |
| RETR-01 | Phase 3 | Complete |
| RETR-02 | Phase 3 | Complete |
| RETR-03 | Phase 3 | Complete |
| RETR-04 | Phase 3 | Complete |
| RETR-05 | Phase 04.3 | Complete |
| RETR-06 | Phase 04.3 | Complete |
| RETR-07 | Phase 04.5 | Complete |
| RETR-08 | Phase 04.5 | Complete |
| TIME-01 | Phase 2 | Complete |
| TIME-02 | Phase 2 | Complete |
| TIME-03 | Phase 3 | Complete |
| QUAL-01 | Phase 3 | Complete |
| QUAL-02 | Phase 4 | Complete |
| QUAL-03 | Phase 4 | Complete |
| QUAL-04 | Phase 04.1 | Planned |
| QUAL-05 | Phase 04.5 | Complete |

**Coverage:**
- v1 requirements: 27 total
- Mapped to phases: 27
- Unmapped: 0

---
*Requirements defined: 2026-04-06*
*Last updated: 2026-04-06 after Phase 04.5 execution*
