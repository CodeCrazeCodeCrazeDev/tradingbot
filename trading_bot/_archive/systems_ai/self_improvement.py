"""
Self-Improvement Loop
=====================
Feedback loop for continuous system improvement.

LOOP STAGES:
1. OUTCOME LABELING: Tag every trade with result
2. DRIFT DETECTION: Detect distribution shifts
3. DECAY DETECTION: Detect performance degradation
4. RETRAINING TRIGGER: Decide when to retrain
5. VALIDATION GATE: Validate new model
6. DEPLOYMENT GATE: Deploy with approval

ALL IMPROVEMENTS MUST BE:
- Measured (quantified impact)
- Reversible (rollback available)
- Auditable (full trace)

DRIFT TYPES:
- Data drift: Input distribution changes
- Concept drift: Relationship between inputs and outputs changes
- Label drift: Target distribution changes

DECAY DETECTION:
- Rolling performance metrics
- Comparison to baseline
- Statistical significance testing

RETRAINING TRIGGERS:
- Performance below threshold
- Drift detected
- Scheduled (time-based)
- Manual request

VALIDATION REQUIREMENTS:
- Out-of-sample performance
- Regime robustness
- Stress testing
- Shadow testing

DEPLOYMENT REQUIREMENTS:
- Human approval (G0)
- Canary deployment
- Rollback plan
- Monitoring setup
"""

import hashlib
import json
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Callable, Tuple
from threading import RLock
import statistics

logger = logging.getLogger(__name__)


class DriftType(Enum):
    """Types of drift."""
    DATA_DRIFT = "data_drift"
    CONCEPT_DRIFT = "concept_drift"
    LABEL_DRIFT = "label_drift"
    PERFORMANCE_DRIFT = "performance_drift"


class DriftSeverity(Enum):
    """Severity of detected drift."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TriggerType(Enum):
    """Types of retraining triggers."""
    PERFORMANCE_DECAY = "performance_decay"
    DRIFT_DETECTED = "drift_detected"
    SCHEDULED = "scheduled"
    MANUAL = "manual"
    ANOMALY_DETECTED = "anomaly_detected"


class ImprovementStatus(Enum):
    """Status of improvement cycle."""
    PROPOSED = "proposed"
    VALIDATING = "validating"
    VALIDATED = "validated"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    DEPLOYING = "deploying"
    DEPLOYED = "deployed"
    ROLLED_BACK = "rolled_back"
    REJECTED = "rejected"


@dataclass
class OutcomeLabel:
    """Label for a trade outcome."""
    signal_id: str
    timestamp: datetime
    
    # Outcome
    direction_correct: bool
    pnl: float
    pnl_percent: float
    
    # Context
    regime_id: str
    volatility: float
    liquidity: float
    
    # Attribution
    model_id: str
    model_version: str
    feature_hash: str
    
    # Quality
    slippage: float
    execution_quality: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "timestamp": self.timestamp.isoformat(),
            "direction_correct": self.direction_correct,
            "pnl": self.pnl,
            "pnl_percent": self.pnl_percent,
            "regime_id": self.regime_id,
            "volatility": self.volatility,
            "liquidity": self.liquidity,
            "model_id": self.model_id,
            "model_version": self.model_version,
            "feature_hash": self.feature_hash,
            "slippage": self.slippage,
            "execution_quality": self.execution_quality,
        }


@dataclass
class DriftDetection:
    """Result of drift detection."""
    detection_id: str
    timestamp: datetime
    drift_type: DriftType
    severity: DriftSeverity
    
    # Metrics
    drift_score: float
    p_value: Optional[float]
    baseline_metric: float
    current_metric: float
    
    # Details
    affected_features: List[str]
    details: Dict[str, Any]
    
    # Recommendation
    action_recommended: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "detection_id": self.detection_id,
            "timestamp": self.timestamp.isoformat(),
            "drift_type": self.drift_type.value,
            "severity": self.severity.value,
            "drift_score": self.drift_score,
            "p_value": self.p_value,
            "baseline_metric": self.baseline_metric,
            "current_metric": self.current_metric,
            "affected_features": self.affected_features,
            "details": self.details,
            "action_recommended": self.action_recommended,
        }


@dataclass
class PerformanceSnapshot:
    """Snapshot of performance metrics."""
    snapshot_id: str
    timestamp: datetime
    period_start: datetime
    period_end: datetime
    
    # Core metrics
    total_signals: int
    win_rate: float
    avg_pnl: float
    sharpe_ratio: float
    max_drawdown: float
    profit_factor: float
    
    # By regime
    regime_performance: Dict[str, Dict[str, float]]
    
    # By model
    model_performance: Dict[str, Dict[str, float]]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "timestamp": self.timestamp.isoformat(),
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "total_signals": self.total_signals,
            "win_rate": self.win_rate,
            "avg_pnl": self.avg_pnl,
            "sharpe_ratio": self.sharpe_ratio,
            "max_drawdown": self.max_drawdown,
            "profit_factor": self.profit_factor,
            "regime_performance": self.regime_performance,
            "model_performance": self.model_performance,
        }


@dataclass
class RetrainingTrigger:
    """Trigger for model retraining."""
    trigger_id: str
    timestamp: datetime
    trigger_type: TriggerType
    
    # Cause
    cause_description: str
    cause_metrics: Dict[str, float]
    
    # Target
    model_id: str
    current_version: str
    
    # Recommendation
    recommended_action: str
    priority: str  # "low", "medium", "high", "critical"
    
    # Status
    acknowledged: bool = False
    acted_upon: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "trigger_id": self.trigger_id,
            "timestamp": self.timestamp.isoformat(),
            "trigger_type": self.trigger_type.value,
            "cause_description": self.cause_description,
            "cause_metrics": self.cause_metrics,
            "model_id": self.model_id,
            "current_version": self.current_version,
            "recommended_action": self.recommended_action,
            "priority": self.priority,
            "acknowledged": self.acknowledged,
            "acted_upon": self.acted_upon,
        }


@dataclass
class ImprovementCycle:
    """A complete improvement cycle."""
    cycle_id: str
    created_at: datetime
    status: ImprovementStatus
    
    # Trigger
    trigger: RetrainingTrigger
    
    # Proposed improvement
    improvement_type: str
    improvement_description: str
    expected_impact: Dict[str, float]
    
    # Validation
    validation_results: Dict[str, Any] = field(default_factory=dict)
    validation_passed: Optional[bool] = None
    
    # Approval
    approval_request_id: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    
    # Deployment
    deployed_at: Optional[datetime] = None
    new_model_version: Optional[str] = None
    
    # Rollback
    rolled_back_at: Optional[datetime] = None
    rollback_reason: Optional[str] = None
    
    # Metrics
    pre_improvement_metrics: Dict[str, float] = field(default_factory=dict)
    post_improvement_metrics: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle_id": self.cycle_id,
            "created_at": self.created_at.isoformat(),
            "status": self.status.value,
            "trigger": self.trigger.to_dict(),
            "improvement_type": self.improvement_type,
            "improvement_description": self.improvement_description,
            "expected_impact": self.expected_impact,
            "validation_results": self.validation_results,
            "validation_passed": self.validation_passed,
            "approval_request_id": self.approval_request_id,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "deployed_at": self.deployed_at.isoformat() if self.deployed_at else None,
            "new_model_version": self.new_model_version,
            "rolled_back_at": self.rolled_back_at.isoformat() if self.rolled_back_at else None,
            "rollback_reason": self.rollback_reason,
            "pre_improvement_metrics": self.pre_improvement_metrics,
            "post_improvement_metrics": self.post_improvement_metrics,
        }


class OutcomeLabeler:
    """Labels trade outcomes for learning."""
    
    def __init__(self):
        self._labels: Dict[str, OutcomeLabel] = {}
        self._lock = RLock()
    
    def label_outcome(
        self,
        signal_id: str,
        direction_correct: bool,
        pnl: float,
        pnl_percent: float,
        regime_id: str,
        volatility: float,
        liquidity: float,
        model_id: str,
        model_version: str,
        feature_hash: str,
        slippage: float,
        execution_quality: float,
    ) -> OutcomeLabel:
        """Label a trade outcome."""
        label = OutcomeLabel(
            signal_id=signal_id,
            timestamp=datetime.utcnow(),
            direction_correct=direction_correct,
            pnl=pnl,
            pnl_percent=pnl_percent,
            regime_id=regime_id,
            volatility=volatility,
            liquidity=liquidity,
            model_id=model_id,
            model_version=model_version,
            feature_hash=feature_hash,
            slippage=slippage,
            execution_quality=execution_quality,
        )
        
        with self._lock:
            self._labels[signal_id] = label
        
        return label
    
    def get_labels(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        model_id: Optional[str] = None,
        regime_id: Optional[str] = None,
    ) -> List[OutcomeLabel]:
        """Get outcome labels with filtering."""
        with self._lock:
            labels = list(self._labels.values())
            
            if start_time:
                labels = [l for l in labels if l.timestamp >= start_time]
            if end_time:
                labels = [l for l in labels if l.timestamp <= end_time]
            if model_id:
                labels = [l for l in labels if l.model_id == model_id]
            if regime_id:
                labels = [l for l in labels if l.regime_id == regime_id]
            
            return labels
    
    def compute_metrics(
        self,
        labels: List[OutcomeLabel],
    ) -> Dict[str, float]:
        """Compute metrics from labels."""
        if not labels:
            return {}
        
        pnls = [l.pnl_percent for l in labels]
        wins = [l for l in labels if l.direction_correct]
        
        return {
            "total_signals": len(labels),
            "win_rate": len(wins) / len(labels),
            "avg_pnl": statistics.mean(pnls),
            "std_pnl": statistics.stdev(pnls) if len(pnls) > 1 else 0,
            "total_pnl": sum(pnls),
            "avg_slippage": statistics.mean([l.slippage for l in labels]),
            "avg_execution_quality": statistics.mean([l.execution_quality for l in labels]),
        }


class DriftDetector:
    """Detects various types of drift."""
    
    # Thresholds
    DATA_DRIFT_THRESHOLD = 0.1
    CONCEPT_DRIFT_THRESHOLD = 0.15
    PERFORMANCE_DRIFT_THRESHOLD = 0.2
    
    def __init__(self):
        self._baseline_distributions: Dict[str, Dict[str, float]] = {}
        self._baseline_performance: Dict[str, float] = {}
        self._detections: List[DriftDetection] = []
        self._lock = RLock()
    
    def set_baseline(
        self,
        feature_distributions: Dict[str, Dict[str, float]],
        performance_metrics: Dict[str, float],
    ):
        """Set baseline for drift detection."""
        with self._lock:
            self._baseline_distributions = feature_distributions
            self._baseline_performance = performance_metrics
    
    def detect_data_drift(
        self,
        current_distributions: Dict[str, Dict[str, float]],
    ) -> Optional[DriftDetection]:
        """Detect data drift in feature distributions."""
        if not self._baseline_distributions:
            return None
        
        drift_scores = {}
        affected_features = []
        
        for feature, baseline_dist in self._baseline_distributions.items():
            if feature not in current_distributions:
                continue
            
            current_dist = current_distributions[feature]
            
            # Simple KL-divergence approximation
            baseline_mean = baseline_dist.get("mean", 0)
            baseline_std = baseline_dist.get("std", 1)
            current_mean = current_dist.get("mean", 0)
            current_std = current_dist.get("std", 1)
            
            # Normalized difference
            if baseline_std > 0:
                drift_score = abs(current_mean - baseline_mean) / baseline_std
            else:
                drift_score = abs(current_mean - baseline_mean)
            
            drift_scores[feature] = drift_score
            
            if drift_score > self.DATA_DRIFT_THRESHOLD:
                affected_features.append(feature)
        
        if not affected_features:
            return None
        
        max_drift = max(drift_scores.values())
        severity = self._score_to_severity(max_drift)
        
        detection = DriftDetection(
            detection_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            drift_type=DriftType.DATA_DRIFT,
            severity=severity,
            drift_score=max_drift,
            p_value=None,
            baseline_metric=0,
            current_metric=max_drift,
            affected_features=affected_features,
            details={"drift_scores": drift_scores},
            action_recommended=self._get_recommendation(severity),
        )
        
        with self._lock:
            self._detections.append(detection)
        
        return detection
    
    def detect_performance_drift(
        self,
        current_performance: Dict[str, float],
    ) -> Optional[DriftDetection]:
        """Detect performance drift."""
        if not self._baseline_performance:
            return None
        
        drift_scores = {}
        affected_metrics = []
        
        for metric, baseline_value in self._baseline_performance.items():
            if metric not in current_performance:
                continue
            
            current_value = current_performance[metric]
            
            # Relative change
            if baseline_value != 0:
                drift_score = abs(current_value - baseline_value) / abs(baseline_value)
            else:
                drift_score = abs(current_value - baseline_value)
            
            drift_scores[metric] = drift_score
            
            if drift_score > self.PERFORMANCE_DRIFT_THRESHOLD:
                affected_metrics.append(metric)
        
        if not affected_metrics:
            return None
        
        max_drift = max(drift_scores.values())
        severity = self._score_to_severity(max_drift)
        
        detection = DriftDetection(
            detection_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            drift_type=DriftType.PERFORMANCE_DRIFT,
            severity=severity,
            drift_score=max_drift,
            p_value=None,
            baseline_metric=self._baseline_performance.get("sharpe_ratio", 0),
            current_metric=current_performance.get("sharpe_ratio", 0),
            affected_features=affected_metrics,
            details={"drift_scores": drift_scores},
            action_recommended=self._get_recommendation(severity),
        )
        
        with self._lock:
            self._detections.append(detection)
        
        return detection
    
    def _score_to_severity(self, score: float) -> DriftSeverity:
        """Convert drift score to severity."""
        if score < 0.1:
            return DriftSeverity.NONE
        elif score < 0.2:
            return DriftSeverity.LOW
        elif score < 0.3:
            return DriftSeverity.MEDIUM
        elif score < 0.5:
            return DriftSeverity.HIGH
        else:
            return DriftSeverity.CRITICAL
    
    def _get_recommendation(self, severity: DriftSeverity) -> str:
        """Get recommendation based on severity."""
        recommendations = {
            DriftSeverity.NONE: "No action needed",
            DriftSeverity.LOW: "Monitor closely",
            DriftSeverity.MEDIUM: "Consider retraining",
            DriftSeverity.HIGH: "Recommend retraining",
            DriftSeverity.CRITICAL: "Urgent retraining required",
        }
        return recommendations.get(severity, "Unknown")
    
    def get_recent_detections(
        self,
        hours: int = 24,
    ) -> List[DriftDetection]:
        """Get recent drift detections."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        with self._lock:
            return [d for d in self._detections if d.timestamp >= cutoff]


class PerformanceTracker:
    """Tracks performance over time."""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self._snapshots: List[PerformanceSnapshot] = []
        self._rolling_metrics: List[Dict[str, float]] = []
        self._lock = RLock()
    
    def add_snapshot(self, snapshot: PerformanceSnapshot):
        """Add a performance snapshot."""
        with self._lock:
            self._snapshots.append(snapshot)
            
            # Keep rolling window
            if len(self._snapshots) > self.window_size:
                self._snapshots = self._snapshots[-self.window_size:]
    
    def compute_rolling_metrics(
        self,
        window_days: int = 7,
    ) -> Dict[str, float]:
        """Compute rolling performance metrics."""
        cutoff = datetime.utcnow() - timedelta(days=window_days)
        
        with self._lock:
            recent = [s for s in self._snapshots if s.timestamp >= cutoff]
        
        if not recent:
            return {}
        
        return {
            "avg_win_rate": statistics.mean([s.win_rate for s in recent]),
            "avg_sharpe": statistics.mean([s.sharpe_ratio for s in recent]),
            "avg_pnl": statistics.mean([s.avg_pnl for s in recent]),
            "max_drawdown": min([s.max_drawdown for s in recent]),
            "total_signals": sum([s.total_signals for s in recent]),
        }
    
    def detect_decay(
        self,
        baseline_metrics: Dict[str, float],
        threshold: float = 0.2,
    ) -> Tuple[bool, Dict[str, float]]:
        """Detect performance decay."""
        current = self.compute_rolling_metrics()
        
        if not current or not baseline_metrics:
            return False, {}
        
        decay_metrics = {}
        decay_detected = False
        
        for metric in ["avg_win_rate", "avg_sharpe", "avg_pnl"]:
            if metric in current and metric in baseline_metrics:
                baseline = baseline_metrics[metric]
                current_val = current[metric]
                
                if baseline != 0:
                    decay = (baseline - current_val) / abs(baseline)
                else:
                    decay = baseline - current_val
                
                decay_metrics[metric] = decay
                
                if decay > threshold:
                    decay_detected = True
        
        return decay_detected, decay_metrics
    
    def get_trend(
        self,
        metric: str,
        periods: int = 10,
    ) -> Tuple[str, float]:
        """Get trend for a metric."""
        with self._lock:
            if len(self._snapshots) < periods:
                return "insufficient_data", 0.0
            
            recent = self._snapshots[-periods:]
        
        values = [getattr(s, metric, None) for s in recent]
        values = [v for v in values if v is not None]
        
        if len(values) < 2:
            return "insufficient_data", 0.0
        
        # Simple linear regression slope
        n = len(values)
        x_mean = (n - 1) / 2
        y_mean = statistics.mean(values)
        
        numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return "flat", 0.0
        
        slope = numerator / denominator
        
        # Normalize slope
        if y_mean != 0:
            normalized_slope = slope / abs(y_mean)
        else:
            normalized_slope = slope
        
        if normalized_slope > 0.05:
            return "improving", normalized_slope
        elif normalized_slope < -0.05:
            return "declining", normalized_slope
        else:
            return "stable", normalized_slope


class RetrainingManager:
    """Manages retraining triggers and cycles."""
    
    # Thresholds
    PERFORMANCE_THRESHOLD = 0.5  # Sharpe ratio
    WIN_RATE_THRESHOLD = 0.45
    DECAY_THRESHOLD = 0.2
    
    def __init__(self):
        self._triggers: List[RetrainingTrigger] = []
        self._cycles: Dict[str, ImprovementCycle] = {}
        self._lock = RLock()
    
    def check_triggers(
        self,
        current_metrics: Dict[str, float],
        baseline_metrics: Dict[str, float],
        drift_detections: List[DriftDetection],
    ) -> List[RetrainingTrigger]:
        """Check for retraining triggers."""
        triggers = []
        
        # Performance decay trigger
        sharpe = current_metrics.get("sharpe_ratio", 0)
        if sharpe < self.PERFORMANCE_THRESHOLD:
            triggers.append(RetrainingTrigger(
                trigger_id=str(uuid.uuid4()),
                timestamp=datetime.utcnow(),
                trigger_type=TriggerType.PERFORMANCE_DECAY,
                cause_description=f"Sharpe ratio {sharpe:.2f} below threshold {self.PERFORMANCE_THRESHOLD}",
                cause_metrics={"sharpe_ratio": sharpe},
                model_id="default",
                current_version="current",
                recommended_action="Retrain with recent data",
                priority="high" if sharpe < 0 else "medium",
            ))
        
        # Win rate trigger
        win_rate = current_metrics.get("win_rate", 0)
        if win_rate < self.WIN_RATE_THRESHOLD:
            triggers.append(RetrainingTrigger(
                trigger_id=str(uuid.uuid4()),
                timestamp=datetime.utcnow(),
                trigger_type=TriggerType.PERFORMANCE_DECAY,
                cause_description=f"Win rate {win_rate:.2%} below threshold {self.WIN_RATE_THRESHOLD:.2%}",
                cause_metrics={"win_rate": win_rate},
                model_id="default",
                current_version="current",
                recommended_action="Analyze losing trades and retrain",
                priority="medium",
            ))
        
        # Drift triggers
        for detection in drift_detections:
            if detection.severity in [DriftSeverity.HIGH, DriftSeverity.CRITICAL]:
                triggers.append(RetrainingTrigger(
                    trigger_id=str(uuid.uuid4()),
                    timestamp=datetime.utcnow(),
                    trigger_type=TriggerType.DRIFT_DETECTED,
                    cause_description=f"{detection.drift_type.value}: {detection.action_recommended}",
                    cause_metrics={"drift_score": detection.drift_score},
                    model_id="default",
                    current_version="current",
                    recommended_action="Retrain to adapt to new distribution",
                    priority="critical" if detection.severity == DriftSeverity.CRITICAL else "high",
                ))
        
        with self._lock:
            self._triggers.extend(triggers)
        
        return triggers
    
    def create_improvement_cycle(
        self,
        trigger: RetrainingTrigger,
        improvement_type: str,
        improvement_description: str,
        expected_impact: Dict[str, float],
    ) -> ImprovementCycle:
        """Create a new improvement cycle."""
        cycle = ImprovementCycle(
            cycle_id=str(uuid.uuid4()),
            created_at=datetime.utcnow(),
            status=ImprovementStatus.PROPOSED,
            trigger=trigger,
            improvement_type=improvement_type,
            improvement_description=improvement_description,
            expected_impact=expected_impact,
        )
        
        with self._lock:
            self._cycles[cycle.cycle_id] = cycle
            trigger.acted_upon = True
        
        return cycle
    
    def update_cycle_status(
        self,
        cycle_id: str,
        status: ImprovementStatus,
        **kwargs,
    ) -> bool:
        """Update improvement cycle status."""
        with self._lock:
            cycle = self._cycles.get(cycle_id)
            if cycle is None:
                return False
            
            cycle.status = status
            
            for key, value in kwargs.items():
                if hasattr(cycle, key):
                    setattr(cycle, key, value)
            
            return True
    
    def get_pending_triggers(self) -> List[RetrainingTrigger]:
        """Get triggers that haven't been acted upon."""
        with self._lock:
            return [t for t in self._triggers if not t.acted_upon]
    
    def get_active_cycles(self) -> List[ImprovementCycle]:
        """Get active improvement cycles."""
        active_statuses = [
            ImprovementStatus.PROPOSED,
            ImprovementStatus.VALIDATING,
            ImprovementStatus.VALIDATED,
            ImprovementStatus.AWAITING_APPROVAL,
            ImprovementStatus.APPROVED,
            ImprovementStatus.DEPLOYING,
        ]
        with self._lock:
            return [c for c in self._cycles.values() if c.status in active_statuses]


class SelfImprovementLoop:
    """
    Self-Improvement Loop Coordinator.
    
    Orchestrates the continuous improvement process:
    1. Label outcomes
    2. Detect drift
    3. Track performance
    4. Trigger retraining
    5. Validate improvements
    6. Deploy with approval
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        self.outcome_labeler = OutcomeLabeler()
        self.drift_detector = DriftDetector()
        self.performance_tracker = PerformanceTracker()
        self.retraining_manager = RetrainingManager()
        
        self._baseline_set = False
        self._lock = RLock()
        
        logger.info("Self-Improvement Loop initialized")
    
    def label_outcome(
        self,
        signal_id: str,
        direction_correct: bool,
        pnl: float,
        pnl_percent: float,
        regime_id: str,
        volatility: float,
        liquidity: float,
        model_id: str,
        model_version: str,
        feature_hash: str,
        slippage: float,
        execution_quality: float,
    ) -> OutcomeLabel:
        """Label a trade outcome."""
        return self.outcome_labeler.label_outcome(
            signal_id=signal_id,
            direction_correct=direction_correct,
            pnl=pnl,
            pnl_percent=pnl_percent,
            regime_id=regime_id,
            volatility=volatility,
            liquidity=liquidity,
            model_id=model_id,
            model_version=model_version,
            feature_hash=feature_hash,
            slippage=slippage,
            execution_quality=execution_quality,
        )
    
    def set_baseline(
        self,
        feature_distributions: Dict[str, Dict[str, float]],
        performance_metrics: Dict[str, float],
    ):
        """Set baseline for drift detection."""
        self.drift_detector.set_baseline(feature_distributions, performance_metrics)
        self._baseline_set = True
        logger.info("Baseline set for drift detection")
    
    def run_detection_cycle(
        self,
        current_distributions: Dict[str, Dict[str, float]],
        current_performance: Dict[str, float],
    ) -> Dict[str, Any]:
        """Run a complete detection cycle."""
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "drift_detections": [],
            "performance_decay": False,
            "triggers": [],
        }
        
        # Detect data drift
        data_drift = self.drift_detector.detect_data_drift(current_distributions)
        if data_drift:
            results["drift_detections"].append(data_drift.to_dict())
        
        # Detect performance drift
        perf_drift = self.drift_detector.detect_performance_drift(current_performance)
        if perf_drift:
            results["drift_detections"].append(perf_drift.to_dict())
        
        # Check for performance decay
        baseline = self.drift_detector._baseline_performance
        decay_detected, decay_metrics = self.performance_tracker.detect_decay(baseline)
        results["performance_decay"] = decay_detected
        results["decay_metrics"] = decay_metrics
        
        # Check triggers
        drift_detections = self.drift_detector.get_recent_detections(hours=1)
        triggers = self.retraining_manager.check_triggers(
            current_metrics=current_performance,
            baseline_metrics=baseline,
            drift_detections=drift_detections,
        )
        results["triggers"] = [t.to_dict() for t in triggers]
        
        return results
    
    def propose_improvement(
        self,
        trigger_id: str,
        improvement_type: str,
        improvement_description: str,
        expected_impact: Dict[str, float],
    ) -> Optional[ImprovementCycle]:
        """Propose an improvement based on a trigger."""
        # Find the trigger
        trigger = None
        for t in self.retraining_manager._triggers:
            if t.trigger_id == trigger_id:
                trigger = t
                break
        
        if trigger is None:
            logger.warning(f"Trigger not found: {trigger_id}")
            return None
        
        cycle = self.retraining_manager.create_improvement_cycle(
            trigger=trigger,
            improvement_type=improvement_type,
            improvement_description=improvement_description,
            expected_impact=expected_impact,
        )
        
        logger.info(f"Created improvement cycle: {cycle.cycle_id}")
        return cycle
    
    def validate_improvement(
        self,
        cycle_id: str,
        validation_results: Dict[str, Any],
    ) -> Tuple[bool, str]:
        """Validate an improvement."""
        cycle = self.retraining_manager._cycles.get(cycle_id)
        if cycle is None:
            return False, "Cycle not found"
        
        # Update cycle
        cycle.validation_results = validation_results
        cycle.status = ImprovementStatus.VALIDATING
        
        # Check validation criteria
        passed = True
        reasons = []
        
        # Check performance improvement
        if "sharpe_improvement" in validation_results:
            if validation_results["sharpe_improvement"] < 0:
                passed = False
                reasons.append("Sharpe ratio did not improve")
        
        # Check robustness
        if "regime_coverage" in validation_results:
            if validation_results["regime_coverage"] < 0.8:
                passed = False
                reasons.append("Insufficient regime coverage")
        
        # Check stress test
        if "stress_test_passed" in validation_results:
            if not validation_results["stress_test_passed"]:
                passed = False
                reasons.append("Failed stress test")
        
        cycle.validation_passed = passed
        cycle.status = ImprovementStatus.VALIDATED if passed else ImprovementStatus.REJECTED
        
        message = "Validation passed" if passed else f"Validation failed: {', '.join(reasons)}"
        return passed, message
    
    def request_approval(
        self,
        cycle_id: str,
    ) -> Tuple[bool, str]:
        """Request approval for a validated improvement."""
        cycle = self.retraining_manager._cycles.get(cycle_id)
        if cycle is None:
            return False, "Cycle not found"
        
        if cycle.status != ImprovementStatus.VALIDATED:
            return False, f"Cycle not validated: {cycle.status.value}"
        
        # Create approval request (would integrate with governance)
        cycle.approval_request_id = str(uuid.uuid4())
        cycle.status = ImprovementStatus.AWAITING_APPROVAL
        
        logger.info(f"Requested approval for cycle: {cycle_id}")
        return True, f"Approval request created: {cycle.approval_request_id}"
    
    def approve_improvement(
        self,
        cycle_id: str,
        approver: str,
    ) -> Tuple[bool, str]:
        """Approve an improvement (G0 action)."""
        cycle = self.retraining_manager._cycles.get(cycle_id)
        if cycle is None:
            return False, "Cycle not found"
        
        if cycle.status != ImprovementStatus.AWAITING_APPROVAL:
            return False, f"Cycle not awaiting approval: {cycle.status.value}"
        
        cycle.approved_by = approver
        cycle.approved_at = datetime.utcnow()
        cycle.status = ImprovementStatus.APPROVED
        
        logger.info(f"Approved improvement cycle: {cycle_id} by {approver}")
        return True, "Approved"
    
    def deploy_improvement(
        self,
        cycle_id: str,
        new_model_version: str,
    ) -> Tuple[bool, str]:
        """Deploy an approved improvement."""
        cycle = self.retraining_manager._cycles.get(cycle_id)
        if cycle is None:
            return False, "Cycle not found"
        
        if cycle.status != ImprovementStatus.APPROVED:
            return False, f"Cycle not approved: {cycle.status.value}"
        
        cycle.status = ImprovementStatus.DEPLOYING
        cycle.new_model_version = new_model_version
        
        # Deployment would happen here (integrate with training-first architecture)
        
        cycle.deployed_at = datetime.utcnow()
        cycle.status = ImprovementStatus.DEPLOYED
        
        logger.info(f"Deployed improvement cycle: {cycle_id} as version {new_model_version}")
        return True, f"Deployed as version {new_model_version}"
    
    def rollback_improvement(
        self,
        cycle_id: str,
        reason: str,
    ) -> Tuple[bool, str]:
        """Rollback a deployed improvement."""
        cycle = self.retraining_manager._cycles.get(cycle_id)
        if cycle is None:
            return False, "Cycle not found"
        
        if cycle.status != ImprovementStatus.DEPLOYED:
            return False, f"Cycle not deployed: {cycle.status.value}"
        
        cycle.rolled_back_at = datetime.utcnow()
        cycle.rollback_reason = reason
        cycle.status = ImprovementStatus.ROLLED_BACK
        
        logger.warning(f"Rolled back improvement cycle: {cycle_id} - {reason}")
        return True, "Rolled back"
    
    def get_improvement_summary(self) -> Dict[str, Any]:
        """Get summary of improvement activity."""
        cycles = list(self.retraining_manager._cycles.values())
        triggers = self.retraining_manager._triggers
        
        by_status = {}
        for status in ImprovementStatus:
            by_status[status.value] = len([c for c in cycles if c.status == status])
        
        return {
            "total_cycles": len(cycles),
            "by_status": by_status,
            "pending_triggers": len([t for t in triggers if not t.acted_upon]),
            "active_cycles": len(self.retraining_manager.get_active_cycles()),
            "recent_detections": len(self.drift_detector.get_recent_detections(hours=24)),
        }
