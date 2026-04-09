from __future__ import annotations

from agent.kernel_memory_bootstrap import (
    load_kernel_memory_config,
    load_kernel_memory_store,
)


def test_load_kernel_memory_config_requires_enabled(tmp_path):
    hermes_home = tmp_path / "hermes-home"
    hermes_home.mkdir()
    (hermes_home / "config.yaml").write_text(
        "kernel_memory:\n  enabled: false\n",
        encoding="utf-8",
    )

    try:
        load_kernel_memory_config(hermes_home=hermes_home, require_enabled=True)
    except ValueError as exc:
        assert str(exc) == "kernel_memory.enabled=false"
    else:
        raise AssertionError("Expected ValueError for disabled kernel memory")


def test_load_kernel_memory_store_uses_config_namespace(tmp_path):
    hermes_home = tmp_path / "hermes-home"
    kernel_root = tmp_path / "kernel-memory"
    hermes_home.mkdir()
    (hermes_home / "config.yaml").write_text(
        "\n".join(
            [
                "kernel_memory:",
                "  enabled: true",
                f"  root_dir: {kernel_root}",
                "  namespace: bestie",
            ]
        ),
        encoding="utf-8",
    )

    store = load_kernel_memory_store(
        hermes_home=hermes_home,
        require_enabled=True,
    )

    assert store.config.namespace == "bestie"
    assert store.config.root_dir == kernel_root
