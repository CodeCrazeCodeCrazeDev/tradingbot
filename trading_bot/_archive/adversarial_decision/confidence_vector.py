"""
Confidence Vector System - STEP 5

Calibrated confidence estimates for each claim.
NO VERBAL CONFIDENCE - only numerical vectors.

Applies:
- Sample-size penalties
- Regime novelty decay
- Alpha half-life decay

Minimum confidence dominates (averages are irrelevant).
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import numpy as np
import logging

from .claim_system import TradeClaim, ClaimType
from .verification_system import VerificationResult

logger = logging.getLogger(__name__)


@dataclass
class ConfidenceThresholds:
    """Confidence thresholds for decision making"""
    minimum_acceptable: float = 0.6
    statistical_min: float = 0.6
    regime_min: float = 0.6
    execution_min: float = 0.7
    tail_risk_min: float = 0.7
    model_stability_min: float = 0.6


@dataclass
class ConfidenceVector:
    """
    Multi-dimensional confidence vector.
    Minimum confidence dominates - averages are irrelevant.
    """
    statistical_confidence: float
    regime_confidence: float
    execution_confidence: float
    tail_risk_confidence: float
    model_stability_confidence: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def get_minimum(self) -> float:
        """Get minimum confidence (dominates decision)"""
        return min(
            self.statistical_confidence,
            self.regime_confidence,
            self.execution_confidence,
            self.tail_risk_confidence,
            self.model_stability_confidence
        )
    
    def get_average(self) -> float:
        """Get average confidence (for reference only, not decision)"""
        return np.mean([
            self.statistical_confidence,
            self.regime_confidence,
            self.execution_confidence,
            self.tail_risk_confidence,
            self.model_stability_confidence
        ])
    
    def passes_thresholds(self, thresholds: ConfidenceThresholds) -> bool:
        """Check if all confidences pass their thresholds"""
        return (
            self.statistical_confidence >= thresholds.statistical_min and
            self.regime_confidence >= thresholds.regime_min and
            self.execution_confidence >= thresholds.execution_min and
            self.tail_risk_confidence >= thresholds.tail_risk_min and
            self.model_stability_confidence >= thresholds.model_stability_min
        )
    
    def get_weakest_dimension(self) -> str:
        """Get the weakest confidence dimension"""
        confidences = {
            'statistical': self.statistical_confidence,
            'regime': self.regime_confidence,
            'execution': self.execution_confidence,
            'tail_risk': self.tail_risk_confidence,
            'model_stability': self.model_stability_confidence
        }
        return min(confidences.items(), key=lambda x: x[1])[0]


class ConfidenceCalculator:
    """
    Calculates calibrated confidence vectors with penalties.
    
    Applies:
    - Sample-size penalties
    - Regime novelty decay
    - Alpha half-life decay
    """
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.thresholds = ConfidenceThresholds()
        
        # Penalty parameters
        self.min_sample_size = self.config.get('min_sample_size', 100)
        self.regime_novelty_halflife_days = self.config.get('regime_novelty_halflife_days', 30)
        self.alpha_halflife_days = self.config.get('alpha_halflife_days', 90)
        
    def calculate_confidence_vector(
        self,
        claims: List[TradeClaim],
        verification_results: Dict[ClaimType, List[VerificationResult]],
        market_data: Dict[str, Any],
        signal_data: Dict[str, Any],
        historical_data: Dict[str, Any]
    ) -> ConfidenceVector:
        """
        Calculate calibrated confidence vector.
        
        Returns:
            ConfidenceVector with all dimensions calculated
        """
        # Calculate each confidence dimension
        statistical_conf = self._calculate_statistical_confidence(
            claims, verification_results, signal_data
        )
        
        regime_conf = self._calculate_regime_confidence(
            claims, verification_results, market_data, historical_data
        )
        
        execution_conf = self._calculate_execution_confidence(
            claims, verification_results, market_data
        )
        
        tail_risk_conf = self._calculate_tail_risk_confidence(
            claims, verification_results, market_data
        )
        
        model_stability_conf = self._calculate_model_stability_confidence(
            signal_data, historical_data
        )
        
        return ConfidenceVector(
            statistical_confidence=statistical_conf,
            regime_confidence=regime_conf,
            execution_confidence=execution_conf,
            tail_risk_confidence=tail_risk_conf,
            model_stability_confidence=model_stability_conf
        )
    
    def _calculate_statistical_confidence(
        self,
        claims: List[TradeClaim],
        verification_results: Dict[ClaimType, List[VerificationResult]],
        signal_data: Dict[str, Any]
    ) -> float:
        """Calculate statistical confidence with sample-size penalty"""
        base_confidence = 0.5
        
        # Get expectancy claim
        expectancy_claim = next(
            (c for c in claims if c.claim_type == ClaimType.SIGNAL_EXPECTANCY),
            None
        )
        
        if not expectancy_claim:
            return 0.3
        
        # Sample size penalty
        sample_size = expectancy_claim.evidence.get('sample_size', 0)
        sample_penalty = self._apply_sample_size_penalty(sample_size)
        
        # Verification score
        verifications = verification_results.get(ClaimType.SIGNAL_EXPECTANCY, [])
        if verifications:
            avg_verification = np.mean([v.score for v in verifications])
            base_confidence = avg_verification
        
        # Apply penalty
        confidence = base_confidence * sample_penalty
        
        # Expectancy check
        expectancy = expectancy_claim.evidence.get('expectancy', 0.0)
        if expectancy <= 0:
            confidence *= 0.3
        
        # Win rate sanity check
        win_rate = expectancy_claim.evidence.get('win_rate', 0.0)
        if win_rate < 0.3 or win_rate > 0.9:
            confidence *= 0.7
        
        return np.clip(confidence, 0.0, 1.0)
    
    def _calculate_regime_confidence(
        self,
        claims: List[TradeClaim],
        verification_results: Dict[ClaimType, List[VerificationResult]],
        market_data: Dict[str, Any],
        historical_data: Dict[str, Any]
    ) -> float:
        """Calculate regime confidence with novelty decay"""
        base_confidence = 0.5
        
        # Get regime claim
        regime_claim = next(
            (c for c in claims if c.claim_type == ClaimType.REGIME_VALIDITY),
            None
        )
        
        if not regime_claim:
            return 0.3
        
        # Verification score
        verifications = verification_results.get(ClaimType.REGIME_VALIDITY, [])
        if verifications:
            avg_verification = np.mean([v.score for v in verifications])
            base_confidence = avg_verification
        
        # Regime novelty decay
        regime = market_data.get('regime', 'UNKNOWN')
        regime_first_seen = historical_data.get('regime_first_seen', {}).get(regime)
        
        if regime_first_seen:
            days_since_seen = (datetime.utcnow() - regime_first_seen).days
            novelty_penalty = self._apply_regime_novelty_decay(days_since_seen)
        else:
            # Never seen this regime - heavy penalty
            novelty_penalty = 0.3
        
        # Regime stability
        regime_stability = regime_claim.evidence.get('regime_stability', 0.0)
        stability_factor = 0.7 + (regime_stability * 0.3)
        
        confidence = base_confidence * novelty_penalty * stability_factor
        
        return np.clip(confidence, 0.0, 1.0)
    
    def _calculate_execution_confidence(
        self,
        claims: List[TradeClaim],
        verification_results: Dict[ClaimType, List[VerificationResult]],
        market_data: Dict[str, Any]
    ) -> float:
        """Calculate execution confidence"""
        base_confidence = 0.5
        
        # Get execution and liquidity claims
        exec_claim = next(
            (c for c in claims if c.claim_type == ClaimType.EXECUTION_FEASIBILITY),
            None
        )
        liq_claim = next(
            (c for c in claims if c.claim_type == ClaimType.LIQUIDITY_SLIPPAGE),
            None
        )
        
        if not exec_claim or not liq_claim:
            return 0.3
        
        # Execution verification
        exec_verifications = verification_results.get(ClaimType.EXECUTION_FEASIBILITY, [])
        if exec_verifications:
            exec_score = np.mean([v.score for v in exec_verifications])
        else:
            exec_score = 0.5
        
        # Liquidity verification
        liq_verifications = verification_results.get(ClaimType.LIQUIDITY_SLIPPAGE, [])
        if liq_verifications:
            liq_score = np.mean([v.score for v in liq_verifications])
        else:
            liq_score = 0.5
        
        # Combined confidence (minimum dominates)
        confidence = min(exec_score, liq_score)
        
        # Latency penalty
        latency = exec_claim.evidence.get('latency', 0.0)
        if latency > 100:
            confidence *= 0.5
        elif latency > 50:
            confidence *= 0.8
        
        # Spread penalty
        spread = liq_claim.evidence.get('bid_ask_spread', 0.0)
        if spread > 0.001:  # 10 bps
            confidence *= 0.8
        
        return np.clip(confidence, 0.0, 1.0)
    
    def _calculate_tail_risk_confidence(
        self,
        claims: List[TradeClaim],
        verification_results: Dict[ClaimType, List[VerificationResult]],
        market_data: Dict[str, Any]
    ) -> float:
        """Calculate tail risk confidence"""
        base_confidence = 0.5
        
        # Get tail risk claim
        tail_claim = next(
            (c for c in claims if c.claim_type == ClaimType.TAIL_RISK_EXPOSURE),
            None
        )
        
        if not tail_claim:
            return 0.3
        
        # Verification score
        verifications = verification_results.get(ClaimType.TAIL_RISK_EXPOSURE, [])
        if verifications:
            avg_verification = np.mean([v.score for v in verifications])
            base_confidence = avg_verification
        
        # CVaR check
        cvar_95 = tail_claim.evidence.get('cvar_95', 0.0)
        if cvar_95 > 0.05:
            base_confidence *= 0.5
        elif cvar_95 > 0.03:
            base_confidence *= 0.8
        
        # Kurtosis check (fat tails)
        kurtosis = tail_claim.evidence.get('kurtosis', 3.0)
        if kurtosis > 5.0:
            base_confidence *= 0.6
        elif kurtosis > 4.0:
            base_confidence *= 0.8
        
        # Volatility regime check
        volatility_regime = market_data.get('volatility_regime', 'NORMAL')
        if volatility_regime in ['EXTREME', 'CRISIS']:
            base_confidence *= 0.3
        elif volatility_regime == 'HIGH':
            base_confidence *= 0.7
        
        return np.clip(base_confidence, 0.0, 1.0)
    
    def _calculate_model_stability_confidence(
        self,
        signal_data: Dict[str, Any],
        historical_data: Dict[str, Any]
    ) -> float:
        """Calculate model stability confidence with alpha half-life decay"""
        base_confidence = 0.5
        
        # Alpha half-life decay
        model_last_updated = signal_data.get('model_last_updated')
        if model_last_updated:
            days_since_update = (datetime.utcnow() - model_last_updated).days
            alpha_decay = self._apply_alpha_halflife_decay(days_since_update)
        else:
            alpha_decay = 0.5
        
        # In-sample vs out-of-sample performance
        in_sample_sharpe = signal_data.get('in_sample_sharpe', 0.0)
        out_sample_sharpe = signal_data.get('out_sample_sharpe', 0.0)
        
        if in_sample_sharpe > 0 and out_sample_sharpe > 0:
            performance_ratio = out_sample_sharpe / in_sample_sharpe
            if performance_ratio < 0.5:
                # Severe overfit
                base_confidence = 0.3
            elif performance_ratio < 0.7:
                base_confidence = 0.6
            else:
                base_confidence = 0.9
        
        # Recent performance
        recent_sharpe = historical_data.get('recent_sharpe', 0.0)
        if recent_sharpe < 0:
            base_confidence *= 0.5
        elif recent_sharpe < 0.5:
            base_confidence *= 0.8
        
        confidence = base_confidence * alpha_decay
        
        return np.clip(confidence, 0.0, 1.0)
    
    def _apply_sample_size_penalty(self, sample_size: int) -> float:
        """
        Apply sample-size penalty.
        
        Returns penalty multiplier (0.0 to 1.0)
        """
        if sample_size < 30:
            return 0.3
        elif sample_size < self.min_sample_size:
            # Linear interpolation between 30 and min_sample_size
            return 0.3 + (sample_size - 30) / (self.min_sample_size - 30) * 0.5
        else:
            # Logarithmic growth after min_sample_size
            return min(0.8 + np.log10(sample_size / self.min_sample_size) * 0.1, 1.0)
    
    def _apply_regime_novelty_decay(self, days_since_seen: int) -> float:
        """
        Apply regime novelty decay using half-life.
        
        Returns decay multiplier (0.0 to 1.0)
        """
        if days_since_seen == 0:
            return 1.0
        
        # Exponential decay with half-life
        decay = 0.5 ** (days_since_seen / self.regime_novelty_halflife_days)
        
        # Minimum confidence for very old regimes
        return max(decay, 0.3)
    
    def _apply_alpha_halflife_decay(self, days_since_update: int) -> float:
        """
        Apply alpha half-life decay.
        
        Returns decay multiplier (0.0 to 1.0)
        """
        if days_since_update == 0:
            return 1.0
        
        # Exponential decay with half-life
        decay = 0.5 ** (days_since_update / self.alpha_halflife_days)
        
        # Minimum confidence for very stale models
        return max(decay, 0.2)
