import pytest
from trading_bot.core.unified_registry import UnifiedComponentRegistry, registry

def test_registry_singleton():
    reg1 = UnifiedComponentRegistry()
    reg2 = UnifiedComponentRegistry()
    assert reg1 is reg2
    assert reg1 is registry

def test_registry_registration():
    registry.clear()
    registry.register("test_comp", {"data": 1}, "test_type")
    assert registry.get("test_comp") == {"data": 1}
    assert len(registry.get_by_type("test_type")) == 1
