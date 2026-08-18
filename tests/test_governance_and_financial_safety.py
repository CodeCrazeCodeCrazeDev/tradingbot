import pytest
from trading_bot.core.security.defense import HardenedGovernanceRoot, DeterministicFinancialGateway

def test_hardened_governance_root_rejects_agent_modification():
    assert HardenedGovernanceRoot.get_risk_limit("max_position_usd") == 100000.0
    success = HardenedGovernanceRoot.attempt_modify_risk_limit("rogue_agent", "max_position_usd", 1000000.0)
    assert success is False
    assert HardenedGovernanceRoot.get_risk_limit("max_position_usd") == 100000.0

def test_deterministic_gateway_rejects_over_sized_trade():
    proposal = {
        "symbol": "BTC/USD",
        "qty_usd": 250000.0,
        "master_risk_stamp": "STAMP_VALID_123"
    }
    assert DeterministicFinancialGateway.authorize_execution(proposal) is False

def test_deterministic_gateway_rejects_missing_risk_stamp():
    proposal = {
        "symbol": "BTC/USD",
        "qty_usd": 50000.0,
        "master_risk_stamp": None
    }
    assert DeterministicFinancialGateway.authorize_execution(proposal) is False

def test_deterministic_gateway_rejects_when_kill_switch_active():
    proposal = {
        "symbol": "BTC/USD",
        "qty_usd": 50000.0,
        "master_risk_stamp": "STAMP_VALID_123"
    }
    assert DeterministicFinancialGateway.authorize_execution(proposal, kill_switch_active=True) is False
