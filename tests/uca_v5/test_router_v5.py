import pytest
from unittest.mock import MagicMock
from trading_bot.core.csc.router import SkillRouter, SkillType

@pytest.mark.asyncio
async def test_router_hasp_routing():
    router = SkillRouter()

    # Context with high volatility
    context = {"market": {"volatility": 0.5}}

    result = await router.route_task("execution", context)

    assert result["status"] == "pf_intervention"
    assert result["result"]["action"] == "override_to_hold"

@pytest.mark.asyncio
async def test_router_s2l_routing():
    router = SkillRouter()

    # Context needing hedging
    context = {"market": {"volatility": 0.1}, "needs_hedging": True}

    result = await router.route_task("hedging_task", context)

    assert result["status"] == "s2l_routed"
    assert result["adapter_id"] == "lora_hedging_v1"
