from __future__ import annotations

from datetime import timedelta

from agent.kernel_memory import KernelMemoryConfig, KernelMemoryStore
from agent.kernel_memory_tasks import KernelMemoryTaskService
from hermes_time import now as hermes_now


def test_task_service_creates_task_and_mirrors_memory(tmp_path, monkeypatch):
    import cron.jobs as cron_jobs
    import agent.kernel_memory_tasks as tasks_mod

    monkeypatch.setattr(cron_jobs, "CRON_DIR", tmp_path / "cron")
    monkeypatch.setattr(cron_jobs, "JOBS_FILE", tmp_path / "cron" / "jobs.json")
    monkeypatch.setattr(cron_jobs, "OUTPUT_DIR", tmp_path / "cron" / "output")
    monkeypatch.setattr(tasks_mod, "resolve_proactive_delivery_string", lambda preferred_platform="discord": "local")

    config = KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel", namespace="bestie")
    store = KernelMemoryStore.from_config(config)
    service = KernelMemoryTaskService(config, store)

    task = service.create_task_from_capture(
        {
            "title": "Minden hétvégén heti összefoglaló",
            "schedule": "every 7d",
            "prompt": "Készíts heti összefoglalót.",
            "task_type": "weekly_digest",
            "metadata": {"category": "digest"},
        },
        source_event_id="evt-1",
        source_session_id="sess-1",
    )

    assert task["status"] == "scheduled"
    assert service.queue_metrics()["pending"] == 1
    assert any(
        record["metadata"].get("task_id") == task["task_id"]
        for record in store.list_curated_memories()
    )


def test_task_service_retrieves_task_context(tmp_path):
    config = KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel", namespace="bestie")
    store = KernelMemoryStore.from_config(config)
    service = KernelMemoryTaskService(config, store)
    service._save(
        [
            {
                "task_id": "task-1",
                "namespace": "bestie",
                "title": "Havi email emlékeztető",
                "task_type": "reminder",
                "schedule": "every 30d",
                "schedule_display": "every 30d",
                "status": "scheduled",
                "next_run_at": (hermes_now() + timedelta(hours=2)).isoformat(),
                "updated_at": "2026-03-31T00:00:00+00:00",
                "missed_count": 0,
            }
        ]
    )

    result = service.retrieve_task_context("mi a feladatom ma")

    assert "Havi email emlékeztető" in result["text"]


def test_task_service_filters_tasks_to_tomorrow_window(tmp_path):
    config = KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel", namespace="bestie")
    store = KernelMemoryStore.from_config(config)
    service = KernelMemoryTaskService(config, store)
    now = hermes_now()
    tomorrow = (now + timedelta(days=1)).replace(hour=18, minute=15, second=0, microsecond=0)
    today = now.replace(hour=14, minute=0, second=0, microsecond=0)
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
                "missed_count": 0,
            },
            {
                "task_id": "task-today",
                "namespace": "bestie",
                "title": "Feri taxi",
                "task_type": "reminder",
                "schedule_display": "once today 14:00",
                "status": "scheduled",
                "next_run_at": today.isoformat(),
                "updated_at": now.isoformat(),
                "missed_count": 0,
            },
        ]
    )

    result = service.retrieve_task_context("mik a holnapi teendőim?")

    assert "Viza-Vet" in result["text"]
    assert "Feri taxi" not in result["text"]


def test_task_service_uses_recent_temporal_focus_for_follow_up(tmp_path):
    config = KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel", namespace="bestie")
    store = KernelMemoryStore.from_config(config)
    service = KernelMemoryTaskService(config, store)
    now = hermes_now()
    tomorrow = (now + timedelta(days=1)).replace(hour=18, minute=15, second=0, microsecond=0)
    today = now.replace(hour=14, minute=0, second=0, microsecond=0)
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
                "missed_count": 0,
            },
            {
                "task_id": "task-today",
                "namespace": "bestie",
                "title": "Feri taxi",
                "task_type": "reminder",
                "schedule_display": "once today 14:00",
                "status": "scheduled",
                "next_run_at": today.isoformat(),
                "updated_at": now.isoformat(),
                "missed_count": 0,
            },
        ]
    )

    result = service.retrieve_task_context(
        "Mi van még?",
        recent_user_turns=["Te írd le hogy mik a holnapi teendőim!"],
    )

    assert "Viza-Vet" in result["text"]
    assert "Feri taxi" not in result["text"]


def test_task_service_filters_other_namespaces(tmp_path):
    config = KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel", namespace="bestie")
    store = KernelMemoryStore.from_config(config)
    service = KernelMemoryTaskService(config, store)
    now = hermes_now()
    service._save(
        [
            {
                "task_id": "task-bestie",
                "namespace": "bestie",
                "title": "Bestie task",
                "task_type": "reminder",
                "schedule_display": "once tomorrow 18:15",
                "status": "scheduled",
                "next_run_at": (now + timedelta(days=1)).isoformat(),
                "updated_at": now.isoformat(),
                "missed_count": 0,
            },
            {
                "task_id": "task-lulu",
                "namespace": "lulu",
                "title": "Lulu task",
                "task_type": "reminder",
                "schedule_display": "once tomorrow 19:15",
                "status": "scheduled",
                "next_run_at": (now + timedelta(days=1, hours=1)).isoformat(),
                "updated_at": now.isoformat(),
                "missed_count": 0,
            },
        ]
    )

    result = service.retrieve_task_context("mik a holnapi teendőim?")

    assert "Bestie task" in result["text"]
    assert "Lulu task" not in result["text"]


def test_task_service_records_job_outcome_updates_persisted_task(tmp_path, monkeypatch):
    import agent.kernel_memory_tasks as tasks_mod

    config = KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel", namespace="bestie")
    store = KernelMemoryStore.from_config(config)
    service = KernelMemoryTaskService(config, store)
    service._save(
        [
            {
                "task_id": "task-1",
                "namespace": "bestie",
                "title": "Viza-Vet",
                "task_type": "reminder",
                "schedule_display": "once tomorrow 18:15",
                "status": "scheduled",
                "cron_job_id": "job-1",
                "updated_at": "2026-04-01T00:00:00+00:00",
                "completed_count": 0,
                "missed_count": 0,
            }
        ]
    )
    monkeypatch.setattr(
        tasks_mod,
        "get_job",
        lambda job_id: {
            "id": job_id,
            "last_run_at": "2026-04-02T10:00:00+00:00",
            "next_run_at": None,
            "last_error": None,
            "schedule_display": "completed once",
            "schedule": {"kind": "once"},
            "state": "completed",
        },
    )

    service.record_job_outcome(
        {"id": "job-1", "metadata": {"task_id": "task-1"}, "repeat": {"times": 1}},
        success=True,
        final_response="done",
    )

    task = service.list_tasks()[0]
    assert task["status"] == "completed"
    assert task["completed_count"] == 1
    assert task["last_run_at"] == "2026-04-02T10:00:00+00:00"


def test_task_service_records_missed_notice_updates_persisted_task(tmp_path, monkeypatch):
    import agent.kernel_memory_tasks as tasks_mod

    config = KernelMemoryConfig(enabled=True, root_dir=tmp_path / "kernel", namespace="bestie")
    store = KernelMemoryStore.from_config(config)
    service = KernelMemoryTaskService(config, store)
    service._save(
        [
            {
                "task_id": "task-1",
                "namespace": "bestie",
                "title": "Viza-Vet",
                "task_type": "reminder",
                "schedule_display": "once tomorrow 18:15",
                "status": "scheduled",
                "cron_job_id": "job-1",
                "updated_at": "2026-04-01T00:00:00+00:00",
                "completed_count": 0,
                "missed_count": 0,
            }
        ]
    )
    monkeypatch.setattr(
        tasks_mod,
        "get_job",
        lambda job_id: {
            "id": job_id,
            "last_run_at": None,
            "next_run_at": "2026-04-03T10:00:00+00:00",
            "last_error": None,
            "schedule_display": "retry tomorrow",
            "schedule": {"kind": "once"},
            "state": "missed",
        },
    )

    service.record_missed_notice(
        {"id": "job-1", "metadata": {"task_id": "task-1"}},
        notice_message="missed",
    )

    task = service.list_tasks()[0]
    assert task["status"] == "missed"
    assert task["missed_count"] == 1
    assert task["next_run_at"] == "2026-04-03T10:00:00+00:00"
