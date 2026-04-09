from __future__ import annotations

from agent.kernel_memory import KernelMemoryConfig, KernelMemoryStore
from agent.kernel_memory_fact_facets import extract_fact_facets


def test_extract_fact_facets_captures_money_age_and_descriptor_pairs():
    facets = extract_fact_facets(
        "I'm 32 and I bought a $325,000 house. I want a collar that suits a Golden Retriever like Max."
    )

    assert facets["age_value"] == 32
    assert facets["money_values"][0]["text"] == "$325,000"
    assert any(item["descriptor"] == "Golden Retriever" and item["entity"] == "Max" for item in facets["descriptor_pairs"])


def test_semantic_retrieval_renders_fact_facets_for_claims(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(
            enabled=True,
            root_dir=tmp_path / "kernel",
            namespace="bestie",
            curated_retrieval_only=False,
        )
    )
    facets = extract_fact_facets("I'm 32 and I bought a $325,000 house.")
    store.ingest_claim(
        claim_type="user_fact",
        content="I'm 32 and I bought a $325,000 house.",
        fact_facets=facets,
        observed_at="2023-05-24T12:00:00+00:00",
        metadata={"origin": "test"},
    )

    result = store.retrieve_semantic_context(
        "$325,000",
        max_records=2,
        max_chars=1200,
        namespaces={"bestie"},
    )

    assert "Facts:" in result["text"]
    assert "$325,000" in result["text"]
    assert "Observed: 2023-05-24" in result["text"]


def test_graph_retrieval_renders_event_dates_and_fact_facets(tmp_path):
    store = KernelMemoryStore.from_config(
        KernelMemoryConfig(
            enabled=True,
            root_dir=tmp_path / "kernel",
            namespace="bestie",
            curated_retrieval_only=False,
        )
    )
    rachel = store.upsert_entity(name="Rachel", entity_type="person")
    event = store.ingest_event(
        event_type="personal_event",
        title="Personal event: Ukulele lesson with Rachel",
        summary="I started taking ukulele lessons with Rachel.",
        actor_entity_id=None,
        counterparty_entity_ids=[rachel["id"]],
        fact_facets=extract_fact_facets("I started taking ukulele lessons with Rachel on Wednesday."),
        temporal_markers=["wednesday"],
        observed_at="2023-02-01T12:00:00+00:00",
        claim_ids=[],
        entity_ids=[rachel["id"]],
        relation_ids=[],
        source_ids=[],
    )

    result = store.retrieve_graph_context(
        "Rachel Wednesday",
        max_records=2,
        max_chars=1200,
        namespaces={"bestie"},
    )

    assert event["id"] in {item["id"] for item in result["items"]}
    assert "date=2023-02-01" in result["text"]
    assert "Fact facets:" in result["text"]
