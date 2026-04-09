from __future__ import annotations

from agent.kernel_memory_semantic_domains import (
    has_problem_signal,
    has_temporal_intent,
    infer_domain_flags,
    infer_risk_level,
)


def test_semantic_domains_infer_bilingual_domains():
    assert "quotes" in infer_domain_flags("Mi a kedvenc idézetem?")
    assert "scheduling" in infer_domain_flags("What is the reminder rule for the scheduler?")
    assert "business_brainstorming" in infer_domain_flags("Software business and investing ideas")


def test_semantic_domains_infer_risk_levels_without_direct_core_wordlists():
    assert infer_risk_level("Ez nagyon érzékeny orvosi téma.") == "high"
    assert infer_risk_level("This is an important rule we should follow.") == "medium"
    assert infer_risk_level("Orbital notes about transfer windows.") == "low"


def test_semantic_domains_detect_temporal_intent_bilingually():
    assert has_temporal_intent("When did Laura start rehab?")
    assert has_temporal_intent("Mikor kezdődött Laura rehabilitációja?")


def test_semantic_domains_detect_problem_signal():
    assert has_problem_signal("The deployment is blocked by a permissions error.")
    assert has_problem_signal("A telepítés hibába futott és elakadt.")
