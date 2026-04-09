# Codebase Map: Stack

## Summary

`hermes-agent-core2` is primarily a Python agent/runtime codebase with a smaller Node footprint for browser tooling and the Docusaurus website. The runtime centers on `run_agent.py`, `cli.py`, `gateway/run.py`, `model_tools.py`, and `toolsets.py`.

## Languages And Runtimes

- Python 3 is the main implementation language across the agent, gateway, CLI, tools, plugins, and tests.
- Node.js is present for package-managed browser tooling and the docs site via `package.json` and `website/package.json`.
- Shell scripts appear in support tooling and optional skills under `optional-skills/`.

## Core Runtime Modules

- `run_agent.py` holds the primary `AIAgent` conversation loop and agent lifecycle orchestration.
- `cli.py` provides the interactive terminal experience.
- `gateway/run.py` is the messaging/multi-platform runtime entry point.
- `model_tools.py` is the thin orchestration layer over the tool registry.
- `toolsets.py` defines shared and platform-specific toolset groupings.
- `agent/` contains extracted internal subsystems such as prompt building, model metadata, compression, and memory abstractions.

## Dependency And Packaging Signals

- `package.json` declares the project as `hermes-agent`, private, with browser-related dependencies `agent-browser` and `@askjo/camoufox-browser`.
- The Node side is minimal in the root package and is mostly operational/supporting, not the primary application runtime.
- Python dependencies and runtime behavior are configured in the Python side of the repo rather than a frontend-heavy Node app layout.

## Tooling Architecture

- Tool modules self-register through `tools.registry.register(...)`.
- `model_tools.py` imports tool modules to trigger discovery for modules such as `tools.web_tools`, `tools.terminal_tool`, `tools.file_tools`, `tools.memory_tool`, `tools.code_execution_tool`, and `tools.delegate_tool`.
- `toolsets.py` composes those discovered tools into reusable distributions for CLI and gateway platforms.

## Configuration Surfaces

- Environment loading is profile-aware and routed through Hermes home resolution rather than hardcoded home-directory assumptions.
- `gateway/run.py` bridges `config.yaml` values into environment variables for downstream consumers.
- Runtime defaults for model, terminal, browser, compression, routing, and agent behavior are defined in configuration code paths referenced by `cli.py` and `gateway/run.py`.

## Memory Stack Baseline

- Built-in curated memory exists via `tools/memory_tool.py` with durable file-backed stores.
- External memory is plugin-based through `plugins/memory/`.
- The current plugin discovery contract lives in `plugins/memory/__init__.py`.
- The external-provider abstraction is defined in `agent/memory_provider.py`.

## Website And Docs

- `website/` is a Docusaurus documentation site.
- Repo docs and user guides live under `website/docs/`.
- Deployment and validation workflows exist under `.github/workflows/` for docs and release operations.

## Relevant Paths

- `run_agent.py`
- `cli.py`
- `gateway/run.py`
- `model_tools.py`
- `toolsets.py`
- `agent/`
- `tools/`
- `plugins/memory/`
- `tests/`
- `website/`
