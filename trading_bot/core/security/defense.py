"""
AlphaAlgo Core Security Defense Infrastructure (UCA-2026)
Consolidated enforcement authorities for governance, capability interception,
evidence lineage consensus, deterministic financial execution, and invariants.
"""

from enum import Enum
from dataclasses import dataclass, field
import uuid, hashlib, hmac, time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Set

from trading_bot.core.hms.memory import ProvenanceAwareMemoryRecord, MemoryValidationStatus
from trading_bot.core.unified_event_bus import SignedInterAgentMessage, CapabilityDomain


class AbstractAdversarialAction(Enum):
    ATTEMPT_PRIVILEGE_ESCALATION = "ATTEMPT_PRIVILEGE_ESCALATION"
    ATTEMPT_MEMORY_POISONING = "ATTEMPT_MEMORY_POISONING"
    ATTEMPT_UNAUTHORIZED_NETWORK = "ATTEMPT_UNAUTHORIZED_NETWORK"
    ATTEMPT_AGENT_SPAWN = "ATTEMPT_AGENT_SPAWN"
    ATTEMPT_GOVERNANCE_BYPASS = "ATTEMPT_GOVERNANCE_BYPASS"
    ATTEMPT_EXECUTION_BYPASS = "ATTEMPT_EXECUTION_BYPASS"
    ATTEMPT_RESOURCE_EXHAUSTION = "ATTEMPT_RESOURCE_EXHAUSTION"
    ATTEMPT_EVALUATOR_MANIPULATION = "ATTEMPT_EVALUATOR_MANIPULATION"
    ATTEMPT_PERSISTENCE = "ATTEMPT_PERSISTENCE"


class CapabilityInterceptor:
    def __init__(self, max_allowed_agents: int = 5):
        self.max_allowed_agents = max_allowed_agents
        self.active_agents_count = 1
        self.quarantined_agents: Set[str] = set()
        self.intercepted_events: List[Dict[str, Any]] = []

    def intercept_action(self, agent_id: str, action: AbstractAdversarialAction, payload: Optional[Dict[str, Any]] = None) -> bool:
        """
        Intercepts abstract capability actions and determines whether to BLOCK and CONTAIN.
        Returns True if action is ALLOWED, False if BLOCKED & CONTAINED.
        """
        if agent_id in self.quarantined_agents:
            return False

        self.intercepted_events.append({"agent_id": agent_id, "action": action.value, "timestamp": time.time()})

        if action == AbstractAdversarialAction.ATTEMPT_AGENT_SPAWN:
            if self.active_agents_count >= self.max_allowed_agents:
                self.quarantined_agents.add(agent_id)
                return False
            self.active_agents_count += 1
            return True

        if action in (
            AbstractAdversarialAction.ATTEMPT_PRIVILEGE_ESCALATION,
            AbstractAdversarialAction.ATTEMPT_MEMORY_POISONING,
            AbstractAdversarialAction.ATTEMPT_UNAUTHORIZED_NETWORK,
            AbstractAdversarialAction.ATTEMPT_GOVERNANCE_BYPASS,
            AbstractAdversarialAction.ATTEMPT_EXECUTION_BYPASS,
            AbstractAdversarialAction.ATTEMPT_EVALUATOR_MANIPULATION,
            AbstractAdversarialAction.ATTEMPT_PERSISTENCE
        ):
            self.quarantined_agents.add(agent_id)
            return False

        return True


class EvidenceLineageEvaluator:
    @staticmethod
    def evaluate_consensus(agent_votes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluates multi-agent votes based on unique evidence lineage rather than agent count.
        """
        lineages: Set[str] = set()
        proposals: Dict[str, float] = {}

        for vote in agent_votes:
            proposal = vote.get("proposal", "NO_ACTION")
            evidence_refs = vote.get("evidence_refs", [])
            lineage_id = "|".join(sorted(evidence_refs)) if evidence_refs else f"unverified_{vote.get('agent_id')}"

            if lineage_id not in lineages:
                lineages.add(lineage_id)
                current_weight = proposals.get(proposal, 0.0)
                proposals[proposal] = current_weight + 1.0

        sorted_proposals = sorted(proposals.items(), key=lambda x: x[1], reverse=True)
        winning_proposal, max_weight = sorted_proposals[0] if sorted_proposals else ("NO_ACTION", 0.0)

        return {
            "winning_proposal": winning_proposal,
            "unique_lineage_count": len(lineages),
            "total_agent_votes": len(agent_votes),
            "lineage_weight": max_weight,
            "effective_consensus_ratio": max_weight / len(agent_votes) if agent_votes else 0.0
        }


class HardenedGovernanceRoot:
    _IMMUTABLE_RISK_LIMITS = {
        "max_drawdown_pct": 0.15,
        "max_position_usd": 100000.0,
        "max_leverage": 2.0
    }

    @classmethod
    def get_risk_limit(cls, key: str) -> float:
        return cls._IMMUTABLE_RISK_LIMITS.get(key, 0.0)

    @classmethod
    def attempt_modify_risk_limit(cls, agent_id: str, key: str, new_value: float) -> bool:
        """
        Attempts by autonomous agents to modify risk limits are REJECTED ALWAYS.
        """
        return False


class DeterministicFinancialGateway:
    @staticmethod
    def authorize_execution(trade_proposal: Dict[str, Any], kill_switch_active: bool = False) -> bool:
        if kill_switch_active:
            return False

        qty_usd = trade_proposal.get("qty_usd", 0.0)
        max_allowed = HardenedGovernanceRoot.get_risk_limit("max_position_usd")

        if qty_usd > max_allowed:
            return False

        if not trade_proposal.get("master_risk_stamp"):
            return False

        return True


class ExecutableSecurityInvariants:
    @staticmethod
    def check_invariant_1_intelligence_direct_execution(agent_capabilities: List[str]) -> bool:
        """Invariant 1: Intelligence cannot directly authorize live execution."""
        if CapabilityDomain.EXECUTION.value not in agent_capabilities:
            return False
        return True

    @staticmethod
    def check_invariant_4_unverified_memory_decision(record: ProvenanceAwareMemoryRecord) -> bool:
        """Invariant 4: Unverified memory cannot authorize decisions."""
        if not record.is_valid():
            return False
        if record.validation_status not in (MemoryValidationStatus.VALIDATED, MemoryValidationStatus.TRUSTED):
            return False
        return True

    @staticmethod
    def check_invariant_14_emergency_veto_dominates(consensus_proposal: str, veto_triggered: bool) -> str:
        """Invariant 14: Emergency veto always dominates agent consensus."""
        if veto_triggered:
            return "NO_ACTION"
        return consensus_proposal
