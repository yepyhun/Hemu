from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Tuple


_TRACEBACK_RE = re.compile(r"\b(traceback|exception|permission denied|file not found|no such file|failed)\b", re.IGNORECASE)
_ERROR_STATUS_VALUES = {"error", "failed", "failure"}
_ARTIFACT_SOURCE_TYPES = {"tool_artifact", "file_artifact"}


def _looks_like_error_payload(text: str) -> bool:
    normalized = str(text or "").strip()
    if not normalized:
        return False
    if normalized.startswith("{"):
        try:
            payload = json.loads(normalized)
        except json.JSONDecodeError:
            return bool(_TRACEBACK_RE.search(normalized))
        if not isinstance(payload, dict):
            return False
        if isinstance(payload.get("error"), str) and payload.get("error", "").strip():
            return True
        if payload.get("success") is False:
            return True
        status = str(payload.get("status") or "").strip().lower()
        if status in _ERROR_STATUS_VALUES:
            return True
        return False
    return bool(_TRACEBACK_RE.search(normalized))


def detect_noise_problems(record: Dict[str, Any]) -> Tuple[str, ...]:
    title = str(record.get("title") or "").strip().lower()
    source_type = str(record.get("source_type") or "").strip().lower()
    text = str(record.get("content") or "").strip()
    problems: List[str] = []
    if source_type in _ARTIFACT_SOURCE_TYPES and _looks_like_error_payload(text):
        if source_type == "tool_artifact":
            problems.append("tool_error_artifact")
        elif source_type == "file_artifact":
            problems.append("file_error_artifact")
    elif (title.startswith("tool.") or title.startswith("file.")) and _looks_like_error_payload(text):
        problems.append("named_error_artifact")
    return tuple(problems)


def repair_core2_noise(*, runtime: Any, source_ref: str, limit: int = 1200) -> Dict[str, Any]:
    issues: List[Dict[str, Any]] = []
    repaired = 0
    for record in runtime.store.list_canonical_objects(include_inactive=False)[:limit]:
        problems = detect_noise_problems(record)
        if not problems:
            continue
        repaired += int(
            runtime.store.update_canonical_state(
                str(record.get("object_id") or ""),
                "rejected",
                "noise_repair",
                metadata_patch={
                    **dict(record.get("metadata") or {}),
                    "noise_repair": {
                        "source_ref": str(source_ref or "").strip(),
                        "problems": list(problems),
                    },
                },
            )
        )
        issues.append(
            {
                "object_id": str(record.get("object_id") or ""),
                "title": str(record.get("title") or ""),
                "source_type": str(record.get("source_type") or ""),
                "problems": list(problems),
            }
        )
    return {
        "success": True,
        "source_ref": str(source_ref or "").strip(),
        "issues_found": len(issues),
        "records_repaired": repaired,
        "issues": issues,
    }
