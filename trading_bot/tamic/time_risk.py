"""
Time-Based Risk Management for TAMIC

This module implements time-based risk management focusing on:
1. Drawdown speed monitoring - Fast drawdowns are more dangerous than slow ones
2. Recovery duration tracking - Long recovery periods indicate deeper issues
3. Loss clustering detection - Clustered losses indicate regime change or model failure

The primary goal is to reduce exposure when time-based risk metrics indicate danger.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from .core import TimeHorizon, MarketTimeState

logger = logging.getLogger(__name__)


class DrawdownSpeed(Enum):
    """
    Classification of drawdown speed.
    Fast drawdowns are more dangerous than slow ones.
    """
    SLOW = "slow"  # Gradual decline over many periods
    MEDIUM = "medium"  # Moderate decline over several periods
    FAST = "fast"  # Rapid decline over few periods
    CRASH = "crash"  # Extremely rapid decline (flash crash)


@dataclass
class DrawdownMetrics:
    """Metrics related to drawdown analysis"""
    current_drawdown: float = 0.0  # Current drawdown as percentage
    max_drawdown: float = 0.0  # Maximum drawdown as percentage
    drawdown_speed: DrawdownSpeed = DrawdownSpeed.SLOW
    drawdown_duration: int = 0  # Duration in periods
    drawdown_slope: float = 0.0  # Rate of decline
    recovery_duration: int = 0  # Duration of recovery in periods
    loss_cluster_detected: bool = False
    loss_cluster_strength: float = 0.0  # 0-1 scale
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RiskAssessmentResult:
    """Result of time-based risk assessment"""
    max_exposure: float  # Maximum recommended exposure (0-1)
    risk_assessment: Dict[str, Any]  # Detailed risk assessment
    risk_score: float  # Overall risk score (0-1)
    drawdown_metrics: DrawdownMetrics  # Detailed drawdown metrics
    recovery_metrics: Dict[str, Any]  # Recovery-related metrics
    loss_cluster_metrics: Dict[str, Any]  # Loss clustering metrics
    recommendations: List[str]  # Risk management recommendations


class DrawdownSpeedMonitor:
    """
    Monitors the speed of drawdowns.
    
    Fast drawdowns are more dangerous than slow ones and require
    immediate reduction in exposure.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize DrawdownSpeedMonitor.
        
        Args:
            config: Configuration parameters
        """
        try:
            self.config = config or {}
            self.drawdown_history = {}  # Symbol -> {horizon -> history}
            self.logger = logging.getLogger("trading_bot.tamic.time_risk.drawdown_speed")
        
            # Default thresholds for drawdown speed classification
            self.speed_thresholds = self.config.get("speed_thresholds", {
                DrawdownSpeed.SLOW: 0.005,  # 0.5% per period
                DrawdownSpeed.MEDIUM: 0.015,  # 1.5% per period
                DrawdownSpeed.FAST: 0.03,  # 3% per period
                DrawdownSpeed.CRASH: 0.05,  # 5% per period
            })
        
            # Default weights for different drawdown speeds
            self.speed_weights = self.config.get("speed_weights", {
                DrawdownSpeed.SLOW: 0.5,
                DrawdownSpeed.MEDIUM: 1.0,
                DrawdownSpeed.FAST: 2.0,
                DrawdownSpeed.CRASH: 4.0,
            })
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _initialize_symbol_history(self, symbol: str, horizon: TimeHorizon):
        """Initialize history tracking for a symbol and horizon"""
        try:
            if symbol not in self.drawdown_history:
                self.drawdown_history[symbol] = {}
        
            if horizon not in self.drawdown_history[symbol]:
                self.drawdown_history[symbol][horizon] = {
                    "prices": [],
                    "drawdowns": [],
                    "speeds": [],
                    "last_peak": None,
                    "current_drawdown": 0.0,
                    "max_drawdown": 0.0,
                    "drawdown_duration": 0,
                }
        except Exception as e:
            logger.error(f"Error in _initialize_symbol_history: {e}")
            raise
    
    def _calculate_drawdown_speed(self, drawdown: float, duration: int) -> float:
        """
        Calculate drawdown speed as drawdown percentage per period.
        
        Args:
            drawdown: Drawdown as percentage (0-1)
            duration: Duration in periods
            
        Returns:
            Drawdown speed (percentage per period)
        """
        try:
            if duration <= 0:
                return 0.0
        
            return drawdown / duration
        except Exception as e:
            logger.error(f"Error in _calculate_drawdown_speed: {e}")
            raise
    
    def _classify_drawdown_speed(self, speed: float) -> DrawdownSpeed:
        """
        Classify drawdown speed based on thresholds.
        
        Args:
            speed: Drawdown speed (percentage per period)
            
        Returns:
            DrawdownSpeed classification
        """
        try:
            if speed >= self.speed_thresholds[DrawdownSpeed.CRASH]:
                return DrawdownSpeed.CRASH
            elif speed >= self.speed_thresholds[DrawdownSpeed.FAST]:
                return DrawdownSpeed.FAST
            elif speed >= self.speed_thresholds[DrawdownSpeed.MEDIUM]:
                return DrawdownSpeed.MEDIUM
            else:
                return DrawdownSpeed.SLOW
        except Exception as e:
            logger.error(f"Error in _classify_drawdown_speed: {e}")
            raise
    
    async def update(self, symbol: str, horizon: TimeHorizon, price: float) -> Dict[str, Any]:
        """
        Update drawdown tracking with new price data.
        
        Args:
            symbol: Market symbol
            horizon: Time horizon
            price: Current price
            
        Returns:
            Dictionary with drawdown metrics
        """
        try:
            self._initialize_symbol_history(symbol, horizon)
            history = self.drawdown_history[symbol][horizon]
        
            # Add price to history
            history["prices"].append(price)
        
            # Keep a limited history based on horizon
            max_history = {
                TimeHorizon.MICROSTRUCTURE: 100,
                TimeHorizon.INTRADAY: 200,
                TimeHorizon.SHORT_SWING: 50,
                TimeHorizon.MEDIUM_HORIZON: 30,
            }.get(horizon, 100)
        
            if len(history["prices"]) > max_history:
                history["prices"] = history["prices"][-max_history:]
        
            # Update peak and calculate drawdown
            if history["last_peak"] is None or price > history["last_peak"]:
                # New peak
                history["last_peak"] = price
                history["current_drawdown"] = 0.0
                history["drawdown_duration"] = 0
            else:
                # In drawdown
                history["current_drawdown"] = (history["last_peak"] - price) / history["last_peak"]
                history["drawdown_duration"] += 1
            
                # Update max drawdown
                history["max_drawdown"] = max(history["max_drawdown"], history["current_drawdown"])
        
            # Calculate drawdown speed
            speed = self._calculate_drawdown_speed(
                history["current_drawdown"], 
                history["drawdown_duration"]
            )
            history["speeds"].append(speed)
        
            # Classify drawdown speed
            drawdown_speed = self._classify_drawdown_speed(speed)
        
            # Prepare result
            result = {
                "current_drawdown": history["current_drawdown"],
                "max_drawdown": history["max_drawdown"],
                "drawdown_duration": history["drawdown_duration"],
                "drawdown_speed": drawdown_speed,
                "drawdown_slope": speed,
                "speed_weight": self.speed_weights[drawdown_speed],
            }
        
            self.logger.debug(f"{symbol} {horizon.value}: Drawdown {result['current_drawdown']:.2%}, "
                             f"Speed {drawdown_speed.value}, Duration {history['drawdown_duration']}")
        
            return result
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise


class RecoveryDurationTracker:
    """
    Tracks the duration of recovery periods after drawdowns.
    
    Long recovery periods indicate deeper issues with the market or strategy.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize RecoveryDurationTracker.
        
        Args:
            config: Configuration parameters
        """
        try:
            self.config = config or {}
            self.recovery_history = {}  # Symbol -> {horizon -> history}
            self.logger = logging.getLogger("trading_bot.tamic.time_risk.recovery_duration")
        
            # Default recovery duration thresholds
            self.recovery_thresholds = self.config.get("recovery_thresholds", {
                "short": 5,  # periods
                "medium": 10,
                "long": 20,
                "very_long": 30,
            })
        
            # Default penalties for recovery duration
            self.recovery_penalties = self.config.get("recovery_penalties", {
                "short": 0.05,
                "medium": 0.15,
                "long": 0.3,
                "very_long": 0.5,
            })
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _initialize_symbol_history(self, symbol: str, horizon: TimeHorizon):
        """Initialize history tracking for a symbol and horizon"""
        try:
            if symbol not in self.recovery_history:
                self.recovery_history[symbol] = {}
        
            if horizon not in self.recovery_history[symbol]:
                self.recovery_history[symbol][horizon] = {
                    "in_recovery": False,
                    "recovery_start": None,
                    "recovery_duration": 0,
                    "previous_peak": None,
                    "drawdown_depth": 0.0,
                    "recovery_periods": [],
                    "recovery_depths": [],
                }
        except Exception as e:
            logger.error(f"Error in _initialize_symbol_history: {e}")
            raise
    
    def _classify_recovery_duration(self, duration: int) -> str:
        """
        Classify recovery duration based on thresholds.
        
        Args:
            duration: Recovery duration in periods
            
        Returns:
            Classification as string
        """
        try:
            if duration >= self.recovery_thresholds["very_long"]:
                return "very_long"
            elif duration >= self.recovery_thresholds["long"]:
                return "long"
            elif duration >= self.recovery_thresholds["medium"]:
                return "medium"
            else:
                return "short"
        except Exception as e:
            logger.error(f"Error in _classify_recovery_duration: {e}")
            raise
    
    async def update(
        self, 
        symbol: str, 
        horizon: TimeHorizon, 
        price: float, 
        drawdown_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update recovery tracking with new price data.
        
        Args:
            symbol: Market symbol
            horizon: Time horizon
            price: Current price
            drawdown_metrics: Metrics from DrawdownSpeedMonitor
            
        Returns:
            Dictionary with recovery metrics
        """
        try:
            self._initialize_symbol_history(symbol, horizon)
            history = self.recovery_history[symbol][horizon]
        
            current_drawdown = drawdown_metrics["current_drawdown"]
        
            # Check if we're entering recovery
            if not history["in_recovery"] and current_drawdown > 0 and drawdown_metrics["drawdown_duration"] > 0:
                # We were in drawdown, now starting recovery
                history["in_recovery"] = True
                history["recovery_start"] = time.time()
                history["recovery_duration"] = 0
                history["drawdown_depth"] = current_drawdown
                history["previous_peak"] = price / (1 - current_drawdown)
            
                self.logger.info(f"{symbol} {horizon.value}: Entering recovery from "
                               f"{current_drawdown:.2%} drawdown")
        
            # Update recovery tracking
            if history["in_recovery"]:
                history["recovery_duration"] += 1
            
                # Check if recovery is complete
                if price >= history["previous_peak"]:
                    # Recovery complete
                    history["in_recovery"] = False
                    recovery_duration = history["recovery_duration"]
                    recovery_depth = history["drawdown_depth"]
                
                    # Store recovery statistics
                    history["recovery_periods"].append(recovery_duration)
                    history["recovery_depths"].append(recovery_depth)
                
                    # Keep limited history
                    max_history = 20
                    if len(history["recovery_periods"]) > max_history:
                        history["recovery_periods"] = history["recovery_periods"][-max_history:]
                        history["recovery_depths"] = history["recovery_depths"][-max_history:]
                
                    self.logger.info(f"{symbol} {horizon.value}: Recovery complete after "
                                   f"{recovery_duration} periods from {recovery_depth:.2%} drawdown")
        
            # Calculate recovery metrics
            recovery_duration = history["recovery_duration"] if history["in_recovery"] else 0
            recovery_class = self._classify_recovery_duration(recovery_duration)
            recovery_penalty = self.recovery_penalties[recovery_class] if history["in_recovery"] else 0
        
            # Calculate average recovery duration
            avg_recovery_duration = (
                sum(history["recovery_periods"]) / len(history["recovery_periods"])
                if history["recovery_periods"] else 0
            )
        
            # Calculate recovery ratio (duration / depth)
            recovery_ratio = (
                recovery_duration / history["drawdown_depth"] 
                if history["in_recovery"] and history["drawdown_depth"] > 0 
                else 0
            )
        
            # Prepare result
            result = {
                "in_recovery": history["in_recovery"],
                "recovery_duration": recovery_duration,
                "recovery_class": recovery_class,
                "recovery_penalty": recovery_penalty,
                "drawdown_depth": history["drawdown_depth"] if history["in_recovery"] else 0,
                "avg_recovery_duration": avg_recovery_duration,
                "recovery_ratio": recovery_ratio,
            }
        
            if history["in_recovery"]:
                self.logger.debug(f"{symbol} {horizon.value}: Recovery day {recovery_duration}, "
                                 f"Class {recovery_class}, Penalty {recovery_penalty:.2f}")
        
            return result
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise


class LossClusteringDetector:
    """
    Detects clustering of losses over time.
    
    Clustered losses indicate regime change or model failure.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize LossClusteringDetector.
        
        Args:
            config: Configuration parameters
        """
        try:
            self.config = config or {}
            self.loss_history = {}  # Symbol -> {horizon -> history}
            self.logger = logging.getLogger("trading_bot.tamic.time_risk.loss_clustering")
        
            # Default window sizes for different horizons
            self.window_sizes = self.config.get("window_sizes", {
                TimeHorizon.MICROSTRUCTURE: 20,
                TimeHorizon.INTRADAY: 15,
                TimeHorizon.SHORT_SWING: 10,
                TimeHorizon.MEDIUM_HORIZON: 7,
            })
        
            # Default thresholds for loss clustering detection
            self.clustering_thresholds = self.config.get("clustering_thresholds", {
                "mild": 0.3,  # 30% of periods show losses
                "moderate": 0.5,  # 50% of periods show losses
                "severe": 0.7,  # 70% of periods show losses
            })
        
            # Default penalties for loss clustering
            self.clustering_penalties = self.config.get("clustering_penalties", {
                "none": 0.0,
                "mild": 0.1,
                "moderate": 0.3,
                "severe": 0.6,
            })
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _initialize_symbol_history(self, symbol: str, horizon: TimeHorizon):
        """Initialize history tracking for a symbol and horizon"""
        try:
            if symbol not in self.loss_history:
                self.loss_history[symbol] = {}
        
            if horizon not in self.loss_history[symbol]:
                self.loss_history[symbol][horizon] = {
                    "returns": [],
                    "losses": [],
                    "clusters": [],
                }
        except Exception as e:
            logger.error(f"Error in _initialize_symbol_history: {e}")
            raise
    
    def _detect_loss_clustering(self, losses: List[bool], window_size: int) -> float:
        """
        Detect clustering of losses in a rolling window.
        
        Args:
            losses: List of boolean values (True for loss, False for gain)
            window_size: Size of the rolling window
            
        Returns:
            Loss clustering strength (0-1)
        """
        try:
            if len(losses) < window_size:
                return 0.0
        
            # Use only the most recent window
            recent_losses = losses[-window_size:]
            loss_ratio = sum(recent_losses) / len(recent_losses)
        
            return loss_ratio
        except Exception as e:
            logger.error(f"Error in _detect_loss_clustering: {e}")
            raise
    
    def _classify_clustering(self, clustering_strength: float) -> str:
        """
        Classify loss clustering based on thresholds.
        
        Args:
            clustering_strength: Loss clustering strength (0-1)
            
        Returns:
            Classification as string
        """
        try:
            if clustering_strength >= self.clustering_thresholds["severe"]:
                return "severe"
            elif clustering_strength >= self.clustering_thresholds["moderate"]:
                return "moderate"
            elif clustering_strength >= self.clustering_thresholds["mild"]:
                return "mild"
            else:
                return "none"
        except Exception as e:
            logger.error(f"Error in _classify_clustering: {e}")
            raise
    
    async def update(self, symbol: str, horizon: TimeHorizon, price: float, prev_price: float) -> Dict[str, Any]:
        """
        Update loss clustering detection with new price data.
        
        Args:
            symbol: Market symbol
            horizon: Time horizon
            price: Current price
            prev_price: Previous price
            
        Returns:
            Dictionary with loss clustering metrics
        """
        try:
            self._initialize_symbol_history(symbol, horizon)
            history = self.loss_history[symbol][horizon]
        
            # Calculate return
            ret = (price / prev_price - 1) if prev_price > 0 else 0
            history["returns"].append(ret)
        
            # Determine if this is a loss
            is_loss = ret < 0
            history["losses"].append(is_loss)
        
            # Keep limited history based on horizon
            window_size = self.window_sizes.get(horizon, 10)
            max_history = window_size * 3
        
            if len(history["returns"]) > max_history:
                history["returns"] = history["returns"][-max_history:]
                history["losses"] = history["losses"][-max_history:]
        
            # Detect loss clustering
            clustering_strength = self._detect_loss_clustering(history["losses"], window_size)
            history["clusters"].append(clustering_strength)
        
            if len(history["clusters"]) > max_history:
                history["clusters"] = history["clusters"][-max_history:]
        
            # Classify clustering
            clustering_class = self._classify_clustering(clustering_strength)
            clustering_penalty = self.clustering_penalties[clustering_class]
        
            # Calculate additional metrics
            avg_loss_size = np.mean([r for r, is_l in zip(history["returns"], history["losses"]) if is_l]) if any(history["losses"]) else 0
            max_consecutive_losses = 0
            current_streak = 0
        
            for is_loss in history["losses"]:
                if is_loss:
                    current_streak += 1
                    max_consecutive_losses = max(max_consecutive_losses, current_streak)
                else:
                    current_streak = 0
        
            # Prepare result
            result = {
                "loss_clustering_strength": clustering_strength,
                "loss_clustering_class": clustering_class,
                "loss_clustering_penalty": clustering_penalty,
                "avg_loss_size": avg_loss_size,
                "max_consecutive_losses": max_consecutive_losses,
                "recent_loss_ratio": sum(history["losses"][-window_size:]) / window_size if len(history["losses"]) >= window_size else 0,
            }
        
            if clustering_class != "none":
                self.logger.debug(f"{symbol} {horizon.value}: Loss clustering {clustering_strength:.2f}, "
                                 f"Class {clustering_class}, Penalty {clustering_penalty:.2f}")
        
            return result
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise


class TimeBasedRiskManager:
    """
    Time-Based Risk Manager for TAMIC
    
    Focuses on:
    1. Drawdown speed monitoring
    2. Recovery duration tracking
    3. Loss clustering detection
    
    Provides risk assessment and exposure recommendations based on time-based risk metrics.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize TimeBasedRiskManager.
        
        Args:
            config: Configuration parameters
        """
        try:
            self.config = config or {}
            self.logger = logging.getLogger("trading_bot.tamic.time_risk")
        
            # Initialize components
            self.drawdown_monitor = DrawdownSpeedMonitor(self.config.get("drawdown_speed", {}))
            self.recovery_tracker = RecoveryDurationTracker(self.config.get("recovery_duration", {}))
            self.loss_detector = LossClusteringDetector(self.config.get("loss_clustering", {}))
        
            # Default weights for risk components
            self.risk_weights = self.config.get("risk_weights", {
                "drawdown_speed": 0.4,
                "recovery_duration": 0.3,
                "loss_clustering": 0.3,
            })
        
            # Price history
            self.price_history = {}  # Symbol -> {horizon -> prices}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _initialize_price_history(self, symbol: str, horizon: TimeHorizon):
        """Initialize price history for a symbol and horizon"""
        try:
            if symbol not in self.price_history:
                self.price_history[symbol] = {}
        
            if horizon not in self.price_history[symbol]:
                self.price_history[symbol][horizon] = []
        except Exception as e:
            logger.error(f"Error in _initialize_price_history: {e}")
            raise
    
    def _get_previous_price(self, symbol: str, horizon: TimeHorizon) -> float:
        """Get previous price for a symbol and horizon"""
        try:
            if (symbol in self.price_history and 
                horizon in self.price_history[symbol] and 
                len(self.price_history[symbol][horizon]) > 0):
                return self.price_history[symbol][horizon][-1]
            return 0.0
        except Exception as e:
            logger.error(f"Error in _get_previous_price: {e}")
            raise
    
    def _calculate_risk_score(
        self,
        drawdown_metrics: Dict[str, Any],
        recovery_metrics: Dict[str, Any],
        loss_metrics: Dict[str, Any]
    ) -> float:
        """
        Calculate overall risk score based on component metrics.
        
        Args:
            drawdown_metrics: Metrics from DrawdownSpeedMonitor
            recovery_metrics: Metrics from RecoveryDurationTracker
            loss_metrics: Metrics from LossClusteringDetector
            
        Returns:
            Risk score (0-1)
        """
        # Component risk scores
        try:
            drawdown_risk = min(1.0, drawdown_metrics["current_drawdown"] * drawdown_metrics["speed_weight"])
            recovery_risk = recovery_metrics["recovery_penalty"]
            loss_risk = loss_metrics["loss_clustering_penalty"]
        
            # Weighted average
            risk_score = (
                drawdown_risk * self.risk_weights["drawdown_speed"] +
                recovery_risk * self.risk_weights["recovery_duration"] +
                loss_risk * self.risk_weights["loss_clustering"]
            )
        
            return min(1.0, risk_score)
        except Exception as e:
            logger.error(f"Error in _calculate_risk_score: {e}")
            raise
    
    def _calculate_max_exposure(self, risk_score: float) -> float:
        """
        Calculate maximum exposure based on risk score.
        
        Args:
            risk_score: Risk score (0-1)
            
        Returns:
            Maximum exposure (0-1)
        """
        # Linear reduction: 1.0 at risk_score=0, 0.0 at risk_score=1
        return max(0.0, 1.0 - risk_score)
    
    def _generate_recommendations(
        self,
        risk_score: float,
        drawdown_metrics: Dict[str, Any],
        recovery_metrics: Dict[str, Any],
        loss_metrics: Dict[str, Any]
    ) -> List[str]:
        """
        Generate risk management recommendations.
        
        Args:
            risk_score: Overall risk score
            drawdown_metrics: Metrics from DrawdownSpeedMonitor
            recovery_metrics: Metrics from RecoveryDurationTracker
            loss_metrics: Metrics from LossClusteringDetector
            
        Returns:
            List of recommendation strings
        """
        try:
            recommendations = []
        
            # Drawdown recommendations
            if drawdown_metrics["drawdown_speed"] == DrawdownSpeed.CRASH:
                recommendations.append("Immediate position reduction due to crash-speed drawdown")
            elif drawdown_metrics["drawdown_speed"] == DrawdownSpeed.FAST:
                recommendations.append("Reduce position size due to fast drawdown")
        
            # Recovery recommendations
            if recovery_metrics["recovery_class"] == "very_long":
                recommendations.append("Consider strategy review due to very long recovery period")
            elif recovery_metrics["recovery_class"] == "long":
                recommendations.append("Monitor recovery closely, consider partial position reduction")
        
            # Loss clustering recommendations
            if loss_metrics["loss_clustering_class"] == "severe":
                recommendations.append("Possible regime change detected, consider trading pause")
            elif loss_metrics["loss_clustering_class"] == "moderate":
                recommendations.append("Loss clustering detected, reduce position sizes")
        
            # Overall risk recommendations
            if risk_score > 0.8:
                recommendations.append("Critical risk level: Minimal exposure recommended")
            elif risk_score > 0.6:
                recommendations.append("High risk level: Significantly reduce exposure")
            elif risk_score > 0.4:
                recommendations.append("Moderate risk level: Reduce exposure")
        
            return recommendations
        except Exception as e:
            logger.error(f"Error in _generate_recommendations: {e}")
            raise
    
    async def evaluate_risk(
        self,
        symbol: str,
        horizon: TimeHorizon,
        market_data: Dict[str, Any]
    ) -> RiskAssessmentResult:
        """
        Evaluate time-based risk for a symbol and horizon.
        
        Args:
            symbol: Market symbol
            horizon: Time horizon
            market_data: Market data dictionary
            
        Returns:
            RiskAssessmentResult with risk assessment and recommendations
        """
        try:
            self.logger.info(f"Evaluating time-based risk for {symbol} on {horizon.value} horizon")
        
            # Extract price data
            price_key = "close"
            if price_key not in market_data:
                self.logger.warning(f"Price data not found for {symbol}, using fallback")
                price_key = next((k for k in ["close", "price", "last"] if k in market_data), None)
            
                if price_key is None:
                    self.logger.error(f"No price data found for {symbol}")
                    # Return default risk assessment
                    return RiskAssessmentResult(
                        max_exposure=0.5,
                        risk_assessment={"error": "No price data found"},
                        risk_score=0.5,
                        drawdown_metrics=DrawdownMetrics(),
                        recovery_metrics={},
                        loss_cluster_metrics={},
                        recommendations=["Insufficient data for risk assessment"]
                    )
        
            price = market_data[price_key]
            if isinstance(price, (list, np.ndarray, pd.Series)):
                price = price[-1]  # Use most recent price
        
            # Initialize price history
            self._initialize_price_history(symbol, horizon)
            prev_price = self._get_previous_price(symbol, horizon)
        
            # Update price history
            self.price_history[symbol][horizon].append(price)
        
            # Keep limited history
            max_history = {
                TimeHorizon.MICROSTRUCTURE: 100,
                TimeHorizon.INTRADAY: 200,
                TimeHorizon.SHORT_SWING: 50,
                TimeHorizon.MEDIUM_HORIZON: 30,
            }.get(horizon, 100)
        
            if len(self.price_history[symbol][horizon]) > max_history:
                self.price_history[symbol][horizon] = self.price_history[symbol][horizon][-max_history:]
        
            # Update components
            drawdown_metrics = await self.drawdown_monitor.update(symbol, horizon, price)
            recovery_metrics = await self.recovery_tracker.update(symbol, horizon, price, drawdown_metrics)
            loss_metrics = await self.loss_detector.update(symbol, horizon, price, prev_price or price)
        
            # Calculate risk score
            risk_score = self._calculate_risk_score(drawdown_metrics, recovery_metrics, loss_metrics)
        
            # Calculate max exposure
            max_exposure = self._calculate_max_exposure(risk_score)
        
            # Generate recommendations
            recommendations = self._generate_recommendations(
                risk_score, drawdown_metrics, recovery_metrics, loss_metrics
            )
        
            # Create drawdown metrics dataclass
            drawdown_metrics_obj = DrawdownMetrics(
                current_drawdown=drawdown_metrics["current_drawdown"],
                max_drawdown=drawdown_metrics["max_drawdown"],
                drawdown_speed=drawdown_metrics["drawdown_speed"],
                drawdown_duration=drawdown_metrics["drawdown_duration"],
                drawdown_slope=drawdown_metrics["drawdown_slope"],
                recovery_duration=recovery_metrics["recovery_duration"],
                loss_cluster_detected=loss_metrics["loss_clustering_class"] != "none",
                loss_cluster_strength=loss_metrics["loss_clustering_strength"],
            )
        
            # Create risk assessment
            risk_assessment = {
                "risk_score": risk_score,
                "max_exposure": max_exposure,
                "drawdown_risk": {
                    "current_drawdown": drawdown_metrics["current_drawdown"],
                    "drawdown_speed": drawdown_metrics["drawdown_speed"].value,
                    "drawdown_duration": drawdown_metrics["drawdown_duration"],
                },
                "recovery_risk": {
                    "in_recovery": recovery_metrics["in_recovery"],
                    "recovery_duration": recovery_metrics["recovery_duration"],
                    "recovery_class": recovery_metrics["recovery_class"],
                },
                "loss_clustering_risk": {
                    "clustering_strength": loss_metrics["loss_clustering_strength"],
                    "clustering_class": loss_metrics["loss_clustering_class"],
                    "max_consecutive_losses": loss_metrics["max_consecutive_losses"],
                }
            }
        
            self.logger.info(f"{symbol} {horizon.value}: Risk score {risk_score:.2f}, "
                            f"Max exposure {max_exposure:.2f}")
        
            return RiskAssessmentResult(
                max_exposure=max_exposure,
                risk_assessment=risk_assessment,
                risk_score=risk_score,
                drawdown_metrics=drawdown_metrics_obj,
                recovery_metrics=recovery_metrics,
                loss_cluster_metrics=loss_metrics,
                recommendations=recommendations
            )
        except Exception as e:
            logger.error(f"Error in evaluate_risk: {e}")
            raise
