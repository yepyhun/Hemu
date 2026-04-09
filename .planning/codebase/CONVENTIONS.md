# Codebase Map: Conventions

## General Style

- The repo uses explicit module boundaries and descriptive filenames rather than deep metaprogramming.
- Runtime comments tend to explain operational intent, safety rationale, or lifecycle ordering.
- Compatibility-preserving wrappers and bridge layers are common, especially around configuration and runtime orchestration.

## Naming Patterns

- Tool modules follow `*_tool.py`.
- Platform adapters live under `gateway/platforms/` and are named after the platform.
- Tests are organized by subsystem with `test_<behavior>.py`.
- Plugin providers live in `plugins/memory/<provider>/`.

## Registry And Plugin Pattern

- Tools self-register on import through the registry.
- Memory providers expose a clean plugin boundary rather than being hardcoded directly into runtime-specific branches.
- The code favors “discover and compose” patterns over manually maintained switchboards where possible.

## Error Handling And Operational Discipline

- The runtime includes explicit safeguards for broken stdio, environment loading, and backward-compatible config bridging.
- Tool and provider abstractions emphasize non-crashing behavior and availability checks before activation.
- Comments and docstrings frequently document why ordering matters, especially around environment/config setup and runtime hooks.

## Testing Convention Signals

- Test layout mirrors the source layout closely.
- There is dedicated coverage for memory provider behavior, ACP/MCP surfaces, gateway behavior, and end-to-end platform interactions.
- Fake servers and fixtures are kept under `tests/fakes/` and shared `conftest.py` files.

## Configuration Convention Signals

- Hermes home/profile indirection is preferred over raw home-directory paths.
- `config.yaml` is treated as an authoritative runtime configuration surface in several flows.
- Deprecated config keys are kept with migration guidance instead of being removed abruptly.

## Conventions Relevant To New Memory Kernel

- Keep new memory logic behind an explicit abstraction boundary.
- Respect profile-aware storage paths and configuration resolution.
- Avoid duplicating tool schemas or creating multiple simultaneously active external memory backends unless the repo contract changes deliberately.
- Preserve hooks already expected by runtime consumers: session start, turn sync, pre-compress extraction, delegation observation, and shutdown.
