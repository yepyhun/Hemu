# Core2 Glossary

## Purpose

This tiny glossary keeps the project vocabulary stable across planning, implementation, review, and gate analysis.

## Terms

### Knowledge Structure

The deeper substrate shape of memory:

- entities
- facts
- relations/links
- validity windows
- episodes
- compact summaries or clusters where needed

This is deeper than routing jargon.

### Family

A kernel-side memory/query handling category, not a social or graph community label.

Examples:

- personal attribute
- preference
- habit/routine
- collection/count
- temporal update
- conflict/supersession case

### Candidate

A proposed structured memory object derived from raw input before it is fully accepted into canonical durable state.

### Fact

A structured durable-memory object that Core2 can inspect, index, and reason over under explicit state rules.

### Supersede

A deterministic state transition where a newer covered fact validly replaces an older one.

### Conflict

A state where the kernel cannot safely collapse competing claims under its deterministic rules.

### Fact-First Recall

Recall behavior that prefers the structured fact substrate for covered families before broader canonical/raw-style search.

### Answer Surface

A provider-owned, deterministic answer-ready structure built from structured kernel objects for covered cases.

### Handoff Miss

A failure where the kernel likely has the needed memory substrate, but the final provider/runtime/answer handoff does not render or preserve it correctly.

### Judge Artifact

A miss caused by the external evaluator or judge path rather than by a clear kernel correctness failure.

