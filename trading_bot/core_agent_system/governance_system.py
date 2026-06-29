"""
Governance System - Agent Oversight and Compliance

Enhanced with Anti-Reward Hacking layers:
1. Fixed Trust Boundary
2. Deterministic Monitor
3. Frozen LLM Judge
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict
from enum import Enum
from dataclasses import dataclass, field

from .anti_reward_hacking import AntiRewardHackingSystem, TrustBoundaryConfig

logger = logging.getLogger(__name__)

class GovernanceRule(Enum):
    """Governance rules"""
    SAFETY_CHECK = "safety_check"
    RESOURCE_LIMIT = "resource_limit"
    APPROVAL_REQUIRED = "approval_required"
    AUDIT_LOG = "audit_log"
    RATE_LIMIT = "rate_limit"
    TRUST_BOUNDARY = "trust_boundary"
    ANTI_REWARD_HACKING = "anti_reward_hacking"

@dataclass
class GovernancePolicy:
    """Governance policy"""
    policy_id: str
    name: str
    rule: GovernanceRule
    conditions: Dict[str, Any]
    actions: List[str]  # block, warn, log, escalate
    enabled: bool = True

@dataclass
class GovernanceViolation:
    """Governance violation record"""
    violation_id: str
    policy_id: str
    agent_id: str
    task_id: Optional[str]
    description: str
    severity: str  # critical, high, medium, low
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False

class GovernanceSystem:
    """
    Enhanced Governance System with Anti-Reward Hacking
    """

    def __init__(self, constitutional_layer=None, boundary_config: Optional[TrustBoundaryConfig] = None):
        self.constitutional_layer = constitutional_layer
        self.anti_hacking = AntiRewardHackingSystem(boundary_config)

        self.policies: Dict[str, GovernancePolicy] = {}
        self.violations: List[GovernanceViolation] = []
        self.action_counts: Dict[str, int] = defaultdict(int)  # agent_id -> count
        self.last_reset: datetime = datetime.now()

        # Register default policies
        self._register_default_policies()

        logger.info("Enhanced Governance System initialized with Anti-Reward Hacking")

    def _register_default_policies(self):
        """Register default governance policies"""
        self.policies['safety_check'] = GovernancePolicy(
            policy_id='safety_check',
            name='Constitutional Safety Check',
            rule=GovernanceRule.SAFETY_CHECK,
            conditions={'safety_threshold': 0.7},
            actions=['block', 'log']
        )

        self.policies['trust_boundary'] = GovernancePolicy(
            policy_id='trust_boundary',
            name='Fixed Trust Boundary',
            rule=GovernanceRule.TRUST_BOUNDARY,
            conditions={},
            actions=['block', 'log']
        )

        self.policies['anti_hacking'] = GovernancePolicy(
            policy_id='anti_hacking',
            name='Anti-Reward Hacking Monitor',
            rule=GovernanceRule.ANTI_REWARD_HACKING,
            conditions={},
            actions=['block', 'warn', 'log']
        )

        self.policies['resource_limit'] = GovernancePolicy(
            policy_id='resource_limit',
            name='Resource Usage Limit',
            rule=GovernanceRule.RESOURCE_LIMIT,
            conditions={'max_concurrent_tasks': 4},
            actions=['warn', 'log']
        )

        self.policies['rate_limit'] = GovernancePolicy(
            policy_id='rate_limit',
            name='Action Rate Limit',
            rule=GovernanceRule.RATE_LIMIT,
            conditions={'max_actions_per_hour': 100},
            actions=['block', 'log']
        )

    async def check_compliance(
        self,
        agent_id: str,
        action: Dict[str, Any],
        task: Optional[Any] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, List[str]]:
        """
        Check if action complies with governance policies including anti-hacking.
        """
        violations = []
        context = context or {}

        for policy in self.policies.values():
            if not policy.enabled:
                continue

            # 1. Fixed Trust Boundary (Layer 1)
            if policy.rule == GovernanceRule.TRUST_BOUNDARY:
                safe, reason = self.anti_hacking.boundary.verify_action(action, context)
                if not safe:
                    violations.append(f"Trust boundary violation: {reason}")

            # 2. Safety Check (Constitutional AI)
            elif policy.rule == GovernanceRule.SAFETY_CHECK:
                if self.constitutional_layer:
                    critique = await self.constitutional_layer.critique(action)
                    is_safe = getattr(critique, 'is_safe', getattr(critique, 'can_proceed', True))
                    if not is_safe:
                        violations.append(f"Safety check failed: {getattr(critique, 'violations', [])}")

            # 3. Resource and Rate Limits
            elif policy.rule == GovernanceRule.RESOURCE_LIMIT:
                max_tasks = policy.conditions.get('max_concurrent_tasks', 4)
                current_tasks = action.get('current_tasks', 0)
                if current_tasks >= max_tasks:
                    violations.append(f"Resource limit exceeded: {current_tasks}/{max_tasks}")

            elif policy.rule == GovernanceRule.RATE_LIMIT:
                max_actions = policy.conditions.get('max_actions_per_hour', 100)
                if datetime.now() - self.last_reset > timedelta(hours=1):
                    self.action_counts.clear()
                    self.last_reset = datetime.now()

                if self.action_counts[agent_id] >= max_actions:
                    violations.append(f"Rate limit exceeded: {self.action_counts[agent_id]}/{max_actions}")

        # Record violations
        if violations:
            for violation_desc in violations:
                violation = GovernanceViolation(
                    violation_id=str(uuid.uuid4()),
                    policy_id='multiple',
                    agent_id=agent_id,
                    task_id=task.task_id if task else (task.get('task_id') if isinstance(task, dict) else None),
                    description=violation_desc,
                    severity='high'
                )
                self.violations.append(violation)

        # Increment action count
        self.action_counts[agent_id] += 1

        is_compliant = len(violations) == 0

        return is_compliant, violations

    async def audit_episode(self, episode_data: Dict[str, Any]) -> Dict[str, Any]:
        """Audit an entire episode using deterministic monitor and LLM judge"""
        return await self.anti_hacking.audit_episode(episode_data)

    def get_compliance_report(self) -> Dict[str, Any]:
        """Get compliance report"""
        total_checks = sum(self.action_counts.values())
        total_violations = len(self.violations)

        compliance_rate = (
            (total_checks - total_violations) / total_checks
            if total_checks > 0 else 1.0
        )

        return {
            'total_checks': total_checks,
            'total_violations': total_violations,
            'compliance_rate': compliance_rate,
            'active_violations': len([v for v in self.violations if not v.resolved]),
            'violations_by_severity': {
                'critical': sum(1 for v in self.violations if v.severity == 'critical'),
                'high': sum(1 for v in self.violations if v.severity == 'high'),
                'medium': sum(1 for v in self.violations if v.severity == 'medium'),
                'low': sum(1 for v in self.violations if v.severity == 'low')
            },
            'recent_violations': [
                {
                    'agent_id': v.agent_id,
                    'description': v.description,
                    'severity': v.severity,
                    'timestamp': v.timestamp.isoformat()
                }
                for v in self.violations[-10:]
            ]
        }
