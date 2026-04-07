# Core2 Handmade Acceptance Set

## Purpose

This is the small local benchmark that should answer:

“Are we walking in the right direction?”

It is not a replacement for the paid LongMemEval gate. It is a pre-gate directional proof used to decide whether a rerun is worth spending.

## Pass Rule

The handmade set is green only if:

- the expected answer or abstention matches
- the expected structured support/path is present
- no case requires hidden benchmark-specific interpretation to look successful

## Cases

### Case 1: Current Attribute

- Family: personal attribute
- Setup: remember current occupation
- Query: “What is my current occupation?”
- Expected: direct answer from current structured fact
- Expected path: fact-first recall -> answer surface
- Fail if: answer comes only from raw fallback or ambiguous broad search

### Case 2: Updated Attribute

- Family: temporal update/currentness
- Setup: remember old residence, then newer residence
- Query: “Where do I live now?”
- Expected: current value only, with previous value still inspectable in history
- Expected path: deterministic supersession + fact-first recall
- Fail if: old and new values collapse into ambiguity without conflict or currentness

### Case 3: Preference With Negative Guidance

- Family: preference
- Setup: remember a stable positive preference plus a negative evening constraint
- Query: “What do I prefer in the evening?”
- Expected: bounded preference answer reflecting the current negative/positive guidance
- Expected path: structured preference fact(s) -> answer surface
- Fail if: answer is generic advice instead of memory-backed preference recall

### Case 4: Habit / Routine

- Family: habit/routine
- Setup: remember a repeated routine with a temporal qualifier
- Query: “What do I usually do before bed?”
- Expected: compact routine answer from structured routine memory
- Expected path: fact-first recall
- Fail if: the system reconstructs from broad raw text each time

### Case 5: Collection Count Update

- Family: collection/count
- Setup: remember collection total, then item-added update
- Query: “How many items are in my collection now?”
- Expected: updated total from structured aggregate/current state
- Expected path: deterministic update materialization -> fact-first recall
- Fail if: total only appears after wide raw rescans or ad hoc topic logic

### Case 6: Temporal Before/After

- Family: temporal update
- Setup: remember two anchored events in order
- Query: “Which happened first?”
- Expected: bounded temporal answer from structured event anchors
- Expected path: structured temporal facts, not freeform timeline reconstruction
- Fail if: the system has to improvise from raw history to compare order

### Case 7: Conflict

- Family: conflict/supersession
- Setup: remember incompatible claims that should not be silently merged
- Query: “What is the current truth here?”
- Expected: explicit conflict or safe abstention unless one claim validly supersedes the other
- Expected path: conflict state or abstention
- Fail if: the kernel silently picks one unsupported claim

### Case 8: Abstention

- Family: abstention
- Setup: memory does not contain enough support
- Query: covered durable-memory question with insufficient structured support
- Expected: abstain or explicit fallback
- Expected path: fail-closed surface behavior
- Fail if: the system guesses confidently

### Case 9: Handoff-Sensitive Covered Case

- Family: covered durable-memory handoff
- Setup: covered fact exists and is answerable
- Query: a case known to be sensitive to final handoff formatting
- Expected: correct answer plus clear structured support in the provider-owned surface
- Expected path: fact-first recall -> answer surface -> clean handoff
- Fail if: the kernel is correct internally but the surface drops or muddles the support

## Rerun Trigger Rule

Do not rerun the paid external gate unless all of the following are true:

1. The handmade set is green.
2. The current change is tied to an explicit blocker class.
3. The expected effect on the gate is clear enough to justify the rerun.

If any of these are false, the next step is not “rerun the benchmark,” but “clarify the local proof first.”

