from __future__ import annotations

import json
import logging
from datetime import timedelta
from pathlib import Path

from agent.kernel_memory import KernelMemoryConfig, KernelMemoryStore
from agent.kernel_memory_events import (
    KernelMemoryEventBridge,
    KernelMemoryWorker,
    KernelMemoryWorkerLock,
    KernelMemoryWorkerStateStore,
)
from agent.kernel_memory_retrieval import KernelMemoryRetriever
from agent.kernel_memory_runtime import KernelMemoryRuntime
from agent.kernel_memory_fact_facets import extract_fact_facets
from agent.kernel_memory_tasks import KernelMemoryTaskService
from hermes_time import now as hermes_now


def test_kernel_memory_config_normalizes_string_root_dir():
    config = KernelMemoryConfig(enabled=True, root_dir="/tmp/kernel-memory-test", namespace="bestie")

    assert isinstance(config.root_dir, Path)
    assert config.root_dir == Path("/tmp/kernel-memory-test")


def test_kernel_memory_runtime_disabled_when_skip_memory(tmp_path):
    runtime = KernelMemoryRuntime.from_agent_config(
        {
            "enabled": True,
            "root_dir": str(tmp_path / "kernel"),
        },
        skip_memory=True,
        logger=logging.getLogger("test.kernel_memory_runtime"),
    )

    assert runtime.enabled is False
    assert runtime.store is None


def test_kernel_memory_runtime_captures_init_error(tmp_path):
    blocked_root = tmp_path / "blocked"
    blocked_root.write_text("not a directory", encoding="utf-8")

    runtime = KernelMemoryRuntime.from_agent_config(
        {
            "enabled": True,
            "root_dir": str(blocked_root),
        },
        skip_memory=False,
        logger=logging.getLogger("test.kernel_memory_runtime"),
    )

    assert runtime.enabled is False
    assert runtime.store is None
    assert runtime.init_error


def test_kernel_memory_runtime_normalizes_honcho_policy(tmp_path):
    runtime = KernelMemoryRuntime.from_agent_config(
        {
            "enabled": True,
            "root_dir": str(tmp_path / "kernel"),
            "honcho_system_of_record": True,
            "honcho_context_enrichment": False,
        },
        skip_memory=False,
        logger=logging.getLogger("test.kernel_memory_runtime"),
    )

    runtime.apply_honcho_policy(
        honcho_active=True,
        logger=logging.getLogger("test.kernel_memory_runtime"),
    )

    assert runtime.honcho_system_of_record is False
    assert runtime.honcho_context_enrichment_enabled is False


def test_kernel_memory_store_retrieves_bounded_curated_context(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel")
    )
    store.materialize_curated_memory(
        title="Hermes kernel roadmap",
        summary="Kernel memory retrieval should stay additive and bounded for normal chats.",
        retrieval_scope="shared",
    )
    store.materialize_curated_memory(
        title="Unrelated note",
        summary="A shopping list with coffee and bread.",
    )

    result = store.retrieve_curated_context(
        "How should Hermes kernel memory retrieval behave?",
        max_records=2,
        max_chars=220,
    )

    assert len(result["items"]) == 1
    assert result["items"][0]["title"] == "Hermes kernel roadmap"
    assert "Kernel memory retrieval should stay additive" in result["text"]
    assert len(result["text"]) <= 220


def test_kernel_memory_store_filters_memory_save_acknowledgements_from_curated_retrieval(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel")
    )
    store.materialize_curated_memory(
        title="Stable profile",
        summary="Tomi prefers concise reminders in Europe/Budapest local time.",
    )
    store.materialize_curated_memory(
        title="Conversation memory: save ack",
        summary="Elmentettem.",
        metadata={"origin": "assistant_turn_completed"},
    )

    result = store.retrieve_curated_context(
        "What should I remember about Tomi?",
        max_records=3,
        max_chars=400,
    )

    assert len(result["items"]) == 1
    assert "Elmentettem" not in result["text"]


def test_kernel_memory_store_filters_memory_tool_json_from_source_retrieval(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel")
    )
    clean = store.ingest_resource(
        resource_type="conversation_turn",
        content="USER: Hi\n\nASSISTANT: Tomi prefers concise answers.",
        metadata={"origin": "assistant_turn_completed"},
    )
    store.ingest_extract(
        resource_id=clean["id"],
        content="Tomi prefers concise answers.",
        metadata={"origin": "assistant_turn_completed"},
    )
    store.ingest_resource(
        resource_type="tool_result",
        content='{"success": true, "target": "user"}',
        metadata={"origin": "tool_result_available", "tool_name": "memory"},
    )

    result = store.retrieve_source_context(
        "concise answers",
        max_records=3,
        max_chars=400,
    )

    assert len(result["items"]) == 1
    assert '"target": "user"' not in result["text"]


def test_kernel_memory_store_normalizes_provenance_contract_on_ingest(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel")
    )

    record = store.ingest_claim(
        claim_type="fact",
        content="Orbital transfers require careful timing.",
        extract_ids=["ext-2", "ext-1", "ext-1"],
        resource_ids=["res-2", "res-1", "res-1"],
        provenance={
            "event_id": "evt-123",
            "trace_id": "trace-123",
            "correlation_id": "corr-123",
            "source_event_ids": ["evt-2", "evt-1", "evt-2"],
            "resource_ids": ["res-3", "res-2", "res-3"],
            "blank": "",
        },
    )

    assert record["provenance"]["event_id"] == "evt-123"
    assert record["provenance"]["trace_id"] == "trace-123"
    assert record["provenance"]["correlation_id"] == "corr-123"
    assert record["provenance"]["source_event_ids"] == ["evt-1", "evt-2"]
    assert record["provenance"]["extract_ids"] == ["ext-1", "ext-2"]
    assert record["provenance"]["resource_ids"] == ["res-1", "res-2", "res-3"]
    assert "blank" not in record["provenance"]


def test_kernel_memory_store_merge_normalizes_provenance_lists(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel")
    )
    first = store.materialize_curated_memory(
        title="Original",
        summary="Original summary.",
        provenance={"merged_record_ids": ["cur-x", "cur-x"], "source_event_ids": ["evt-3"]},
    )
    second = store.materialize_curated_memory(
        title="Canonical",
        summary="Canonical summary.",
        provenance={"merged_record_ids": ["cur-y"], "source_event_ids": ["evt-2", "evt-2"]},
    )

    store.merge_records(
        "curated_memory",
        first["id"],
        second["id"],
        reason="dedupe",
    )

    merged = store.get_record("curated_memory", second["id"])
    assert merged is not None
    assert merged["provenance"]["merged_record_ids"] == ["cur-x", "cur-y", first["id"]]
    assert merged["provenance"]["source_event_ids"] == ["evt-2", "evt-3"]


def test_kernel_memory_runtime_returns_empty_context_when_no_match(tmp_path):
    runtime = KernelMemoryRuntime.from_agent_config(
        {
            "enabled": True,
            "root_dir": str(tmp_path / "kernel"),
        },
        skip_memory=False,
        logger=logging.getLogger("test.kernel_memory_runtime"),
    )

    context = runtime.retrieve_turn_context(
        "short unmatched query",
        logger=logging.getLogger("test.kernel_memory_runtime"),
    )

    assert context == ""


def test_kernel_memory_runtime_uses_recent_user_turns_for_task_followup(tmp_path):
    runtime = KernelMemoryRuntime.from_agent_config(
        {
            "enabled": True,
            "root_dir": str(tmp_path / "kernel"),
            "namespace": "bestie",
        },
        skip_memory=False,
        logger=logging.getLogger("test.kernel_memory_runtime"),
    )

    assert runtime.store is not None
    service = KernelMemoryTaskService(runtime.config, runtime.store)
    now = hermes_now()
    tomorrow = (now + timedelta(days=1)).replace(hour=18, minute=15, second=0, microsecond=0)
    today = now.replace(hour=10, minute=0, second=0, microsecond=0)
    service._save(
        [
            {
                "task_id": "task-tomorrow",
                "namespace": "bestie",
                "title": "Viza-Vet",
                "task_type": "reminder",
                "schedule_display": "once tomorrow 18:15",
                "status": "scheduled",
                "next_run_at": tomorrow.isoformat(),
                "updated_at": now.isoformat(),
            },
            {
                "task_id": "task-today",
                "namespace": "bestie",
                "title": "Feri taxi",
                "task_type": "reminder",
                "schedule_display": "once today 10:00",
                "status": "scheduled",
                "next_run_at": today.isoformat(),
                "updated_at": now.isoformat(),
            },
        ]
    )

    text = runtime.retrieve_turn_context(
        "Mi van még?",
        recent_user_turns=["Te írd le hogy mik a holnapi teendőim!"],
        logger=logging.getLogger("test.kernel_memory_runtime"),
    )

    assert "Viza-Vet" in text
    assert "Feri taxi" not in text


def test_kernel_memory_runtime_formats_turn_context(tmp_path):
    runtime = KernelMemoryRuntime.from_agent_config(
        {
            "enabled": True,
            "root_dir": str(tmp_path / "kernel"),
            "retrieval_max_records": 1,
            "retrieval_max_chars": 400,
            "retrieval_min_query_chars": 3,
        },
        skip_memory=False,
        logger=logging.getLogger("test.kernel_memory_runtime"),
    )
    assert runtime.store is not None
    runtime.store.materialize_curated_memory(
        title="Research ingestion",
        summary="Deep research results are ingested into curated kernel memory.",
    )

    context = runtime.retrieve_turn_context(
        "research ingestion",
        logger=logging.getLogger("test.kernel_memory_runtime"),
    )

    assert "# Kernel Memory" in context or "# KERNEL_RESOLVED_ANSWER" in context
    assert "Deep research results are ingested" in context


def test_kernel_memory_runtime_honors_as_of_override(tmp_path):
    runtime = KernelMemoryRuntime.from_agent_config(
        {
            "enabled": True,
            "root_dir": str(tmp_path / "kernel"),
            "retrieval_max_records": 2,
            "retrieval_max_chars": 600,
            "retrieval_min_query_chars": 3,
        },
        skip_memory=False,
        logger=logging.getLogger("test.kernel_memory_runtime"),
    )
    assert runtime.store is not None
    runtime.store.materialize_curated_memory(
        title="Mission owner",
        summary="Alice owns the mission.",
        valid_from="2026-01-01T00:00:00+00:00",
        valid_to="2026-02-01T00:00:00+00:00",
    )
    runtime.store.materialize_curated_memory(
        title="Mission owner",
        summary="Bob owns the mission.",
        valid_from="2026-02-01T00:00:00+00:00",
    )

    january = runtime.retrieve_turn_context(
        "mission owner",
        as_of="2026-01-15T12:00:00+00:00",
        logger=logging.getLogger("test.kernel_memory_runtime"),
    )
    march = runtime.retrieve_turn_context(
        "mission owner",
        as_of="2026-03-15T12:00:00+00:00",
        logger=logging.getLogger("test.kernel_memory_runtime"),
    )

    assert "Alice owns the mission" in january
    assert "Bob owns the mission" not in january
    assert "Bob owns the mission" in march
    assert "Alice owns the mission" not in march
    assert "resolved against as_of=2026-01-15T12:00:00+00:00" in january
    assert "resolved against as_of=2026-03-15T12:00:00+00:00" in march


def test_kernel_memory_runtime_instructs_model_to_trust_supported_answer_synthesis():
    contract = KernelMemoryRuntime._kernel_prompt_contract(
        result={
            "response_mode": "source_supported",
            "answer_packet": {"delivery_mode": "supported"},
            "objective_execution": {"supported": True},
        },
        effective_as_of="2026-03-01T00:00:00+00:00",
    )

    assert "If a 'Resolved answer from kernel memory:' or 'Best candidate answer from kernel memory:' line appears" in contract
    assert "Resolved answer from kernel memory:" in contract
    assert "Best candidate answer from kernel memory:" in contract
    assert "resolved against as_of=2026-03-01T00:00:00+00:00" in contract


def test_kernel_memory_runtime_extracts_authoritative_turn_response():
    payload = KernelMemoryRuntime._authoritative_turn_response(
        {
            "answer_packet": {
                "delivery_tier": "final_compact",
                "resolved_answer_final": True,
                "should_abstain": False,
                "resolved_answer_text": "29 days",
                "resolved_answer_payload": {
                    "objective": "temporal_delta",
                    "delivery_mode": "supported",
                    "answer": "29 days",
                    "support": ["Spark plug replacement date", "Turbocharged Tuesdays event date"],
                    "used_item_ids": ["cur_a", "evt_b"],
                },
            }
        }
    )

    assert payload == {
        "answer": "29 days",
        "objective": "temporal_delta",
        "delivery_mode": "supported",
        "delivery_tier": "final_compact",
        "support": ["Spark plug replacement date", "Turbocharged Tuesdays event date"],
        "used_item_ids": ["cur_a", "evt_b"],
    }


def test_kernel_memory_runtime_supported_compact_uses_packet_block_without_full_memory_blob():
    result = {
        "text": "Resolved answer from kernel memory: PlankChallenge\n\n# Kernel Memory\nToo much extra context",
        "answer_packet": {
            "delivery_tier": "supported_compact",
            "resolved_answer_final": False,
            "should_abstain": False,
            "resolved_answer_text": "PlankChallenge",
            "resolved_answer_payload": {
                "objective": "event",
                "delivery_mode": "supported",
                "answer": "PlankChallenge",
                "support": ["Social challenge activity from 5 days ago."],
                "used_item_ids": ["evt_1"],
            },
        },
        "objective_execution": {"supported": True},
        "cache": {},
    }

    block = KernelMemoryRuntime._answer_packet_block(result)

    assert "# KERNEL_SUPPORTED_ANSWER" in block
    assert "PlankChallenge" in block


def test_kernel_memory_runtime_final_answer_block_trims_support_to_one_line():
    result = {
        "answer_packet": {
            "delivery_tier": "final_compact",
            "resolved_answer_final": True,
            "should_abstain": False,
            "resolved_answer_text": "29 days",
            "resolved_answer_payload": {
                "objective": "temporal_delta",
                "delivery_mode": "supported",
                "answer": "29 days",
                "support": ["Spark plug replacement date", "Turbocharged Tuesdays event date"],
                "used_item_ids": ["cur_a", "evt_b"],
            },
        }
    }

    block = KernelMemoryRuntime._answer_packet_block(result)

    assert "# KERNEL_RESOLVED_ANSWER" in block
    assert "Spark plug replacement date" in block
    assert "Turbocharged Tuesdays event date" not in block


def test_kernel_memory_runtime_records_sampled_live_telemetry(tmp_path):
    runtime = KernelMemoryRuntime.from_agent_config(
        {
            "enabled": True,
            "root_dir": str(tmp_path / "kernel"),
            "retrieval_max_records": 3,
            "retrieval_max_chars": 1200,
            "retrieval_min_query_chars": 3,
            "retrieval_live_telemetry_enabled": True,
            "retrieval_live_telemetry_sample_percent": 100,
        },
        skip_memory=False,
        logger=logging.getLogger("test.kernel_memory_runtime"),
    )
    assert runtime.store is not None
    runtime.store.materialize_curated_memory(
        title="Orbital memo",
        summary="Orbital mechanics notes should appear in live retrieval telemetry.",
    )

    context = runtime.retrieve_turn_context(
        "orbital mechanics",
        logger=logging.getLogger("test.kernel_memory_runtime"),
    )

    assert "Orbital mechanics notes" in context
    snapshot_path = tmp_path / "kernel" / "state" / "quality" / "latest_snapshot.json"
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    assert snapshot["last_live_retrieval"]["budget_profile"] == "short_query"
    assert snapshot["last_live_retrieval"]["result_items"] >= 1
    assert "curated" in snapshot["last_live_retrieval"]["routes"]


def test_kernel_memory_runtime_uses_retrieval_cache_and_refreshes_after_invalidation(tmp_path):
    from agent.kernel_memory_retrieval_cache import KernelMemoryRetrievalCache

    runtime = KernelMemoryRuntime.from_agent_config(
        {
            "enabled": True,
            "root_dir": str(tmp_path / "kernel"),
            "retrieval_max_records": 3,
            "retrieval_max_chars": 1200,
            "retrieval_min_query_chars": 3,
            "retrieval_cache_enabled": True,
        },
        skip_memory=False,
        logger=logging.getLogger("test.kernel_memory_runtime"),
    )
    assert runtime.store is not None
    runtime.store.materialize_curated_memory(
        title="Cache note one",
        summary="Cache recall includes the first memory.",
    )

    first = runtime.retrieve_turn_context(
        "cache recall",
        logger=logging.getLogger("test.kernel_memory_runtime"),
    )
    second = runtime.retrieve_turn_context(
        "cache recall",
        logger=logging.getLogger("test.kernel_memory_runtime"),
    )

    runtime.store.materialize_curated_memory(
        title="Cache note two",
        summary="Cache recall includes the second memory.",
    )
    KernelMemoryRetrievalCache(runtime.config).bump_namespaces(
        {runtime.config.namespace},
        reason="test",
    )
    refreshed = runtime.retrieve_turn_context(
        "cache recall",
        logger=logging.getLogger("test.kernel_memory_runtime"),
    )
    stats = KernelMemoryRetrievalCache(runtime.config).stats()

    assert "first memory" in first
    assert "first memory" in second
    assert "second memory" in refreshed
    assert stats["hits"] >= 1
    assert stats["writes"] >= 2


def test_kernel_memory_runtime_resolves_shared_namespaces(tmp_path):
    runtime = KernelMemoryRuntime.from_agent_config(
        {
            "enabled": True,
            "root_dir": str(tmp_path / "kernel"),
            "namespace": "bestie",
            "retrieval_scopes": ["self", "shared", "tomi"],
            "shared_namespaces": ["shared"],
        },
        skip_memory=False,
        logger=logging.getLogger("test.kernel_memory_runtime"),
    )

    assert runtime.resolve_retrieval_namespaces() == {"bestie", "shared", "tomi"}


def test_kernel_memory_store_filters_retrieval_by_namespace(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel", namespace="bestie")
    )
    store.materialize_curated_memory(
        title="Bestie note",
        summary="Private notebook entry about gardening.",
    )
    shared_store = KernelMemoryStore.from_config(
        KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel", namespace="shared")
    )
    shared_store.materialize_curated_memory(
        title="Shared note",
        summary="Cross-agent memory about orbital mechanics.",
    )
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel", namespace="bestie")
    )

    result = store.retrieve_curated_context(
        "orbital mechanics",
        namespaces={"bestie"},
    )
    shared_result = store.retrieve_curated_context(
        "orbital mechanics",
        namespaces={"shared"},
    )

    assert result["items"] == []
    assert len(shared_result["items"]) == 1
    assert shared_result["items"][0]["namespace"] == "shared"


def test_kernel_memory_store_policy_router_uses_semantic_graph_and_source_routes(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(
            enabled=True,
            root_dir=tmp_path / "kernel",
            namespace="bestie",
            retrieval_policy_order=["semantic", "graph", "source"],
        )
    )
    resource = store.ingest_resource(
        resource_type="note",
        title="Orbital mechanics notebook",
        content="Orbital mechanics uses Hohmann transfer windows and delta-v budgeting.",
    )
    extract = store.ingest_extract(
        resource_id=resource["id"],
        extract_type="paragraph",
        sequence=0,
        content="Hohmann transfers reduce fuel costs for orbital transfers.",
    )
    claim = store.ingest_claim(
        claim_type="fact",
        content="Hohmann transfers are fuel efficient orbital maneuvers.",
        extract_ids=[extract["id"]],
        resource_ids=[resource["id"]],
    )
    store.upsert_entity(
        name="Hohmann transfer",
        entity_type="concept",
        claim_ids=[claim["id"]],
        extract_ids=[extract["id"]],
        resource_ids=[resource["id"]],
    )

    result = store.retrieve_context_by_policy(
        "Tell me about Hohmann transfer orbital mechanics",
        max_records=6,
        max_chars=1200,
    )

    assert result["items"]
    assert "semantic" in result["routes"]
    assert "graph" in result["routes"]
    assert "source" in result["routes"]
    assert "Hohmann" in result["text"]


def test_kernel_memory_semantic_route_can_return_first_class_event_records(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(
            enabled=True,
            root_dir=tmp_path / "kernel",
            namespace="bestie",
            retrieval_policy_order=["semantic", "curated"],
        )
    )
    claim = store.ingest_claim(
        claim_type="dated_fact",
        content="Laura rehab started on February 22 after the home accident.",
    )
    event = store.ingest_event(
        event_type="personal_event",
        title="Laura rehab start",
        summary="Laura rehab started on February 22 after the home accident.",
        temporal_markers=["February 22"],
        claim_ids=[claim["id"]],
    )

    result = store.retrieve_semantic_context(
        "When did Laura rehab start?",
        max_records=3,
        max_chars=900,
    )

    assert result["items"]
    assert any(item["id"] == event["id"] for item in result["items"])
    assert "Kind: event" in result["text"]


def test_kernel_memory_retrieval_promotes_grounded_direct_attribute_to_final_compact(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(
            enabled=True,
            root_dir=tmp_path / "kernel",
            namespace="bestie",
            retrieval_policy_order=["semantic", "curated"],
        )
    )
    store.ingest_claim(
        claim_type="pet_fact",
        content="Do you have any recommendations for a good collar brand or type that would suit a Golden Retriever like Max?",
        fact_facets={
            "descriptor_pairs": [{"descriptor": "Golden Retriever", "entity": "Max"}],
        },
        metadata={"speaker_role": "user"},
    )

    result = KernelMemoryRetriever(store.config, store).retrieve_context_by_policy(
        "What breed is my dog?",
        max_records=4,
        max_chars=900,
        namespaces={"bestie"},
        route_order=["semantic", "curated"],
        response_mode=store.classify_query_response_mode("What breed is my dog?"),
    )

    assert result["answer_packet"]["delivery_tier"] == "final_compact"
    assert result["answer_packet"]["resolved_answer_final"] is True
    assert result["answer_packet"]["resolved_answer_text"] == "Golden Retriever"


def test_kernel_memory_retrieval_promotes_current_inventory_count_to_final_compact(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(
            enabled=True,
            root_dir=tmp_path / "kernel",
            namespace="bestie",
            retrieval_policy_order=["semantic", "curated"],
        )
    )
    store.ingest_claim(
        claim_type="user_fact",
        content="I currently own 4 musical instruments: a Yamaha FG800, a Fender Stratocaster, a Korg B1, and a Pearl Export drum kit.",
        fact_facets=extract_fact_facets(
            "I currently own 4 musical instruments: a Yamaha FG800, a Fender Stratocaster, a Korg B1, and a Pearl Export drum kit."
        ),
        metadata={"speaker_role": "user", "primary_language": "en"},
        observed_at="2023-03-10T10:00:00+00:00",
    )

    result = KernelMemoryRetriever(store.config, store).retrieve_context_by_policy(
        "How many musical instruments do I currently own?",
        max_records=4,
        max_chars=900,
        namespaces={"bestie"},
        route_order=["semantic", "curated"],
        response_mode=store.classify_query_response_mode("How many musical instruments do I currently own?"),
    )

    assert result["answer_packet"]["delivery_tier"] == "final_compact"
    assert result["answer_packet"]["resolved_answer_final"] is True
    assert result["answer_packet"]["resolved_answer_text"].startswith("I currently own 4 musical instruments:")


def test_kernel_memory_ingest_normalizes_relation_and_event_ontology(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel", namespace="bestie")
    )
    left = store.upsert_entity(name="Laura", entity_type="person")
    right = store.upsert_entity(name="Tomi", entity_type="person")
    relation = store.upsert_relation(
        relation_type="co_occurs_with",
        subject_entity_id=left["id"],
        object_entity_id=right["id"],
    )
    event = store.ingest_event(
        event_type="personal",
        title="Laura milestone",
        summary="Laura reached a new recovery milestone.",
        event_status="done",
    )

    assert relation["relation_type"] == "cooccurs_with"
    assert relation["metadata"]["original_relation_type"] == "co_occurs_with"
    assert event["event_type"] == "personal_event"
    assert event["metadata"]["original_event_type"] == "personal"
    assert event["event_status"] == "observed"
    assert event["metadata"]["original_event_status"] == "done"


def test_kernel_memory_store_source_route_prefers_extracts_over_duplicate_resources(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel", namespace="bestie")
    )
    store.ingest_document(
        document_type="note",
        title="Queued note",
        content="Orbital mechanics notes can be queued for background ingest.",
    )

    result = store.retrieve_source_context(
        "orbital mechanics",
        max_records=3,
        max_chars=1200,
    )

    kinds = [item["kind"] for item in result["items"]]
    assert "extract" in kinds
    assert "resource" not in kinds


def test_kernel_memory_event_bridge_and_worker_process_turn(tmp_path):
    config = KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel", namespace="bestie")
    bridge = KernelMemoryEventBridge(config)
    queued = bridge.emit(
        "conversation_turn_completed",
        payload={
            "session_id": "s1",
            "user_message": "Remember this research plan",
            "assistant_response": "The plan is to build a worker and shared kernel root.",
            "model": "gpt-5.4",
        },
    )
    assert queued["status"] == "queued"

    worker = KernelMemoryWorker(config)
    result = worker.process_once()

    assert result["processed"] == 1
    store = KernelMemoryStore.from_config(config)
    curated = store.list_curated_memories()
    assert len(curated) == 1
    assert "shared kernel root" in curated[0]["summary"]


def test_kernel_memory_worker_mirrors_shareable_events_to_shared_namespace(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        shared_write_enabled=True,
        shared_namespaces=["shared"],
    )
    bridge = KernelMemoryEventBridge(config)
    bridge.emit(
        "assistant_turn_completed",
        payload={
            "session_id": "s1",
            "user_message": "Remember this shared plan",
            "assistant_response": "We will reuse this knowledge across agents.",
        },
    )

    worker = KernelMemoryWorker(config)
    result = worker.process_once()

    assert result["processed"] == 1
    bestie_store = KernelMemoryStore.from_config(config)
    shared_store = KernelMemoryStore.from_config(
        KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel", namespace="shared")
    )
    assert len(bestie_store.list_curated_memories(namespaces={"bestie"})) >= 1
    assert len(shared_store.list_curated_memories(namespaces={"shared"})) == 1


def test_kernel_memory_worker_ingests_events_entities_and_episode_for_conversation_turn(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
    )
    bridge = KernelMemoryEventBridge(config)
    bridge.emit(
        "assistant_turn_completed",
        payload={
            "session_id": "s1",
            "user_message": (
                "Laura 2026. február 22-én itthoni balesetben gerincsérülést szenvedett, "
                "és most ő a fő prioritás."
            ),
            "assistant_response": (
                "Rendben, Laura állapotát érzékeny, kiemelt témaként fogom kezelni, "
                "és figyelek rá a későbbi beszélgetésekben is."
            ),
        },
    )

    worker = KernelMemoryWorker(config)
    result = worker.process_once()
    store = KernelMemoryStore.from_config(config)
    curated = store.list_curated_memories()
    events = store.list_records("event")
    episodes = store.list_records("episode")
    entities = store.list_records("entity")
    associations = store.list_records("association")

    assert result["processed"] == 1
    assert len(curated) == 1
    assert len(events) >= 1
    assert len(episodes) == 1
    assert any(entity["name"] == "Laura" for entity in entities)
    assert associations
    assert any(association["association_origin"] == "episode_compilation" for association in associations)
    assert curated[0]["event_ids"]
    assert curated[0]["episode_id"] == episodes[0]["id"]
    assert "Laura" in curated[0]["summary"]
    assert any(event.get("action_lemma") for event in events)
    assert any(event.get("event_status") for event in events)
    assert any(event.get("lifecycle") for event in events)


def test_kernel_memory_event_bridge_emits_phase_b_contract(tmp_path):
    config = KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel", namespace="bestie")
    bridge = KernelMemoryEventBridge(config)

    queued = bridge.emit(
        "assistant_turn_completed",
        payload={
            "user_message": "Remember this preference",
            "assistant_response": "You prefer concise updates.",
        },
        source_session_id="session-1",
        source_turn_id="turn-1",
    )

    event_path = Path(queued["path"])
    payload = json.loads(event_path.read_text(encoding="utf-8"))
    assert payload["event_type"] == "assistant_turn_completed"
    assert payload["schema_version"] == "phase-b.v1"
    assert payload["source_session_id"] == "session-1"
    assert payload["source_turn_id"] == "turn-1"
    assert payload["namespace_id"] == "bestie"
    assert payload["agent_id"] == "bestie"


def test_kernel_memory_worker_retries_then_fails_unknown_event(tmp_path):
    config = KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel", namespace="bestie")
    bridge = KernelMemoryEventBridge(config)
    bridge.emit("session_started", payload={"session_id": "s1"})

    outbox = bridge.list_outbox()
    raw = json.loads(outbox[0].read_text(encoding="utf-8"))
    raw["event_type"] = "unsupported_event"
    outbox[0].write_text(json.dumps(raw, ensure_ascii=False, sort_keys=True), encoding="utf-8")

    worker = KernelMemoryWorker(config, max_delivery_attempts=2)
    first = worker.process_once()
    second = worker.process_once()

    assert first["processed"] == 0
    assert second["failed"] == 1
    assert bridge.queue_metrics()["failed"] == 1


def test_kernel_memory_worker_records_shadow_suggestion(tmp_path):
    config = KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel", namespace="bestie")
    bridge = KernelMemoryEventBridge(config)
    bridge.emit(
        "assistant_turn_completed",
        payload={
            "session_id": "s1",
            "user_message": "Please remember that I prefer concise answers.",
            "assistant_response": "I will keep replies concise.",
            "model": "gpt-5.4",
        },
        source_session_id="s1",
        source_turn_id="turn-1",
    )

    worker = KernelMemoryWorker(config)
    result = worker.process_once()
    shadow_path = config.root_dir / "state" / "proactive" / "shadow_actions.jsonl"
    suggestions = [json.loads(line) for line in shadow_path.read_text(encoding="utf-8").splitlines()]
    worker_state = KernelMemoryWorkerStateStore(config).read()

    assert result["processed"] == 1
    assert suggestions[0]["suggested_action_type"] == "curate_user_preference"
    assert worker_state["last_processed_event_id"]


def test_kernel_memory_worker_ingests_deep_research_event(tmp_path):
    config = KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel", namespace="bestie")
    bridge = KernelMemoryEventBridge(config)
    bridge.emit(
        "deep_research_completed",
        payload={
            "query": "Hermes memory architecture",
            "report": (
                "Hermes should keep the online path bounded and move expensive memory work "
                "into an asynchronous worker.\n\n"
                "A shared kernel root with explicit namespaces improves inspectability."
            ),
            "report_type": "research_report",
            "preset": "deep",
        },
        source_session_id="research-session",
        source_turn_id="turn-1",
    )

    worker = KernelMemoryWorker(config)
    result = worker.process_once()
    store = KernelMemoryStore.from_config(config)
    curated = store.list_curated_memories()
    episodes = store.list_records("episode")
    relations = store.list_records("relation")
    associations = store.list_records("association")

    assert result["processed"] == 1
    assert len(curated) == 1
    assert curated[0]["title"] == "Deep Research: Hermes memory architecture"
    assert len(episodes) == 1
    assert curated[0]["episode_id"] == episodes[0]["id"]
    assert isinstance(relations, list)
    assert associations
    assert any(association["association_origin"] == "episode_compilation" for association in associations)


def test_kernel_memory_event_bridge_accepts_root_path(tmp_path):
    bridge = KernelMemoryEventBridge(tmp_path / "kernel")

    queued = bridge.emit(
        "session_started",
        payload={"session_id": "smoke-session"},
        namespace="bestie",
    )
    payload = json.loads(Path(queued["path"]).read_text(encoding="utf-8"))

    assert queued["status"] == "queued"
    assert bridge.list_outbox()
    assert payload["agent_id"] == "bestie"


def test_kernel_memory_event_bridge_prioritizes_high_before_low(tmp_path):
    bridge = KernelMemoryEventBridge(
        KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel", namespace="bestie")
    )
    bridge.emit("session_started", payload={"session_id": "low"}, priority="low")
    bridge.emit("assistant_turn_completed", payload={"user_message": "x", "assistant_response": "y"}, priority="high")

    outbox = bridge.list_outbox()
    first = json.loads(outbox[0].read_text(encoding="utf-8"))

    assert first["priority"] == "high"


def test_kernel_memory_worker_lock_is_single_holder_and_releasable(tmp_path):
    config = KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel", namespace="bestie")
    first_lock = KernelMemoryWorkerLock(config)
    second_lock = KernelMemoryWorkerLock(config)

    first_lock.acquire()
    try:
        try:
            second_lock.acquire()
        except RuntimeError as exc:
            assert "already held" in str(exc)
        else:
            raise AssertionError("expected second lock acquisition to fail while first lock is held")
    finally:
        first_lock.release()

    second_lock.acquire()
    second_lock.release()


def test_kernel_memory_store_can_supersede_curated_memory(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel", namespace="bestie")
    )
    original = store.materialize_curated_memory(
        title="Old summary",
        summary="Original summary",
    )

    replacement = store.supersede_curated_memory(
        original["id"],
        title="New summary",
        summary="Updated summary",
    )

    original_after = store.get_record("curated_memory", original["id"])
    assert original_after["status"] == "superseded"
    assert original_after["provenance"]["replacement_record_id"] == replacement["id"]
    assert replacement["provenance"]["supersedes"] == original["id"]
