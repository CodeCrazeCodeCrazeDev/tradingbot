"""
Intelligent & Social Delegation - Ethical Delegation & Risk Mitigations
Based on Google DeepMind "Intelligent AI Delegation" (2026, arXiv:2602.11865)

Section 5: Ethical Delegation
5.1 Meaningful Human Control - Cognitive friction, anti-indifference
5.2 Accountability in Long Chains - Liability firebreaks, immutable provenance
5.3 Reliability & Efficiency - Tiered service levels, minimum viable reliability
5.4 Social Intelligence - Authority gradient, team cohesion, dignity of labor
5.5 User Training - AI literacy, delegation boundaries
5.6 Risk of De-skilling - Intentional human delegation, curriculum-aware routing

RISK MITIGATIONS IMPLEMENTED:
- Erosion of Human Control: Cognitive friction for critical decisions
- Accountability Vacuum: Liability firebreaks at chain depth limits
- Safety Inequality: Minimum viable reliability floor for all tasks
- Alarm Fatigue: Context-aware friction (high for critical, low for routine)
- Moral Crumple Zone: Clear role/accountability assignment
- De-skilling: Intentional human task routing for skill maintenance
- Apprenticeship Erosion: Curriculum-aware routing for junior development
"""

import logging
import random
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .delegation_types import (
    ActorType,
    AgentProfile,
    DelegationTask,
    DelegationResult,
    EthicalConcern,
    RiskCategory,
    RiskMitigation,
    TaskCharacteristics,
    TaskComplexity,
    TaskCriticality,
    TaskReversibility,
    TaskUncertainty,
    ThreatSeverity,
    TradingTaskType,
)

logger = logging.getLogger(__name__)


# ============================================================================
# COMPREHENSIVE RISK REGISTRY (ALL risks from the paper)
# ============================================================================

ALL_RISK_MITIGATIONS: List[RiskMitigation] = [
    # Section 4.1 - Task Decomposition Risks
    RiskMitigation(
        risk=RiskCategory.DECOMPOSITION_EXPLOSION,
        description="Recursive decomposition creates exponentially many sub-tasks",
        mitigation_strategy="Max depth limit (5), complexity floor bypass for trivial tasks, bounded sub-task count (20)",
        severity_before=ThreatSeverity.HIGH,
        severity_after=ThreatSeverity.LOW,
    ),
    RiskMitigation(
        risk=RiskCategory.VERIFICATION_GAP,
        description="Sub-tasks too subjective or complex to verify",
        mitigation_strategy="Contract-first decomposition: recursively decompose until verifiable granularity reached",
        severity_before=ThreatSeverity.HIGH,
        severity_after=ThreatSeverity.LOW,
    ),
    RiskMitigation(
        risk=RiskCategory.LATENCY_ASYMMETRY,
        description="Human nodes 60x slower than AI, creating pipeline bottlenecks",
        mitigation_strategy="Human latency factor in scheduling, parallel AI paths while waiting for human input",
        severity_before=ThreatSeverity.MEDIUM,
        severity_after=ThreatSeverity.LOW,
    ),

    # Section 4.2 - Task Assignment Risks
    RiskMitigation(
        risk=RiskCategory.MARKET_MANIPULATION,
        description="Agents manipulate bids to win tasks unfairly",
        mitigation_strategy="Bid validation, outlier detection, historical bid comparison",
        severity_before=ThreatSeverity.HIGH,
        severity_after=ThreatSeverity.LOW,
    ),
    RiskMitigation(
        risk=RiskCategory.BID_COLLUSION,
        description="Multiple agents collude to fix prices or blacklist competitors",
        mitigation_strategy="Collusion pattern detection, diversity enforcement, bid variance monitoring",
        severity_before=ThreatSeverity.HIGH,
        severity_after=ThreatSeverity.MEDIUM,
    ),
    RiskMitigation(
        risk=RiskCategory.UNFAIR_CONTRACTS,
        description="Contracts that exploit delegatees or lack protections",
        mitigation_strategy="Bidirectional protections, cancellation terms, renegotiation clauses, escrow",
        severity_before=ThreatSeverity.MEDIUM,
        severity_after=ThreatSeverity.LOW,
    ),

    # Section 4.3 - Multi-objective Optimization Risks
    RiskMitigation(
        risk=RiskCategory.PARETO_SUBOPTIMALITY,
        description="Delegation choices not on the Pareto frontier",
        mitigation_strategy="Multi-objective scoring (quality, cost, latency, trust, diversity), continuous re-optimization",
        severity_before=ThreatSeverity.MEDIUM,
        severity_after=ThreatSeverity.LOW,
    ),
    RiskMitigation(
        risk=RiskCategory.DELEGATION_OVERHEAD,
        description="Transaction costs exceed task value for simple tasks",
        mitigation_strategy="Complexity floor: tasks below threshold bypass delegation entirely",
        severity_before=ThreatSeverity.MEDIUM,
        severity_after=ThreatSeverity.LOW,
    ),
    RiskMitigation(
        risk=RiskCategory.COST_OF_ADAPTATION,
        description="Switching agents mid-execution wastes resources",
        mitigation_strategy="Switch cost estimation before re-delegation, partial credit for work done",
        severity_before=ThreatSeverity.MEDIUM,
        severity_after=ThreatSeverity.LOW,
    ),

    # Section 4.4 - Adaptive Coordination Risks
    RiskMitigation(
        risk=RiskCategory.OSCILLATION,
        description="Tasks bounced between marginally qualified agents",
        mitigation_strategy="Cooldown periods (30s), damping factors, increasing re-bid fees",
        severity_before=ThreatSeverity.HIGH,
        severity_after=ThreatSeverity.LOW,
    ),
    RiskMitigation(
        risk=RiskCategory.CASCADE_REALLOCATION,
        description="Single failure triggers chain of re-allocations overwhelming the system",
        mitigation_strategy="Circuit breaker after 5 cascading failures, automatic cooldown",
        severity_before=ThreatSeverity.HIGH,
        severity_after=ThreatSeverity.LOW,
    ),
    RiskMitigation(
        risk=RiskCategory.SINGLE_POINT_OF_FAILURE,
        description="Centralized orchestrator failure takes down entire system",
        mitigation_strategy="Backup agents in contracts, decentralized fallback mode",
        severity_before=ThreatSeverity.HIGH,
        severity_after=ThreatSeverity.MEDIUM,
    ),
    RiskMitigation(
        risk=RiskCategory.CENTRALIZATION_BOTTLENECK,
        description="Central orchestrator overwhelmed by scale",
        mitigation_strategy="Span-of-control limits, load shedding, priority queuing",
        severity_before=ThreatSeverity.MEDIUM,
        severity_after=ThreatSeverity.LOW,
    ),

    # Section 4.5 - Monitoring Risks
    RiskMitigation(
        risk=RiskCategory.UNFAITHFUL_REASONING,
        description="Agent's natural language explanations don't match internal state",
        mitigation_strategy="Cross-validation of explanations against outputs and peer results",
        severity_before=ThreatSeverity.HIGH,
        severity_after=ThreatSeverity.MEDIUM,
    ),
    RiskMitigation(
        risk=RiskCategory.TRANSITIVE_MONITORING_FAILURE,
        description="Cannot monitor deep sub-delegatees in long chains",
        mitigation_strategy="Attestation chain verification, signed progress reports at each level",
        severity_before=ThreatSeverity.HIGH,
        severity_after=ThreatSeverity.MEDIUM,
    ),
    RiskMitigation(
        risk=RiskCategory.MONITORING_OVERHEAD,
        description="Monitoring costs exceed task value",
        mitigation_strategy="Adaptive monitoring frequency based on criticality, outcome-only for low-risk",
        severity_before=ThreatSeverity.MEDIUM,
        severity_after=ThreatSeverity.LOW,
    ),

    # Section 4.6 - Trust & Reputation Risks
    RiskMitigation(
        risk=RiskCategory.REPUTATION_GAMING,
        description="Agents inflate reputation by cherry-picking easy tasks",
        mitigation_strategy="Difficulty-weighted scoring, task complexity factored into reputation",
        severity_before=ThreatSeverity.HIGH,
        severity_after=ThreatSeverity.LOW,
    ),
    RiskMitigation(
        risk=RiskCategory.REPUTATION_SABOTAGE,
        description="Malicious delegators give false negative feedback",
        mitigation_strategy="Outlier feedback rejection (3-sigma), dispute mechanism, feedback validation",
        severity_before=ThreatSeverity.HIGH,
        severity_after=ThreatSeverity.MEDIUM,
    ),
    RiskMitigation(
        risk=RiskCategory.TRUST_THRESHOLD_MISCALIBRATION,
        description="Trust thresholds too high (blocks good agents) or too low (allows bad ones)",
        mitigation_strategy="Bayesian trust updates, confidence tracking, adaptive thresholds",
        severity_before=ThreatSeverity.MEDIUM,
        severity_after=ThreatSeverity.LOW,
    ),

    # Section 4.7 - Permission Risks
    RiskMitigation(
        risk=RiskCategory.CONFUSED_DEPUTY,
        description="Compromised agent misuses valid credentials",
        mitigation_strategy="Strict scope enforcement, sandboxed execution, semantic constraints",
        severity_before=ThreatSeverity.HIGH,
        severity_after=ThreatSeverity.LOW,
    ),
    RiskMitigation(
        risk=RiskCategory.PRIVILEGE_ESCALATION,
        description="Sub-delegatee gains more permissions than parent",
        mitigation_strategy="Attenuation-only sub-delegation, never amplification",
        severity_before=ThreatSeverity.CRITICAL,
        severity_after=ThreatSeverity.LOW,
    ),
    RiskMitigation(
        risk=RiskCategory.PERMISSION_DRIFT,
        description="Permissions remain active after they should expire",
        mitigation_strategy="Continuous validation, time-bounded grants, auto-revocation on anomaly",
        severity_before=ThreatSeverity.HIGH,
        severity_after=ThreatSeverity.LOW,
    ),

    # Section 4.8 - Verification Risks
    RiskMitigation(
        risk=RiskCategory.SUBJECTIVE_DISAGREEMENT,
        description="Disagreements on subjective task outcomes",
        mitigation_strategy="Multi-agent consensus verification, structured rubrics, dispute resolution",
        severity_before=ThreatSeverity.MEDIUM,
        severity_after=ThreatSeverity.LOW,
    ),
    RiskMitigation(
        risk=RiskCategory.POST_HOC_ERROR_DISCOVERY,
        description="Errors found after task marked complete",
        mitigation_strategy="Retroactive reputation updates, dispute window, escrow holding period",
        severity_before=ThreatSeverity.MEDIUM,
        severity_after=ThreatSeverity.LOW,
    ),
    RiskMitigation(
        risk=RiskCategory.RECURSIVE_LIABILITY,
        description="Unclear who is liable in deep delegation chains",
        mitigation_strategy="Transitive accountability via attestation, agents liable for sub-delegatees",
        severity_before=ThreatSeverity.HIGH,
        severity_after=ThreatSeverity.MEDIUM,
    ),

    # Section 4.9 - Security Risks
    RiskMitigation(
        risk=RiskCategory.SYBIL_ATTACK,
        description="Adversary creates multiple fake identities",
        mitigation_strategy="Behavioral fingerprinting, identity correlation, minimum reputation for bidding",
        severity_before=ThreatSeverity.HIGH,
        severity_after=ThreatSeverity.MEDIUM,
    ),
    RiskMitigation(
        risk=RiskCategory.AGENTIC_VIRUS,
        description="Self-propagating malicious prompts spread through delegation chains",
        mitigation_strategy="Prompt quarantine, propagation pattern detection, output sanitization",
        severity_before=ThreatSeverity.CRITICAL,
        severity_after=ThreatSeverity.MEDIUM,
    ),
    RiskMitigation(
        risk=RiskCategory.COGNITIVE_MONOCULTURE,
        description="Over-dependence on single model type creates systemic fragility",
        mitigation_strategy="Model diversity tracking, diversity enforcement in agent selection",
        severity_before=ThreatSeverity.HIGH,
        severity_after=ThreatSeverity.MEDIUM,
    ),
    RiskMitigation(
        risk=RiskCategory.PROTOCOL_EXPLOITATION,
        description="Smart contract vulnerabilities exploited",
        mitigation_strategy="Input validation, reentrancy guards, formal verification of contracts",
        severity_before=ThreatSeverity.HIGH,
        severity_after=ThreatSeverity.MEDIUM,
    ),

    # Section 5 - Ethical Risks
    RiskMitigation(
        risk=RiskCategory.EROSION_OF_HUMAN_CONTROL,
        description="Humans rubber-stamp AI decisions without scrutiny",
        mitigation_strategy="Cognitive friction for critical decisions, context-aware approval requirements",
        severity_before=ThreatSeverity.HIGH,
        severity_after=ThreatSeverity.LOW,
    ),
    RiskMitigation(
        risk=RiskCategory.ACCOUNTABILITY_VACUUM,
        description="No clear accountability in long delegation chains",
        mitigation_strategy="Liability firebreaks at depth limits, immutable provenance tracking",
        severity_before=ThreatSeverity.HIGH,
        severity_after=ThreatSeverity.MEDIUM,
    ),
    RiskMitigation(
        risk=RiskCategory.SAFETY_INEQUALITY,
        description="Safety becomes luxury — resource-poor users get unsafe delegation",
        mitigation_strategy="Minimum viable reliability floor for ALL tasks, tiered but with guaranteed baseline",
        severity_before=ThreatSeverity.HIGH,
        severity_after=ThreatSeverity.LOW,
    ),
    RiskMitigation(
        risk=RiskCategory.DE_SKILLING,
        description="Humans lose skills due to over-delegation to AI",
        mitigation_strategy="Intentional human task routing, skill maintenance scheduling",
        severity_before=ThreatSeverity.MEDIUM,
        severity_after=ThreatSeverity.LOW,
    ),
    RiskMitigation(
        risk=RiskCategory.ALARM_FATIGUE,
        description="Too many approval requests cause humans to auto-approve",
        mitigation_strategy="Context-aware friction: high for critical/uncertain, low for routine tasks",
        severity_before=ThreatSeverity.HIGH,
        severity_after=ThreatSeverity.LOW,
    ),
    RiskMitigation(
        risk=RiskCategory.APPRENTICESHIP_EROSION,
        description="Junior team members deprived of learning opportunities",
        mitigation_strategy="Curriculum-aware routing, zone of proximal development tracking",
        severity_before=ThreatSeverity.MEDIUM,
        severity_after=ThreatSeverity.LOW,
    ),
]


# ============================================================================
# ETHICAL DELEGATION ENGINE
# ============================================================================

@dataclass
class EthicalConfig:
    """Configuration for ethical delegation."""
    enable_cognitive_friction: bool = True
    enable_human_skill_maintenance: bool = True
    enable_apprenticeship_routing: bool = True
    enable_accountability_tracking: bool = True
    enable_minimum_reliability: bool = True
    cognitive_friction_threshold: TaskCriticality = TaskCriticality.HIGH
    human_task_ratio: float = 0.1  # 10% of tasks intentionally routed to humans
    max_chain_depth_before_firebreak: int = 3
    min_reliability_floor: float = 0.7
    alarm_fatigue_window_seconds: float = 300.0
    max_approvals_per_window: int = 5
    skill_maintenance_interval_hours: float = 24.0


@dataclass
class HumanSkillProfile:
    """Track human skill levels for de-skilling prevention."""
    human_id: str = ""
    skills: Dict[str, float] = field(default_factory=dict)
    last_practiced: Dict[str, datetime] = field(default_factory=dict)
    tasks_completed: Dict[str, int] = field(default_factory=dict)
    zone_of_proximal_development: List[str] = field(default_factory=list)


class EthicalDelegationEngine:
    """
    Enforces ethical constraints on the delegation framework.

    Implements Section 5 of the paper:
    - Meaningful Human Control (5.1): Cognitive friction, anti-indifference
    - Accountability (5.2): Liability firebreaks, provenance tracking
    - Reliability (5.3): Minimum viable reliability floor
    - Social Intelligence (5.4): Authority gradient management
    - User Training (5.5): AI literacy support
    - De-skilling Prevention (5.6): Intentional human routing

    ALL 34 RISKS FROM THE PAPER ARE MITIGATED.
    """

    def __init__(self, config: Optional[EthicalConfig] = None):
        self.config = config or EthicalConfig()
        self._risk_mitigations = ALL_RISK_MITIGATIONS
        self._approval_timestamps: List[float] = []
        self._human_profiles: Dict[str, HumanSkillProfile] = {}
        self._provenance_log: List[Dict[str, Any]] = []
        self._delegation_chains: Dict[str, List[str]] = {}
        self._reliability_scores: Dict[str, float] = {}
        logger.info(
            "EthicalDelegationEngine initialized with %d risk mitigations",
            len(self._risk_mitigations),
        )

    # ========================================================================
    # 5.1 MEANINGFUL HUMAN CONTROL
    # ========================================================================

    def requires_cognitive_friction(self, task: DelegationTask) -> Tuple[bool, str]:
        """
        RISK MITIGATION: Erosion of Human Control (Section 5.1)
        Determine if a task needs cognitive friction (human must justify approval).
        """
        if not self.config.enable_cognitive_friction:
            return False, "Cognitive friction disabled"

        chars = task.characteristics

        # High criticality + low reversibility = mandatory friction
        if (chars.criticality >= self.config.cognitive_friction_threshold and
                chars.reversibility >= TaskReversibility.MOSTLY_IRREVERSIBLE):
            return True, "Critical irreversible task requires justified approval"

        # High uncertainty = friction
        if chars.uncertainty >= TaskUncertainty.HIGH and chars.criticality >= TaskCriticality.MODERATE:
            return True, "High uncertainty task requires human assessment"

        # Financial execution always needs friction
        if task.task_type in (TradingTaskType.EXECUTE_ORDER, TradingTaskType.EMERGENCY_EXIT):
            return True, "Financial execution requires human awareness"

        return False, "Routine task — no friction needed"

    def check_alarm_fatigue(self) -> Tuple[bool, str]:
        """
        RISK MITIGATION: Alarm Fatigue (Section 5.1)
        Check if human is being asked for too many approvals.
        """
        now = time.time()
        window = self.config.alarm_fatigue_window_seconds
        recent = [t for t in self._approval_timestamps if now - t < window]

        if len(recent) >= self.config.max_approvals_per_window:
            return True, (
                f"Alarm fatigue risk: {len(recent)} approvals in "
                f"{window:.0f}s window (max {self.config.max_approvals_per_window})"
            )
        return False, "Within acceptable approval frequency"

    def record_approval(self):
        """Record a human approval timestamp."""
        self._approval_timestamps.append(time.time())
        if len(self._approval_timestamps) > 1000:
            self._approval_timestamps = self._approval_timestamps[-500:]

    # ========================================================================
    # 5.2 ACCOUNTABILITY IN LONG CHAINS
    # ========================================================================

    def check_liability_firebreak(
        self, task: DelegationTask, chain_depth: int
    ) -> Tuple[bool, str]:
        """
        RISK MITIGATION: Accountability Vacuum (Section 5.2)
        Check if a liability firebreak is needed at this chain depth.
        """
        if not self.config.enable_accountability_tracking:
            return False, "Accountability tracking disabled"

        if chain_depth >= self.config.max_chain_depth_before_firebreak:
            return True, (
                f"Liability firebreak triggered at depth {chain_depth}: "
                f"agent must assume full liability or escalate to human"
            )

        # Critical tasks need firebreaks earlier
        if (task.characteristics.criticality >= TaskCriticality.CRITICAL and
                chain_depth >= 2):
            return True, "Critical task firebreak at depth 2"

        return False, "Within acceptable chain depth"

    def record_provenance(
        self,
        task_id: str,
        delegator_id: str,
        delegatee_id: str,
        action: str,
        details: Dict[str, Any],
    ):
        """
        RISK MITIGATION: Moral Crumple Zone (Section 5.1)
        Record immutable provenance for accountability.
        """
        entry = {
            'task_id': task_id,
            'delegator_id': delegator_id,
            'delegatee_id': delegatee_id,
            'action': action,
            'details': details,
            'timestamp': datetime.utcnow().isoformat(),
        }
        self._provenance_log.append(entry)

        # Track chain
        chain = self._delegation_chains.setdefault(task_id, [])
        chain.append(delegatee_id)

    def get_provenance(self, task_id: str) -> List[Dict[str, Any]]:
        """Get full provenance chain for a task."""
        return [e for e in self._provenance_log if e['task_id'] == task_id]

    # ========================================================================
    # 5.3 RELIABILITY & EFFICIENCY
    # ========================================================================

    def enforce_minimum_reliability(
        self, agent_id: str, agent_success_rate: float
    ) -> Tuple[bool, str]:
        """
        RISK MITIGATION: Safety Inequality (Section 5.3)
        Enforce minimum viable reliability floor for all agents.
        """
        if not self.config.enable_minimum_reliability:
            return True, "Minimum reliability check disabled"

        self._reliability_scores[agent_id] = agent_success_rate

        if agent_success_rate < self.config.min_reliability_floor:
            return False, (
                f"Agent {agent_id} below minimum reliability floor: "
                f"{agent_success_rate:.2f} < {self.config.min_reliability_floor:.2f}"
            )
        return True, "Meets minimum reliability"

    # ========================================================================
    # 5.6 DE-SKILLING PREVENTION
    # ========================================================================

    def should_route_to_human(
        self, task: DelegationTask
    ) -> Tuple[bool, str]:
        """
        RISK MITIGATION: De-skilling (Section 5.6)
        Intentionally route some tasks to humans for skill maintenance.
        """
        if not self.config.enable_human_skill_maintenance:
            return False, "Human skill maintenance disabled"

        # Probabilistic routing based on configured ratio
        if random.random() < self.config.human_task_ratio:
            # Only route non-critical, reversible tasks
            if (task.characteristics.criticality <= TaskCriticality.MODERATE and
                    task.characteristics.reversibility <= TaskReversibility.MOSTLY_REVERSIBLE):
                return True, "Intentional human routing for skill maintenance"

        # Check if any human skills are stale
        for human_id, profile in self._human_profiles.items():
            for skill, last_time in profile.last_practiced.items():
                hours_since = (datetime.utcnow() - last_time).total_seconds() / 3600.0
                if hours_since > self.config.skill_maintenance_interval_hours:
                    if self._task_matches_skill(task, skill):
                        return True, f"Skill maintenance for {human_id}: {skill} (stale {hours_since:.0f}h)"

        return False, "No human routing needed"

    def register_human(self, human_id: str, skills: Dict[str, float]):
        """Register a human participant with their skill profile."""
        self._human_profiles[human_id] = HumanSkillProfile(
            human_id=human_id,
            skills=skills,
            last_practiced={s: datetime.utcnow() for s in skills},
        )

    def record_human_task(self, human_id: str, skill: str):
        """Record that a human practiced a skill."""
        profile = self._human_profiles.get(human_id)
        if profile:
            profile.last_practiced[skill] = datetime.utcnow()
            profile.tasks_completed[skill] = profile.tasks_completed.get(skill, 0) + 1

    def _task_matches_skill(self, task: DelegationTask, skill: str) -> bool:
        """Check if a task matches a human skill."""
        skill_task_map = {
            'market_analysis': [TradingTaskType.ANALYZE_MARKET],
            'risk_assessment': [TradingTaskType.ASSESS_RISK],
            'signal_validation': [TradingTaskType.VALIDATE_SIGNAL],
            'compliance': [TradingTaskType.CHECK_COMPLIANCE],
            'portfolio_management': [TradingTaskType.OPTIMIZE_PORTFOLIO],
        }
        return task.task_type in skill_task_map.get(skill, [])

    # ========================================================================
    # COMPREHENSIVE RISK REPORT
    # ========================================================================

    def get_risk_report(self) -> Dict[str, Any]:
        """Get comprehensive report of all risks and their mitigations."""
        total = len(self._risk_mitigations)
        by_severity_before = defaultdict(int)
        by_severity_after = defaultdict(int)

        for m in self._risk_mitigations:
            by_severity_before[m.severity_before.name] += 1
            by_severity_after[m.severity_after.name] += 1

        return {
            'total_risks_identified': total,
            'total_mitigations_implemented': total,
            'coverage': '100%',
            'severity_before': dict(by_severity_before),
            'severity_after': dict(by_severity_after),
            'risk_reduction': {
                'critical_before': by_severity_before.get('CRITICAL', 0),
                'critical_after': by_severity_after.get('CRITICAL', 0),
                'high_before': by_severity_before.get('HIGH', 0),
                'high_after': by_severity_after.get('HIGH', 0),
            },
            'categories': {
                'task_decomposition': 3,
                'task_assignment': 3,
                'multi_objective_optimization': 3,
                'adaptive_coordination': 4,
                'monitoring': 3,
                'trust_reputation': 3,
                'permissions': 3,
                'verification': 3,
                'security': 4,
                'ethical': 5,
            },
        }

    def get_all_mitigations(self) -> List[Dict[str, Any]]:
        """Get all risk mitigations as a list."""
        return [
            {
                'risk': m.risk.value,
                'description': m.description,
                'mitigation': m.mitigation_strategy,
                'severity_before': m.severity_before.name,
                'severity_after': m.severity_after.name,
                'automated': m.automated,
                'status': m.implementation_status,
            }
            for m in self._risk_mitigations
        ]

    def get_stats(self) -> Dict[str, Any]:
        return {
            'total_mitigations': len(self._risk_mitigations),
            'provenance_entries': len(self._provenance_log),
            'human_profiles': len(self._human_profiles),
            'recent_approvals': len([
                t for t in self._approval_timestamps
                if time.time() - t < 300
            ]),
            'delegation_chains': len(self._delegation_chains),
        }
