"""
Layer 4: Regime Applicability Engine

Maps every claim and strategy to known market states.
Uses multidimensional regime ontology:
- volatility state
- liquidity state
- trend persistence
- correlation clustering
- macro event density
- order-flow toxicity
- spread/impact conditions

Asks:
- Has this logic historically worked in this regime neighborhood?
- Is this regime underrepresented in training or validation?
"""

from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime
from dataclasses import dataclass
from collections import defaultdict
import logging
import numpy as np

from .core_types import (
    Claim, ClaimType, MarketRegime, RegimeDimension, DecisionRecord
)

logger = logging.getLogger(__name__)


@dataclass
class RegimePerformance:
    """Performance of a strategy in a specific regime"""
    regime_hash: str
    trades_count: int
    win_rate: float
    avg_return: float
    sharpe_ratio: float
    max_drawdown: float
    confidence: float  # Statistical confidence in these metrics


@dataclass
class RegimeSimilarity:
    """Similarity between two regimes"""
    regime1_id: str
    regime2_id: str
    similarity_score: float  # 0 to 1
    dimension_differences: Dict[str, float]


@dataclass
class RegimeTransitionSignal:
    """Early warning signal for regime transition"""
    timestamp: datetime
    transition_probability: float  # 0-1
    from_regime: str
    to_regime: str
    confidence: float
    leading_indicators: List[str]
    warning_signals: Dict[str, float]
    estimated_time_to_transition: int  # minutes
    severity: str  # low, medium, high, critical


class RegimeTransitionEarlyWarning:
    """
    Regime Transition Early Warning System
    
    Detect when regimes are ABOUT TO change, not after.
    
    Signals:
    - Volatility structure distortion
    - Correlation breakdown
    - Liquidity fragmentation
    - Spread anomalies
    
    Output: regime_shift_probability
    Action: reduce risk BEFORE damage happens
    """
    
    def __init__(self, warning_threshold: float = 0.6, critical_threshold: float = 0.8):
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        
        # Historical patterns of regime transitions
        self.transition_patterns: List[Dict] = []
        
        # Current signals
        self.active_warnings: List[RegimeTransitionSignal] = []
        self.signal_history: List[RegimeTransitionSignal] = []
        
        # Baseline metrics for anomaly detection
        self.baseline_metrics: Dict[str, float] = {}
        
    def detect_early_warning_signals(
        self,
        current_regime: MarketRegime,
        market_data: Dict[str, Any],
        historical_window: int = 20
    ) -> RegimeTransitionSignal:
        """
        Detect early warning signals of impending regime change.
        
        Args:
            current_regime: Current market regime
            market_data: Recent market data
            historical_window: Lookback period for baseline
            
        Returns:
            RegimeTransitionSignal with probability and details
        """
        warnings = {}
        leading_indicators = []
        
        # 1. Volatility Structure Distortion
        vol_distortion = self._detect_volatility_structure_distortion(market_data)
        warnings['volatility_distortion'] = vol_distortion
        if vol_distortion > 0.7:
            leading_indicators.append("Volatility term structure inversion")
        
        # 2. Correlation Breakdown
        corr_breakdown = self._detect_correlation_breakdown(market_data)
        warnings['correlation_breakdown'] = corr_breakdown
        if corr_breakdown > 0.7:
            leading_indicators.append("Cross-asset correlation breakdown")
        
        # 3. Liquidity Fragmentation
        liq_fragmentation = self._detect_liquidity_fragmentation(market_data)
        warnings['liquidity_fragmentation'] = liq_fragmentation
        if liq_fragmentation > 0.7:
            leading_indicators.append("Liquidity fragmentation detected")
        
        # 4. Spread Anomalies
        spread_anomaly = self._detect_spread_anomalies(market_data)
        warnings['spread_anomaly'] = spread_anomaly
        if spread_anomaly > 0.7:
            leading_indicators.append("Bid-ask spread anomaly")
        
        # 5. Order Flow Toxicity Spike
        toxicity_spike = self._detect_flow_toxicity_spike(market_data)
        warnings['flow_toxicity'] = toxicity_spike
        if toxicity_spike > 0.7:
            leading_indicators.append("Order flow toxicity spike")
        
        # 6. Skew/Kurtosis Shift
        distribution_shift = self._detect_distribution_shift(market_data)
        warnings['distribution_shift'] = distribution_shift
        if distribution_shift > 0.7:
            leading_indicators.append("Return distribution shift")
        
        # Calculate composite probability
        transition_prob = self._calculate_transition_probability(warnings)
        
        # Estimate time to transition
        time_estimate = self._estimate_time_to_transition(warnings)
        
        # Determine severity
        severity = self._determine_severity(transition_prob, warnings)
        
        # Predict target regime
        target_regime = self._predict_target_regime(current_regime, warnings)
        
        signal = RegimeTransitionSignal(
            timestamp=datetime.now(),
            transition_probability=transition_prob,
            from_regime=self._regime_to_string(current_regime),
            to_regime=target_regime,
            confidence=min(1.0, sum(warnings.values()) / len(warnings)) if warnings else 0,
            leading_indicators=leading_indicators,
            warning_signals=warnings,
            estimated_time_to_transition=time_estimate,
            severity=severity
        )
        
        self.signal_history.append(signal)
        
        if transition_prob > self.warning_threshold:
            self.active_warnings.append(signal)
            logger.warning(f"Regime transition warning: {transition_prob:.1%} probability "
                         f"to {target_regime} within {time_estimate} minutes")
        
        return signal
    
    def _detect_volatility_structure_distortion(self, market_data: Dict) -> float:
        """Detect distortion in volatility term structure."""
        vol_surface = market_data.get('volatility_surface', {})
        
        if not vol_surface:
            return 0.0
        
        # Check for inversion (short vol > long vol)
        short_vol = vol_surface.get('1w', 0)
        long_vol = vol_surface.get('3m', vol_surface.get('1m', 0))
        
        if short_vol > 0 and long_vol > 0:
            if short_vol > long_vol * 1.2:  # 20% inversion
                return min(1.0, (short_vol / long_vol - 1.0) * 2.0)
        
        # Check for rapid changes
        vol_change = market_data.get('volatility_change_24h', 0)
        if abs(vol_change) > 0.5:  # 50% change
            return min(1.0, abs(vol_change))
        
        return 0.0
    
    def _detect_correlation_breakdown(self, market_data: Dict) -> float:
        """Detect breakdown in normal correlations."""
        correlations = market_data.get('correlation_matrix', {})
        
        if not correlations:
            return 0.0
        
        breakdown_score = 0.0
        
        # Check for correlation spikes (normally uncorrelated assets suddenly correlated)
        for pair, corr in correlations.items():
            if abs(corr) > 0.8:  # Very high correlation
                # Check if this is abnormal for this pair
                historical_avg = market_data.get(f'historical_corr_{pair}', 0.3)
                if abs(corr - historical_avg) > 0.5:
                    breakdown_score += 0.3
        
        # Check for correlation sign flips
        sign_changes = market_data.get('correlation_sign_changes', 0)
        if sign_changes > 3:
            breakdown_score += 0.4
        
        return min(1.0, breakdown_score)
    
    def _detect_liquidity_fragmentation(self, market_data: Dict) -> float:
        """Detect fragmentation of liquidity across venues."""
        # Check for order book depth reduction
        depth = market_data.get('order_book_depth', 0)
        avg_depth = market_data.get('avg_order_book_depth', 100)
        
        if avg_depth > 0 and depth < avg_depth * 0.5:
            return min(1.0, 1.0 - (depth / avg_depth))
        
        # Check for increased venue dispersion
        venue_dispersion = market_data.get('venue_price_dispersion', 0)
        if venue_dispersion > 0.1:  # 10bp dispersion
            return min(1.0, venue_dispersion * 10)
        
        return 0.0
    
    def _detect_spread_anomalies(self, market_data: Dict) -> float:
        """Detect anomalies in bid-ask spreads."""
        current_spread = market_data.get('bid_ask_spread', 0)
        avg_spread = market_data.get('avg_bid_ask_spread', 0.01)
        
        if avg_spread > 0 and current_spread > avg_spread * 3:
            return min(1.0, (current_spread / avg_spread - 1) / 3)
        
        # Check for spread volatility
        spread_vol = market_data.get('spread_volatility', 0)
        if spread_vol > 0.5:
            return min(1.0, spread_vol)
        
        return 0.0
    
    def _detect_flow_toxicity_spike(self, market_data: Dict) -> float:
        """Detect spike in order flow toxicity."""
        vp_in = market_data.get('volume_synchronized_probability_informed', 0)
        
        if vp_in > 0.6:  # High probability of informed trading
            return min(1.0, vp_in)
        
        # Check for order book imbalance
        ob_imbalance = market_data.get('order_book_imbalance', 0)
        if abs(ob_imbalance) > 0.7:
            return abs(ob_imbalance)
        
        return 0.0
    
    def _detect_distribution_shift(self, market_data: Dict) -> float:
        """Detect shift in return distribution (skew/kurtosis)."""
        skew = market_data.get('return_skew', 0)
        kurt = market_data.get('return_kurtosis', 3)
        
        shift_score = 0.0
        
        # High kurtosis indicates tail risk
        if kurt > 5:
            shift_score += min(0.5, (kurt - 3) / 10)
        
        # Extreme skew indicates directional pressure
        if abs(skew) > 1:
            shift_score += min(0.5, abs(skew) / 3)
        
        return shift_score
    
    def _calculate_transition_probability(self, warnings: Dict[str, float]) -> float:
        """Calculate composite transition probability from warnings."""
        if not warnings:
            return 0.0
        
        # Weighted average with emphasis on multiple signals
        weights = {
            'volatility_distortion': 0.20,
            'correlation_breakdown': 0.20,
            'liquidity_fragmentation': 0.15,
            'spread_anomaly': 0.15,
            'flow_toxicity': 0.15,
            'distribution_shift': 0.15
        }
        
        weighted_sum = sum(
            warnings.get(k, 0) * v for k, v in weights.items()
        )
        
        # Boost if multiple high signals
        high_signals = sum(1 for v in warnings.values() if v > 0.7)
        if high_signals >= 3:
            weighted_sum *= 1.3
        
        return min(1.0, weighted_sum)
    
    def _estimate_time_to_transition(self, warnings: Dict[str, float]) -> int:
        """Estimate minutes until regime transition."""
        avg_warning = sum(warnings.values()) / len(warnings) if warnings else 0
        
        if avg_warning > 0.8:
            return 5  # Minutes
        elif avg_warning > 0.6:
            return 30
        elif avg_warning > 0.4:
            return 120
        else:
            return 480
    
    def _determine_severity(self, probability: float, warnings: Dict) -> str:
        """Determine severity level of warning."""
        high_signals = sum(1 for v in warnings.values() if v > 0.7)
        
        if probability > self.critical_threshold or high_signals >= 4:
            return "critical"
        elif probability > self.warning_threshold or high_signals >= 2:
            return "high"
        elif probability > 0.4:
            return "medium"
        else:
            return "low"
    
    def _predict_target_regime(self, current: MarketRegime, warnings: Dict) -> str:
        """Predict what regime we're transitioning to."""
        # Simple heuristic based on dominant warning
        max_warning = max(warnings.items(), key=lambda x: x[1]) if warnings else (None, 0)
        
        warning_regime_map = {
            'volatility_distortion': 'high_volatility',
            'correlation_breakdown': 'risk_off',
            'liquidity_fragmentation': 'liquidity_crisis',
            'spread_anomaly': 'market_stress',
            'flow_toxicity': 'informed_trading_dominated',
            'distribution_shift': 'tail_risk_elevated'
        }
        
        return warning_regime_map.get(max_warning[0], 'unknown_transition')
    
    def _regime_to_string(self, regime: MarketRegime) -> str:
        """Convert regime to string representation."""
        return f"{regime.volatility_state}_{regime.liquidity_state}"
    
    def should_reduce_risk(self) -> Tuple[bool, float]:
        """
        Determine if risk should be reduced based on active warnings.
        
        Returns:
            (should_reduce, recommended_reduction_pct)
        """
        if not self.active_warnings:
            return False, 0.0
        
        # Get most severe warning
        most_severe = max(self.active_warnings, key=lambda w: w.transition_probability)
        
        if most_severe.severity == "critical":
            return True, 0.75
        elif most_severe.severity == "high":
            return True, 0.50
        elif most_severe.severity == "medium":
            return True, 0.25
        else:
            return False, 0.0
    
    def get_active_warnings(self) -> List[RegimeTransitionSignal]:
        """Get all active warning signals."""
        # Clean up old warnings
        cutoff = datetime.now() - timedelta(hours=1)
        self.active_warnings = [
            w for w in self.active_warnings 
            if w.timestamp > cutoff and w.transition_probability > self.warning_threshold
        ]
        return self.active_warnings
    
    def generate_early_warning_report(self) -> Dict[str, Any]:
        """Generate comprehensive early warning report."""
        recent_signals = [s for s in self.signal_history[-100:]]
        
        if not recent_signals:
            return {'status': 'no_data'}
        
        avg_probability = sum(s.transition_probability for s in recent_signals) / len(recent_signals)
        max_probability = max(s.transition_probability for s in recent_signals)
        
        warning_counts = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        for s in recent_signals:
            warning_counts[s.severity] += 1
        
        should_reduce, reduction = self.should_reduce_risk()
        
        return {
            'current_status': 'warning' if self.active_warnings else 'normal',
            'active_warnings_count': len(self.active_warnings),
            'avg_transition_probability_24h': avg_probability,
            'max_transition_probability_24h': max_probability,
            'warning_distribution': warning_counts,
            'should_reduce_risk': should_reduce,
            'recommended_risk_reduction': reduction,
            'latest_signals': [{
                'timestamp': s.timestamp.isoformat(),
                'probability': s.transition_probability,
                'from': s.from_regime,
                'to': s.to_regime,
                'severity': s.severity,
                'time_to_transition': s.estimated_time_to_transition
            } for s in self.active_warnings[-5:]]
        }


class RegimeApplicabilityEngine:
    """
    Evaluates how applicable a trading thesis is to current market regime.
    Maintains historical performance data by regime.
    """
    
    def __init__(
        self,
        similarity_threshold: float = 0.7,
        min_historical_trades: int = 10,
        underrepresentation_threshold: float = 0.1
    ):
        self.similarity_threshold = similarity_threshold
        self.min_historical_trades = min_historical_trades
        self.underrepresentation_threshold = underrepresentation_threshold
        
        # Historical performance database by regime
        self.regime_performance_db: Dict[str, List[RegimePerformance]] = defaultdict(list)
        
        # Known regime clusters (for similarity matching)
        self.known_regimes: Dict[str, MarketRegime] = {}
        
    def evaluate_regime_fit(
        self,
        claims: List[Claim],
        current_regime: MarketRegime,
        strategy_signature: Optional[str] = None
    ) -> Tuple[float, bool, List[Dict[str, Any]]]:
        """
        Evaluate how well current regime supports the claims/thesis.
        
        Returns:
            Tuple of:
            - applicability_score: 0 to 1
            - underrepresentation_warning: True if regime is underrepresented
            - regime_analysis: Detailed analysis per claim
        """
        regime_analysis = []
        total_score = 0.0
        
        for claim in claims:
            claim_fit = self._evaluate_claim_regime_fit(claim, current_regime, strategy_signature)
            regime_analysis.append(claim_fit)
            total_score += claim_fit['score']
            
        avg_score = total_score / len(claims) if claims else 0.0
        
        # Check for underrepresentation
        regime_hash = self._compute_regime_hash(current_regime)
        historical_data = self.regime_performance_db.get(regime_hash, [])
        
        total_historical_trades = sum(p.trades_count for p in historical_data)
        underrepresented = total_historical_trades < self.min_historical_trades
        
        # Also check similar regimes
        similar_regimes = self._find_similar_regimes(current_regime)
        total_similar_trades = sum(
            sum(p.trades_count for p in self.regime_performance_db.get(r.regime2_id, []))
            for r in similar_regimes if r.similarity_score > self.similarity_threshold
        )
        
        if total_similar_trades < self.min_historical_trades * 2:
            underrepresented = True
            
        return avg_score, underrepresented, regime_analysis
    
    def _evaluate_claim_regime_fit(
        self,
        claim: Claim,
        current_regime: MarketRegime,
        strategy_signature: Optional[str]
    ) -> Dict[str, Any]:
        """Evaluate regime fit for a single claim"""
        
        score = 1.0
        concerns = []
        
        if claim.claim_type == ClaimType.THESIS:
            # Check if thesis has regime constraints
            if claim.regime_constraints:
                regime_match = self._check_regime_constraints(current_regime, claim.regime_constraints)
                if not regime_match:
                    score *= 0.5
                    concerns.append("Regime constraints not fully met")
                    
        elif claim.claim_type == ClaimType.INFERRED_CAUSAL_LINK:
            # Causal links may break in extreme regimes
            if current_regime.volatility_state == "extreme":
                score *= 0.7
                concerns.append("Causal relationships unstable in extreme volatility")
            if current_regime.correlation_clustering == "high":
                score *= 0.8
                concerns.append("High correlation regime may distort causal inference")
                
        elif claim.claim_type == ClaimType.PREDICTED_OUTCOME:
            # Predictions less reliable in certain regimes
            if current_regime.macro_event_density == "elevated":
                score *= 0.6
                concerns.append("Elevated macro uncertainty reduces prediction reliability")
            if current_regime.order_flow_toxicity == "toxic":
                score *= 0.7
                concerns.append("Toxic flow makes price predictions less reliable")
                
        # Check historical performance if we have strategy signature
        if strategy_signature:
            hist_score = self._check_historical_regime_performance(
                strategy_signature, current_regime
            )
            score = (score + hist_score) / 2  # Blend current and historical
            
        return {
            'claim_id': claim.id,
            'claim_type': claim.claim_type.value,
            'score': score,
            'concerns': concerns,
            'regime_compatible': score > 0.6
        }
    
    def _check_regime_constraints(
        self,
        current_regime: MarketRegime,
        constraints: List[str]
    ) -> bool:
        """Check if current regime meets specified constraints"""
        
        regime_vector = current_regime.to_vector()
        
        for constraint in constraints:
            # Parse simple constraints like "volatility < 0.5"
            if "volatility" in constraint.lower():
                if "high" in constraint.lower() and regime_vector['volatility'] < 0.6:
                    return False
                if "low" in constraint.lower() and regime_vector['volatility'] > 0.3:
                    return False
            if "liquidity" in constraint.lower():
                if "ample" in constraint.lower() and regime_vector['liquidity'] > 0.3:
                    return False
            if "toxic" in constraint.lower():
                if "not" in constraint.lower() and regime_vector['flow_toxicity'] > 0.5:
                    return False
                    
        return True
    
    def _check_historical_regime_performance(
        self,
        strategy_signature: str,
        current_regime: MarketRegime
    ) -> float:
        """Check historical performance of strategy in similar regimes"""
        
        regime_hash = self._compute_regime_hash(current_regime)
        
        # Direct match
        if regime_hash in self.regime_performance_db:
            perf_data = self.regime_performance_db[regime_hash]
            strategy_perf = [p for p in perf_data if p.regime_hash == strategy_signature]
            
            if strategy_perf:
                avg_win_rate = sum(p.win_rate for p in strategy_perf) / len(strategy_perf)
                return avg_win_rate
                
        # Find similar regimes
        similar = self._find_similar_regimes(current_regime)
        if similar:
            weighted_scores = []
            for sim in similar:
                if sim.similarity_score > self.similarity_threshold:
                    perf_data = self.regime_performance_db.get(sim.regime2_id, [])
                    strategy_perf = [p for p in perf_data if p.regime_hash == strategy_signature]
                    
                    if strategy_perf:
                        avg_win_rate = sum(p.win_rate for p in strategy_perf) / len(strategy_perf)
                        weighted_scores.append(avg_win_rate * sim.similarity_score)
                        
            if weighted_scores:
                return sum(weighted_scores) / len(weighted_scores)
                
        return 0.5  # Neutral if no data
    
    def _compute_regime_hash(self, regime: MarketRegime) -> str:
        """Compute a hash representing the regime state"""
        vector = regime.to_vector()
        # Discretize to create regime buckets
        discrete = {
            'vol': round(vector['volatility'] * 3) / 3,
            'liq': round(vector['liquidity'] * 3) / 3,
            'trend': round(vector['trend_persistence'] * 2) / 2,
            'corr': round(vector['correlation'] * 2) / 2,
            'macro': round(vector['macro_density'] * 3) / 3,
            'toxic': round(vector['flow_toxicity'] * 2) / 2,
            'spread': round(vector['spread_impact'] * 3) / 3
        }
        
        import hashlib
        content = f"{discrete['vol']}{discrete['liq']}{discrete['trend']}{discrete['corr']}"
        return hashlib.sha256(content.encode()).hexdigest()[:12]
    
    def _find_similar_regimes(
        self,
        target_regime: MarketRegime,
        top_k: int = 5
    ) -> List[RegimeSimilarity]:
        """Find historically known regimes similar to target"""
        
        if not self.known_regimes:
            return []
            
        target_vector = target_regime.to_vector()
        similarities = []
        
        for regime_id, known_regime in self.known_regimes.items():
            known_vector = known_regime.to_vector()
            
            # Calculate Euclidean distance across dimensions
            differences = {}
            squared_diffs = []
            
            for dim in target_vector:
                diff = abs(target_vector[dim] - known_vector[dim])
                differences[dim] = diff
                squared_diffs.append(diff ** 2)
                
            distance = np.sqrt(sum(squared_diffs))
            similarity = max(0, 1 - (distance / np.sqrt(len(target_vector))))
            
            similarities.append(RegimeSimilarity(
                regime1_id=self._compute_regime_hash(target_regime),
                regime2_id=regime_id,
                similarity_score=similarity,
                dimension_differences=differences
            ))
            
        # Sort by similarity and return top k
        similarities.sort(key=lambda x: x.similarity_score, reverse=True)
        return similarities[:top_k]
    
    def record_regime_performance(
        self,
        regime: MarketRegime,
        strategy_signature: str,
        trade_result: Dict[str, Any]
    ) -> None:
        """Record performance outcome for a regime-strategy pair"""
        
        regime_hash = self._compute_regime_hash(regime)
        
        # Update or create performance record
        existing = [
            p for p in self.regime_performance_db[regime_hash]
            if p.regime_hash == strategy_signature
        ]
        
        if existing:
            # Update existing record
            perf = existing[0]
            perf.trades_count += 1
            # Rolling average update
            n = perf.trades_count
            perf.win_rate = (perf.win_rate * (n-1) + (1 if trade_result['pnl'] > 0 else 0)) / n
            perf.avg_return = (perf.avg_return * (n-1) + trade_result['pnl']) / n
        else:
            # Create new record
            new_perf = RegimePerformance(
                regime_hash=strategy_signature,
                trades_count=1,
                win_rate=1.0 if trade_result['pnl'] > 0 else 0.0,
                avg_return=trade_result['pnl'],
                sharpe_ratio=0.0,  # Requires multiple trades
                max_drawdown=trade_result.get('drawdown', 0.0),
                confidence=0.1
            )
            self.regime_performance_db[regime_hash].append(new_perf)
            
        # Store regime for similarity matching
        if regime_hash not in self.known_regimes:
            self.known_regimes[regime_hash] = regime
            
        logger.info(f"Recorded performance for regime {regime_hash}, strategy {strategy_signature}")
    
    def get_regime_characterization(
        self,
        regime: MarketRegime
    ) -> Dict[str, Any]:
        """Get detailed characterization of current regime"""
        
        vector = regime.to_vector()
        
        # Determine regime "personality"
        characteristics = []
        
        if vector['volatility'] > 0.6:
            characteristics.append("high_volatility")
        if vector['liquidity'] > 0.5:
            characteristics.append("liquidity_constrained")
        if vector['flow_toxicity'] > 0.5:
            characteristics.append("toxic_flow")
        if vector['macro_density'] > 0.5:
            characteristics.append("macro_eventful")
        if vector['trend_persistence'] > 0.7:
            characteristics.append("trending")
        elif vector['trend_persistence'] < 0.3:
            characteristics.append("mean_reverting")
            
        return {
            'vector': vector,
            'characteristics': characteristics,
            'trading_difficulty': self._estimate_trading_difficulty(vector),
            'prediction_reliability': self._estimate_prediction_reliability(vector)
        }
    
    def _estimate_trading_difficulty(self, vector: Dict[str, float]) -> str:
        """Estimate how difficult current regime is for trading"""
        
        difficulty_score = (
            vector['volatility'] * 0.3 +
            vector['liquidity'] * 0.25 +
            vector['flow_toxicity'] * 0.25 +
            vector['spread_impact'] * 0.2
        )
        
        if difficulty_score > 0.7:
            return "extreme"
        elif difficulty_score > 0.5:
            return "difficult"
        elif difficulty_score > 0.3:
            return "moderate"
        else:
            return "favorable"
    
    def _estimate_prediction_reliability(self, vector: Dict[str, float]) -> str:
        """Estimate reliability of predictions in current regime"""
        
        reliability_score = (
            (1 - vector['volatility']) * 0.3 +
            (1 - vector['macro_density']) * 0.3 +
            vector['trend_persistence'] * 0.2 +
            (1 - vector['flow_toxicity']) * 0.2
        )
        
        if reliability_score > 0.8:
            return "high"
        elif reliability_score > 0.6:
            return "moderate"
        elif reliability_score > 0.4:
            return "low"
        else:
            return "very_low"


# Lazy import for numpy
try:
    import numpy as np
except ImportError:
    np = None


class VolatilityRegimeDetector:
    """
    Volatility Regime Detector
    
    Classifies current volatility environment:
    - Low vol (compression)
    - Normal vol
    - High vol (expansion)
    - Extreme vol (crisis)
    
    Uses multiple timeframes and realized vs implied vol comparison.
    """
    
    def __init__(self, lookback_days: int = 30):
        self.lookback_days = lookback_days
        self.volatility_history: Dict[str, Deque[float]] = {
            '1d': deque(maxlen=lookback_days),
            '5d': deque(maxlen=lookback_days // 5),
            '20d': deque(maxlen=lookback_days // 20)
        }
        self.implied_vol_history: Deque[float] = deque(maxlen=lookback_days)
        
    def update_realized_vol(
        self,
        timeframe: str,
        volatility: float,
        timestamp: Optional[datetime] = None
    ):
        """Update realized volatility for a timeframe."""
        if timeframe in self.volatility_history:
            self.volatility_history[timeframe].append({
                'vol': volatility,
                'timestamp': timestamp or datetime.now()
            })
    
    def update_implied_vol(self, iv: float, timestamp: Optional[datetime] = None):
        """Update implied volatility (from options)."""
        self.implied_vol_history.append({
            'iv': iv,
            'timestamp': timestamp or datetime.now()
        })
    
    def detect_volatility_regime(self) -> Dict[str, Any]:
        """
        Detect current volatility regime.
        
        Returns:
            Volatility regime classification with confidence
        """
        # Get current volatilities
        current_1d = self._get_current_vol('1d')
        current_5d = self._get_current_vol('5d')
        current_20d = self._get_current_vol('20d')
        
        if not all([current_1d, current_5d, current_20d]):
            return {'status': 'insufficient_data', 'regime': 'unknown'}
        
        # Calculate historical percentiles
        vols_1d = [v['vol'] for v in self.volatility_history['1d']]
        if not vols_1d:
            return {'status': 'insufficient_data', 'regime': 'unknown'}
        
        percentile_1d = self._calculate_percentile(current_1d, vols_1d)
        
        # Determine regime
        regime, confidence = self._classify_regime(percentile_1d, current_1d, current_5d, current_20d)
        
        # Check vol of vol (volatility of volatility)
        vol_of_vol = np.std(vols_1d[-5:]) if len(vols_1d) >= 5 else 0
        
        # Check IV-RV spread if implied vol available
        iv_rv_spread = None
        if self.implied_vol_history:
            current_iv = self.implied_vol_history[-1]['iv']
            iv_rv_spread = (current_iv - current_1d) / current_1d if current_1d > 0 else 0
        
        return {
            'regime': regime,
            'confidence': confidence,
            'current_1d_vol': current_1d,
            'current_5d_vol': current_5d,
            'current_20d_vol': current_20d,
            'volatility_percentile': percentile_1d,
            'vol_of_vol': vol_of_vol,
            'iv_rv_spread': iv_rv_spread,
            'term_structure': self._get_vol_term_structure(),
            'trading_implications': self._get_trading_implications(regime, iv_rv_spread)
        }
    
    def _get_current_vol(self, timeframe: str) -> Optional[float]:
        """Get most recent volatility for timeframe."""
        history = self.volatility_history[timeframe]
        if history:
            return history[-1]['vol']
        return None
    
    def _calculate_percentile(self, value: float, history: List[float]) -> float:
        """Calculate percentile of value in historical distribution."""
        if not history:
            return 0.5
        return sum(1 for v in history if v < value) / len(history)
    
    def _classify_regime(
        self,
        percentile: float,
        vol_1d: float,
        vol_5d: float,
        vol_20d: float
    ) -> Tuple[str, float]:
        """Classify volatility regime."""
        # Trend analysis
        vol_trend = 'increasing' if vol_1d > vol_5d > vol_20d else \
                   'decreasing' if vol_1d < vol_5d < vol_20d else 'mixed'
        
        if percentile > 0.9:
            return 'extreme', 0.9
        elif percentile > 0.75:
            return 'high', 0.8
        elif percentile > 0.9 and vol_trend == 'decreasing':
            return 'extreme_fading', 0.7
        elif percentile < 0.1:
            return 'compression', 0.8
        elif percentile < 0.25:
            return 'low', 0.7
        else:
            return 'normal', 0.6
    
    def _get_vol_term_structure(self) -> str:
        """Analyze volatility term structure."""
        vol_1d = self._get_current_vol('1d') or 0
        vol_5d = self._get_current_vol('5d') or 0
        vol_20d = self._get_current_vol('20d') or 0
        
        if vol_1d > vol_5d > vol_20d:
            return 'backwardation'  # Short-term stress
        elif vol_1d < vol_5d < vol_20d:
            return 'contango'  # Elevated long-term expectations
        else:
            return 'mixed'
    
    def _get_trading_implications(self, regime: str, iv_rv_spread: Optional[float]) -> List[str]:
        """Get trading implications for regime."""
        implications = []
        
        if regime == 'extreme':
            implications.append('Reduce position sizes by 50-70%')
            implications.append('Widen stop losses')
            implications.append('Avoid new directional trades')
        elif regime == 'compression':
            implications.append('Prepare for volatility expansion')
            implications.append('Consider long volatility strategies')
            implications.append('Tighten stops - breakouts imminent')
        elif regime == 'high':
            implications.append('Mean reversion strategies favored')
            implications.append('Reduce holding periods')
        
        if iv_rv_spread and iv_rv_spread > 0.3:
            implications.append('IV > RV: Options expensive, consider selling vol')
        elif iv_rv_spread and iv_rv_spread < -0.2:
            implications.append('IV < RV: Options cheap, consider buying vol')
        
        return implications if implications else ['Normal trading conditions']


class CorrelationStressTester:
    """
    Correlation Stress Tester
    
    Monitors correlation breakdown during stress periods.
    
    Key insight: Correlations → 1 during crisis, destroying diversification.
    """
    
    def __init__(self, lookback_days: int = 30):
        self.lookback_days = lookback_days
        self.price_history: Dict[str, Deque[Dict]] = {}
        self.correlation_matrix: Optional[pd.DataFrame] = None
        
    def update_prices(self, symbol: str, price: float, timestamp: Optional[datetime] = None):
        """Update price history for correlation calculation."""
        if symbol not in self.price_history:
            self.price_history[symbol] = deque(maxlen=self.lookback_days)
        
        self.price_history[symbol].append({
            'price': price,
            'timestamp': timestamp or datetime.now()
        })
    
    def calculate_correlation_matrix(self) -> Dict[str, Any]:
        """Calculate and analyze correlation matrix."""
        if len(self.price_history) < 2:
            return {'status': 'insufficient_symbols'}
        
        # Build returns dataframe
        returns_data = {}
        for symbol, history in self.price_history.items():
            if len(history) < 10:
                continue
            
            prices = [h['price'] for h in history]
            returns = [(prices[i] - prices[i-1]) / prices[i-1] 
                      for i in range(1, len(prices))]
            returns_data[symbol] = returns
        
        if len(returns_data) < 2:
            return {'status': 'insufficient_data'}
        
        # Create dataframe and calculate correlation
        import pandas as pd
        df = pd.DataFrame(returns_data)
        corr_matrix = df.corr()
        
        self.correlation_matrix = corr_matrix
        
        # Analyze correlation structure
        avg_correlation = corr_matrix.values[np.triu_indices_from(corr_matrix.values, k=1)].mean()
        max_correlation = corr_matrix.values[np.triu_indices_from(corr_matrix.values, k=1)].max()
        
        # Check for correlation breakdown (correlations > 0.8)
        high_corr_pairs = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                if corr_matrix.iloc[i, j] > 0.8:
                    high_corr_pairs.append({
                        'pair': (corr_matrix.columns[i], corr_matrix.columns[j]),
                        'correlation': corr_matrix.iloc[i, j]
                    })
        
        return {
            'average_correlation': avg_correlation,
            'max_correlation': max_correlation,
            'high_correlation_pairs': high_corr_pairs,
            'correlation_regime': self._classify_correlation_regime(avg_correlation),
            'diversification_effectiveness': 1 - avg_correlation,
            'stress_indicator': len(high_corr_pairs) > len(self.price_history) * 0.3
        }
    
    def _classify_correlation_regime(self, avg_corr: float) -> str:
        """Classify correlation regime."""
        if avg_corr > 0.8:
            return 'extreme_convergence'
        elif avg_corr > 0.6:
            return 'high_correlation'
        elif avg_corr > 0.4:
            return 'moderate_correlation'
        else:
            return 'diversified'
    
    def stress_test_portfolio(self, weights: Dict[str, float]) -> Dict[str, Any]:
        """
        Stress test portfolio under correlation breakdown.
        
        Args:
            weights: Portfolio weights by symbol
            
        Returns:
            Stress test results
        """
        corr_data = self.calculate_correlation_matrix()
        
        if corr_data.get('status') == 'insufficient_data':
            return {'status': 'insufficient_data'}
        
        current_corr = corr_data['average_correlation']
        
        # Simulate correlation breakdown (all correlations → 0.9)
        stress_corr = 0.9
        
        # Calculate portfolio variance impact
        # Simplified: var_p = sum(w_i^2 * var_i) + 2*rho*sum(w_i*w_j*std_i*std_j)
        portfolio_variance_normal = self._estimate_portfolio_variance(weights, current_corr)
        portfolio_variance_stress = self._estimate_portfolio_variance(weights, stress_corr)
        
        variance_increase = (portfolio_variance_stress - portfolio_variance_normal) / portfolio_variance_normal \
                           if portfolio_variance_normal > 0 else 0
        
        return {
            'current_correlation': current_corr,
            'stress_correlation': stress_corr,
            'normal_portfolio_variance': portfolio_variance_normal,
            'stress_portfolio_variance': portfolio_variance_stress,
            'variance_increase_pct': variance_increase * 100,
            'diversification_benefit_at_risk': variance_increase > 0.5,
            'recommendation': 'Reduce position sizes' if variance_increase > 0.5 else 'Diversification adequate'
        }
    
    def _estimate_portfolio_variance(self, weights: Dict[str, float], correlation: float) -> float:
        """Estimate portfolio variance given correlation assumption."""
        # Simplified calculation assuming equal volatilities
        n = len(weights)
        avg_weight = np.mean(list(weights.values()))
        
        # Portfolio variance = avg_var/n + (n-1)/n * corr * avg_var
        # Assuming avg_var = 1 for relative comparison
        return (1/n + (n-1)/n * correlation) * avg_weight**2


class FatTailRiskCalculator:
    """
    Fat Tail Risk Calculator
    
    Estimates risk of extreme events using:
    - Historical VaR/CVaR
    - Extreme Value Theory
    - Tail risk metrics (skewness, kurtosis)
    """
    
    def __init__(self, confidence_levels: List[float] = None):
        self.confidence_levels = confidence_levels or [0.95, 0.99, 0.999]
        self.return_history: Deque[float] = deque(maxlen=252)  # 1 year
        
    def update_returns(self, daily_return: float, timestamp: Optional[datetime] = None):
        """Update return history."""
        self.return_history.append({
            'return': daily_return,
            'timestamp': timestamp or datetime.now()
        })
    
    def calculate_tail_risk(self) -> Dict[str, Any]:
        """Calculate comprehensive tail risk metrics."""
        if len(self.return_history) < 30:
            return {'status': 'insufficient_data'}
        
        returns = [r['return'] for r in self.return_history]
        
        # Basic statistics
        mean_ret = np.mean(returns)
        std_ret = np.std(returns)
        
        # Higher moments
        skewness = self._calculate_skewness(returns)
        excess_kurtosis = self._calculate_kurtosis(returns)
        
        # VaR and CVaR at different confidence levels
        var_metrics = {}
        for conf in self.confidence_levels:
            var = np.percentile(returns, (1 - conf) * 100)
            cvar = np.mean([r for r in returns if r <= var]) if any(r <= var for r in returns) else var
            
            var_metrics[f'var_{int(conf*100)}'] = var
            var_metrics[f'cvar_{int(conf*100)}'] = cvar
        
        # Maximum drawdown from returns
        cumulative = np.cumprod([1 + r for r in returns])
        running_max = np.maximum.accumulate(cumulative)
        drawdowns = (cumulative - running_max) / running_max
        max_drawdown = np.min(drawdowns)
        
        # Tail risk score (0-1)
        tail_risk_score = (
            abs(skewness) * 0.2 +
            max(0, excess_kurtosis) * 0.3 +
            abs(max_drawdown) * 5 * 0.3 +
            (abs(var_metrics.get('var_99', 0)) / std_ret if std_ret > 0 else 0) * 0.2
        )
        tail_risk_score = min(1.0, tail_risk_score)
        
        return {
            'tail_risk_score': tail_risk_score,
            'skewness': skewness,
            'excess_kurtosis': excess_kurtosis,
            'max_drawdown': max_drawdown,
            'value_at_risk': var_metrics,
            'tail_regime': self._classify_tail_regime(skewness, excess_kurtosis),
            'extreme_event_probability': self._estimate_extreme_probability(returns),
            'risk_adjusted_position_limit': max(0.1, 1 - tail_risk_score)
        }
    
    def _calculate_skewness(self, returns: List[float]) -> float:
        """Calculate skewness of returns."""
        n = len(returns)
        mean = np.mean(returns)
        std = np.std(returns)
        
        if std == 0:
            return 0
        
        return (np.mean([(r - mean) ** 3 for r in returns]) / (std ** 3))
    
    def _calculate_kurtosis(self, returns: List[float]) -> float:
        """Calculate excess kurtosis of returns."""
        n = len(returns)
        mean = np.mean(returns)
        std = np.std(returns)
        
        if std == 0:
            return 0
        
        kurt = np.mean([(r - mean) ** 4 for r in returns]) / (std ** 4)
        return kurt - 3  # Excess kurtosis
    
    def _classify_tail_regime(self, skewness: float, kurtosis: float) -> str:
        """Classify tail regime."""
        if kurtosis > 3:
            if skewness < -0.5:
                return 'fat_tail_left'  # Crash risk
            elif skewness > 0.5:
                return 'fat_tail_right'  # Spike risk
            else:
                return 'fat_tail_both'  # High volatility
        elif kurtosis < 0:
            return 'thin_tails'  # Abnormally calm
        else:
            return 'normal_tails'
    
    def _estimate_extreme_probability(self, returns: List[float], threshold: float = -0.05) -> float:
        """Estimate probability of extreme move (>5% daily)."""
        extremes = sum(1 for r in returns if abs(r) > abs(threshold))
        return extremes / len(returns) if returns else 0


class IntradaySeasonalityAnalyzer:
    """
    Intraday Seasonality Analyzer
    
    Analyzes patterns within trading days:
    - Opening range behavior
    - Lunch hour effects
    - Closing auction dynamics
    - Best/worst execution times
    """
    
    def __init__(self):
        self.hourly_stats: Dict[int, List[Dict]] = defaultdict(list)
        self.minute_patterns: Dict[int, Deque[Dict]] = {}
        
    def record_minute_data(
        self,
        timestamp: datetime,
        price: float,
        volume: float,
        volatility: float,
        spread_bps: float
    ):
        """Record intraday minute data."""
        minute_of_day = timestamp.hour * 60 + timestamp.minute
        
        if minute_of_day not in self.minute_patterns:
            self.minute_patterns[minute_of_day] = deque(maxlen=30)  # 30 days
        
        self.minute_patterns[minute_of_day].append({
            'price': price,
            'volume': volume,
            'volatility': volatility,
            'spread_bps': spread_bps,
            'timestamp': timestamp
        })
        
        # Also update hourly stats
        hour = timestamp.hour
        self.hourly_stats[hour].append({
            'price': price,
            'volume': volume,
            'volatility': volatility
        })
    
    def analyze_seasonality(self) -> Dict[str, Any]:
        """Analyze intraday seasonal patterns."""
        if len(self.hourly_stats) < 6:  # Need at least 6 hours of data
            return {'status': 'insufficient_data'}
        
        # Analyze by hour
        hourly_analysis = {}
        for hour, data in self.hourly_stats.items():
            if len(data) < 10:
                continue
            
            volumes = [d['volume'] for d in data]
            volatilities = [d['volatility'] for d in data]
            
            hourly_analysis[hour] = {
                'avg_volume': np.mean(volumes),
                'avg_volatility': np.mean(volatilities),
                'volume_percentile': self._calculate_hourly_volume_percentile(hour, volumes),
                'trading_quality_score': self._calculate_trading_quality(hour, data)
            }
        
        # Identify best/worst times
        if hourly_analysis:
            sorted_by_quality = sorted(
                hourly_analysis.items(),
                key=lambda x: x[1]['trading_quality_score'],
                reverse=True
            )
            
            best_hours = [h[0] for h in sorted_by_quality[:3]]
            worst_hours = [h[0] for h in sorted_by_quality[-3:]]
        else:
            best_hours = []
            worst_hours = []
        
        return {
            'hourly_analysis': hourly_analysis,
            'best_trading_hours': best_hours,
            'avoid_hours': worst_hours,
            'opening_range_character': self._analyze_opening_range(),
            'closing_auction_dynamics': self._analyze_closing_auction(),
            'lunch_effect': self._analyze_lunch_effect(hourly_analysis)
        }
    
    def _calculate_hourly_volume_percentile(self, hour: int, volumes: List[float]) -> float:
        """Calculate volume percentile for this hour vs others."""
        all_volumes = []
        for h, data in self.hourly_stats.items():
            all_volumes.extend([d['volume'] for d in data])
        
        if not all_volumes:
            return 0.5
        
        avg_vol = np.mean(volumes)
        return sum(1 for v in all_volumes if v < avg_vol) / len(all_volumes)
    
    def _calculate_trading_quality(self, hour: int, data: List[Dict]) -> float:
        """Calculate trading quality score for hour."""
        # Higher volume, lower volatility = better
        volumes = [d['volume'] for d in data]
        volatilities = [d['volatility'] for d in data]
        
        avg_volume = np.mean(volumes)
        avg_vol = np.mean(volatilities)
        
        # Normalize and combine
        volume_score = min(1.0, avg_volume / 1000000)  # Assume 1M is max
        vol_score = max(0, 1 - avg_vol / 0.5)  # Lower vol is better
        
        return volume_score * 0.6 + vol_score * 0.4
    
    def _analyze_opening_range(self) -> str:
        """Analyze opening range (first 30 minutes) characteristics."""
        opening_data = []
        for minute in range(570, 600):  # 9:30 - 10:00
            if minute in self.minute_patterns:
                opening_data.extend(self.minute_patterns[minute])
        
        if len(opening_data) < 10:
            return 'insufficient_data'
        
        volatilities = [d['volatility'] for d in opening_data]
        avg_vol = np.mean(volatilities)
        
        if avg_vol > 0.3:
            return 'high_volatility_discovery'
        elif avg_vol > 0.2:
            return 'normal_discovery'
        else:
            return 'calm_opening'
    
    def _analyze_closing_auction(self) -> str:
        """Analyze closing auction (last 15 minutes) characteristics."""
        closing_data = []
        for minute in range(945, 960):  # 15:45 - 16:00
            if minute in self.minute_patterns:
                closing_data.extend(self.minute_patterns[minute])
        
        if len(closing_data) < 10:
            return 'insufficient_data'
        
        volumes = [d['volume'] for d in closing_data]
        avg_volume = np.mean(volumes)
        
        # Compare to average
        all_volumes = []
        for patterns in self.minute_patterns.values():
            all_volumes.extend([p['volume'] for p in patterns])
        
        if all_volumes:
            closing_volume_pct = avg_volume / np.mean(all_volumes)
            if closing_volume_pct > 2:
                return 'high_volume_auction'
            elif closing_volume_pct > 1.5:
                return 'elevated_closing_volume'
            else:
                return 'normal_closing'
        
        return 'unknown'
    
    def _analyze_lunch_effect(self, hourly_analysis: Dict) -> Dict[str, Any]:
        """Analyze lunch hour (12:00-14:00) effects."""
        lunch_hours = [12, 13]
        lunch_data = {h: hourly_analysis[h] for h in lunch_hours if h in hourly_analysis}
        
        if not lunch_data:
            return {'detected': False}
        
        # Compare lunch to morning
        morning_hours = [9, 10, 11]
        morning_data = {h: hourly_analysis[h] for h in morning_hours if h in hourly_analysis}
        
        if morning_data:
            lunch_vol = np.mean([d['avg_volume'] for d in lunch_data.values()])
            morning_vol = np.mean([d['avg_volume'] for d in morning_data.values()])
            
            volume_drop = (morning_vol - lunch_vol) / morning_vol if morning_vol > 0 else 0
            
            return {
                'detected': volume_drop > 0.3,
                'volume_drop_pct': volume_drop * 100,
                'implication': 'Avoid trading during lunch lull' if volume_drop > 0.4 else 'Lunch effect minimal'
            }
        
        return {'detected': False}
