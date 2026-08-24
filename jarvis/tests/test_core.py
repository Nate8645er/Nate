"""Tests for core building blocks: config, container, events, security."""

from __future__ import annotations

import asyncio

import pytest

from jarvis.core.config import JarvisConfig, load_config
from jarvis.core.container import ServiceContainer
from jarvis.core.errors import ConfigurationError, PermissionDeniedError
from jarvis.core.events import EventBus
from jarvis.core.security import PermissionManager, PythonSandbox


class TestConfig:
    def test_defaults(self, config: JarvisConfig) -> None:
        assert config.assistant_name == "JARVIS"
        assert config.llm.max_tokens == 4096
        assert config.api.port == 8765

    def test_env_override(self, monkeypatch, tmp_path) -> None:
        monkeypatch.setenv("JARVIS_DATA_DIR", str(tmp_path))
        monkeypatch.setenv("JARVIS_LLM__DEFAULT_PROVIDER", "ollama")
        monkeypatch.setenv("JARVIS_API__PORT", "9001")
        cfg = JarvisConfig(_env_file=None)
        assert cfg.llm.default_provider == "ollama"
        assert cfg.api.port == 9001

    def test_yaml_file_merge(self, monkeypatch, tmp_path) -> None:
        monkeypatch.setenv("JARVIS_DATA_DIR", str(tmp_path))
        cfg_file = tmp_path / "config.yaml"
        cfg_file.write_text("assistant_name: FRIDAY\nvoice:\n  wake_word: friday\n")
        cfg = load_config(cfg_file)
        assert cfg.assistant_name == "FRIDAY"
        assert cfg.voice.wake_word == "friday"

    def test_provider_key_from_env(self, config: JarvisConfig, monkeypatch) -> None:
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
        provider_cfg = config.provider("deepseek")
        assert provider_cfg.api_key is not None
        assert provider_cfg.api_key.get_secret_value() == "sk-test"

    def test_resolve_path(self, config: JarvisConfig) -> None:
        assert config.resolve_path("memory.db") == config.data_dir / "memory.db"
        assert config.resolve_path("/abs/x.db").as_posix() == "/abs/x.db"


class TestContainer:
    async def test_singleton_and_instance(self) -> None:
        container = ServiceContainer()
        container.register_instance(str, "hello")
        calls = []

        class Service:
            pass

        def factory(c: ServiceContainer) -> Service:
            calls.append(1)
            return Service()

        container.register_singleton(Service, factory)
        assert container.resolve(str) == "hello"
        first = container.resolve(Service)
        second = container.resolve(Service)
        assert first is second
        assert len(calls) == 1

    async def test_async_factory(self) -> None:
        container = ServiceContainer()

        class Db:
            pass

        async def factory(c: ServiceContainer) -> Db:
            await asyncio.sleep(0)
            return Db()

        container.register_singleton(Db, factory)
        with pytest.raises(ConfigurationError):
            container.resolve(Db)
        db = await container.aresolve(Db)
        assert isinstance(db, Db)
        assert await container.aresolve(Db) is db

    async def test_missing_service(self) -> None:
        with pytest.raises(ConfigurationError):
            ServiceContainer().resolve(int)

    async def test_close_hooks_reverse_order(self) -> None:
        container = ServiceContainer()
        order: list[int] = []
        container.on_close(lambda: order.append(1))

        async def closer() -> None:
            order.append(2)

        container.on_close(closer)
        await container.aclose()
        assert order == [2, 1]


class TestEventBus:
    async def test_wildcard_and_cancel(self) -> None:
        bus = EventBus()
        seen: list[str] = []
        sub = bus.subscribe("voice.*", lambda e: seen.append(e.topic))
        await bus.publish("voice.wake", {})
        await bus.publish("vision.frame", {})
        sub.cancel()
        await bus.publish("voice.wake", {})
        assert seen == ["voice.wake"]

    async def test_handler_error_isolated(self) -> None:
        bus = EventBus()
        seen: list[str] = []

        def bad(event) -> None:
            raise RuntimeError("boom")

        bus.subscribe("*", bad)
        bus.subscribe("*", lambda e: seen.append(e.topic))
        await bus.publish("x", {})
        assert seen == ["x"]


class TestSecurity:
    async def test_default_deny_headless(self, config: JarvisConfig) -> None:
        manager = PermissionManager(config)
        with pytest.raises(PermissionDeniedError):
            await manager.check("desktop.terminal", "rm -rf /")

    async def test_allow_policy_and_persistence(self, config: JarvisConfig) -> None:
        manager = PermissionManager(config)
        manager.set_policy("files.read", "allow")
        await manager.check("files.read", "read file")  # must not raise
        # Fresh manager reads persisted policy.
        manager2 = PermissionManager(config)
        assert manager2.policy_for("files.read") == "allow"

    async def test_prefix_policy(self, config: JarvisConfig) -> None:
        manager = PermissionManager(config)
        manager.set_policy("desktop.*", "deny")
        assert manager.policy_for("desktop.input") == "deny"

    async def test_confirmer_approval(self, config: JarvisConfig) -> None:
        manager = PermissionManager(config)

        async def yes(capability: str, description: str) -> bool:
            return True

        manager.set_confirmer(yes)
        await manager.check("desktop.input", "click")  # must not raise


class TestSandbox:
    async def test_runs_code(self) -> None:
        sandbox = PythonSandbox(timeout_seconds=10)
        result = await sandbox.run("print(6*7)")
        assert result["exit_code"] == 0
        assert "42" in str(result["stdout"])

    async def test_timeout(self) -> None:
        sandbox = PythonSandbox(timeout_seconds=1)
        result = await sandbox.run("import time; time.sleep(5)")
        assert result["exit_code"] == -1
        assert "timed out" in str(result["stderr"])
