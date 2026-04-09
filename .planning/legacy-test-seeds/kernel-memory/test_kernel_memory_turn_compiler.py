from __future__ import annotations

from agent.kernel_memory_turn_compiler import KernelMemoryTurnCompiler


def test_turn_compiler_emits_claims_events_and_episode_for_structured_turn():
    compiler = KernelMemoryTurnCompiler()

    compiled = compiler.compile_turn(
        user_message=(
            "Laura 2026. február 22-én itthoni balesetben gerincsérülést szenvedett, "
            "és most ő a fő prioritás."
        ),
        assistant_response=(
            "Rendben, Laura állapotát érzékeny, kiemelt témaként fogom kezelni, "
            "és figyelek rá a későbbi beszélgetésekben is."
        ),
    )

    assert len(compiled.claim_specs) >= 2
    assert any(
        spec.claim_type in {"dated_fact", "user_fact", "user_preference"}
        and (
            spec.claim_type != "user_preference"
            or spec.metadata.get("temporal_markers")
        )
        for spec in compiled.claim_specs
    )
    assert any(event.event_type == "personal_event" for event in compiled.event_specs)
    assert any("február" in marker.lower() for event in compiled.event_specs for marker in event.temporal_markers)
    assert any(event.action_lemma for event in compiled.event_specs)
    assert any(event.event_status for event in compiled.event_specs)
    assert compiled.episode_spec is not None
    assert "Conversation episode:" in compiled.episode_spec.title


def test_turn_compiler_emits_correction_semantics_for_update_turn():
    compiler = KernelMemoryTurnCompiler()

    compiled = compiler.compile_turn(
        user_message=(
            "Ez nem a kedvenc idézetem. A kedvenc idézetem inkább az, hogy "
            "Egyik szél sem jó annak a hajósnak, aki nem tudja melyik kikötőbe tart."
        ),
        assistant_response=(
            "Javítottam, a korábbi idézet helyett ezt kezelem kedvenc idézetként."
        ),
    )

    assert any(
        claim.metadata.get("conflict_signal") == "correction"
        for claim in compiled.claim_specs
    )
    correction_claim = next(
        claim for claim in compiled.claim_specs if claim.metadata.get("conflict_signal") == "correction"
    )
    assert correction_claim.metadata["correction_parse"]["new_value"] is not None
    assert any(event.event_type == "superseded" for event in compiled.event_specs)
    correction_event = next(event for event in compiled.event_specs if event.event_type == "superseded")
    assert correction_event.event_status == "superseded"
    assert correction_event.metadata.get("conflict_signal") == "correction"
    assert correction_event.actor_label == "user"


def test_turn_compiler_clusters_continuation_sentence_into_same_event():
    compiler = KernelMemoryTurnCompiler()

    compiled = compiler.compile_turn(
        user_message=(
            "I recently bought a luxury evening gown for a wedding. "
            "It was a big purchase, $800, but I felt like I needed to make a good impression."
        ),
        assistant_response="That sounds like an emotionally driven luxury purchase.",
    )

    clustered_claims = [
        claim
        for claim in compiled.claim_specs
        if claim.speaker_role == "user" and claim.cluster_key
    ]
    assert len(clustered_claims) >= 2
    assert len({claim.cluster_key for claim in clustered_claims}) == 1

    event = next(
        event
        for event in compiled.event_specs
        if "luxury evening gown" in event.summary.lower()
    )
    assert "$800" in event.summary
    assert len(event.claim_contents) >= 2
    assert any("$800" in content for content in event.claim_contents)
    assert event.claim_cluster_key == clustered_claims[0].cluster_key
