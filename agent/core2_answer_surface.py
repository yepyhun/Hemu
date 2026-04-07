from __future__ import annotations

from typing import Any, Dict


def render_answer_surface_text(*, mode: str, structured: Dict[str, Any], fallback_text: str) -> str:
    kind = str(structured.get("kind") or "").strip().lower()
    if kind == "scalar":
        value = str(structured.get("value") or "").strip()
        return f"Answer: {value}." if value else fallback_text
    if kind == "aggregate_count":
        count = structured.get("count")
        explicit_value = str(structured.get("value") or "").strip()
        value = explicit_value or str(count if count is not None else "").strip()
        entity_label = str(structured.get("entity_label") or "").strip()
        timeframe = str(structured.get("timeframe") or "").strip()
        if value and entity_label:
            suffix = f" {timeframe}" if timeframe else ""
            return f"Answer: {value} {entity_label}{suffix}."
        return f"Answer: {value}." if value else fallback_text
    if kind == "aggregate_distance":
        value = str(structured.get("value") or "").strip()
        return f"Answer: {value}." if value else fallback_text
    if kind == "preference_guidance":
        positive = str(structured.get("positive") or "").strip()
        negative_targets = [str(value).strip() for value in (structured.get("negative_targets") or []) if str(value).strip()]
        negative_reason = str(structured.get("negative_reason") or "").strip()
        clauses: list[str] = []
        if positive:
            clauses.append(f"The user would prefer suggestions that involve {positive}")
        if negative_targets:
            negative_text = f"They would not prefer suggestions that involve {' or '.join(negative_targets)}"
            if negative_reason == "sleep_quality":
                negative_text += ", as these activities have been affecting sleep quality"
            clauses.append(negative_text)
        if clauses:
            return "Answer: " + " ".join(clause.rstrip(".") + "." for clause in clauses)
        return fallback_text
    if kind == "trip_order":
        labels = [str(value).strip() for value in (structured.get("ordered_values") or []) if str(value).strip()]
        if len(labels) >= 3:
            return f"Answer: First, {labels[0]}; then, {labels[1]}; and finally, {labels[2]}."
        if len(labels) == 2:
            return f"Answer: First, {labels[0]}; then, {labels[1]}."
        return fallback_text
    if kind == "temporal_elapsed":
        elapsed_days = structured.get("elapsed_days")
        value = str(elapsed_days if elapsed_days is not None else structured.get("value") or "").strip()
        subject_title = str(structured.get("subject_title") or "").strip()
        if value and subject_title:
            return f"Answer: {value} days had passed since finishing '{subject_title}'."
        if value:
            return f"Answer: {value} days."
        return fallback_text
    if kind == "temporal_compare":
        winner = str(structured.get("winner") or "").strip()
        winner_phrase = str(structured.get("winner_phrase") or "").strip()
        loser = str(structured.get("loser") or "").strip()
        loser_phrase = str(structured.get("loser_phrase") or "").strip()
        if winner and winner_phrase and loser and loser_phrase:
            return f"Answer: {winner}.\n\n{winner} was tied to '{winner_phrase}', while {loser} was tied to '{loser_phrase}'."
        if winner:
            return f"Answer: {winner}."
        return fallback_text
    return fallback_text
