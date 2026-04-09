# Codebase Map: Structure

## Top-Level Layout

- `run_agent.py`: main agent runtime
- `cli.py`: interactive CLI entry
- `model_tools.py`: tool discovery and dispatch layer
- `toolsets.py`: toolset definitions and shared distributions
- `agent/`: internal agent subsystems
- `tools/`: model-callable tool implementations
- `plugins/`: plugin surfaces, including memory providers
- `gateway/`: messaging/gateway runtime and platform adapters
- `hermes_cli/`: CLI and configuration support package
- `tests/`: unit, integration, and platform coverage
- `website/`: docs site
- `optional-skills/`: packaged higher-level workflows and research/security skills
- `plans/`: design notes and architecture plans

## Agent-Relevant Subtrees

### Core Runtime

- `run_agent.py`
- `agent/`
- `model_tools.py`
- `toolsets.py`

### CLI And UX

- `cli.py`
- `hermes_cli/`

### Gateway And Platforms

- `gateway/run.py`
- `gateway/platforms/`
- `gateway/stream_consumer.py`
- `gateway/session.py`

### Tools

- `tools/web_tools.py`
- `tools/terminal_tool.py`
- `tools/file_tools.py`
- `tools/memory_tool.py`
- `tools/code_execution_tool.py`
- `tools/delegate_tool.py`
- `tools/browser_tool.py`

### Memory Plugin Area

- `plugins/memory/__init__.py`
- `plugins/memory/byterover/`

This subtree is the most relevant structural landing zone for a new modular memory kernel.

## Naming And Layout Patterns

- Tool implementations generally follow `<capability>_tool.py`.
- Platform adapters are grouped by channel under `gateway/platforms/`.
- Tests mirror production areas: `tests/agent/`, `tests/gateway/`, `tests/acp/`, `tests/e2e/`, `tests/cron/`.
- Optional skills ship as directory-scoped units with `SKILL.md`.

## Change Hotspots For Memory Work

- `agent/memory_provider.py`
- `tools/memory_tool.py`
- `plugins/memory/`
- `run_agent.py`
- `gateway/run.py`
- `tests/agent/test_memory_provider.py`
- `tests/agent/test_memory_plugin_e2e.py`
- gateway tests covering memory flush/session behavior

## Structural Recommendation

For the new kernel, prefer a new isolated provider/module subtree under `plugins/memory/` or adjacent memory-specific modules rather than expanding `run_agent.py` with kernel-specific business logic. Keep native/core files thin and use them for wiring and lifecycle invocation.
