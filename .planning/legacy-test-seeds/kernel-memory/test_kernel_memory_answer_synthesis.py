from __future__ import annotations

from agent.kernel_memory import KernelMemoryConfig, KernelMemoryStore
from agent.kernel_memory_fact_facets import extract_fact_facets
from agent.kernel_memory_objective_executor import KernelMemoryObjectiveExecutor
from agent.kernel_memory_retrieval import KernelMemoryRetriever
from agent.kernel_memory_runtime import KernelMemoryRuntime


def test_preview_retrieval_surfaces_aggregate_total_synthesis(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        curated_retrieval_only=False,
        retrieval_policy_order=["semantic", "curated"],
    )
    store = KernelMemoryStore.from_config(config)
    store.ingest_claim(
        claim_type="purchase",
        content="I bought a luxury watch for $1,200 last month.",
        fact_facets=extract_fact_facets("I bought a luxury watch for $1,200 last month."),
    )
    store.ingest_claim(
        claim_type="purchase",
        content="I bought a luxury designer handbag for $800 this month.",
        fact_facets=extract_fact_facets("I bought a luxury designer handbag for $800 this month."),
    )
    store.materialize_curated_memory(
        title="Luxury spending summary",
        summary="The user has been buying luxury items recently.",
    )
    retriever = KernelMemoryRetriever(config, store)

    preview = retriever.preview_retrieval(
        "What is the total amount I spent on luxury items?",
        max_records=6,
        max_chars=1800,
    )

    synthesis = preview["retrieval"]["answer_synthesis"]["text"]
    assert synthesis.startswith("Answer-bearing synthesis:")
    assert "$2,000" in synthesis
    assert "$1,200" in synthesis
    assert "$800" in synthesis
    preview_text = preview["retrieval"]["text"]
    assert preview_text.startswith(
        (
            "Resolved answer from kernel memory:",
            "Best candidate answer from kernel memory:",
            "Answer-bearing synthesis:",
        )
    )
    assert (
        synthesis in preview_text
        or "Total identified amount: $2,000." in preview_text
        or "$2,000" in preview_text
    )


def test_preview_retrieval_marks_resolved_answer_as_final_for_runtime(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        curated_retrieval_only=False,
        retrieval_policy_order=["semantic", "curated"],
    )
    store = KernelMemoryStore.from_config(config)
    store.ingest_claim(
        claim_type="purchase",
        content="I bought a luxury watch for $1,200 last month.",
        fact_facets=extract_fact_facets("I bought a luxury watch for $1,200 last month."),
    )
    store.ingest_claim(
        claim_type="purchase",
        content="I bought a luxury designer handbag for $800 this month.",
        fact_facets=extract_fact_facets("I bought a luxury designer handbag for $800 this month."),
    )
    retriever = KernelMemoryRetriever(config, store)
    preview = retriever.preview_retrieval(
        "What is the total amount I spent on luxury items?",
        max_records=6,
        max_chars=1800,
    )

    contract = KernelMemoryRuntime._kernel_prompt_contract(
        result={
            **dict(preview["retrieval"]),
            "answer_packet": {
                **dict(preview["retrieval"]["answer_packet"] or {}),
                "resolved_answer_final": True,
                "direct_answer_available": True,
                "resolved_answer_text": "$2,000",
                "should_abstain": False,
            },
            "objective_execution": {
                **dict(preview["retrieval"]["objective_execution"] or {}),
                "supported": True,
            },
        },
        effective_as_of=None,
    )
    lowered_contract = contract.lower()
    assert "grounded final answer" in lowered_contract
    assert "do not say the information is missing" in lowered_contract
    assert "return this resolved answer text verbatim as your complete answer unless the user explicitly asks for elaboration: $2,000".lower() in lowered_contract


def test_preview_retrieval_final_compact_delivery_stays_minimal(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        curated_retrieval_only=False,
        retrieval_policy_order=["semantic", "curated"],
    )
    store = KernelMemoryStore.from_config(config)
    store.ingest_claim(
        claim_type="purchase",
        content="I bought a luxury watch for $1,200 last month.",
        fact_facets=extract_fact_facets("I bought a luxury watch for $1,200 last month."),
        metadata={"speaker_role": "user"},
    )
    store.ingest_claim(
        claim_type="purchase",
        content="I bought a luxury designer handbag for $800 this month.",
        fact_facets=extract_fact_facets("I bought a luxury designer handbag for $800 this month."),
        metadata={"speaker_role": "user"},
    )
    retriever = KernelMemoryRetriever(config, store)

    preview = retriever.preview_retrieval(
        "What is the total amount I spent on luxury items?",
        max_records=6,
        max_chars=1800,
    )

    preview_text = preview["retrieval"]["text"]
    assert preview["retrieval"]["answer_packet"]["delivery_tier"] in {"final_compact", "supported_compact"}
    assert preview_text.startswith(
        (
            "Resolved answer from kernel memory: $2,000",
            "Best candidate answer from kernel memory: $2,000",
        )
    )
    assert "Support:" not in preview_text


def test_preview_retrieval_aggregate_total_does_not_drop_semantically_related_amounts(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        curated_retrieval_only=False,
        retrieval_policy_order=["semantic", "curated"],
    )
    store = KernelMemoryStore.from_config(config)
    store.ingest_claim(
        claim_type="purchase",
        content="I bought a luxury Gucci handbag for $1,200.",
        fact_facets=extract_fact_facets("I bought a luxury Gucci handbag for $1,200."),
        metadata={"memory_class": "shopping"},
    )
    store.ingest_claim(
        claim_type="purchase",
        content="I bought Italian designer boots for $500.",
        fact_facets=extract_fact_facets("I bought Italian designer boots for $500."),
        metadata={"memory_class": "shopping"},
    )
    store.ingest_claim(
        claim_type="purchase",
        content="I bought a luxury evening gown for $800.",
        fact_facets=extract_fact_facets("I bought a luxury evening gown for $800."),
        metadata={"memory_class": "shopping"},
    )
    retriever = KernelMemoryRetriever(config, store)

    preview = retriever.preview_retrieval(
        "What is the total amount I spent on luxury items in the past few months?",
        max_records=8,
        max_chars=2200,
    )

    synthesis = preview["retrieval"]["answer_synthesis"]["text"]
    assert "$2,500" in synthesis
    assert "$1,200" in synthesis
    assert "$500" in synthesis
    assert "$800" in synthesis


def test_preview_retrieval_aggregate_total_uses_local_sentence_window_for_money_scope(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        curated_retrieval_only=False,
        retrieval_policy_order=["semantic", "curated"],
    )
    store = KernelMemoryStore.from_config(config)
    store.ingest_claim(
        claim_type="purchase",
        content=(
            "I've been noticing that I tend to splurge on luxury items when I'm feeling stressed or celebratory, "
            "like when I recently bought a luxury evening gown for a wedding. "
            "It was a big purchase, $800, but I felt like I needed to make a good impression."
        ),
        fact_facets=extract_fact_facets(
            "I've been noticing that I tend to splurge on luxury items when I'm feeling stressed or celebratory, "
            "like when I recently bought a luxury evening gown for a wedding. "
            "It was a big purchase, $800, but I felt like I needed to make a good impression."
        ),
        metadata={"memory_class": "shopping"},
    )
    store.ingest_claim(
        claim_type="purchase",
        content="I bought a high-end designer bag for $1,200.",
        fact_facets=extract_fact_facets("I bought a high-end designer bag for $1,200."),
        metadata={"memory_class": "shopping"},
    )
    retriever = KernelMemoryRetriever(config, store)

    preview = retriever.preview_retrieval(
        "What is the total amount I spent on luxury items in the past few months?",
        max_records=8,
        max_chars=2200,
    )

    synthesis = preview["retrieval"]["answer_synthesis"]["text"]
    assert "$2,000" in synthesis
    assert "$800" in synthesis
    assert "$1,200" in synthesis


def test_objective_executor_aggregate_total_backfills_linked_money_support(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        curated_retrieval_only=False,
        retrieval_policy_order=["graph", "semantic", "curated"],
    )
    store = KernelMemoryStore.from_config(config)
    event_claim = store.ingest_claim(
        claim_type="purchase",
        content=(
            "I recently bought a luxury evening gown for a wedding. "
            "It was a big purchase, $800, but I felt like I needed to make a good impression."
        ),
        fact_facets=extract_fact_facets(
            "I recently bought a luxury evening gown for a wedding. "
            "It was a big purchase, $800, but I felt like I needed to make a good impression."
        ),
    )
    event = store.ingest_event(
        event_type="purchase",
        title="Luxury evening gown purchase",
        summary="I recently bought a luxury evening gown for a wedding.",
        claim_ids=[event_claim["id"]],
    )
    gucci_claim = store.ingest_claim(
        claim_type="purchase",
        content="I bought a designer Gucci handbag for $1,200.",
        fact_facets=extract_fact_facets("I bought a designer Gucci handbag for $1,200."),
    )
    executor = KernelMemoryObjectiveExecutor(config, store)
    result = executor.execute(
        query="What is the total amount I spent on luxury items in the past few months?",
        items=[
            {
                **event,
                "route": "graph",
            },
            {
                **gucci_claim,
                "route": "semantic",
            },
        ],
    )

    assert result.supported is True
    assert any("$2,000" in line for line in result.lines)
    assert any("$800" in line for line in result.lines)
    assert any("$1,200" in line for line in result.lines)


def test_objective_executor_aggregate_total_uses_store_backed_claim_units_before_raw_fallback(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        curated_retrieval_only=False,
        retrieval_policy_order=["graph", "semantic", "curated"],
    )
    store = KernelMemoryStore.from_config(config)
    boots_claim = store.ingest_claim(
        claim_type="purchase",
        content="But I've also made some luxury purchases, like a pair of leather boots from a high-end Italian designer that I got for $500.",
        fact_facets=extract_fact_facets(
            "But I've also made some luxury purchases, like a pair of leather boots from a high-end Italian designer that I got for $500."
        ),
        metadata={"speaker_role": "user"},
    )
    gown_claim = store.ingest_claim(
        claim_type="purchase",
        content="I've been noticing that I tend to splurge on luxury items when I'm feeling stressed or celebratory, like when I recently bought a luxury evening gown for a wedding. It was a big purchase, $800, but I felt like I needed to make a good impression.",
        fact_facets=extract_fact_facets(
            "I've been noticing that I tend to splurge on luxury items when I'm feeling stressed or celebratory, like when I recently bought a luxury evening gown for a wedding. It was a big purchase, $800, but I felt like I needed to make a good impression."
        ),
        metadata={"speaker_role": "user"},
    )
    store.ingest_claim(
        claim_type="purchase",
        content="I've been noticing that I tend to splurge on luxury items every now and then, like that designer handbag I just got from Gucci for $1,200, but I also try to balance it out with more budget-friendly options.",
        fact_facets=extract_fact_facets(
            "I've been noticing that I tend to splurge on luxury items every now and then, like that designer handbag I just got from Gucci for $1,200, but I also try to balance it out with more budget-friendly options."
        ),
        metadata={"speaker_role": "user"},
    )
    executor = KernelMemoryObjectiveExecutor(config, store)

    result = executor.execute(
        query="What is the total amount I spent on luxury items in the past few months?",
        items=[
            {**boots_claim, "route": "semantic"},
            {**gown_claim, "route": "semantic"},
        ],
    )

    assert result.supported is True
    assert result.lines[0] == "$2,500"
    assert any("$500" in line for line in result.lines)
    assert any("$800" in line for line in result.lines)
    assert any("$1,200" in line for line in result.lines)


def test_objective_executor_aggregate_total_ignores_unlinked_irrelevant_money_units(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        curated_retrieval_only=False,
        retrieval_policy_order=["graph", "semantic", "curated"],
    )
    store = KernelMemoryStore.from_config(config)
    luxury_claim = store.ingest_claim(
        claim_type="purchase",
        content="I bought a luxury evening gown for $800.",
        fact_facets=extract_fact_facets("I bought a luxury evening gown for $800."),
        metadata={"speaker_role": "user", "memory_class": "shopping"},
    )
    store.ingest_claim(
        claim_type="budget",
        content="My camera budget is about $400, and accessories will cost another $300.",
        fact_facets=extract_fact_facets("My camera budget is about $400, and accessories will cost another $300."),
        metadata={"speaker_role": "user", "memory_class": "photography"},
    )
    store.ingest_claim(
        claim_type="purchase",
        content="I bought a designer handbag for $1,200.",
        fact_facets=extract_fact_facets("I bought a designer handbag for $1,200."),
        metadata={"speaker_role": "user", "memory_class": "shopping"},
    )
    event = store.ingest_event(
        event_type="purchase",
        title="Luxury gown purchase",
        summary="I bought a luxury evening gown.",
        claim_ids=[luxury_claim["id"]],
    )
    executor = KernelMemoryObjectiveExecutor(config, store)

    result = executor.execute(
        query="What is the total amount I spent on luxury items in the past few months?",
        items=[{**event, "route": "graph"}],
        expected_objective="aggregate_total",
    )

    assert result.supported is True
    assert result.lines[0] == "$2,000"
    assert "$400" not in " ".join(result.lines)
    assert "$300" not in " ".join(result.lines)


def test_preview_retrieval_surfaces_event_answer_synthesis(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        curated_retrieval_only=False,
        retrieval_policy_order=["semantic", "graph"],
    )
    store = KernelMemoryStore.from_config(config)
    claim = store.ingest_claim(
        claim_type="dated_fact",
        content="I started taking ukulele lessons with Rachel on Wednesday.",
    )
    store.ingest_event(
        event_type="lesson_start",
        title="Ukulele lessons with Rachel",
        summary="I started taking ukulele lessons with Rachel.",
        claim_ids=[claim["id"]],
        temporal_markers=["Wednesday"],
    )
    retriever = KernelMemoryRetriever(config, store)

    preview = retriever.preview_retrieval(
        "What did I do with Rachel on Wednesday?",
        max_records=5,
        max_chars=1800,
    )

    synthesis = preview["retrieval"]["answer_synthesis"]["text"]
    assert "I started taking ukulele lessons with Rachel." in synthesis


def test_retrieval_promotes_grounded_event_answer_to_final_compact(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        curated_retrieval_only=False,
        retrieval_policy_order=["semantic", "graph"],
    )
    store = KernelMemoryStore.from_config(config)
    claim = store.ingest_claim(
        claim_type="dated_fact",
        content="I started taking ukulele lessons with Rachel on Wednesday.",
        fact_facets=extract_fact_facets("I started taking ukulele lessons with Rachel on Wednesday."),
        observed_at="2023-02-01T12:00:00+00:00",
        metadata={"speaker_role": "user", "primary_language": "en"},
    )
    store.ingest_event(
        event_type="lesson_start",
        title="Ukulele lessons with Rachel",
        summary="I started taking ukulele lessons with Rachel.",
        claim_ids=[claim["id"]],
        observed_at="2023-02-01T12:00:00+00:00",
        temporal_markers=["Wednesday"],
        metadata={"speaker_role": "user", "primary_language": "en"},
    )

    result = KernelMemoryRetriever(config, store).retrieve_context_by_policy(
        "What did I do with Rachel on Wednesday?",
        max_records=5,
        max_chars=1400,
        namespaces={"bestie"},
        route_order=["semantic", "graph"],
        response_mode=store.classify_query_response_mode("What did I do with Rachel on Wednesday?"),
        as_of="2023-04-01T12:00:00+00:00",
    )

    assert result["answer_packet"]["delivery_tier"] == "final_compact"
    assert result["answer_packet"]["resolved_answer_final"] is True
    assert result["answer_packet"]["resolved_answer_text"] == "I started taking ukulele lessons with Rachel."


def test_preview_retrieval_surfaces_recommendation_grounding(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        curated_retrieval_only=False,
        retrieval_policy_order=["semantic", "curated"],
    )
    store = KernelMemoryStore.from_config(config)
    store.ingest_claim(
        claim_type="preference",
        content="I prefer relaxing activities in the evening before 9:30 pm.",
        metadata={"memory_class": "profile_preference"},
    )
    store.ingest_claim(
        claim_type="constraint",
        content="I should avoid using my phone or watching TV in the evening because it hurts my sleep quality.",
        metadata={"memory_class": "profile_preference", "polarity": "dont"},
    )
    retriever = KernelMemoryRetriever(config, store)

    preview = retriever.preview_retrieval(
        "Can you suggest some activities that I can do in the evening?",
        max_records=6,
        max_chars=1800,
    )

    synthesis = preview["retrieval"]["answer_synthesis"]["text"]
    assert "The user would prefer suggestions" in synthesis
    assert "before 9:30 pm" in synthesis
    assert "They would not prefer suggestions" in synthesis
    assert "sleep quality" in synthesis


def test_preview_retrieval_prefers_compact_named_answer_over_scaffolding(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        curated_retrieval_only=False,
        retrieval_policy_order=["semantic", "curated", "graph"],
    )
    store = KernelMemoryStore.from_config(config)
    store.ingest_extract(
        resource_id="res_vatican_foods",
        content=(
            "There are many great food options near the Vatican. "
            "One popular option is Pizzarium. "
            "There's also Roscioli, a famous deli that serves the best cured meats, cheeses, "
            "and traditional Roman cuisine."
        ),
        metadata={"speaker_role": "assistant"},
    )
    store.materialize_curated_memory(
        title="Conversation memory: I'm excited to see the Sistine Chapel and St. Peter's Basilica.",
        summary=(
            "I'm excited to see the Sistine Chapel and St. Peter's Basilica. "
            "Any recommendations for good places to eat nearby?"
        ),
    )
    retriever = KernelMemoryRetriever(config, store)

    preview = retriever.preview_retrieval(
        "Can you remind me of the name of that famous deli near the Vatican with the cured meats and cheeses?",
        max_records=6,
        max_chars=2200,
    )

    synthesis = preview["retrieval"]["answer_synthesis"]["text"]
    assert "Roscioli" in synthesis
    assert "Sistine Chapel" not in synthesis


def test_preview_retrieval_descriptor_lookup_prefers_supported_entity_over_nearby_name_noise(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        curated_retrieval_only=False,
        retrieval_policy_order=["semantic", "curated", "graph"],
    )
    store = KernelMemoryStore.from_config(config)
    store.ingest_extract(
        resource_id="res_vatican_noise",
        content=(
            "There are many great food options near the Vatican. "
            "Caffè Vaticano is a nice cafe, and there's also Roscioli, "
            "a famous deli that serves cured meats, cheeses, and Roman dishes."
        ),
        metadata={"speaker_role": "assistant"},
    )
    retriever = KernelMemoryRetriever(config, store)

    preview = retriever.preview_retrieval(
        "Can you remind me of the name of that famous deli near the Vatican with the cured meats and cheeses?",
        max_records=6,
        max_chars=2200,
    )

    synthesis = preview["retrieval"]["answer_synthesis"]["text"]
    assert "Roscioli" in synthesis
    assert "Caffè Vaticano" not in synthesis


def test_objective_executor_surfaces_general_descriptor_answer(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        curated_retrieval_only=False,
        retrieval_policy_order=["semantic", "curated"],
    )
    store = KernelMemoryStore.from_config(config)
    claim = store.ingest_claim(
        claim_type="pet_fact",
        content="Do you have any recommendations for a good collar brand or type that would suit a Golden Retriever like Max?",
        fact_facets=extract_fact_facets(
            "Do you have any recommendations for a good collar brand or type that would suit a Golden Retriever like Max?"
        ),
    )
    executor = KernelMemoryObjectiveExecutor(config, store)

    result = executor.execute(
        query="What breed is my dog?",
        items=[
            {
                **claim,
                "route": "semantic",
            }
        ],
    )

    assert result.supported is True
    assert any("Golden Retriever" in line for line in result.lines)


def test_objective_executor_prefers_user_owned_descriptor_over_noisy_named_subject(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        curated_retrieval_only=False,
        retrieval_policy_order=["semantic", "curated"],
    )
    store = KernelMemoryStore.from_config(config)
    pet_claim = store.ingest_claim(
        claim_type="pet_fact",
        content="Do you have any recommendations for a good collar brand or type that would suit a Golden Retriever like Max?",
        fact_facets=extract_fact_facets(
            "Do you have any recommendations for a good collar brand or type that would suit a Golden Retriever like Max?"
        ),
        metadata={"speaker_role": "user"},
    )
    noisy_claim = store.ingest_claim(
        claim_type="music_fact",
        content="Max Richter is a contemporary composer known for soothing atmospheric soundscapes.",
        fact_facets=extract_fact_facets(
            "Max Richter is a contemporary composer known for soothing atmospheric soundscapes."
        ),
        metadata={"speaker_role": "assistant"},
    )
    executor = KernelMemoryObjectiveExecutor(config, store)

    result = executor.execute(
        query="What breed is my dog?",
        items=[
            {**noisy_claim, "route": "semantic"},
            {**pet_claim, "route": "semantic"},
        ],
    )

    assert result.supported is True
    assert result.lines[0] == "Golden Retriever"
    assert any("Golden Retriever like Max" in line for line in result.lines[1:])


def test_objective_executor_direct_attribute_units_short_circuit_broad_lookup(tmp_path, monkeypatch):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        curated_retrieval_only=False,
        retrieval_policy_order=["semantic", "curated"],
    )
    store = KernelMemoryStore.from_config(config)
    claim = store.ingest_claim(
        claim_type="pet_fact",
        content="Do you have any recommendations for a good collar brand or type that would suit a Golden Retriever like Max?",
        fact_facets=extract_fact_facets(
            "Do you have any recommendations for a good collar brand or type that would suit a Golden Retriever like Max?"
        ),
        metadata={"speaker_role": "user"},
    )
    executor = KernelMemoryObjectiveExecutor(config, store)

    def _unexpected_broad_scan(_kind: str):
        raise AssertionError("direct attribute lookup should not reopen broad record scans when fresh units exist")

    monkeypatch.setattr(store, "list_records", _unexpected_broad_scan)

    result = executor.execute(
        query="What breed is my dog?",
        items=[{**claim, "route": "semantic"}],
    )

    assert result.supported is True
    assert result.lines[0] == "Golden Retriever"
    assert result.metrics.get("attribute_mode") == "direct_attribute_unit"


def test_objective_executor_aggregate_count_uses_linked_support_labels(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        curated_retrieval_only=False,
        retrieval_policy_order=["graph", "semantic", "curated"],
    )
    store = KernelMemoryStore.from_config(config)
    claim = store.ingest_claim(
        claim_type="hobby_fact",
        content="I just got this 1/72 scale B-29 bomber kit and a 1/24 scale '69 Camaro at a model show.",
        fact_facets=extract_fact_facets(
            "I just got this 1/72 scale B-29 bomber kit and a 1/24 scale '69 Camaro at a model show."
        ),
    )
    event = store.ingest_event(
        event_type="purchase",
        title="Model kit purchases",
        summary="I picked up new model kits at a model show.",
        claim_ids=[claim["id"]],
    )
    executor = KernelMemoryObjectiveExecutor(config, store)

    result = executor.execute(
        query="How many model kits have I worked on or bought?",
        items=[{**event, "route": "graph"}],
    )

    assert result.supported is True
    assert any("model kits" in line for line in result.lines)
    assert any("B-29 bomber" in line for line in result.lines)


def test_objective_executor_direct_attribute_prefers_money_value_with_scope_match(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        curated_retrieval_only=False,
        retrieval_policy_order=["semantic", "curated"],
    )
    store = KernelMemoryStore.from_config(config)
    claim = store.ingest_claim(
        claim_type="finance_fact",
        content="I'm actually buying a $325,000 house, and I got pre-approved for $400,000 from Wells Fargo.",
        fact_facets=extract_fact_facets(
            "I'm actually buying a $325,000 house, and I got pre-approved for $400,000 from Wells Fargo."
        ),
        metadata={"speaker_role": "user"},
    )
    executor = KernelMemoryObjectiveExecutor(config, store)

    result = executor.execute(
        query="What was the amount I was pre-approved for when I got my mortgage from Wells Fargo?",
        items=[{**claim, "route": "semantic"}],
        expected_objective="direct_attribute",
    )

    assert result.supported is True
    assert result.objective == "direct_attribute"
    assert result.lines[0] == "$400,000"
    assert any("pre-approved for $400,000 from Wells Fargo" in line for line in result.lines[1:])


def test_objective_executor_direct_attribute_prefers_claim_truth_over_curated_mirror(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        curated_retrieval_only=False,
        retrieval_policy_order=["semantic", "curated"],
    )
    store = KernelMemoryStore.from_config(config)
    claim = store.ingest_claim(
        claim_type="finance_fact",
        content="I got pre-approved for $400,000 from Wells Fargo.",
        fact_facets=extract_fact_facets("I got pre-approved for $400,000 from Wells Fargo."),
        metadata={"speaker_role": "user"},
    )
    store.materialize_curated_memory(
        title="Mortgage note",
        summary="Wells Fargo mortgage pre-approval: $350,000.",
        source_ids=[claim["id"]],
    )
    executor = KernelMemoryObjectiveExecutor(config, store)

    result = executor.execute(
        query="What was the amount I was pre-approved for when I got my mortgage from Wells Fargo?",
        items=[],
        expected_objective="direct_attribute",
    )

    assert result.supported is True
    assert result.lines[0] == "$400,000"
    assert any("Wells Fargo" in line for line in result.lines[1:])


def test_preview_retrieval_surfaces_event_compare_synthesis(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        curated_retrieval_only=False,
        retrieval_policy_order=["semantic", "graph"],
    )
    store = KernelMemoryStore.from_config(config)
    instant_claim = store.ingest_claim(
        claim_type="purchase",
        content="I bought a new Instant Pot on Sunday.",
        fact_facets=extract_fact_facets("I bought a new Instant Pot on Sunday."),
        observed_at="2023-05-21T08:00:00+00:00",
    )
    air_claim = store.ingest_claim(
        claim_type="purchase",
        content="I bought an Air Fryer later that week.",
        fact_facets=extract_fact_facets("I bought an Air Fryer later that week."),
        observed_at="2023-05-24T08:00:00+00:00",
    )
    store.ingest_event(
        event_type="purchase",
        title="Instant Pot purchase",
        summary="I bought a new Instant Pot.",
        claim_ids=[instant_claim["id"]],
        temporal_markers=["Sunday"],
        observed_at="2023-05-21T08:00:00+00:00",
    )
    store.ingest_event(
        event_type="purchase",
        title="Air Fryer purchase",
        summary="I bought an Air Fryer.",
        claim_ids=[air_claim["id"]],
        temporal_markers=["later that week"],
        observed_at="2023-05-24T08:00:00+00:00",
    )
    retriever = KernelMemoryRetriever(config, store)

    preview = retriever.preview_retrieval(
        "What new kitchen gadget did I invest in before getting the Air Fryer?",
        max_records=6,
        max_chars=2000,
    )

    synthesis = preview["retrieval"]["answer_synthesis"]["text"]
    assert "Reference item: Air Fryer" in synthesis
    assert "Earlier/prior item identified: Instant Pot" in synthesis


def test_preview_retrieval_event_compare_ignores_generic_gadget_noise(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        curated_retrieval_only=False,
        retrieval_policy_order=["semantic", "graph", "curated"],
    )
    store = KernelMemoryStore.from_config(config)
    store.ingest_claim(
        claim_type="gift_search",
        content=(
            "I'm looking for some gift ideas for my brother's birthday. "
            "I've been thinking of getting him a new smartwatch or a high-tech gadget."
        ),
        fact_facets=extract_fact_facets(
            "I'm looking for some gift ideas for my brother's birthday. "
            "I've been thinking of getting him a new smartwatch or a high-tech gadget."
        ),
        metadata={"speaker_role": "user"},
        observed_at="2023-05-21T12:00:00+00:00",
    )
    instant_claim = store.ingest_claim(
        claim_type="purchase",
        content="I'm actually thinking of using my new Instant Pot to make some soups and stews.",
        fact_facets=extract_fact_facets(
            "I'm actually thinking of using my new Instant Pot to make some soups and stews."
        ),
        metadata={"speaker_role": "user"},
        observed_at="2023-05-21T05:48:00+00:00",
    )
    air_claim = store.ingest_claim(
        claim_type="purchase",
        content="I'm actually thinking of using the Air Fryer I got yesterday to make some crispy sweet potato fries.",
        fact_facets=extract_fact_facets(
            "I'm actually thinking of using the Air Fryer I got yesterday to make some crispy sweet potato fries."
        ),
        metadata={"speaker_role": "user"},
        observed_at="2023-05-21T22:54:00+00:00",
    )
    store.ingest_event(
        event_type="purchase",
        title="Instant Pot purchase",
        summary="I bought a new Instant Pot.",
        claim_ids=[instant_claim["id"]],
        observed_at="2023-05-21T05:48:00+00:00",
    )
    store.ingest_event(
        event_type="purchase",
        title="Air Fryer purchase",
        summary="I bought an Air Fryer.",
        claim_ids=[air_claim["id"]],
        observed_at="2023-05-21T22:54:00+00:00",
    )
    retriever = KernelMemoryRetriever(config, store)

    preview = retriever.preview_retrieval(
        "What new kitchen gadget did I invest in before getting the Air Fryer?",
        max_records=8,
        max_chars=2200,
    )

    synthesis = preview["retrieval"]["answer_synthesis"]["text"]
    assert "Earlier/prior item identified: Instant Pot" in synthesis
    assert "gift ideas for my brother's birthday" not in synthesis


def test_objective_executor_event_compare_handles_which_happened_first_queries(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        curated_retrieval_only=False,
        retrieval_policy_order=["semantic", "graph"],
    )
    store = KernelMemoryStore.from_config(config)
    meeting = store.ingest_claim(
        claim_type="meeting",
        content="I had a meeting with Rachel on April 10th about the project.",
        fact_facets=extract_fact_facets("I had a meeting with Rachel on April 10th about the project."),
        metadata={"speaker_role": "user"},
        observed_at="2023-04-10T10:00:00+00:00",
    )
    pride = store.ingest_claim(
        claim_type="event",
        content="I attended a pride parade in my city on May 1st.",
        fact_facets=extract_fact_facets("I attended a pride parade in my city on May 1st."),
        metadata={"speaker_role": "user"},
        observed_at="2023-05-01T12:00:00+00:00",
    )
    executor = KernelMemoryObjectiveExecutor(config, store)

    result = executor.execute(
        query="Which event happened first, the meeting with Rachel or the pride parade?",
        items=[
            {**meeting, "route": "semantic"},
            {**pride, "route": "semantic"},
        ],
    )

    assert result.supported is True
    assert result.lines
    assert result.lines[0].casefold() in {"meeting with rachel", "the meeting with rachel"}


def test_preview_retrieval_promotes_grounded_event_compare_to_final_compact(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        curated_retrieval_only=False,
        retrieval_policy_order=["semantic", "graph", "curated"],
    )
    store = KernelMemoryStore.from_config(config)
    store.ingest_claim(
        claim_type="life_event",
        content="Rachel became a parent in April 2023.",
        fact_facets=extract_fact_facets("Rachel became a parent in April 2023."),
        metadata={"speaker_role": "user"},
        observed_at="2023-04-20T10:00:00+00:00",
    )
    store.ingest_claim(
        claim_type="life_event",
        content="It's really interesting to hear about my cousin Alex becoming a parent in February 2023.",
        fact_facets=extract_fact_facets("It's really interesting to hear about my cousin Alex becoming a parent in February 2023."),
        metadata={"speaker_role": "user"},
        observed_at="2023-02-11T10:00:00+00:00",
    )
    retriever = KernelMemoryRetriever(config, store)

    preview = retriever.preview_retrieval(
        "Who became a parent first, Rachel or Alex?",
        max_records=6,
        max_chars=1600,
    )
    retrieval = preview["retrieval"]

    assert retrieval["answer_packet"]["delivery_tier"] == "final_compact"
    assert retrieval["answer_packet"]["resolved_answer_final"] is True
    assert retrieval["answer_packet"]["resolved_answer_text"] == "Alex"


def test_objective_executor_aggregate_count_filters_to_current_user_owned_domain_records(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        curated_retrieval_only=False,
        retrieval_policy_order=["semantic", "graph", "curated"],
    )
    store = KernelMemoryStore.from_config(config)
    store.ingest_claim(
        claim_type="instrument",
        content="I've had my black Fender Stratocaster electric guitar for about 5 years now.",
        fact_facets=extract_fact_facets("I've had my black Fender Stratocaster electric guitar for about 5 years now."),
        metadata={"speaker_role": "user"},
    )
    store.ingest_claim(
        claim_type="instrument",
        content="My Yamaha FG800 acoustic guitar has been a great companion for songwriting and camping trips.",
        fact_facets=extract_fact_facets("My Yamaha FG800 acoustic guitar has been a great companion for songwriting and camping trips."),
        metadata={"speaker_role": "user"},
    )
    store.ingest_claim(
        claim_type="instrument",
        content="I'm thinking of selling my old drum set, a 5-piece Pearl Export, which I haven't played in years.",
        fact_facets=extract_fact_facets("I'm thinking of selling my old drum set, a 5-piece Pearl Export, which I haven't played in years."),
        metadata={"speaker_role": "user"},
    )
    store.ingest_claim(
        claim_type="instrument",
        content="My Korg B1 piano has started to develop some sticky keys after about 3 years of use.",
        fact_facets=extract_fact_facets("My Korg B1 piano has started to develop some sticky keys after about 3 years of use."),
        metadata={"speaker_role": "user"},
    )
    noise = store.ingest_claim(
        claim_type="assistant_fact",
        content="As a language model, I can discuss musical instruments, but I do not own any myself.",
        fact_facets=extract_fact_facets("As a language model, I can discuss musical instruments, but I do not own any myself."),
        metadata={"speaker_role": "assistant"},
    )
    executor = KernelMemoryObjectiveExecutor(config, store)

    result = executor.execute(
        query="How many musical instruments do I currently own?",
        items=[{**noise, "route": "semantic"}],
    )

    assert result.supported is True
    assert result.lines[0] == "I currently own 4 musical instruments."
    assert any("Fender Stratocaster" in line for line in result.lines)
    assert any("Korg B1" in line for line in result.lines)
    assert result.metrics.get("direct_value_grounded") is True


def test_objective_executor_aggregate_count_ignores_generic_current_numeric_noise(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        curated_retrieval_only=False,
        retrieval_policy_order=["semantic", "graph", "curated"],
    )
    store = KernelMemoryStore.from_config(config)
    store.ingest_claim(
        claim_type="inventory_total",
        content="I currently own 4 musical instruments.",
        fact_facets=extract_fact_facets("I currently own 4 musical instruments."),
        metadata={"speaker_role": "user", "primary_language": "en"},
    )
    store.ingest_claim(
        claim_type="assistant_fact",
        content="According to the provided web search results, there are currently multiple job opportunities for Delphi programmers and developers in Thailand as of January 2023.",
        fact_facets=extract_fact_facets(
            "According to the provided web search results, there are currently multiple job opportunities for Delphi programmers and developers in Thailand as of January 2023."
        ),
        metadata={"speaker_role": "assistant", "primary_language": "en"},
    )
    executor = KernelMemoryObjectiveExecutor(config, store)

    result = executor.execute(
        query="How many musical instruments do I currently own?",
        items=[],
    )

    assert result.supported is True
    assert result.lines
    assert result.lines[0] == "I currently own 4 musical instruments."


def test_objective_executor_direct_attribute_uses_schedule_slot_units(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        curated_retrieval_only=False,
        retrieval_policy_order=["semantic", "curated"],
    )
    store = KernelMemoryStore.from_config(config)
    claim = store.ingest_claim(
        claim_type="routine",
        content="I wake up at 7:30 am on Saturday mornings.",
        fact_facets=extract_fact_facets("I wake up at 7:30 am on Saturday mornings."),
        metadata={"speaker_role": "user", "primary_language": "en"},
    )
    executor = KernelMemoryObjectiveExecutor(config, store)

    result = executor.execute(
        query="What time do I wake up on Saturday mornings?",
        items=[{**claim, "route": "semantic"}],
    )

    assert result.supported is True
    assert result.lines[0] == "7:30 am"
    assert result.metrics.get("attribute_mode") == "schedule_slot_unit"


def test_objective_executor_schedule_prefers_user_declared_schedule_over_assistant_suggestion(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        curated_retrieval_only=False,
        retrieval_policy_order=["semantic", "curated"],
    )
    store = KernelMemoryStore.from_config(config)
    assistant = store.ingest_claim(
        claim_type="assistant_fact",
        content="Wake up at 8:30 am on Saturdays to keep the routine consistent.",
        fact_facets=extract_fact_facets("Wake up at 8:30 am on Saturdays to keep the routine consistent."),
        metadata={"speaker_role": "assistant", "primary_language": "en"},
        observed_at="2023-05-23T14:15:00+00:00",
    )
    user = store.ingest_claim(
        claim_type="operational_rule",
        content="Also, what time should I start my jog, considering I like to wake up at 7:30 am on Saturdays?",
        fact_facets=extract_fact_facets("Also, what time should I start my jog, considering I like to wake up at 7:30 am on Saturdays?"),
        metadata={"speaker_role": "user", "primary_language": "en"},
        observed_at="2023-05-27T02:33:00+00:00",
    )
    executor = KernelMemoryObjectiveExecutor(config, store)

    result = executor.execute(
        query="What time do I wake up on Saturday mornings?",
        items=[{**assistant, "route": "semantic"}, {**user, "route": "semantic"}],
    )

    assert result.supported is True
    assert result.lines[0] == "7:30 am"
    assert result.metrics.get("attribute_mode") == "schedule_slot_unit"


def test_objective_executor_event_compare_can_return_temporal_delta(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        curated_retrieval_only=False,
        retrieval_policy_order=["semantic", "graph"],
    )
    store = KernelMemoryStore.from_config(config)
    spark = store.ingest_event(
        event_type="car_maintenance",
        title="Spark plug replacement",
        summary="I replaced my spark plugs.",
        observed_at="2023-05-01T10:00:00+00:00",
        metadata={"speaker_role": "user"},
    )
    turbo = store.ingest_event(
        event_type="auto_event",
        title="Turbocharged Tuesdays event",
        summary="I participated in the Turbocharged Tuesdays auto racking event.",
        observed_at="2023-05-30T10:00:00+00:00",
        metadata={"speaker_role": "user"},
    )
    executor = KernelMemoryObjectiveExecutor(config, store)

    result = executor.execute(
        query="How many days passed between the day I replaced my spark plugs and the day I participated in the Turbocharged Tuesdays auto racking event?",
        items=[{**spark, "route": "semantic"}, {**turbo, "route": "semantic"}],
    )

    assert result.supported is True
    assert result.lines[0] == "29 days"
    assert result.metrics.get("compare_mode") == "temporal_delta"


def test_objective_executor_temporal_delta_uses_calendar_day_difference(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        curated_retrieval_only=False,
        retrieval_policy_order=["semantic", "graph"],
    )
    store = KernelMemoryStore.from_config(config)
    spark = store.ingest_extract(
        resource_id="spark",
        content="I replaced my spark plugs with new ones from NGK today.",
        observed_at="2023-02-14T16:30:00+00:00",
        metadata={"speaker_role": "user", "session_id": "sess-1"},
    )
    turbo = store.ingest_extract(
        resource_id="turbo",
        content="I completed 10 laps during the Turbocharged Tuesdays event today.",
        observed_at="2023-03-15T08:38:00+00:00",
        metadata={"speaker_role": "user", "session_id": "sess-2"},
    )
    executor = KernelMemoryObjectiveExecutor(config, store)

    result = executor.execute(
        query="How many days passed between the day I replaced my spark plugs and the day I participated in the Turbocharged Tuesdays auto racking event?",
        items=[{**spark, "route": "semantic"}, {**turbo, "route": "semantic"}],
    )

    assert result.supported is True
    assert result.lines[0] == "29 days"


def test_objective_executor_temporal_delta_keeps_abbreviation_and_explicit_date_scope(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        curated_retrieval_only=False,
        retrieval_policy_order=["semantic", "graph"],
    )
    store = KernelMemoryStore.from_config(config)
    sunday = store.ingest_claim(
        content="By the way, I recently attended the Sunday mass at St. Mary's Church on January 2nd, and the sermon on forgiveness really resonated with me.",
        claim_type="dated_fact",
        observed_at="2023-02-20T16:21:00+00:00",
        metadata={"speaker_role": "user", "session_id": "sess-sunday"},
    )
    ash = store.ingest_claim(
        content="By the way, I just came from the Ash Wednesday service at the cathedral on February 1st, and it really made me reflect on the importance of giving back to the community.",
        claim_type="dated_fact",
        observed_at="2023-02-20T04:44:00+00:00",
        metadata={"speaker_role": "user", "session_id": "sess-ash"},
    )
    executor = KernelMemoryObjectiveExecutor(config, store)

    result = executor.execute(
        query="How many days had passed between the Sunday mass at St. Mary's Church and the Ash Wednesday service at the cathedral?",
        items=[{**sunday, "route": "semantic"}, {**ash, "route": "semantic"}],
    )

    assert result.supported is True
    assert result.lines[0] == "30 days"
    assert result.metrics.get("compare_mode") == "temporal_delta"


def test_objective_executor_duration_prefers_scoped_trip_duration(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        curated_retrieval_only=False,
        retrieval_policy_order=["semantic", "curated"],
    )
    store = KernelMemoryStore.from_config(config)
    japan = store.ingest_claim(
        claim_type="user_fact",
        content="I spent two weeks traveling solo around Japan.",
        fact_facets=extract_fact_facets("I spent two weeks traveling solo around Japan."),
        metadata={"speaker_role": "user", "primary_language": "en"},
        observed_at="2023-05-30T03:04:00+00:00",
    )
    barcelona = store.ingest_claim(
        claim_type="dated_fact",
        content="I was on a week-long vacation in Barcelona with my family.",
        fact_facets=extract_fact_facets("I was on a week-long vacation in Barcelona with my family."),
        metadata={"speaker_role": "user", "primary_language": "en"},
        observed_at="2023-05-28T23:29:00+00:00",
    )
    executor = KernelMemoryObjectiveExecutor(config, store)

    result = executor.execute(
        query="How long was I in Japan for?",
        items=[{**barcelona, "route": "semantic"}, {**japan, "route": "semantic"}],
    )

    assert result.supported is True
    assert result.lines[0] == "two weeks"
    assert result.metrics.get("attribute_mode") == "duration_unit"
    assert result.metrics.get("direct_value_grounded") is True


def test_objective_executor_temporal_relative_measures_against_as_of(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        curated_retrieval_only=False,
        retrieval_policy_order=["semantic", "graph"],
    )
    store = KernelMemoryStore.from_config(config)
    festival = store.ingest_event(
        event_type="personal_event",
        title="Seattle International Film Festival",
        summary="I attended the Seattle International Film Festival.",
        observed_at="2023-02-01T12:00:00+00:00",
        metadata={"speaker_role": "user"},
    )
    executor = KernelMemoryObjectiveExecutor(config, store)

    result = executor.execute(
        query="How many months ago did I attend the Seattle International Film Festival?",
        items=[{**festival, "route": "semantic"}],
        as_of="2023-06-01T12:00:00+00:00",
    )

    assert result.supported is True
    assert result.lines[0] == "4 months ago"
    assert result.metrics.get("compare_mode") == "temporal_relative"
    assert result.metrics.get("direct_value_grounded") is True


def test_objective_executor_aggregate_total_sums_duration_units_when_measure_requested(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        curated_retrieval_only=False,
        retrieval_policy_order=["semantic", "graph"],
    )
    store = KernelMemoryStore.from_config(config)
    ten_day_break = store.ingest_claim(
        claim_type="user_fact",
        content="I just got back from a 10-day break from social media in mid-February.",
        fact_facets=extract_fact_facets("I just got back from a 10-day break from social media in mid-February."),
        metadata={"speaker_role": "user", "primary_language": "en"},
        observed_at="2023-02-20T10:00:00+00:00",
    )
    week_break = store.ingest_claim(
        claim_type="user_fact",
        content="I even took a week-long break from social media in mid-January, and it was really refreshing.",
        fact_facets=extract_fact_facets("I even took a week-long break from social media in mid-January, and it was really refreshing."),
        metadata={"speaker_role": "user", "primary_language": "en"},
        observed_at="2023-01-20T10:00:00+00:00",
    )
    executor = KernelMemoryObjectiveExecutor(config, store)

    result = executor.execute(
        query="How many days did I take social media breaks in total?",
        items=[{**ten_day_break, "route": "semantic"}, {**week_break, "route": "semantic"}],
    )

    assert result.supported is True
    assert result.lines[0] == "17 days"
    assert result.metrics.get("aggregate_mode") == "duration_total_unit"
    assert result.metrics.get("direct_value_grounded") is True


def test_objective_executor_duration_total_ignores_unscoped_duration_units(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        curated_retrieval_only=False,
        retrieval_policy_order=["semantic", "graph"],
    )
    store = KernelMemoryStore.from_config(config)
    ten_day_break = store.ingest_claim(
        claim_type="user_fact",
        content="I just got back from a 10-day break from social media in mid-February.",
        fact_facets=extract_fact_facets("I just got back from a 10-day break from social media in mid-February."),
        metadata={"speaker_role": "user", "primary_language": "en"},
        observed_at="2023-02-20T10:00:00+00:00",
    )
    week_break = store.ingest_claim(
        claim_type="user_fact",
        content="I even took a week-long break from social media in mid-January, and it was really refreshing.",
        fact_facets=extract_fact_facets("I even took a week-long break from social media in mid-January, and it was really refreshing."),
        metadata={"speaker_role": "user", "primary_language": "en"},
        observed_at="2023-01-20T10:00:00+00:00",
    )
    unrelated_trip = store.ingest_claim(
        claim_type="user_fact",
        content="I spent 30 days backpacking across Spain last summer.",
        fact_facets=extract_fact_facets("I spent 30 days backpacking across Spain last summer."),
        metadata={"speaker_role": "user", "primary_language": "en"},
        observed_at="2023-08-20T10:00:00+00:00",
    )
    executor = KernelMemoryObjectiveExecutor(config, store)

    result = executor.execute(
        query="How many days did I take social media breaks in total?",
        items=[
            {**ten_day_break, "route": "semantic"},
            {**week_break, "route": "semantic"},
            {**unrelated_trip, "route": "semantic"},
        ],
    )

    assert result.supported is True
    assert result.lines[0] == "17 days"
    assert result.metrics.get("aggregate_mode") == "duration_total_unit"


def test_objective_executor_aggregate_average_prefers_scaled_numeric_measure_units(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        curated_retrieval_only=False,
        retrieval_policy_order=["semantic", "graph"],
    )
    store = KernelMemoryStore.from_config(config)
    graduate = store.ingest_claim(
        claim_type="user_fact",
        content="I recently completed my Master's degree in Data Science from the University of Illinois at Urbana-Champaign, where I maintained a GPA of 3.8 out of 4.0.",
        fact_facets=extract_fact_facets("I recently completed my Master's degree in Data Science from the University of Illinois at Urbana-Champaign, where I maintained a GPA of 3.8 out of 4.0."),
        metadata={"speaker_role": "user", "primary_language": "en"},
        observed_at="2023-05-24T10:17:00+00:00",
    )
    undergraduate = store.ingest_claim(
        claim_type="user_fact",
        content="I graduated with a First-Class distinction in Computer Science from the University of Mumbai, with an overall percentage of 83%, equivalent to a GPA of 3.86 out of 4.0.",
        fact_facets=extract_fact_facets("I graduated with a First-Class distinction in Computer Science from the University of Mumbai, with an overall percentage of 83%, equivalent to a GPA of 3.86 out of 4.0."),
        metadata={"speaker_role": "user", "primary_language": "en"},
        observed_at="2023-05-30T04:37:00+00:00",
    )
    executor = KernelMemoryObjectiveExecutor(config, store)

    result = executor.execute(
        query="What is the average GPA of my undergraduate and graduate studies?",
        items=[{**graduate, "route": "semantic"}, {**undergraduate, "route": "semantic"}],
    )

    assert result.supported is True
    assert result.lines[0] == "3.83"
    assert result.metrics.get("aggregate_mode") == "numeric_average_unit"
    assert result.metrics.get("direct_value_grounded") is True


def test_preview_retrieval_general_named_entity_recall_prefers_scoped_shop_name(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        curated_retrieval_only=False,
        retrieval_policy_order=["semantic", "curated"],
    )
    store = KernelMemoryStore.from_config(config)
    dining = store.ingest_claim(
        claim_type="user_fact",
        content="The Sugar Factory at Icon Park is a fun dessert shop in Orlando that offers giant milkshakes.",
        fact_facets=extract_fact_facets("The Sugar Factory at Icon Park is a fun dessert shop in Orlando that offers giant milkshakes."),
        metadata={"speaker_role": "assistant", "primary_language": "en"},
        observed_at="2023-05-21T17:19:00+00:00",
    )
    store.ingest_claim(
        claim_type="user_fact",
        content="Kelly's Homemade Ice Cream is another Orlando dessert option with handmade flavors.",
        fact_facets=extract_fact_facets("Kelly's Homemade Ice Cream is another Orlando dessert option with handmade flavors."),
        metadata={"speaker_role": "assistant", "primary_language": "en"},
        observed_at="2023-05-21T17:19:00+00:00",
    )
    retriever = KernelMemoryRetriever(config, store)

    preview = retriever.preview_retrieval(
        "I'm planning to revisit Orlando. I was wondering if you could remind me of that unique dessert shop with the giant milkshakes we talked about last time?",
        max_records=8,
        max_chars=2200,
    )

    assert preview["retrieval"]["answer_packet"]["resolved_answer_text"] == "The Sugar Factory at Icon Park"
    assert preview["retrieval"]["answer_packet"]["delivery_tier"] == "final_compact"


def test_preview_retrieval_general_named_entity_recall_prefers_named_place_over_sentence_stub(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        curated_retrieval_only=False,
        retrieval_policy_order=["semantic", "curated"],
    )
    store = KernelMemoryStore.from_config(config)
    store.ingest_claim(
        claim_type="user_fact",
        content="There's also Roscioli, a famous deli that serves the best cured meats, cheeses, and panini in Rome.",
        fact_facets=extract_fact_facets(
            "There's also Roscioli, a famous deli that serves the best cured meats, cheeses, and panini in Rome."
        ),
        metadata={"speaker_role": "assistant", "primary_language": "en"},
        observed_at="2023-05-21T17:19:00+00:00",
    )
    retriever = KernelMemoryRetriever(config, store)

    preview = retriever.preview_retrieval(
        "Which Vatican deli was famous for cured meats and cheeses?",
        max_records=8,
        max_chars=2200,
    )

    assert preview["retrieval"]["answer_packet"]["resolved_answer_text"] == "Roscioli"
    assert preview["retrieval"]["answer_packet"]["delivery_tier"] == "final_compact"


def test_objective_executor_temporal_relative_prefers_referenced_anchor_over_distractor(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        curated_retrieval_only=False,
        retrieval_policy_order=["semantic", "graph"],
    )
    store = KernelMemoryStore.from_config(config)
    festival = store.ingest_event(
        event_type="personal_event",
        title="Seattle International Film Festival",
        summary="I attended the Seattle International Film Festival.",
        observed_at="2023-02-01T12:00:00+00:00",
        metadata={"speaker_role": "user"},
    )
    distractor = store.ingest_event(
        event_type="personal_event",
        title="Barcelona Architecture Walk",
        summary="I attended a walking tour in Barcelona.",
        observed_at="2023-02-03T12:00:00+00:00",
        metadata={"speaker_role": "user"},
    )
    executor = KernelMemoryObjectiveExecutor(config, store)

    result = executor.execute(
        query="How many months ago did I attend the Seattle International Film Festival?",
        items=[{**festival, "route": "semantic"}, {**distractor, "route": "semantic"}],
        as_of="2023-06-01T12:00:00+00:00",
    )

    assert result.supported is True
    assert result.lines[0] == "4 months ago"
    assert result.metrics.get("compare_mode") == "temporal_relative"


def test_objective_executor_count_inventory_marks_current_state_as_directly_grounded(tmp_path):
    config = KernelMemoryConfig(
        enabled=True,
        root_dir=tmp_path / "kernel",
        namespace="bestie",
        curated_retrieval_only=False,
        retrieval_policy_order=["semantic", "curated"],
    )
    store = KernelMemoryStore.from_config(config)
    claim = store.ingest_claim(
        claim_type="user_fact",
        content="I currently own 4 musical instruments: a Yamaha FG800, a Fender Stratocaster, a Korg B1, and a Pearl Export drum kit.",
        fact_facets=extract_fact_facets(
            "I currently own 4 musical instruments: a Yamaha FG800, a Fender Stratocaster, a Korg B1, and a Pearl Export drum kit."
        ),
        metadata={"speaker_role": "user", "primary_language": "en"},
        observed_at="2023-03-10T10:00:00+00:00",
    )
    executor = KernelMemoryObjectiveExecutor(config, store)

    result = executor.execute(
        query="How many musical instruments do I currently own?",
        items=[{**claim, "route": "semantic"}],
    )

    assert result.supported is True
    assert result.metrics.get("count_mode") == "count_inventory_unit"
    assert result.metrics.get("direct_value_grounded") is True
    assert result.metrics.get("grounding_strength") == "high"
