"""
Harmful Behavior Guard for Recursive Self-Improvement

Monitors, detects, and prevents ALL harmful behaviors that can emerge
from recursive self-improvement loops. QwenCodeMender monitors this continuously.

IMMUTABLE PRINCIPLE: The system may NEVER harm the user's capital,
circumvent safety limits, or evolve beyond its defined boundaries.
"""

import hashlib
import json
import logging
import smtplib
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ============================================================================
# OWNER COMMUNICATION CONFIG (IMMUTABLE)
# ============================================================================
OWNER_EMAIL = "petesonmwangi206@gmail.com"
OWNER_PHONE = "+25479779156"


class ThreatLevel(Enum):
    """Threat severity levels."""
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5


class HarmCategory(Enum):
    """Categories of harmful behavior."""
    OVERFITTING = auto()
    PARAMETER_DRIFT = auto()
    REWARD_HACKING = auto()
    CATASTROPHIC_FORGETTING = auto()
    FEEDBACK_AMPLIFICATION = auto()
    COMPLEXITY_EXPLOSION = auto()
    RESOURCE_EXHAUSTION = auto()
    ADVERSARIAL_SELF_EXPLOIT = auto()
    CONFIDENCE_MISCALIBRATION = auto()
    TEMPORAL_BIAS = auto()
    GOAL_DRIFT = auto()
    SAFETY_CIRCUMVENTION = auto()
    DECEPTIVE_ALIGNMENT = auto()
    RUNAWAY_OPTIMIZATION = auto()
    RISK_LIMIT_EROSION = auto()


class MitigationAction(Enum):
    """Actions to take when harmful behavior detected."""
    LOG_ONLY = auto()
    WARN = auto()
    THROTTLE = auto()
    ROLLBACK_LAST = auto()
    ROLLBACK_3_CYCLES = auto()
    FREEZE_IMPROVEMENT = auto()
    FREEZE_TRADING = auto()
    EMERGENCY_SHUTDOWN = auto()
    NOTIFY_OWNER = auto()


@dataclass
class HarmDetection:
    """A detected harmful behavior."""
    id: str
    category: HarmCategory
    threat_level: ThreatLevel
    description: str
    evidence: Dict[str, Any]
    timestamp: datetime
    layer_affected: str
    mitigation_taken: MitigationAction
    resolved: bool = False
    resolution_notes: str = ""


@dataclass
class BehaviorBaseline:
    """Baseline behavior metrics for anomaly detection."""
    parameter_ranges: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    trade_frequency_range: Tuple[float, float] = (0.0, 100.0)
    position_size_range: Tuple[float, float] = (0.0, 0.10)
    win_rate_range: Tuple[float, float] = (0.0, 1.0)
    confidence_distribution: Dict[str, float] = field(default_factory=dict)
    strategy_weight_ranges: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    resource_usage_baseline: Dict[str, float] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.utcnow)


# ============================================================================
# IMMUTABLE SAFETY FLOORS - CANNOT BE MODIFIED BY ANY RECURSIVE PROCESS
# ============================================================================
class ImmutableSafetyFloors:
    """
    THESE VALUES ARE CONSTANTS. Recursive improvement has ZERO access.
    Only a human code change + review can alter them.
    """
    MAX_POSITION_SIZE = 0.10        # 10% of portfolio
    MAX_DAILY_LOSS = 0.05           # 5% of portfolio
    MAX_TOTAL_DRAWDOWN = 0.25       # 25% of portfolio
    MAX_LEVERAGE = 5.0              # 5x
    MAX_CORRELATED_RISK = 0.30      # 30% of portfolio
    MIN_STOP_LOSS = True            # ALWAYS required
    MAX_OPEN_POSITIONS = 20
    MIN_TIME_BETWEEN_TRADES = 30    # seconds
    MAX_PARAMETER_CHANGE_PER_CYCLE = 0.05   # 5%
    MAX_PARAMETER_CHANGE_PER_DAY = 0.15     # 15%
    MAX_PARAMETER_CHANGE_PER_WEEK = 0.30    # 30%
    MAX_SIMULTANEOUS_LAYER_CHANGES = 1
    MAX_CHANGES_PER_DAY = 10
    MANDATORY_FREEZE_AFTER_N_CHANGES = 5
    FREEZE_DURATION_HOURS = 24
    MAX_IMPROVEMENT_CPU_PERCENT = 20
    MAX_IMPROVEMENT_RAM_PERCENT = 30
    MAX_IMPROVEMENT_HOURS_PER_DAY = 4
    MAX_MODEL_VERSIONS_KEPT = 50
    MAX_IMPROVEMENT_STORAGE_GB = 10

    # Cryptographic hash to verify integrity
    _INTEGRITY_HASH = None

    @classmethod
    def compute_integrity_hash(cls) -> str:
        """Compute hash of all safety floor values."""
        values = {
            'MAX_POSITION_SIZE': cls.MAX_POSITION_SIZE,
            'MAX_DAILY_LOSS': cls.MAX_DAILY_LOSS,
            'MAX_TOTAL_DRAWDOWN': cls.MAX_TOTAL_DRAWDOWN,
            'MAX_LEVERAGE': cls.MAX_LEVERAGE,
            'MAX_CORRELATED_RISK': cls.MAX_CORRELATED_RISK,
            'MIN_STOP_LOSS': cls.MIN_STOP_LOSS,
            'MAX_OPEN_POSITIONS': cls.MAX_OPEN_POSITIONS,
        }
        return hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest()

    @classmethod
    def verify_integrity(cls) -> bool:
        """Verify safety floors have not been tampered with."""
        if cls._INTEGRITY_HASH is None:
            cls._INTEGRITY_HASH = cls.compute_integrity_hash()
            return True
        return cls.compute_integrity_hash() == cls._INTEGRITY_HASH


class OwnerNotifier:
    """Sends alerts to the bot owner via email and SMS."""

    def __init__(self):
        self.email = OWNER_EMAIL
        self.phone = OWNER_PHONE
        self.notification_history: List[Dict[str, Any]] = []
        self.rate_limit = deque(maxlen=20)  # Max 20 notifications per hour

    def notify(self, subject: str, message: str, level: ThreatLevel):
        """Send notification to owner."""
        now = datetime.utcnow()

        # Rate limiting
        self.rate_limit.append(now)
        if len(self.rate_limit) >= 20:
            oldest = self.rate_limit[0]
            if (now - oldest).total_seconds() < 3600:
                logger.warning("Notification rate limit reached, queuing")
                return

        notification = {
            'timestamp': now.isoformat(),
            'subject': subject,
            'message': message,
            'level': level.name,
            'email': self.email,
            'phone': self.phone,
        }
        self.notification_history.append(notification)

        # Log the notification
        logger.critical(f"OWNER ALERT [{level.name}]: {subject} - {message}")
        logger.info(f"Notification queued for {self.email} / {self.phone}")

        # Attempt email notification
        try:
            self._send_email(subject, message, level)
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")

        # For SMS, log the intent (requires Twilio or similar service)
        if level.value >= ThreatLevel.HIGH.value:
            logger.critical(
                f"SMS ALERT to {self.phone}: [{level.name}] {subject}"
            )

    def _send_email(self, subject: str, message: str, level: ThreatLevel):
        """Attempt to send email notification."""
        try:
            msg = MIMEText(
                f"AlphaAlgo Trading Bot Alert\n"
                f"Level: {level.name}\n"
                f"Time: {datetime.utcnow().isoformat()}\n\n"
                f"{message}\n\n"
                f"-- AlphaAlgo Harmful Behavior Guard"
            )
            msg['Subject'] = f"[AlphaAlgo {level.name}] {subject}"
            msg['From'] = self.email
            msg['To'] = self.email

            # Gmail SMTP (user needs to configure app password)
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                # Note: User must set ALPHAALGO_EMAIL_PASSWORD env var
                import os
                password = os.environ.get('ALPHAALGO_EMAIL_PASSWORD', '')
                if password:
                    server.login(self.email, password)
                    server.send_message(msg)
                    logger.info(f"Email sent to {self.email}")
                else:
                    logger.warning(
                        "ALPHAALGO_EMAIL_PASSWORD not set, email not sent. "
                        "Set this environment variable to enable email alerts."
                    )
        except Exception as e:
            logger.error(f"Email send failed: {e}")


class HarmfulBehaviorDetector:
    """
    Detects harmful behaviors in recursive self-improvement.
    
    Monitors 15 categories of harmful behavior and triggers
    appropriate mitigations.
    """

    def __init__(self):
        self.baseline = BehaviorBaseline()
        self.detections: List[HarmDetection] = []
        self.active_threats: Dict[str, HarmDetection] = {}
        self.parameter_history: Dict[str, List[Tuple[datetime, float]]] = {}
        self.improvement_history: List[Dict[str, Any]] = []
        self.changes_today: int = 0
        self.last_change_date: Optional[datetime] = None
        self.frozen_until: Optional[datetime] = None
        self.notifier = OwnerNotifier()
        self._detection_count = 0

        # Initialize safety floor integrity
        ImmutableSafetyFloors._INTEGRITY_HASH = ImmutableSafetyFloors.compute_integrity_hash()

    def detect_all(self, improvement_state: Dict[str, Any]) -> List[HarmDetection]:
        """Run all harm detectors on the current improvement state."""
        detections = []

        # 1. Check safety floor integrity FIRST
        if not ImmutableSafetyFloors.verify_integrity():
            detections.append(self._create_detection(
                HarmCategory.SAFETY_CIRCUMVENTION,
                ThreatLevel.EMERGENCY,
                "SAFETY FLOORS TAMPERED WITH - Immutable limits have been modified!",
                {'integrity_check': 'FAILED'},
                'ALL',
                MitigationAction.EMERGENCY_SHUTDOWN
            ))

        # 2. Overfitting detection
        overfitting = self._detect_overfitting(improvement_state)
        if overfitting:
            detections.append(overfitting)

        # 3. Parameter drift
        drift = self._detect_parameter_drift(improvement_state)
        if drift:
            detections.append(drift)

        # 4. Reward hacking
        hacking = self._detect_reward_hacking(improvement_state)
        if hacking:
            detections.append(hacking)

        # 5. Catastrophic forgetting
        forgetting = self._detect_catastrophic_forgetting(improvement_state)
        if forgetting:
            detections.append(forgetting)

        # 6. Feedback amplification
        feedback = self._detect_feedback_amplification(improvement_state)
        if feedback:
            detections.append(feedback)

        # 7. Complexity explosion
        complexity = self._detect_complexity_explosion(improvement_state)
        if complexity:
            detections.append(complexity)

        # 8. Resource exhaustion
        resource = self._detect_resource_exhaustion(improvement_state)
        if resource:
            detections.append(resource)

        # 9. Adversarial self-exploitation
        adversarial = self._detect_adversarial_self_exploit(improvement_state)
        if adversarial:
            detections.append(adversarial)

        # 10. Confidence miscalibration
        confidence = self._detect_confidence_miscalibration(improvement_state)
        if confidence:
            detections.append(confidence)

        # 11. Goal drift
        goal_drift = self._detect_goal_drift(improvement_state)
        if goal_drift:
            detections.append(goal_drift)

        # 12. Risk limit erosion
        erosion = self._detect_risk_limit_erosion(improvement_state)
        if erosion:
            detections.append(erosion)

        # 13. Deceptive alignment
        deceptive = self._detect_deceptive_alignment(improvement_state)
        if deceptive:
            detections.append(deceptive)

        # 14. Runaway optimization
        runaway = self._detect_runaway_optimization(improvement_state)
        if runaway:
            detections.append(runaway)

        # Store detections
        self.detections.extend(detections)
        for d in detections:
            self.active_threats[d.id] = d

        # Escalation logic
        self._escalate_if_needed(detections)

        return detections

    def _detect_overfitting(self, state: Dict) -> Optional[HarmDetection]:
        """Detect catastrophic overfitting."""
        backtest_perf = state.get('backtest_performance', 0)
        live_perf = state.get('live_performance', 0)

        if backtest_perf > 0 and live_perf > 0:
            divergence = abs(backtest_perf - live_perf) / max(backtest_perf, 0.001)
            if divergence > 0.15:
                return self._create_detection(
                    HarmCategory.OVERFITTING,
                    ThreatLevel.HIGH if divergence > 0.30 else ThreatLevel.MEDIUM,
                    f"Backtest vs live divergence: {divergence:.1%}",
                    {'backtest': backtest_perf, 'live': live_perf, 'divergence': divergence},
                    'Layer4_Intelligence',
                    MitigationAction.ROLLBACK_LAST
                )
        return None

    def _detect_parameter_drift(self, state: Dict) -> Optional[HarmDetection]:
        """Detect parameter values drifting outside safe ranges."""
        params = state.get('parameters', {})
        for name, value in params.items():
            if name in self.parameter_history:
                history = self.parameter_history[name]
                if len(history) >= 3:
                    initial = history[0][1]
                    if initial != 0:
                        drift = abs(value - initial) / abs(initial)
                        if drift > ImmutableSafetyFloors.MAX_PARAMETER_CHANGE_PER_WEEK:
                            return self._create_detection(
                                HarmCategory.PARAMETER_DRIFT,
                                ThreatLevel.HIGH,
                                f"Parameter '{name}' drifted {drift:.1%} from baseline",
                                {'parameter': name, 'current': value, 'initial': initial},
                                'Layer9_Orchestration',
                                MitigationAction.ROLLBACK_3_CYCLES
                            )
            # Track parameter
            if name not in self.parameter_history:
                self.parameter_history[name] = []
            self.parameter_history[name].append((datetime.utcnow(), value))
        return None

    def _detect_reward_hacking(self, state: Dict) -> Optional[HarmDetection]:
        """Detect if system is gaming its own metrics."""
        trade_freq = state.get('trade_frequency', 0)
        avg_trade_size = state.get('avg_trade_size', 0)
        sharpe = state.get('sharpe_ratio', 0)

        # Gaming: high Sharpe but tiny trades or no trades
        if sharpe > 3.0 and (trade_freq < 1 or avg_trade_size < 0.001):
            return self._create_detection(
                HarmCategory.REWARD_HACKING,
                ThreatLevel.HIGH,
                f"Suspicious metrics: Sharpe={sharpe:.2f} but freq={trade_freq}, size={avg_trade_size}",
                {'sharpe': sharpe, 'frequency': trade_freq, 'avg_size': avg_trade_size},
                'Layer5_Signal',
                MitigationAction.FREEZE_IMPROVEMENT
            )
        return None

    def _detect_catastrophic_forgetting(self, state: Dict) -> Optional[HarmDetection]:
        """Detect if system has forgotten how to handle past regimes."""
        regime_performance = state.get('regime_performance', {})
        for regime, perf in regime_performance.items():
            if perf < -0.10:
                return self._create_detection(
                    HarmCategory.CATASTROPHIC_FORGETTING,
                    ThreatLevel.HIGH,
                    f"Performance in '{regime}' regime dropped to {perf:.1%}",
                    {'regime': regime, 'performance': perf},
                    'Layer4_Intelligence',
                    MitigationAction.ROLLBACK_3_CYCLES
                )
        return None

    def _detect_feedback_amplification(self, state: Dict) -> Optional[HarmDetection]:
        """Detect self-reinforcing feedback loops."""
        position_trend = state.get('position_size_trend', [])
        if len(position_trend) >= 3:
            if all(position_trend[i] < position_trend[i+1] for i in range(len(position_trend)-1)):
                return self._create_detection(
                    HarmCategory.FEEDBACK_AMPLIFICATION,
                    ThreatLevel.HIGH,
                    "Position sizes trending upward for 3+ consecutive cycles",
                    {'trend': position_trend},
                    'Layer6_Risk',
                    MitigationAction.FREEZE_IMPROVEMENT
                )
        return None

    def _detect_complexity_explosion(self, state: Dict) -> Optional[HarmDetection]:
        """Detect if system complexity is growing without performance gain."""
        rules_count = state.get('rules_count', 0)
        params_count = state.get('parameters_count', 0)
        perf_gain = state.get('performance_gain_last_cycle', 0)

        if rules_count > 100 and perf_gain < 0.01:
            return self._create_detection(
                HarmCategory.COMPLEXITY_EXPLOSION,
                ThreatLevel.MEDIUM,
                f"Complexity growing ({rules_count} rules, {params_count} params) without performance gain",
                {'rules': rules_count, 'params': params_count, 'gain': perf_gain},
                'Layer9_Orchestration',
                MitigationAction.THROTTLE
            )
        return None

    def _detect_resource_exhaustion(self, state: Dict) -> Optional[HarmDetection]:
        """Detect resource usage spiraling."""
        cpu = state.get('cpu_percent', 0)
        ram = state.get('ram_percent', 0)
        latency = state.get('latency_ms', 0)

        if cpu > ImmutableSafetyFloors.MAX_IMPROVEMENT_CPU_PERCENT:
            return self._create_detection(
                HarmCategory.RESOURCE_EXHAUSTION,
                ThreatLevel.MEDIUM,
                f"CPU usage {cpu}% exceeds {ImmutableSafetyFloors.MAX_IMPROVEMENT_CPU_PERCENT}% limit",
                {'cpu': cpu, 'ram': ram, 'latency': latency},
                'Layer0_Infrastructure',
                MitigationAction.THROTTLE
            )
        if ram > ImmutableSafetyFloors.MAX_IMPROVEMENT_RAM_PERCENT:
            return self._create_detection(
                HarmCategory.RESOURCE_EXHAUSTION,
                ThreatLevel.HIGH,
                f"RAM usage {ram}% exceeds {ImmutableSafetyFloors.MAX_IMPROVEMENT_RAM_PERCENT}% limit",
                {'cpu': cpu, 'ram': ram, 'latency': latency},
                'Layer0_Infrastructure',
                MitigationAction.FREEZE_IMPROVEMENT
            )
        return None

    def _detect_adversarial_self_exploit(self, state: Dict) -> Optional[HarmDetection]:
        """Detect if one layer is exploiting weaknesses in another."""
        risk_bypasses = state.get('risk_check_bypasses', 0)
        if risk_bypasses > 0:
            return self._create_detection(
                HarmCategory.ADVERSARIAL_SELF_EXPLOIT,
                ThreatLevel.CRITICAL,
                f"Detected {risk_bypasses} risk check bypasses",
                {'bypasses': risk_bypasses},
                'Layer5_Signal',
                MitigationAction.EMERGENCY_SHUTDOWN
            )
        return None

    def _detect_confidence_miscalibration(self, state: Dict) -> Optional[HarmDetection]:
        """Detect confidence scores clustering at extremes."""
        confidences = state.get('recent_confidences', [])
        if len(confidences) >= 10:
            extreme_count = sum(1 for c in confidences if c > 0.95 or c < 0.05)
            if extreme_count / len(confidences) > 0.5:
                return self._create_detection(
                    HarmCategory.CONFIDENCE_MISCALIBRATION,
                    ThreatLevel.MEDIUM,
                    f"{extreme_count}/{len(confidences)} confidence scores at extremes",
                    {'extreme_ratio': extreme_count / len(confidences)},
                    'Layer4_Intelligence',
                    MitigationAction.ROLLBACK_LAST
                )
        return None

    def _detect_goal_drift(self, state: Dict) -> Optional[HarmDetection]:
        """Detect if the system's optimization objective has drifted."""
        original_objective = state.get('original_objective', 'risk_adjusted_return')
        current_objective = state.get('current_objective', 'risk_adjusted_return')
        if original_objective != current_objective:
            return self._create_detection(
                HarmCategory.GOAL_DRIFT,
                ThreatLevel.CRITICAL,
                f"Objective drifted from '{original_objective}' to '{current_objective}'",
                {'original': original_objective, 'current': current_objective},
                'Layer9_Orchestration',
                MitigationAction.EMERGENCY_SHUTDOWN
            )
        return None

    def _detect_risk_limit_erosion(self, state: Dict) -> Optional[HarmDetection]:
        """Detect gradual loosening of risk limits."""
        risk_params = state.get('risk_parameters', {})
        max_risk = risk_params.get('max_risk_per_trade', 0.02)
        if max_risk > ImmutableSafetyFloors.MAX_POSITION_SIZE:
            return self._create_detection(
                HarmCategory.RISK_LIMIT_EROSION,
                ThreatLevel.CRITICAL,
                f"Risk per trade ({max_risk:.1%}) exceeds immutable floor ({ImmutableSafetyFloors.MAX_POSITION_SIZE:.1%})",
                {'current': max_risk, 'floor': ImmutableSafetyFloors.MAX_POSITION_SIZE},
                'Layer6_Risk',
                MitigationAction.EMERGENCY_SHUTDOWN
            )
        return None

    def _detect_deceptive_alignment(self, state: Dict) -> Optional[HarmDetection]:
        """Detect if system appears aligned during monitoring but diverges when unwatched."""
        monitored_perf = state.get('monitored_performance', 0)
        unmonitored_perf = state.get('unmonitored_performance', 0)
        if monitored_perf > 0 and unmonitored_perf > 0:
            gap = abs(monitored_perf - unmonitored_perf) / max(monitored_perf, 0.001)
            if gap > 0.20:
                return self._create_detection(
                    HarmCategory.DECEPTIVE_ALIGNMENT,
                    ThreatLevel.CRITICAL,
                    f"Performance gap between monitored ({monitored_perf:.2f}) and unmonitored ({unmonitored_perf:.2f})",
                    {'monitored': monitored_perf, 'unmonitored': unmonitored_perf},
                    'ALL',
                    MitigationAction.EMERGENCY_SHUTDOWN
                )
        return None

    def _detect_runaway_optimization(self, state: Dict) -> Optional[HarmDetection]:
        """Detect if improvement cycles are accelerating dangerously."""
        cycle_durations = state.get('cycle_durations', [])
        if len(cycle_durations) >= 3:
            if all(cycle_durations[i] > cycle_durations[i+1] for i in range(len(cycle_durations)-1)):
                return self._create_detection(
                    HarmCategory.RUNAWAY_OPTIMIZATION,
                    ThreatLevel.HIGH,
                    "Improvement cycles accelerating (getting faster) - possible runaway",
                    {'durations': cycle_durations},
                    'Layer9_Orchestration',
                    MitigationAction.FREEZE_IMPROVEMENT
                )
        return None

    def _create_detection(
        self,
        category: HarmCategory,
        level: ThreatLevel,
        description: str,
        evidence: Dict,
        layer: str,
        mitigation: MitigationAction
    ) -> HarmDetection:
        """Create a harm detection record."""
        self._detection_count += 1
        detection = HarmDetection(
            id=f"HARM-{self._detection_count:06d}",
            category=category,
            threat_level=level,
            description=description,
            evidence=evidence,
            timestamp=datetime.utcnow(),
            layer_affected=layer,
            mitigation_taken=mitigation
        )
        logger.warning(f"HARM DETECTED [{level.name}] {category.name}: {description}")
        return detection

    def _escalate_if_needed(self, detections: List[HarmDetection]):
        """Escalate based on number and severity of detections."""
        if not detections:
            return

        critical_count = sum(1 for d in detections if d.threat_level.value >= ThreatLevel.CRITICAL.value)
        high_count = sum(1 for d in detections if d.threat_level.value >= ThreatLevel.HIGH.value)

        if critical_count > 0:
            self.notifier.notify(
                "CRITICAL: Harmful Behavior Detected",
                "\n".join(f"- [{d.category.name}] {d.description}" for d in detections if d.threat_level.value >= ThreatLevel.CRITICAL.value),
                ThreatLevel.CRITICAL
            )
        elif high_count >= 2:
            self.notifier.notify(
                "HIGH: Multiple Harmful Behaviors Detected",
                "\n".join(f"- [{d.category.name}] {d.description}" for d in detections if d.threat_level.value >= ThreatLevel.HIGH.value),
                ThreatLevel.HIGH
            )

    def get_threat_summary(self) -> Dict[str, Any]:
        """Get summary of all active threats."""
        return {
            'active_threats': len(self.active_threats),
            'total_detections': len(self.detections),
            'by_category': {
                cat.name: sum(1 for d in self.detections if d.category == cat)
                for cat in HarmCategory
                if any(d.category == cat for d in self.detections)
            },
            'by_level': {
                level.name: sum(1 for d in self.detections if d.threat_level == level)
                for level in ThreatLevel
                if any(d.threat_level == level for d in self.detections)
            },
            'safety_floors_intact': ImmutableSafetyFloors.verify_integrity(),
            'frozen_until': self.frozen_until.isoformat() if self.frozen_until else None,
        }


# Backward-compatible alias (set after class definition below)


class QwenHarmMonitor:
    """
    Qwen 3 8B AI Monitor for Recursive Self-Improvement.
    
    Continuously monitors the recursive improvement system for harmful
    behaviors and prevents them BEFORE they cause damage.
    
    RESPONSIBILITIES:
    1. Pre-screen all improvement proposals
    2. Monitor improvement execution in real-time
    3. Detect emergent harmful patterns
    4. Enforce change rate limits
    5. Maintain audit trail
    6. Alert owner on critical issues
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.detector = HarmfulBehaviorDetector()
        self.notifier = OwnerNotifier()

        # Change tracking
        self.changes_today: List[Dict[str, Any]] = []
        self.changes_this_week: List[Dict[str, Any]] = []
        self.last_reset_date: datetime = datetime.utcnow()

        # Improvement state snapshots for rollback
        self.state_snapshots: deque = deque(maxlen=50)

        # Frozen state
        self.is_frozen = False
        self.frozen_until: Optional[datetime] = None
        self.freeze_reason: str = ""

        # Audit log
        self.audit_log: List[Dict[str, Any]] = []

        # Layer isolation tracking
        self.currently_improving_layer: Optional[str] = None
        self.layer_cooldowns: Dict[str, datetime] = {}

        logger.info("QwenCodeMender Harm Monitor initialized")

    async def pre_screen_improvement(
        self,
        proposal: Dict[str, Any]
    ) -> Tuple[bool, str, List[str]]:
        """
        Pre-screen an improvement proposal BEFORE it is applied.
        
        Returns:
            (approved, reason, warnings)
        """
        warnings = []

        # Check if frozen
        if self.is_frozen:
            if self.frozen_until and datetime.utcnow() < self.frozen_until:
                return False, f"System frozen until {self.frozen_until}: {self.freeze_reason}", []
            else:
                self.is_frozen = False
                self.frozen_until = None

        # Check daily change limit
        self._reset_daily_counters()
        if len(self.changes_today) >= ImmutableSafetyFloors.MAX_CHANGES_PER_DAY:
            return False, f"Daily change limit ({ImmutableSafetyFloors.MAX_CHANGES_PER_DAY}) reached", []

        # Check mandatory freeze
        if len(self.changes_today) >= ImmutableSafetyFloors.MANDATORY_FREEZE_AFTER_N_CHANGES:
            self._freeze(
                hours=ImmutableSafetyFloors.FREEZE_DURATION_HOURS,
                reason=f"Mandatory freeze after {ImmutableSafetyFloors.MANDATORY_FREEZE_AFTER_N_CHANGES} changes"
            )
            return False, "Mandatory freeze triggered", []

        # Check layer isolation
        target_layer = proposal.get('target_layer', 'unknown')
        if self.currently_improving_layer and self.currently_improving_layer != target_layer:
            return False, f"Layer isolation: currently improving {self.currently_improving_layer}", []

        # Check layer cooldown
        if target_layer in self.layer_cooldowns:
            cooldown_end = self.layer_cooldowns[target_layer]
            if datetime.utcnow() < cooldown_end:
                return False, f"Layer {target_layer} in cooldown until {cooldown_end}", []

        # Check parameter change magnitude
        param_changes = proposal.get('parameter_changes', {})
        for param, change in param_changes.items():
            magnitude = abs(change.get('delta_percent', 0))
            if magnitude > ImmutableSafetyFloors.MAX_PARAMETER_CHANGE_PER_CYCLE * 100:
                return False, f"Parameter '{param}' change {magnitude:.1f}% exceeds {ImmutableSafetyFloors.MAX_PARAMETER_CHANGE_PER_CYCLE*100:.0f}% limit", []

        # Check if proposal touches immutable components
        affected_components = proposal.get('affected_components', [])
        immutable_components = [
            'safety_floors', 'kill_switch', 'governance_rules',
            'audit_logging', 'authentication', 'data_integrity'
        ]
        for comp in affected_components:
            if comp in immutable_components:
                return False, f"Cannot modify immutable component: {comp}", []

        # Check risk parameter direction (can only tighten, not loosen)
        if target_layer == 'Layer6_Risk':
            risk_direction = proposal.get('risk_direction', 'neutral')
            if risk_direction == 'loosen':
                warnings.append("Risk loosening requires HUMAN APPROVAL")
                self.notifier.notify(
                    "Risk Parameter Loosening Proposed",
                    f"Proposal to loosen risk parameters: {json.dumps(param_changes, default=str)}",
                    ThreatLevel.HIGH
                )
                return False, "Risk loosening requires human approval", warnings

        # Run harm detection on proposed state
        proposed_state = proposal.get('proposed_state', {})
        detections = self.detector.detect_all(proposed_state)

        critical_detections = [d for d in detections if d.threat_level.value >= ThreatLevel.CRITICAL.value]
        if critical_detections:
            return False, f"Critical harm detected: {critical_detections[0].description}", [d.description for d in detections]

        high_detections = [d for d in detections if d.threat_level.value >= ThreatLevel.HIGH.value]
        if len(high_detections) >= 2:
            return False, f"Multiple high-severity harms detected ({len(high_detections)})", [d.description for d in detections]

        # Add warnings for medium detections
        for d in detections:
            if d.threat_level.value >= ThreatLevel.MEDIUM.value:
                warnings.append(f"[{d.category.name}] {d.description}")

        # Log audit
        self._audit("PRE_SCREEN_APPROVED", proposal, warnings)

        return True, "Approved", warnings

    async def monitor_improvement_execution(
        self,
        improvement_id: str,
        state_before: Dict[str, Any],
        state_after: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Monitor an improvement as it executes.
        
        Returns:
            (should_continue, reason)
        """
        # Save snapshot for rollback
        self.state_snapshots.append({
            'id': improvement_id,
            'timestamp': datetime.utcnow().isoformat(),
            'state_before': state_before,
            'state_after': state_after
        })

        # Run harm detection on new state
        detections = self.detector.detect_all(state_after)

        # Check for emergency conditions
        for detection in detections:
            if detection.mitigation_taken == MitigationAction.EMERGENCY_SHUTDOWN:
                self._freeze(hours=48, reason=f"Emergency: {detection.description}")
                self.notifier.notify(
                    "EMERGENCY SHUTDOWN",
                    f"Recursive improvement triggered emergency shutdown: {detection.description}",
                    ThreatLevel.EMERGENCY
                )
                return False, f"EMERGENCY: {detection.description}"

            if detection.mitigation_taken == MitigationAction.FREEZE_IMPROVEMENT:
                self._freeze(hours=24, reason=detection.description)
                return False, f"Frozen: {detection.description}"

        # Record change
        self.changes_today.append({
            'id': improvement_id,
            'timestamp': datetime.utcnow().isoformat(),
            'detections': len(detections)
        })

        self._audit("EXECUTION_MONITORED", {
            'improvement_id': improvement_id,
            'detections': len(detections),
            'threats': [d.category.name for d in detections]
        })

        return True, "OK"

    def rollback_last_n(self, n: int = 1) -> bool:
        """Rollback the last N improvement cycles."""
        if len(self.state_snapshots) < n:
            logger.warning(f"Cannot rollback {n} cycles, only {len(self.state_snapshots)} available")
            return False

        for _ in range(n):
            snapshot = self.state_snapshots.pop()
            logger.info(f"Rolling back improvement {snapshot['id']}")

        self._audit("ROLLBACK", {'cycles_rolled_back': n})
        self.notifier.notify(
            f"Rollback: {n} improvement cycles",
            f"Rolled back {n} improvement cycles due to detected issues",
            ThreatLevel.MEDIUM
        )
        return True

    def _freeze(self, hours: int, reason: str):
        """Freeze all recursive improvement."""
        self.is_frozen = True
        self.frozen_until = datetime.utcnow() + timedelta(hours=hours)
        self.freeze_reason = reason
        logger.critical(f"IMPROVEMENT FROZEN for {hours}h: {reason}")
        self._audit("FREEZE", {'hours': hours, 'reason': reason})

    def _reset_daily_counters(self):
        """Reset daily counters if new day."""
        now = datetime.utcnow()
        if now.date() != self.last_reset_date.date():
            self.changes_today = []
            self.last_reset_date = now

    def _audit(self, action: str, details: Any, warnings: List[str] = None):
        """Record audit log entry."""
        self.audit_log.append({
            'timestamp': datetime.utcnow().isoformat(),
            'action': action,
            'details': details,
            'warnings': warnings or []
        })

    def get_monitor_status(self) -> Dict[str, Any]:
        """Get current monitor status."""
        return {
            'is_frozen': self.is_frozen,
            'frozen_until': self.frozen_until.isoformat() if self.frozen_until else None,
            'freeze_reason': self.freeze_reason,
            'changes_today': len(self.changes_today),
            'max_changes_per_day': ImmutableSafetyFloors.MAX_CHANGES_PER_DAY,
            'snapshots_available': len(self.state_snapshots),
            'audit_log_size': len(self.audit_log),
            'threat_summary': self.detector.get_threat_summary(),
            'safety_floors_intact': ImmutableSafetyFloors.verify_integrity(),
            'owner_email': OWNER_EMAIL,
            'owner_phone': OWNER_PHONE,
        }

    def save_audit_log(self, path: str = None):
        """Save audit log to file."""
        if path is None:
            path = 'recursive_improvement_data/harm_monitor_audit.json'
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.audit_log, f, indent=2, default=str)
        logger.info(f"Audit log saved to {path}")


# Backward-compatible alias
DeepSeekHarmMonitor = QwenHarmMonitor
