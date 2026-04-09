from __future__ import annotations

import json

from agent.kernel_memory import KernelMemoryConfig, KernelMemoryStore
from agent.kernel_memory_admin import KernelMemoryAdminService
from agent.kernel_memory_daemon import KernelMemoryDaemon
from agent.kernel_memory_contracts import build_kernel_memory_event
from agent.kernel_memory_events import KernelMemoryEventBridge, KernelMemoryWorker
from agent.kernel_memory_pipeline import KernelMemoryWriteService


def test_proactive_automatic_mode_executes_low_risk_action(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        proactive_mode="automatic",
        hybrid_retrieval_enabled=True,
        embedding_index_enabled=True,
        embedding_provider="deterministic",
    )
    service = KernelMemoryWriteService(config)
    event = build_kernel_memory_event(
        event_type="assistant_turn_completed",
        payload={
            "session_id": "s1",
            "user_message": "Please remember that I prefer concise answers.",
            "assistant_response": "I will keep replies concise.",
        },
        namespace_id="bestie",
        agent_id="bestie",
    )

    result = service.process_event(event)

    actions = result["proactive_actions"]
    assert actions
    assert actions[0]["status"] == "executed"
    store = KernelMemoryStore.from_config(config)
    curated_titles = [record["title"] for record in store.list_curated_memories()]
    assert any(title.startswith("User preference:") for title in curated_titles)


def test_write_service_links_turn_corrections_into_supersession_lineage(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        assistant_acknowledgement_filter_enabled=False,
    )
    service = KernelMemoryWriteService(config)

    first = build_kernel_memory_event(
        event_type="assistant_turn_completed",
        payload={
            "session_id": "s1",
            "user_message": 'A kedvenc idézetem az, hogy "Régi idézet".',
            "assistant_response": "Rendben, ezt kedvenc idézetként fogom kezelni.",
        },
        namespace_id="bestie",
        agent_id="bestie",
    )
    second = build_kernel_memory_event(
        event_type="assistant_turn_completed",
        payload={
            "session_id": "s1",
            "user_message": (
                'Ez nem a kedvenc idézetem. A kedvenc idézetem inkább az, hogy "Új idézet".'
            ),
            "assistant_response": "Javítottam, a korábbi idézet helyett ezt kezelem kedvenc idézetként.",
        },
        namespace_id="bestie",
        agent_id="bestie",
    )

    service.process_event(first)
    result = service.process_event(second)

    store = KernelMemoryStore.from_config(config)
    claims = store.list_records("claim")
    events = store.list_records("event")
    curated = store.list_curated_memories(status=None)

    old_claim = next(record for record in claims if "Régi idézet" in str(record.get("content") or ""))
    new_claim = next(record for record in claims if "Új idézet" in str(record.get("content") or ""))
    assert old_claim["status"] == "superseded"
    assert old_claim["superseded_by"] == new_claim["id"]
    assert new_claim["supersedes"] == old_claim["id"]

    old_event = next(record for record in events if "Régi idézet" in str(record.get("summary") or ""))
    new_event = next(
        record
        for record in events
        if record.get("event_type") == "superseded" and "Új idézet" in str(record.get("summary") or "")
    )
    assert old_event["status"] == "superseded"
    assert old_event["superseded_by"] == new_event["id"]
    assert new_event["supersedes"] == old_event["id"]

    old_curated = next(record for record in curated if "Régi idézet" in str(record.get("summary") or ""))
    new_curated = next(record for record in curated if "Új idézet" in str(record.get("summary") or ""))
    assert old_curated["status"] == "superseded"
    assert old_curated["superseded_by"] == new_curated["id"]
    assert new_curated["supersedes"] == old_curated["id"]

    assert result["superseded_claim_ids"] == [old_claim["id"]]
    assert result["superseded_event_ids"] == [old_event["id"]]
    assert result["superseded_curated_memory_ids"] == [old_curated["id"]]


def test_admin_service_can_replay_failed_events_and_repair_index(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
    )
    bridge = KernelMemoryEventBridge(config)
    queued = bridge.emit("session_started", payload={"session_id": "s1"})
    event_path = bridge.list_outbox()[0]
    payload = json.loads(event_path.read_text(encoding="utf-8"))
    payload["event_type"] = "unsupported_event"
    event_path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True), encoding="utf-8")

    worker = KernelMemoryWorker(config, max_delivery_attempts=1)
    result = worker.process_once()

    assert result["failed"] == 1
    admin = KernelMemoryAdminService(config)
    failed = admin.list_failed_events()
    assert failed and failed[0]["event_id"] == queued["event_id"]

    replayed = admin.replay_failed(event_id=queued["event_id"])
    assert replayed[0]["status"] == "queued"
    repaired = admin.repair_event_index()
    assert repaired["status"] == "rebuilt"
    assert repaired["queue"]["queued"] == 1


def test_write_service_skips_memory_tool_results_and_memory_save_acknowledgements(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        excluded_tool_result_tools=["memory"],
        assistant_acknowledgement_filter_enabled=True,
    )
    service = KernelMemoryWriteService(config)

    tool_event = build_kernel_memory_event(
        event_type="tool_result_available",
        payload={
            "tool_name": "memory",
            "tool_result": '{"success": true, "target": "user"}',
        },
        namespace_id="bestie",
        agent_id="bestie",
    )
    tool_result = service.process_event(tool_event)
    assert tool_result["ingested"] is False
    assert tool_result["reason"] == "excluded_tool_result:memory"

    ack_event = build_kernel_memory_event(
        event_type="assistant_turn_completed",
        payload={
            "session_id": "s1",
            "user_message": "Remember that my cat is Laura.",
            "assistant_response": "Elmentettem.",
        },
        namespace_id="bestie",
        agent_id="bestie",
    )
    ack_result = service.process_event(ack_event)
    assert ack_result["ingested"] is False
    assert ack_result["reason"] == "assistant_memory_acknowledgement"


def test_store_correction_merge_and_inspect(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel", namespace="bestie")
    )
    first = store.materialize_curated_memory(
        title="Original",
        summary="Original summary about kernel memory repair discipline.",
        source_ids=["doc:1"],
    )
    second = store.materialize_curated_memory(
        title="Canonical",
        summary="Canonical summary about kernel memory repair discipline.",
        source_ids=["doc:2"],
    )

    result = store.apply_correction(
        "curated_memory",
        first["id"],
        operation="merge",
        reason="duplicate canonicalization",
        target_record_id=second["id"],
    )

    assert result["status"] == "merged"
    merged_source = store.get_record("curated_memory", first["id"])
    merged_target = store.get_record("curated_memory", second["id"])
    assert merged_source["status"] == "merged"
    assert first["id"] in merged_target["provenance"]["merged_record_ids"]

    inspected = store.inspect_record("curated_memory", second["id"])
    assert inspected["record"]["id"] == second["id"]
    assert "sources" in inspected["related"]


def test_admin_service_runs_golden_set_and_daemon_writes_health(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        proactive_mode="automatic",
        hybrid_retrieval_enabled=True,
        embedding_index_enabled=True,
        embedding_provider="deterministic",
    )
    store = KernelMemoryStore.from_config(config)
    store.materialize_curated_memory(
        title="Research note",
        summary="Orbital mechanics uses Hohmann transfer trajectories.",
    )
    claim = store.ingest_claim(
        claim_type="fact",
        content="Orbital mechanics uses Hohmann transfer trajectories.",
    )
    earth = store.upsert_entity(name="Earth", entity_type="planet", claim_ids=[claim["id"]])
    mars = store.upsert_entity(name="Mars", entity_type="planet", claim_ids=[claim["id"]])
    store.upsert_relation(
        relation_type="transfers_to",
        subject_entity_id=earth["id"],
        object_entity_id=mars["id"],
        claim_ids=[claim["id"]],
        confidence=0.9,
    )
    admin = KernelMemoryAdminService(config)
    admin.add_golden_case(
        name="orbital-recall",
        query="orbital mechanics",
        expected_substrings=["Hohmann transfer"],
    )
    admin.enqueue_corpus_document(
        document_type="note",
        title="Queued corpus note",
        content="Orbital mechanics notes can be queued for background ingest.",
        metadata={"origin": "test"},
    )

    daemon = KernelMemoryDaemon(config, interval_seconds=5)
    result = daemon.run_once()

    assert result["golden_set"]["failed"] == 0
    assert result["corpus"]["processed"] == 1
    assert "canonicalization_maintenance" in result
    assert "curated_maintenance" in result
    health = json.loads((config.root_dir / "state" / "ops" / "health.json").read_text(encoding="utf-8"))
    assert health["acceptance_ok"] is True
    assert health["golden_set"]["failed"] == 0
    assert "canonicalization_maintenance" in health
    assert "curated_maintenance" in health
    assert health["corpus_queue"]["processed"] == 1
    assert health["corpus_documents"]["documents_total"] >= 1
    assert health["embedding_index"]["rows"] >= 1
    assert health["graph_extraction"]["processed_claims"] >= 1
    assert health["retrieval_cache"]["entries"] >= 1
    assert health["nightly_artifact"]["curated_hotset_count"] >= 1
    assert health["nightly_benchmark"]["total_cases"] >= 1
    assert health["validation_suite"]["total_cases"] >= 0
    assert health["ops_policy"]["status"] in {"healthy", "degraded", "halted"}
    assert "tasks" in health
    assert "conflicts" in health
    assert "revisit" in health
    assert "scale_triggers" in health
    assert health["consolidation"]["active_consolidated"] >= 1
    assert health["consolidation_created"] >= 1
    assert health["relations"]["total"] >= 1
    assert health["activation_maintenance"]["status"] == "ok"
    assert "evaluated" in health["activation_maintenance"]
    assert "lineage_resolved" in health["activation_maintenance"]
    assert "lineage_resolved" in health["curated_maintenance"]
    assert "hard_negative_summary" in health
    assert health["deterministic_recompile"]["ok"] is True
    assert health["deterministic_recompile"]["classification_status"] == "clean"
    assert health["deterministic_recompile"]["auto_apply_safe"] is False
    assert result["deterministic_recompile"]["comparison"]["ok"] is True
    assert health["quality"]["last_golden_run"]["passed"] >= 1
    assert health["prewarm_queue"]["processed"] >= 1


def test_daemon_cached_quality_outputs_use_validation_suite_snapshot(tmp_path, monkeypatch):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
    )
    daemon = KernelMemoryDaemon(config, interval_seconds=5)
    monkeypatch.setattr(daemon.admin, "latest_health_snapshot", lambda: {})
    monkeypatch.setattr(
        daemon.admin,
        "latest_quality_snapshot",
        lambda: {
            "last_validation_suite": {"passed": 3, "total_cases": 3},
            "last_golden_run": {"passed": 2, "total": 2},
        },
    )
    monkeypatch.setattr(daemon.admin, "latest_nightly_artifact", lambda: {"summary": {"curated_hotset_count": 1}})
    monkeypatch.setattr(daemon.admin, "latest_nightly_benchmark", lambda: {"passed": 2, "total_cases": 2})
    monkeypatch.setattr(daemon, "_should_run_quality_cycle", lambda *, force_quality: False)

    quality = daemon._run_quality_phases(force_quality=False)

    assert quality.validation_result["passed"] == 3
    assert quality.golden_set["passed"] == 2
    assert quality.deterministic_recompile == {}


def test_admin_service_can_enqueue_and_run_prewarm_jobs(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        retrieval_cache_enabled=True,
        retrieval_prewarm_enabled=True,
    )
    store = KernelMemoryStore.from_config(config)
    store.materialize_curated_memory(
        title="Prewarmable note",
        summary="Kernel memory should prewarm reusable cache entries.",
    )
    admin = KernelMemoryAdminService(config)

    queued = admin.enqueue_prewarm_query("reusable cache", namespaces=["bestie"])
    processed = admin.run_prewarm(max_jobs=1)
    cache_stats = admin.retrieval_cache_stats()

    assert queued["status"] == "queued"
    assert processed["processed"] == 1
    assert cache_stats["entries"] >= 1


def test_admin_service_runs_graph_extraction(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        graph_relation_promote_min_observations=1,
        graph_relation_promote_min_confidence=0.5,
    )
    store = KernelMemoryStore.from_config(config)
    store.ingest_claim(
        claim_type="fact",
        content="Earth transfers to Mars during orbital planning.",
    )
    admin = KernelMemoryAdminService(config)

    result = admin.run_graph_extraction(max_claims=10)
    metrics = admin.relation_metrics()

    assert result["created_relations"] >= 1
    assert metrics["total"] >= 1


def test_admin_service_runs_graph_projection_and_persists_snapshot(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        graph_projection_enabled=True,
        neo4j_uri="bolt://localhost:7687",
    )
    store = KernelMemoryStore.from_config(config)
    resource = store.ingest_resource(
        resource_type="note",
        title="Mission plan",
        content="Earth transfers to Mars during orbital planning.",
    )
    extract = store.ingest_extract(
        resource_id=resource["id"],
        content="Earth transfers to Mars during orbital planning.",
    )
    claim = store.ingest_claim(
        claim_type="fact",
        content="Earth transfers to Mars during orbital planning.",
        extract_ids=[extract["id"]],
    )
    earth = store.upsert_entity(name="Earth", entity_type="planet", claim_ids=[claim["id"]])
    mars = store.upsert_entity(name="Mars", entity_type="planet", claim_ids=[claim["id"]])
    store.upsert_relation(
        relation_type="transfers_to",
        subject_entity_id=earth["id"],
        object_entity_id=mars["id"],
        claim_ids=[claim["id"]],
        confidence=0.9,
    )
    admin = KernelMemoryAdminService(config)

    result = admin.run_graph_projection()
    latest = admin.latest_graph_projection()
    health = admin.graph_store_health()

    assert result["projection"]["node_count"] >= 5
    assert latest["projection"]["edge_count"] >= 4
    assert health["status"] == "disabled"
    assert health["reason"] == "neo4j_password_missing"


def test_admin_service_benchmarks_memory_assembly_and_persists_snapshot(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
    )
    store = KernelMemoryStore.from_config(config)
    store.materialize_curated_memory(
        title="Project task",
        summary="The migration task should preserve rollback safety and exact-source support.",
        metadata={"memory_class": "project_task"},
    )
    admin = KernelMemoryAdminService(config)

    result = admin.benchmark_memory_assembly("migration task")
    snapshot = admin.latest_quality_snapshot()

    assert result["current_kernel_baseline"]["chars"] >= result["heavy_semantic_baseline"]["chars"]
    assert snapshot["last_memory_assembly_baseline"]["saved_chars"] >= 0


def test_admin_service_builds_nightly_artifact(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
    )
    store = KernelMemoryStore.from_config(config)
    store.materialize_curated_memory(
        title="Nightly memory",
        summary="Nightly artifact generation should persist a curated hotset.",
    )
    admin = KernelMemoryAdminService(config)

    artifact = admin.build_nightly_artifacts()
    latest = admin.latest_nightly_artifact()

    assert artifact["summary"]["curated_hotset_count"] >= 1
    assert latest["summary"]["curated_hotset_count"] >= 1


def test_admin_service_runs_nightly_benchmarks(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
    )
    store = KernelMemoryStore.from_config(config)
    store.materialize_curated_memory(
        title="Nightly benchmark memory",
        summary="Nightly benchmarks should capture compression and pass-rate metrics.",
    )
    admin = KernelMemoryAdminService(config)
    admin.add_golden_case(
        name="nightly-benchmark",
        query="benchmark memory",
        expected_substrings=["compression"],
    )

    result = admin.run_nightly_benchmarks(max_cases=5)
    latest = admin.latest_nightly_benchmark()

    assert result["total_cases"] == 1
    assert latest["total_cases"] == 1


def test_admin_service_runs_validation_suite(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        validation_suite_enabled=True,
    )
    store = KernelMemoryStore.from_config(config)
    store.ingest_document(
        document_type="note",
        title="Legal recall",
        content="Contract review must preserve exact source clauses.",
    )
    admin = KernelMemoryAdminService(config)
    admin.add_validation_case(
        name="legal-source",
        domain="legal",
        query="exact source clauses",
        expected_substrings=["exact source clauses"],
        expected_response_mode="exact_source_required",
        tags=["leakage"],
    )

    result = admin.run_validation_suite()
    snapshot = admin.latest_quality_snapshot()

    assert result["total_cases"] == 1
    assert snapshot["last_validation_suite"]["passed"] == 1


def test_admin_service_evaluates_ops_policy_from_latest_health(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
    )
    admin = KernelMemoryAdminService(config)
    health_path = config.root_dir / "state" / "ops" / "health.json"
    health_path.parent.mkdir(parents=True, exist_ok=True)
    health_path.write_text(
        json.dumps(
            {
                "acceptance_ok": True,
                "failed_events": 1,
                "golden_set": {"failed": 0},
                "validation_suite": {"failed": 1},
                "embedding_provider": {"ok": True},
            },
            ensure_ascii=False,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    result = admin.evaluate_ops_policy()

    assert result["status"] == "degraded"
    assert "validation_suite_failed" in result["warnings"]


def test_admin_service_restores_verified_backup_and_lists_migrations(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
    )
    admin = KernelMemoryAdminService(config)
    marker = config.root_dir / "state" / "ops" / "marker.txt"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("before\n", encoding="utf-8")

    backup = admin.create_backup(label="ops-baseline")
    started = admin.begin_migration(name="layout-v2", summary="Rebuild runtime layout")
    marker.write_text("after\n", encoding="utf-8")

    restored = admin.restore_backup(backup_path=str(backup["backup_path"]))
    migrations = admin.list_migrations(limit=5)

    assert restored["status"] == "restored"
    assert restored["acceptance"]["ok"] is True
    assert marker.read_text(encoding="utf-8") == "before\n"
    assert any(entry["migration_id"] == started["migration_id"] for entry in migrations)


def test_admin_service_runs_backup_restore_drill(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        graph_projection_enabled=True,
        neo4j_uri="bolt://localhost:7687",
    )
    admin = KernelMemoryAdminService(config)
    marker = config.root_dir / "state" / "ops" / "restore_drill_marker.txt"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("before-drill\n", encoding="utf-8")

    result = admin.run_backup_restore_drill(label="ops-drill")

    assert result["status"] == "completed"
    assert result["backup"]["verification_ok"] is True
    assert result["restore"]["status"] == "restored"
    assert result["marker_restored"] is True
    assert result["graph_projection_after"]["status"] == "ok"


def test_golden_set_supports_route_assertions_and_persists_quality_snapshot(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        hybrid_retrieval_enabled=True,
        embedding_index_enabled=True,
        embedding_provider="deterministic",
        graph_relation_promote_min_observations=1,
        graph_relation_promote_min_confidence=0.5,
        retrieval_policy_order=["source", "semantic", "graph"],
    )
    store = KernelMemoryStore.from_config(config)
    document = store.ingest_document(
        document_type="note",
        title="Orbital source note",
        content="Hohmann transfer appears in the source document for orbital mechanics.",
    )
    claim = store.ingest_claim(
        claim_type="fact",
        content="Earth transfers to Mars via a Hohmann transfer.",
        resource_ids=[document["resource"]["id"]],
        extract_ids=document["extract_ids"][:1],
    )
    earth = store.upsert_entity(name="Earth", entity_type="planet", claim_ids=[claim["id"]])
    mars = store.upsert_entity(name="Mars", entity_type="planet", claim_ids=[claim["id"]])
    store.upsert_relation(
        relation_type="transfers_to",
        subject_entity_id=earth["id"],
        object_entity_id=mars["id"],
        claim_ids=[claim["id"]],
        confidence=0.9,
    )

    admin = KernelMemoryAdminService(config)
    admin.run_embedding_index(discover_limit=20, max_jobs=20)
    admin.add_golden_case(
        name="source-proof",
        query="Please quote the exact source for Hohmann transfer",
        expected_substrings=["Hohmann transfer"],
        required_routes=["source"],
        forbidden_routes=["semantic", "graph"],
        expected_response_mode="exact_source_required",
    )

    result = admin.run_golden_set(case_names=["source-proof"])
    snapshot = admin.latest_quality_snapshot()
    recent = admin.list_quality_runs(limit=5, run_type="golden_set")

    assert result["failed"] == 0
    assert snapshot["last_golden_run"]["passed"] == 1
    assert recent and recent[0]["passed"] == 1
