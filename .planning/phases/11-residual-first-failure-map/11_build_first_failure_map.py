#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

from agent.core2_longmemeval_benchmark import (
    BENCHMARK_FAST_PROFILES,
    DEFAULT_DATASET,
    _packet_contains_answer,
    _seed_core2_kernel,
)
from agent.core2_runtime import Core2Runtime


PHASE_DIR = Path(__file__).resolve().parent
STATUS_PATH = PHASE_DIR.parent / "08.1-invariant-harness-and-noise-repair-import" / "08.1-HYBRID-RETEST-38-STATUS.json"
MANIFEST_PATH = PHASE_DIR / "11-RESIDUAL-MANIFEST.json"
TRANSITIONS_PATH = PHASE_DIR / "11-CASE-TRANSITIONS.jsonl"
OUTCOME_PATH = PHASE_DIR / "11-OUTCOME.json"


def _load_manifest_question_ids() -> list[str]:
    payload = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    return [str(value).strip() for value in payload.get("latest_question_ids") or [] if str(value).strip()]


def _load_dataset_entries() -> dict[str, dict[str, Any]]:
    entries = json.loads(DEFAULT_DATASET.read_text(encoding="utf-8"))
    return {str(entry.get("question_id") or "").strip(): entry for entry in entries}


def _compact_recall(runtime: Core2Runtime, question: str) -> dict[str, Any]:
    packet = runtime.recall(
        question,
        mode="source_supported",
        operator=None,
        risk_class="standard",
        max_items=6,
    )
    return packet.to_dict(
        compact=True,
        tool_budget_profile=BENCHMARK_FAST_PROFILES["supported"]["tool_budget_profile"],
        tool_payload_mode=BENCHMARK_FAST_PROFILES["supported"]["tool_payload_mode"],
    )


def _classify_first_failure(*, recall_packet: dict[str, Any], evidence_contains_answer: bool, answer_surface_hit: bool) -> tuple[str, str]:
    if not recall_packet or not evidence_contains_answer:
        return "retrieval_selection", "retrieval/selection miss"
    if not answer_surface_hit:
        return "structured_route_unavailable", "evidence present but no authoritative answer surface"
    return "delivery_prompt_path", "evidence and authoritative surface present; downstream delivery/handoff/judge remains"


def main() -> None:
    question_ids = _load_manifest_question_ids()
    entries = _load_dataset_entries()

    manifest: list[dict[str, Any]] = []
    transitions: list[dict[str, Any]] = []
    bucket_counts: Counter[str] = Counter()

    for question_id in question_ids:
        entry = entries.get(question_id)
        if not entry:
            continue
        manifest.append(
            {
                "question_id": question_id,
                "question_type": str(entry.get("question_type") or "unknown"),
                "question": str(entry.get("question") or "").strip(),
                "answer": str(entry.get("answer") or "").strip(),
                "abstention_case": "_abs" in question_id,
            }
        )

        with tempfile.TemporaryDirectory(prefix=f"phase11-{question_id}-") as tmp_dir:
            home = Path(tmp_dir)
            seeded_entries = _seed_core2_kernel(home, entry, oracle_only=False)
            runtime = Core2Runtime(str(home / "core2" / "core2.db"))
            runtime.initialize(f"phase11-{question_id}")
            try:
                recall_packet = _compact_recall(runtime, str(entry.get("question") or ""))
            finally:
                runtime.shutdown()

        answer = str(entry.get("answer") or "").strip()
        evidence_contains_answer = _packet_contains_answer(recall_packet, answer)
        answer_surface = dict(recall_packet.get("answer_surface") or {})
        answer_surface_mode = str(answer_surface.get("mode") or "").strip().lower()
        answer_surface_family = str(answer_surface.get("family") or "").strip()
        answer_surface_text = str(answer_surface.get("text") or "").strip()
        answer_surface_hit = bool(answer_surface) and answer_surface_mode in {"fact_only", "fact_plus_summary"} and bool(answer_surface_text)
        first_failure_stage, short_reason = _classify_first_failure(
            recall_packet=recall_packet,
            evidence_contains_answer=evidence_contains_answer,
            answer_surface_hit=answer_surface_hit,
        )
        bucket_counts[first_failure_stage] += 1
        transitions.append(
            {
                "case_id": question_id,
                "question_type": str(entry.get("question_type") or "unknown"),
                "query_family": str(recall_packet.get("query_family") or ""),
                "route_family": str(recall_packet.get("route_family") or ""),
                "seeded_core2_entries": seeded_entries,
                "evidence_present": evidence_contains_answer,
                "evidence_item_count": len(recall_packet.get("items") or []),
                "covered_route_available": bool(answer_surface),
                "answer_surface_hit": answer_surface_hit,
                "answer_surface_mode": answer_surface_mode,
                "answer_surface_family": answer_surface_family,
                "promptless_authoritative_possible": bool(answer_surface_hit),
                "first_failure_stage": first_failure_stage,
                "failure_bucket": first_failure_stage,
                "short_reason": short_reason,
            }
        )

    dominant_bucket = ""
    dominant_count = 0
    for name, count in bucket_counts.items():
        if count > dominant_count:
            dominant_bucket = name
            dominant_count = count

    verdict_map = {
        "retrieval_selection": "retrieval-dominant",
        "structured_route_unavailable": "retrieval-dominant",
        "delivery_prompt_path": "delivery-dominant",
    }
    verdict = verdict_map.get(dominant_bucket, "mixed/no-single-bottleneck")
    if not bucket_counts:
        verdict = "mixed/no-single-bottleneck"

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    with TRANSITIONS_PATH.open("w", encoding="utf-8") as handle:
        for row in transitions:
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")
    OUTCOME_PATH.write_text(
        json.dumps(
            {
                "total_cases": len(transitions),
                "bucket_counts": dict(bucket_counts),
                "dominant_bucket": dominant_bucket,
                "dominant_bucket_count": dominant_count,
                "verdict": verdict,
                "note": "This map is intentionally local and upstream-first: it classifies where the case fails before downstream model judging, so benchmark-level handoff/judge artifacts remain secondary annotations from prior paid reruns.",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
