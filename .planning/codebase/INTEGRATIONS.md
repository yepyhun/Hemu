# Codebase Map: Integrations

## Summary

The repo integrates multiple model providers, messaging platforms, browser automation tooling, and pluggable memory backends. It is an integration-heavy agent platform rather than a single-service application.

## Model And AI Provider Surfaces

- `run_agent.py` uses the OpenAI-compatible client path for model interaction.
- `hermes_cli/tools_config.py` and related config/status code mention OpenAI, Anthropic, Gemini-style model settings, and provider base URLs.
- `tools/web_tools.py`, `tools/vision_tools.py`, and voice-related modules expose model-backed capabilities beyond plain chat.

## Messaging And Gateway Platforms

- `gateway/platforms/telegram.py`
- `gateway/platforms/slack.py`
- `gateway/platforms/whatsapp.py`
- `gateway/platforms/signal.py`
- `gateway/platforms/mattermost.py`
- `gateway/platforms/matrix.py`
- `gateway/platforms/email.py`
- `gateway/platforms/discord*.py`

These indicate Hermes runs as a multi-channel agent platform with per-platform adapters and delivery logic wired from `gateway/run.py`.

## Browser And Execution Backends

- Root `package.json` includes `agent-browser` and `@askjo/camoufox-browser`.
- `tools/browser_tool.py` and related config paths imply browser automation support.
- Terminal/execution environments are implemented under `tools/environments/` and `environments/`.
- Configuration references Docker, Singularity, Modal, and Daytona execution backends.

## Memory Providers And Persistence

- Built-in persistent memory uses file-backed stores via `tools/memory_tool.py`.
- External memory providers are loaded from `plugins/memory/<provider>/`.
- Current in-repo plugin evidence includes `plugins/memory/byterover/`.
- `agent/memory_provider.py` defines lifecycle hooks such as `initialize`, `prefetch`, `sync_turn`, `system_prompt_block`, `get_tool_schemas`, and `handle_tool_call`.

## MCP And External Tool Ecosystem

- MCP-related code is present in `hermes_cli/mcp_config.py`, `mcp_serve.py`, and ACP/MCP tests under `tests/acp/`.
- Tool discovery includes MCP tool discovery alongside built-in and plugin-based tools in `model_tools.py`.

## Docs, Release, And Supply-Chain Integrations

- CI workflows exist for tests, docs checks, Nix, Docker publish, and supply-chain audit under `.github/workflows/`.
- The docs site is deployed separately through website-related workflows.

## Likely Integration Implications For Modular Memory Kernel

- New kernel work should fit the existing `MemoryProvider` plugin boundary rather than bypassing it.
- Provider setup/config should remain profile-aware through Hermes home resolution and config-driven setup.
- Messaging, delegation, compression, and session lifecycle hooks already exist and should be treated as first-class integration points for memory behavior.
