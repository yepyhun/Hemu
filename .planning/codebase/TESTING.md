# Codebase Map: Testing

## Summary

Testing coverage is broad and subsystem-oriented. The repo has meaningful automated coverage across agent internals, gateway/platform behavior, ACP/MCP paths, cron jobs, and memory provider behavior.

## Test Layout

- `tests/agent/`: agent internals, prompt building, model metadata, memory provider behavior, subagent progress, routing
- `tests/gateway/`: gateway APIs, delivery behavior, platform adapters, config bridging, memory flush behavior, approvals, media handling
- `tests/acp/`: ACP/MCP-related auth, server, tools, and session tests
- `tests/e2e/`: higher-level integration flows
- `tests/cron/`: scheduled/background job behavior
- `tests/fakes/`: helper fake services
- `tests/conftest.py` and scoped `conftest.py` files: shared fixtures

## Memory-Relevant Tests

- `tests/agent/test_memory_provider.py`
- `tests/agent/test_memory_plugin_e2e.py`
- `tests/gateway/test_async_memory_flush.py`
- `tests/gateway/test_flush_memory_stale_guard.py`

These are the first places to extend when introducing a new modular kernel.

## CI Signals

Relevant GitHub workflows include:

- `.github/workflows/tests.yml`
- `.github/workflows/nix.yml`
- `.github/workflows/docs-site-checks.yml`
- `.github/workflows/docker-publish.yml`
- `.github/workflows/supply-chain-audit.yml`

This suggests the repo expects tests plus packaging/docs quality checks in CI.

## Quality Characteristics

- Coverage spans both pure logic and platform/runtime integration concerns.
- The repo appears comfortable with large-scale integration testing, not just isolated unit tests.
- Memory changes will likely require both provider-level tests and integration coverage through runtime/gateway flows.

## Testing Recommendation For Kernel Work

- Add unit tests for provider invariants and state transitions.
- Add integration tests for hook timing (`initialize`, `prefetch`, `sync_turn`, `on_session_end`, `on_pre_compress`, `on_delegation`).
- Extend gateway/agent tests where memory flush, compression, or delegation semantics change.
- Preserve backward compatibility for existing built-in memory expectations unless intentionally versioned.
