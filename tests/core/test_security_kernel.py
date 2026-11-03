"""AgentSecurityKernel — signed messages, capability domains, the
separation invariant, artifact signing/quarantine semantics."""

import time

import pytest

from trading_bot.core.csc.security_kernel import (
    AgentSecurityKernel, CapabilityDomain, SignedInterAgentMessage)


@pytest.fixture
def kernel():
    return AgentSecurityKernel(ttl_s=30)


def test_sign_verify_roundtrip(kernel):
    kernel.issue_identity("adv1", [CapabilityDomain.INTELLIGENCE])
    msg = kernel.sign("adv1", {"direction": "BUY", "conf": 0.7},
                      task_id="t1")
    ok, reason = kernel.verify(msg)
    assert ok and reason == "ok"


def test_tampered_payload_rejected(kernel):
    kernel.issue_identity("adv1", [CapabilityDomain.INTELLIGENCE])
    msg = kernel.sign("adv1", {"direction": "BUY"})
    msg.payload = {"direction": "SELL"}  # forged after signing
    ok, reason = kernel.verify(msg)
    assert not ok and reason == "payload_tampered"


def test_forged_signature_rejected(kernel):
    kernel.issue_identity("adv1", [CapabilityDomain.INTELLIGENCE])
    msg = kernel.sign("adv1", {"x": 1})
    msg.signature = "0" * 64
    ok, reason = kernel.verify(msg)
    assert not ok and reason == "bad_signature"


def test_expired_message_rejected(kernel):
    k = AgentSecurityKernel(ttl_s=0.01)
    k.issue_identity("adv1", [CapabilityDomain.INTELLIGENCE])
    msg = k.sign("adv1", {"x": 1})
    time.sleep(0.05)
    ok, reason = k.verify(msg)
    assert not ok and reason == "expired"


def test_unknown_sender_rejected(kernel):
    kernel.issue_identity("adv1", [CapabilityDomain.INTELLIGENCE])
    msg = kernel.sign("adv1", {"x": 1})
    msg.sender_id = "mallory"          # identity spoof attempt
    ok, reason = kernel.verify(msg)
    assert not ok and reason == "unknown_sender"


def test_unsigned_agent_cannot_sign(kernel):
    with pytest.raises(PermissionError):
        kernel.sign("ghost", {"x": 1})


def test_separation_invariant(kernel):
    with pytest.raises(PermissionError):
        kernel.issue_identity(
            "superagent", [CapabilityDomain.DEPLOYMENT],
            capabilities=["memory_write", "code_exec", "net_egress",
                          "credentials", "agent_spawn"])
    # bounded dangerous set is allowed
    ident = kernel.issue_identity(
        "bounded", [CapabilityDomain.RESEARCH],
        capabilities=["net_egress", "code_exec"])
    assert ident.agent_id == "bounded"


def test_domain_require(kernel):
    kernel.issue_identity("researcher", [CapabilityDomain.RESEARCH])
    assert kernel.require("researcher", CapabilityDomain.RESEARCH)
    assert not kernel.require("researcher", CapabilityDomain.EXECUTION)


def test_artifact_sign_verify(kernel):
    kernel.issue_identity("opportunity_scanner",
                          [CapabilityDomain.INTELLIGENCE])
    art = kernel.sign_artifact(
        "opportunity_scanner",
        {"agent": "opportunity_scanner", "direction": "BUY",
         "net_edge_positive": True})
    ok, reason = kernel.verify_artifact(art)
    assert ok and reason == "ok"


def test_artifact_tamper_quarantined(kernel):
    kernel.issue_identity("adv1", [CapabilityDomain.INTELLIGENCE])
    art = kernel.sign_artifact("adv1", {"direction": "BUY"})
    art["direction"] = "SELL"
    ok, reason = kernel.verify_artifact(art)
    assert not ok and reason == "bad_signature"


def test_unsigned_artifact_flagged(kernel):
    ok, reason = kernel.verify_artifact({"direction": "BUY"})
    assert not ok and reason == "unsigned"


def test_wire_envelope_roundtrip(kernel):
    kernel.issue_identity("adv1", [CapabilityDomain.INTELLIGENCE])
    msg = kernel.sign("adv1", {"a": [1, 2, 3]},
                      causal_parent="parent-1",
                      provenance={"src": "test"})
    wire = msg.to_wire()
    restored = SignedInterAgentMessage.from_wire(wire)
    ok, _ = kernel.verify(restored)
    assert ok
    assert restored.causal_parent == "parent-1"
