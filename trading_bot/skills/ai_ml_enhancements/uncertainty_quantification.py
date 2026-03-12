"""
Skill #24: Uncertainty Quantification
=====================================

Quantifies prediction uncertainty using Bayesian methods
and ensemble disagreement.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class UncertaintyEstimate:
    """Uncertainty estimate for a prediction."""
    aleatoric: float  # Data uncertainty
    epistemic: float  # Model uncertainty
    total: float
    confidence_interval: tuple
    calibration_score: float


@dataclass
class UncertaintyResult:
    """Complete uncertainty quantification result."""
    prediction: float
    uncertainty: UncertaintyEstimate
    ensemble_predictions: List[float]
    ensemble_std: float
    is_reliable: bool
    trading_signal: str


class UncertaintyQuantifier:
    """Bayesian uncertainty quantification for predictions."""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.num_ensemble = self.config.get('num_ensemble', 10)
            self.dropout_rate = self.config.get('dropout_rate', 0.1)
            self.ensemble_weights = [np.random.randn(10) * 0.1 for _ in range(self.num_ensemble)]
            logger.info("UncertaintyQuantifier initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def quantify(self, prices: np.ndarray, volumes: np.ndarray) -> UncertaintyResult:
        """Quantify prediction uncertainty."""
        try:
            if len(prices) < 20:
                return self._create_empty_result()
        
            features = self._extract_features(prices, volumes)
        
            # Get ensemble predictions
            predictions = []
            for weights in self.ensemble_weights:
                pred = self._predict_with_dropout(features, weights)
                predictions.append(pred)
        
            mean_pred = np.mean(predictions)
            std_pred = np.std(predictions)
        
            # Calculate uncertainty components
            aleatoric = self._estimate_aleatoric(prices)
            epistemic = std_pred
            total = np.sqrt(aleatoric**2 + epistemic**2)
        
            # Confidence interval
            ci = (mean_pred - 1.96 * total, mean_pred + 1.96 * total)
        
            # Calibration score
            calibration = self._calculate_calibration(predictions)
        
            uncertainty = UncertaintyEstimate(
                aleatoric=aleatoric,
                epistemic=epistemic,
                total=total,
                confidence_interval=ci,
                calibration_score=calibration
            )
        
            is_reliable = total < 0.1 and calibration > 0.7
            signal = self._generate_signal(mean_pred, uncertainty, is_reliable)
        
            return UncertaintyResult(
                prediction=mean_pred,
                uncertainty=uncertainty,
                ensemble_predictions=predictions,
                ensemble_std=std_pred,
                is_reliable=is_reliable,
                trading_signal=signal
            )
        except Exception as e:
            logger.error(f"Error in quantify: {e}")
            raise
    
    def _extract_features(self, prices: np.ndarray, volumes: np.ndarray) -> np.ndarray:
        """Extract features."""
        try:
            returns = np.diff(prices) / prices[:-1]
            return np.array([
                np.mean(returns[-10:]), np.std(returns[-10:]),
                np.mean(returns[-5:]), np.std(returns[-5:]),
                prices[-1] / prices[-10] - 1,
                np.mean(volumes[-10:]) / np.mean(volumes),
                np.max(returns[-10:]), np.min(returns[-10:]),
                self._calculate_trend(prices), 0
            ])
        except Exception as e:
            logger.error(f"Error in _extract_features: {e}")
            raise
    
    def _calculate_trend(self, prices: np.ndarray) -> float:
        """Calculate trend strength."""
        try:
            x = np.arange(min(20, len(prices)))
            y = prices[-len(x):]
            return np.polyfit(x, y, 1)[0] / np.mean(y)
        except Exception as e:
            logger.error(f"Error in _calculate_trend: {e}")
            raise
    
    def _predict_with_dropout(self, features: np.ndarray, weights: np.ndarray) -> float:
        """Predict with MC dropout."""
        try:
            mask = np.random.binomial(1, 1 - self.dropout_rate, len(weights))
            masked_weights = weights * mask / (1 - self.dropout_rate)
            return float(np.dot(features, masked_weights))
        except Exception as e:
            logger.error(f"Error in _predict_with_dropout: {e}")
            raise
    
    def _estimate_aleatoric(self, prices: np.ndarray) -> float:
        """Estimate aleatoric (data) uncertainty."""
        try:
            returns = np.diff(prices) / prices[:-1]
            return float(np.std(returns[-20:]))
        except Exception as e:
            logger.error(f"Error in _estimate_aleatoric: {e}")
            raise
    
    def _calculate_calibration(self, predictions: List[float]) -> float:
        """Calculate calibration score."""
        # Simplified: check if predictions are well-distributed
        try:
            std = np.std(predictions)
            if std < 0.01:
                return 0.5  # Too concentrated
            elif std > 0.5:
                return 0.3  # Too spread
            return 0.8
        except Exception as e:
            logger.error(f"Error in _calculate_calibration: {e}")
            raise
    
    def _generate_signal(
        self,
        prediction: float,
        uncertainty: UncertaintyEstimate,
        is_reliable: bool
    ) -> str:
        """Generate trading signal."""
        try:
            if not is_reliable:
                return f"UNCERTAIN: High uncertainty ({uncertainty.total:.2f}), avoid trading"
        
            if prediction > 0.02:
                return f"BUY: Predicted return {prediction:.1%} ± {uncertainty.total:.1%}"
            elif prediction < -0.02:
                return f"SELL: Predicted return {prediction:.1%} ± {uncertainty.total:.1%}"
            return f"NEUTRAL: Predicted return {prediction:.1%} ± {uncertainty.total:.1%}"
        except Exception as e:
            logger.error(f"Error in _generate_signal: {e}")
            raise
    
    def _create_empty_result(self) -> UncertaintyResult:
        """Create empty result."""
        return UncertaintyResult(
            prediction=0,
            uncertainty=UncertaintyEstimate(0, 0, 0, (0, 0), 0),
            ensemble_predictions=[],
            ensemble_std=0,
            is_reliable=False,
            trading_signal="Insufficient data"
        )
