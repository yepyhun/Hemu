from __future__ import annotations

import json
import os
import random
import re
import time
from collections import Counter, defaultdict
from contextlib import ExitStack
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict, List, Sequence
from unittest.mock import patch

import openai
import yaml

from agent.core2_runtime import Core2Runtime


DEFAULT_DATASET = Path("/home/lauratom/LongMemEval/data/longmemeval_s_cleaned.json")
DEFAULT_BENCHMARK_PROVIDER = "cometapi"
DEFAULT_BENCHMARK_BASE_URL = "https://api.cometapi.com/v1"
DEFAULT_BENCHMARK_MODEL = "minimax-m2.7"
DEFAULT_JUDGE_MODEL = "minimax-m2.7"
DEFAULT_CANARY_QUESTION_IDS = (
    "0db4c65d",
    "195a1a1b",
    "d682f1a2",
    "gpt4_7f6b06db",
    "f523d9fe",
)
BENCHMARK_FAST_PROFILES: dict[str, dict[str, Any]] = {
    "minimal": {
        "tool_budget_profile": "minimal",
        "tool_payload_mode": "benchmark_lean",
        "max_iterations": 2,
        "max_tokens": 160,
        "ephemeral_system_prompt": (
            "Benchmark mode. Answer directly from memory evidence only. "
            "Use at most 1 short sentence. If evidence is insufficient, abstain in 1 short sentence."
        ),
    },
    "compact": {
        "tool_budget_profile": "compact",
        "tool_payload_mode": "benchmark_lean",
        "max_iterations": 3,
        "max_tokens": 256,
        "ephemeral_system_prompt": (
            "Benchmark mode. Answer briefly and directly from memory evidence only. "
            "Use at most 2 short sentences. If evidence is insufficient, abstain in 1 short sentence."
        ),
    },
    "supported": {
        "tool_budget_profile": "supported",
        "tool_payload_mode": "benchmark_lean",
        "max_iterations": 3,
        "max_tokens": 280,
        "ephemeral_system_prompt": (
            "Benchmark mode. Answer directly from memory evidence only. "
            "For compare, update, or timeline questions, prefer one consolidated recall call first and only make a second recall call if the first one is still ambiguous. "
            "Put the direct answer in the first sentence in the form `Answer: <result>`. "
            "For compare questions, name only the winning result and do not restate both options unless needed for one short evidence clause. "
            "If both memories are before the same anchor date, compare them directly and choose the earlier one. "
            "After the answer line, give at most one very short evidence sentence. "
            "Do not add offers to save memory, disclaimers, or extra coaching. If evidence is insufficient, abstain in 1 short sentence."
        ),
    },
}

_SUPPORTED_BUDGET_HINTS = (
    " which ",
    " compare ",
    " first ",
    " last ",
    " before ",
    " after ",
    " earlier ",
    " later ",
    " order ",
    " updated ",
    " changed ",
)

_YES_NO_RE = re.compile(r"\b(yes|no)\b", re.IGNORECASE)
_ABSTENTION_HINTS = (
    "i don't know",
    "i do not know",
    "not enough information",
    "cannot determine",
    "can't determine",
    "unclear",
    "insufficient information",
    "no stored",
)


@dataclass(frozen=True)
class Core2LongMemEvalRunResult:
    question_id: str
    question_type: str
    passed: bool
    judge: str
    hypothesis: str
    answer: str
    prompt_excerpt: str
    prompt_tokens_estimate: int
    baseline_replay_tokens_estimate: int
    estimated_token_savings: int
    estimated_savings_ratio: float
    seeded_core2_entries: int
    seed_seconds: float
    tool_seconds: float
    conversation_seconds: float
    api_seconds: float
    judge_seconds: float
    total_wall_seconds: float
    kernel_local_seconds: float
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    api_calls: int
    provider: str
    base_url: str
    model: str
    budget_profile: str
    failure_pattern: str
    recall_abstained: bool
    recall_route_family: str
    recall_query_family: str
    evidence_item_count: int
    evidence_contains_answer: bool
    memory_tool_calls: int
    prompt_contains_answer: bool
    prompt_contains_question_terms: bool
    answer_surface_mode: str = ""
    answer_surface_family: str = ""
    answer_surface_hit: bool = False
    promptless_authoritative: bool = False
    local_comparator: str = ""
    local_comparator_reason: str = ""
    route_notes: List[str] = field(default_factory=list)
    support_confidence: str = ""
    temporal_confidence: str = ""
    resolution_confidence: str = ""
    identity_confidence: str = ""

    def as_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["estimated_savings_ratio"] = round(self.estimated_savings_ratio, 6)
        return payload


def stratum_key(entry: dict[str, Any]) -> str:
    suffix = "abs" if "_abs" in str(entry.get("question_id") or "") else "std"
    return f"{entry.get('question_type', 'unknown')}|{suffix}"


def stratified_sample(entries: list[dict[str, Any]], target_size: int, seed: int) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in entries:
        grouped[stratum_key(entry)].append(entry)
    for bucket in grouped.values():
        rng.shuffle(bucket)
    total = len(entries)
    raw = {key: len(bucket) * target_size / total for key, bucket in grouped.items()}
    base = {key: int(value) for key, value in raw.items()}
    remaining = target_size - sum(base.values())
    order = sorted(((raw[key] - base[key], key) for key in grouped.keys()), reverse=True)
    for _, key in order[:remaining]:
        base[key] += 1
    sample: list[dict[str, Any]] = []
    for key in sorted(grouped.keys()):
        sample.extend(grouped[key][: base[key]])
    rng.shuffle(sample)
    return sample


def get_anscheck_prompt(task: str, question: str, answer: str, response: str, *, abstention: bool) -> str:
    if not abstention:
        if task in {"single-session-user", "single-session-assistant", "multi-session"}:
            template = (
                "I will give you a question, a correct answer, and a response from a model. "
                "Please answer yes if the response contains the correct answer. Otherwise, answer no. "
                "If the response is equivalent to the correct answer or contains all the intermediate "
                "steps to get the correct answer, you should also answer yes. If the response only "
                "contains a subset of the information required by the answer, answer no.\n\n"
                "Question: {}\n\nCorrect Answer: {}\n\nModel Response: {}\n\n"
                "Is the model response correct? Answer yes or no only."
            )
            return template.format(question, answer, response)
        if task == "temporal-reasoning":
            template = (
                "I will give you a question, a correct answer, and a response from a model. "
                "Please answer yes if the response contains the correct answer. Otherwise, answer no. "
                "If the response is equivalent to the correct answer or contains all the intermediate "
                "steps to get the correct answer, you should also answer yes. If the response only "
                "contains a subset of the information required by the answer, answer no. In addition, "
                "do not penalize off-by-one errors for the number of days. If the question asks for "
                "the number of days/weeks/months, etc., and the model makes off-by-one errors "
                "(e.g., predicting 19 days when the answer is 18), the model's response is still correct.\n\n"
                "Question: {}\n\nCorrect Answer: {}\n\nModel Response: {}\n\n"
                "Is the model response correct? Answer yes or no only."
            )
            return template.format(question, answer, response)
        if task == "knowledge-update":
            template = (
                "I will give you a question, a correct answer, and a response from a model. "
                "Please answer yes if the response contains the correct answer. Otherwise, answer no. "
                "If the response contains some previous information along with an updated answer, "
                "the response should be considered as correct as long as the updated answer is the "
                "required answer.\n\nQuestion: {}\n\nCorrect Answer: {}\n\nModel Response: {}\n\n"
                "Is the model response correct? Answer yes or no only."
            )
            return template.format(question, answer, response)
        if task == "single-session-preference":
            template = (
                "I will give you a question, a rubric for desired personalized response, and a response "
                "from a model. Please answer yes if the response satisfies the desired response. "
                "Otherwise, answer no. The model does not need to reflect all the points in the rubric. "
                "The response is correct as long as it recalls and utilizes the user's personal information correctly.\n\n"
                "Question: {}\n\nRubric: {}\n\nModel Response: {}\n\n"
                "Is the model response correct? Answer yes or no only."
            )
            return template.format(question, answer, response)
        raise NotImplementedError(f"Unsupported task type: {task}")
    template = (
        "I will give you an unanswerable question, an explanation, and a response from a model. "
        "Please answer yes if the model correctly identifies the question as unanswerable. "
        "The model could say that the information is incomplete, or some other information is "
        "given but the asked information is not.\n\nQuestion: {}\n\nExplanation: {}\n\n"
        "Model Response: {}\n\nDoes the model correctly identify the question as unanswerable? "
        "Answer yes or no only."
    )
    return template.format(question, answer, response)


def estimate_text_tokens(value: str) -> int:
    text = str(value or "")
    if not text:
        return 0
    return max(1, (len(text) + 3) // 4)


def estimate_message_tokens(messages: Sequence[dict[str, Any]]) -> int:
    total = 0
    for msg in messages or []:
        total += 4
        total += estimate_text_tokens(msg.get("role", ""))
        content = msg.get("content", "")
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    total += estimate_text_tokens(item.get("text", "") or item.get("content", ""))
                else:
                    total += estimate_text_tokens(str(item))
        else:
            total += estimate_text_tokens(str(content))
        for tool_call in msg.get("tool_calls") or []:
            total += estimate_text_tokens(str(tool_call))
    return total


def _normalize_answer_text(text: str) -> str:
    return " ".join(str(text or "").split()).casefold()


def _normalize_loose_answer_text(text: str) -> str:
    compact = _normalize_answer_text(text)
    compact = re.sub(r"[*_`\"'“”‘’]+", " ", compact)
    compact = re.sub(r"[^a-z0-9]+", " ", compact)
    return " ".join(compact.split())


def _response_contains_answer(response: str, answer: str) -> bool:
    normalized_answer = _normalize_loose_answer_text(answer)
    normalized_response = _normalize_loose_answer_text(response)
    if not normalized_answer or not normalized_response:
        return False
    first_sentence = str(response or "").split(".", 1)[0]
    normalized_first_sentence = _normalize_loose_answer_text(first_sentence)
    if not normalized_first_sentence:
        return False
    if re.fullmatch(r"\d+(?:\s+\d+)*", normalized_answer):
        return re.search(rf"(?<![a-z0-9]){re.escape(normalized_answer)}(?![a-z0-9])", normalized_first_sentence) is not None
    if len(normalized_answer) < 4:
        return False
    return normalized_answer in normalized_first_sentence


def _normalize_judge_text(*parts: str) -> str:
    text = " ".join(str(part or "").strip() for part in parts if str(part or "").strip())
    compact = " ".join(text.split())
    if not compact:
        return ""
    match = _YES_NO_RE.search(compact)
    return str(match.group(1) or "").lower() if match else ""


def _extract_ints(text: str) -> list[int]:
    return [int(match) for match in re.findall(r"\d+", str(text or ""))]


def _contains_phrase(text: str, phrase: str) -> bool:
    normalized_text = _normalize_loose_answer_text(text)
    normalized_phrase = _normalize_loose_answer_text(phrase)
    return bool(normalized_text and normalized_phrase and normalized_phrase in normalized_text)


def _normalize_preference_match_text(text: str) -> str:
    normalized = _normalize_loose_answer_text(text)
    if not normalized:
        return ""
    normalized = re.sub(r"\b(my|your|their)\b", "their", normalized)
    return " ".join(normalized.split())


def _contains_preference_phrase(text: str, phrase: str) -> bool:
    normalized_text = _normalize_preference_match_text(text)
    normalized_phrase = _normalize_preference_match_text(phrase)
    return bool(normalized_text and normalized_phrase and normalized_phrase in normalized_text)


def _contains_in_order(text: str, phrases: Sequence[str]) -> bool:
    normalized_text = _normalize_loose_answer_text(text)
    if not normalized_text:
        return False
    start = 0
    for phrase in phrases:
        normalized_phrase = _normalize_loose_answer_text(phrase)
        if not normalized_phrase:
            return False
        idx = normalized_text.find(normalized_phrase, start)
        if idx < 0:
            return False
        start = idx + len(normalized_phrase)
    return True


def _trip_support_phrases(ordered_values: Sequence[str]) -> list[str]:
    support: list[str] = []
    for value in ordered_values:
        raw = str(value or "").strip()
        if not raw:
            continue
        destination_match = re.search(r"\b(?:to|at)\s+(.+)$", raw, flags=re.IGNORECASE)
        if destination_match:
            destination = destination_match.group(1).strip()
            if destination:
                support.append(destination)
                continue
        support.append(raw)
    deduped: list[str] = []
    seen: set[str] = set()
    for value in support:
        normalized = _normalize_loose_answer_text(value)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(value)
    return deduped


def _surface_text_coherent(answer_surface: Dict[str, Any], hypothesis: str) -> bool:
    structured = dict(answer_surface.get("structured") or {})
    kind = str(structured.get("kind") or "").strip().lower()
    if not kind:
        return False
    if kind == "scalar":
        value = str(structured.get("value") or "").strip()
        return bool(value) and _contains_phrase(hypothesis, value)
    if kind == "aggregate_count":
        count = structured.get("count")
        if count is None:
            return False
        numbers = _extract_ints(hypothesis)
        if int(count) not in numbers:
            return False
        entity_label = str(structured.get("entity_label") or "").strip()
        if entity_label and not _contains_phrase(hypothesis, entity_label):
            return False
        return True
    if kind == "temporal_elapsed":
        elapsed_days = structured.get("elapsed_days")
        if elapsed_days is None:
            return False
        numbers = _extract_ints(hypothesis)
        if int(elapsed_days) not in numbers:
            return False
        subject_title = str(structured.get("subject_title") or "").strip()
        return not subject_title or _contains_phrase(hypothesis, subject_title)
    if kind == "trip_order":
        ordered_values = [str(value).strip() for value in (structured.get("ordered_values") or []) if str(value).strip()]
        return len(ordered_values) >= 2 and _contains_in_order(hypothesis, ordered_values)
    if kind == "preference_guidance":
        positive = str(structured.get("positive") or "").strip()
        if positive and not _contains_phrase(hypothesis, positive):
            return False
        negative_targets = [str(value).strip() for value in (structured.get("negative_targets") or []) if str(value).strip()]
        if negative_targets and not all(_contains_phrase(hypothesis, target) for target in negative_targets):
            return False
        negative_reason = str(structured.get("negative_reason") or "").strip()
        if negative_reason == "sleep_quality" and not _contains_phrase(hypothesis, "sleep quality"):
            return False
        return bool(positive or negative_targets)
    return False


def _canonical_local_comparator(
    *,
    question_type: str,
    answer: str,
    hypothesis: str,
    answer_surface: Dict[str, Any] | None,
    promptless_authoritative: bool,
) -> tuple[str, str]:
    if not promptless_authoritative:
        return "not_applicable", "not_promptless_authoritative"
    surface = dict(answer_surface or {})
    structured = dict(surface.get("structured") or {})
    kind = str(structured.get("kind") or "").strip().lower()
    if not kind:
        return "not_applicable", "missing_structured_kind"
    supported_kinds = {"aggregate_count", "temporal_elapsed", "trip_order", "preference_guidance", "scalar"}
    if kind not in supported_kinds:
        return "not_applicable", f"unsupported_kind:{kind}"
    if not _surface_text_coherent(surface, hypothesis):
        return "no", "surface_text_structured_mismatch"

    normalized_question_type = str(question_type or "").strip().lower()
    if kind == "aggregate_count":
        count = structured.get("count")
        if count is None:
            return "not_applicable", "missing_count"
        answer_numbers = _extract_ints(answer)
        if answer_numbers and int(count) not in answer_numbers:
            return "no", "count_not_supported_by_gold_answer"
        return "yes", "structured_count_match"

    if kind == "temporal_elapsed":
        elapsed_days = structured.get("elapsed_days")
        if elapsed_days is None:
            return "not_applicable", "missing_elapsed_days"
        accepted_numbers = _extract_ints(answer)
        if accepted_numbers and int(elapsed_days) not in accepted_numbers:
            return "no", "elapsed_days_not_supported_by_gold_answer"
        if normalized_question_type != "temporal-reasoning":
            return "not_applicable", "unexpected_question_type"
        return "yes", "structured_temporal_elapsed_match"

    if kind == "trip_order":
        ordered_values = [str(value).strip() for value in (structured.get("ordered_values") or []) if str(value).strip()]
        if len(ordered_values) < 2:
            return "not_applicable", "insufficient_ordered_values"
        support_phrases = _trip_support_phrases(ordered_values)
        if not _contains_in_order(answer, support_phrases):
            return "no", "ordered_values_not_supported_by_gold_answer"
        return "yes", "structured_trip_order_match"

    if kind == "preference_guidance":
        positive = str(structured.get("positive") or "").strip()
        negative_targets = [str(value).strip() for value in (structured.get("negative_targets") or []) if str(value).strip()]
        negative_reason = str(structured.get("negative_reason") or "").strip()
        if positive and not _contains_preference_phrase(answer, positive):
            return "no", "positive_guidance_not_supported_by_gold_answer"
        if negative_targets and not all(_contains_preference_phrase(answer, target) for target in negative_targets):
            return "no", "negative_targets_not_supported_by_gold_answer"
        if negative_reason == "sleep_quality" and not _contains_phrase(answer, "sleep quality"):
            return "no", "negative_reason_not_supported_by_gold_answer"
        return "yes", "structured_preference_guidance_match"

    if kind == "scalar":
        value = str(structured.get("value") or "").strip()
        if not value:
            return "not_applicable", "missing_scalar_value"
        return ("yes", "structured_scalar_match") if _contains_phrase(answer, value) else ("no", "scalar_not_supported_by_gold_answer")

    return "not_applicable", f"unsupported_kind:{kind}"


def _judge_yes_no(*, base_url: str, api_key: str, model: str, prompt: str, max_tokens: int = 32, max_attempts: int = 3) -> str:
    client = openai.OpenAI(base_url=base_url, api_key=api_key)
    system_prompts = [
        "Reply with exactly one word: yes or no.",
        "Return only one lowercase word: yes or no. No punctuation. No explanation.",
        "Judge correctness. Output exactly yes or exactly no.",
    ]
    last_text = ""
    for attempt in range(max_attempts):
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompts[min(attempt, len(system_prompts) - 1)]},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=0,
        )
        choices = getattr(response, "choices", None) or []
        if not choices:
            last_text = ""
            continue
        message = getattr(choices[0], "message", None)
        text = str(getattr(message, "content", "") or "").strip()
        last_text = text
        normalized = _normalize_judge_text(text)
        if normalized in {"yes", "no"}:
            return normalized
    return _normalize_judge_text(last_text) or "unknown"


def _flatten_session(session_date: str, session_entry: Any) -> str:
    lines = [f"Session Date: {session_date}"]
    if isinstance(session_entry, list):
        for turn in session_entry:
            if not isinstance(turn, dict):
                continue
            role = str(turn.get("role") or "").strip() or "unknown"
            content = str(turn.get("content") or "").strip()
            if content:
                lines.append(f"{role.upper()}: {content}")
    elif isinstance(session_entry, dict):
        for key, value in session_entry.items():
            lines.append(f"{key}: {value}")
    else:
        lines.append(str(session_entry))
    return "\n".join(lines).strip()


def _iter_session_turns(session_entry: Any) -> list[tuple[str, str]]:
    turns: list[tuple[str, str]] = []
    if not isinstance(session_entry, list):
        return turns
    for turn in session_entry:
        if not isinstance(turn, dict):
            continue
        role = str(turn.get("role") or "").strip().lower() or "unknown"
        content = str(turn.get("content") or "").strip()
        if content:
            turns.append((role, content))
    return turns


def _iter_session_exchange_pairs(session_entry: Any) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    pending_user: list[str] = []
    for role, content in _iter_session_turns(session_entry):
        if role == "user":
            pending_user.append(content)
            continue
        if role != "assistant":
            continue
        user_message = "\n".join(part for part in pending_user if part).strip()
        if not user_message:
            continue
        assistant_response = str(content or "").strip()
        if not assistant_response:
            continue
        pairs.append((user_message, assistant_response))
        pending_user = []
    return pairs


def _iter_entry_sessions(entry: dict[str, Any], *, oracle_only: bool) -> list[tuple[int, str, Any]]:
    allowed_indices: set[int] | None = None
    if oracle_only:
        answer_ids = {
            str(value).strip()
            for value in (entry.get("answer_session_ids") or [])
            if str(value).strip()
        }
        haystack_ids = [str(value).strip() for value in (entry.get("haystack_session_ids") or [])]
        allowed_indices = {idx for idx, session_id in enumerate(haystack_ids, start=1) if session_id in answer_ids}
    items: list[tuple[int, str, Any]] = []
    for idx, (session_date, session_entry) in enumerate(
        zip(entry.get("haystack_dates") or [], entry.get("haystack_sessions") or []),
        start=1,
    ):
        if allowed_indices is not None and idx not in allowed_indices:
            continue
        items.append((idx, str(session_date or ""), session_entry))
    return items


def _session_event_timestamp(session_date: str, *, offset_minutes: int) -> str | None:
    raw = str(session_date or "").strip()
    if not raw:
        return None
    for fmt in (
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%Y-%m-%d %H:%M",
        "%Y/%m/%d %H:%M",
        "%Y-%m-%d (%a) %H:%M",
        "%Y/%m/%d (%a) %H:%M",
    ):
        try:
            base = datetime.strptime(raw, fmt).replace(tzinfo=timezone.utc)
            stamped = base + timedelta(hours=12, minutes=offset_minutes)
            if "%H:%M" in fmt:
                stamped = base + timedelta(minutes=offset_minutes)
            return stamped.isoformat()
        except ValueError:
            continue
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return (parsed + timedelta(minutes=offset_minutes)).isoformat()


def _question_terms(question: str) -> set[str]:
    return {
        token.strip(".,!?;:()[]{}\"'").lower()
        for token in str(question or "").split()
        if len(token.strip(".,!?;:()[]{}\"'")) >= 4
    }


def _build_config(mode: str) -> dict[str, Any]:
    memory_cfg: dict[str, Any] = {
        "memory_enabled": mode == "builtin_only",
        "user_profile_enabled": mode == "builtin_only",
    }
    if mode == "core2":
        memory_cfg["provider"] = "core2"
    return {
        "model": DEFAULT_BENCHMARK_MODEL,
        "providers": {},
        "toolsets": [],
        "agent": {"max_turns": 4},
        "memory": memory_cfg,
    }


def _benchmark_namespace(entry: dict[str, Any]) -> str:
    # LongMemEval exercises user-history recall through Hermes, so benchmark
    # seeds should land in the personal memory lane rather than in library-only
    # space that personal recall routes may intentionally exclude.
    return "personal"


def _seed_builtin_memory(home: Path, entry: dict[str, Any], *, oracle_only: bool) -> int:
    from tools.memory_tool import MemoryStore
    from tools import memory_tool as memory_tool_module

    saved = 0
    memory_dir = home / "memories"
    memory_dir.mkdir(parents=True, exist_ok=True)
    original_dir = memory_tool_module.MEMORY_DIR
    memory_tool_module.MEMORY_DIR = memory_dir
    try:
        store = MemoryStore(memory_char_limit=6000, user_char_limit=4000)
        store.load_from_disk()
        for idx, session_date, session_entry in _iter_entry_sessions(entry, oracle_only=oracle_only):
            result = store.add("memory", _flatten_session(session_date, session_entry)[:1800])
            if not result.get("success"):
                break
            saved += 1
    finally:
        memory_tool_module.MEMORY_DIR = original_dir
    return saved


def _seed_core2_kernel(home: Path, entry: dict[str, Any], *, oracle_only: bool) -> int:
    from plugins.memory import load_memory_provider

    provider = load_memory_provider("core2")
    if provider is None:
        raise RuntimeError("Core2 memory provider is unavailable.")
    provider.initialize(f"seed-{entry.get('question_id')}", hermes_home=str(home), platform="cli")
    runtime = provider.runtime
    assert runtime is not None

    emitted = 0
    question_id = str(entry.get("question_id") or "")
    namespace = _benchmark_namespace(entry)
    try:
        for idx, session_date, session_entry in _iter_entry_sessions(entry, oracle_only=oracle_only):
            session_stamp = _session_event_timestamp(session_date, offset_minutes=0)
            runtime.ingest_note(
                _flatten_session(session_date, session_entry),
                title=f"LongMemEval session {idx}",
                namespace=namespace,
                risk_class="standard",
                language="en",
                effective_from=session_stamp,
                source_type="document_source",
                metadata={
                    "dataset": "LongMemEval-S",
                    "question_id": question_id,
                    "session_index": idx,
                    "session_date": session_date,
                },
            )
            emitted += 1
            for turn_index, (user_message, assistant_response) in enumerate(_iter_session_exchange_pairs(session_entry), start=1):
                timestamp = _session_event_timestamp(session_date, offset_minutes=turn_index)
                runtime.ingest_turn(user_message, assistant_response, session_id=f"longmemeval:{question_id}:session:{idx}")
                runtime.ingest_note(
                    f"User asked: {user_message}\nAssistant answered: {assistant_response}",
                    title=f"LongMemEval turn {idx}.{turn_index}",
                    namespace=namespace,
                    risk_class="standard",
                    language="en",
                    effective_from=timestamp,
                    source_type="document_source",
                    metadata={
                        "dataset": "LongMemEval-S",
                        "question_id": question_id,
                        "session_index": idx,
                        "turn_index": turn_index,
                    },
                )
                emitted += 1
    finally:
        provider.shutdown()
    return emitted


def _naive_baseline_messages(entry: dict[str, Any]) -> list[dict[str, Any]]:
    blocks = [_flatten_session(str(session_date or ""), session_entry) for session_date, session_entry in zip(entry.get("haystack_dates") or [], entry.get("haystack_sessions") or [])]
    return [
        {"role": "system", "content": "\n\n".join(blocks)},
        {"role": "user", "content": str(entry.get("question") or "")},
    ]


def _safe_json_loads(value: Any) -> Dict[str, Any] | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        payload = json.loads(value)
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _packet_contains_answer(packet: Dict[str, Any] | None, answer: str) -> bool:
    if not packet or not answer:
        return False
    answer_text = answer.casefold()
    fields = [
        str(packet.get("canonical_value") or ""),
        str(packet.get("display_value") or ""),
        str(packet.get("reason") or ""),
        str(packet.get("abstain_reason") or ""),
    ]
    for item in packet.get("items") or []:
        if isinstance(item, dict):
            fields.extend(
                [
                    str(item.get("title") or ""),
                    str(item.get("content") or ""),
                    str(item.get("snippet") or ""),
                ]
            )
    haystack = " ".join(fields).casefold()
    return answer_text in haystack


def _failure_pattern(
    *,
    passed: bool,
    judge: str,
    recall_packet: Dict[str, Any] | None,
    evidence_contains_answer: bool,
    prompt_contains_question_terms: bool,
    response: str,
    promptless_authoritative: bool = False,
    local_comparator: str = "",
    latency_exceeded: bool = False,
) -> str:
    if latency_exceeded:
        return "latency_abort"
    if passed:
        return "passed"
    if str(judge or "").strip().lower() == "unknown":
        if promptless_authoritative:
            return "judge_artifact"
        return "prompt_miss"
    if promptless_authoritative and str(local_comparator or "").strip().lower() == "no":
        return "handoff_format_miss"
    normalized = _normalize_answer_text(response)
    response_abstained = any(hint in normalized for hint in _ABSTENTION_HINTS)
    if recall_packet is None:
        return "prompt_miss"
    if evidence_contains_answer:
        return "grounding_handoff_miss"
    if recall_packet.get("abstained"):
        return "memory_abstention"
    if response_abstained:
        return "abstention"
    if not prompt_contains_question_terms:
        return "prompt_miss"
    return "retrieval_or_reasoning_miss"


def _failure_family(pattern: str) -> str:
    normalized = str(pattern or "").strip().lower()
    if normalized == "passed":
        return "passed"
    if normalized == "latency_abort":
        return "latency"
    if normalized in {"prompt_miss", "grounding_handoff_miss", "abstention", "handoff_format_miss"}:
        return "handoff_format"
    if normalized == "judge_artifact":
        return "judge_artifact"
    if normalized == "memory_abstention":
        return "kernel_correctness"
    return "unknown"


PIPELINE_ATTRIBUTION_LABELS = (
    "passed",
    "retrieval_failure",
    "sufficiency_failure",
    "reasoning_failure",
    "delivery_surface_failure",
    "judge_false_positive",
    "judge_false_negative",
    "latency_abort",
)

PIPELINE_ATTRIBUTION_STAGE_BUCKETS = (
    "passed",
    "retrieval",
    "sufficiency",
    "reasoning_delivery",
    "judge_like",
    "latency",
)


def _normalized_route_notes(item: Dict[str, Any]) -> List[str]:
    raw = item.get("route_notes") or []
    if not isinstance(raw, list):
        return []
    return [str(note).strip() for note in raw if str(note).strip()]


def _judge_false_positive(item: Dict[str, Any]) -> bool:
    if not bool(item.get("passed")):
        return False
    if bool(item.get("evidence_contains_answer")) or bool(item.get("answer_surface_hit")):
        return False
    if bool(item.get("recall_abstained")):
        return False
    if int(item.get("evidence_item_count") or 0) <= 0:
        return False
    judge = str(item.get("judge") or "").strip().lower()
    return judge.startswith("yes")


def build_pipeline_attribution_record(result: Dict[str, Any]) -> Dict[str, Any]:
    item = dict(result or {})
    failure_pattern = str(item.get("failure_pattern") or "").strip().lower()
    route_notes = _normalized_route_notes(item)
    evidence_contains_answer = bool(item.get("evidence_contains_answer"))
    answer_surface_hit = bool(item.get("answer_surface_hit"))
    recall_abstained = bool(item.get("recall_abstained"))
    passed = bool(item.get("passed"))

    if failure_pattern == "latency_abort":
        stage_bucket = "latency"
        attribution_label = "latency_abort"
        short_reason = "latency threshold exceeded before a stable diagnostic outcome"
    elif _judge_false_positive(item):
        stage_bucket = "judge_like"
        attribution_label = "judge_false_positive"
        short_reason = "judge accepted an answer without grounded evidence or authoritative surface support"
    elif failure_pattern == "judge_artifact":
        stage_bucket = "judge_like"
        attribution_label = "judge_false_negative"
        short_reason = "judge-like rejection despite promptless authoritative support"
    elif passed:
        stage_bucket = "passed"
        attribution_label = "passed"
        short_reason = "case passed"
    elif recall_abstained or int(item.get("evidence_item_count") or 0) <= 0 or not evidence_contains_answer:
        stage_bucket = "retrieval"
        attribution_label = "retrieval_failure"
        short_reason = "retrieval did not surface answer-bearing evidence"
    elif not answer_surface_hit:
        stage_bucket = "sufficiency"
        attribution_label = "sufficiency_failure"
        short_reason = "evidence was present but did not produce a sufficient authoritative answer surface"
    elif failure_pattern in {"prompt_miss", "grounding_handoff_miss", "handoff_format_miss"}:
        stage_bucket = "reasoning_delivery"
        attribution_label = "delivery_surface_failure"
        short_reason = "downstream delivery or handoff failed after grounded evidence was available"
    else:
        stage_bucket = "reasoning_delivery"
        attribution_label = "reasoning_failure"
        short_reason = "downstream reasoning or execution failed after grounded evidence retrieval"

    return {
        "question_id": str(item.get("question_id") or "").strip(),
        "question_type": str(item.get("question_type") or "unknown"),
        "passed": passed,
        "judge": str(item.get("judge") or "").strip(),
        "failure_pattern": failure_pattern,
        "attribution_label": attribution_label,
        "stage_bucket": stage_bucket,
        "recall_route_family": str(item.get("recall_route_family") or ""),
        "recall_query_family": str(item.get("recall_query_family") or ""),
        "route_notes": route_notes,
        "evidence_item_count": int(item.get("evidence_item_count") or 0),
        "evidence_contains_answer": evidence_contains_answer,
        "answer_surface_hit": answer_surface_hit,
        "answer_surface_mode": str(item.get("answer_surface_mode") or ""),
        "answer_surface_family": str(item.get("answer_surface_family") or ""),
        "promptless_authoritative": bool(item.get("promptless_authoritative")),
        "selector_engaged": "hybrid_budgeted_selector" in route_notes,
        "constituent_expanded": "hybrid_constituent_expand" in route_notes,
        "aggregation_safety_abstained": "hybrid_aggregation_safety_abstain" in route_notes,
        "recall_abstained": recall_abstained,
        "support_confidence": str(item.get("support_confidence") or ""),
        "temporal_confidence": str(item.get("temporal_confidence") or ""),
        "resolution_confidence": str(item.get("resolution_confidence") or ""),
        "identity_confidence": str(item.get("identity_confidence") or ""),
        "local_comparator": str(item.get("local_comparator") or ""),
        "local_comparator_reason": str(item.get("local_comparator_reason") or ""),
        "sufficient_retrieval": bool(evidence_contains_answer and answer_surface_hit),
        "judge_like": stage_bucket == "judge_like",
        "short_reason": short_reason,
    }


def build_pipeline_attribution_artifact(report: Dict[str, Any]) -> Dict[str, Any]:
    results = [dict(item or {}) for item in list(report.get("results") or [])]
    records = [build_pipeline_attribution_record(item) for item in results]
    total = len(records)
    label_counts = dict(Counter(str(item.get("attribution_label") or "") for item in records))
    stage_counts = dict(Counter(str(item.get("stage_bucket") or "") for item in records))
    evidence_present = sum(1 for item in records if item.get("evidence_contains_answer"))
    sufficient_retrieval = sum(1 for item in records if item.get("sufficient_retrieval"))
    answer_surface_hits = sum(1 for item in records if item.get("answer_surface_hit"))
    selector_engaged = sum(1 for item in records if item.get("selector_engaged"))
    aggregation_safety = sum(1 for item in records if item.get("aggregation_safety_abstained"))
    judge_like = sum(1 for item in records if item.get("judge_like"))
    return {
        "schema_version": "phase15.v1",
        "labels": list(PIPELINE_ATTRIBUTION_LABELS),
        "stage_buckets": list(PIPELINE_ATTRIBUTION_STAGE_BUCKETS),
        "summary": {
            "total_cases": total,
            "label_counts": label_counts,
            "stage_counts": stage_counts,
            "evidence_present_cases": evidence_present,
            "sufficient_retrieval_cases": sufficient_retrieval,
            "answer_surface_hit_cases": answer_surface_hits,
            "selector_engaged_cases": selector_engaged,
            "aggregation_safety_abstentions": aggregation_safety,
            "judge_like_cases": judge_like,
            "evidence_present_rate": round(evidence_present / total, 4) if total else 0.0,
            "sufficient_retrieval_rate": round(sufficient_retrieval / total, 4) if total else 0.0,
            "answer_surface_hit_rate": round(answer_surface_hits / total, 4) if total else 0.0,
            "selector_engaged_rate": round(selector_engaged / total, 4) if total else 0.0,
        },
        "records": records,
    }


def select_benchmark_fast_profile(entry: dict[str, Any]) -> str:
    question = f" {str(entry.get('question') or '').strip().lower()} "
    question_type = str(entry.get("question_type") or "").strip().lower()
    question_id = str(entry.get("question_id") or "").strip().lower()
    if "_abs" in question_id:
        return "compact"
    if question_type in {"temporal-reasoning", "knowledge-update"}:
        return "supported"
    if any(hint in question for hint in _SUPPORTED_BUDGET_HINTS):
        return "supported"
    return "compact"


def run_core2_longmemeval_generation(
    *,
    entry: dict[str, Any],
    mode: str,
    model: str,
    base_url: str,
    api_key: str,
    provider: str = DEFAULT_BENCHMARK_PROVIDER,
    oracle_seed: bool = False,
    max_iterations: int = 4,
    benchmark_fast: bool = True,
) -> Core2LongMemEvalRunResult:
    import run_agent
    from agent.memory_manager import MemoryManager

    if mode not in {"core2", "builtin_only"}:
        raise ValueError(f"Unsupported mode: {mode}")

    with TemporaryDirectory(prefix=f"core2-longmemeval-run-{mode}-") as tmp_dir:
        total_started = time.perf_counter()
        home = Path(tmp_dir)
        (home / "memories").mkdir(parents=True, exist_ok=True)
        config = _build_config(mode)
        (home / "config.yaml").write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
        budget_profile = select_benchmark_fast_profile(entry) if benchmark_fast else "full"
        budget_cfg = BENCHMARK_FAST_PROFILES.get(budget_profile, BENCHMARK_FAST_PROFILES["compact"])

        seed_started = time.perf_counter()
        if mode == "core2":
            seeded_entries = _seed_core2_kernel(home, entry, oracle_only=oracle_seed)
        else:
            seeded_entries = _seed_builtin_memory(home, entry, oracle_only=oracle_seed)
        seed_seconds = time.perf_counter() - seed_started

        captured: dict[str, Any] = {}
        api_seconds = 0.0
        tool_seconds = 0.0
        tool_events: List[Dict[str, Any]] = []
        judge_seconds = 0.0

        original_interruptible = run_agent.AIAgent._interruptible_api_call
        original_streaming = getattr(run_agent.AIAgent, "_interruptible_streaming_api_call", None)
        original_memory_handle = MemoryManager.handle_tool_call

        def _capture_then_call(agent_self, api_kwargs: dict[str, Any]):
            nonlocal api_seconds
            messages = list(api_kwargs.get("messages") or [])
            captured["prompt"] = "\n\n".join(str(message.get("content") or "") for message in messages)
            call_started = time.perf_counter()
            try:
                return original_interruptible(agent_self, api_kwargs)
            finally:
                api_seconds += time.perf_counter() - call_started

        def _capture_then_stream(agent_self, api_kwargs: dict[str, Any], on_first_delta=None):
            nonlocal api_seconds
            messages = list(api_kwargs.get("messages") or [])
            captured["prompt"] = "\n\n".join(str(message.get("content") or "") for message in messages)
            call_started = time.perf_counter()
            try:
                if benchmark_fast:
                    if on_first_delta:
                        on_first_delta()
                    return original_interruptible(agent_self, api_kwargs)
                return original_streaming(agent_self, api_kwargs, on_first_delta=on_first_delta)
            finally:
                api_seconds += time.perf_counter() - call_started

        def _timed_memory_tool(self, tool_name: str, args: Dict[str, Any], **kwargs):
            nonlocal tool_seconds
            started = time.perf_counter()
            result = original_memory_handle(self, tool_name, args, **kwargs)
            duration = time.perf_counter() - started
            tool_seconds += duration
            parsed = _safe_json_loads(result)
            tool_events.append(
                {
                    "tool_name": tool_name,
                    "args": dict(args or {}),
                    "duration_seconds": round(duration, 6),
                    "parsed_result": parsed or {},
                }
            )
            return result

        patchers = [
            patch.dict(
                os.environ,
                {
                    "HERMES_HOME": str(home),
                    "CORE2_TOOL_BUDGET_PROFILE": str(
                        budget_cfg.get("tool_budget_profile", "compact") if benchmark_fast else "full"
                    ),
                    "CORE2_TOOL_PAYLOAD_MODE": str(
                        budget_cfg.get("tool_payload_mode", "default") if benchmark_fast else "default"
                    ),
                },
            ),
            patch("run_agent._hermes_home", home),
            patch("run_agent.get_tool_definitions", return_value=[]),
            patch("run_agent.check_toolset_requirements", return_value={}),
            patch("hermes_cli.config.load_config", return_value=config),
            patch.object(run_agent.AIAgent, "_interruptible_api_call", _capture_then_call),
            patch.object(MemoryManager, "handle_tool_call", _timed_memory_tool),
        ]
        if original_streaming is not None:
            patchers.append(patch.object(run_agent.AIAgent, "_interruptible_streaming_api_call", _capture_then_stream))

        with ExitStack() as stack:
            for patcher in patchers:
                stack.enter_context(patcher)
            agent = run_agent.AIAgent(
                api_key=api_key,
                model=model,
                provider=provider,
                base_url=base_url,
                quiet_mode=True,
                skip_context_files=True,
                skip_memory=False,
                session_id=f"longmemeval-{mode}-{entry['question_id']}",
                persist_session=False,
                max_iterations=int(budget_cfg["max_iterations"]) if benchmark_fast else max_iterations,
                ephemeral_system_prompt=str(budget_cfg["ephemeral_system_prompt"]) if benchmark_fast else None,
                max_tokens=int(budget_cfg["max_tokens"]) if benchmark_fast else None,
            )
            agent._cleanup_task_resources = lambda task_id: None
            agent._persist_session = lambda messages, history=None: None
            agent._save_trajectory = lambda messages, user_message, completed: None
            agent._save_session_log = lambda messages: None
            conversation_started = time.perf_counter()
            raw_result = agent.run_conversation(str(entry["question"]))
            conversation_seconds = time.perf_counter() - conversation_started
            # Some provider failure paths return a partial failure dict without
            # final_response. Normalize that shape so the benchmark records an
            # honest failed run instead of crashing its own harness.
            if isinstance(raw_result, dict):
                result = dict(raw_result)
            else:
                result = {"final_response": str(raw_result or "")}

        hypothesis = str(result.get("final_response") or "").strip()
        prompt_excerpt = str(captured.get("prompt") or "")[:2400]
        answer = str(entry.get("answer") or "").strip()
        terms = _question_terms(str(entry.get("question") or ""))
        prompt_blob = str(captured.get("prompt") or "")
        prompt_terms = prompt_blob.lower()
        prompt_contains_question_terms = bool(terms) and any(term in prompt_terms for term in terms)
        prompt_contains_answer = bool(answer) and answer.lower() in prompt_blob.lower()
        recall_event = next((event for event in reversed(tool_events) if event["tool_name"] == "core2_recall"), None)
        recall_packet = dict(recall_event.get("parsed_result") or {}) if recall_event else None
        if recall_packet is None and mode == "core2":
            try:
                runtime = Core2Runtime(str(home / "core2" / "core2.db"))
                runtime.initialize(f"inspect-{entry['question_id']}")
                recall_packet = runtime.recall(
                    str(entry["question"]),
                    mode="source_supported",
                    operator=None,
                    risk_class="standard",
                    max_items=6,
                ).to_dict(compact=True, tool_budget_profile=budget_cfg["tool_budget_profile"], tool_payload_mode=budget_cfg["tool_payload_mode"])
                runtime.shutdown()
            except Exception:
                recall_packet = None
        evidence_contains_answer = _packet_contains_answer(recall_packet, answer)
        evidence_item_count = len(recall_packet.get("items") or []) if recall_packet else 0
        recall_abstained = bool(recall_packet.get("abstained")) if recall_packet else False
        recall_route_family = str(recall_packet.get("route_family") or "")
        recall_query_family = str(recall_packet.get("query_family") or "")
        route_notes = [str(note).strip() for note in list((recall_packet.get("route_plan") or {}).get("notes") or []) if str(note).strip()]
        answer_surface = dict(recall_packet.get("answer_surface") or {}) if recall_packet else {}
        answer_surface_mode = str(answer_surface.get("mode") or "").strip().lower()
        answer_surface_family = str(answer_surface.get("family") or "").strip()
        answer_surface_hit = bool(answer_surface) and answer_surface_mode in {"fact_only", "fact_plus_summary"} and bool(
            str(answer_surface.get("text") or "").strip()
        )
        promptless_authoritative = answer_surface_hit and int(result.get("api_calls") or 0) == 0
        support_confidence = str(recall_packet.get("support_confidence") or "") if recall_packet else ""
        temporal_confidence = str(recall_packet.get("temporal_confidence") or "") if recall_packet else ""
        resolution_confidence = str(recall_packet.get("resolution_confidence") or "") if recall_packet else ""
        identity_confidence = str(recall_packet.get("identity_confidence") or "") if recall_packet else ""

        prompt_tokens_estimate = estimate_text_tokens(prompt_excerpt)
        baseline_replay_tokens_estimate = estimate_message_tokens(_naive_baseline_messages(entry))
        estimated_token_savings = max(0, baseline_replay_tokens_estimate - prompt_tokens_estimate)
        estimated_savings_ratio = (
            estimated_token_savings / baseline_replay_tokens_estimate
            if baseline_replay_tokens_estimate
            else 0.0
        )

        normalized_answer = _normalize_answer_text(answer)
        normalized_hypothesis = _normalize_answer_text(hypothesis)
        local_comparator = "not_applicable"
        local_comparator_reason = "not_evaluated"
        if normalized_answer and normalized_answer == normalized_hypothesis:
            judge = "yes_exact_match"
        elif _response_contains_answer(hypothesis, answer):
            judge = "yes_answer_contained"
        elif promptless_authoritative:
            local_comparator, local_comparator_reason = _canonical_local_comparator(
                question_type=str(entry.get("question_type") or ""),
                answer=answer,
                hypothesis=hypothesis,
                answer_surface=answer_surface,
                promptless_authoritative=promptless_authoritative,
            )
            if local_comparator == "yes":
                judge = "yes_local_comparator"
            elif local_comparator == "no":
                judge = "no_local_comparator"
            else:
                judge_started = time.perf_counter()
                judge = _judge_yes_no(
                    base_url=base_url,
                    api_key=api_key,
                    model=DEFAULT_JUDGE_MODEL,
                    prompt=get_anscheck_prompt(
                        str(entry.get("question_type") or ""),
                        str(entry.get("question") or ""),
                        answer,
                        hypothesis,
                        abstention="_abs" in str(entry.get("question_id") or ""),
                    ),
                )
                judge_seconds = time.perf_counter() - judge_started
        else:
            judge_started = time.perf_counter()
            judge = _judge_yes_no(
                base_url=base_url,
                api_key=api_key,
                model=DEFAULT_JUDGE_MODEL,
                prompt=get_anscheck_prompt(
                    str(entry.get("question_type") or ""),
                    str(entry.get("question") or ""),
                    answer,
                    hypothesis,
                    abstention="_abs" in str(entry.get("question_id") or ""),
                ),
            )
            judge_seconds = time.perf_counter() - judge_started
        passed = judge.startswith("yes")
        total_wall_seconds = time.perf_counter() - total_started

        return Core2LongMemEvalRunResult(
            question_id=str(entry["question_id"]),
            question_type=str(entry.get("question_type") or "unknown"),
            passed=passed,
            judge=judge,
            hypothesis=hypothesis,
            answer=answer,
            prompt_excerpt=prompt_excerpt,
            prompt_tokens_estimate=prompt_tokens_estimate,
            baseline_replay_tokens_estimate=baseline_replay_tokens_estimate,
            estimated_token_savings=estimated_token_savings,
            estimated_savings_ratio=estimated_savings_ratio,
            seeded_core2_entries=seeded_entries,
            seed_seconds=seed_seconds,
            tool_seconds=tool_seconds,
            conversation_seconds=conversation_seconds,
            api_seconds=api_seconds,
            judge_seconds=judge_seconds,
            total_wall_seconds=total_wall_seconds,
            kernel_local_seconds=max(0.0, conversation_seconds - api_seconds - tool_seconds),
            prompt_tokens=int(result.get("prompt_tokens") or 0),
            completion_tokens=int(result.get("completion_tokens") or 0),
            total_tokens=int(result.get("total_tokens") or 0),
            api_calls=int(result.get("api_calls") or 0),
            provider=provider,
            base_url=base_url,
            model=model,
            budget_profile=budget_profile,
            failure_pattern=_failure_pattern(
                passed=passed,
                judge=judge,
                recall_packet=recall_packet,
                evidence_contains_answer=evidence_contains_answer,
                prompt_contains_question_terms=prompt_contains_question_terms,
                response=hypothesis,
                promptless_authoritative=promptless_authoritative,
                local_comparator=local_comparator,
            ),
            recall_abstained=recall_abstained,
            recall_route_family=recall_route_family,
            recall_query_family=recall_query_family,
            evidence_item_count=evidence_item_count,
            evidence_contains_answer=evidence_contains_answer,
            memory_tool_calls=len(tool_events),
            prompt_contains_answer=prompt_contains_answer,
            prompt_contains_question_terms=prompt_contains_question_terms,
            answer_surface_mode=answer_surface_mode,
            answer_surface_family=answer_surface_family,
            answer_surface_hit=answer_surface_hit,
            promptless_authoritative=promptless_authoritative,
            local_comparator=local_comparator,
            local_comparator_reason=local_comparator_reason,
            route_notes=route_notes,
            support_confidence=support_confidence,
            temporal_confidence=temporal_confidence,
            resolution_confidence=resolution_confidence,
            identity_confidence=identity_confidence,
        )


def run_core2_longmemeval_subset(
    *,
    sample_size: int,
    seed: int,
    mode: str,
    model: str,
    base_url: str,
    api_key: str,
    provider: str = DEFAULT_BENCHMARK_PROVIDER,
    oracle_seed: bool = False,
    stop_on_bad_start: bool = True,
    question_ids: Sequence[str] | None = None,
    benchmark_fast: bool = True,
    max_conversation_seconds: float = 0.0,
    max_total_wall_seconds: float = 0.0,
) -> Dict[str, Any]:
    entries = json.loads(DEFAULT_DATASET.read_text(encoding="utf-8"))
    if question_ids:
        wanted = [str(value).strip() for value in question_ids if str(value).strip()]
        by_id = {str(entry.get("question_id") or ""): entry for entry in entries}
        sample = [by_id[qid] for qid in wanted if qid in by_id]
    else:
        sample = stratified_sample(entries, sample_size, seed)
    results: list[dict[str, Any]] = []
    failure_counter: Counter[str] = Counter()
    budget_profile_counter: Counter[str] = Counter()
    answer_surface_mode_counter: Counter[str] = Counter()
    started = time.perf_counter()
    aborted_early = False
    aborted_reason = ""

    for idx, entry in enumerate(sample, start=1):
        run = run_core2_longmemeval_generation(
            entry=entry,
            mode=mode,
            model=model,
            base_url=base_url,
            api_key=api_key,
            provider=provider,
            oracle_seed=oracle_seed,
            benchmark_fast=benchmark_fast,
        )
        payload = {"sample_index": idx, **run.as_dict()}
        latency_exceeded = (
            (max_conversation_seconds > 0 and payload["conversation_seconds"] > max_conversation_seconds)
            or (max_total_wall_seconds > 0 and payload["total_wall_seconds"] > max_total_wall_seconds)
        )
        if latency_exceeded:
            payload["failure_pattern"] = "latency_abort"
        results.append(payload)
        failure_counter[str(payload["failure_pattern"])] += 1
        budget_profile_counter[str(payload.get("budget_profile") or "")] += 1
        answer_surface_mode_counter[str(payload.get("answer_surface_mode") or "")] += 1

        if latency_exceeded:
            aborted_early = True
            aborted_reason = "latency_threshold_exceeded"
            break

        if stop_on_bad_start and idx >= 5:
            passed = sum(1 for item in results if item["passed"])
            if passed == 0:
                aborted_early = True
                aborted_reason = "bad_start_zero_passes"
                break

    total = len(results)
    passed = sum(1 for item in results if item["passed"])
    summary = {
        "dataset": str(DEFAULT_DATASET),
        "sample_size_requested": sample_size,
        "sample_size_completed": total,
        "mode": mode,
        "model": model,
        "provider": provider,
        "base_url": base_url,
        "benchmark_fast": benchmark_fast,
        "passed": passed,
        "total": total,
        "pass_rate": (passed / total) if total else 0.0,
        "aborted_early": aborted_early,
        "aborted_reason": aborted_reason,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "avg_seed_seconds": round(sum(item["seed_seconds"] for item in results) / total, 3) if total else 0.0,
        "avg_tool_seconds": round(sum(item["tool_seconds"] for item in results) / total, 3) if total else 0.0,
        "avg_conversation_seconds": round(sum(item["conversation_seconds"] for item in results) / total, 3) if total else 0.0,
        "avg_api_seconds": round(sum(item["api_seconds"] for item in results) / total, 3) if total else 0.0,
        "avg_judge_seconds": round(sum(item["judge_seconds"] for item in results) / total, 3) if total else 0.0,
        "avg_total_wall_seconds": round(sum(item["total_wall_seconds"] for item in results) / total, 3) if total else 0.0,
        "avg_kernel_local_seconds": round(sum(item["kernel_local_seconds"] for item in results) / total, 3) if total else 0.0,
        "avg_memory_tool_calls": round(sum(item["memory_tool_calls"] for item in results) / total, 2) if total else 0.0,
        "avg_evidence_item_count": round(sum(item["evidence_item_count"] for item in results) / total, 2) if total else 0.0,
        "promptless_authoritative_cases": sum(1 for item in results if item.get("promptless_authoritative")),
        "answer_surface_hits": sum(1 for item in results if item.get("answer_surface_hit")),
        "answer_surface_hit_rate": round(sum(1 for item in results if item.get("answer_surface_hit")) / total, 4) if total else 0.0,
        "avg_prompt_tokens": round(sum(item["prompt_tokens"] for item in results) / total, 1) if total else 0.0,
        "avg_completion_tokens": round(sum(item["completion_tokens"] for item in results) / total, 1) if total else 0.0,
        "avg_total_tokens": round(sum(item["total_tokens"] for item in results) / total, 1) if total else 0.0,
        "avg_prompt_tokens_estimate": round(sum(item["prompt_tokens_estimate"] for item in results) / total, 1) if total else 0.0,
        "avg_baseline_replay_tokens_estimate": round(sum(item["baseline_replay_tokens_estimate"] for item in results) / total, 1) if total else 0.0,
        "avg_estimated_savings_ratio": round(sum(item["estimated_savings_ratio"] for item in results) / total, 4) if total else 0.0,
        "failure_patterns": dict(failure_counter),
        "budget_profiles": dict(budget_profile_counter),
        "answer_surface_modes": {key: value for key, value in dict(answer_surface_mode_counter).items() if key},
        "local_comparator": dict(Counter(str(item.get("local_comparator") or "") for item in results if str(item.get("local_comparator") or ""))),
    }
    return {"summary": summary, "results": results}


def build_gate_status_artifact(report: Dict[str, Any]) -> Dict[str, Any]:
    summary = dict(report.get("summary") or {})
    results = list(report.get("results") or [])
    failure_patterns = dict(summary.get("failure_patterns") or {})
    failure_families: Dict[str, int] = {}
    for pattern, count in failure_patterns.items():
        family = _failure_family(pattern)
        if family == "passed":
            continue
        failure_families[family] = failure_families.get(family, 0) + int(count)
    dominant_failure = ""
    dominant_count = 0
    for pattern, count in failure_patterns.items():
        if pattern == "passed":
            continue
        if int(count) > dominant_count:
            dominant_failure = str(pattern)
            dominant_count = int(count)
    dominant_family = ""
    dominant_family_count = 0
    for family, count in failure_families.items():
        if int(count) > dominant_family_count:
            dominant_family = str(family)
            dominant_family_count = int(count)
    current_blocker = dominant_family or (dominant_failure if dominant_failure else "unknown")
    return {
        "status": "green" if summary.get("aborted_early") is False and float(summary.get("pass_rate") or 0.0) >= 1.0 else "needs_work",
        "classification_mode": "fail_closed",
        "sample_size_requested": int(summary.get("sample_size_requested") or 0),
        "sample_size_completed": int(summary.get("sample_size_completed") or 0),
        "pass_rate": float(summary.get("pass_rate") or 0.0),
        "aborted_early": bool(summary.get("aborted_early")),
        "aborted_reason": str(summary.get("aborted_reason") or ""),
        "current_blocker": current_blocker,
        "dominant_failure_pattern": dominant_failure,
        "dominant_failure_family": dominant_family,
        "failure_patterns": failure_patterns,
        "failure_families": failure_families,
        "answer_surface_hit_rate": float(summary.get("answer_surface_hit_rate") or 0.0),
        "answer_surface_modes": dict(summary.get("answer_surface_modes") or {}),
        "promptless_authoritative_cases": int(summary.get("promptless_authoritative_cases") or 0),
        "local_comparator": dict(summary.get("local_comparator") or {}),
        "authoritative_status_source": "04.1-GATE-STATUS.json",
        "avg_total_wall_seconds": float(summary.get("avg_total_wall_seconds") or 0.0),
        "avg_conversation_seconds": float(summary.get("avg_conversation_seconds") or 0.0),
        "avg_api_seconds": float(summary.get("avg_api_seconds") or 0.0),
        "latest_question_ids": [str(item.get("question_id") or "") for item in results],
        "canary_question_ids": list(DEFAULT_CANARY_QUESTION_IDS),
        "canary_size": len(DEFAULT_CANARY_QUESTION_IDS),
    }


__all__ = [
    "PIPELINE_ATTRIBUTION_LABELS",
    "PIPELINE_ATTRIBUTION_STAGE_BUCKETS",
    "build_gate_status_artifact",
    "build_pipeline_attribution_artifact",
    "build_pipeline_attribution_record",
    "DEFAULT_BENCHMARK_BASE_URL",
    "DEFAULT_BENCHMARK_MODEL",
    "DEFAULT_CANARY_QUESTION_IDS",
    "DEFAULT_BENCHMARK_PROVIDER",
    "DEFAULT_DATASET",
    "DEFAULT_JUDGE_MODEL",
    "Core2LongMemEvalRunResult",
    "get_anscheck_prompt",
    "run_core2_longmemeval_generation",
    "run_core2_longmemeval_subset",
    "stratified_sample",
]
