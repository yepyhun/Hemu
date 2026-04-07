from __future__ import annotations

from typing import Any, Dict


class Core2MaintenanceEngine:
    """Local deterministic maintenance loops for Phase 2 state semantics."""

    def __init__(self, store):
        self.store = store

    def propose_merges(self) -> Dict[str, Any]:
        clusters = self.store.find_identity_clusters()
        merge_candidates = sum(max(len(cluster) - 1, 0) for cluster in clusters if len(cluster) > 1)
        return {"merge_candidates": merge_candidates}

    def detect_conflicts(self) -> Dict[str, Any]:
        conflicts_marked = 0
        for cluster in self.store.find_identity_clusters(include_inactive=False):
            normalized_contents = {record["content"].strip().lower() for record in cluster}
            if len(cluster) > 1 and len(normalized_contents) > 1:
                primary = cluster[0]
                for other in cluster[1:]:
                    if self.store.mark_conflict(primary["object_id"], other["object_id"], "identity_cluster_conflict"):
                        conflicts_marked += 1
        return {"conflicts_marked": conflicts_marked}

    def detect_supersessions(self) -> Dict[str, Any]:
        superseded = 0
        for record in self.store.list_canonical_objects(include_inactive=False):
            target = (record.get("metadata") or {}).get("supersedes")
            if not target:
                continue
            if self.store.supersede_object(record["object_id"], str(target), "maintenance_supersession"):
                superseded += 1
        return {"superseded_records": superseded}

    def demote_stale_provisionals(self, *, now: str | None = None, stale_days: int = 30) -> Dict[str, Any]:
        archived = self.store.archive_stale_provisionals(now=now, stale_days=stale_days)
        return {"stale_provisionals_archived": archived}

    def rebuild_indices(self) -> Dict[str, Any]:
        rebuilt = 0
        for record in self.store.list_canonical_objects(include_inactive=False):
            self.store.rebuild_indices_for_object(record["object_id"])
            rebuilt += 1
        return {"indices_rebuilt": rebuilt}

    def activation_decay(self) -> Dict[str, Any]:
        decayed = self.store.apply_activation_decay()
        return {"activation_updates": decayed}

    def run_all(self, *, now: str | None = None, stale_days: int = 30) -> Dict[str, Any]:
        result = {}
        result.update(self.propose_merges())
        result.update(self.detect_conflicts())
        result.update(self.detect_supersessions())
        result.update(self.demote_stale_provisionals(now=now, stale_days=stale_days))
        result.update(self.rebuild_indices())
        result.update(self.activation_decay())
        return result
