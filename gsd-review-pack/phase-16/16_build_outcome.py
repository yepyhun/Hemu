#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


PHASE_DIR = Path(__file__).resolve().parent
STATUS_PATH = PHASE_DIR / "16-ATTRIBUTED-STATUS.json"
OUTCOME_PATH = PHASE_DIR / "16-ATTRIBUTED-OUTCOME.json"


def _dominant(counter: dict[str, int]) -> tuple[str, int, bool]:
    filtered = {str(k): int(v) for k, v in (counter or {}).items() if str(k)}
    if not filtered:
        return "", 0, False
    ordered = sorted(filtered.items(), key=lambda item: (-item[1], item[0]))
    top_name, top_count = ordered[0]
    tied = len(ordered) > 1 and int(ordered[1][1]) == int(top_count)
    return top_name, int(top_count), tied


def _next_direction(label: str) -> str:
    mapping = {
        "retrieval_failure": "retrieval_selection_followup",
        "sufficiency_failure": "retrieval_sufficiency_followup",
        "reasoning_failure": "reasoning_followup",
        "delivery_surface_failure": "delivery_surface_followup",
        "judge_false_positive": "judge_artifact_followup",
        "judge_false_negative": "judge_artifact_followup",
        "latency_abort": "latency_budget_followup",
    }
    return mapping.get(label, "")


def main() -> None:
    status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    gate_status = dict(status.get("gate_status") or {})
    attribution = dict(status.get("attribution") or {})
    summary = dict(attribution.get("summary") or {})
    records = list(attribution.get("records") or [])
    label_counts = {str(k): int(v) for k, v in (summary.get("label_counts") or {}).items()}
    stage_counts = {str(k): int(v) for k, v in (summary.get("stage_counts") or {}).items()}
    raw_passed = int(gate_status.get("failure_patterns", {}).get("passed") or 0)
    attributed_passed = sum(1 for record in records if str(record.get("attribution_label") or "") == "passed")
    judge_false_positive_passes = sum(
        1
        for record in records
        if bool(record.get("passed")) and str(record.get("attribution_label") or "") == "judge_false_positive"
    )

    dominant_label, dominant_label_count, label_tied = _dominant(
        {k: v for k, v in label_counts.items() if k not in {"passed"}}
    )
    dominant_stage, dominant_stage_count, stage_tied = _dominant(
        {k: v for k, v in stage_counts.items() if k not in {"passed"}}
    )

    next_direction = _next_direction(dominant_label) if dominant_label and not label_tied else ""
    stop_rule = ""
    if not next_direction:
        stop_rule = "Do not open multiple new build hypotheses from this replay; carry the attributed outcome forward as a stop-point until one dominant actionable bucket emerges."

    outcome = {
        "schema_version": "phase16.outcome.v2",
        "total_cases": int(summary.get("total_cases") or 0),
        "pass_rate": float(gate_status.get("pass_rate") or 0.0),
        "passed": raw_passed,
        "attributed_passed": attributed_passed,
        "judge_false_positive_passes": judge_false_positive_passes,
        "label_counts": label_counts,
        "stage_counts": stage_counts,
        "dominant_label": dominant_label,
        "dominant_label_count": dominant_label_count,
        "dominant_stage": dominant_stage,
        "dominant_stage_count": dominant_stage_count,
        "verdict": "single_dominant_bucket" if next_direction else "mixed_or_non_actionable",
        "next_direction": next_direction,
        "stop_rule": stop_rule,
        "note": "Attributed replay outcome derived from the frozen hard 38 set and the phase-15 attribution contract. Raw benchmark passes may exceed attributed grounded passes when the replay surfaces judge-false-positive cases.",
    }
    OUTCOME_PATH.write_text(json.dumps(outcome, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
