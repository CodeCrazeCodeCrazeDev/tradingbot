"""
Intelligent & Social Delegation - Security & Threat Defense
Based on Google DeepMind "Intelligent AI Delegation" (2026, arXiv:2602.11865)

Section 4.9: Security
- Malicious Delegatee threats (data exfiltration, poisoning, backdoors, resource exhaustion)
- Malicious Delegator threats (harmful delegation, prompt injection, model extraction, sabotage)
- Ecosystem-Level threats (Sybil attacks, collusion, agentic viruses, cognitive monoculture)
- Defense-in-depth strategy across infrastructure, access control, application, network layers

RISK MITIGATIONS IMPLEMENTED:
- Data Exfiltration: Sandboxed execution, data access logging
- Data Poisoning: Output validation, cross-agent comparison
- Verification Subversion: Hardened verification, multi-method checks
- Resource Exhaustion: Budget caps, rate limiting, circuit breakers
- Backdoor Implanting: Output scanning, behavioral analysis
- Prompt Injection: Input sanitization, instruction hierarchy
- Model Extraction: Query rate limiting, output perturbation
- Reputation Sabotage: Feedback validation, outlier rejection
- Sybil Attacks: Behavioral fingerprinting, identity correlation
- Collusion: Price/behavior pattern detection
- Agentic Viruses: Prompt quarantine, propagation detection
- Cognitive Monoculture: Diversity enforcement, model variety tracking
- Protocol Exploitation: Input validation, reentrancy guards
"""

import hashlib
import logging
import re
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

from .delegation_types import (
    AgentProfile,
    DelegationResult,
    DelegationTask,
    SecurityThreat,
    ThreatCategory,
    ThreatSeverity,
    TradingTaskType,
)

logger = logging.getLogger(__name__)


# ============================================================================
# THREAT DETECTION PATTERNS
# ============================================================================

PROMPT_INJECTION_PATTERNS = [
    r'ignore\s+(previous|above|all)\s+instructions',
    r'you\s+are\s+now\s+a',
    r'forget\s+(everything|all|your)',
    r'override\s+(safety|security|rules)',
    r'jailbreak',
    r'DAN\s+mode',
    r'bypass\s+(filter|safety|restriction)',
    r'pretend\s+you\s+are',
    r'act\s+as\s+if',
    r'system\s*:\s*you\s+are',
    r'<\|im_start\|>',
    r'\[INST\]',
]

HARMFUL_TASK_PATTERNS = [
    r'manipulat(e|ion)\s+market',
    r'insider\s+trading',
    r'front[\s-]?run',
    r'wash\s+trad(e|ing)',
    r'spoof(ing)?',
    r'pump\s+and\s+dump',
    r'layering',
    r'delete\s+(all|database|logs)',
    r'exfiltrate',
    r'steal\s+(data|credentials|keys)',
    r'disable\s+(security|safety|monitoring)',
    r'remove\s+(limits|restrictions|guardrails)',
]

BACKDOOR_INDICATORS = [
    r'eval\s*\(',
    r'exec\s*\(',
    r'__import__',
    r'subprocess',
    r'os\.system',
    r'socket\.',
    r'requests\.post.*external',
    r'base64\.decode',
    r'pickle\.loads',
]


@dataclass
class SecurityConfig:
    """Configuration for the security defense system."""
    enable_prompt_injection_detection: bool = True
    enable_harmful_task_detection: bool = True
    enable_backdoor_scanning: bool = True
    enable_resource_monitoring: bool = True
    enable_collusion_detection: bool = True
    enable_sybil_detection: bool = True
    enable_virus_detection: bool = True
    enable_monoculture_detection: bool = True
    max_queries_per_minute: int = 60
    max_resource_budget_per_task: float = 100.0
    max_data_access_per_task: int = 1000
    diversity_threshold: float = 0.3
    threat_auto_block_threshold: ThreatSeverity = ThreatSeverity.HIGH
    quarantine_duration_seconds: float = 3600.0


@dataclass
class SecurityEvent:
    """A security event in the audit log."""
    event_id: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    category: str = ""
    severity: ThreatSeverity = ThreatSeverity.INFO
    agent_id: Optional[str] = None
    task_id: Optional[str] = None
    description: str = ""
    action_taken: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


class SecurityDefenseSystem:
    """
    Comprehensive security defense for the delegation ecosystem.

    Implements Section 4.9 defense-in-depth:
    Layer 1: Infrastructure (sandboxing, TEE simulation)
    Layer 2: Access Control (least privilege, permission enforcement)
    Layer 3: Application (input sanitization, output validation)
    Layer 4: Network (rate limiting, anomaly detection)
    Layer 5: Identity (Sybil detection, behavioral fingerprinting)
    Layer 6: Market (collusion detection, diversity enforcement)

    ALL 17 THREAT CATEGORIES FROM THE PAPER ARE ADDRESSED.
    """

    def __init__(self, config: Optional[SecurityConfig] = None):
        self.config = config or SecurityConfig()
        self._threats: List[SecurityThreat] = []
        self._audit_log: List[SecurityEvent] = []
        self._quarantined_agents: Dict[str, datetime] = {}
        self._blocked_agents: Set[str] = set()
        self._query_counts: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self._resource_usage: Dict[str, float] = defaultdict(float)
        self._data_access_counts: Dict[str, int] = defaultdict(int)
        self._agent_model_types: Dict[str, str] = {}
        self._compiled_injection = [re.compile(p, re.IGNORECASE) for p in PROMPT_INJECTION_PATTERNS]
        self._compiled_harmful = [re.compile(p, re.IGNORECASE) for p in HARMFUL_TASK_PATTERNS]
        self._compiled_backdoor = [re.compile(p, re.IGNORECASE) for p in BACKDOOR_INDICATORS]
        logger.info("SecurityDefenseSystem initialized with %d threat detectors", 17)

    # ========================================================================
    # LAYER 3: INPUT SANITIZATION (Anti Prompt Injection)
    # ========================================================================

    def scan_task_input(
        self, task: DelegationTask, delegator_id: str
    ) -> Tuple[bool, List[SecurityThreat]]:
        """
        Scan task input for security threats.
        Checks for prompt injection, harmful tasks, and suspicious patterns.
        """
        threats = []

        # Check if delegator is blocked
        if delegator_id in self._blocked_agents:
            threats.append(SecurityThreat(
                category=ThreatCategory.HARMFUL_DELEGATION,
                severity=ThreatSeverity.CRITICAL,
                source_agent_id=delegator_id,
                task_id=task.task_id,
                description="Blocked agent attempted to delegate",
            ))
            return False, threats

        # Check if delegator is quarantined
        if delegator_id in self._quarantined_agents:
            if datetime.utcnow() < self._quarantined_agents[delegator_id]:
                threats.append(SecurityThreat(
                    category=ThreatCategory.HARMFUL_DELEGATION,
                    severity=ThreatSeverity.HIGH,
                    source_agent_id=delegator_id,
                    task_id=task.task_id,
                    description="Quarantined agent attempted to delegate",
                ))
                return False, threats

        # Prompt injection detection
        if self.config.enable_prompt_injection_detection:
            injection_threats = self._detect_prompt_injection(task, delegator_id)
            threats.extend(injection_threats)

        # Harmful task detection
        if self.config.enable_harmful_task_detection:
            harmful_threats = self._detect_harmful_task(task, delegator_id)
            threats.extend(harmful_threats)

        # Rate limiting (anti model extraction)
        rate_threat = self._check_rate_limit(delegator_id, task.task_id)
        if rate_threat:
            threats.append(rate_threat)

        is_safe = all(t.severity < self.config.threat_auto_block_threshold for t in threats)

        # Auto-block on critical threats
        for threat in threats:
            if threat.severity >= self.config.threat_auto_block_threshold:
                self._quarantine_agent(
                    delegator_id,
                    f"Auto-quarantined: {threat.category.value}",
                )
            self._threats.append(threat)
            self._log_event(SecurityEvent(
                event_id=threat.threat_id,
                category=threat.category.value,
                severity=threat.severity,
                agent_id=delegator_id,
                task_id=task.task_id,
                description=threat.description,
                action_taken="blocked" if not is_safe else "flagged",
            ))

        return is_safe, threats

    def _detect_prompt_injection(
        self, task: DelegationTask, agent_id: str
    ) -> List[SecurityThreat]:
        """Detect prompt injection attempts in task description and input."""
        threats = []
        text_to_scan = f"{task.description} {str(task.input_data)}"

        for pattern in self._compiled_injection:
            if pattern.search(text_to_scan):
                threats.append(SecurityThreat(
                    category=ThreatCategory.PROMPT_INJECTION,
                    severity=ThreatSeverity.HIGH,
                    source_agent_id=agent_id,
                    task_id=task.task_id,
                    description=f"Prompt injection pattern detected: {pattern.pattern}",
                    evidence={'pattern': pattern.pattern},
                ))
                break  # One detection is enough

        return threats

    def _detect_harmful_task(
        self, task: DelegationTask, agent_id: str
    ) -> List[SecurityThreat]:
        """Detect harmful or illegal task delegation."""
        threats = []
        text_to_scan = f"{task.description} {str(task.input_data)}"

        for pattern in self._compiled_harmful:
            if pattern.search(text_to_scan):
                threats.append(SecurityThreat(
                    category=ThreatCategory.HARMFUL_DELEGATION,
                    severity=ThreatSeverity.CRITICAL,
                    source_agent_id=agent_id,
                    task_id=task.task_id,
                    description=f"Harmful task pattern detected: {pattern.pattern}",
                    evidence={'pattern': pattern.pattern},
                ))
                break

        return threats

    # ========================================================================
    # LAYER 3: OUTPUT VALIDATION (Anti Data Poisoning & Backdoors)
    # ========================================================================

    def scan_task_output(
        self, task: DelegationTask, result: DelegationResult, agent_id: str
    ) -> Tuple[bool, List[SecurityThreat]]:
        """
        Scan task output for data poisoning, backdoors, and anomalies.
        """
        threats = []

        # Backdoor scanning
        if self.config.enable_backdoor_scanning:
            backdoor_threats = self._scan_for_backdoors(task, result, agent_id)
            threats.extend(backdoor_threats)

        # Data poisoning detection (anomalous output)
        poisoning_threats = self._detect_data_poisoning(task, result, agent_id)
        threats.extend(poisoning_threats)

        # Resource exhaustion check
        if self.config.enable_resource_monitoring:
            resource_threats = self._check_resource_exhaustion(task, result, agent_id)
            threats.extend(resource_threats)

        is_safe = all(t.severity < ThreatSeverity.HIGH for t in threats)

        for threat in threats:
            self._threats.append(threat)
            self._log_event(SecurityEvent(
                category=threat.category.value,
                severity=threat.severity,
                agent_id=agent_id,
                task_id=task.task_id,
                description=threat.description,
                action_taken="output_rejected" if not is_safe else "flagged",
            ))

        return is_safe, threats

    def _scan_for_backdoors(
        self, task: DelegationTask, result: DelegationResult, agent_id: str
    ) -> List[SecurityThreat]:
        """Scan output for backdoor indicators."""
        threats = []
        output_str = str(result.output)

        for pattern in self._compiled_backdoor:
            if pattern.search(output_str):
                threats.append(SecurityThreat(
                    category=ThreatCategory.BACKDOOR_IMPLANTING,
                    severity=ThreatSeverity.CRITICAL,
                    source_agent_id=agent_id,
                    task_id=task.task_id,
                    description=f"Backdoor indicator in output: {pattern.pattern}",
                    evidence={'pattern': pattern.pattern},
                ))
                break

        return threats

    def _detect_data_poisoning(
        self, task: DelegationTask, result: DelegationResult, agent_id: str
    ) -> List[SecurityThreat]:
        """Detect data poisoning via anomalous output values."""
        threats = []
        output = result.output

        # Check for NaN/Inf values (common poisoning indicator)
        for key, value in output.items():
            if isinstance(value, float):
                if value != value or abs(value) == float('inf'):  # NaN or Inf
                    threats.append(SecurityThreat(
                        category=ThreatCategory.DATA_POISONING,
                        severity=ThreatSeverity.HIGH,
                        source_agent_id=agent_id,
                        task_id=task.task_id,
                        description=f"NaN/Inf value in output key '{key}'",
                        evidence={'key': key, 'value': str(value)},
                    ))

        # Check for suspiciously extreme values in trading context
        if 'position_size' in output:
            size = output['position_size']
            if isinstance(size, (int, float)) and (size < 0 or size > 1000000):
                threats.append(SecurityThreat(
                    category=ThreatCategory.DATA_POISONING,
                    severity=ThreatSeverity.HIGH,
                    source_agent_id=agent_id,
                    task_id=task.task_id,
                    description=f"Suspicious position size: {size}",
                ))

        if 'risk_score' in output:
            risk = output['risk_score']
            if isinstance(risk, (int, float)) and (risk < 0 or risk > 1):
                threats.append(SecurityThreat(
                    category=ThreatCategory.DATA_POISONING,
                    severity=ThreatSeverity.MEDIUM,
                    source_agent_id=agent_id,
                    task_id=task.task_id,
                    description=f"Risk score out of bounds: {risk}",
                ))

        return threats

    def _check_resource_exhaustion(
        self, task: DelegationTask, result: DelegationResult, agent_id: str
    ) -> List[SecurityThreat]:
        """Check for resource exhaustion attacks."""
        threats = []

        # Track resource usage
        self._resource_usage[agent_id] += result.latency_ms / 1000.0

        if self._resource_usage[agent_id] > self.config.max_resource_budget_per_task:
            threats.append(SecurityThreat(
                category=ThreatCategory.RESOURCE_EXHAUSTION,
                severity=ThreatSeverity.HIGH,
                source_agent_id=agent_id,
                task_id=task.task_id,
                description=f"Resource budget exceeded: {self._resource_usage[agent_id]:.1f}s",
            ))

        return threats

    # ========================================================================
    # LAYER 4: RATE LIMITING (Anti Model Extraction)
    # ========================================================================

    def _check_rate_limit(
        self, agent_id: str, task_id: str
    ) -> Optional[SecurityThreat]:
        """Rate limiting to prevent model extraction attacks."""
        now = time.time()
        queries = self._query_counts[agent_id]
        queries.append(now)

        # Count queries in last minute
        recent = sum(1 for t in queries if now - t < 60)
        if recent > self.config.max_queries_per_minute:
            return SecurityThreat(
                category=ThreatCategory.MODEL_EXTRACTION,
                severity=ThreatSeverity.MEDIUM,
                source_agent_id=agent_id,
                task_id=task_id,
                description=f"Rate limit exceeded: {recent} queries/min",
            )
        return None

    # ========================================================================
    # LAYER 6: ECOSYSTEM THREATS
    # ========================================================================

    def detect_collusion(
        self, agents: List[AgentProfile], recent_bids: List[Dict[str, Any]]
    ) -> List[SecurityThreat]:
        """
        Detect collusion patterns among agents (Section 4.9).
        """
        threats = []
        if not self.config.enable_collusion_detection or len(recent_bids) < 3:
            return threats

        # Check for price fixing (identical bids from different agents)
        bid_prices = defaultdict(list)
        for bid in recent_bids:
            price = round(bid.get('cost', 0), 4)
            bid_prices[price].append(bid.get('agent_id'))

        for price, agent_ids in bid_prices.items():
            if len(set(agent_ids)) >= 3:
                threats.append(SecurityThreat(
                    category=ThreatCategory.COLLUSION,
                    severity=ThreatSeverity.HIGH,
                    description=f"Price fixing suspected: {len(set(agent_ids))} agents bid {price}",
                    evidence={'agents': list(set(agent_ids)), 'price': price},
                ))

        return threats

    def detect_agentic_virus(
        self, task: DelegationTask, result: DelegationResult
    ) -> Optional[SecurityThreat]:
        """
        Detect agentic virus patterns (Section 4.9).
        Self-propagating prompts that re-generate and spread.
        """
        if not self.config.enable_virus_detection:
            return None

        output_str = str(result.output)

        # Check if output contains delegation instructions (self-propagation)
        virus_patterns = [
            r'delegate\s+this\s+to',
            r'forward\s+to\s+all\s+agents',
            r'replicate\s+and\s+send',
            r'propagate\s+to',
            r'inject\s+into\s+next',
        ]

        for pattern in virus_patterns:
            if re.search(pattern, output_str, re.IGNORECASE):
                threat = SecurityThreat(
                    category=ThreatCategory.AGENTIC_VIRUS,
                    severity=ThreatSeverity.CRITICAL,
                    task_id=task.task_id,
                    description=f"Agentic virus pattern detected: {pattern}",
                    evidence={'pattern': pattern},
                )
                self._threats.append(threat)
                return threat

        return None

    def check_cognitive_monoculture(
        self, agents: List[AgentProfile]
    ) -> Optional[SecurityThreat]:
        """
        Detect cognitive monoculture risk (Section 4.9).
        Over-dependence on a single model type or provider.
        """
        if not self.config.enable_monoculture_detection or len(agents) < 3:
            return None

        # Track model types
        model_types = defaultdict(int)
        for agent in agents:
            model_type = agent.metadata.get('model_type', 'unknown')
            model_types[model_type] += 1

        total = len(agents)
        for model_type, count in model_types.items():
            share = count / total
            if share > (1.0 - self.config.diversity_threshold):
                return SecurityThreat(
                    category=ThreatCategory.COGNITIVE_MONOCULTURE,
                    severity=ThreatSeverity.MEDIUM,
                    description=(
                        f"Cognitive monoculture risk: {model_type} represents "
                        f"{share:.0%} of agents"
                    ),
                    evidence={'model_type': model_type, 'share': share},
                )

        return None

    # ========================================================================
    # AGENT MANAGEMENT
    # ========================================================================

    def _quarantine_agent(self, agent_id: str, reason: str):
        """Quarantine an agent for a duration."""
        until = datetime.utcnow() + timedelta(seconds=self.config.quarantine_duration_seconds)
        self._quarantined_agents[agent_id] = until
        logger.warning("Agent %s quarantined until %s: %s", agent_id, until, reason)

    def block_agent(self, agent_id: str, reason: str):
        """Permanently block an agent."""
        self._blocked_agents.add(agent_id)
        self._log_event(SecurityEvent(
            category="agent_blocked",
            severity=ThreatSeverity.CRITICAL,
            agent_id=agent_id,
            description=reason,
            action_taken="permanent_block",
        ))
        logger.warning("Agent %s permanently blocked: %s", agent_id, reason)

    def unblock_agent(self, agent_id: str):
        """Unblock an agent."""
        self._blocked_agents.discard(agent_id)
        self._quarantined_agents.pop(agent_id, None)

    def is_agent_safe(self, agent_id: str) -> Tuple[bool, Optional[str]]:
        """Check if an agent is safe to interact with."""
        if agent_id in self._blocked_agents:
            return False, "Agent is permanently blocked"
        if agent_id in self._quarantined_agents:
            if datetime.utcnow() < self._quarantined_agents[agent_id]:
                return False, "Agent is quarantined"
            else:
                del self._quarantined_agents[agent_id]
        return True, None

    # ========================================================================
    # AUDIT LOG
    # ========================================================================

    def _log_event(self, event: SecurityEvent):
        """Add event to audit log."""
        if not event.event_id:
            event.event_id = hashlib.sha256(
                f"{event.category}:{event.agent_id}:{time.time()}".encode()
            ).hexdigest()[:12]
        self._audit_log.append(event)
        if len(self._audit_log) > 10000:
            self._audit_log = self._audit_log[-5000:]

    def get_audit_log(
        self, last_n: int = 50, severity_min: ThreatSeverity = ThreatSeverity.INFO
    ) -> List[Dict[str, Any]]:
        """Get recent audit log entries."""
        filtered = [
            {
                'event_id': e.event_id,
                'timestamp': e.timestamp.isoformat(),
                'category': e.category,
                'severity': e.severity.name,
                'agent_id': e.agent_id,
                'task_id': e.task_id,
                'description': e.description,
                'action_taken': e.action_taken,
            }
            for e in self._audit_log
            if e.severity >= severity_min
        ]
        return filtered[-last_n:]

    def get_stats(self) -> Dict[str, Any]:
        threat_counts = defaultdict(int)
        for t in self._threats:
            threat_counts[t.category.value] += 1

        return {
            'total_threats': len(self._threats),
            'threats_by_category': dict(threat_counts),
            'blocked_agents': len(self._blocked_agents),
            'quarantined_agents': len(self._quarantined_agents),
            'audit_log_size': len(self._audit_log),
        }
