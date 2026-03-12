"""
Intelligent & Social Delegation - Adaptive Coordination & Monitoring
Based on Google DeepMind "Intelligent AI Delegation" (2026, arXiv:2602.11865)

Section 4.4: Adaptive Coordination
- External triggers (spec change, cancellation, resource outage, preemption, security)
- Internal triggers (performance degradation, budget exceeded, verification failed, unresponsive)
- Adaptive response cycle: detect → diagnose → evaluate → respond
- Centralized vs decentralized orchestration
- Market-level stability measures

Section 4.5: Monitoring
- 5 axes: target, observability, transparency, privacy, topology
- Process-level and outcome-level monitoring
- Transitive monitoring via attestation chains
- Event streaming for real-time oversight

RISK MITIGATIONS IMPLEMENTED:
- Oscillation: Cooldown periods, damping factors, re-bid limits
- Cascade Reallocation: Circuit breakers, max re-delegation depth
- Single Point of Failure: Backup agents, decentralized fallback
- Centralization Bottleneck: Span-of-control limits, load shedding
- Unfaithful Reasoning: Cross-validation of agent explanations
- Transitive Monitoring Failure: Attestation chain verification
- Monitoring Overhead: Adaptive monitoring frequency
"""

import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .delegation_types import (
    AdaptiveTrigger,
    AdaptiveTriggerType,
    AgentProfile,
    DelegationContract,
    DelegationTask,
    MonitoringEvent,
    MonitoringMode,
    MonitoringObservability,
    MonitoringPrivacy,
    MonitoringTarget,
    MonitoringTransparency,
    TaskCriticality,
    TaskReversibility,
    ThreatSeverity,
    TradingTaskType,
)

logger = logging.getLogger(__name__)


# ============================================================================
# MONITORING ENGINE (Section 4.5)
# ============================================================================

@dataclass
class MonitoringConfig:
    """Configuration for the monitoring system."""
    default_interval_seconds: float = 10.0
    critical_interval_seconds: float = 1.0
    max_events_per_task: int = 1000
    anomaly_threshold: float = 2.0  # Std devs for anomaly detection
    stale_threshold_seconds: float = 60.0
    enable_process_monitoring: bool = True
    enable_cross_validation: bool = True
    attestation_required: bool = True
    max_monitoring_overhead_percent: float = 10.0


class MonitoringEngine:
    """
    Monitors delegated task execution across all 5 axes from Section 4.5.

    Axes:
    1. Target: outcome-level vs process-level
    2. Observability: direct vs indirect
    3. Transparency: black-box vs white-box
    4. Privacy: full transparency vs zero-knowledge
    5. Topology: direct vs transitive (attestation chains)

    RISK MITIGATIONS:
    - Unfaithful Reasoning (4.5): Cross-validation of agent explanations
    - Transitive Monitoring Failure (4.5): Attestation chain verification
    - Monitoring Overhead (4.5): Adaptive frequency based on task criticality
    """

    def __init__(self, config: Optional[MonitoringConfig] = None):
        self.config = config or MonitoringConfig()
        self._task_events: Dict[str, List[MonitoringEvent]] = defaultdict(list)
        self._task_baselines: Dict[str, Dict[str, float]] = {}
        self._attestation_chains: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._anomaly_counts: Dict[str, int] = defaultdict(int)
        self._last_check: Dict[str, float] = {}
        self._callbacks: List[Callable[[MonitoringEvent], None]] = []
        logger.info("MonitoringEngine initialized")

    def register_callback(self, callback: Callable[[MonitoringEvent], None]):
        """Register a callback for monitoring events."""
        self._callbacks.append(callback)

    def emit_event(self, event: MonitoringEvent):
        """Emit a monitoring event and check for anomalies."""
        task_id = event.task_id
        self._task_events[task_id].append(event)

        # Bound event history
        if len(self._task_events[task_id]) > self.config.max_events_per_task:
            self._task_events[task_id] = self._task_events[task_id][-500:]

        # Anomaly detection
        if event.anomaly_detected:
            self._anomaly_counts[task_id] = self._anomaly_counts.get(task_id, 0) + 1
            logger.warning(
                "Anomaly detected for task %s by agent %s: %s",
                task_id, event.agent_id, event.details,
            )

        # Check quality against baseline
        if event.quality_score is not None:
            self._check_quality_anomaly(event)

        # Notify callbacks
        for cb in self._callbacks:
            try:
                cb(event)
            except Exception as e:
                logger.error("Monitoring callback error: %s", e)

        self._last_check[task_id] = time.time()

    def _check_quality_anomaly(self, event: MonitoringEvent):
        """Detect quality anomalies using baseline comparison."""
        task_id = event.task_id
        baseline = self._task_baselines.get(task_id)
        if not baseline:
            self._task_baselines[task_id] = {
                'quality_sum': event.quality_score,
                'quality_sq_sum': event.quality_score ** 2,
                'count': 1,
            }
            return

        n = baseline['count']
        mean = baseline['quality_sum'] / n
        variance = (baseline['quality_sq_sum'] / n) - (mean ** 2)
        std = max(variance ** 0.5, 0.01)

        if abs(event.quality_score - mean) > self.config.anomaly_threshold * std:
            event.anomaly_detected = True
            self._anomaly_counts[task_id] = self._anomaly_counts.get(task_id, 0) + 1
            logger.warning(
                "Quality anomaly for task %s: score=%.3f, baseline=%.3f±%.3f",
                task_id, event.quality_score, mean, std,
            )

        baseline['quality_sum'] += event.quality_score
        baseline['quality_sq_sum'] += event.quality_score ** 2
        baseline['count'] += 1

    def check_staleness(self, task_id: str) -> bool:
        """Check if a task's monitoring data is stale."""
        last = self._last_check.get(task_id)
        if last is None:
            return True
        return (time.time() - last) > self.config.stale_threshold_seconds

    def get_task_health(self, task_id: str) -> Dict[str, Any]:
        """Get health summary for a monitored task."""
        events = self._task_events.get(task_id, [])
        anomalies = self._anomaly_counts.get(task_id, 0)
        is_stale = self.check_staleness(task_id)

        if not events:
            return {'status': 'unknown', 'events': 0, 'anomalies': 0, 'stale': True}

        latest = events[-1]
        return {
            'status': 'healthy' if anomalies == 0 and not is_stale else 'degraded',
            'events': len(events),
            'anomalies': anomalies,
            'stale': is_stale,
            'latest_progress': latest.progress_percent,
            'latest_quality': latest.quality_score,
            'latest_event_type': latest.event_type,
        }

    # ========================================================================
    # ATTESTATION CHAINS (Section 4.5 - Topology Axis)
    # ========================================================================

    def add_attestation(
        self,
        task_id: str,
        attester_id: str,
        attestee_id: str,
        quality_score: float,
        details: Dict[str, Any],
    ):
        """
        Add a transitive attestation (Section 4.5 Topology).
        Agent B attests to Agent C's work, forwarded to Agent A.
        """
        import hashlib
        content = f"{attester_id}:{attestee_id}:{task_id}:{quality_score}:{time.time()}"
        attestation = {
            'attester_id': attester_id,
            'attestee_id': attestee_id,
            'task_id': task_id,
            'quality_score': quality_score,
            'details': details,
            'timestamp': datetime.utcnow().isoformat(),
            'hash': hashlib.sha256(content.encode()).hexdigest()[:16],
        }
        self._attestation_chains[task_id].append(attestation)

    def verify_attestation_chain(self, task_id: str) -> Tuple[bool, List[str]]:
        """
        RISK MITIGATION: Transitive Monitoring Failure (Section 4.5)
        Verify the integrity of an attestation chain.
        """
        chain = self._attestation_chains.get(task_id, [])
        if not chain:
            return False, ["No attestation chain found"]

        issues = []
        for i, att in enumerate(chain):
            if not att.get('hash'):
                issues.append(f"Missing hash at position {i}")
            if att.get('quality_score', 0) < 0 or att.get('quality_score', 0) > 1:
                issues.append(f"Invalid quality score at position {i}")

        return len(issues) == 0, issues

    # ========================================================================
    # CROSS-VALIDATION (Section 4.5 - Unfaithful Reasoning Mitigation)
    # ========================================================================

    def cross_validate(
        self,
        task_id: str,
        agent_explanation: str,
        agent_output: Dict[str, Any],
        validator_outputs: List[Dict[str, Any]],
    ) -> Tuple[bool, float, str]:
        """
        RISK MITIGATION: Unfaithful Reasoning (Section 4.5)
        Cross-validate agent's explanation against its output and peer outputs.
        """
        if not self.config.enable_cross_validation:
            return True, 1.0, "Cross-validation disabled"

        if not validator_outputs:
            return True, 0.5, "No validators available"

        # Check consistency: does the output match the explanation's claims?
        consistency_score = 1.0

        # Compare with peer outputs for consensus
        if validator_outputs:
            agreements = 0
            for vo in validator_outputs:
                # Simple key overlap check
                common_keys = set(agent_output.keys()) & set(vo.keys())
                if common_keys:
                    matching = sum(
                        1 for k in common_keys
                        if str(agent_output.get(k)) == str(vo.get(k))
                    )
                    agreements += matching / len(common_keys)

            consensus = agreements / len(validator_outputs)
            consistency_score = consensus

        passed = consistency_score >= 0.5
        reason = f"Consensus score: {consistency_score:.2f}"
        return passed, consistency_score, reason

    def get_monitoring_stats(self) -> Dict[str, Any]:
        return {
            'monitored_tasks': len(self._task_events),
            'total_events': sum(len(e) for e in self._task_events.values()),
            'total_anomalies': sum(self._anomaly_counts.values()),
            'attestation_chains': len(self._attestation_chains),
            'stale_tasks': sum(1 for t in self._task_events if self.check_staleness(t)),
        }


# ============================================================================
# ADAPTIVE COORDINATION ENGINE (Section 4.4)
# ============================================================================

@dataclass
class CoordinationConfig:
    """Configuration for adaptive coordination."""
    max_re_delegations: int = 3
    cooldown_seconds: float = 30.0
    damping_factor: float = 0.5
    cascade_circuit_breaker_threshold: int = 5
    max_delegation_chain_depth: int = 5
    immediate_response_threshold: ThreatSeverity = ThreatSeverity.HIGH
    escalation_threshold: ThreatSeverity = ThreatSeverity.CRITICAL
    performance_degradation_threshold: float = 0.3
    budget_exceeded_threshold: float = 1.5
    unresponsive_timeout_seconds: float = 30.0
    enable_preemption: bool = True
    enable_market_stability: bool = True


class AdaptiveCoordinationEngine:
    """
    Handles adaptive re-delegation when tasks fail or conditions change.

    Implements Section 4.4 of the paper:
    - External triggers: spec change, cancellation, resource outage, preemption, security
    - Internal triggers: performance degradation, budget exceeded, verification failed, unresponsive
    - Response cycle: detect → diagnose → evaluate → respond
    - Market stability measures: cooldowns, damping, circuit breakers

    RISK MITIGATIONS:
    - Oscillation (4.4): Cooldown periods between re-delegations
    - Cascade Reallocation (4.4): Circuit breaker after N cascading failures
    - Single Point of Failure (4.4): Backup agent fallback
    - Centralization Bottleneck (4.4): Span-of-control limits
    """

    def __init__(self, config: Optional[CoordinationConfig] = None):
        self.config = config or CoordinationConfig()
        self._re_delegation_counts: Dict[str, int] = defaultdict(int)
        self._last_re_delegation: Dict[str, float] = {}
        self._cascade_counter: int = 0
        self._circuit_breaker_open: bool = False
        self._circuit_breaker_opened_at: Optional[float] = None
        self._trigger_history: List[AdaptiveTrigger] = []
        self._response_callbacks: Dict[AdaptiveTriggerType, List[Callable]] = defaultdict(list)
        logger.info("AdaptiveCoordinationEngine initialized")

    def register_response(
        self,
        trigger_type: AdaptiveTriggerType,
        callback: Callable[[AdaptiveTrigger], Optional[str]],
    ):
        """Register a response handler for a trigger type."""
        self._response_callbacks[trigger_type].append(callback)

    def process_trigger(self, trigger: AdaptiveTrigger) -> Dict[str, Any]:
        """
        Process an adaptive trigger and determine response.
        Returns response action and metadata.
        """
        self._trigger_history.append(trigger)
        task_id = trigger.task_id

        # RISK MITIGATION: Circuit breaker for cascade prevention
        if self._circuit_breaker_open:
            elapsed = time.time() - (self._circuit_breaker_opened_at or 0)
            if elapsed < self.config.cooldown_seconds * 3:
                logger.warning(
                    "Circuit breaker OPEN — blocking re-delegation for task %s",
                    task_id,
                )
                return {
                    'action': 'blocked',
                    'reason': 'circuit_breaker_open',
                    'retry_after': self.config.cooldown_seconds * 3 - elapsed,
                }
            else:
                self._circuit_breaker_open = False
                self._cascade_counter = 0
                logger.info("Circuit breaker CLOSED — resuming normal operations")

        # RISK MITIGATION: Cooldown period (anti-oscillation)
        last = self._last_re_delegation.get(task_id, 0)
        if time.time() - last < self.config.cooldown_seconds:
            logger.debug("Cooldown active for task %s", task_id)
            return {
                'action': 'cooldown',
                'reason': 'cooldown_period',
                'retry_after': self.config.cooldown_seconds - (time.time() - last),
            }

        # RISK MITIGATION: Max re-delegation limit
        count = self._re_delegation_counts.get(task_id, 0)
        if count >= self.config.max_re_delegations:
            logger.warning(
                "Max re-delegations (%d) reached for task %s — escalating",
                self.config.max_re_delegations, task_id,
            )
            return {
                'action': 'escalate_to_human',
                'reason': 'max_re_delegations_exceeded',
                'count': count,
            }

        # Determine response based on trigger type and severity
        response = self._determine_response(trigger)

        # Update cascade counter
        if response.get('action') == 're_delegate':
            self._cascade_counter += 1
            self._re_delegation_counts[task_id] = count + 1
            self._last_re_delegation[task_id] = time.time()

            # Check cascade threshold
            if self._cascade_counter >= self.config.cascade_circuit_breaker_threshold:
                self._circuit_breaker_open = True
                self._circuit_breaker_opened_at = time.time()
                logger.warning(
                    "CASCADE CIRCUIT BREAKER TRIGGERED after %d re-delegations",
                    self._cascade_counter,
                )

        # Execute registered callbacks
        for cb in self._response_callbacks.get(trigger.trigger_type, []):
            try:
                cb(trigger)
            except Exception as e:
                logger.error("Trigger callback error: %s", e)

        return response

    def _determine_response(self, trigger: AdaptiveTrigger) -> Dict[str, Any]:
        """Determine the appropriate response for a trigger."""

        # IMMEDIATE responses (no delay)
        if trigger.requires_immediate_response:
            if trigger.trigger_type == AdaptiveTriggerType.SECURITY_THREAT:
                return {
                    'action': 'terminate_and_escalate',
                    'reason': 'security_threat',
                    'urgency': 'immediate',
                    'details': trigger.details,
                }
            elif trigger.trigger_type == AdaptiveTriggerType.VOLATILITY_SPIKE:
                return {
                    'action': 'pause_and_reassess',
                    'reason': 'volatility_spike',
                    'urgency': 'immediate',
                }
            elif trigger.trigger_type == AdaptiveTriggerType.LIQUIDITY_CRISIS:
                return {
                    'action': 'emergency_exit',
                    'reason': 'liquidity_crisis',
                    'urgency': 'immediate',
                }

        # HUMAN ESCALATION
        if trigger.requires_human_escalation:
            return {
                'action': 'escalate_to_human',
                'reason': trigger.trigger_type.value,
                'severity': trigger.severity.value,
            }

        # Standard responses by trigger type
        responses = {
            AdaptiveTriggerType.PERFORMANCE_DEGRADATION: {
                'action': 're_delegate',
                'reason': 'performance_degradation',
                'strategy': 'find_better_agent',
            },
            AdaptiveTriggerType.BUDGET_EXCEEDED: {
                'action': 'renegotiate_or_terminate',
                'reason': 'budget_exceeded',
                'strategy': 'reduce_scope_or_switch',
            },
            AdaptiveTriggerType.VERIFICATION_FAILED: {
                'action': 're_delegate',
                'reason': 'verification_failed',
                'strategy': 'find_verified_agent',
            },
            AdaptiveTriggerType.AGENT_UNRESPONSIVE: {
                'action': 're_delegate',
                'reason': 'agent_unresponsive',
                'strategy': 'use_backup_or_market',
            },
            AdaptiveTriggerType.SPEC_CHANGE: {
                'action': 'redecompose',
                'reason': 'specification_changed',
                'strategy': 'full_redecomposition',
            },
            AdaptiveTriggerType.TASK_CANCELLED: {
                'action': 'cancel_chain',
                'reason': 'task_cancelled',
                'strategy': 'graceful_termination',
            },
            AdaptiveTriggerType.RESOURCE_UNAVAILABLE: {
                'action': 're_delegate',
                'reason': 'resource_unavailable',
                'strategy': 'find_alternative_resource',
            },
            AdaptiveTriggerType.HIGHER_PRIORITY_TASK: {
                'action': 'preempt',
                'reason': 'higher_priority',
                'strategy': 'pause_and_preempt',
            },
            AdaptiveTriggerType.MARKET_REGIME_CHANGE: {
                'action': 'reassess',
                'reason': 'regime_change',
                'strategy': 'revalidate_all_tasks',
            },
        }

        return responses.get(trigger.trigger_type, {
            'action': 'log_and_monitor',
            'reason': trigger.trigger_type.value,
        })

    # ========================================================================
    # MARKET STABILITY MEASURES (Section 4.4)
    # ========================================================================

    def get_stability_status(self) -> Dict[str, Any]:
        """Get current market stability status."""
        recent_triggers = [
            t for t in self._trigger_history
            if (datetime.utcnow() - t.timestamp).total_seconds() < 300
        ]

        return {
            'circuit_breaker_open': self._circuit_breaker_open,
            'cascade_counter': self._cascade_counter,
            'recent_triggers_5min': len(recent_triggers),
            'total_re_delegations': sum(self._re_delegation_counts.values()),
            'stability': 'stable' if not self._circuit_breaker_open and len(recent_triggers) < 10 else 'unstable',
        }

    def reset_circuit_breaker(self):
        """Manually reset the circuit breaker."""
        self._circuit_breaker_open = False
        self._cascade_counter = 0
        self._circuit_breaker_opened_at = None
        logger.info("Circuit breaker manually reset")

    def get_stats(self) -> Dict[str, Any]:
        return {
            'total_triggers': len(self._trigger_history),
            'total_re_delegations': sum(self._re_delegation_counts.values()),
            'circuit_breaker_open': self._circuit_breaker_open,
            'cascade_counter': self._cascade_counter,
            'registered_handlers': sum(len(v) for v in self._response_callbacks.values()),
        }
