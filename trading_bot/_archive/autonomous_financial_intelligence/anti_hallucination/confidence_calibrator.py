"""
Confidence Calibrator

Calibrates confidence scores to actual accuracy.
Ensures reported confidence matches empirical performance.
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

logger = logging.getLogger(__name__)


class CalibrationStatus(Enum):
    """Status of calibration."""
    WELL_CALIBRATED = "well_calibrated"
    OVERCONFIDENT = "overconfident"
    UNDERCONFIDENT = "underconfident"
    POORLY_CALIBRATED = "poorly_calibrated"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass
class CalibrationMetrics:
    """Metrics for calibration assessment."""
    expected_calibration_error: float
    maximum_calibration_error: float
    brier_score: float
    reliability_score: float
    resolution_score: float
    sharpness: float
    overconfidence_ratio: float
    underconfidence_ratio: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'expected_calibration_error': self.expected_calibration_error,
            'maximum_calibration_error': self.maximum_calibration_error,
            'brier_score': self.brier_score,
            'reliability_score': self.reliability_score,
            'resolution_score': self.resolution_score,
            'sharpness': self.sharpness,
            'overconfidence_ratio': self.overconfidence_ratio,
            'underconfidence_ratio': self.underconfidence_ratio,
        }


@dataclass
class CalibrationResult:
    """Result of calibration analysis."""
    result_id: str
    agent_id: str
    status: CalibrationStatus
    metrics: CalibrationMetrics
    adjustment_factor: float
    calibrated_confidence: float
    original_confidence: float
    sample_size: int
    recommendations: List[str]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'result_id': self.result_id,
            'agent_id': self.agent_id,
            'status': self.status.value,
            'metrics': self.metrics.to_dict(),
            'adjustment_factor': self.adjustment_factor,
            'calibrated_confidence': self.calibrated_confidence,
            'original_confidence': self.original_confidence,
            'sample_size': self.sample_size,
            'recommendations': self.recommendations,
            'timestamp': self.timestamp.isoformat(),
        }


@dataclass
class PredictionRecord:
    """Record of a prediction and its outcome."""
    record_id: str
    agent_id: str
    prediction_confidence: float
    actual_outcome: bool
    prediction_type: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'record_id': self.record_id,
            'agent_id': self.agent_id,
            'prediction_confidence': self.prediction_confidence,
            'actual_outcome': self.actual_outcome,
            'prediction_type': self.prediction_type,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata,
        }


class ConfidenceCalibrator:
    """
    Calibrates confidence scores to match actual accuracy.
    
    Provides:
    - Calibration curve analysis
    - Expected calibration error calculation
    - Confidence adjustment recommendations
    - Historical tracking of calibration
    - Agent-specific calibration profiles
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.storage_path = Path(self.config.get('storage_path', 'confidence_calibrator_data'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._prediction_records: Dict[str, List[PredictionRecord]] = {}
        self._calibration_results: Dict[str, CalibrationResult] = {}
        self._agent_profiles: Dict[str, Dict[str, Any]] = {}
        
        self._calibration_config = {
            'minimum_samples': 30,
            'num_bins': 10,
            'ece_threshold_good': 0.05,
            'ece_threshold_acceptable': 0.10,
            'overconfidence_threshold': 0.6,
            'underconfidence_threshold': 0.4,
            'recalibration_interval_hours': 24,
        }
        
        logger.info("✅ Confidence Calibrator initialized")
    
    async def record_prediction(
        self,
        agent_id: str,
        confidence: float,
        outcome: bool,
        prediction_type: str = "general",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PredictionRecord:
        """
        Record a prediction and its outcome.
        
        Args:
            agent_id: ID of the agent making prediction
            confidence: Predicted confidence (0-1)
            outcome: Actual outcome (True/False)
            prediction_type: Type of prediction
            metadata: Additional metadata
        
        Returns:
            PredictionRecord
        """
        record_id = f"PR-{uuid.uuid4().hex[:12]}"
        
        record = PredictionRecord(
            record_id=record_id,
            agent_id=agent_id,
            prediction_confidence=max(0.0, min(1.0, confidence)),
            actual_outcome=outcome,
            prediction_type=prediction_type,
            timestamp=datetime.now(timezone.utc),
            metadata=metadata or {},
        )
        
        if agent_id not in self._prediction_records:
            self._prediction_records[agent_id] = []
        
        self._prediction_records[agent_id].append(record)
        
        if len(self._prediction_records[agent_id]) > 10000:
            self._prediction_records[agent_id] = self._prediction_records[agent_id][-10000:]
        
        return record
    
    async def calibrate_agent(
        self,
        agent_id: str,
        target_confidence: Optional[float] = None,
    ) -> CalibrationResult:
        """
        Calibrate confidence for an agent.
        
        Args:
            agent_id: ID of the agent
            target_confidence: Optional specific confidence to calibrate
        
        Returns:
            CalibrationResult
        """
        result_id = f"CR-{uuid.uuid4().hex[:12]}"
        
        records = self._prediction_records.get(agent_id, [])
        
        if len(records) < self._calibration_config['minimum_samples']:
            return CalibrationResult(
                result_id=result_id,
                agent_id=agent_id,
                status=CalibrationStatus.INSUFFICIENT_DATA,
                metrics=CalibrationMetrics(
                    expected_calibration_error=0.0,
                    maximum_calibration_error=0.0,
                    brier_score=0.0,
                    reliability_score=0.0,
                    resolution_score=0.0,
                    sharpness=0.0,
                    overconfidence_ratio=0.0,
                    underconfidence_ratio=0.0,
                ),
                adjustment_factor=1.0,
                calibrated_confidence=target_confidence or 0.5,
                original_confidence=target_confidence or 0.5,
                sample_size=len(records),
                recommendations=["Collect more prediction data for calibration"],
                timestamp=datetime.now(timezone.utc),
            )
        
        metrics = self._calculate_calibration_metrics(records)
        
        status = self._determine_calibration_status(metrics)
        
        adjustment_factor = self._calculate_adjustment_factor(records, metrics)
        
        original_confidence = target_confidence or self._get_average_confidence(records)
        calibrated_confidence = self._apply_calibration(original_confidence, adjustment_factor, metrics)
        
        recommendations = self._generate_calibration_recommendations(metrics, status)
        
        result = CalibrationResult(
            result_id=result_id,
            agent_id=agent_id,
            status=status,
            metrics=metrics,
            adjustment_factor=adjustment_factor,
            calibrated_confidence=calibrated_confidence,
            original_confidence=original_confidence,
            sample_size=len(records),
            recommendations=recommendations,
            timestamp=datetime.now(timezone.utc),
        )
        
        self._calibration_results[result_id] = result
        self._update_agent_profile(agent_id, result)
        
        await self._persist_result(result)
        
        logger.info(f"Calibration complete for agent {agent_id}: {status.value} "
                   f"(ECE: {metrics.expected_calibration_error:.3f})")
        
        return result
    
    def _calculate_calibration_metrics(
        self,
        records: List[PredictionRecord],
    ) -> CalibrationMetrics:
        """Calculate calibration metrics from prediction records."""
        num_bins = self._calibration_config['num_bins']
        
        bins = [[] for _ in range(num_bins)]
        
        for record in records:
            bin_idx = min(int(record.prediction_confidence * num_bins), num_bins - 1)
            bins[bin_idx].append(record)
        
        ece = 0.0
        mce = 0.0
        total_samples = len(records)
        
        overconfident_count = 0
        underconfident_count = 0
        
        for i, bin_records in enumerate(bins):
            if not bin_records:
                continue
            
            bin_confidence = sum(r.prediction_confidence for r in bin_records) / len(bin_records)
            bin_accuracy = sum(1 for r in bin_records if r.actual_outcome) / len(bin_records)
            
            bin_error = abs(bin_confidence - bin_accuracy)
            bin_weight = len(bin_records) / total_samples
            
            ece += bin_weight * bin_error
            mce = max(mce, bin_error)
            
            if bin_confidence > bin_accuracy:
                overconfident_count += len(bin_records)
            elif bin_confidence < bin_accuracy:
                underconfident_count += len(bin_records)
        
        confidences = [r.prediction_confidence for r in records]
        outcomes = [1 if r.actual_outcome else 0 for r in records]
        
        brier_score = sum((c - o) ** 2 for c, o in zip(confidences, outcomes)) / len(records)
        
        base_rate = sum(outcomes) / len(outcomes)
        
        reliability = 1 - ece
        
        resolution = sum((o - base_rate) ** 2 for o in outcomes) / len(outcomes)
        
        sharpness = sum((c - 0.5) ** 2 for c in confidences) / len(confidences)
        
        overconfidence_ratio = overconfident_count / total_samples if total_samples > 0 else 0
        underconfidence_ratio = underconfident_count / total_samples if total_samples > 0 else 0
        
        return CalibrationMetrics(
            expected_calibration_error=ece,
            maximum_calibration_error=mce,
            brier_score=brier_score,
            reliability_score=reliability,
            resolution_score=resolution,
            sharpness=sharpness,
            overconfidence_ratio=overconfidence_ratio,
            underconfidence_ratio=underconfidence_ratio,
        )
    
    def _determine_calibration_status(
        self,
        metrics: CalibrationMetrics,
    ) -> CalibrationStatus:
        """Determine calibration status from metrics."""
        ece = metrics.expected_calibration_error
        
        if ece <= self._calibration_config['ece_threshold_good']:
            return CalibrationStatus.WELL_CALIBRATED
        
        if metrics.overconfidence_ratio > self._calibration_config['overconfidence_threshold']:
            return CalibrationStatus.OVERCONFIDENT
        
        if metrics.underconfidence_ratio > self._calibration_config['underconfidence_threshold']:
            return CalibrationStatus.UNDERCONFIDENT
        
        if ece <= self._calibration_config['ece_threshold_acceptable']:
            return CalibrationStatus.WELL_CALIBRATED
        
        return CalibrationStatus.POORLY_CALIBRATED
    
    def _calculate_adjustment_factor(
        self,
        records: List[PredictionRecord],
        metrics: CalibrationMetrics,
    ) -> float:
        """Calculate adjustment factor for confidence."""
        if metrics.expected_calibration_error < 0.01:
            return 1.0
        
        avg_confidence = sum(r.prediction_confidence for r in records) / len(records)
        actual_accuracy = sum(1 for r in records if r.actual_outcome) / len(records)
        
        if avg_confidence == 0:
            return 1.0
        
        adjustment = actual_accuracy / avg_confidence
        
        adjustment = max(0.5, min(1.5, adjustment))
        
        return adjustment
    
    def _apply_calibration(
        self,
        confidence: float,
        adjustment_factor: float,
        metrics: CalibrationMetrics,
    ) -> float:
        """Apply calibration to a confidence value."""
        calibrated = confidence * adjustment_factor
        
        calibrated = max(0.01, min(0.99, calibrated))
        
        return calibrated
    
    def _get_average_confidence(self, records: List[PredictionRecord]) -> float:
        """Get average confidence from records."""
        if not records:
            return 0.5
        return sum(r.prediction_confidence for r in records) / len(records)
    
    def _generate_calibration_recommendations(
        self,
        metrics: CalibrationMetrics,
        status: CalibrationStatus,
    ) -> List[str]:
        """Generate recommendations for improving calibration."""
        recommendations = []
        
        if status == CalibrationStatus.OVERCONFIDENT:
            recommendations.append("Reduce confidence levels - predictions are overconfident")
            recommendations.append(f"Consider multiplying confidence by {1/metrics.overconfidence_ratio:.2f}")
        
        if status == CalibrationStatus.UNDERCONFIDENT:
            recommendations.append("Increase confidence levels - predictions are underconfident")
        
        if metrics.expected_calibration_error > 0.1:
            recommendations.append("Implement Platt scaling or isotonic regression for better calibration")
        
        if metrics.sharpness < 0.1:
            recommendations.append("Predictions lack discrimination - improve model to be more decisive")
        
        if metrics.brier_score > 0.25:
            recommendations.append("Overall prediction quality is poor - consider model retraining")
        
        if not recommendations:
            recommendations.append("Calibration is acceptable - continue monitoring")
        
        return recommendations
    
    def _update_agent_profile(self, agent_id: str, result: CalibrationResult):
        """Update agent calibration profile."""
        if agent_id not in self._agent_profiles:
            self._agent_profiles[agent_id] = {
                'calibration_history': [],
                'current_adjustment_factor': 1.0,
                'last_calibrated': None,
            }
        
        profile = self._agent_profiles[agent_id]
        profile['calibration_history'].append({
            'result_id': result.result_id,
            'status': result.status.value,
            'ece': result.metrics.expected_calibration_error,
            'adjustment_factor': result.adjustment_factor,
            'timestamp': result.timestamp.isoformat(),
        })
        
        if len(profile['calibration_history']) > 100:
            profile['calibration_history'] = profile['calibration_history'][-100:]
        
        profile['current_adjustment_factor'] = result.adjustment_factor
        profile['last_calibrated'] = result.timestamp.isoformat()
    
    async def get_calibrated_confidence(
        self,
        agent_id: str,
        raw_confidence: float,
    ) -> float:
        """
        Get calibrated confidence for an agent.
        
        Args:
            agent_id: ID of the agent
            raw_confidence: Raw confidence value
        
        Returns:
            Calibrated confidence
        """
        profile = self._agent_profiles.get(agent_id)
        
        if not profile:
            return raw_confidence
        
        adjustment_factor = profile.get('current_adjustment_factor', 1.0)
        
        calibrated = raw_confidence * adjustment_factor
        calibrated = max(0.01, min(0.99, calibrated))
        
        return calibrated
    
    def get_agent_profile(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get calibration profile for an agent."""
        return self._agent_profiles.get(agent_id)
    
    def get_result(self, result_id: str) -> Optional[CalibrationResult]:
        """Get a calibration result by ID."""
        return self._calibration_results.get(result_id)
    
    async def _persist_result(self, result: CalibrationResult):
        """Persist result to storage."""
        result_file = self.storage_path / 'results' / f"{result.result_id}.json"
        result_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(result_file, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get calibrator statistics."""
        total_records = sum(len(records) for records in self._prediction_records.values())
        
        status_counts = {}
        for result in self._calibration_results.values():
            status_counts[result.status.value] = status_counts.get(result.status.value, 0) + 1
        
        return {
            'total_agents': len(self._prediction_records),
            'total_prediction_records': total_records,
            'total_calibrations': len(self._calibration_results),
            'calibrations_by_status': status_counts,
            'agents_with_profiles': len(self._agent_profiles),
        }
