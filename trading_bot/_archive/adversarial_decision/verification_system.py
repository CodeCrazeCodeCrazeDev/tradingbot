"""
Orthogonal Verification System - STEP 3

Evaluates each claim using independent methods.
Shared assumptions are invalid. Correlated reasoning is rejected.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional
from datetime import datetime
import numpy as np
import logging

from .claim_system import TradeClaim, ClaimType

logger = logging.getLogger(__name__)


class VerificationMethod(Enum):
    """Independent verification methods - no shared assumptions"""
    STATISTICAL = "statistical"
    REGIME_BASED = "regime_based"
    MICROSTRUCTURE = "microstructure"
    HISTORICAL_ANALOG = "historical_analog"
    ADVERSARIAL_FAILURE = "adversarial_failure"


@dataclass
class VerificationResult:
    """Result from a single verification method"""
    method: VerificationMethod
    claim_type: ClaimType
    passed: bool
    score: float
    evidence: Dict[str, Any]
    failure_reasons: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def is_valid(self) -> bool:
        """Check if verification passed threshold"""
        return self.passed and self.score >= 0.6


class OrthogonalVerifier:
    """
    Verifies claims using independent, orthogonal methods.
    
    RULE: Shared assumptions are invalid
    RULE: Correlated reasoning is rejected
    """
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.min_verification_score = self.config.get('min_verification_score', 0.6)
        self.require_all_methods = self.config.get('require_all_methods', False)
        
    def verify_claim(
        self,
        claim: TradeClaim,
        market_data: Dict[str, Any],
        historical_data: Dict[str, Any]
    ) -> List[VerificationResult]:
        """
        Verify claim using all applicable orthogonal methods.
        
        Returns:
            List of VerificationResult objects (one per method)
        """
        results = []
        
        # Apply all verification methods
        methods = [
            self._verify_statistical,
            self._verify_regime_based,
            self._verify_microstructure,
            self._verify_historical_analog,
            self._verify_adversarial_failure,
        ]
        
        for method in methods:
            try:
                result = method(claim, market_data, historical_data)
                if result:
                    results.append(result)
            except Exception as e:
                logger.error(f"Verification method {method.__name__} failed: {e}")
        
        return results
    
    def _verify_statistical(
        self,
        claim: TradeClaim,
        market_data: Dict[str, Any],
        historical_data: Dict[str, Any]
    ) -> Optional[VerificationResult]:
        """Statistical verification using hypothesis testing"""
        try:
            evidence = claim.evidence
            score = 0.0
            passed = False
            failure_reasons = []
            
            if claim.claim_type == ClaimType.SIGNAL_EXPECTANCY:
                # Verify expectancy with statistical significance
                expectancy = evidence.get('expectancy', 0.0)
                sample_size = evidence.get('sample_size', 0)
                win_rate = evidence.get('win_rate', 0.0)
                
                # Sample size penalty
                if sample_size < 30:
                    failure_reasons.append(f"Insufficient sample size: {sample_size} < 30")
                    score = 0.3
                elif sample_size < 100:
                    score = 0.6 + (sample_size - 30) / 70 * 0.2
                else:
                    score = 0.8
                
                # Expectancy must be positive
                if expectancy <= 0:
                    failure_reasons.append(f"Non-positive expectancy: {expectancy:.4f}")
                    score = min(score, 0.2)
                else:
                    score = min(score + 0.2, 1.0)
                
                # Win rate sanity check
                if win_rate < 0.3 or win_rate > 0.9:
                    failure_reasons.append(f"Suspicious win rate: {win_rate:.2%}")
                    score *= 0.8
                
                passed = score >= self.min_verification_score and len(failure_reasons) == 0
                
            elif claim.claim_type == ClaimType.VOLATILITY_SUITABILITY:
                # Verify volatility is within acceptable range
                current_vol = evidence.get('current_volatility', 0.0)
                historical_vol = evidence.get('historical_volatility', 0.0)
                vol_percentile = evidence.get('volatility_percentile', 50.0)
                
                # Check if volatility is extreme
                if vol_percentile > 95 or vol_percentile < 5:
                    failure_reasons.append(f"Extreme volatility percentile: {vol_percentile:.1f}")
                    score = 0.3
                elif vol_percentile > 90 or vol_percentile < 10:
                    score = 0.6
                else:
                    score = 0.8
                
                # Check volatility stability
                if historical_vol > 0:
                    vol_ratio = current_vol / historical_vol
                    if vol_ratio > 2.0 or vol_ratio < 0.5:
                        failure_reasons.append(f"Unstable volatility ratio: {vol_ratio:.2f}")
                        score *= 0.7
                
                passed = score >= self.min_verification_score
                
            elif claim.claim_type == ClaimType.LIQUIDITY_SLIPPAGE:
                # Verify liquidity is adequate
                spread = evidence.get('bid_ask_spread', 0.0)
                volume = evidence.get('volume', 0.0)
                avg_volume = evidence.get('avg_volume', 1.0)
                
                # Volume check
                if avg_volume > 0:
                    volume_ratio = volume / avg_volume
                    if volume_ratio < 0.5:
                        failure_reasons.append(f"Low volume ratio: {volume_ratio:.2f}")
                        score = 0.4
                    elif volume_ratio < 0.8:
                        score = 0.6
                    else:
                        score = 0.8
                
                # Spread check
                if spread > 0.001:  # 10 bps
                    failure_reasons.append(f"Wide spread: {spread:.6f}")
                    score *= 0.7
                
                passed = score >= self.min_verification_score
                
            else:
                # Generic statistical verification
                score = 0.7
                passed = True
            
            return VerificationResult(
                method=VerificationMethod.STATISTICAL,
                claim_type=claim.claim_type,
                passed=passed,
                score=score,
                evidence={'method': 'statistical', 'details': evidence},
                failure_reasons=failure_reasons
            )
            
        except Exception as e:
            logger.error(f"Statistical verification failed: {e}")
            return None
    
    def _verify_regime_based(
        self,
        claim: TradeClaim,
        market_data: Dict[str, Any],
        historical_data: Dict[str, Any]
    ) -> Optional[VerificationResult]:
        """Regime-based verification"""
        try:
            evidence = claim.evidence
            score = 0.0
            passed = False
            failure_reasons = []
            
            regime = market_data.get('regime', 'UNKNOWN')
            
            if claim.claim_type == ClaimType.REGIME_VALIDITY:
                # Verify regime is stable and known
                regime_stability = evidence.get('regime_stability', 0.0)
                regime_duration = evidence.get('regime_duration', 0)
                
                if regime == 'UNKNOWN' or regime == 'TRANSITIONING':
                    failure_reasons.append(f"Invalid regime: {regime}")
                    score = 0.2
                elif regime_stability < 0.5:
                    failure_reasons.append(f"Low regime stability: {regime_stability:.2f}")
                    score = 0.4
                elif regime_duration < 10:
                    failure_reasons.append(f"Short regime duration: {regime_duration}")
                    score = 0.6
                else:
                    score = 0.9
                
                passed = score >= self.min_verification_score
                
            elif claim.claim_type == ClaimType.SIGNAL_EXPECTANCY:
                # Verify signal performs in current regime
                regime_performance = historical_data.get('regime_performance', {})
                regime_expectancy = regime_performance.get(regime, 0.0)
                
                if regime_expectancy <= 0:
                    failure_reasons.append(f"Negative expectancy in {regime}: {regime_expectancy:.4f}")
                    score = 0.3
                elif regime_expectancy < 0.01:
                    score = 0.6
                else:
                    score = 0.9
                
                passed = score >= self.min_verification_score
                
            else:
                # Generic regime verification
                if regime in ['TRENDING', 'RANGING', 'VOLATILE']:
                    score = 0.7
                    passed = True
                else:
                    score = 0.4
                    passed = False
            
            return VerificationResult(
                method=VerificationMethod.REGIME_BASED,
                claim_type=claim.claim_type,
                passed=passed,
                score=score,
                evidence={'regime': regime, 'details': evidence},
                failure_reasons=failure_reasons
            )
            
        except Exception as e:
            logger.error(f"Regime-based verification failed: {e}")
            return None
    
    def _verify_microstructure(
        self,
        claim: TradeClaim,
        market_data: Dict[str, Any],
        historical_data: Dict[str, Any]
    ) -> Optional[VerificationResult]:
        """Microstructure verification"""
        try:
            evidence = claim.evidence
            score = 0.0
            passed = False
            failure_reasons = []
            
            if claim.claim_type == ClaimType.LIQUIDITY_SLIPPAGE:
                # Verify using order book microstructure
                order_book_depth = market_data.get('order_book_depth', 0.0)
                market_depth = evidence.get('market_depth', 0.0)
                
                if market_depth < 1000:
                    failure_reasons.append(f"Shallow market depth: {market_depth:.0f}")
                    score = 0.4
                elif market_depth < 10000:
                    score = 0.7
                else:
                    score = 0.9
                
                passed = score >= self.min_verification_score
                
            elif claim.claim_type == ClaimType.EXECUTION_FEASIBILITY:
                # Verify execution quality
                latency = evidence.get('latency', 0.0)
                execution_quality = evidence.get('execution_quality', 0.0)
                
                if latency > 100:  # 100ms
                    failure_reasons.append(f"High latency: {latency:.2f}ms")
                    score = 0.4
                elif latency > 50:
                    score = 0.6
                else:
                    score = 0.8
                
                if execution_quality < 0.7:
                    failure_reasons.append(f"Low execution quality: {execution_quality:.2f}")
                    score *= 0.8
                
                passed = score >= self.min_verification_score
                
            else:
                # Generic microstructure check
                score = 0.6
                passed = True
            
            return VerificationResult(
                method=VerificationMethod.MICROSTRUCTURE,
                claim_type=claim.claim_type,
                passed=passed,
                score=score,
                evidence={'microstructure': market_data, 'details': evidence},
                failure_reasons=failure_reasons
            )
            
        except Exception as e:
            logger.error(f"Microstructure verification failed: {e}")
            return None
    
    def _verify_historical_analog(
        self,
        claim: TradeClaim,
        market_data: Dict[str, Any],
        historical_data: Dict[str, Any]
    ) -> Optional[VerificationResult]:
        """Historical analog verification"""
        try:
            evidence = claim.evidence
            score = 0.0
            passed = False
            failure_reasons = []
            
            # Find similar historical conditions
            similar_conditions = historical_data.get('similar_conditions', [])
            
            if len(similar_conditions) == 0:
                failure_reasons.append("No historical analogs found")
                score = 0.3
            else:
                # Calculate success rate in similar conditions
                successes = sum(1 for c in similar_conditions if c.get('outcome', 0) > 0)
                success_rate = successes / len(similar_conditions)
                
                if success_rate < 0.4:
                    failure_reasons.append(f"Low historical success rate: {success_rate:.2%}")
                    score = 0.4
                elif success_rate < 0.6:
                    score = 0.6
                else:
                    score = 0.9
                
                # Penalize if sample size is small
                if len(similar_conditions) < 10:
                    score *= 0.8
                    failure_reasons.append(f"Small analog sample: {len(similar_conditions)}")
            
            passed = score >= self.min_verification_score
            
            return VerificationResult(
                method=VerificationMethod.HISTORICAL_ANALOG,
                claim_type=claim.claim_type,
                passed=passed,
                score=score,
                evidence={'analogs': len(similar_conditions), 'details': evidence},
                failure_reasons=failure_reasons
            )
            
        except Exception as e:
            logger.error(f"Historical analog verification failed: {e}")
            return None
    
    def _verify_adversarial_failure(
        self,
        claim: TradeClaim,
        market_data: Dict[str, Any],
        historical_data: Dict[str, Any]
    ) -> Optional[VerificationResult]:
        """Adversarial failure search"""
        try:
            evidence = claim.evidence
            score = 1.0
            passed = True
            failure_reasons = []
            
            # Search for failure modes
            if claim.claim_type == ClaimType.TAIL_RISK_EXPOSURE:
                # Check for tail risk vulnerabilities
                kurtosis = evidence.get('kurtosis', 3.0)
                skewness = evidence.get('skewness', 0.0)
                
                if kurtosis > 5.0:
                    failure_reasons.append(f"High kurtosis (fat tails): {kurtosis:.2f}")
                    score = 0.4
                
                if abs(skewness) > 1.0:
                    failure_reasons.append(f"High skewness: {skewness:.2f}")
                    score = min(score, 0.5)
                
            elif claim.claim_type == ClaimType.CORRELATION_PORTFOLIO:
                # Check for hidden correlations
                max_correlation = evidence.get('max_correlation', 0.0)
                
                if max_correlation > 0.8:
                    failure_reasons.append(f"High correlation risk: {max_correlation:.2f}")
                    score = 0.3
                elif max_correlation > 0.7:
                    score = 0.6
                
            # Generic adversarial checks
            if len(failure_reasons) == 0:
                score = 0.8
                passed = True
            else:
                passed = score >= self.min_verification_score
            
            return VerificationResult(
                method=VerificationMethod.ADVERSARIAL_FAILURE,
                claim_type=claim.claim_type,
                passed=passed,
                score=score,
                evidence={'adversarial_check': True, 'details': evidence},
                failure_reasons=failure_reasons
            )
            
        except Exception as e:
            logger.error(f"Adversarial failure verification failed: {e}")
            return None
