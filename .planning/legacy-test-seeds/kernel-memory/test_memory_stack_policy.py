from __future__ import annotations

from types import SimpleNamespace

from agent.memory_stack_policy import (
    KernelNoisePolicy,
    KernelRetrievalPolicy,
    MemoryStackPolicy,
)


def test_memory_stack_policy_loads_native_and_honcho_settings_from_agent_config():
    policy = MemoryStackPolicy.from_agent_config(
        {
            "memory_stack": {
                "native": {
                    "user_entry_max_chars": 180,
                    "memory_entry_max_chars": 220,
                },
                "honcho": {
                    "read_only": True,
                    "allow_seed_migration": False,
                },
            },
            "kernel_memory": {
                "excluded_tool_result_tools": ["memory"],
                "curated_retrieval_only": True,
            },
        }
    )

    assert policy.native.user_entry_max_chars == 180
    assert policy.honcho.read_only is True
    assert policy.kernel_noise.tool_result_excluded("memory") is True
    assert policy.kernel_retrieval.curated_retrieval_only is True


def test_kernel_noise_policy_filters_memory_tool_and_short_save_acknowledgements():
    policy = KernelNoisePolicy.from_config(
        SimpleNamespace(
            excluded_tool_result_tools=["memory"],
            assistant_acknowledgement_filter_enabled=True,
            assistant_acknowledgement_max_chars=280,
            assistant_acknowledgement_phrases=["elmentettem"],
        )
    )

    assert policy.tool_result_excluded("memory") is True
    assert policy.assistant_turn_excluded("Elmentettem.") is True
    assert (
        policy.record_excluded_from_online_retrieval(
            {
                "metadata": {
                    "origin": "assistant_turn_completed",
                },
                "summary": "Elmentettem.",
            }
        )
        is True
    )


def test_kernel_retrieval_policy_resolves_curated_first_route_order():
    policy = KernelRetrievalPolicy.from_config(
        SimpleNamespace(curated_retrieval_only=True)
    )

    assert policy.resolve_route_order(
        query="What do we know about Tomi?",
        response_mode="source_supported",
        requested_route_order=None,
        default_route_order=["curated", "source", "graph", "semantic"],
        valid_routes=["curated", "source", "graph", "semantic"],
        source_hint=False,
        graph_hint=False,
        current_state_hint=False,
    ) == ["curated"]

    assert policy.resolve_route_order(
        query="What is the relationship between Laura and Tomi?",
        response_mode="source_supported",
        requested_route_order=None,
        default_route_order=["curated", "source", "graph", "semantic"],
        valid_routes=["curated", "source", "graph", "semantic"],
        source_hint=False,
        graph_hint=True,
        current_state_hint=False,
    ) == ["curated", "graph"]

    assert policy.resolve_route_order(
        query="What is Laura's current favorite quote?",
        response_mode="source_supported",
        requested_route_order=None,
        default_route_order=["curated", "source", "graph", "semantic"],
        valid_routes=["curated", "source", "graph", "semantic"],
        source_hint=False,
        graph_hint=False,
        current_state_hint=True,
    ) == ["curated", "semantic"]
