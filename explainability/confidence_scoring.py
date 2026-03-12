"""
Phase 7: Explainability - Confidence Scoring
Quantifies uncertainty in trading decisions
"""

import torch
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ConfidenceMetrics:
    """Comprehensive confidence metrics."""
    overall: float
    signal_strength: float
    prediction_uncertainty: float
    market_uncertainty: float
    data_quality: float
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict:
        return {
            'overall': self.overall,
            'signal_strength': self.signal_strength,
            'prediction_uncertainty': self.prediction_uncertainty,
            'market_uncertainty': self.market_uncertainty,
            'data_quality': self.data_quality,
            'timestamp': self.timestamp
        }


class ConfidenceScorer:
    """
    Quantifies confidence in trading decisions.
    Considers multiple sources of uncertainty.
    """
    
    def __init__(self):
        # Confidence thresholds
        self.thresholds = {
            'high': 0.8,
            'medium': 0.5,
            'low': 0.2
        }
        
        # Component weights
        self.weights = {
            'signal_strength': 0.3,
            'prediction_uncertainty': 0.3,
            'market_uncertainty': 0.2,
            'data_quality': 0.2
        }
        
        # Historical metrics
        self.history = []
        
        logger.info("✅ Confidence Scorer initialized")
    
    def calculate_confidence(
        self,
        predictions: torch.Tensor,
        market_state: Dict,
        data_quality: Optional[Dict] = None
    ) -> ConfidenceMetrics:
        """
        Calculate comprehensive confidence metrics.
        
        Args:
            predictions: Model predictions
            market_state: Current market conditions
            data_quality: Optional data quality metrics
        
        Returns:
            ConfidenceMetrics object
        """
        # 1. Signal strength
        signal_strength = self._calculate_signal_strength(predictions)
        
        # 2. Prediction uncertainty
        pred_uncertainty = self._calculate_prediction_uncertainty(predictions)
        
        # 3. Market uncertainty
        market_uncertainty = self._calculate_market_uncertainty(market_state)
        
        # 4. Data quality
        if data_quality is None:
            data_quality = {'score': 1.0}  # Default perfect quality
        quality_score = self._calculate_data_quality(data_quality)
        
        # Combine metrics
        overall = self._combine_metrics(
            signal_strength,
            pred_uncertainty,
            market_uncertainty,
            quality_score
        )
        
        metrics = ConfidenceMetrics(
            overall=overall,
            signal_strength=signal_strength,
            prediction_uncertainty=pred_uncertainty,
            market_uncertainty=market_uncertainty,
            data_quality=quality_score
        )
        
        # Update history
        self.history.append(metrics)
        if len(self.history) > 1000:  # Keep last 1000
            self.history.pop(0)
        
        return metrics
    
    def _calculate_signal_strength(
        self,
        predictions: torch.Tensor
    ) -> float:
        """
        Calculate signal strength from predictions.
        Strong signal = clear decision with high probability.
        """
        # Get probabilities
        probs = torch.softmax(predictions, dim=-1)
        
        # Maximum probability
        max_prob = float(torch.max(probs).item())
        
        # Entropy of distribution
        entropy = float(-torch.sum(probs * torch.log(probs + 1e-10)).item())
        max_entropy = float(-torch.log(torch.tensor(1.0 / len(probs))).item())
        
        # Normalize entropy to [0, 1]
        entropy_score = 1.0 - (entropy / max_entropy)
        
        # Combine max prob and entropy
        return 0.7 * max_prob + 0.3 * entropy_score
    
    def _calculate_prediction_uncertainty(
        self,
        predictions: torch.Tensor
    ) -> float:
        """
        Calculate prediction uncertainty.
        Low uncertainty = high confidence.
        """
        # Get probabilities
        probs = torch.softmax(predictions, dim=-1)
        
        # Calculate variance
        mean = torch.mean(probs)
        variance = torch.mean((probs - mean) ** 2)
        
        # Convert to confidence score (1 - uncertainty)
        return 1.0 - float(variance.item())
    
    def _calculate_market_uncertainty(
        self,
        market_state: Dict
    ) -> float:
        """
        Calculate market uncertainty.
        Considers volatility, liquidity, and market regime.
        """
        uncertainty_factors = []
        
        # Volatility
        if 'volatility' in market_state:
            vol = market_state['volatility']
            vol_score = 1.0 - min(vol / 0.02, 1.0)  # Cap at 2% volatility
            uncertainty_factors.append(vol_score)
        
        # Liquidity
        if 'liquidity' in market_state:
            liq = market_state['liquidity']
            liq_score = min(liq / 1.0, 1.0)  # Normalize to [0, 1]
            uncertainty_factors.append(liq_score)
        
        # Market regime
        if 'regime' in market_state:
            regime = market_state['regime']
            regime_scores = {
                'trending': 0.8,
                'ranging': 0.6,
                'high_volatility': 0.3,
                'crisis': 0.1
            }
            regime_score = regime_scores.get(regime, 0.5)
            uncertainty_factors.append(regime_score)
        
        # Average all factors
        if uncertainty_factors:
            return float(np.mean(uncertainty_factors))
        else:
            return 0.5  # Default medium uncertainty
    
    def _calculate_data_quality(self, quality_metrics: Dict) -> float:
        """
        Calculate data quality score.
        Considers completeness, timeliness, and accuracy.
        """
        quality_scores = []
        
        # Overall quality score
        if 'score' in quality_metrics:
            quality_scores.append(quality_metrics['score'])
        
        # Completeness
        if 'completeness' in quality_metrics:
            quality_scores.append(quality_metrics['completeness'])
        
        # Timeliness
        if 'timeliness' in quality_metrics:
            quality_scores.append(quality_metrics['timeliness'])
        
        # Accuracy
        if 'accuracy' in quality_metrics:
            quality_scores.append(quality_metrics['accuracy'])
        
        # Average all scores
        if quality_scores:
            return float(np.mean(quality_scores))
        else:
            return quality_metrics.get('score', 1.0)
    
    def _combine_metrics(
        self,
        signal_strength: float,
        pred_uncertainty: float,
        market_uncertainty: float,
        data_quality: float
    ) -> float:
        """Combine all metrics into overall confidence."""
        return float(np.average(
            [signal_strength, pred_uncertainty, market_uncertainty, data_quality],
            weights=[
                self.weights['signal_strength'],
                self.weights['prediction_uncertainty'],
                self.weights['market_uncertainty'],
                self.weights['data_quality']
            ]
        ))
    
    def get_confidence_level(self, confidence: float) -> str:
        """Get qualitative confidence level."""
        if confidence >= self.thresholds['high']:
            return 'high'
        elif confidence >= self.thresholds['medium']:
            return 'medium'
        elif confidence >= self.thresholds['low']:
            return 'low'
        else:
            return 'very_low'
    
    def analyze_confidence_trend(
        self,
        window_size: int = 20
    ) -> Dict:
        """
        Analyze trend in confidence metrics.
        
        Args:
            window_size: Number of recent samples to analyze
        
        Returns:
            Dictionary with trend analysis
        """
        if len(self.history) < 2:
            return {'trend': 'insufficient_data'}
        
        # Get recent metrics
        recent = self.history[-window_size:]
        
        # Calculate trends
        trends = {}
        
        for field in ['overall', 'signal_strength', 'prediction_uncertainty',
                     'market_uncertainty', 'data_quality']:
            values = [getattr(m, field) for m in recent]
            
            # Linear regression for trend
            x = np.arange(len(values))
            slope, _ = np.polyfit(x, values, 1)
            
            # Determine trend direction
            if abs(slope) < 0.001:
                direction = 'stable'
            else:
                direction = 'improving' if slope > 0 else 'deteriorating'
            
            trends[field] = {
                'direction': direction,
                'slope': float(slope),
                'current': values[-1],
                'mean': float(np.mean(values)),
                'std': float(np.std(values))
            }
        
        return {
            'trends': trends,
            'window_size': window_size,
            'samples': len(recent)
        }
    
    def explain_confidence(
        self,
        metrics: ConfidenceMetrics,
        include_trend: bool = True
    ) -> str:
        """
        Generate explanation of confidence metrics.
        
        Args:
            metrics: Confidence metrics to explain
            include_trend: Whether to include trend analysis
        
        Returns:
            Natural language explanation
        """
        level = self.get_confidence_level(metrics.overall)
        
        explanation = [
            f"Overall Confidence: {metrics.overall:.1%} ({level})\n",
            "Component Breakdown:",
            f"- Signal Strength: {metrics.signal_strength:.1%}",
            f"- Prediction Certainty: {metrics.prediction_uncertainty:.1%}",
            f"- Market Certainty: {metrics.market_uncertainty:.1%}",
            f"- Data Quality: {metrics.data_quality:.1%}"
        ]
        
        if include_trend and len(self.history) >= 2:
            trend_analysis = self.analyze_confidence_trend()
            
            explanation.append("\nTrend Analysis:")
            for field, trend in trend_analysis['trends'].items():
                explanation.append(
                    f"- {field}: {trend['direction']} "
                    f"(current: {trend['current']:.1%})"
                )
        
        return "\n".join(explanation)
    
    def save_state(self, filepath: str):
        """Save confidence scorer state."""
        state = {
            'thresholds': self.thresholds,
            'weights': self.weights,
            'history': [m.to_dict() for m in self.history]
        }
        torch.save(state, filepath)
        logger.info(f"💾 Confidence Scorer state saved to {filepath}")
    
    def load_state(self, filepath: str):
        """Load confidence scorer state."""
        state = torch.load(filepath)
        
        self.thresholds = state['thresholds']
        self.weights = state['weights']
        
        self.history = [
            ConfidenceMetrics(**m) for m in state['history']
        ]
        
        logger.info(f"📂 Confidence Scorer state loaded from {filepath}")
        logger.info(f"   History samples: {len(self.history)}")
