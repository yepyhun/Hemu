from __future__ import annotations

from agent.kernel_memory import KernelMemoryConfig, KernelMemoryStore
from agent.kernel_memory_fusion import KernelMemoryFusionPolicy
from agent.kernel_memory_query_planner import KernelMemoryQueryPlanner
from agent.kernel_memory_value_anchor_priority import (
    value_anchor_priority_adjustment,
    value_anchor_signals,
)


def test_value_anchor_priority_detects_quoted_query_values():
    signals = value_anchor_signals('Is my favorite quote "Egyik szél sem jó annak a hajósnak"?')

    assert signals
    assert signals[0].startswith("value:")


def test_value_anchor_priority_boosts_exact_quote_match():
    item = {
        "content": 'Favorite quote: "Egyik szél sem jó annak a hajósnak, aki nem tudja melyik kikötőbe tart."',
    }

    bonus = value_anchor_priority_adjustment(
        item,
        query='Is my favorite quote "Egyik szél sem jó annak a hajósnak"?',
    )

    assert bonus >= 5


def test_fusion_policy_prioritizes_exact_value_match_for_quoted_query(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(
            enabled=True,
            root_dir=tmp_path / "kernel",
            namespace="bestie",
            curated_retrieval_only=False,
        )
    )
    planner = KernelMemoryQueryPlanner(store.config, store)
    fusion = KernelMemoryFusionPolicy(store.config)

    plan = planner.plan(
        'Is my favorite quote "Egyik szél sem jó annak a hajósnak"?',
        max_records=3,
        max_chars=900,
        namespaces={"bestie"},
    )
    route_results = {
        "semantic": {
            "items": [
                {
                    "id": "wrong",
                    "kind": "claim",
                    "route": "semantic",
                    "evidence_class": "semantic_lexical",
                    "status": "active",
                    "content": 'Favorite quote: "Nem az vagyok ami történt velem."',
                },
                {
                    "id": "right",
                    "kind": "claim",
                    "route": "semantic",
                    "evidence_class": "semantic_lexical",
                    "status": "active",
                    "content": 'Favorite quote: "Egyik szél sem jó annak a hajósnak, aki nem tudja melyik kikötőbe tart."',
                },
            ],
        },
    }

    fused = fusion.fuse(
        query=plan.normalized_query,
        plan=plan,
        route_results=route_results,
        max_records=2,
    )

    assert fused[0].record_id == "right"
