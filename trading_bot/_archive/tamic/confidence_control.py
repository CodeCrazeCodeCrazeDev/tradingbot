"""
Confidence and Humility Controls for TAMIC

This module implements confidence calibration and uncertainty handling focusing on:
1. Overconfidence detection - Identifying and penalizing overconfidence
2. Confidence calibration - Ensuring confidence matches historical accuracy
3. Uncertainty quantification - Properly accounting for uncertainty
4. Win streak adjustment - Reducing confidence after win streaks
5. Humility enforcement - Ensuring appropriate humility in predictions

The primary goal is to ensure that confidence levels accurately reflect
true predictive ability and prevent overconfidence.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import numpy as np
import pandas as pd

from .core import TimeHorizon, MarketTimeState

logger = logging.getLogger(__name__)


class ConfidenceCalibration(Enum):
    """Confidence calibration status"""
    WELL_CALIBRATED = "well_calibrated"  # Confidence matches historical accuracy
    OVERCONFIDENT = "overconfident"  # Confidence exceeds historical accuracy
    UNDERCONFIDENT = "underconfident"  # Confidence below historical accuracy
    UNKNOWN = "unknown"  # Insufficient data for calibration


class UncertaintyLevel(Enum):
    """Level of uncertainty in prediction"""
    LOW = "low"  # Low uncertainty
    MODERATE = "moderate"  # Moderate uncertainty
    HIGH = "high"  # High uncertainty
    EXTREME = "extreme"  # Extreme uncertainty


@dataclass
class ConfidenceMetrics:
    """Metrics related to confidence calibration"""
    raw_confidence: float = 0.0  # Raw confidence score (0-1)
    calibrated_confidence: float = 0.0  # Calibrated confidence score (0-1)
    historical_accuracy: float = 0.0  # Historical accuracy (0-1)
    calibration_error: float = 0.0  # Calibration error (0-1)
    uncertainty: float = 0.0  # Uncertainty level (0-1)
    win_streak_length: int = 0  # Length of current win streak
    loss_streak_length: int = 0  # Length of current loss streak
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConfidenceResult:
    """Result from confidence calibration"""
    calibrated_confidence: float  # Calibrated confidence score (0-1)
    calibration_status: ConfidenceCalibration  # Confidence calibration status
    uncertainty_level: UncertaintyLevel  # Level of uncertainty
    metrics: ConfidenceMetrics  # Detailed confidence metrics
    timestamp: float = field(default_factory=time.time)


class ConfidenceHumilityControl:
    """
    Control system for confidence calibration and humility enforcement.
    
    Ensures that confidence levels accurately reflect true predictive ability
    and prevents overconfidence.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize ConfidenceHumilityControl.
        
        Args:
            config: Configuration parameters
        """
        self.config = config or {}
        self.logger = logging.getLogger("trading_bot.tamic.confidence_control")
        
        # Performance history
        self.performance_history = {}  # Symbol -> {horizon -> history}
        
        # Calibration thresholds
        self.calibration_thresholds = self.config.get("calibration_thresholds", {
            "overconfident": 0.1,  # Confidence exceeds accuracy by this much
            "underconfident": -0.1,  # Confidence below accuracy by this much
        })
        
        # Uncertainty thresholds
        self.uncertainty_thresholds = self.config.get("uncertainty_thresholds", {
            UncertaintyLevel.LOW: 0.2,
            UncertaintyLevel.MODERATE: 0.4,
            UncertaintyLevel.HIGH: 0.6,
            UncertaintyLevel.EXTREME: 0.8,
        })
        
        # Win streak settings
        self.win_streak_confidence_reduction = self.config.get("win_streak_confidence_reduction", 0.05)
        self.win_streak_threshold = self.config.get("win_streak_threshold", 3)  # Threshold for win streak adjustment
        
        # Loss streak settings
        self.loss_streak_confidence_boost = self.config.get("loss_streak_confidence_boost", 0.03)
        self.loss_streak_threshold = self.config.get("loss_streak_threshold", 3)  # Threshold for loss streak adjustment
        
        # Overconfidence penalty
        self.overconfidence_penalty = self.config.get("overconfidence_penalty", 0.3)
        
        # Minimum required samples for calibration
        self.min_samples = self.config.get("min_samples", 10)
    
    def _initialize_performance_history(self, symbol: str, horizon: TimeHorizon):
        """Initialize performance history for a symbol and horizon"""
        if symbol not in self.performance_history:
            self.performance_history[symbol] = {}
        
        if horizon not in self.performance_history[symbol]:
            self.performance_history[symbol][horizon] = {
                "predictions": [],  # List of prediction confidences
                "outcomes": [],  # List of outcomes (True/False)
                "win_streak": 0,  # Current win streak
                "loss_streak": 0,  # Current loss streak
                "accuracy": 0.0,  # Historical accuracy
            }
    
    def _calculate_historical_accuracy(self, symbol: str, horizon: TimeHorizon) -> float:
        """
        Calculate historical accuracy for a symbol and horizon.
        
        Args:
            symbol: Market symbol
            horizon: Time horizon
            
        Returns:
            Historical accuracy (0-1)
        """
        self._initialize_performance_history(symbol, horizon)
        history = self.performance_history[symbol][horizon]
        
        if not history["outcomes"]:
            return 0.5  # Default to 0.5 if no history
        
        # Calculate accuracy
        accuracy = sum(history["outcomes"]) / len(history["outcomes"])
        
        return accuracy
    
    def _calculate_calibration_error(
        self,
        confidence: float,
        historical_accuracy: float
    ) -> float:
        """
        Calculate calibration error.
        
        Args:
            confidence: Confidence score (0-1)
            historical_accuracy: Historical accuracy (0-1)
            
        Returns:
            Calibration error (0-1)
        """
        return confidence - historical_accuracy
    
    def _get_calibration_status(self, calibration_error: float) -> ConfidenceCalibration:
        """
        Get calibration status based on calibration error.
        
        Args:
            calibration_error: Calibration error (0-1)
            
        Returns:
            ConfidenceCalibration status
        """
        if calibration_error > self.calibration_thresholds["overconfident"]:
            return ConfidenceCalibration.OVERCONFIDENT
        elif calibration_error < self.calibration_thresholds["underconfident"]:
            return ConfidenceCalibration.UNDERCONFIDENT
        else:
            return ConfidenceCalibration.WELL_CALIBRATED
    
    def _calculate_uncertainty(
        self,
        symbol: str,
        horizon: TimeHorizon,
        market_data: Dict[str, Any]
    ) -> Tuple[UncertaintyLevel, float]:
        """
        Calculate uncertainty level.
        
        Args:
            symbol: Market symbol
            horizon: Time horizon
            market_data: Market data dictionary
            
        Returns:
            Tuple of (uncertainty_level, uncertainty_value)
        """
        # This would typically be a more sophisticated analysis
        # For now, we'll use a simple approach based on volatility and market regime
        
        # Default uncertainty - moderate
        uncertainty_value = 0.4
        
        # If we have volatility data, adjust based on volatility
        if "volatility" in market_data:
            volatility = market_data["volatility"]
            if isinstance(volatility, (int, float)):
                # Higher volatility = higher uncertainty
                if volatility > 0.03:  # 3% daily volatility
                    uncertainty_value += 0.3
                elif volatility > 0.02:  # 2% daily volatility
                    uncertainty_value += 0.2
                elif volatility > 0.01:  # 1% daily volatility
                    uncertainty_value += 0.1
        
        # If we have market regime data, adjust based on regime
        if "market_regime" in market_data:
            regime = market_data["market_regime"]
            if isinstance(regime, str):
                # Different regimes have different uncertainty levels
                if regime.lower() in ["volatile", "high_volatility"]:
                    uncertainty_value += 0.2
                elif regime.lower() in ["trending", "strong_trend"]:
                    uncertainty_value -= 0.1
                elif regime.lower() in ["ranging", "sideways"]:
                    uncertainty_value += 0.1
        
        # If we have correlation data, adjust based on correlation stability
        if "correlation_stability" in market_data:
            stability = market_data["correlation_stability"]
            if isinstance(stability, (int, float)):
                # Lower stability = higher uncertainty
                if stability < 0.3:
                    uncertainty_value += 0.2
                elif stability < 0.5:
                    uncertainty_value += 0.1
        
        # Cap between 0 and 1
        uncertainty_value = max(0.0, min(1.0, uncertainty_value))
        
        # Determine uncertainty level
        if uncertainty_value >= self.uncertainty_thresholds[UncertaintyLevel.EXTREME]:
            uncertainty_level = UncertaintyLevel.EXTREME
        elif uncertainty_value >= self.uncertainty_thresholds[UncertaintyLevel.HIGH]:
            uncertainty_level = UncertaintyLevel.HIGH
        elif uncertainty_value >= self.uncertainty_thresholds[UncertaintyLevel.MODERATE]:
            uncertainty_level = UncertaintyLevel.MODERATE
        else:
            uncertainty_level = UncertaintyLevel.LOW
        
        return uncertainty_level, uncertainty_value
    
    def _adjust_for_win_streak(
        self,
        confidence: float,
        win_streak: int
    ) -> float:
        """
        Adjust confidence for win streak.
        
        Args:
            confidence: Confidence score (0-1)
            win_streak: Length of win streak
            
        Returns:
            Adjusted confidence (0-1)
        """
        if win_streak >= self.win_streak_threshold:
            # Calculate reduction based on streak length
            streak_factor = min(5, win_streak - self.win_streak_threshold + 1)  # Cap at 5
            reduction = self.win_streak_confidence_reduction * streak_factor
            
            # Apply reduction
            adjusted_confidence = max(0.1, confidence - reduction)
            
            self.logger.info(f"Win streak of {win_streak}: Reducing confidence from {confidence:.2f} to {adjusted_confidence:.2f}")
            
            return adjusted_confidence
        
        return confidence
    
    def _adjust_for_loss_streak(
        self,
        confidence: float,
        loss_streak: int
    ) -> float:
        """
        Adjust confidence for loss streak.
        
        Args:
            confidence: Confidence score (0-1)
            loss_streak: Length of loss streak
            
        Returns:
            Adjusted confidence (0-1)
        """
        if loss_streak >= self.loss_streak_threshold:
            # Calculate boost based on streak length
            streak_factor = min(5, loss_streak - self.loss_streak_threshold + 1)  # Cap at 5
            boost = self.loss_streak_confidence_boost * streak_factor
            
            # Apply boost
            adjusted_confidence = min(0.9, confidence + boost)
            
            self.logger.info(f"Loss streak of {loss_streak}: Boosting confidence from {confidence:.2f} to {adjusted_confidence:.2f}")
            
            return adjusted_confidence
        
        return confidence
    
    def _adjust_for_calibration(
        self,
        confidence: float,
        calibration_status: ConfidenceCalibration,
        calibration_error: float
    ) -> float:
        """
        Adjust confidence based on calibration status.
        
        Args:
            confidence: Confidence score (0-1)
            calibration_status: Calibration status
            calibration_error: Calibration error (0-1)
            
        Returns:
            Adjusted confidence (0-1)
        """
        if calibration_status == ConfidenceCalibration.OVERCONFIDENT:
            # Apply overconfidence penalty
            penalty = min(self.overconfidence_penalty, abs(calibration_error))
            adjusted_confidence = max(0.1, confidence - penalty)
            
            self.logger.info(f"Overconfident: Reducing confidence from {confidence:.2f} to {adjusted_confidence:.2f}")
            
            return adjusted_confidence
        elif calibration_status == ConfidenceCalibration.UNDERCONFIDENT:
            # Apply underconfidence boost
            boost = min(0.2, abs(calibration_error))
            adjusted_confidence = min(0.9, confidence + boost)
            
            self.logger.info(f"Underconfident: Boosting confidence from {confidence:.2f} to {adjusted_confidence:.2f}")
            
            return adjusted_confidence
        
        return confidence
    
    def _adjust_for_uncertainty(
        self,
        confidence: float,
        uncertainty_level: UncertaintyLevel,
        uncertainty_value: float
    ) -> float:
        """
        Adjust confidence based on uncertainty level.
        
        Args:
            confidence: Confidence score (0-1)
            uncertainty_level: Uncertainty level
            uncertainty_value: Uncertainty value (0-1)
            
        Returns:
            Adjusted confidence (0-1)
        """
        if uncertainty_level == UncertaintyLevel.EXTREME:
            # Extreme uncertainty - cap confidence
            max_confidence = 0.6
            if confidence > max_confidence:
                self.logger.info(f"Extreme uncertainty: Capping confidence at {max_confidence:.2f}")
                return max_confidence
        elif uncertainty_level == UncertaintyLevel.HIGH:
            # High uncertainty - cap confidence
            max_confidence = 0.75
            if confidence > max_confidence:
                self.logger.info(f"High uncertainty: Capping confidence at {max_confidence:.2f}")
                return max_confidence
        elif uncertainty_level == UncertaintyLevel.MODERATE:
            # Moderate uncertainty - slight reduction
            reduction = uncertainty_value * 0.1
            adjusted_confidence = max(0.1, confidence - reduction)
            
            if adjusted_confidence < confidence:
                self.logger.info(f"Moderate uncertainty: Reducing confidence from {confidence:.2f} to {adjusted_confidence:.2f}")
                
                return adjusted_confidence
        
        return confidence
    
    def record_outcome(
        self,
        symbol: str,
        horizon: TimeHorizon,
        prediction_confidence: float,
        outcome: bool
    ):
        """
        Record prediction outcome for a symbol and horizon.
        
        Args:
            symbol: Market symbol
            horizon: Time horizon
            prediction_confidence: Confidence of prediction (0-1)
            outcome: Whether prediction was correct (True/False)
        """
        self._initialize_performance_history(symbol, horizon)
        history = self.performance_history[symbol][horizon]
        
        # Add to history
        history["predictions"].append(prediction_confidence)
        history["outcomes"].append(outcome)
        
        # Update win/loss streak
        if outcome:
            history["win_streak"] += 1
            history["loss_streak"] = 0
        else:
            history["win_streak"] = 0
            history["loss_streak"] += 1
        
        # Update accuracy
        history["accuracy"] = sum(history["outcomes"]) / len(history["outcomes"])
        
        # Keep limited history
        max_history = 100
        if len(history["predictions"]) > max_history:
            history["predictions"] = history["predictions"][-max_history:]
            history["outcomes"] = history["outcomes"][-max_history:]
        
        self.logger.info(f"Recorded outcome for {symbol} {horizon.value}: "
                        f"Confidence {prediction_confidence:.2f}, Outcome {outcome}, "
                        f"Accuracy {history['accuracy']:.2f}")
    
    async def calibrate_confidence(
        self,
        symbol: str,
        horizon: TimeHorizon,
        raw_confidence: float,
        market_data: Dict[str, Any]
    ) -> ConfidenceResult:
        """
        Calibrate confidence for a symbol and horizon.
        
        Args:
            symbol: Market symbol
            horizon: Time horizon
            raw_confidence: Raw confidence score (0-1)
            market_data: Market data dictionary
            
        Returns:
            ConfidenceResult with calibrated confidence
        """
        self.logger.info(f"Calibrating confidence for {symbol} on {horizon.value} horizon")
        
        # Initialize performance history if needed
        self._initialize_performance_history(symbol, horizon)
        history = self.performance_history[symbol][horizon]
        
        # Get historical accuracy
        historical_accuracy = self._calculate_historical_accuracy(symbol, horizon)
        
        # Calculate calibration error
        calibration_error = self._calculate_calibration_error(raw_confidence, historical_accuracy)
        
        # Get calibration status
        if len(history["outcomes"]) < self.min_samples:
            calibration_status = ConfidenceCalibration.UNKNOWN
        else:
            calibration_status = self._get_calibration_status(calibration_error)
        
        # Calculate uncertainty
        uncertainty_level, uncertainty_value = self._calculate_uncertainty(symbol, horizon, market_data)
        
        # Start with raw confidence
        calibrated_confidence = raw_confidence
        
        # Apply adjustments
        if calibration_status != ConfidenceCalibration.UNKNOWN:
            calibrated_confidence = self._adjust_for_calibration(
                calibrated_confidence, calibration_status, calibration_error
            )
        
        calibrated_confidence = self._adjust_for_win_streak(
            calibrated_confidence, history["win_streak"]
        )
        
        calibrated_confidence = self._adjust_for_loss_streak(
            calibrated_confidence, history["loss_streak"]
        )
        
        calibrated_confidence = self._adjust_for_uncertainty(
            calibrated_confidence, uncertainty_level, uncertainty_value
        )
        
        # Create metrics
        metrics = ConfidenceMetrics(
            raw_confidence=raw_confidence,
            calibrated_confidence=calibrated_confidence,
            historical_accuracy=historical_accuracy,
            calibration_error=calibration_error,
            uncertainty=uncertainty_value,
            win_streak_length=history["win_streak"],
            loss_streak_length=history["loss_streak"],
            metrics={
                "raw_confidence": raw_confidence,
                "calibrated_confidence": calibrated_confidence,
                "historical_accuracy": historical_accuracy,
                "calibration_error": calibration_error,
                "calibration_status": calibration_status.value,
                "uncertainty_level": uncertainty_level.value,
                "uncertainty_value": uncertainty_value,
                "win_streak": history["win_streak"],
                "loss_streak": history["loss_streak"],
                "sample_size": len(history["outcomes"]),
            }
        )
        
        # Log results
        self.logger.info(f"{symbol} {horizon.value}: Raw confidence {raw_confidence:.2f}, "
                        f"Calibrated {calibrated_confidence:.2f}, "
                        f"Status {calibration_status.value}, "
                        f"Uncertainty {uncertainty_level.value}")
        
        # Create result
        result = ConfidenceResult(
            calibrated_confidence=calibrated_confidence,
            calibration_status=calibration_status,
            uncertainty_level=uncertainty_level,
            metrics=metrics
        )
        
        return result
