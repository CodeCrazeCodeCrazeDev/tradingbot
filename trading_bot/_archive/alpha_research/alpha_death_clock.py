"""
Alpha Death Clock Module
========================
Every deployed alpha has:
- A decay clock
- Live performance tracking
- Auto-retirement on decay or regime mismatch
- Automatic replacement with next best feature

Author: AlphaAlgo Research Team
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd

from .rdaos_core import (
    AlphaDeathClock,
    FeatureFamily,
    HARD_LIMITS,
    ProductionStatus,
    RegimeType,
    generate_id
)

logger = logging.getLogger(__name__)


class DecayStage(Enum):
    """Stages of alpha decay"""
    HEALTHY = "healthy"
    EARLY_DECAY = "early_decay"
    MODERATE_DECAY = "moderate_decay"
    SEVERE_DECAY = "severe_decay"
    TERMINAL = "terminal"
    RETIRED = "retired"


class RetirementReason(Enum):
    """Reasons for alpha retirement"""
    SHARPE_DECAY = "sharpe_decay"
    CAPACITY_EXHAUSTION = "capacity_exhaustion"
    REGIME_MISMATCH = "regime_mismatch"
    CORRELATION_INCREASE = "correlation_increase"
    MANUAL = "manual"
    REPLACED = "replaced"
    MAX_AGE = "max_age"


@dataclass
class DecayMetrics:
    """Metrics for tracking decay"""
    initial_sharpe: float = 0.0
    current_sharpe: float = 0.0
    sharpe_decay_pct: float = 0.0
    
    initial_capacity: float = 0.0
    current_capacity: float = 0.0
    capacity_decay_pct: float = 0.0
    
    days_deployed: int = 0
    expected_half_life_days: int = 90
    
    decay_rate_per_day: float = 0.0
    projected_zero_sharpe_date: Optional[datetime] = None
    
    def compute_decay(self):
        """Compute decay metrics"""
        if self.initial_sharpe > 0:
            self.sharpe_decay_pct = (
                (self.initial_sharpe - self.current_sharpe) / self.initial_sharpe * 100
            )
        
        if self.initial_capacity > 0:
            self.capacity_decay_pct = (
                (self.initial_capacity - self.current_capacity) / self.initial_capacity * 100
            )
        
        if self.days_deployed > 0 and self.initial_sharpe > 0:
            self.decay_rate_per_day = self.sharpe_decay_pct / self.days_deployed
            
            if self.decay_rate_per_day > 0:
                days_to_zero = (100 - self.sharpe_decay_pct) / self.decay_rate_per_day
                self.projected_zero_sharpe_date = (
                    datetime.utcnow() + timedelta(days=days_to_zero)
                )


@dataclass
class DecayAlert:
    """Alert for decay detection"""
    alert_id: str
    family_id: str
    
    stage: DecayStage
    severity: str  # low, medium, high, critical
    
    message: str
    metrics: DecayMetrics
    
    recommended_action: str
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            "alert_id": self.alert_id,
            "family_id": self.family_id,
            "stage": self.stage.value,
            "severity": self.severity,
            "message": self.message,
            "recommended_action": self.recommended_action,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class RetirementRecord:
    """Record of alpha retirement"""
    family_id: str
    reason: RetirementReason
    
    final_metrics: DecayMetrics
    
    replacement_family_id: Optional[str] = None
    
    retired_at: datetime = field(default_factory=datetime.utcnow)
    
    lessons_learned: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "family_id": self.family_id,
            "reason": self.reason.value,
            "replacement_family_id": self.replacement_family_id,
            "retired_at": self.retired_at.isoformat(),
            "lessons_learned": self.lessons_learned
        }


class DecayDetector:
    """
    Detect alpha decay patterns.
    
    Monitors:
    - Sharpe ratio decay
    - Capacity exhaustion
    - Return degradation
    - Signal strength weakening
    """
    
    # Decay thresholds
    EARLY_DECAY_THRESHOLD = 20.0  # 20% Sharpe decay
    MODERATE_DECAY_THRESHOLD = 40.0  # 40% Sharpe decay
    SEVERE_DECAY_THRESHOLD = 60.0  # 60% Sharpe decay
    TERMINAL_THRESHOLD = 80.0  # 80% Sharpe decay
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Custom thresholds
        self.early_threshold = self.config.get("early_decay_threshold", self.EARLY_DECAY_THRESHOLD)
        self.moderate_threshold = self.config.get("moderate_decay_threshold", self.MODERATE_DECAY_THRESHOLD)
        self.severe_threshold = self.config.get("severe_decay_threshold", self.SEVERE_DECAY_THRESHOLD)
        self.terminal_threshold = self.config.get("terminal_threshold", self.TERMINAL_THRESHOLD)
    
    def detect(self, metrics: DecayMetrics) -> DecayStage:
        """Detect current decay stage"""
        decay_pct = metrics.sharpe_decay_pct
        
        if decay_pct >= self.terminal_threshold:
            return DecayStage.TERMINAL
        elif decay_pct >= self.severe_threshold:
            return DecayStage.SEVERE_DECAY
        elif decay_pct >= self.moderate_threshold:
            return DecayStage.MODERATE_DECAY
        elif decay_pct >= self.early_threshold:
            return DecayStage.EARLY_DECAY
        else:
            return DecayStage.HEALTHY
    
    def compute_decay_velocity(
        self,
        sharpe_history: List[Tuple[datetime, float]]
    ) -> float:
        """Compute rate of decay from history"""
        if len(sharpe_history) < 2:
            return 0.0
        
        # Sort by date
        sorted_history = sorted(sharpe_history, key=lambda x: x[0])
        
        # Compute daily decay rates
        decay_rates = []
        for i in range(1, len(sorted_history)):
            prev_date, prev_sharpe = sorted_history[i-1]
            curr_date, curr_sharpe = sorted_history[i]
            
            days = (curr_date - prev_date).days
            if days > 0 and prev_sharpe > 0:
                daily_decay = (prev_sharpe - curr_sharpe) / prev_sharpe / days
                decay_rates.append(daily_decay)
        
        if decay_rates:
            return np.mean(decay_rates) * 100  # As percentage per day
        return 0.0


class RegimeMismatchDetector:
    """
    Detect regime mismatch for deployed alphas.
    
    Monitors:
    - Current regime vs designed regime
    - Performance in current regime
    - Regime transition signals
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Performance threshold for mismatch
        self.mismatch_sharpe_threshold = self.config.get("mismatch_sharpe_threshold", 0.0)
    
    def detect_mismatch(
        self,
        family: FeatureFamily,
        current_regime: RegimeType,
        current_sharpe: float
    ) -> Tuple[bool, str]:
        """Detect if there's a regime mismatch"""
        
        # Check if current regime is in designed regimes
        if current_regime not in family.regime_conditions:
            if current_sharpe < self.mismatch_sharpe_threshold:
                return True, f"Operating in {current_regime.value} but designed for {[r.value for r in family.regime_conditions]}"
        
        # Check for opposite regimes
        opposite_regimes = {
            RegimeType.TRENDING_UP: RegimeType.TRENDING_DOWN,
            RegimeType.TRENDING_DOWN: RegimeType.TRENDING_UP,
            RegimeType.HIGH_VOLATILITY: RegimeType.LOW_VOLATILITY,
            RegimeType.LOW_VOLATILITY: RegimeType.HIGH_VOLATILITY
        }
        
        if current_regime in opposite_regimes:
            opposite = opposite_regimes[current_regime]
            if opposite in family.regime_conditions and current_regime not in family.regime_conditions:
                return True, f"Regime {current_regime.value} is opposite to designed regime {opposite.value}"
        
        return False, ""


class ReplacementSelector:
    """
    Select replacement for retiring alpha.
    
    Criteria:
    - Best performing candidate
    - Low correlation with existing
    - Suitable for current regime
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
    
    def select_replacement(
        self,
        retiring_family: FeatureFamily,
        candidates: List[FeatureFamily],
        current_regime: RegimeType,
        existing_family_ids: List[str]
    ) -> Optional[FeatureFamily]:
        """Select best replacement"""
        
        if not candidates:
            return None
        
        # Filter candidates
        suitable = []
        for candidate in candidates:
            # Must not already be deployed
            if candidate.family_id in existing_family_ids:
                continue
            
            # Must be suitable for current regime
            if current_regime in candidate.regime_conditions:
                suitable.append(candidate)
        
        if not suitable:
            # Fallback: any candidate not deployed
            suitable = [c for c in candidates if c.family_id not in existing_family_ids]
        
        if not suitable:
            return None
        
        # Sort by expected performance (capacity as proxy)
        suitable.sort(key=lambda x: x.capacity_limit_usd, reverse=True)
        
        return suitable[0]


class AlphaDeathClockManager:
    """
    Manage death clocks for all deployed alphas.
    
    Coordinates:
    - Decay detection
    - Regime mismatch detection
    - Auto-retirement
    - Replacement selection
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Initialize components
        self.decay_detector = DecayDetector(config)
        self.regime_detector = RegimeMismatchDetector(config)
        self.replacement_selector = ReplacementSelector(config)
        
        # State
        self.death_clocks: Dict[str, AlphaDeathClock] = {}
        self.decay_metrics: Dict[str, DecayMetrics] = {}
        self.sharpe_history: Dict[str, List[Tuple[datetime, float]]] = {}
        
        # Alerts
        self.active_alerts: List[DecayAlert] = []
        
        # Retirement records
        self.retirement_records: List[RetirementRecord] = []
        
        # Thresholds
        self.auto_retire_sharpe = self.config.get(
            "auto_retire_sharpe",
            HARD_LIMITS.AUTO_RETIRE_SHARPE_THRESHOLD
        )
        self.max_decay_rate = self.config.get(
            "max_decay_rate",
            HARD_LIMITS.MAX_SHARPE_DECAY_RATE
        )
        
        logger.info("Alpha Death Clock Manager initialized")
    
    def create_death_clock(
        self,
        family: FeatureFamily,
        initial_sharpe: float,
        expected_decay_days: int
    ) -> AlphaDeathClock:
        """Create death clock for a newly deployed alpha"""
        
        clock = AlphaDeathClock(
            family_id=family.family_id,
            deployment_date=datetime.utcnow(),
            expected_decay_date=datetime.utcnow() + timedelta(days=expected_decay_days),
            initial_sharpe=initial_sharpe,
            current_sharpe=initial_sharpe,
            initial_capacity=family.capacity_limit_usd,
            current_capacity=family.capacity_limit_usd,
            days_until_expected_decay=expected_decay_days
        )
        
        self.death_clocks[family.family_id] = clock
        
        # Initialize metrics
        self.decay_metrics[family.family_id] = DecayMetrics(
            initial_sharpe=initial_sharpe,
            current_sharpe=initial_sharpe,
            initial_capacity=family.capacity_limit_usd,
            current_capacity=family.capacity_limit_usd,
            expected_half_life_days=expected_decay_days // 2
        )
        
        # Initialize history
        self.sharpe_history[family.family_id] = [(datetime.utcnow(), initial_sharpe)]
        
        logger.info(
            f"Created death clock for {family.family_id}: "
            f"expected decay in {expected_decay_days} days"
        )
        
        return clock
    
    def update(
        self,
        family_id: str,
        current_sharpe: float,
        current_capacity: Optional[float] = None
    ) -> Optional[DecayAlert]:
        """Update death clock with current metrics"""
        
        if family_id not in self.death_clocks:
            return None
        
        clock = self.death_clocks[family_id]
        metrics = self.decay_metrics[family_id]
        
        # Update clock
        clock.current_sharpe = current_sharpe
        clock.days_deployed = (datetime.utcnow() - clock.deployment_date).days
        clock.days_until_expected_decay = max(
            0,
            (clock.expected_decay_date - datetime.utcnow()).days
        )
        
        if current_capacity is not None:
            clock.current_capacity = current_capacity
            metrics.current_capacity = current_capacity
        
        # Update metrics
        metrics.current_sharpe = current_sharpe
        metrics.days_deployed = clock.days_deployed
        metrics.compute_decay()
        
        # Update history
        self.sharpe_history[family_id].append((datetime.utcnow(), current_sharpe))
        
        # Compute decay velocity
        decay_velocity = self.decay_detector.compute_decay_velocity(
            self.sharpe_history[family_id]
        )
        metrics.decay_rate_per_day = decay_velocity
        clock.sharpe_decay_rate = decay_velocity / 100  # Convert from percentage
        
        # Detect decay stage
        stage = self.decay_detector.detect(metrics)
        
        # Check for decay detection
        if stage in [DecayStage.MODERATE_DECAY, DecayStage.SEVERE_DECAY, DecayStage.TERMINAL]:
            if not clock.decay_detected:
                clock.decay_detected = True
                clock.decay_detection_date = datetime.utcnow()
        
        # Generate alert if needed
        alert = self._generate_alert(family_id, stage, metrics)
        
        return alert
    
    def _generate_alert(
        self,
        family_id: str,
        stage: DecayStage,
        metrics: DecayMetrics
    ) -> Optional[DecayAlert]:
        """Generate decay alert if needed"""
        
        if stage == DecayStage.HEALTHY:
            return None
        
        # Determine severity
        severity_map = {
            DecayStage.EARLY_DECAY: "low",
            DecayStage.MODERATE_DECAY: "medium",
            DecayStage.SEVERE_DECAY: "high",
            DecayStage.TERMINAL: "critical"
        }
        severity = severity_map.get(stage, "low")
        
        # Generate message
        message = f"Alpha {family_id} showing {stage.value}: Sharpe decay {metrics.sharpe_decay_pct:.1f}%"
        
        # Recommend action
        action_map = {
            DecayStage.EARLY_DECAY: "Monitor closely, consider reducing allocation",
            DecayStage.MODERATE_DECAY: "Reduce allocation by 50%, prepare replacement",
            DecayStage.SEVERE_DECAY: "Reduce allocation to minimum, activate replacement",
            DecayStage.TERMINAL: "Retire immediately, deploy replacement"
        }
        action = action_map.get(stage, "Monitor")
        
        alert = DecayAlert(
            alert_id=generate_id("alert"),
            family_id=family_id,
            stage=stage,
            severity=severity,
            message=message,
            metrics=metrics,
            recommended_action=action
        )
        
        self.active_alerts.append(alert)
        
        logger.warning(f"Decay alert: {message}")
        
        return alert
    
    def check_auto_retirement(
        self,
        family_id: str,
        current_regime: Optional[RegimeType] = None,
        family: Optional[FeatureFamily] = None
    ) -> Tuple[bool, Optional[RetirementReason]]:
        """Check if alpha should be auto-retired"""
        
        if family_id not in self.death_clocks:
            return False, None
        
        clock = self.death_clocks[family_id]
        metrics = self.decay_metrics[family_id]
        
        # Check Sharpe threshold
        if clock.current_sharpe < self.auto_retire_sharpe:
            return True, RetirementReason.SHARPE_DECAY
        
        # Check decay rate
        if clock.sharpe_decay_rate > self.max_decay_rate:
            return True, RetirementReason.SHARPE_DECAY
        
        # Check regime mismatch
        if current_regime and family:
            is_mismatch, _ = self.regime_detector.detect_mismatch(
                family,
                current_regime,
                clock.current_sharpe
            )
            if is_mismatch and clock.current_sharpe < 0:
                return True, RetirementReason.REGIME_MISMATCH
        
        # Check capacity exhaustion
        if metrics.capacity_decay_pct > 80:
            return True, RetirementReason.CAPACITY_EXHAUSTION
        
        return False, None
    
    def retire(
        self,
        family_id: str,
        reason: RetirementReason,
        replacement_id: Optional[str] = None
    ) -> RetirementRecord:
        """Retire an alpha"""
        
        metrics = self.decay_metrics.get(family_id, DecayMetrics())
        
        # Generate lessons learned
        lessons = self._extract_lessons(family_id, reason, metrics)
        
        record = RetirementRecord(
            family_id=family_id,
            reason=reason,
            final_metrics=metrics,
            replacement_family_id=replacement_id,
            lessons_learned=lessons
        )
        
        self.retirement_records.append(record)
        
        # Update death clock
        if family_id in self.death_clocks:
            clock = self.death_clocks[family_id]
            clock.auto_retirement_triggered = True
            clock.retirement_date = datetime.utcnow()
            clock.retirement_reason = reason.value
            clock.replacement_family_id = replacement_id
        
        logger.info(
            f"Retired alpha {family_id}: {reason.value}, "
            f"replacement: {replacement_id}"
        )
        
        return record
    
    def _extract_lessons(
        self,
        family_id: str,
        reason: RetirementReason,
        metrics: DecayMetrics
    ) -> List[str]:
        """Extract lessons from retirement"""
        lessons = []
        
        if reason == RetirementReason.SHARPE_DECAY:
            lessons.append(
                f"Alpha decayed {metrics.sharpe_decay_pct:.1f}% over {metrics.days_deployed} days"
            )
            if metrics.decay_rate_per_day > 0:
                lessons.append(
                    f"Decay rate was {metrics.decay_rate_per_day:.2f}% per day"
                )
        
        elif reason == RetirementReason.REGIME_MISMATCH:
            lessons.append("Alpha failed to adapt to regime change")
        
        elif reason == RetirementReason.CAPACITY_EXHAUSTION:
            lessons.append(
                f"Capacity reduced by {metrics.capacity_decay_pct:.1f}%"
            )
        
        return lessons
    
    def select_replacement(
        self,
        retiring_family: FeatureFamily,
        candidates: List[FeatureFamily],
        current_regime: RegimeType,
        existing_family_ids: List[str]
    ) -> Optional[FeatureFamily]:
        """Select replacement for retiring alpha"""
        return self.replacement_selector.select_replacement(
            retiring_family,
            candidates,
            current_regime,
            existing_family_ids
        )
    
    def get_death_clock(self, family_id: str) -> Optional[AlphaDeathClock]:
        """Get death clock for a family"""
        return self.death_clocks.get(family_id)
    
    def get_decay_metrics(self, family_id: str) -> Optional[DecayMetrics]:
        """Get decay metrics for a family"""
        return self.decay_metrics.get(family_id)
    
    def get_active_alerts(self) -> List[DecayAlert]:
        """Get all active alerts"""
        return self.active_alerts
    
    def clear_alert(self, alert_id: str):
        """Clear an alert"""
        self.active_alerts = [a for a in self.active_alerts if a.alert_id != alert_id]
    
    def get_retirement_history(self) -> List[RetirementRecord]:
        """Get retirement history"""
        return self.retirement_records
    
    def get_alphas_near_death(self, days_threshold: int = 30) -> List[str]:
        """Get alphas near expected decay date"""
        near_death = []
        
        for family_id, clock in self.death_clocks.items():
            if clock.days_until_expected_decay <= days_threshold:
                near_death.append(family_id)
        
        return near_death


def create_death_clock_manager(config: Optional[Dict] = None) -> AlphaDeathClockManager:
    """Factory function to create death clock manager"""
    return AlphaDeathClockManager(config)
