from __future__ import annotations

from agent.memory_plan_delivery_audit import run_memory_plan_delivery_audit


def test_memory_plan_delivery_audit_reports_all_plan_checks_green(tmp_path):
    payload = run_memory_plan_delivery_audit(root_dir=tmp_path / "audit")

    assert payload["ok"] is True
    assert payload["failed_checks"] == []
    assert {"architect", "terv5", "terv7", "terv8", "terv9", "terv10"} == set(payload["plans"])
    assert payload["plans"]["terv5"]["passed"] >= 3
    assert payload["plans"]["terv10"]["total"] == 1
