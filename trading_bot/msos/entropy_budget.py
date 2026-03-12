"""
AlphaAlgo MSOS - Entropy Budget Manager

Maintain an explicit uncertainty budget.

When uncertainty exceeds measurable bounds:
- Exposure is reduced globally
- Capital is protected regardless of signals

Unquantifiable risk is treated as hostile.
Each position consumes entropy. Complexity must never exceed controllability.

Author: AlphaAlgo MSOS
"""

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Deque, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


class EntropyLevel(Enum):
    """Entropy/uncertainty levels"""
    LOW = auto()           # System well understood
    MODERATE = auto()      # Normal uncertainty
    HIGH = auto()          # Elevated uncertainty
    EXTREME = auto()       # Near budget limit
    EXCEEDED = auto()      # Budget exceeded


class UncertaintySource(Enum):
    """Sources of uncertainty"""
    MODEL = auto()         # Model uncertainty
    DATA = auto()          # Data quality uncertainty
    REGIME = auto()        # Regime uncertainty
    EXECUTION = auto()     # Execution uncertainty
    CORRELATION = auto()   # Correlation uncertainty
    TAIL = auto()          # Tail risk uncertainty
    UNKNOWN = auto()       # Unknown unknowns


@dataclass
class UncertaintyBudget:
    """Uncertainty budget allocation"""
    total_budget: float = 1.0  # Total entropy budget
    consumed: float = 0.0
    remaining: float = 1.0
    by_source: Dict[UncertaintySource, float] = field(default_factory=dict)
    by_strategy: Dict[str, float] = field(default_factory=dict)
    level: EntropyLevel = EntropyLevel.LOW
    
    def consume(self, amount: float, source: UncertaintySource, strategy_id: str = "system"):
        """Consume entropy budget"""
        try:
            self.consumed += amount
            self.remaining = max(0, self.total_budget - self.consumed)
        
            # Track by source
            if source not in self.by_source:
                self.by_source[source] = 0.0
            self.by_source[source] += amount
        
            # Track by strategy
            if strategy_id not in self.by_strategy:
                self.by_strategy[strategy_id] = 0.0
            self.by_strategy[strategy_id] += amount
        
            # Update level
            self._update_level()
        except Exception as e:
            logger.error(f"Error in consume: {e}")
            raise
    
    def release(self, amount: float, source: UncertaintySource, strategy_id: str = "system"):
        """Release entropy budget"""
        try:
            self.consumed = max(0, self.consumed - amount)
            self.remaining = self.total_budget - self.consumed
        
            if source in self.by_source:
                self.by_source[source] = max(0, self.by_source[source] - amount)
        
            if strategy_id in self.by_strategy:
                self.by_strategy[strategy_id] = max(0, self.by_strategy[strategy_id] - amount)
        
            self._update_level()
        except Exception as e:
            logger.error(f"Error in release: {e}")
            raise
    
    def _update_level(self):
        """Update entropy level"""
        try:
            ratio = self.consumed / self.total_budget
        
            if ratio >= 1.0:
                self.level = EntropyLevel.EXCEEDED
            elif ratio >= 0.8:
                self.level = EntropyLevel.EXTREME
            elif ratio >= 0.6:
                self.level = EntropyLevel.HIGH
            elif ratio >= 0.3:
                self.level = EntropyLevel.MODERATE
            else:
                self.level = EntropyLevel.LOW
        except Exception as e:
            logger.error(f"Error in _update_level: {e}")
            raise
    
    def reset(self):
        """Reset budget"""
        try:
            self.consumed = 0.0
            self.remaining = self.total_budget
            self.by_source.clear()
            self.by_strategy.clear()
            self.level = EntropyLevel.LOW
        except Exception as e:
            logger.error(f"Error in reset: {e}")
            raise


@dataclass
class EntropyConsumption:
    """Record of entropy consumption"""
    source: UncertaintySource
    strategy_id: str
    amount: float
    reason: str
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'source': self.source.name,
            'strategy_id': self.strategy_id,
            'amount': self.amount,
            'reason': self.reason,
            'timestamp': self.timestamp
        }


@dataclass
class EntropyResult:
    """Result from entropy budget check"""
    level: EntropyLevel
    can_add_exposure: bool
    exposure_multiplier: float
    budget: UncertaintyBudget
    warnings: List[str]
    reason: str
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'level': self.level.name,
            'can_add_exposure': self.can_add_exposure,
            'exposure_multiplier': self.exposure_multiplier,
            'consumed': self.budget.consumed,
            'remaining': self.budget.remaining,
            'warnings': self.warnings,
            'reason': self.reason,
            'timestamp': self.timestamp
        }


class UncertaintyEstimator:
    """Estimates uncertainty from various sources"""
    
    def __init__(self, window_size: int = 100):
        try:
            self.window_size = window_size
            self._model_errors: Deque[float] = deque(maxlen=window_size)
            self._data_quality: Deque[float] = deque(maxlen=window_size)
            self._regime_confidence: Deque[float] = deque(maxlen=window_size)
            self._execution_quality: Deque[float] = deque(maxlen=window_size)
            self._correlations: Deque[float] = deque(maxlen=window_size)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def estimate_model_uncertainty(self, prediction_error: float) -> float:
        """Estimate model uncertainty from prediction errors"""
        try:
            self._model_errors.append(prediction_error)
        
            if len(self._model_errors) < 10:
                return 0.5  # Default uncertainty
        
            errors = np.array(list(self._model_errors))
        
            # Uncertainty increases with error magnitude and variance
            mean_error = np.mean(np.abs(errors))
            error_std = np.std(errors)
        
            uncertainty = min(1.0, mean_error + error_std)
            return uncertainty
        except Exception as e:
            logger.error(f"Error in estimate_model_uncertainty: {e}")
            raise
    
    def estimate_data_uncertainty(self, quality_score: float) -> float:
        """Estimate data uncertainty from quality scores"""
        try:
            self._data_quality.append(quality_score)
        
            if len(self._data_quality) < 10:
                return 0.3
        
            # Uncertainty is inverse of quality
            avg_quality = np.mean(list(self._data_quality))
            quality_std = np.std(list(self._data_quality))
        
            uncertainty = (1 - avg_quality) + quality_std
            return min(1.0, uncertainty)
        except Exception as e:
            logger.error(f"Error in estimate_data_uncertainty: {e}")
            raise
    
    def estimate_regime_uncertainty(self, regime_confidence: float) -> float:
        """Estimate regime uncertainty"""
        try:
            self._regime_confidence.append(regime_confidence)
        
            if len(self._regime_confidence) < 10:
                return 0.5
        
            # Uncertainty is inverse of confidence
            avg_confidence = np.mean(list(self._regime_confidence))
            confidence_std = np.std(list(self._regime_confidence))
        
            uncertainty = (1 - avg_confidence) + confidence_std * 2
            return min(1.0, uncertainty)
        except Exception as e:
            logger.error(f"Error in estimate_regime_uncertainty: {e}")
            raise
    
    def estimate_execution_uncertainty(self, fill_rate: float, slippage: float) -> float:
        """Estimate execution uncertainty"""
        try:
            quality = fill_rate * (1 - min(1, slippage * 10))
            self._execution_quality.append(quality)
        
            if len(self._execution_quality) < 10:
                return 0.3
        
            avg_quality = np.mean(list(self._execution_quality))
            return 1 - avg_quality
        except Exception as e:
            logger.error(f"Error in estimate_execution_uncertainty: {e}")
            raise
    
    def estimate_correlation_uncertainty(self, correlation_stability: float) -> float:
        """Estimate correlation uncertainty"""
        try:
            self._correlations.append(correlation_stability)
        
            if len(self._correlations) < 10:
                return 0.4
        
            avg_stability = np.mean(list(self._correlations))
            stability_std = np.std(list(self._correlations))
        
            uncertainty = (1 - avg_stability) + stability_std
            return min(1.0, uncertainty)
        except Exception as e:
            logger.error(f"Error in estimate_correlation_uncertainty: {e}")
            raise


class EntropyBudgetManager:
    """
    Entropy Budget Manager
    
    RULES:
    1. Maintain explicit uncertainty budget
    2. Each position consumes entropy
    3. When budget exceeded → reduce exposure globally
    4. Unquantifiable risk is treated as HOSTILE
    5. Complexity must never exceed controllability
    """
    
    # Budget thresholds
    EXPOSURE_REDUCTION_THRESHOLD = 0.6
    NO_NEW_EXPOSURE_THRESHOLD = 0.8
    FORCE_REDUCTION_THRESHOLD = 0.9
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
            self.logger = logging.getLogger("msos.entropy")
        
            # Budget
            self._budget = UncertaintyBudget(
                total_budget=config.get('total_budget', 1.0) if config else 1.0
            )
        
            # Estimator
            self._estimator = UncertaintyEstimator()
        
            # History
            self._consumption_history: Deque[EntropyConsumption] = deque(maxlen=1000)
        
            self.logger.info("Entropy Budget Manager initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def check_budget(self) -> EntropyResult:
        """Check current entropy budget status"""
        try:
            warnings = []
        
            # Check level
            if self._budget.level == EntropyLevel.EXCEEDED:
                warnings.append("ENTROPY BUDGET EXCEEDED - Force reduction required")
            elif self._budget.level == EntropyLevel.EXTREME:
                warnings.append("Entropy near limit - No new exposure allowed")
            elif self._budget.level == EntropyLevel.HIGH:
                warnings.append("Elevated entropy - Reduce exposure")
        
            # Check by source
            for source, amount in self._budget.by_source.items():
                if amount > 0.3:
                    warnings.append(f"High {source.name} uncertainty: {amount:.2f}")
        
            # Determine exposure multiplier
            ratio = self._budget.consumed / self._budget.total_budget
        
            if ratio >= self.FORCE_REDUCTION_THRESHOLD:
                exposure_multiplier = 0.1
                can_add = False
            elif ratio >= self.NO_NEW_EXPOSURE_THRESHOLD:
                exposure_multiplier = 0.3
                can_add = False
            elif ratio >= self.EXPOSURE_REDUCTION_THRESHOLD:
                exposure_multiplier = 0.5
                can_add = True
            else:
                exposure_multiplier = 1.0
                can_add = True
        
            reason = self._generate_reason(self._budget.level, ratio)
        
            return EntropyResult(
                level=self._budget.level,
                can_add_exposure=can_add,
                exposure_multiplier=exposure_multiplier,
                budget=self._budget,
                warnings=warnings,
                reason=reason
            )
        except Exception as e:
            logger.error(f"Error in check_budget: {e}")
            raise
    
    def consume(
        self,
        source: UncertaintySource,
        amount: float,
        strategy_id: str = "system",
        reason: str = ""
    ) -> EntropyResult:
        """Consume entropy budget"""
        try:
            self._budget.consume(amount, source, strategy_id)
        
            # Record consumption
            self._consumption_history.append(EntropyConsumption(
                source=source,
                strategy_id=strategy_id,
                amount=amount,
                reason=reason
            ))
        
            self.logger.debug(
                f"Entropy consumed: {amount:.3f} from {source.name} ({strategy_id})"
            )
        
            return self.check_budget()
        except Exception as e:
            logger.error(f"Error in consume: {e}")
            raise
    
    def release(
        self,
        source: UncertaintySource,
        amount: float,
        strategy_id: str = "system"
    ) -> EntropyResult:
        """Release entropy budget"""
        try:
            self._budget.release(amount, source, strategy_id)
        
            self.logger.debug(
                f"Entropy released: {amount:.3f} from {source.name} ({strategy_id})"
            )
        
            return self.check_budget()
        except Exception as e:
            logger.error(f"Error in release: {e}")
            raise
    
    def update_from_market(
        self,
        prediction_error: float = 0.0,
        data_quality: float = 1.0,
        regime_confidence: float = 1.0,
        fill_rate: float = 1.0,
        slippage: float = 0.0,
        correlation_stability: float = 1.0
    ) -> EntropyResult:
        """Update entropy budget from market observations"""
        # Estimate uncertainties
        try:
            model_unc = self._estimator.estimate_model_uncertainty(prediction_error)
            data_unc = self._estimator.estimate_data_uncertainty(data_quality)
            regime_unc = self._estimator.estimate_regime_uncertainty(regime_confidence)
            exec_unc = self._estimator.estimate_execution_uncertainty(fill_rate, slippage)
            corr_unc = self._estimator.estimate_correlation_uncertainty(correlation_stability)
        
            # Reset and recalculate budget
            self._budget.reset()
        
            # Consume based on uncertainties
            self._budget.consume(model_unc * 0.2, UncertaintySource.MODEL)
            self._budget.consume(data_unc * 0.15, UncertaintySource.DATA)
            self._budget.consume(regime_unc * 0.25, UncertaintySource.REGIME)
            self._budget.consume(exec_unc * 0.15, UncertaintySource.EXECUTION)
            self._budget.consume(corr_unc * 0.15, UncertaintySource.CORRELATION)
        
            # Add unknown unknowns buffer (always consume some)
            self._budget.consume(0.1, UncertaintySource.UNKNOWN)
        
            return self.check_budget()
        except Exception as e:
            logger.error(f"Error in update_from_market: {e}")
            raise
    
    def add_position_entropy(
        self,
        strategy_id: str,
        position_size: float,
        complexity: float = 0.5
    ) -> EntropyResult:
        """Add entropy for a new position"""
        # Larger positions consume more entropy
        try:
            size_entropy = position_size * 0.5
        
            # Complex strategies consume more entropy
            complexity_entropy = complexity * 0.3
        
            total = size_entropy + complexity_entropy
        
            return self.consume(
                source=UncertaintySource.MODEL,
                amount=total,
                strategy_id=strategy_id,
                reason=f"Position size={position_size:.2%}, complexity={complexity:.2f}"
            )
        except Exception as e:
            logger.error(f"Error in add_position_entropy: {e}")
            raise
    
    def remove_position_entropy(
        self,
        strategy_id: str,
        position_size: float,
        complexity: float = 0.5
    ) -> EntropyResult:
        """Remove entropy when closing a position"""
        try:
            size_entropy = position_size * 0.5
            complexity_entropy = complexity * 0.3
            total = size_entropy + complexity_entropy
        
            return self.release(
                source=UncertaintySource.MODEL,
                amount=total,
                strategy_id=strategy_id
            )
        except Exception as e:
            logger.error(f"Error in remove_position_entropy: {e}")
            raise
    
    def _generate_reason(self, level: EntropyLevel, ratio: float) -> str:
        """Generate explanation"""
        try:
            if level == EntropyLevel.EXCEEDED:
                return f"ENTROPY EXCEEDED ({ratio:.1%}) - FORCE REDUCTION"
            elif level == EntropyLevel.EXTREME:
                return f"Extreme entropy ({ratio:.1%}) - No new exposure"
            elif level == EntropyLevel.HIGH:
                return f"High entropy ({ratio:.1%}) - Reduce exposure"
            elif level == EntropyLevel.MODERATE:
                return f"Moderate entropy ({ratio:.1%}) - Monitor"
            else:
                return f"Low entropy ({ratio:.1%}) - Normal operations"
        except Exception as e:
            logger.error(f"Error in _generate_reason: {e}")
            raise
    
    def get_budget(self) -> UncertaintyBudget:
        """Get current budget"""
        return self._budget
    
    def get_strategy_entropy(self, strategy_id: str) -> float:
        """Get entropy consumed by a strategy"""
        return self._budget.by_strategy.get(strategy_id, 0.0)
    
    def get_source_entropy(self, source: UncertaintySource) -> float:
        """Get entropy from a source"""
        return self._budget.by_source.get(source, 0.0)
    
    def can_add_exposure(self) -> bool:
        """Check if new exposure can be added"""
        return self._budget.level not in [EntropyLevel.EXTREME, EntropyLevel.EXCEEDED]
    
    def get_exposure_multiplier(self) -> float:
        """Get exposure multiplier based on entropy"""
        try:
            result = self.check_budget()
            return result.exposure_multiplier
        except Exception as e:
            logger.error(f"Error in get_exposure_multiplier: {e}")
            raise
