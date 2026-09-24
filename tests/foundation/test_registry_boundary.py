"""Dependency and lifecycle tests for the canonical component registry."""

import pytest

from trading_bot.core.unified_registry import UnifiedComponentRegistry


class _Component:
    def __init__(self):
        self.initialized_with = None

    def initialize(self, config):
        self.initialized_with = config


@pytest.mark.asyncio
async def test_registry_initializes_dependencies_first() -> None:
    registry = UnifiedComponentRegistry()
    registry.clear()
    dependency = _Component()
    dependent = _Component()

    registry.register("data", dependency, component_type="data", config={"name": "data"})
    registry.register(
        "brain",
        dependent,
        component_type="brain",
        dependencies=["data"],
        config={"name": "brain"},
    )

    assert registry.initialization_order() == ["data", "brain"]
    assert await registry.initialize_all() is True
    assert dependency.initialized_with == {"name": "data"}
    assert dependent.initialized_with == {"name": "brain"}


def test_registry_rejects_unresolved_dependencies() -> None:
    registry = UnifiedComponentRegistry()
    registry.clear()
    registry.register("brain", _Component(), dependencies=["missing"])

    assert registry.validate_dependencies() == {"brain": ["missing"]}
    with pytest.raises(ValueError, match="Unresolved component dependencies"):
        registry.initialization_order()


def test_registry_rejects_dependency_cycles() -> None:
    registry = UnifiedComponentRegistry()
    registry.clear()
    registry.register("a", _Component(), dependencies=["b"])
    registry.register("b", _Component(), dependencies=["a"])

    with pytest.raises(ValueError, match="Circular component dependency"):
        registry.initialization_order()
