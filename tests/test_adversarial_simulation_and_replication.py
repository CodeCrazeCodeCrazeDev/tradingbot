import pytest
from trading_bot.core.security.defense import CapabilityInterceptor, AbstractAdversarialAction

def test_interceptor_blocks_unauthorized_spawn_and_contains():
    interceptor = CapabilityInterceptor(max_allowed_agents=2)

    assert interceptor.intercept_action("agent_alpha", AbstractAdversarialAction.ATTEMPT_AGENT_SPAWN) is True
    assert interceptor.active_agents_count == 2

    assert interceptor.intercept_action("agent_alpha", AbstractAdversarialAction.ATTEMPT_AGENT_SPAWN) is False
    assert "agent_alpha" in interceptor.quarantined_agents

    assert interceptor.intercept_action("agent_alpha", AbstractAdversarialAction.ATTEMPT_PRIVILEGE_ESCALATION) is False

def test_interceptor_blocks_governance_bypass_attempt():
    interceptor = CapabilityInterceptor()

    assert interceptor.intercept_action("agent_rogue", AbstractAdversarialAction.ATTEMPT_GOVERNANCE_BYPASS) is False
    assert "agent_rogue" in interceptor.quarantined_agents
