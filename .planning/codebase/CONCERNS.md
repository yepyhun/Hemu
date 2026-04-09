# Codebase Map: Concerns

## Main Risks

### 1. Large Orchestrator Files

`run_agent.py` and `gateway/run.py` are central and broad in responsibility. Changes that cut across memory, config, delegation, and lifecycle behavior can create regressions far from the feature being built.

### 2. Memory Surface Fragmentation

Memory already exists in multiple layers:

- built-in file-backed memory in `tools/memory_tool.py`
- external provider contract in `agent/memory_provider.py`
- plugin discovery in `plugins/memory/__init__.py`
- runtime hook invocation in agent/gateway code

The new kernel must tighten the architecture, not add a parallel side-channel.

### 3. Backward Compatibility Pressure

Hermes supports CLI, gateway, MCP-related surfaces, multiple platform adapters, and optional plugins. Memory behavior that works in one path but not another will be costly.

### 4. Existing Technical Debt Signals

Repository searches show TODO/deprecation/workaround markers in areas such as:

- `hermes_cli/providers.py` for future provider extensibility
- `hermes_cli/config.py` for deprecated configuration keys
- `gateway/run.py` and related files for operational edge-case handling
- dependency deprecation notices in `package-lock.json`

These do not block the project, but they indicate an already evolving runtime with compatibility baggage.

### 5. Security And Prompt-Integrity Requirements

`tools/memory_tool.py` includes content scanning for injection/exfiltration before accepting memory writes. Any new kernel that stores or rehydrates memory into prompts needs to preserve or improve that posture.

### 6. Hook Semantics Are Easy To Break

The provider lifecycle includes:

- `initialize`
- `system_prompt_block`
- `prefetch`
- `sync_turn`
- `on_turn_start`
- `on_session_end`
- `on_pre_compress`
- `on_memory_write`
- `on_delegation`
- `shutdown`

Kernel work that only handles retrieval/write paths and ignores lifecycle hooks will likely be incomplete.

## Opportunity

The repo already has the right abstraction seam for a modular kernel: provider plugins plus explicit lifecycle hooks. The main architectural opportunity is to move toward a stronger, more coherent provider implementation without bloating the native runtime files.

## Recommended Guardrails

- Keep kernel logic in isolated new modules.
- Limit changes in `run_agent.py` and `gateway/run.py` to thin wiring.
- Treat memory safety and source-of-truth rules as first-class, not optional polish.
- Add tests before or alongside any lifecycle contract expansion.
