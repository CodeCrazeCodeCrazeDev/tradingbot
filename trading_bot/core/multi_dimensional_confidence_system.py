"""
Multi-Dimensional Confidence System - Stage 4 Fix

Addresses violations:
- Single confidence scores used
- No multi-dimensional confidence
- Sample size not considered
- Regime novelty penalty missing
- Alpha decay not systematic

Replaces ALL single confidence scores with multi-dimensional vectors.

Author: AlphaAlgo Core
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import deque
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ConfidenceVector:
    """
    Multi-dimensional confidence vector.
    
    NEVER use a single confidence score.
    ALWAYS use minimum confidence, not average.
    """
    # Core dimensions
    statistical_confidence: float  # Historical win rate, sample size adjusted
    regime_confidence: float  # Regime detection confidence
    execution_confidence: float  # Execution feasibility
    tail_risk_confidence: float  # Tail risk bounded
    model_stability_confidence: float  # Model not degrading
    
    # Penalties applied
    sample_size_penalty: float = 0.0
    regime_novelty_penalty: float = 0.0
    alpha_decay_penalty: float = 0.0
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def minimum_confidence(self) -> float:
        """
        MINIMUM confidence dominates.
        This is the ONLY confidence that matters.
        """
        try:
            confidences = [
                self.statistical_confidence,
                self.regime_confidence,
                self.execution_confidence,
                self.tail_risk_confidence,
                self.model_stability_confidence
            ]
            return min(confidences)
        except Exception as e:
            logger.error(f"Error in minimum_confidence: {e}")
            raise
    
    @property
    def mean_confidence(self) -> float:
        """
        Mean confidence for reference ONLY.
        DO NOT USE THIS FOR DECISIONS.
        """
        try:
            confidences = [
                self.statistical_confidence,
                self.regime_confidence,
                self.execution_confidence,
                self.tail_risk_confidence,
                self.model_stability_confidence
            ]
            return np.mean(confidences)
        except Exception as e:
            logger.error(f"Error in mean_confidence: {e}")
            raise
    
    @property
    def total_penalty(self) -> float:
        """Total penalty applied"""
        return self.sample_size_penalty + self.regime_novelty_penalty + self.alpha_decay_penalty
    
    @property
    def penalized_minimum_confidence(self) -> float:
        """Minimum confidence after penalties"""
        return max(0.0, self.minimum_confidence - self.total_penalty)
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary"""
        return {
            'statistical': self.statistical_confidence,
            'regime': self.regime_confidence,
            'execution': self.execution_confidence,
            'tail_risk': self.tail_risk_confidence,
            'model_stability': self.model_stability_confidence,
            'minimum': self.minimum_confidence,
            'mean': self.mean_confidence,
            'sample_size_penalty': self.sample_size_penalty,
            'regime_novelty_penalty': self.regime_novelty_penalty,
            'alpha_decay_penalty': self.alpha_decay_penalty,
            'penalized_minimum': self.penalized_minimum_confidence
        }


class SampleSizeAdjuster:
    """
    Adjusts confidence based on sample size.
    
    Small sample = low confidence penalty.
    """
    
    def calculate_penalty(self, sample_size: int) -> float:
        """
        Calculate sample size penalty.
        
        Args:
            sample_size: Number of historical samples
            
        Returns:
            Penalty (0.0 to 0.5)
        """
        try:
            if sample_size >= 100:
                return 0.0  # No penalty for large samples
            elif sample_size >= 50:
                return 0.05  # Small penalty
            elif sample_size >= 20:
                return 0.15  # Medium penalty
            elif sample_size >= 10:
                return 0.25  # Large penalty
            else:
                return 0.5  # Massive penalty for tiny samples
        except Exception as e:
            logger.error(f"Error in calculate_penalty: {e}")
            raise


class RegimeNoveltyPenalizer:
    """
    Penalizes confidence in novel regimes.
    
    New regime = no historical data = low confidence.
    """
    
    def __init__(self, window_size: int = 1000):
        try:
            self.regime_history: deque = deque(maxlen=window_size)
            self.regime_first_seen: Dict[str, datetime] = {}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(self, regime: str):
        """Update regime history"""
        try:
            self.regime_history.append({
                'regime': regime,
                'timestamp': datetime.utcnow()
            })
        
            if regime not in self.regime_first_seen:
                self.regime_first_seen[regime] = datetime.utcnow()
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise
    
    def calculate_penalty(self, regime: str) -> float:
        """
        Calculate regime novelty penalty.
        
        Args:
            regime: Current regime
            
        Returns:
            Penalty (0.0 to 0.4)
        """
        try:
            if regime not in self.regime_first_seen:
                return 0.4  # Maximum penalty for completely new regime
        
            # Time since first seen
            first_seen = self.regime_first_seen[regime]
            time_known = (datetime.utcnow() - first_seen).total_seconds() / 3600  # Hours
        
            # Count occurrences in history
            occurrences = sum(1 for r in self.regime_history if r['regime'] == regime)
        
            # Penalty decreases with time and occurrences
            if time_known < 24:  # Less than 1 day
                time_penalty = 0.3
            elif time_known < 168:  # Less than 1 week
                time_penalty = 0.2
            elif time_known < 720:  # Less than 1 month
                time_penalty = 0.1
            else:
                time_penalty = 0.0
        
            if occurrences < 10:
                occurrence_penalty = 0.3
            elif occurrences < 50:
                occurrence_penalty = 0.15
            elif occurrences < 100:
                occurrence_penalty = 0.05
            else:
                occurrence_penalty = 0.0
        
            return min(time_penalty + occurrence_penalty, 0.4)
        except Exception as e:
            logger.error(f"Error in calculate_penalty: {e}")
            raise


class AlphaDecayCalculator:
    """
    Calculates alpha decay penalty.
    
    Alpha decays over time. Old strategies lose edge.
    """
    
    def __init__(self):
        try:
            self.strategy_creation_times: Dict[str, datetime] = {}
            self.strategy_last_update: Dict[str, datetime] = {}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def register_strategy(self, strategy_id: str, creation_time: Optional[datetime] = None):
        """Register strategy creation time"""
        try:
            if strategy_id not in self.strategy_creation_times:
                self.strategy_creation_times[strategy_id] = creation_time or datetime.utcnow()
                self.strategy_last_update[strategy_id] = datetime.utcnow()
        except Exception as e:
            logger.error(f"Error in register_strategy: {e}")
            raise
    
    def update_strategy(self, strategy_id: str):
        """Update strategy (e.g., parameters changed)"""
        try:
            self.strategy_last_update[strategy_id] = datetime.utcnow()
        except Exception as e:
            logger.error(f"Error in update_strategy: {e}")
            raise
    
    def calculate_penalty(
        self,
        strategy_id: str,
        half_life_days: float = 90.0
    ) -> float:
        """
        Calculate alpha decay penalty.
        
        Args:
            strategy_id: Strategy identifier
            half_life_days: Days until alpha decays to 50%
            
        Returns:
            Penalty (0.0 to 0.5)
        """
        try:
            if strategy_id not in self.strategy_last_update:
                return 0.3  # Unknown strategy = high penalty
        
            last_update = self.strategy_last_update[strategy_id]
            days_since_update = (datetime.utcnow() - last_update).total_seconds() / 86400
        
            # Exponential decay
            # penalty = 0.5 * (1 - exp(-days / half_life))
            decay_factor = np.exp(-days_since_update / half_life_days)
            penalty = 0.5 * (1.0 - decay_factor)
        
            return penalty
        except Exception as e:
            logger.error(f"Error in calculate_penalty: {e}")
            raise


class MultiDimensionalConfidenceBuilder:
    """
    Builds multi-dimensional confidence vectors.
    
    This REPLACES all single confidence scores.
    """
    
    def __init__(self):
        try:
            self.sample_size_adjuster = SampleSizeAdjuster()
            self.regime_penalizer = RegimeNoveltyPenalizer()
            self.alpha_decay_calculator = AlphaDecayCalculator()
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def build_confidence_vector(
        self,
        signal: Dict,
        market_context: Dict,
        historical_data: Optional[Dict] = None
    ) -> ConfidenceVector:
        """
        Build complete confidence vector.
        
        Args:
            signal: Signal data
            market_context: Market conditions
            historical_data: Historical performance data
            
        Returns:
            ConfidenceVector with all dimensions
        """
        # Extract data
        try:
            strategy_id = signal.get('strategy_id', 'unknown')
            regime = market_context.get('regime', 'unknown')
        
            # Build core dimensions
            statistical_conf = self._calculate_statistical_confidence(signal, historical_data)
            regime_conf = self._calculate_regime_confidence(market_context)
            execution_conf = self._calculate_execution_confidence(signal, market_context)
            tail_risk_conf = self._calculate_tail_risk_confidence(signal, market_context)
            model_stability_conf = self._calculate_model_stability_confidence(signal, historical_data)
        
            # Calculate penalties
            sample_size = historical_data.get('sample_size', 0) if historical_data else 0
            sample_penalty = self.sample_size_adjuster.calculate_penalty(sample_size)
        
            self.regime_penalizer.update(regime)
            regime_penalty = self.regime_penalizer.calculate_penalty(regime)
        
            self.alpha_decay_calculator.register_strategy(strategy_id)
            decay_penalty = self.alpha_decay_calculator.calculate_penalty(strategy_id)
        
            # Build vector
            vector = ConfidenceVector(
                statistical_confidence=statistical_conf,
                regime_confidence=regime_conf,
                execution_confidence=execution_conf,
                tail_risk_confidence=tail_risk_conf,
                model_stability_confidence=model_stability_conf,
                sample_size_penalty=sample_penalty,
                regime_novelty_penalty=regime_penalty,
                alpha_decay_penalty=decay_penalty
            )
        
            logger.debug(
                f"Confidence vector for {signal.get('symbol')}:\n"
                f"  Statistical: {statistical_conf:.2%}\n"
                f"  Regime: {regime_conf:.2%}\n"
                f"  Execution: {execution_conf:.2%}\n"
                f"  Tail Risk: {tail_risk_conf:.2%}\n"
                f"  Model Stability: {model_stability_conf:.2%}\n"
                f"  MINIMUM: {vector.minimum_confidence:.2%}\n"
                f"  Penalties: sample={sample_penalty:.2%}, regime={regime_penalty:.2%}, decay={decay_penalty:.2%}\n"
                f"  PENALIZED MINIMUM: {vector.penalized_minimum_confidence:.2%}"
            )
        
            return vector
        except Exception as e:
            logger.error(f"Error in build_confidence_vector: {e}")
            raise
    
    def _calculate_statistical_confidence(
        self,
        signal: Dict,
        historical_data: Optional[Dict]
    ) -> float:
        """Calculate statistical confidence from historical performance"""
        try:
            if not historical_data:
                return 0.5  # No data = neutral
        
            win_rate = historical_data.get('win_rate', 0.5)
            sharpe = historical_data.get('sharpe', 0.0)
        
            # Confidence from win rate
            win_rate_conf = win_rate
        
            # Confidence from Sharpe ratio
            # Sharpe > 2.0 = high confidence
            sharpe_conf = min(sharpe / 2.0, 1.0) if sharpe > 0 else 0.0
        
            # Combined
            return (win_rate_conf * 0.6 + sharpe_conf * 0.4)
        except Exception as e:
            logger.error(f"Error in _calculate_statistical_confidence: {e}")
            raise
    
    def _calculate_regime_confidence(self, market_context: Dict) -> float:
        """Calculate regime detection confidence"""
        try:
            regime_confidence = market_context.get('regime_confidence', 0.5)
            regime_stability = market_context.get('regime_stability', 0.5)
        
            # Both must be high
            return min(regime_confidence, regime_stability)
        except Exception as e:
            logger.error(f"Error in _calculate_regime_confidence: {e}")
            raise
    
    def _calculate_execution_confidence(
        self,
        signal: Dict,
        market_context: Dict
    ) -> float:
        """Calculate execution feasibility confidence"""
        try:
            liquidity_score = market_context.get('liquidity_score', 0.5)
            spread_bps = market_context.get('spread_bps', 20.0)
        
            # High liquidity = high confidence
            liquidity_conf = liquidity_score
        
            # Low spread = high confidence
            # 10 bps = 1.0, 50 bps = 0.0
            spread_conf = max(0.0, 1.0 - (spread_bps - 10.0) / 40.0)
        
            return (liquidity_conf * 0.6 + spread_conf * 0.4)
        except Exception as e:
            logger.error(f"Error in _calculate_execution_confidence: {e}")
            raise
    
    def _calculate_tail_risk_confidence(
        self,
        signal: Dict,
        market_context: Dict
    ) -> float:
        """Calculate tail risk bounded confidence"""
        try:
            stop_loss = signal.get('stop_loss')
            entry_price = signal['price']
        
            if not stop_loss:
                return 0.0  # No stop loss = no confidence
        
            # Calculate max loss
            max_loss_pct = abs(stop_loss - entry_price) / entry_price
        
            # Tight stop = high confidence
            # 2% stop = 1.0, 10% stop = 0.0
            if max_loss_pct <= 0.02:
                return 1.0
            elif max_loss_pct <= 0.05:
                return 0.7
            elif max_loss_pct <= 0.10:
                return 0.3
            else:
                return 0.0
        except Exception as e:
            logger.error(f"Error in _calculate_tail_risk_confidence: {e}")
            raise
    
    def _calculate_model_stability_confidence(
        self,
        signal: Dict,
        historical_data: Optional[Dict]
    ) -> float:
        """Calculate model stability confidence"""
        try:
            if not historical_data:
                return 0.5
        
            # Check if performance is stable over time
            recent_win_rate = historical_data.get('recent_win_rate', 0.5)
            overall_win_rate = historical_data.get('win_rate', 0.5)
        
            # Stable if recent matches overall
            stability = 1.0 - abs(recent_win_rate - overall_win_rate)
        
            return stability
        except Exception as e:
            logger.error(f"Error in _calculate_model_stability_confidence: {e}")
            raise


class ConfidenceVectorValidator:
    """
    Validates that confidence vectors are used correctly.
    
    Enforces:
    - Minimum confidence dominates (not average)
    - No single confidence scores
    - All dimensions present
    """
    
    @staticmethod
    def validate(vector: ConfidenceVector, threshold: float = 0.6) -> bool:
        """
        Validate confidence vector.
        
        Returns:
            True if valid and passes threshold
        """
        # Check all dimensions present
        try:
            if any([
                vector.statistical_confidence is None,
                vector.regime_confidence is None,
                vector.execution_confidence is None,
                vector.tail_risk_confidence is None,
                vector.model_stability_confidence is None
            ]):
                logger.error("Confidence vector missing dimensions")
                return False
        
            # Check minimum confidence (not average)
            if vector.penalized_minimum_confidence < threshold:
                logger.info(
                    f"Confidence vector fails threshold: "
                    f"min={vector.penalized_minimum_confidence:.2%} < {threshold:.2%}"
                )
                return False
        
            return True
        except Exception as e:
            logger.error(f"Error in validate: {e}")
            raise
    
    @staticmethod
    def enforce_minimum_dominance(vector: ConfidenceVector) -> float:
        """
        Enforce that minimum confidence is used.
        
        Returns:
            Minimum confidence (penalized)
        """
        # This is the ONLY confidence that should be used for decisions
        return vector.penalized_minimum_confidence


# Global singleton
_global_builder: Optional[MultiDimensionalConfidenceBuilder] = None


def get_global_builder() -> MultiDimensionalConfidenceBuilder:
    """Get global builder singleton"""
    try:
        global _global_builder
        if _global_builder is None:
            _global_builder = MultiDimensionalConfidenceBuilder()
        return _global_builder
    except Exception as e:
        logger.error(f"Error in get_global_builder: {e}")
        raise


def build_confidence_vector(
    signal: Dict,
    market_context: Dict,
    historical_data: Optional[Dict] = None
) -> ConfidenceVector:
    """Build confidence vector using global builder"""
    return get_global_builder().build_confidence_vector(signal, market_context, historical_data)


def validate_confidence_vector(vector: ConfidenceVector, threshold: float = 0.6) -> bool:
    """Validate confidence vector"""
    return ConfidenceVectorValidator.validate(vector, threshold)
