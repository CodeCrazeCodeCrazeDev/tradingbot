"""
Anomaly Detector

Detects anomalous patterns in agent behavior and outputs.
Identifies potential issues before they cause problems.
"""

import asyncio
import math
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import uuid
from collections import deque

logger = logging.getLogger(__name__)


class AnomalyType(Enum):
    """Types of anomalies."""
    STATISTICAL_OUTLIER = "statistical_outlier"
    BEHAVIORAL_CHANGE = "behavioral_change"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    OUTPUT_DRIFT = "output_drift"
    CONFIDENCE_ANOMALY = "confidence_anomaly"
    TEMPORAL_ANOMALY = "temporal_anomaly"
    FREQUENCY_ANOMALY = "frequency_anomaly"
    PATTERN_BREAK = "pattern_break"
    RESOURCE_ANOMALY = "resource_anomaly"


class AnomalySeverity(Enum):
    """Severity of anomalies."""
    INFO = "info"
    WARNING = "warning"
    ALERT = "alert"
    CRITICAL = "critical"


class DetectionMethod(Enum):
    """Methods for anomaly detection."""
    ZSCORE = "zscore"
    IQR = "iqr"
    MOVING_AVERAGE = "moving_average"
    ISOLATION_FOREST = "isolation_forest"
    CHANGE_POINT = "change_point"
    THRESHOLD = "threshold"


@dataclass
class Anomaly:
    """A detected anomaly."""
    anomaly_id: str
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    agent_id: str
    description: str
    value: Any
    expected_range: Tuple[float, float]
    deviation: float
    detection_method: DetectionMethod
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'anomaly_id': self.anomaly_id,
            'anomaly_type': self.anomaly_type.value,
            'severity': self.severity.value,
            'agent_id': self.agent_id,
            'description': self.description,
            'value': self.value,
            'expected_range': self.expected_range,
            'deviation': self.deviation,
            'detection_method': self.detection_method.value,
            'timestamp': self.timestamp.isoformat(),
            'context': self.context,
        }


@dataclass
class AnomalyReport:
    """Report of anomaly detection."""
    report_id: str
    agent_id: str
    anomalies: List[Anomaly]
    total_anomalies: int
    critical_count: int
    alert_count: int
    warning_count: int
    overall_health_score: float
    recommendations: List[str]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'report_id': self.report_id,
            'agent_id': self.agent_id,
            'anomalies': [a.to_dict() for a in self.anomalies],
            'total_anomalies': self.total_anomalies,
            'critical_count': self.critical_count,
            'alert_count': self.alert_count,
            'warning_count': self.warning_count,
            'overall_health_score': self.overall_health_score,
            'recommendations': self.recommendations,
            'timestamp': self.timestamp.isoformat(),
        }


@dataclass
class AgentMetrics:
    """Metrics tracked for an agent."""
    agent_id: str
    confidence_history: deque
    output_frequency: deque
    error_rate_history: deque
    latency_history: deque
    last_updated: datetime
    baseline_stats: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    def __post_init__(self):
        if not isinstance(self.confidence_history, deque):
            self.confidence_history = deque(maxlen=1000)
        if not isinstance(self.output_frequency, deque):
            self.output_frequency = deque(maxlen=1000)
        if not isinstance(self.error_rate_history, deque):
            self.error_rate_history = deque(maxlen=1000)
        if not isinstance(self.latency_history, deque):
            self.latency_history = deque(maxlen=1000)


class AnomalyDetector:
    """
    Detects anomalous patterns in agent behavior.
    
    Provides:
    - Statistical anomaly detection
    - Behavioral change detection
    - Performance monitoring
    - Output drift detection
    - Real-time alerting
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.storage_path = Path(self.config.get('storage_path', 'anomaly_detector_data'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._agent_metrics: Dict[str, AgentMetrics] = {}
        self._anomalies: Dict[str, Anomaly] = {}
        self._reports: Dict[str, AnomalyReport] = {}
        self._alert_callbacks: List[callable] = []
        
        self._detection_config = {
            'zscore_threshold': 3.0,
            'iqr_multiplier': 1.5,
            'moving_average_window': 20,
            'minimum_samples': 30,
            'confidence_ceiling': 0.99,
            'confidence_floor': 0.01,
            'max_latency_ms': 5000,
            'max_error_rate': 0.1,
            'drift_threshold': 0.2,
        }
        
        logger.info("✅ Anomaly Detector initialized")
    
    async def record_metric(
        self,
        agent_id: str,
        metric_type: str,
        value: float,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Record a metric for an agent.
        
        Args:
            agent_id: ID of the agent
            metric_type: Type of metric
            value: Metric value
            metadata: Additional metadata
        """
        if agent_id not in self._agent_metrics:
            self._agent_metrics[agent_id] = AgentMetrics(
                agent_id=agent_id,
                confidence_history=deque(maxlen=1000),
                output_frequency=deque(maxlen=1000),
                error_rate_history=deque(maxlen=1000),
                latency_history=deque(maxlen=1000),
                last_updated=datetime.now(timezone.utc),
            )
        
        metrics = self._agent_metrics[agent_id]
        metrics.last_updated = datetime.now(timezone.utc)
        
        record = {
            'value': value,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'metadata': metadata or {},
        }
        
        if metric_type == 'confidence':
            metrics.confidence_history.append(record)
        elif metric_type == 'frequency':
            metrics.output_frequency.append(record)
        elif metric_type == 'error_rate':
            metrics.error_rate_history.append(record)
        elif metric_type == 'latency':
            metrics.latency_history.append(record)
    
    async def detect_anomalies(
        self,
        agent_id: str,
        current_values: Optional[Dict[str, float]] = None,
    ) -> AnomalyReport:
        """
        Detect anomalies for an agent.
        
        Args:
            agent_id: ID of the agent
            current_values: Optional current values to check
        
        Returns:
            AnomalyReport
        """
        report_id = f"AR-{uuid.uuid4().hex[:12]}"
        anomalies = []
        
        if agent_id not in self._agent_metrics:
            return AnomalyReport(
                report_id=report_id,
                agent_id=agent_id,
                anomalies=[],
                total_anomalies=0,
                critical_count=0,
                alert_count=0,
                warning_count=0,
                overall_health_score=1.0,
                recommendations=["No metrics recorded for this agent yet"],
                timestamp=datetime.now(timezone.utc),
            )
        
        metrics = self._agent_metrics[agent_id]
        
        confidence_anomalies = await self._detect_confidence_anomalies(agent_id, metrics, current_values)
        anomalies.extend(confidence_anomalies)
        
        frequency_anomalies = await self._detect_frequency_anomalies(agent_id, metrics)
        anomalies.extend(frequency_anomalies)
        
        error_anomalies = await self._detect_error_rate_anomalies(agent_id, metrics, current_values)
        anomalies.extend(error_anomalies)
        
        latency_anomalies = await self._detect_latency_anomalies(agent_id, metrics, current_values)
        anomalies.extend(latency_anomalies)
        
        drift_anomalies = await self._detect_output_drift(agent_id, metrics)
        anomalies.extend(drift_anomalies)
        
        for anomaly in anomalies:
            self._anomalies[anomaly.anomaly_id] = anomaly
        
        critical_count = sum(1 for a in anomalies if a.severity == AnomalySeverity.CRITICAL)
        alert_count = sum(1 for a in anomalies if a.severity == AnomalySeverity.ALERT)
        warning_count = sum(1 for a in anomalies if a.severity == AnomalySeverity.WARNING)
        
        health_score = self._calculate_health_score(anomalies)
        
        recommendations = self._generate_recommendations(anomalies, health_score)
        
        report = AnomalyReport(
            report_id=report_id,
            agent_id=agent_id,
            anomalies=anomalies,
            total_anomalies=len(anomalies),
            critical_count=critical_count,
            alert_count=alert_count,
            warning_count=warning_count,
            overall_health_score=health_score,
            recommendations=recommendations,
            timestamp=datetime.now(timezone.utc),
        )
        
        self._reports[report_id] = report
        
        if critical_count > 0:
            await self._trigger_alerts(report)
        
        await self._persist_report(report)
        
        logger.info(f"Anomaly detection complete for {agent_id}: "
                   f"{len(anomalies)} anomalies, health score: {health_score:.2f}")
        
        return report
    
    async def _detect_confidence_anomalies(
        self,
        agent_id: str,
        metrics: AgentMetrics,
        current_values: Optional[Dict[str, float]],
    ) -> List[Anomaly]:
        """Detect confidence-related anomalies."""
        anomalies = []
        
        if current_values and 'confidence' in current_values:
            confidence = current_values['confidence']
            
            if confidence > self._detection_config['confidence_ceiling']:
                anomalies.append(Anomaly(
                    anomaly_id=f"ANM-{uuid.uuid4().hex[:8]}",
                    anomaly_type=AnomalyType.CONFIDENCE_ANOMALY,
                    severity=AnomalySeverity.WARNING,
                    agent_id=agent_id,
                    description=f"Confidence {confidence:.3f} exceeds ceiling",
                    value=confidence,
                    expected_range=(0.0, self._detection_config['confidence_ceiling']),
                    deviation=confidence - self._detection_config['confidence_ceiling'],
                    detection_method=DetectionMethod.THRESHOLD,
                    timestamp=datetime.now(timezone.utc),
                ))
            
            if confidence < self._detection_config['confidence_floor']:
                anomalies.append(Anomaly(
                    anomaly_id=f"ANM-{uuid.uuid4().hex[:8]}",
                    anomaly_type=AnomalyType.CONFIDENCE_ANOMALY,
                    severity=AnomalySeverity.INFO,
                    agent_id=agent_id,
                    description=f"Confidence {confidence:.3f} below floor",
                    value=confidence,
                    expected_range=(self._detection_config['confidence_floor'], 1.0),
                    deviation=self._detection_config['confidence_floor'] - confidence,
                    detection_method=DetectionMethod.THRESHOLD,
                    timestamp=datetime.now(timezone.utc),
                ))
        
        if len(metrics.confidence_history) >= self._detection_config['minimum_samples']:
            values = [r['value'] for r in metrics.confidence_history]
            
            mean = sum(values) / len(values)
            variance = sum((v - mean) ** 2 for v in values) / len(values)
            std = math.sqrt(variance) if variance > 0 else 0.001
            
            if current_values and 'confidence' in current_values:
                zscore = abs(current_values['confidence'] - mean) / std
                
                if zscore > self._detection_config['zscore_threshold']:
                    anomalies.append(Anomaly(
                        anomaly_id=f"ANM-{uuid.uuid4().hex[:8]}",
                        anomaly_type=AnomalyType.STATISTICAL_OUTLIER,
                        severity=AnomalySeverity.ALERT if zscore > 4 else AnomalySeverity.WARNING,
                        agent_id=agent_id,
                        description=f"Confidence z-score {zscore:.2f} exceeds threshold",
                        value=current_values['confidence'],
                        expected_range=(mean - 2*std, mean + 2*std),
                        deviation=zscore,
                        detection_method=DetectionMethod.ZSCORE,
                        timestamp=datetime.now(timezone.utc),
                        context={'mean': mean, 'std': std, 'zscore': zscore},
                    ))
        
        return anomalies
    
    async def _detect_frequency_anomalies(
        self,
        agent_id: str,
        metrics: AgentMetrics,
    ) -> List[Anomaly]:
        """Detect output frequency anomalies."""
        anomalies = []
        
        if len(metrics.output_frequency) < 10:
            return anomalies
        
        recent = list(metrics.output_frequency)[-20:]
        timestamps = [datetime.fromisoformat(r['timestamp']) for r in recent]
        
        if len(timestamps) >= 2:
            intervals = []
            for i in range(1, len(timestamps)):
                interval = (timestamps[i] - timestamps[i-1]).total_seconds()
                intervals.append(interval)
            
            if intervals:
                mean_interval = sum(intervals) / len(intervals)
                
                if len(intervals) >= 5:
                    recent_intervals = intervals[-5:]
                    recent_mean = sum(recent_intervals) / len(recent_intervals)
                    
                    if mean_interval > 0:
                        change_ratio = recent_mean / mean_interval
                        
                        if change_ratio > 2.0:
                            anomalies.append(Anomaly(
                                anomaly_id=f"ANM-{uuid.uuid4().hex[:8]}",
                                anomaly_type=AnomalyType.FREQUENCY_ANOMALY,
                                severity=AnomalySeverity.WARNING,
                                agent_id=agent_id,
                                description="Output frequency has decreased significantly",
                                value=recent_mean,
                                expected_range=(mean_interval * 0.5, mean_interval * 1.5),
                                deviation=change_ratio,
                                detection_method=DetectionMethod.MOVING_AVERAGE,
                                timestamp=datetime.now(timezone.utc),
                                context={'historical_mean': mean_interval, 'recent_mean': recent_mean},
                            ))
                        elif change_ratio < 0.5:
                            anomalies.append(Anomaly(
                                anomaly_id=f"ANM-{uuid.uuid4().hex[:8]}",
                                anomaly_type=AnomalyType.FREQUENCY_ANOMALY,
                                severity=AnomalySeverity.INFO,
                                agent_id=agent_id,
                                description="Output frequency has increased significantly",
                                value=recent_mean,
                                expected_range=(mean_interval * 0.5, mean_interval * 1.5),
                                deviation=change_ratio,
                                detection_method=DetectionMethod.MOVING_AVERAGE,
                                timestamp=datetime.now(timezone.utc),
                            ))
        
        return anomalies
    
    async def _detect_error_rate_anomalies(
        self,
        agent_id: str,
        metrics: AgentMetrics,
        current_values: Optional[Dict[str, float]],
    ) -> List[Anomaly]:
        """Detect error rate anomalies."""
        anomalies = []
        
        if current_values and 'error_rate' in current_values:
            error_rate = current_values['error_rate']
            max_rate = self._detection_config['max_error_rate']
            
            if error_rate > max_rate:
                severity = AnomalySeverity.CRITICAL if error_rate > max_rate * 2 else AnomalySeverity.ALERT
                
                anomalies.append(Anomaly(
                    anomaly_id=f"ANM-{uuid.uuid4().hex[:8]}",
                    anomaly_type=AnomalyType.PERFORMANCE_DEGRADATION,
                    severity=severity,
                    agent_id=agent_id,
                    description=f"Error rate {error_rate:.1%} exceeds threshold {max_rate:.1%}",
                    value=error_rate,
                    expected_range=(0.0, max_rate),
                    deviation=error_rate - max_rate,
                    detection_method=DetectionMethod.THRESHOLD,
                    timestamp=datetime.now(timezone.utc),
                ))
        
        return anomalies
    
    async def _detect_latency_anomalies(
        self,
        agent_id: str,
        metrics: AgentMetrics,
        current_values: Optional[Dict[str, float]],
    ) -> List[Anomaly]:
        """Detect latency anomalies."""
        anomalies = []
        
        if current_values and 'latency_ms' in current_values:
            latency = current_values['latency_ms']
            max_latency = self._detection_config['max_latency_ms']
            
            if latency > max_latency:
                severity = AnomalySeverity.ALERT if latency > max_latency * 2 else AnomalySeverity.WARNING
                
                anomalies.append(Anomaly(
                    anomaly_id=f"ANM-{uuid.uuid4().hex[:8]}",
                    anomaly_type=AnomalyType.PERFORMANCE_DEGRADATION,
                    severity=severity,
                    agent_id=agent_id,
                    description=f"Latency {latency:.0f}ms exceeds threshold {max_latency}ms",
                    value=latency,
                    expected_range=(0, max_latency),
                    deviation=latency - max_latency,
                    detection_method=DetectionMethod.THRESHOLD,
                    timestamp=datetime.now(timezone.utc),
                ))
        
        return anomalies
    
    async def _detect_output_drift(
        self,
        agent_id: str,
        metrics: AgentMetrics,
    ) -> List[Anomaly]:
        """Detect drift in output patterns."""
        anomalies = []
        
        if len(metrics.confidence_history) < self._detection_config['minimum_samples'] * 2:
            return anomalies
        
        values = [r['value'] for r in metrics.confidence_history]
        
        mid_point = len(values) // 2
        first_half = values[:mid_point]
        second_half = values[mid_point:]
        
        mean_first = sum(first_half) / len(first_half)
        mean_second = sum(second_half) / len(second_half)
        
        drift = abs(mean_second - mean_first)
        
        if drift > self._detection_config['drift_threshold']:
            anomalies.append(Anomaly(
                anomaly_id=f"ANM-{uuid.uuid4().hex[:8]}",
                anomaly_type=AnomalyType.OUTPUT_DRIFT,
                severity=AnomalySeverity.WARNING,
                agent_id=agent_id,
                description=f"Output drift detected: mean shifted by {drift:.3f}",
                value=drift,
                expected_range=(0, self._detection_config['drift_threshold']),
                deviation=drift,
                detection_method=DetectionMethod.CHANGE_POINT,
                timestamp=datetime.now(timezone.utc),
                context={'mean_first_half': mean_first, 'mean_second_half': mean_second},
            ))
        
        return anomalies
    
    def _calculate_health_score(self, anomalies: List[Anomaly]) -> float:
        """Calculate overall health score from anomalies."""
        if not anomalies:
            return 1.0
        
        severity_penalties = {
            AnomalySeverity.INFO: 0.02,
            AnomalySeverity.WARNING: 0.1,
            AnomalySeverity.ALERT: 0.25,
            AnomalySeverity.CRITICAL: 0.5,
        }
        
        total_penalty = sum(severity_penalties.get(a.severity, 0.1) for a in anomalies)
        
        health_score = max(0.0, 1.0 - total_penalty)
        
        return health_score
    
    def _generate_recommendations(
        self,
        anomalies: List[Anomaly],
        health_score: float,
    ) -> List[str]:
        """Generate recommendations based on anomalies."""
        recommendations = []
        
        if health_score < 0.5:
            recommendations.append("URGENT: Agent health is critically low - consider quarantine")
        
        anomaly_types = set(a.anomaly_type for a in anomalies)
        
        if AnomalyType.CONFIDENCE_ANOMALY in anomaly_types:
            recommendations.append("Review confidence calibration - values are outside expected range")
        
        if AnomalyType.PERFORMANCE_DEGRADATION in anomaly_types:
            recommendations.append("Investigate performance issues - error rate or latency elevated")
        
        if AnomalyType.OUTPUT_DRIFT in anomaly_types:
            recommendations.append("Output patterns have shifted - may need recalibration")
        
        if AnomalyType.FREQUENCY_ANOMALY in anomaly_types:
            recommendations.append("Output frequency has changed - check for resource issues")
        
        critical_anomalies = [a for a in anomalies if a.severity == AnomalySeverity.CRITICAL]
        if critical_anomalies:
            recommendations.append(f"Address {len(critical_anomalies)} critical anomalies immediately")
        
        if not recommendations:
            recommendations.append("No immediate action required - continue monitoring")
        
        return recommendations
    
    async def _trigger_alerts(self, report: AnomalyReport):
        """Trigger alerts for critical anomalies."""
        for callback in self._alert_callbacks:
            try:
                await callback(report)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")
        
        logger.warning(f"ALERT: Critical anomalies detected for agent {report.agent_id}")
    
    def register_alert_callback(self, callback: callable):
        """Register a callback for alerts."""
        self._alert_callbacks.append(callback)
    
    def get_anomaly(self, anomaly_id: str) -> Optional[Anomaly]:
        """Get an anomaly by ID."""
        return self._anomalies.get(anomaly_id)
    
    def get_report(self, report_id: str) -> Optional[AnomalyReport]:
        """Get a report by ID."""
        return self._reports.get(report_id)
    
    def get_agent_metrics(self, agent_id: str) -> Optional[AgentMetrics]:
        """Get metrics for an agent."""
        return self._agent_metrics.get(agent_id)
    
    async def _persist_report(self, report: AnomalyReport):
        """Persist report to storage."""
        report_file = self.storage_path / 'reports' / f"{report.report_id}.json"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(report.to_dict(), f, indent=2)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get detector statistics."""
        severity_counts = {}
        type_counts = {}
        
        for anomaly in self._anomalies.values():
            severity_counts[anomaly.severity.value] = severity_counts.get(anomaly.severity.value, 0) + 1
            type_counts[anomaly.anomaly_type.value] = type_counts.get(anomaly.anomaly_type.value, 0) + 1
        
        return {
            'total_agents_monitored': len(self._agent_metrics),
            'total_anomalies_detected': len(self._anomalies),
            'total_reports': len(self._reports),
            'anomalies_by_severity': severity_counts,
            'anomalies_by_type': type_counts,
            'alert_callbacks_registered': len(self._alert_callbacks),
        }
