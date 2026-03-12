"""
AlphaAlgo Core - Continuous Validity Monitor (Layer 6)

Monitors live behavior vs expected behavior:
- Tracks prediction vs reality deviation
- Monitors for silent drift
- Detects assumption violations in real-time
- Enforces kill switch without human intervention

If deviation exceeds threshold → strategy is frozen.
No exceptions, no overrides.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd

from .capital_governance import (
    GovernanceLayer,
    ValidationMonitorResult,
    ValidationState,
    ValidationError
)

logger = logging.getLogger(__name__)


class DeviationType(Enum):
    """Types of deviations to monitor"""
    PREDICTION_ERROR = "prediction_error"
    SILENT_DRIFT = "silent_drift"
    ASSUMPTION_VIOLATION = "assumption_violation"
    BEHAVIOR_ANOMALY = "behavior_anomaly"


class ContinuousValidityMonitor(GovernanceLayer):
    """
    Layer 6 - Continuous Validity Monitor
    
    Continuously monitors strategies for deviations from expected behavior.
    Can automatically freeze strategies that exceed deviation thresholds.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("continuous_validity_monitor")
        self.config = config or {}
        
        # Deviation thresholds
        self.thresholds = {
            "prediction_error_threshold": self.config.get("prediction_error_threshold", 2.5),  # Z-score threshold
            "drift_threshold": self.config.get("drift_threshold", 0.3),  # Drift magnitude threshold
            "assumption_violation_threshold": self.config.get("assumption_violation_threshold", 0.7),  # Violation severity threshold
            "behavior_anomaly_threshold": self.config.get("behavior_anomaly_threshold", 0.8),  # Anomaly score threshold
            "overall_deviation_threshold": self.config.get("overall_deviation_threshold", 50.0),  # Overall deviation threshold (0-100)
        }
        
        # Frozen strategies registry
        self.frozen_strategies = set()
        
        # Load previously frozen strategies if available
        self._load_frozen_strategies()
        
        # Strategy behavior history
        self.behavior_history = {}
        
        # Deviation detectors
        self.deviation_detectors = {
            DeviationType.PREDICTION_ERROR: self._detect_prediction_error,
            DeviationType.SILENT_DRIFT: self._detect_silent_drift,
            DeviationType.ASSUMPTION_VIOLATION: self._detect_assumption_violation,
            DeviationType.BEHAVIOR_ANOMALY: self._detect_behavior_anomaly
        }
        
        logger.info(f"Continuous Validity Monitor initialized with thresholds: {self.thresholds}")
    
    def _load_frozen_strategies(self):
        """Load previously frozen strategies"""
        try:
            # Try to load from file
            frozen_path = self.config.get("frozen_strategies_path", "frozen_strategies.json")
            with open(frozen_path, 'r') as f:
                self.frozen_strategies = set(json.load(f))
            logger.info(f"Loaded {len(self.frozen_strategies)} frozen strategies")
        except (FileNotFoundError, json.JSONDecodeError):
            # If file doesn't exist or is invalid, start with empty set
            self.frozen_strategies = set()
            logger.info("No existing frozen strategies found, starting fresh")
    
    def _save_frozen_strategies(self):
        """Save frozen strategies to persistent storage"""
        try:
            # Save to file
            frozen_path = self.config.get("frozen_strategies_path", "frozen_strategies.json")
            with open(frozen_path, 'w') as f:
                json.dump(list(self.frozen_strategies), f)
            logger.info(f"Saved {len(self.frozen_strategies)} frozen strategies")
        except Exception as e:
            logger.error(f"Error saving frozen strategies: {e}")
    
    def freeze_strategy(self, strategy_id: str, reason: str):
        """
        Freeze a strategy due to validity concerns.
        
        This is an irreversible action - frozen strategies remain frozen.
        """
        if strategy_id not in self.frozen_strategies:
            self.frozen_strategies.add(strategy_id)
            logger.warning(f"Strategy {strategy_id} FROZEN: {reason}")
            self._save_frozen_strategies()
    
    def update_behavior_history(self, strategy_id: str, behavior_data: Dict[str, Any]):
        """
        Update the behavior history for a strategy.
        
        Args:
            strategy_id: Unique identifier for the strategy
            behavior_data: Dictionary of behavior metrics
        """
        if strategy_id not in self.behavior_history:
            self.behavior_history[strategy_id] = []
        
        # Add timestamp if not present
        if "timestamp" not in behavior_data:
            behavior_data["timestamp"] = time.time()
        
        self.behavior_history[strategy_id].append(behavior_data)
        
        # Limit history size
        max_history = 1000
        if len(self.behavior_history[strategy_id]) > max_history:
            self.behavior_history[strategy_id] = self.behavior_history[strategy_id][-max_history:]
    
    async def process(
        self,
        strategy_id: str,
        strategy_config: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> ValidationMonitorResult:
        """
        Process a strategy to validate its behavior against expectations.
        
        Args:
            strategy_id: Unique identifier for the strategy
            strategy_config: Strategy configuration
            market_data: Current market data
            
        Returns:
            ValidationMonitorResult with validity determination
        """
        try:
            # Check if strategy is already frozen
            if strategy_id in self.frozen_strategies:
                return ValidationMonitorResult(
                    strategy_id=strategy_id,
                    state=ValidationState.FROZEN,
                    deviation=100.0,  # Maximum deviation for frozen strategies
                    is_valid=False,
                    reason="Strategy previously frozen due to validity concerns",
                    metrics={}
                )
            
            # Extract behavior data from market data
            behavior_data = self._extract_behavior_data(strategy_id, strategy_config, market_data)
            
            # Update behavior history
            self.update_behavior_history(strategy_id, behavior_data)
            
            # Check for deviations
            deviations = []
            deviation_metrics = {}
            
            for deviation_type in DeviationType:
                detector = self.deviation_detectors.get(deviation_type)
                if detector:
                    is_deviation, score, details = await detector(
                        strategy_id, strategy_config, market_data, behavior_data
                    )
                    
                    if is_deviation:
                        deviations.append((deviation_type, score, details))
                    
                    # Store deviation score in metrics
                    deviation_metrics[f"{deviation_type.value}_score"] = score
            
            # Calculate overall deviation
            overall_deviation = self._calculate_overall_deviation(deviations)
            deviation_metrics["overall_deviation"] = overall_deviation
            
            # Determine if strategy is valid
            is_valid = overall_deviation < self.thresholds["overall_deviation_threshold"]
            
            # Determine state
            if not is_valid:
                # Freeze the strategy if it exceeds the threshold
                reason_details = "; ".join([f"{d[0].value}: {d[2]}" for d in deviations if d[0]])
                freeze_reason = f"Deviation threshold exceeded: {overall_deviation:.1f} > {self.thresholds['overall_deviation_threshold']:.1f}. Details: {reason_details}"
                self.freeze_strategy(strategy_id, freeze_reason)
                
                return ValidationMonitorResult(
                    strategy_id=strategy_id,
                    state=ValidationState.FROZEN,
                    deviation=overall_deviation,
                    is_valid=False,
                    reason=freeze_reason,
                    metrics=deviation_metrics
                )
            elif deviations:
                # Strategy has deviations but not enough to freeze
                reason_details = "; ".join([f"{d[0].value}: {d[2]}" for d in deviations if d[0]])
                return ValidationMonitorResult(
                    strategy_id=strategy_id,
                    state=ValidationState.INVALID,
                    deviation=overall_deviation,
                    is_valid=False,
                    reason=f"Validity concerns detected: {reason_details}",
                    metrics=deviation_metrics
                )
            else:
                # Strategy is valid
                return ValidationMonitorResult(
                    strategy_id=strategy_id,
                    state=ValidationState.VALID,
                    deviation=overall_deviation,
                    is_valid=True,
                    reason="Strategy behavior within expected parameters",
                    metrics=deviation_metrics
                )
            
        except Exception as e:
            logger.exception(f"Error in continuous validity monitor: {e}")
            return ValidationMonitorResult(
                strategy_id=strategy_id,
                state=ValidationState.UNKNOWN,
                deviation=100.0,  # Maximum deviation on error
                is_valid=False,
                reason=f"Error in validity monitoring: {str(e)}",
                metrics={}
            )
    
    def _extract_behavior_data(
        self,
        strategy_id: str,
        strategy_config: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract behavior data from market data.
        
        Returns a dictionary of behavior metrics.
        """
        behavior_data = {}
        
        # Extract prediction data if available
        if "predictions" in market_data:
            behavior_data["predictions"] = market_data["predictions"]
        
        # Extract actual outcomes if available
        if "actuals" in market_data:
            behavior_data["actuals"] = market_data["actuals"]
        
        # Extract performance metrics if available
        if "performance" in market_data:
            behavior_data["performance"] = market_data["performance"]
        
        # Extract strategy-specific metrics if available
        if "strategy_metrics" in market_data and strategy_id in market_data["strategy_metrics"]:
            behavior_data["strategy_metrics"] = market_data["strategy_metrics"][strategy_id]
        
        # Extract assumption metrics if available
        if "assumptions" in market_data:
            behavior_data["assumptions"] = market_data["assumptions"]
        
        # Add timestamp
        behavior_data["timestamp"] = time.time()
        
        return behavior_data
    
    def _calculate_overall_deviation(self, deviations: List[Tuple[DeviationType, float, str]]) -> float:
        """
        Calculate overall deviation score from individual deviations.
        
        Returns a float between 0 and 100, where higher values indicate more deviation.
        """
        if not deviations:
            return 0.0
        
        # Weights for different deviation types
        weights = {
            DeviationType.PREDICTION_ERROR: 0.25,
            DeviationType.SILENT_DRIFT: 0.25,
            DeviationType.ASSUMPTION_VIOLATION: 0.3,
            DeviationType.BEHAVIOR_ANOMALY: 0.2
        }
        
        # Calculate weighted average
        total_weight = 0.0
        weighted_sum = 0.0
        
        for deviation_type, score, _ in deviations:
            weight = weights.get(deviation_type, 0.0)
            weighted_sum += score * weight
            total_weight += weight
        
        if total_weight > 0:
            return (weighted_sum / total_weight) * 100.0
        else:
            return 0.0
    
    # === Deviation detectors ===
    
    async def _detect_prediction_error(
        self,
        strategy_id: str,
        strategy_config: Dict[str, Any],
        market_data: Dict[str, Any],
        behavior_data: Dict[str, Any]
    ) -> Tuple[bool, float, str]:
        """
        Detect prediction errors (difference between predicted and actual outcomes).
        
        Returns a tuple of (is_deviation, score, details).
        """
        # Check if we have prediction and actual data
        if "predictions" not in behavior_data or "actuals" not in behavior_data:
            return False, 0.0, ""
        
        predictions = behavior_data["predictions"]
        actuals = behavior_data["actuals"]
        
        # Check if we have compatible data structures
        if not isinstance(predictions, dict) or not isinstance(actuals, dict):
            return False, 0.0, ""
        
        # Calculate prediction errors
        errors = []
        
        for key in predictions:
            if key in actuals:
                pred = predictions[key]
                actual = actuals[key]
                
                if isinstance(pred, (int, float)) and isinstance(actual, (int, float)):
                    # Calculate relative error
                    if abs(actual) > 1e-10:
                        error = abs((pred - actual) / actual)
                    else:
                        error = abs(pred - actual)
                    
                    errors.append(error)
        
        if not errors:
            return False, 0.0, ""
        
        # Calculate average error
        avg_error = sum(errors) / len(errors)
        
        # Get historical errors for this strategy
        historical_errors = []
        
        if strategy_id in self.behavior_history:
            for history_item in self.behavior_history[strategy_id]:
                if "prediction_error" in history_item:
                    historical_errors.append(history_item["prediction_error"])
        
        # Calculate z-score if we have enough history
        if len(historical_errors) >= 10:
            error_mean = np.mean(historical_errors)
            error_std = np.std(historical_errors)
            
            if error_std > 0:
                z_score = (avg_error - error_mean) / error_std
                
                # Check if z-score exceeds threshold
                threshold = self.thresholds["prediction_error_threshold"]
                if z_score > threshold:
                    return True, z_score, f"Prediction error z-score {z_score:.2f} exceeds threshold {threshold:.2f}"
        
        # If we don't have enough history, check if error is very large
        elif avg_error > 0.5:  # 50% error is very large
            return True, avg_error * 5, f"Large prediction error: {avg_error:.2f} (50%+ error)"
        
        # Store current error in behavior data for future reference
        behavior_data["prediction_error"] = avg_error
        
        return False, avg_error, ""
    
    async def _detect_silent_drift(
        self,
        strategy_id: str,
        strategy_config: Dict[str, Any],
        market_data: Dict[str, Any],
        behavior_data: Dict[str, Any]
    ) -> Tuple[bool, float, str]:
        """
        Detect silent drift (gradual changes in behavior over time).
        
        Returns a tuple of (is_deviation, score, details).
        """
        # Need sufficient history to detect drift
        if strategy_id not in self.behavior_history or len(self.behavior_history[strategy_id]) < 20:
            return False, 0.0, ""
        
        # Get historical behavior
        history = self.behavior_history[strategy_id]
        
        # Check for performance drift
        if "performance" in behavior_data:
            perf_history = [h.get("performance", {}).get("return", 0) for h in history if "performance" in h]
            
            if len(perf_history) >= 20:
                # Calculate trend using linear regression
                x = np.arange(len(perf_history))
                y = np.array(perf_history)
                
                # Simple linear regression
                slope = np.polyfit(x, y, 1)[0]
                
                # Normalize slope by average performance
                avg_perf = np.mean(np.abs(y))
                if avg_perf > 1e-10:
                    norm_slope = slope / avg_perf
                else:
                    norm_slope = slope
                
                # Check if normalized slope indicates drift
                threshold = self.thresholds["drift_threshold"]
                if abs(norm_slope) > threshold:
                    drift_direction = "upward" if norm_slope > 0 else "downward"
                    return True, abs(norm_slope), f"Performance showing {drift_direction} drift: {abs(norm_slope):.4f} > {threshold:.4f}"
        
        # Check for prediction error drift
        error_history = [h.get("prediction_error", 0) for h in history if "prediction_error" in h]
        
        if len(error_history) >= 20:
            # Calculate trend using linear regression
            x = np.arange(len(error_history))
            y = np.array(error_history)
            
            # Simple linear regression
            slope = np.polyfit(x, y, 1)[0]
            
            # Check if slope indicates increasing errors
            threshold = self.thresholds["drift_threshold"] / 2  # Lower threshold for error drift
            if slope > threshold:
                return True, slope * 2, f"Prediction errors showing upward drift: {slope:.4f} > {threshold:.4f}"
        
        # Check for behavior metric drift
        if "strategy_metrics" in behavior_data:
            metrics = behavior_data["strategy_metrics"]
            
            for metric_name, metric_value in metrics.items():
                if not isinstance(metric_value, (int, float)):
                    continue
                
                # Get history for this metric
                metric_history = [
                    h.get("strategy_metrics", {}).get(metric_name, None) 
                    for h in history 
                    if "strategy_metrics" in h and metric_name in h["strategy_metrics"]
                ]
                
                # Filter out None values
                metric_history = [m for m in metric_history if m is not None]
                
                if len(metric_history) >= 20:
                    # Calculate trend using linear regression
                    x = np.arange(len(metric_history))
                    y = np.array(metric_history)
                    
                    # Simple linear regression
                    slope = np.polyfit(x, y, 1)[0]
                    
                    # Normalize slope by average metric value
                    avg_metric = np.mean(np.abs(y))
                    if avg_metric > 1e-10:
                        norm_slope = slope / avg_metric
                    else:
                        norm_slope = slope
                    
                    # Check if normalized slope indicates drift
                    threshold = self.thresholds["drift_threshold"]
                    if abs(norm_slope) > threshold:
                        drift_direction = "upward" if norm_slope > 0 else "downward"
                        return True, abs(norm_slope), f"Metric '{metric_name}' showing {drift_direction} drift: {abs(norm_slope):.4f} > {threshold:.4f}"
        
        return False, 0.0, ""
    
    async def _detect_assumption_violation(
        self,
        strategy_id: str,
        strategy_config: Dict[str, Any],
        market_data: Dict[str, Any],
        behavior_data: Dict[str, Any]
    ) -> Tuple[bool, float, str]:
        """
        Detect assumption violations (when strategy assumptions are no longer valid).
        
        Returns a tuple of (is_deviation, score, details).
        """
        # Check if we have assumption data
        if "assumptions" not in behavior_data:
            return False, 0.0, ""
        
        assumptions = behavior_data["assumptions"]
        
        # Check if we have strategy assumptions defined
        if "assumptions" not in strategy_config:
            return False, 0.0, ""
        
        strategy_assumptions = strategy_config["assumptions"]
        
        # Check for violations
        violations = []
        
        for assumption_name, assumption_details in strategy_assumptions.items():
            if assumption_name in assumptions:
                # Get current value
                current_value = assumptions[assumption_name]
                
                # Get threshold
                threshold = assumption_details.get("threshold", 0.5)
                
                # Check if assumption is violated
                is_violated = False
                violation_severity = 0.0
                
                if "direction" in assumption_details:
                    direction = assumption_details["direction"]
                    
                    if direction == "above" and current_value < threshold:
                        is_violated = True
                        violation_severity = (threshold - current_value) / threshold
                    elif direction == "below" and current_value > threshold:
                        is_violated = True
                        violation_severity = (current_value - threshold) / threshold
                else:
                    # Default: assume value should be above threshold
                    if current_value < threshold:
                        is_violated = True
                        violation_severity = (threshold - current_value) / threshold
                
                if is_violated:
                    violations.append((assumption_name, violation_severity))
        
        if not violations:
            return False, 0.0, ""
        
        # Calculate maximum violation severity
        max_violation = max(violations, key=lambda x: x[1])
        max_assumption_name = max_violation[0]
        max_severity = max_violation[1]
        
        # Check if severity exceeds threshold
        threshold = self.thresholds["assumption_violation_threshold"]
        if max_severity > threshold:
            return True, max_severity, f"Assumption '{max_assumption_name}' violated with severity {max_severity:.2f} > {threshold:.2f}"
        
        return False, max_severity, ""
    
    async def _detect_behavior_anomaly(
        self,
        strategy_id: str,
        strategy_config: Dict[str, Any],
        market_data: Dict[str, Any],
        behavior_data: Dict[str, Any]
    ) -> Tuple[bool, float, str]:
        """
        Detect behavior anomalies (unusual patterns in strategy behavior).
        
        Returns a tuple of (is_deviation, score, details).
        """
        # Need sufficient history to detect anomalies
        if strategy_id not in self.behavior_history or len(self.behavior_history[strategy_id]) < 20:
            return False, 0.0, ""
        
        # Get historical behavior
        history = self.behavior_history[strategy_id]
        
        # Check for performance anomalies
        if "performance" in behavior_data:
            current_perf = behavior_data["performance"].get("return", 0)
            perf_history = [h.get("performance", {}).get("return", 0) for h in history[-20:] if "performance" in h]
            
            if len(perf_history) >= 10:
                # Calculate mean and standard deviation
                perf_mean = np.mean(perf_history)
                perf_std = np.std(perf_history)
                
                if perf_std > 0:
                    # Calculate z-score
                    z_score = abs((current_perf - perf_mean) / perf_std)
                    
                    # Check if z-score indicates anomaly
                    if z_score > 3.0:  # 3 sigma event
                        anomaly_score = min(1.0, z_score / 6.0)  # Normalize to 0-1
                        threshold = self.thresholds["behavior_anomaly_threshold"]
                        if anomaly_score > threshold:
                            return True, anomaly_score, f"Performance anomaly detected: z-score {z_score:.2f}, anomaly score {anomaly_score:.2f} > {threshold:.2f}"
        
        # Check for strategy metric anomalies
        if "strategy_metrics" in behavior_data:
            metrics = behavior_data["strategy_metrics"]
            
            for metric_name, metric_value in metrics.items():
                if not isinstance(metric_value, (int, float)):
                    continue
                
                # Get history for this metric
                metric_history = [
                    h.get("strategy_metrics", {}).get(metric_name, None) 
                    for h in history[-20:] 
                    if "strategy_metrics" in h and metric_name in h["strategy_metrics"]
                ]
                
                # Filter out None values
                metric_history = [m for m in metric_history if m is not None]
                
                if len(metric_history) >= 10:
                    # Calculate mean and standard deviation
                    metric_mean = np.mean(metric_history)
                    metric_std = np.std(metric_history)
                    
                    if metric_std > 0:
                        # Calculate z-score
                        z_score = abs((metric_value - metric_mean) / metric_std)
                        
                        # Check if z-score indicates anomaly
                        if z_score > 3.0:  # 3 sigma event
                            anomaly_score = min(1.0, z_score / 6.0)  # Normalize to 0-1
                            threshold = self.thresholds["behavior_anomaly_threshold"]
                            if anomaly_score > threshold:
                                return True, anomaly_score, f"Metric '{metric_name}' anomaly detected: z-score {z_score:.2f}, anomaly score {anomaly_score:.2f} > {threshold:.2f}"
        
        # Check for prediction pattern anomalies
        if "predictions" in behavior_data and "actuals" in behavior_data:
            predictions = behavior_data["predictions"]
            actuals = behavior_data["actuals"]
            
            # Check for sign errors (predicted up but went down or vice versa)
            sign_errors = 0
            total_predictions = 0
            
            for key in predictions:
                if key in actuals:
                    pred = predictions[key]
                    actual = actuals[key]
                    
                    if isinstance(pred, (int, float)) and isinstance(actual, (int, float)):
                        total_predictions += 1
                        if (pred > 0 and actual < 0) or (pred < 0 and actual > 0):
                            sign_errors += 1
            
            if total_predictions > 0:
                sign_error_rate = sign_errors / total_predictions
                
                # Check historical sign error rates
                historical_sign_error_rates = []
                
                for h in history:
                    if "sign_error_rate" in h:
                        historical_sign_error_rates.append(h["sign_error_rate"])
                
                if len(historical_sign_error_rates) >= 10:
                    # Calculate mean and standard deviation
                    rate_mean = np.mean(historical_sign_error_rates)
                    rate_std = np.std(historical_sign_error_rates)
                    
                    if rate_std > 0:
                        # Calculate z-score
                        z_score = (sign_error_rate - rate_mean) / rate_std
                        
                        # Check if z-score indicates anomaly
                        if z_score > 2.0:  # 2 sigma event for sign errors
                            anomaly_score = min(1.0, z_score / 4.0)  # Normalize to 0-1
                            threshold = self.thresholds["behavior_anomaly_threshold"]
                            if anomaly_score > threshold:
                                return True, anomaly_score, f"Sign error rate anomaly detected: {sign_error_rate:.2f}, z-score {z_score:.2f}, anomaly score {anomaly_score:.2f} > {threshold:.2f}"
                
                # Store current sign error rate in behavior data
                behavior_data["sign_error_rate"] = sign_error_rate
        
        return False, 0.0, ""
