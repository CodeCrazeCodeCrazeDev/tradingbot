"""Agent Security Kernel — signed inter-agent messages + capability
domains. Implements the AGENT_SECURITY_ARCHITECTURE spec:

1. SignedInterAgentMessage — HMAC-SHA256 signed envelope carrying
   sender identity, task/message IDs, causal parent, provenance,
   payload hash, declared capabilities, and expiry.
2. Six non-overlapping capability domains enforcing least privilege.
3. The separation invariant: no agent may simultaneously hold
   memory-write + code-exec + net-egress + credentials + spawning +
   self-modification + deployment + live-trading capabilities.

HONEST LIMIT: in-process HMAC is a *protocol enforcement* layer, not
a cryptographic process boundary — agents share the Python heap and
could in principle read the key store. It makes spoofing an explicit
violation rather than an accident, gives every artifact a verifiable
origin + expiry + lineage, and is the seam a real process/memory
isolation boundary would later plug into. It does NOT replace the
sandbox for untrusted code.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import logging

logger = logging.getLogger(__name__)


class CapabilityDomain(str, Enum):
    INTELLIGENCE = "INTELLIGENCE"   # observation, signals, hypotheses
    RESEARCH = "RESEARCH"           # backtests, literature, candidates
    GOVERNANCE = "GOVERNANCE"       # policy enforcement, promotion gates
    RISK = "RISK"                   # exposure, sizing, kill-switch
    EXECUTION = "EXECUTION"         # orders, broker, reconciliation
    DEPLOYMENT = "DEPLOYMENT"       # release packaging, prod checks


# Raw capabilities an agent may declare; the invariant forbids one
# agent from holding the whole dangerous set simultaneously.
_DANGEROUS_CAPS = frozenset({
    "memory_write", "code_exec", "net_egress", "credentials",
    "agent_spawn", "self_modify", "deploy", "live_trade"})

# Sane ceiling per agent — below the full dangerous set by rule.
_MAX_DANGEROUS = 2


def _canonical(fields: Dict[str, Any]) -> bytes:
    return json.dumps(fields, sort_keys=True, default=str,
                      separators=(",", ":")).encode("utf-8")


def _payload_hash(payload: Any) -> str:
    return hashlib.sha256(_canonical({"p": payload})).hexdigest()


@dataclass
class SignedInterAgentMessage:
    sender_id: str
    sender_version: str
    task_id: str
    message_id: str
    timestamp: float
    causal_parent: Optional[str]
    provenance: Dict[str, Any]
    payload_hash: str
    capabilities: List[str]
    expiration: float
    signature: str
    payload: Any = field(default=None, repr=False)

    def verify_material(self) -> Dict[str, Any]:
        return {
            "sender_id": self.sender_id,
            "sender_version": self.sender_version,
            "task_id": self.task_id,
            "message_id": self.message_id,
            "timestamp": self.timestamp,
            "causal_parent": self.causal_parent,
            "provenance": self.provenance,
            "payload_hash": self.payload_hash,
            "capabilities": sorted(self.capabilities),
            "expiration": self.expiration,
        }

    def to_wire(self) -> Dict[str, Any]:
        d = self.verify_material()
        d["signature"] = self.signature
        d["payload"] = self.payload
        return d

    @classmethod
    def from_wire(cls, d: Dict[str, Any]) -> "SignedInterAgentMessage":
        return cls(
            sender_id=d["sender_id"],
            sender_version=d["sender_version"],
            task_id=d["task_id"],
            message_id=d["message_id"],
            timestamp=float(d["timestamp"]),
            causal_parent=d.get("causal_parent"),
            provenance=dict(d.get("provenance") or {}),
            payload_hash=d["payload_hash"],
            capabilities=list(d.get("capabilities") or []),
            expiration=float(d["expiration"]),
            signature=d["signature"],
            payload=d.get("payload"))


@dataclass
class AgentIdentity:
    agent_id: str
    domains: frozenset
    capabilities: frozenset
    version: str
    key: bytes = field(repr=False)   # session key; never serialized


class AgentSecurityKernel:
    """Issues identities, signs/verifies messages, enforces domains."""

    def __init__(self, ttl_s: float = None,
                 max_dangerous: int = _MAX_DANGEROUS) -> None:
        self.ttl_s = ttl_s or float(
            os.environ.get("TB_AGENT_MSG_TTL", "60"))
        # Artifacts live for a whole advisory cycle (~minutes) — the
        # 60s wire TTL expired every signature before the verify sweep
        # ran (377 false quarantines on the tiered run).
        self.artifact_ttl_s = float(
            os.environ.get("TB_ARTIFACT_SIG_TTL", "900"))
        self.max_dangerous = max_dangerous
        self._identities: Dict[str, AgentIdentity] = {}

    # ------------------------------------------------ identities --
    def issue_identity(self, agent_id: str,
                       domains: List[CapabilityDomain],
                       capabilities: List[str] = (),
                       version: str = "unknown") -> AgentIdentity:
        caps = frozenset(capabilities)
        dangerous = caps & _DANGEROUS_CAPS
        if len(dangerous) > self.max_dangerous:
            raise PermissionError(
                f"invariant: agent {agent_id} requests "
                f"{len(dangerous)} dangerous capabilities "
                f"{sorted(dangerous)} > max {self.max_dangerous} — "
                "memory_write+code_exec+net_egress+credentials+spawn+"
                "self_modify+deploy+live_trade may not co-reside")
        ident = AgentIdentity(
            agent_id=str(agent_id), domains=frozenset(domains),
            capabilities=caps, version=str(version),
            key=secrets.token_bytes(32))
        self._identities[ident.agent_id] = ident
        return ident

    def require(self, agent_id: str,
                domain: CapabilityDomain) -> bool:
        ident = self._identities.get(agent_id)
        ok = ident is not None and domain in ident.domains
        if not ok:
            logger.warning("capability deny: %s lacks domain %s",
                           agent_id, domain.value)
        return ok

    # ------------------------------------------------- messaging --
    def sign(self, agent_id: str, payload: Any, *,
             task_id: str = "", causal_parent: str = None,
             provenance: Dict[str, Any] = None,
             ttl_s: float = None) -> SignedInterAgentMessage:
        ident = self._identities.get(agent_id)
        if ident is None:
            raise PermissionError(f"unsigned agent: {agent_id}")
        now = time.time()
        msg = SignedInterAgentMessage(
            sender_id=agent_id, sender_version=ident.version,
            task_id=task_id or uuid.uuid4().hex,
            message_id=uuid.uuid4().hex,
            timestamp=now, causal_parent=causal_parent,
            provenance=dict(provenance or {}),
            payload_hash=_payload_hash(payload),
            capabilities=sorted(ident.capabilities),
            expiration=now + (ttl_s or self.ttl_s),
            signature="", payload=payload)
        msg.signature = hmac.new(
            ident.key, _canonical(msg.verify_material()),
            hashlib.sha256).hexdigest()
        return msg

    def verify(self, msg: SignedInterAgentMessage) -> Tuple[bool, str]:
        ident = self._identities.get(msg.sender_id)
        if ident is None:
            return False, "unknown_sender"
        now = time.time()
        if now > msg.expiration:
            return False, "expired"
        if msg.payload_hash != _payload_hash(msg.payload):
            return False, "payload_tampered"
        expect = hmac.new(ident.key, _canonical(msg.verify_material()),
                          hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expect, msg.signature):
            return False, "bad_signature"
        return True, "ok"

    # ------------------------------------------- artifact signing --
    @staticmethod
    def _artifact_material(agent_id, version, body, exp):
        return {"sender_id": agent_id, "sender_version": version,
                "channel": "advisory",
                "payload_hash": _payload_hash(body),
                "expiration": exp}

    def sign_artifact(self, agent_id: str, artifact: Dict[str, Any],
                      ttl_s: float = None) -> Dict[str, Any]:
        """Embed a signature block inside an advisory artifact so a
        downstream consumer can verify origin/expiry without the wire
        envelope. Adds ``sig``/``sig_agent``/``sig_exp`` — never
        mutates evidence fields."""
        ident = self._identities.get(agent_id)
        if ident is None:
            raise PermissionError(f"unsigned agent: {agent_id}")
        body = {k: v for k, v in artifact.items()
                if k not in ("sig", "sig_agent", "sig_exp")}
        exp = time.time() + (ttl_s or self.artifact_ttl_s)
        material = self._artifact_material(
            agent_id, ident.version, body, exp)
        out = dict(artifact)
        out["sig"] = hmac.new(
            ident.key, _canonical(material), hashlib.sha256).hexdigest()
        out["sig_agent"] = agent_id
        out["sig_exp"] = exp
        return out

    def verify_artifact(self, artifact: Dict[str, Any]
                        ) -> Tuple[bool, str]:
        sig = artifact.get("sig")
        agent_id = artifact.get("sig_agent")
        if not sig or not agent_id:
            return False, "unsigned"
        if time.time() > float(artifact.get("sig_exp") or 0):
            return False, "expired"
        ident = self._identities.get(agent_id)
        if ident is None:
            return False, "unknown_sender"
        body = {k: v for k, v in artifact.items()
                if k not in ("sig", "sig_agent", "sig_exp")}
        material = self._artifact_material(
            agent_id, ident.version, body,
            float(artifact.get("sig_exp") or 0))
        expect = hmac.new(ident.key, _canonical(material),
                          hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expect, sig):
            return False, "bad_signature"
        return True, "ok"
