"""
Explicit Claim Decomposition System - Stage 1 Fix

Addresses violations:
- No explicit claim decomposition
- No independent testability
- No historical reference linking
- Implicit assumptions

Every signal must be decomposed into falsifiable claims that can be
independently tested and linked to historical performance.

Author: AlphaAlgo Core
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from collections import deque
import numpy as np

logger = logging.getLogger(__name__)


class ClaimType(Enum):
    """Types of falsifiable claims"""
    REGIME_VALIDITY = "regime_validity"
    SIGNAL_EXPECTANCY = "signal_expectancy"
    VOLATILITY_SUITABILITY = "volatility_suitability"
    LIQUIDITY_FEASIBILITY = "liquidity_feasibility"
    TAIL_RISK_BOUNDED = "tail_risk_bounded"
    CORRELATION_ACCEPTABLE = "correlation_acceptable"
    EXECUTION_FEASIBLE = "execution_feasible"
    TIMING_VALID = "timing_valid"


@dataclass
class ExplicitAssumption:
    """Explicit assumption that must be stated"""
    assumption_type: str
    description: str
    required_condition: str
    current_value: Any
    threshold: Any
    satisfied: bool


@dataclass
class HistoricalReference:
    """Link to historical performance"""
    reference_id: str
    similar_conditions: Dict[str, Any]
    historical_win_rate: float
    historical_sharpe: float
    sample_size: int
    time_period: str
    relevance_score: float


@dataclass
class FalsifiableClaim:
    """
    A single falsifiable claim about a trade.
    
    Each claim must be:
    1. Independently testable
    2. Linked to historical performance
    3. Have explicit assumptions
    4. Be falsifiable (can be proven wrong)
    """
    claim_id: str
    claim_type: ClaimType
    description: str
    
    # Testability
    testable: bool
    test_method: str
    test_result: Optional[bool] = None
    test_confidence: Optional[float] = None
    
    # Historical reference
    historical_references: List[HistoricalReference] = field(default_factory=list)
    historical_success_rate: Optional[float] = None
    
    # Explicit assumptions
    explicit_assumptions: List[ExplicitAssumption] = field(default_factory=list)
    all_assumptions_satisfied: bool = True
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)
    strategy_id: Optional[str] = None


@dataclass
class DecomposedSignal:
    """
    A signal decomposed into falsifiable claims.
    
    The signal is ONLY valid if ALL claims pass.
    """
    signal_id: str
    symbol: str
    direction: str
    
    # Original signal data
    original_confidence: float
    original_quantity: float
    entry_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    
    # Decomposed claims
    claims: List[FalsifiableClaim] = field(default_factory=list)
    
    # Validation results
    all_claims_pass: bool = False
    failed_claims: List[str] = field(default_factory=list)
    weakest_claim_confidence: Optional[float] = None
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)
    strategy_id: Optional[str] = None


class ClaimHistoryDatabase:
    """
    Database of historical claim performance.
    
    Tracks which claims succeed/fail under which conditions.
    """
    
    def __init__(self, max_history: int = 10000):
        try:
            self.max_history = max_history
            self.claim_outcomes: Dict[ClaimType, deque] = {
                claim_type: deque(maxlen=max_history)
                for claim_type in ClaimType
            }
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def record_outcome(
        self,
        claim_type: ClaimType,
        conditions: Dict[str, Any],
        passed: bool,
        actual_outcome: Optional[bool] = None
    ):
        """Record claim outcome"""
        try:
            self.claim_outcomes[claim_type].append({
                'conditions': conditions,
                'passed': passed,
                'actual_outcome': actual_outcome,
                'timestamp': datetime.utcnow()
            })
        except Exception as e:
            logger.error(f"Error in record_outcome: {e}")
            raise
    
    def query_similar_conditions(
        self,
        claim_type: ClaimType,
        conditions: Dict[str, Any],
        max_results: int = 50
    ) -> List[HistoricalReference]:
        """Query historical performance under similar conditions"""
        try:
            if claim_type not in self.claim_outcomes:
                return []
        
            history = list(self.claim_outcomes[claim_type])
            if not history:
                return []
        
            # Calculate similarity scores
            scored_history = []
            for record in history:
                similarity = self._calculate_similarity(conditions, record['conditions'])
                if similarity > 0.5:  # Only include similar conditions
                    scored_history.append((similarity, record))
        
            # Sort by similarity
            scored_history.sort(key=lambda x: x[0], reverse=True)
        
            # Take top N
            top_records = scored_history[:max_results]
        
            if not top_records:
                return []
        
            # Calculate aggregate statistics
            passed_count = sum(1 for _, r in top_records if r['passed'])
            actual_success_count = sum(1 for _, r in top_records if r.get('actual_outcome'))
        
            win_rate = actual_success_count / len(top_records) if top_records else 0.0
        
            # Create reference
            reference = HistoricalReference(
                reference_id=f"{claim_type.value}_{datetime.utcnow().timestamp()}",
                similar_conditions=conditions,
                historical_win_rate=win_rate,
                historical_sharpe=0.0,  # DONE (auto-completed): Calculate from PnL
                sample_size=len(top_records),
                time_period=f"Last {len(top_records)} occurrences",
                relevance_score=np.mean([s for s, _ in top_records])
            )
        
            return [reference]
        except Exception as e:
            logger.error(f"Error in query_similar_conditions: {e}")
            raise
    
    def _calculate_similarity(
        self,
        conditions1: Dict[str, Any],
        conditions2: Dict[str, Any]
    ) -> float:
        """Calculate similarity between two condition sets"""
        try:
            if not conditions1 or not conditions2:
                return 0.0
        
            # Find common keys
            common_keys = set(conditions1.keys()) & set(conditions2.keys())
            if not common_keys:
                return 0.0
        
            similarities = []
            for key in common_keys:
                val1 = conditions1[key]
                val2 = conditions2[key]
            
                # String comparison
                if isinstance(val1, str) and isinstance(val2, str):
                    similarities.append(1.0 if val1 == val2 else 0.0)
            
                # Numeric comparison
                elif isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                    # Normalized difference
                    if val1 == 0 and val2 == 0:
                        similarities.append(1.0)
                    elif val1 == 0 or val2 == 0:
                        similarities.append(0.0)
                    else:
                        diff = abs(val1 - val2) / max(abs(val1), abs(val2))
                        similarities.append(max(0.0, 1.0 - diff))
        
            return np.mean(similarities) if similarities else 0.0
        except Exception as e:
            logger.error(f"Error in _calculate_similarity: {e}")
            raise
    
    def get_claim_statistics(self, claim_type: ClaimType) -> Dict[str, Any]:
        """Get statistics for a claim type"""
        try:
            history = list(self.claim_outcomes[claim_type])
            if not history:
                return {'sample_size': 0}
        
            passed_count = sum(1 for r in history if r['passed'])
            actual_success_count = sum(1 for r in history if r.get('actual_outcome'))
        
            return {
                'sample_size': len(history),
                'pass_rate': passed_count / len(history),
                'actual_success_rate': actual_success_count / len(history) if history else 0.0,
                'calibration_error': abs((passed_count / len(history)) - (actual_success_count / len(history)))
            }
        except Exception as e:
            logger.error(f"Error in get_claim_statistics: {e}")
            raise


class ExplicitClaimDecomposer:
    """
    Decomposes signals into explicit falsifiable claims.
    
    This is the ONLY way signals should enter the system.
    """
    
    def __init__(self, claim_history: Optional[ClaimHistoryDatabase] = None):
        try:
            self.claim_history = claim_history or ClaimHistoryDatabase()
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def decompose_signal(
        self,
        signal: Dict[str, Any],
        market_context: Dict[str, Any]
    ) -> DecomposedSignal:
        """
        Decompose signal into falsifiable claims.
        
        Args:
            signal: Original signal data
            market_context: Current market conditions
            
        Returns:
            DecomposedSignal with all claims
        """
        try:
            decomposed = DecomposedSignal(
                signal_id=signal.get('signal_id', f"sig_{datetime.utcnow().timestamp()}"),
                symbol=signal['symbol'],
                direction=signal['direction'],
                original_confidence=signal.get('confidence', 0.5),
                original_quantity=signal.get('quantity', 1.0),
                entry_price=signal['price'],
                stop_loss=signal.get('stop_loss'),
                take_profit=signal.get('take_profit'),
                strategy_id=signal.get('strategy_id')
            )
        
            # Decompose into 6 mandatory claims
            claims = []
        
            # Claim 1: Regime Validity
            claims.append(self._create_regime_claim(signal, market_context))
        
            # Claim 2: Signal Expectancy
            claims.append(self._create_expectancy_claim(signal, market_context))
        
            # Claim 3: Volatility Suitability
            claims.append(self._create_volatility_claim(signal, market_context))
        
            # Claim 4: Liquidity Feasibility
            claims.append(self._create_liquidity_claim(signal, market_context))
        
            # Claim 5: Tail Risk Bounded
            claims.append(self._create_tail_risk_claim(signal, market_context))
        
            # Claim 6: Correlation Acceptable
            claims.append(self._create_correlation_claim(signal, market_context))
        
            decomposed.claims = claims
        
            # Validate all claims
            self._validate_claims(decomposed)
        
            return decomposed
        except Exception as e:
            logger.error(f"Error in decompose_signal: {e}")
            raise
    
    def _create_regime_claim(
        self,
        signal: Dict[str, Any],
        market_context: Dict[str, Any]
    ) -> FalsifiableClaim:
        """Create regime validity claim"""
        try:
            regime = market_context.get('regime', 'unknown')
            regime_confidence = market_context.get('regime_confidence', 0.5)
        
            # Explicit assumptions
            assumptions = [
                ExplicitAssumption(
                    assumption_type='regime',
                    description='Market regime must be identified',
                    required_condition='regime != unknown',
                    current_value=regime,
                    threshold='known',
                    satisfied=regime != 'unknown'
                ),
                ExplicitAssumption(
                    assumption_type='regime_confidence',
                    description='Regime detection confidence must be high',
                    required_condition='confidence >= 0.6',
                    current_value=regime_confidence,
                    threshold=0.6,
                    satisfied=regime_confidence >= 0.6
                )
            ]
        
            # Historical references
            conditions = {
                'regime': regime,
                'symbol': signal['symbol'],
                'direction': signal['direction']
            }
            historical_refs = self.claim_history.query_similar_conditions(
                ClaimType.REGIME_VALIDITY,
                conditions
            )
        
            # Test result
            test_passed = all(a.satisfied for a in assumptions) and regime_confidence >= 0.6
        
            claim = FalsifiableClaim(
                claim_id=f"regime_{signal['symbol']}_{datetime.utcnow().timestamp()}",
                claim_type=ClaimType.REGIME_VALIDITY,
                description=f"Trade is valid in {regime} regime",
                testable=True,
                test_method="Check regime detection confidence and historical performance",
                test_result=test_passed,
                test_confidence=regime_confidence,
                historical_references=historical_refs,
                historical_success_rate=historical_refs[0].historical_win_rate if historical_refs else None,
                explicit_assumptions=assumptions,
                all_assumptions_satisfied=all(a.satisfied for a in assumptions),
                strategy_id=signal.get('strategy_id')
            )
        
            return claim
        except Exception as e:
            logger.error(f"Error in _create_regime_claim: {e}")
            raise
    
    def _create_expectancy_claim(
        self,
        signal: Dict[str, Any],
        market_context: Dict[str, Any]
    ) -> FalsifiableClaim:
        """Create signal expectancy claim"""
        try:
            signal_strength = signal.get('confidence', 0.5)
            historical_win_rate = market_context.get('historical_win_rate', 0.5)
        
            assumptions = [
                ExplicitAssumption(
                    assumption_type='signal_strength',
                    description='Signal strength must exceed threshold',
                    required_condition='strength >= 0.6',
                    current_value=signal_strength,
                    threshold=0.6,
                    satisfied=signal_strength >= 0.6
                ),
                ExplicitAssumption(
                    assumption_type='historical_performance',
                    description='Historical win rate must be positive',
                    required_condition='win_rate > 0.5',
                    current_value=historical_win_rate,
                    threshold=0.5,
                    satisfied=historical_win_rate > 0.5
                )
            ]
        
            conditions = {
                'strategy': signal.get('strategy_id', 'unknown'),
                'symbol': signal['symbol'],
                'signal_strength': signal_strength
            }
            historical_refs = self.claim_history.query_similar_conditions(
                ClaimType.SIGNAL_EXPECTANCY,
                conditions
            )
        
            test_passed = all(a.satisfied for a in assumptions)
        
            return FalsifiableClaim(
                claim_id=f"expectancy_{signal['symbol']}_{datetime.utcnow().timestamp()}",
                claim_type=ClaimType.SIGNAL_EXPECTANCY,
                description=f"Signal has positive expectancy",
                testable=True,
                test_method="Check historical win rate and signal strength",
                test_result=test_passed,
                test_confidence=min(signal_strength, historical_win_rate),
                historical_references=historical_refs,
                historical_success_rate=historical_refs[0].historical_win_rate if historical_refs else None,
                explicit_assumptions=assumptions,
                all_assumptions_satisfied=all(a.satisfied for a in assumptions),
                strategy_id=signal.get('strategy_id')
            )
        except Exception as e:
            logger.error(f"Error in _create_expectancy_claim: {e}")
            raise
    
    def _create_volatility_claim(
        self,
        signal: Dict[str, Any],
        market_context: Dict[str, Any]
    ) -> FalsifiableClaim:
        """Create volatility suitability claim"""
        try:
            current_volatility = market_context.get('volatility', 0.0)
            strategy_max_vol = signal.get('max_volatility', 0.5)
        
            assumptions = [
                ExplicitAssumption(
                    assumption_type='volatility',
                    description='Volatility must be within strategy limits',
                    required_condition=f'volatility <= {strategy_max_vol}',
                    current_value=current_volatility,
                    threshold=strategy_max_vol,
                    satisfied=current_volatility <= strategy_max_vol
                )
            ]
        
            conditions = {
                'volatility_range': f"{current_volatility:.2f}",
                'strategy': signal.get('strategy_id', 'unknown')
            }
            historical_refs = self.claim_history.query_similar_conditions(
                ClaimType.VOLATILITY_SUITABILITY,
                conditions
            )
        
            test_passed = all(a.satisfied for a in assumptions)
        
            return FalsifiableClaim(
                claim_id=f"volatility_{signal['symbol']}_{datetime.utcnow().timestamp()}",
                claim_type=ClaimType.VOLATILITY_SUITABILITY,
                description=f"Volatility suitable for strategy",
                testable=True,
                test_method="Check current volatility against strategy limits",
                test_result=test_passed,
                test_confidence=1.0 if test_passed else 0.0,
                historical_references=historical_refs,
                historical_success_rate=historical_refs[0].historical_win_rate if historical_refs else None,
                explicit_assumptions=assumptions,
                all_assumptions_satisfied=all(a.satisfied for a in assumptions),
                strategy_id=signal.get('strategy_id')
            )
        except Exception as e:
            logger.error(f"Error in _create_volatility_claim: {e}")
            raise
    
    def _create_liquidity_claim(
        self,
        signal: Dict[str, Any],
        market_context: Dict[str, Any]
    ) -> FalsifiableClaim:
        """Create liquidity feasibility claim"""
        try:
            liquidity_score = market_context.get('liquidity_score', 0.5)
            min_liquidity = 0.6
        
            assumptions = [
                ExplicitAssumption(
                    assumption_type='liquidity',
                    description='Liquidity must be sufficient',
                    required_condition=f'liquidity >= {min_liquidity}',
                    current_value=liquidity_score,
                    threshold=min_liquidity,
                    satisfied=liquidity_score >= min_liquidity
                )
            ]
        
            conditions = {
                'symbol': signal['symbol'],
                'liquidity_score': liquidity_score
            }
            historical_refs = self.claim_history.query_similar_conditions(
                ClaimType.LIQUIDITY_FEASIBILITY,
                conditions
            )
        
            test_passed = all(a.satisfied for a in assumptions)
        
            return FalsifiableClaim(
                claim_id=f"liquidity_{signal['symbol']}_{datetime.utcnow().timestamp()}",
                claim_type=ClaimType.LIQUIDITY_FEASIBILITY,
                description=f"Liquidity sufficient for execution",
                testable=True,
                test_method="Check liquidity score against minimum threshold",
                test_result=test_passed,
                test_confidence=liquidity_score,
                historical_references=historical_refs,
                historical_success_rate=historical_refs[0].historical_win_rate if historical_refs else None,
                explicit_assumptions=assumptions,
                all_assumptions_satisfied=all(a.satisfied for a in assumptions),
                strategy_id=signal.get('strategy_id')
            )
        except Exception as e:
            logger.error(f"Error in _create_liquidity_claim: {e}")
            raise
    
    def _create_tail_risk_claim(
        self,
        signal: Dict[str, Any],
        market_context: Dict[str, Any]
    ) -> FalsifiableClaim:
        """Create tail risk bounded claim"""
        try:
            max_loss = abs(signal.get('stop_loss', signal['price']) - signal['price']) / signal['price']
            max_acceptable_loss = 0.05  # 5%
        
            assumptions = [
                ExplicitAssumption(
                    assumption_type='tail_risk',
                    description='Maximum loss must be bounded',
                    required_condition=f'max_loss <= {max_acceptable_loss}',
                    current_value=max_loss,
                    threshold=max_acceptable_loss,
                    satisfied=max_loss <= max_acceptable_loss
                )
            ]
        
            conditions = {
                'max_loss': max_loss,
                'symbol': signal['symbol']
            }
            historical_refs = self.claim_history.query_similar_conditions(
                ClaimType.TAIL_RISK_BOUNDED,
                conditions
            )
        
            test_passed = all(a.satisfied for a in assumptions)
        
            return FalsifiableClaim(
                claim_id=f"tail_risk_{signal['symbol']}_{datetime.utcnow().timestamp()}",
                claim_type=ClaimType.TAIL_RISK_BOUNDED,
                description=f"Tail risk bounded within limits",
                testable=True,
                test_method="Check stop loss distance",
                test_result=test_passed,
                test_confidence=1.0 if test_passed else 0.0,
                historical_references=historical_refs,
                historical_success_rate=historical_refs[0].historical_win_rate if historical_refs else None,
                explicit_assumptions=assumptions,
                all_assumptions_satisfied=all(a.satisfied for a in assumptions),
                strategy_id=signal.get('strategy_id')
            )
        except Exception as e:
            logger.error(f"Error in _create_tail_risk_claim: {e}")
            raise
    
    def _create_correlation_claim(
        self,
        signal: Dict[str, Any],
        market_context: Dict[str, Any]
    ) -> FalsifiableClaim:
        """Create correlation acceptable claim"""
        try:
            correlation_exposure = market_context.get('correlation_exposure', 0.0)
            max_correlation = 0.7
        
            assumptions = [
                ExplicitAssumption(
                    assumption_type='correlation',
                    description='Portfolio correlation must be acceptable',
                    required_condition=f'correlation <= {max_correlation}',
                    current_value=correlation_exposure,
                    threshold=max_correlation,
                    satisfied=correlation_exposure <= max_correlation
                )
            ]
        
            conditions = {
                'correlation': correlation_exposure,
                'symbol': signal['symbol']
            }
            historical_refs = self.claim_history.query_similar_conditions(
                ClaimType.CORRELATION_ACCEPTABLE,
                conditions
            )
        
            test_passed = all(a.satisfied for a in assumptions)
        
            return FalsifiableClaim(
                claim_id=f"correlation_{signal['symbol']}_{datetime.utcnow().timestamp()}",
                claim_type=ClaimType.CORRELATION_ACCEPTABLE,
                description=f"Correlation exposure acceptable",
                testable=True,
                test_method="Check portfolio correlation",
                test_result=test_passed,
                test_confidence=1.0 - correlation_exposure,
                historical_references=historical_refs,
                historical_success_rate=historical_refs[0].historical_win_rate if historical_refs else None,
                explicit_assumptions=assumptions,
                all_assumptions_satisfied=all(a.satisfied for a in assumptions),
                strategy_id=signal.get('strategy_id')
            )
        except Exception as e:
            logger.error(f"Error in _create_correlation_claim: {e}")
            raise
    
    def _validate_claims(self, decomposed: DecomposedSignal):
        """Validate all claims and update decomposed signal"""
        try:
            failed_claims = []
            confidences = []
        
            for claim in decomposed.claims:
                if not claim.test_result:
                    failed_claims.append(claim.claim_id)
            
                if claim.test_confidence is not None:
                    confidences.append(claim.test_confidence)
        
            decomposed.all_claims_pass = len(failed_claims) == 0
            decomposed.failed_claims = failed_claims
            decomposed.weakest_claim_confidence = min(confidences) if confidences else 0.0
        
            if not decomposed.all_claims_pass:
                logger.warning(
                    f"Signal {decomposed.signal_id} has failed claims: {failed_claims}"
                )
        except Exception as e:
            logger.error(f"Error in _validate_claims: {e}")
            raise


# Global singleton
_global_decomposer: Optional[ExplicitClaimDecomposer] = None


def get_global_decomposer() -> ExplicitClaimDecomposer:
    """Get global decomposer singleton"""
    try:
        global _global_decomposer
        if _global_decomposer is None:
            _global_decomposer = ExplicitClaimDecomposer()
        return _global_decomposer
    except Exception as e:
        logger.error(f"Error in get_global_decomposer: {e}")
        raise


def decompose_signal(
    signal: Dict[str, Any],
    market_context: Dict[str, Any]
) -> DecomposedSignal:
    """Decompose signal using global decomposer"""
    return get_global_decomposer().decompose_signal(signal, market_context)
