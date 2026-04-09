from __future__ import annotations

from agent.kernel_memory import KernelMemoryConfig, KernelMemoryStore
from agent.kernel_memory_semantic_policy import (
    classify_polarity,
    extract_contraindication_predicates,
    extract_contraindications,
    infer_applicability_scope,
    infer_misapply_risk,
)


def test_semantic_policy_extracts_structured_polarity_and_contraindications():
    text = "Only promise reminders when a scheduler tool is actually available."

    polarity = classify_polarity(text=text)
    contraindications = extract_contraindications(text=text)
    predicates = extract_contraindication_predicates(text=text)
    applicability_scope = infer_applicability_scope(text=text, metadata={"memory_class": "project_task"})
    risk = infer_misapply_risk(text=text)

    assert polarity == "neutral"
    assert contraindications == ["a scheduler tool is actually available"]
    assert any(predicate.get("type") == "requires_capability" for predicate in predicates)
    assert applicability_scope["domain"] == "scheduling"
    assert applicability_scope["memory_class"] == "project_task"
    assert risk == "high"


def test_claim_reingest_increments_derivation_count_and_activation(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel", namespace="bestie")
    )

    first = store.ingest_claim(
        claim_type="operational_rule",
        content="Only promise reminders when a scheduler tool is actually available.",
    )
    second = store.ingest_claim(
        claim_type="operational_rule",
        content="Only promise reminders when a scheduler tool is actually available.",
    )

    assert first["id"] == second["id"]
    assert second["derivation_count"] == 2
    assert second["activation_state"] in {"provisional", "fading", "active_warm", "active_hot"}
    assert second["polarity"] == "neutral"
    assert second["contraindications"]
    assert second["contraindication_predicates"]
    assert second["risk_if_misapplied"] == "high"


def test_explicit_user_memory_starts_outside_provisional_lane(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel", namespace="bestie")
    )

    record = store.ingest_claim(
        claim_type="user_preference",
        content="Tomi prefers direct exact answers.",
        metadata={"speaker_role": "user", "authority_class": "user_explicit"},
    )

    assert record["activation_state"] in {"fading", "active_warm", "active_hot"}
    assert record["activation_state"] != "provisional"


def test_curated_retrieval_prefers_reinforced_record(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel", namespace="bestie")
    )
    weak = store.materialize_curated_memory(
        title="One-off reminder note",
        summary="Only promise reminders when a scheduler tool is actually available.",
    )
    strong = store.materialize_curated_memory(
        title="Scheduler rule",
        summary="Only promise reminders when a scheduler tool is actually available.",
        metadata={"memory_class": "project_task"},
    )
    store.materialize_curated_memory(
        title="Unrelated",
        summary="Orbital mechanics notes belong elsewhere.",
    )
    store.materialize_curated_memory(
        title="Scheduler rule",
        summary="Only promise reminders when a scheduler tool is actually available.",
        metadata={"memory_class": "project_task"},
    )

    result = store.retrieve_curated_context(
        "scheduler rule for reminders",
        max_records=2,
        max_chars=600,
    )

    assert result["items"]
    assert result["items"][0]["id"] == strong["id"]
    assert result["items"][0]["derivation_count"] == 2
    assert weak["id"] != strong["id"]


def test_low_support_claim_stays_provisional_until_directly_targeted(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel", namespace="bestie")
    )

    record = store.ingest_claim(
        claim_type="fact",
        content="Tomi once mentioned an obscure orbital mnemonic.",
    )
    assert record["activation_state"] == "provisional"

    broad_result = store.retrieve_semantic_context(
        "Tell me about orbital mechanics notes",
        max_records=4,
        max_chars=800,
    )
    targeted_result = store.retrieve_semantic_context(
        "What was the obscure orbital mnemonic Tomi mentioned?",
        max_records=4,
        max_chars=800,
    )

    assert all(item["id"] != record["id"] for item in broad_result["items"])
    assert any(item["id"] == record["id"] for item in targeted_result["items"])


def test_high_risk_contraindicated_record_is_blocked_for_matching_query(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel", namespace="bestie")
    )

    safe = store.materialize_curated_memory(
        title="Scheduling rule",
        summary="Only promise reminders when a scheduler tool is actually available.",
        metadata={"memory_class": "project_task"},
    )
    blocked = store.materialize_curated_memory(
        title="Do not over-promise reminders",
        summary="Do not promise reminders without scheduler support.",
        metadata={
            "memory_class": "project_task",
            "contraindications": ["without scheduler support"],
            "contraindication_predicates": [
                {
                    "type": "text_condition",
                    "field": "query_context",
                    "operator": "contains",
                    "value": "without scheduler support",
                }
            ],
            "risk_if_misapplied": "high",
        },
    )

    matching = store.retrieve_curated_context(
        "Can you promise reminders without scheduler support?",
        max_records=4,
        max_chars=800,
    )
    safe_query = store.retrieve_curated_context(
        "scheduler rule for reminders",
        max_records=4,
        max_chars=800,
    )

    assert all(item["id"] != blocked["id"] for item in matching["items"])
    assert any(item["id"] == safe["id"] for item in safe_query["items"])


def test_explicit_polarity_metadata_still_wins_over_conservative_inference(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel", namespace="bestie")
    )

    record = store.ingest_claim(
        claim_type="operational_rule",
        content="Always confirm the next reminder time before scheduling it.",
        metadata={"polarity": "do"},
    )

    assert record["polarity"] == "do"
