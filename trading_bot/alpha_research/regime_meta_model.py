"""
Regime-Aware Meta Model
=======================
Combine features into a meta-model that:
- Is regime aware
- Dynamically weights signals based on market state
- Avoids alpha crowding
- Controls exposure and drawdown
- Adapts to correlation spikes

This meta-model is the core decision engine.

Author: AlphaAlgo Research Team
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd

from .rdaos_core import (
    AlphaHorizon,
    FeatureFamily,
    HARD_LIMITS,
    ProductionStatus,
    RegimeType,
    TestingMetrics,
    generate_id
)

logger = logging.getLogger(__name__)


class MarketState(Enum):
    """Current market state"""
    NORMAL = "normal"
    STRESSED = "stressed"
    CRISIS = "crisis"
    RECOVERY = "recovery"
    EUPHORIA = "euphoria"


class ExposureMode(Enum):
    """Exposure control mode"""
    FULL = "full"
    REDUCED = "reduced"
    MINIMAL = "minimal"
    ZERO = "zero"


@dataclass
class RegimeClassification:
    """Classification of current market regime"""
    primary_regime: RegimeType
    confidence: float
    
    secondary_regimes: List[Tuple[RegimeType, float]] = field(default_factory=list)
    
    volatility_percentile: float = 0.5
    trend_strength: float = 0.0
    correlation_level: float = 0.0
    liquidity_score: float = 1.0
    
    classified_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            "primary_regime": self.primary_regime.value,
            "confidence": self.confidence,
            "secondary_regimes": [(r.value, c) for r, c in self.secondary_regimes],
            "volatility_percentile": self.volatility_percentile,
            "trend_strength": self.trend_strength,
            "correlation_level": self.correlation_level,
            "liquidity_score": self.liquidity_score
        }


@dataclass
class FeatureWeight:
    """Weight for a feature in the meta-model"""
    family_id: str
    
    base_weight: float = 1.0
    regime_adjustment: float = 1.0
    crowding_adjustment: float = 1.0
    decay_adjustment: float = 1.0
    
    final_weight: float = 1.0
    
    def compute_final(self):
        """Compute final weight"""
        try:
            self.final_weight = (
                self.base_weight *
                self.regime_adjustment *
                self.crowding_adjustment *
                self.decay_adjustment
            )
            return self.final_weight
        except Exception as e:
            logger.error(f"Error in compute_final: {e}")
            raise


@dataclass
class MetaModelSignal:
    """Signal from the meta-model"""
    signal_id: str
    timestamp: datetime
    
    direction: float  # -1 to 1
    strength: float   # 0 to 1
    confidence: float # 0 to 1
    
    regime: RegimeType
    exposure_mode: ExposureMode
    
    feature_contributions: Dict[str, float] = field(default_factory=dict)
    
    position_size_pct: float = 0.0
    stop_loss_pct: float = 0.0
    take_profit_pct: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "signal_id": self.signal_id,
            "timestamp": self.timestamp.isoformat(),
            "direction": self.direction,
            "strength": self.strength,
            "confidence": self.confidence,
            "regime": self.regime.value,
            "exposure_mode": self.exposure_mode.value,
            "feature_contributions": self.feature_contributions,
            "position_size_pct": self.position_size_pct,
            "stop_loss_pct": self.stop_loss_pct,
            "take_profit_pct": self.take_profit_pct
        }


class RegimeClassifier:
    """
    Classify current market regime.
    
    Uses:
    - Volatility levels
    - Trend indicators
    - Correlation structure
    - Liquidity metrics
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        
            # Thresholds
            self.high_vol_percentile = self.config.get("high_vol_percentile", 0.75)
            self.low_vol_percentile = self.config.get("low_vol_percentile", 0.25)
            self.trend_threshold = self.config.get("trend_threshold", 0.3)
            self.crisis_vol_percentile = self.config.get("crisis_vol_percentile", 0.95)
        
            # History for percentile calculation
            self.volatility_history: List[float] = []
            self.max_history = self.config.get("max_history", 252 * 5)  # 5 years
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def classify(
        self,
        data: pd.DataFrame,
        returns: pd.Series
    ) -> RegimeClassification:
        """Classify current regime"""
        
        # Compute volatility
        try:
            current_vol = returns.iloc[-20:].std() * np.sqrt(252)
            self.volatility_history.append(current_vol)
        
            if len(self.volatility_history) > self.max_history:
                self.volatility_history = self.volatility_history[-self.max_history:]
        
            # Volatility percentile
            vol_percentile = sum(1 for v in self.volatility_history if v <= current_vol) / len(self.volatility_history)
        
            # Trend strength
            if "close" in data.columns:
                prices = data["close"]
                sma_20 = prices.rolling(20).mean().iloc[-1]
                sma_50 = prices.rolling(50).mean().iloc[-1]
                current_price = prices.iloc[-1]
            
                trend_strength = (current_price - sma_50) / (sma_50 + 1e-10)
            else:
                trend_strength = 0.0
        
            # Determine primary regime
            primary_regime, confidence = self._determine_regime(
                vol_percentile,
                trend_strength,
                returns
            )
        
            # Secondary regimes
            secondary_regimes = self._get_secondary_regimes(
                vol_percentile,
                trend_strength,
                primary_regime
            )
        
            return RegimeClassification(
                primary_regime=primary_regime,
                confidence=confidence,
                secondary_regimes=secondary_regimes,
                volatility_percentile=vol_percentile,
                trend_strength=trend_strength,
                correlation_level=self._compute_correlation_level(returns),
                liquidity_score=self._compute_liquidity_score(data)
            )
        except Exception as e:
            logger.error(f"Error in classify: {e}")
            raise
    
    def _determine_regime(
        self,
        vol_percentile: float,
        trend_strength: float,
        returns: pd.Series
    ) -> Tuple[RegimeType, float]:
        """Determine primary regime"""
        
        # Crisis check
        try:
            if vol_percentile >= self.crisis_vol_percentile:
                recent_return = returns.iloc[-5:].sum()
                if recent_return < -0.05:  # 5% drop
                    return RegimeType.CRISIS, 0.9
        
            # High volatility
            if vol_percentile >= self.high_vol_percentile:
                return RegimeType.HIGH_VOLATILITY, 0.8
        
            # Low volatility
            if vol_percentile <= self.low_vol_percentile:
                return RegimeType.LOW_VOLATILITY, 0.8
        
            # Trending
            if abs(trend_strength) >= self.trend_threshold:
                if trend_strength > 0:
                    return RegimeType.TRENDING_UP, 0.7
                else:
                    return RegimeType.TRENDING_DOWN, 0.7
        
            # Ranging
            if abs(trend_strength) < self.trend_threshold / 2:
                return RegimeType.RANGING, 0.6
        
            # Normal
            return RegimeType.NORMAL, 0.5
        except Exception as e:
            logger.error(f"Error in _determine_regime: {e}")
            raise
    
    def _get_secondary_regimes(
        self,
        vol_percentile: float,
        trend_strength: float,
        primary: RegimeType
    ) -> List[Tuple[RegimeType, float]]:
        """Get secondary regime classifications"""
        try:
            secondary = []
        
            # Add volatility regime if not primary
            if primary not in [RegimeType.HIGH_VOLATILITY, RegimeType.LOW_VOLATILITY]:
                if vol_percentile >= self.high_vol_percentile:
                    secondary.append((RegimeType.HIGH_VOLATILITY, 0.5))
                elif vol_percentile <= self.low_vol_percentile:
                    secondary.append((RegimeType.LOW_VOLATILITY, 0.5))
        
            # Add trend regime if not primary
            if primary not in [RegimeType.TRENDING_UP, RegimeType.TRENDING_DOWN]:
                if trend_strength >= self.trend_threshold:
                    secondary.append((RegimeType.TRENDING_UP, 0.4))
                elif trend_strength <= -self.trend_threshold:
                    secondary.append((RegimeType.TRENDING_DOWN, 0.4))
        
            return secondary
        except Exception as e:
            logger.error(f"Error in _get_secondary_regimes: {e}")
            raise
    
    def _compute_correlation_level(self, returns: pd.Series) -> float:
        """Compute correlation level (simplified)"""
        # In production, compute cross-asset correlations
        return 0.5
    
    def _compute_liquidity_score(self, data: pd.DataFrame) -> float:
        """Compute liquidity score"""
        try:
            if "volume" in data.columns:
                recent_vol = data["volume"].iloc[-5:].mean()
                avg_vol = data["volume"].mean()
                return min(1.0, recent_vol / (avg_vol + 1e-10))
            return 1.0
        except Exception as e:
            logger.error(f"Error in _compute_liquidity_score: {e}")
            raise


class DynamicWeightManager:
    """
    Dynamically weight features based on market state.
    
    Adjusts weights for:
    - Regime conditions
    - Alpha crowding
    - Recent performance
    - Decay signals
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        
            # Weight bounds
            self.min_weight = self.config.get("min_weight", 0.1)
            self.max_weight = self.config.get("max_weight", 2.0)
        
            # Crowding detection
            self.crowding_threshold = self.config.get("crowding_threshold", 0.7)
        
            # Performance tracking
            self.recent_performance: Dict[str, List[float]] = {}
            self.performance_window = self.config.get("performance_window", 20)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def compute_weights(
        self,
        families: List[FeatureFamily],
        regime: RegimeClassification,
        crowding_scores: Optional[Dict[str, float]] = None,
        decay_signals: Optional[Dict[str, float]] = None
    ) -> Dict[str, FeatureWeight]:
        """Compute weights for all features"""
        try:
            weights = {}
            crowding_scores = crowding_scores or {}
            decay_signals = decay_signals or {}
        
            for family in families:
                weight = FeatureWeight(family_id=family.family_id)
            
                # Base weight from historical performance
                weight.base_weight = self._compute_base_weight(family)
            
                # Regime adjustment
                weight.regime_adjustment = self._compute_regime_adjustment(
                    family,
                    regime
                )
            
                # Crowding adjustment
                crowding = crowding_scores.get(family.family_id, 0.0)
                weight.crowding_adjustment = self._compute_crowding_adjustment(crowding)
            
                # Decay adjustment
                decay = decay_signals.get(family.family_id, 0.0)
                weight.decay_adjustment = self._compute_decay_adjustment(decay)
            
                # Compute final weight
                weight.compute_final()
            
                # Apply bounds
                weight.final_weight = max(
                    self.min_weight,
                    min(self.max_weight, weight.final_weight)
                )
            
                weights[family.family_id] = weight
        
            # Normalize weights
            total_weight = sum(w.final_weight for w in weights.values())
            if total_weight > 0:
                for w in weights.values():
                    w.final_weight /= total_weight
        
            return weights
        except Exception as e:
            logger.error(f"Error in compute_weights: {e}")
            raise
    
    def _compute_base_weight(self, family: FeatureFamily) -> float:
        """Compute base weight from historical performance"""
        try:
            family_id = family.family_id
        
            if family_id in self.recent_performance:
                returns = self.recent_performance[family_id]
                if len(returns) > 0:
                    sharpe = np.mean(returns) / (np.std(returns) + 1e-10) * np.sqrt(252)
                    # Map Sharpe to weight (0.5 Sharpe = 1.0 weight)
                    return max(0.5, min(2.0, sharpe / 0.5))
        
            return 1.0
        except Exception as e:
            logger.error(f"Error in _compute_base_weight: {e}")
            raise
    
    def _compute_regime_adjustment(
        self,
        family: FeatureFamily,
        regime: RegimeClassification
    ) -> float:
        """Compute regime-based weight adjustment"""
        # Check if feature is designed for current regime
        try:
            if regime.primary_regime in family.regime_conditions:
                return 1.2  # Boost weight
        
            # Check for regime mismatch
            opposite_regimes = {
                RegimeType.TRENDING_UP: RegimeType.TRENDING_DOWN,
                RegimeType.TRENDING_DOWN: RegimeType.TRENDING_UP,
                RegimeType.HIGH_VOLATILITY: RegimeType.LOW_VOLATILITY,
                RegimeType.LOW_VOLATILITY: RegimeType.HIGH_VOLATILITY
            }
        
            if regime.primary_regime in opposite_regimes:
                opposite = opposite_regimes[regime.primary_regime]
                if opposite in family.regime_conditions and regime.primary_regime not in family.regime_conditions:
                    return 0.5  # Reduce weight
        
            return 1.0
        except Exception as e:
            logger.error(f"Error in _compute_regime_adjustment: {e}")
            raise
    
    def _compute_crowding_adjustment(self, crowding_score: float) -> float:
        """Compute crowding-based weight adjustment"""
        try:
            if crowding_score >= self.crowding_threshold:
                # Reduce weight for crowded strategies
                return max(0.3, 1.0 - crowding_score)
            return 1.0
        except Exception as e:
            logger.error(f"Error in _compute_crowding_adjustment: {e}")
            raise
    
    def _compute_decay_adjustment(self, decay_signal: float) -> float:
        """Compute decay-based weight adjustment"""
        # decay_signal: 0 = no decay, 1 = full decay
        return max(0.2, 1.0 - decay_signal * 0.8)
    
    def update_performance(self, family_id: str, daily_return: float):
        """Update performance tracking"""
        try:
            if family_id not in self.recent_performance:
                self.recent_performance[family_id] = []
        
            self.recent_performance[family_id].append(daily_return)
        
            # Keep only recent window
            if len(self.recent_performance[family_id]) > self.performance_window:
                self.recent_performance[family_id] = self.recent_performance[family_id][-self.performance_window:]
        except Exception as e:
            logger.error(f"Error in update_performance: {e}")
            raise


class ExposureController:
    """
    Control exposure and drawdown.
    
    Implements:
    - Position sizing
    - Drawdown limits
    - Correlation-based exposure reduction
    - Emergency exposure cuts
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        
            # Limits
            self.max_position_pct = self.config.get("max_position_pct", 10.0)
            self.max_total_exposure = self.config.get("max_total_exposure", 100.0)
            self.max_drawdown = self.config.get("max_drawdown", HARD_LIMITS.MAX_DRAWDOWN_PCT)
        
            # Drawdown tracking
            self.peak_equity = 1.0
            self.current_equity = 1.0
            self.current_drawdown = 0.0
        
            # Correlation threshold
            self.high_correlation_threshold = self.config.get("high_correlation_threshold", 0.7)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def determine_exposure_mode(
        self,
        regime: RegimeClassification,
        current_drawdown: float
    ) -> ExposureMode:
        """Determine exposure mode based on conditions"""
        
        # Update drawdown tracking
        try:
            self.current_drawdown = current_drawdown
        
            # Emergency mode
            if current_drawdown >= self.max_drawdown * 0.9:
                return ExposureMode.ZERO
        
            # Crisis mode
            if regime.primary_regime == RegimeType.CRISIS:
                return ExposureMode.MINIMAL
        
            # High drawdown
            if current_drawdown >= self.max_drawdown * 0.7:
                return ExposureMode.MINIMAL
        
            # Moderate drawdown
            if current_drawdown >= self.max_drawdown * 0.5:
                return ExposureMode.REDUCED
        
            # High correlation environment
            if regime.correlation_level >= self.high_correlation_threshold:
                return ExposureMode.REDUCED
        
            # Low liquidity
            if regime.liquidity_score < 0.5:
                return ExposureMode.REDUCED
        
            return ExposureMode.FULL
        except Exception as e:
            logger.error(f"Error in determine_exposure_mode: {e}")
            raise
    
    def compute_position_size(
        self,
        signal_strength: float,
        exposure_mode: ExposureMode,
        volatility: float
    ) -> float:
        """Compute position size as percentage of portfolio"""
        
        # Base position from signal strength
        try:
            base_position = signal_strength * self.max_position_pct
        
            # Exposure mode multiplier
            mode_multipliers = {
                ExposureMode.FULL: 1.0,
                ExposureMode.REDUCED: 0.5,
                ExposureMode.MINIMAL: 0.25,
                ExposureMode.ZERO: 0.0
            }
        
            position = base_position * mode_multipliers[exposure_mode]
        
            # Volatility adjustment (reduce position in high vol)
            if volatility > 0.2:  # 20% annualized vol
                vol_adjustment = 0.2 / volatility
                position *= min(1.0, vol_adjustment)
        
            return min(position, self.max_position_pct)
        except Exception as e:
            logger.error(f"Error in compute_position_size: {e}")
            raise
    
    def compute_stop_loss(
        self,
        volatility: float,
        regime: RegimeType
    ) -> float:
        """Compute stop loss percentage"""
        # Base stop loss: 2x daily volatility
        try:
            daily_vol = volatility / np.sqrt(252)
            base_stop = daily_vol * 2 * 100  # As percentage
        
            # Regime adjustment
            if regime in [RegimeType.HIGH_VOLATILITY, RegimeType.CRISIS]:
                base_stop *= 1.5  # Wider stops in volatile markets
            elif regime == RegimeType.LOW_VOLATILITY:
                base_stop *= 0.75  # Tighter stops in calm markets
        
            # Cap stop loss
            return min(base_stop, 5.0)  # Max 5% stop
        except Exception as e:
            logger.error(f"Error in compute_stop_loss: {e}")
            raise
    
    def update_equity(self, new_equity: float):
        """Update equity tracking"""
        try:
            self.current_equity = new_equity
            self.peak_equity = max(self.peak_equity, new_equity)
            self.current_drawdown = (self.peak_equity - self.current_equity) / self.peak_equity * 100
        except Exception as e:
            logger.error(f"Error in update_equity: {e}")
            raise


class CrowdingDetector:
    """
    Detect alpha crowding.
    
    Monitors:
    - Strategy popularity
    - Capacity utilization
    - Return correlation with known factors
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        
            # Crowding thresholds
            self.capacity_utilization_threshold = self.config.get("capacity_threshold", 0.5)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def compute_crowding_scores(
        self,
        families: List[FeatureFamily],
        market_data: Optional[pd.DataFrame] = None
    ) -> Dict[str, float]:
        """Compute crowding scores for all features"""
        try:
            scores = {}
        
            for family in families:
                score = self._compute_family_crowding(family, market_data)
                scores[family.family_id] = score
        
            return scores
        except Exception as e:
            logger.error(f"Error in compute_crowding_scores: {e}")
            raise
    
    def _compute_family_crowding(
        self,
        family: FeatureFamily,
        market_data: Optional[pd.DataFrame]
    ) -> float:
        """Compute crowding score for a single family"""
        try:
            crowding = 0.0
        
            # Capacity-based crowding (simplified)
            # In production, track actual AUM in similar strategies
            if family.capacity_limit_usd > 0:
                # Assume some utilization based on strategy age
                days_deployed = (datetime.utcnow() - family.created_at).days
                estimated_utilization = min(1.0, days_deployed / 365)  # Ramp up over 1 year
            
                if estimated_utilization > self.capacity_utilization_threshold:
                    crowding += 0.3
        
            # Alpha source crowding
            crowded_sources = ["momentum", "value", "low_volatility"]
            if family.alpha_source.lower() in crowded_sources:
                crowding += 0.2
        
            return min(1.0, crowding)
        except Exception as e:
            logger.error(f"Error in _compute_family_crowding: {e}")
            raise


class RegimeAwareMetaModel:
    """
    Main meta-model combining all features.
    
    This is the core decision engine that:
    - Classifies current regime
    - Weights features dynamically
    - Controls exposure
    - Generates trading signals
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        
            # Initialize components
            self.regime_classifier = RegimeClassifier(config)
            self.weight_manager = DynamicWeightManager(config)
            self.exposure_controller = ExposureController(config)
            self.crowding_detector = CrowdingDetector(config)
        
            # Active features
            self.active_families: List[FeatureFamily] = []
        
            # State
            self.current_regime: Optional[RegimeClassification] = None
            self.current_weights: Dict[str, FeatureWeight] = {}
        
            logger.info("Regime-Aware Meta Model initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def add_feature_family(self, family: FeatureFamily):
        """Add a feature family to the model"""
        try:
            if family.family_id not in [f.family_id for f in self.active_families]:
                self.active_families.append(family)
                logger.info(f"Added feature family: {family.family_id}")
        except Exception as e:
            logger.error(f"Error in add_feature_family: {e}")
            raise
    
    def remove_feature_family(self, family_id: str):
        """Remove a feature family from the model"""
        try:
            self.active_families = [f for f in self.active_families if f.family_id != family_id]
            logger.info(f"Removed feature family: {family_id}")
        except Exception as e:
            logger.error(f"Error in remove_feature_family: {e}")
            raise
    
    def generate_signal(
        self,
        data: pd.DataFrame,
        returns: pd.Series,
        feature_values: Dict[str, float],
        current_drawdown: float = 0.0,
        decay_signals: Optional[Dict[str, float]] = None
    ) -> MetaModelSignal:
        """Generate a trading signal"""
        
        # Classify regime
        try:
            self.current_regime = self.regime_classifier.classify(data, returns)
        
            # Compute crowding scores
            crowding_scores = self.crowding_detector.compute_crowding_scores(
                self.active_families,
                data
            )
        
            # Compute weights
            self.current_weights = self.weight_manager.compute_weights(
                self.active_families,
                self.current_regime,
                crowding_scores,
                decay_signals
            )
        
            # Determine exposure mode
            exposure_mode = self.exposure_controller.determine_exposure_mode(
                self.current_regime,
                current_drawdown
            )
        
            # Combine feature signals
            direction, strength, contributions = self._combine_signals(
                feature_values,
                self.current_weights
            )
        
            # Compute confidence
            confidence = self._compute_confidence(
                self.current_regime,
                self.current_weights,
                feature_values
            )
        
            # Compute position size
            volatility = returns.iloc[-20:].std() * np.sqrt(252)
            position_size = self.exposure_controller.compute_position_size(
                strength,
                exposure_mode,
                volatility
            )
        
            # Compute stop loss
            stop_loss = self.exposure_controller.compute_stop_loss(
                volatility,
                self.current_regime.primary_regime
            )
        
            # Take profit (2:1 risk-reward)
            take_profit = stop_loss * 2
        
            return MetaModelSignal(
                signal_id=generate_id("sig"),
                timestamp=datetime.utcnow(),
                direction=direction,
                strength=strength,
                confidence=confidence,
                regime=self.current_regime.primary_regime,
                exposure_mode=exposure_mode,
                feature_contributions=contributions,
                position_size_pct=position_size,
                stop_loss_pct=stop_loss,
                take_profit_pct=take_profit
            )
        except Exception as e:
            logger.error(f"Error in generate_signal: {e}")
            raise
    
    def _combine_signals(
        self,
        feature_values: Dict[str, float],
        weights: Dict[str, FeatureWeight]
    ) -> Tuple[float, float, Dict[str, float]]:
        """Combine feature signals into single direction and strength"""
        try:
            weighted_sum = 0.0
            total_weight = 0.0
            contributions = {}
        
            for family_id, weight in weights.items():
                if family_id in feature_values:
                    value = feature_values[family_id]
                    contribution = value * weight.final_weight
                
                    weighted_sum += contribution
                    total_weight += weight.final_weight
                    contributions[family_id] = contribution
        
            if total_weight > 0:
                direction = np.clip(weighted_sum / total_weight, -1, 1)
                strength = min(1.0, abs(weighted_sum))
            else:
                direction = 0.0
                strength = 0.0
        
            return direction, strength, contributions
        except Exception as e:
            logger.error(f"Error in _combine_signals: {e}")
            raise
    
    def _compute_confidence(
        self,
        regime: RegimeClassification,
        weights: Dict[str, FeatureWeight],
        feature_values: Dict[str, float]
    ) -> float:
        """Compute signal confidence"""
        # Base confidence from regime classification
        try:
            confidence = regime.confidence
        
            # Adjust for feature agreement
            if feature_values:
                signs = [np.sign(v) for v in feature_values.values() if v != 0]
                if signs:
                    agreement = abs(sum(signs)) / len(signs)
                    confidence *= (0.5 + 0.5 * agreement)
        
            # Adjust for weight concentration
            if weights:
                weight_values = [w.final_weight for w in weights.values()]
                max_weight = max(weight_values)
                if max_weight > 0.5:  # Single feature dominates
                    confidence *= 0.8
        
            return min(1.0, confidence)
        except Exception as e:
            logger.error(f"Error in _compute_confidence: {e}")
            raise
    
    def update_performance(self, family_id: str, daily_return: float):
        """Update performance tracking for a feature"""
        try:
            self.weight_manager.update_performance(family_id, daily_return)
        except Exception as e:
            logger.error(f"Error in update_performance: {e}")
            raise
    
    def update_equity(self, new_equity: float):
        """Update equity tracking"""
        try:
            self.exposure_controller.update_equity(new_equity)
        except Exception as e:
            logger.error(f"Error in update_equity: {e}")
            raise
    
    def get_active_family_count(self) -> int:
        """Get count of active feature families"""
        return len(self.active_families)
    
    def get_current_regime(self) -> Optional[RegimeClassification]:
        """Get current regime classification"""
        return self.current_regime


def create_meta_model(config: Optional[Dict] = None) -> RegimeAwareMetaModel:
    """Factory function to create meta model"""
    return RegimeAwareMetaModel(config)
