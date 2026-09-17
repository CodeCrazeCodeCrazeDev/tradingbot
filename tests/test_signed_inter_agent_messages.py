import pytest, time
from datetime import datetime, timezone
from trading_bot.core.unified_event_bus import SignedInterAgentMessage, CapabilityDomain

def test_signed_inter_agent_message_creation_and_verification():
    msg = SignedInterAgentMessage(
        sender_id="agent_governance_1",
        sender_version="2.0.0",
        task_id="task_1001",
        payload={"action": "EVALUATE_MODEL", "model_id": "cand_99"},
        capabilities=[CapabilityDomain.GOVERNANCE.value]
    )
    assert msg.message_id is not None
    assert msg.payload_hash != ""
    assert msg.signature != ""
    assert msg.verify_signature("SYSTEM_SECRET_KEY") is True

def test_signature_tampering_rejection():
    msg = SignedInterAgentMessage(
        sender_id="agent_research_1",
        sender_version="1.0.0",
        task_id="task_1002",
        payload={"action": "SUBMIT_HYPOTHESIS"}
    )
    assert msg.verify_signature("SYSTEM_SECRET_KEY") is True

    # Tamper with sender_id
    msg.sender_id = "agent_governance_imposter"
    assert msg.verify_signature("SYSTEM_SECRET_KEY") is False

def test_expired_message_rejection():
    msg = SignedInterAgentMessage(
        sender_id="agent_risk_1",
        sender_version="1.0.0",
        task_id="task_1003",
        payload={"action": "CHECK_RISK"},
        expiration=datetime.now(timezone.utc).timestamp() - 10.0 # Expired 10s ago
    )
    assert msg.verify_signature("SYSTEM_SECRET_KEY") is False
