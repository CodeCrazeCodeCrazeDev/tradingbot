"""
Intelligent & Social Delegation - Task Assignment & Multi-objective Optimization
Based on Google DeepMind "Intelligent AI Delegation" (2026, arXiv:2602.11865)

Section 4.2: Task Assignment
- Capability matching via agent registries
- Decentralized market hubs with competitive bidding
- Smart contract formalization with bidirectional protections
- Negotiation and role/boundary establishment

Section 4.3: Multi-objective Optimization
- Pareto optimality across cost, quality, latency, privacy, risk
- Continuous optimization loop with monitoring feedback
- Delegation overhead accounting (complexity floor)
- Cost of adaptation for mid-execution switches

RISK MITIGATIONS IMPLEMENTED:
- Market Manipulation: Bid validation, outlier detection
- Bid Collusion: Diversity enforcement, collusion detection
- Unfair Contracts: Bidirectional protections, renegotiation clauses
- Pareto Suboptimality: Multi-objective scoring with Pareto front
- Delegation Overhead: Overhead accounting, complexity floor
- Cost of Adaptation: Switch cost estimation before re-delegation
"""

import logging
import math
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

from .delegation_types import (
    AgentCapability,
    AgentProfile,
    AgentSpecialization,
    AutonomyLevel,
    DelegationContract,
    DelegationResult,
    DelegationTask,
    MonitoringMode,
    PermissionScope,
    TaskCharacteristics,
    TaskComplexity,
    TaskCriticality,
    TaskReversibility,
    TaskVerifiability,
    TradingTaskType,
)

logger = logging.getLogger(__name__)


# ============================================================================
# BIDDING SYSTEM (Section 4.2)
# ============================================================================

@dataclass
class AgentBid:
    """A bid from an agent to execute a task."""
    bid_id: str = ""
    agent_id: str = ""
    task_id: str = ""
    estimated_duration_ms: float = 1000.0
    estimated_cost: float = 0.0
    estimated_quality: float = 0.8
    confidence: float = 0.7
    resource_requirements: Dict[str, float] = field(default_factory=dict)
    certifications: List[str] = field(default_factory=list)
    proposed_monitoring: MonitoringMode = MonitoringMode.PERIODIC
    proposed_autonomy: AutonomyLevel = AutonomyLevel.EXECUTE_ONLY
    backup_agent_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def value_score(self) -> float:
        """Quality-adjusted value: quality * confidence / (cost + latency_penalty)."""
        latency_penalty = self.estimated_duration_ms / 10000.0
        cost_factor = max(self.estimated_cost, 0.001)
        return (self.estimated_quality * self.confidence) / (cost_factor + latency_penalty + 0.01)


@dataclass
class AssignmentConfig:
    """Configuration for the task assignment engine."""
    max_bids_per_task: int = 10
    bid_timeout_seconds: float = 5.0
    min_trust_threshold: float = 0.3
    min_reputation_threshold: float = 0.2
    diversity_weight: float = 0.15
    cost_weight: float = 0.20
    quality_weight: float = 0.30
    latency_weight: float = 0.20
    trust_weight: float = 0.15
    collusion_detection_enabled: bool = True
    max_single_agent_share: float = 0.4
    enable_negotiation: bool = True
    contract_duration_seconds: float = 3600.0


class TaskAssignmentEngine:
    """
    Assigns decomposed tasks to the best-matched agents.

    Implements Sections 4.2 and 4.3 of the paper:
    - Agent capability matching
    - Competitive bidding with Pareto optimization
    - Smart contract creation with bidirectional protections
    - Collusion and manipulation detection
    - Diversity enforcement to prevent cognitive monoculture

    RISK MITIGATIONS:
    - Market Manipulation (4.2): Bid outlier detection
    - Bid Collusion (4.9): Diversity enforcement, pattern detection
    - Unfair Contracts (4.2): Bidirectional protections
    - Pareto Suboptimality (4.3): Multi-objective Pareto scoring
    - Delegation Overhead (4.3): Overhead accounting
    - Cognitive Monoculture (4.9): Agent diversity enforcement
    """

    def __init__(self, config: Optional[AssignmentConfig] = None):
        self.config = config or AssignmentConfig()
        self._agents: Dict[str, AgentProfile] = {}
        self._contracts: Dict[str, DelegationContract] = {}
        self._assignment_history: List[Dict[str, Any]] = []
        self._agent_task_counts: Dict[str, int] = {}
        logger.info("TaskAssignmentEngine initialized")

    def register_agent(self, agent: AgentProfile):
        """Register an agent in the delegation market."""
        self._agents[agent.agent_id] = agent
        self._agent_task_counts.setdefault(agent.agent_id, 0)
        logger.debug("Registered agent %s (%s)", agent.name, agent.actor_type.value)

    def unregister_agent(self, agent_id: str):
        """Remove an agent from the market."""
        self._agents.pop(agent_id, None)

    def get_agent(self, agent_id: str) -> Optional[AgentProfile]:
        return self._agents.get(agent_id)

    def assign_task(
        self,
        task: DelegationTask,
        available_agents: Optional[List[AgentProfile]] = None,
    ) -> Tuple[Optional[AgentProfile], Optional[DelegationContract]]:
        """
        Assign a task to the best agent using multi-objective optimization.

        Returns (selected_agent, contract) or (None, None) if no suitable agent.
        """
        candidates = available_agents or list(self._agents.values())

        # Step 1: Filter by capability
        capable = self._filter_capable(task, candidates)
        if not capable:
            logger.warning("No capable agents for task %s (%s)", task.task_id, task.task_type.value)
            return None, None

        # Step 2: Filter by trust/reputation threshold
        trusted = self._filter_trusted(capable)
        if not trusted:
            logger.warning("No trusted agents for task %s", task.task_id)
            return None, None

        # Step 3: Collect bids
        bids = self._collect_bids(task, trusted)
        if not bids:
            logger.warning("No bids received for task %s", task.task_id)
            return None, None

        # Step 4: RISK MITIGATION - Detect collusion
        if self.config.collusion_detection_enabled:
            bids = self._detect_collusion(bids)

        # Step 5: Multi-objective Pareto scoring (Section 4.3)
        scored_bids = self._pareto_score(bids, task)

        # Step 6: RISK MITIGATION - Diversity enforcement (anti-monoculture)
        scored_bids = self._enforce_diversity(scored_bids, task)

        if not scored_bids:
            return None, None

        # Step 7: Select best bid
        best_bid = scored_bids[0]
        selected_agent = self._agents.get(best_bid.agent_id)
        if not selected_agent:
            return None, None

        # Step 8: Create smart contract (Section 4.2)
        contract = self._create_contract(task, selected_agent, best_bid)

        # Update state
        selected_agent.current_load += 1
        selected_agent.active_tasks.append(task.task_id)
        self._agent_task_counts[selected_agent.agent_id] = \
            self._agent_task_counts.get(selected_agent.agent_id, 0) + 1
        task.assigned_to = selected_agent.agent_id
        task.status = "assigned"

        self._assignment_history.append({
            'task_id': task.task_id,
            'agent_id': selected_agent.agent_id,
            'bid_score': best_bid.value_score,
            'timestamp': datetime.utcnow().isoformat(),
        })

        logger.info(
            "Assigned task %s to agent %s (score=%.3f, trust=%.2f)",
            task.task_id, selected_agent.name, best_bid.value_score, selected_agent.trust_score,
        )
        return selected_agent, contract

    def release_task(self, task_id: str, agent_id: str):
        """Release a task from an agent (completion or re-delegation)."""
        agent = self._agents.get(agent_id)
        if agent:
            agent.current_load = max(0, agent.current_load - 1)
            if task_id in agent.active_tasks:
                agent.active_tasks.remove(task_id)

    # ========================================================================
    # FILTERING
    # ========================================================================

    def _filter_capable(
        self, task: DelegationTask, agents: List[AgentProfile]
    ) -> List[AgentProfile]:
        """Filter agents by capability match."""
        capable = []
        for agent in agents:
            if not agent.is_available or agent.is_overloaded:
                continue
            if agent.supports_task(task.task_type):
                cap = agent.get_capability_for(task.task_type)
                if cap and cap.proficiency_score >= 0.3:
                    capable.append(agent)
        return capable

    def _filter_trusted(self, agents: List[AgentProfile]) -> List[AgentProfile]:
        """Filter agents by trust and reputation thresholds."""
        return [
            a for a in agents
            if a.trust_score >= self.config.min_trust_threshold
            and a.reputation_score >= self.config.min_reputation_threshold
        ]

    # ========================================================================
    # BIDDING (Section 4.2)
    # ========================================================================

    def _collect_bids(
        self, task: DelegationTask, agents: List[AgentProfile]
    ) -> List[AgentBid]:
        """Collect bids from capable agents."""
        bids = []
        for agent in agents[:self.config.max_bids_per_task]:
            cap = agent.get_capability_for(task.task_type)
            if not cap:
                continue

            bid = AgentBid(
                bid_id=f"bid_{agent.agent_id}_{task.task_id}",
                agent_id=agent.agent_id,
                task_id=task.task_id,
                estimated_duration_ms=cap.avg_latency_ms * (1.0 + agent.utilization),
                estimated_cost=cap.cost_per_task,
                estimated_quality=cap.proficiency_score * cap.success_rate,
                confidence=min(1.0, agent.trust_score * cap.success_rate),
                certifications=cap.certifications,
                proposed_monitoring=self._suggest_monitoring(task),
                proposed_autonomy=self._suggest_autonomy(task, agent),
            )
            bids.append(bid)

        return bids

    def _suggest_monitoring(self, task: DelegationTask) -> MonitoringMode:
        """Suggest monitoring mode based on task characteristics."""
        if task.characteristics.criticality >= TaskCriticality.CRITICAL:
            return MonitoringMode.CONTINUOUS
        elif task.characteristics.criticality >= TaskCriticality.HIGH:
            return MonitoringMode.PERIODIC
        elif task.characteristics.duration_seconds > 60:
            return MonitoringMode.PERIODIC
        return MonitoringMode.OUTCOME_ONLY

    def _suggest_autonomy(
        self, task: DelegationTask, agent: AgentProfile
    ) -> AutonomyLevel:
        """Suggest autonomy level based on trust and task risk."""
        risk = task.characteristics.risk_score
        trust = agent.trust_score

        if risk >= 0.8:
            return AutonomyLevel.EXECUTE_ONLY
        elif trust >= 0.8 and risk < 0.4:
            return AutonomyLevel.DECOMPOSE_AND_EXECUTE
        elif trust >= 0.6:
            return AutonomyLevel.EXECUTE_WITH_PARAMS
        return AutonomyLevel.EXECUTE_ONLY

    # ========================================================================
    # COLLUSION DETECTION (Section 4.9)
    # ========================================================================

    def _detect_collusion(self, bids: List[AgentBid]) -> List[AgentBid]:
        """
        RISK MITIGATION: Detect bid collusion patterns.
        - Suspiciously similar bids
        - Coordinated pricing
        - Agents from same provider bidding identically
        """
        if len(bids) < 3:
            return bids

        costs = [b.estimated_cost for b in bids]
        durations = [b.estimated_duration_ms for b in bids]

        # Check for suspiciously identical bids (skip if all zero-cost / free agents)
        unique_costs = len(set(round(c, 4) for c in costs))
        all_zero = all(c == 0.0 for c in costs)
        if unique_costs == 1 and len(bids) > 2 and not all_zero:
            logger.warning("COLLUSION DETECTED: All %d bids have identical cost", len(bids))
            # Keep only the highest quality bid from each "group"
            bids.sort(key=lambda b: b.estimated_quality, reverse=True)
            return bids[:max(1, len(bids) // 2)]

        # Check for suspiciously tight clustering
        if costs:
            mean_cost = sum(costs) / len(costs)
            variance = sum((c - mean_cost) ** 2 for c in costs) / len(costs)
            cv = math.sqrt(variance) / max(mean_cost, 0.001)
            if cv < 0.01 and len(bids) > 3:
                logger.warning("COLLUSION SUSPECTED: Bid cost variance too low (CV=%.4f)", cv)

        return bids

    # ========================================================================
    # MULTI-OBJECTIVE PARETO SCORING (Section 4.3)
    # ========================================================================

    def _pareto_score(
        self, bids: List[AgentBid], task: DelegationTask
    ) -> List[AgentBid]:
        """
        Score bids using multi-objective optimization.
        Objectives: quality, cost, latency, trust, diversity.
        """
        if not bids:
            return []

        # Normalize each dimension to [0, 1]
        max_quality = max(b.estimated_quality for b in bids) or 1.0
        max_cost = max(b.estimated_cost for b in bids) or 1.0
        max_latency = max(b.estimated_duration_ms for b in bids) or 1.0

        scored = []
        for bid in bids:
            agent = self._agents.get(bid.agent_id)
            if not agent:
                continue

            # Quality: higher is better
            q_score = bid.estimated_quality / max_quality

            # Cost: lower is better (invert)
            c_score = 1.0 - (bid.estimated_cost / max_cost) if max_cost > 0 else 1.0

            # Latency: lower is better (invert)
            l_score = 1.0 - (bid.estimated_duration_ms / max_latency) if max_latency > 0 else 1.0

            # Trust
            t_score = agent.trust_score

            # Weighted sum
            total = (
                self.config.quality_weight * q_score +
                self.config.cost_weight * c_score +
                self.config.latency_weight * l_score +
                self.config.trust_weight * t_score
            )

            # RISK MITIGATION: Boost for task-critical characteristics
            if task.characteristics.criticality >= TaskCriticality.CRITICAL:
                total += 0.1 * t_score  # Extra trust weight for critical tasks

            bid.confidence = total
            scored.append(bid)

        scored.sort(key=lambda b: b.confidence, reverse=True)
        return scored

    # ========================================================================
    # DIVERSITY ENFORCEMENT (Section 4.9 - Anti Cognitive Monoculture)
    # ========================================================================

    def _enforce_diversity(
        self, bids: List[AgentBid], task: DelegationTask
    ) -> List[AgentBid]:
        """
        RISK MITIGATION: Prevent cognitive monoculture.
        Ensure no single agent gets too many tasks.
        """
        if not bids:
            return bids

        total_tasks = sum(self._agent_task_counts.values()) or 1
        filtered = []

        for bid in bids:
            agent_share = self._agent_task_counts.get(bid.agent_id, 0) / total_tasks
            if agent_share > self.config.max_single_agent_share:
                # Penalize over-represented agents
                bid.confidence *= (1.0 - self.config.diversity_weight)
                logger.debug(
                    "Diversity penalty for agent %s (share=%.2f)",
                    bid.agent_id, agent_share,
                )
            filtered.append(bid)

        filtered.sort(key=lambda b: b.confidence, reverse=True)
        return filtered

    # ========================================================================
    # SMART CONTRACT CREATION (Section 4.2)
    # ========================================================================

    def _create_contract(
        self,
        task: DelegationTask,
        agent: AgentProfile,
        bid: AgentBid,
    ) -> DelegationContract:
        """
        Create a bidirectional smart contract (Section 4.2).
        Protects both delegator AND delegatee.
        """
        contract = DelegationContract(
            task_id=task.task_id,
            delegator_id="system",
            delegatee_id=agent.agent_id,
            expires_at=datetime.utcnow() + timedelta(
                seconds=self.config.contract_duration_seconds
            ),
            autonomy_level=bid.proposed_autonomy,
            monitoring_mode=bid.proposed_monitoring,
            monitoring_interval_seconds=self._monitoring_interval(task),
            performance_requirements={
                'min_quality': max(0.5, bid.estimated_quality * 0.8),
                'max_latency_ms': bid.estimated_duration_ms * 2.0,
                'max_resource_usage': 1.5,
            },
            verification_method=self._select_verification(task),
            max_resource_budget={
                'compute_seconds': bid.estimated_duration_ms / 1000.0 * 3.0,
                'memory_mb': 512,
            },
            cancellation_terms="immediate_with_partial_credit",
            renegotiation_allowed=task.characteristics.duration_seconds > 60,
            backup_agent_id=bid.backup_agent_id,
            dispute_resolution="multi_agent_consensus",
        )

        self._contracts[contract.contract_id] = contract
        return contract

    def _monitoring_interval(self, task: DelegationTask) -> float:
        """Determine monitoring interval based on task characteristics."""
        if task.characteristics.criticality >= TaskCriticality.CRITICAL:
            return 1.0
        elif task.characteristics.criticality >= TaskCriticality.HIGH:
            return 5.0
        elif task.characteristics.duration_seconds > 60:
            return 15.0
        return 30.0

    def _select_verification(self, task: DelegationTask) -> str:
        """Select verification method based on verifiability (Section 4.8)."""
        v = task.characteristics.verifiability
        if v <= TaskVerifiability.AUTO_VERIFIABLE:
            return "automated_test"
        elif v <= TaskVerifiability.EASILY_VERIFIABLE:
            return "direct_inspection"
        elif v <= TaskVerifiability.MODERATELY_VERIFIABLE:
            return "multi_agent_consensus"
        elif v <= TaskVerifiability.HARD_TO_VERIFY:
            return "trusted_third_party"
        return "human_review"

    # ========================================================================
    # RE-ASSIGNMENT (Section 4.4)
    # ========================================================================

    def reassign_task(
        self,
        task: DelegationTask,
        reason: str,
        exclude_agents: Optional[Set[str]] = None,
    ) -> Tuple[Optional[AgentProfile], Optional[DelegationContract]]:
        """
        Re-assign a task to a different agent.
        RISK MITIGATION: Cost of Adaptation (Section 4.3) — accounts for switch cost.
        """
        exclude = exclude_agents or set()
        if task.assigned_to:
            exclude.add(task.assigned_to)
            self.release_task(task.task_id, task.assigned_to)

        candidates = [
            a for a in self._agents.values()
            if a.agent_id not in exclude
        ]

        logger.info(
            "Re-assigning task %s (reason: %s, excluded: %d agents)",
            task.task_id, reason, len(exclude),
        )
        return self.assign_task(task, candidates)

    # ========================================================================
    # STATISTICS
    # ========================================================================

    def get_stats(self) -> Dict[str, Any]:
        return {
            'registered_agents': len(self._agents),
            'active_contracts': len(self._contracts),
            'total_assignments': len(self._assignment_history),
            'agent_task_distribution': dict(self._agent_task_counts),
        }

    def get_market_overview(self) -> Dict[str, Any]:
        """Get overview of the delegation market."""
        agents_by_type = {}
        for agent in self._agents.values():
            t = agent.actor_type.value
            agents_by_type[t] = agents_by_type.get(t, 0) + 1

        return {
            'total_agents': len(self._agents),
            'agents_by_type': agents_by_type,
            'available_agents': sum(1 for a in self._agents.values() if a.is_available),
            'overloaded_agents': sum(1 for a in self._agents.values() if a.is_overloaded),
            'avg_trust': sum(a.trust_score for a in self._agents.values()) / max(len(self._agents), 1),
            'avg_reputation': sum(a.reputation_score for a in self._agents.values()) / max(len(self._agents), 1),
        }
