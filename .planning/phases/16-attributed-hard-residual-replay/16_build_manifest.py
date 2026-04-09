#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


PHASE_DIR = Path(__file__).resolve().parent
SOURCE_STATUS_PATH = (
    PHASE_DIR.parent / "08.1-invariant-harness-and-noise-repair-import" / "08.1-HYBRID-RETEST-38-STATUS.json"
)
MANIFEST_PATH = PHASE_DIR / "16-REPLAY-MANIFEST.json"


def main() -> None:
    source = json.loads(SOURCE_STATUS_PATH.read_text(encoding="utf-8"))
    question_ids = [str(value).strip() for value in source.get("latest_question_ids") or [] if str(value).strip()]
    manifest = {
        "schema_version": "phase16.manifest.v1",
        "source_status_path": str(SOURCE_STATUS_PATH.relative_to(PHASE_DIR.parent.parent)),
        "source_reference_pass_rate": float(source.get("pass_rate") or 0.0),
        "source_reference_passed": int(source.get("failure_patterns", {}).get("passed") or 0),
        "frozen_question_count": len(question_ids),
        "question_ids": question_ids,
        "replay_mode": "core2",
        "benchmark_fast": True,
        "stop_on_bad_start": False,
        "note": "Frozen hard 38 replay set sourced from the canonical pre-ranking-regression 08.1 residual status artifact.",
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
