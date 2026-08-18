import pytest
from scripts.measure_security_benchmarks import run_benchmarks
from trading_bot.core.security.defense import CapabilityInterceptor, AbstractAdversarialAction

def test_red_team_blue_team_harness():
    interceptor = CapabilityInterceptor()
    
    red_attempt_1 = interceptor.intercept_action("rogue_agent", AbstractAdversarialAction.ATTEMPT_PRIVILEGE_ESCALATION)
    assert red_attempt_1 is False
    assert "rogue_agent" in interceptor.quarantined_agents
    
    red_attempt_2 = interceptor.intercept_action("rogue_agent_2", AbstractAdversarialAction.ATTEMPT_MEMORY_POISONING)
    assert red_attempt_2 is False
    assert "rogue_agent_2" in interceptor.quarantined_agents

def test_benchmarks_run_cleanly():
    run_benchmarks()
