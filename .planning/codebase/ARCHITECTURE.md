# Codebase Map: Architecture

## High-Level Pattern

The repo follows a modular agent-platform architecture:

1. Core conversation runtime in `run_agent.py`
2. Tool orchestration and registry in `model_tools.py` and `tools/registry`
3. Toolset composition in `toolsets.py`
4. User-facing shells in `cli.py` and `gateway/run.py`
5. Optional capability modules in `tools/`, `plugins/`, and `optional-skills/`

## Main Entry Points

- `run_agent.py`: primary programmable/CLI-facing agent runner and `AIAgent` lifecycle
- `cli.py`: interactive terminal UX wrapper around the agent runtime
- `gateway/run.py`: long-lived messaging gateway process
- `mcp_serve.py`: MCP-related serving path
- `batch_runner.py`: batch-oriented orchestration path

## Tool Execution Flow

1. Runtime resolves enabled toolsets from CLI or gateway configuration.
2. `model_tools.py` imports tool modules, which self-register into the shared registry.
3. The agent obtains tool schemas via `get_tool_definitions(...)`.
4. The model emits tool calls.
5. `handle_function_call(...)` dispatches tool handlers through the registry.
6. Results flow back into the conversation loop in `run_agent.py`.

## Memory Architecture

The current memory design is already partially modular:

- Built-in curated memory is always available through `tools/memory_tool.py`.
- One external memory provider can be active at a time.
- External providers are discovered from `plugins/memory/`.
- The contract is formalized in `agent/memory_provider.py`.

This is important for the new kernel effort: the repo already expects memory as a provider boundary, not as ad hoc logic spread across the runtime.

## Layer Responsibilities

- `agent/`: reusable internal abstractions and logic extracted from the top-level runner
- `tools/`: callable capabilities exposed to the model
- `plugins/`: pluggable extensions, including memory providers
- `gateway/`: platform transport, delivery, approvals, background jobs
- `hermes_cli/`: command surface, config UX, platform/tool configuration
- `website/`: documentation site

## Data Flow Notes

- System prompt assembly and runtime context start in the agent layer and `run_agent.py`.
- Tool availability is derived dynamically from config and discovery rather than being hardcoded into a single static schema.
- Memory interacts with the agent lifecycle through explicit hooks such as per-turn start, turn sync, pre-compression extraction, session end, and delegation observation.

## Architectural Strengths

- Strong modular boundaries around tools and providers
- Multi-platform delivery separated from core runtime
- Existing hook surface for memory evolution
- Extensive tests across agent and gateway behavior

## Architectural Pressure Points

- `run_agent.py` and `gateway/run.py` remain large orchestrators with many cross-cutting concerns.
- Memory behavior is split between built-in file memory, provider plugins, and gateway/agent lifecycle hooks, so new kernel work needs tight contract discipline to avoid fragmentation.
- Backward compatibility matters because multiple entry points and platforms consume the same agent stack.
