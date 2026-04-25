"""
Multi-Hypothesis Generator and Cross-Strategy Arbitrator

Generates multiple competing hypotheses for the same signal.
Arbitrates between different strategies and tracks ensemble disagreement.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class HypothesisSource(Enum):
    """Source of hypothesis"""
    TREND_FOLLOWING = "trend_following"
    MEAN_REVERSION = "mean_reversion"
    MOMENTUM = "momentum"
    VALUE = "value"
    SENTIMENT = "sentiment"
    STATISTICAL_ARB = "statistical_arbitrage"
    ML_MODEL = "ml_model"
    FUNDAMENTAL = "fundamental"


@dataclass
class TradingHypothesis:
    """A single trading hypothesis"""
    id: str
    symbol: str
    source: HypothesisSource
    direction: str  # buy, sell, hold
    confidence: float
    expected_return: float
    timeframe: str
    rationale: str
    key_factors: List[str]
    invalidation_conditions: List[str]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def __hash__(self):
        return hash(self.id)


@dataclass
class EnsembleDecision:
    """Decision from ensemble of hypotheses"""
    consensus_direction: str
    consensus_confidence: float
    disagreement_score: float  # 0 = unanimous, 1 = maximum disagreement
    contributing_hypotheses: List[TradingHypothesis]
    dissenting_hypotheses: List[TradingHypothesis]
    arbitration_reasoning: str
    recommended_action: str


class MultiHypothesisGenerator:
    """
    Generates multiple hypotheses from different strategy perspectives.
    Each hypothesis represents a different interpretation of market data.
    """
    
    def __init__(self):
        self.hypothesis_counter = 0
        
    def generate_hypotheses(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        signal: Dict[str, Any]
    ) -> List[TradingHypothesis]:
        """
        Generate multiple competing hypotheses for a signal.
        
        Returns:
            List of hypotheses from different perspectives
        """
        hypotheses = []
        
        # Hypothesis 1: Trend following interpretation
        trend_hyp = self._generate_trend_hypothesis(symbol, market_data, signal)
        if trend_hyp:
            hypotheses.append(trend_hyp)
            
        # Hypothesis 2: Mean reversion interpretation
        mr_hyp = self._generate_mean_reversion_hypothesis(symbol, market_data, signal)
        if mr_hyp:
            hypotheses.append(mr_hyp)
            
        # Hypothesis 3: Momentum interpretation
        momentum_hyp = self._generate_momentum_hypothesis(symbol, market_data, signal)
        if momentum_hyp:
            hypotheses.append(momentum_hyp)
            
        # Hypothesis 4: Statistical/factor interpretation
        stat_hyp = self._generate_statistical_hypothesis(symbol, market_data, signal)
        if stat_hyp:
            hypotheses.append(stat_hyp)
            
        # Hypothesis 5: Sentiment interpretation
        sentiment_hyp = self._generate_sentiment_hypothesis(symbol, market_data, signal)
        if sentiment_hyp:
            hypotheses.append(sentiment_hyp)
            
        return hypotheses
    
    def _generate_trend_hypothesis(
        self,
        symbol: str,
        market_data: Dict,
        signal: Dict
    ) -> Optional[TradingHypothesis]:
        """Generate trend-following hypothesis"""
        
        price = market_data.get('price', 0)
        ma_50 = market_data.get('ma_50', price)
        ma_200 = market_data.get('ma_200', price)
        
        if price > ma_50 > ma_200:
            direction = 'buy'
            confidence = 0.7
            rationale = "Price above both MAs, trend is up"
        elif price < ma_50 < ma_200:
            direction = 'sell'
            confidence = 0.7
            rationale = "Price below both MAs, trend is down"
        else:
            direction = 'hold'
            confidence = 0.5
            rationale = "Mixed trend signals"
            
        return TradingHypothesis(
            id=f"trend_{self.hypothesis_counter}_{symbol}",
            symbol=symbol,
            source=HypothesisSource.TREND_FOLLOWING,
            direction=direction,
            confidence=confidence,
            expected_return=0.02 if direction != 'hold' else 0,
            timeframe='1d',
            rationale=rationale,
            key_factors=['price_vs_ma50', 'price_vs_ma200', 'trend_slope'],
            invalidation_conditions=['MA crossover against position']
        )
        
    def _generate_mean_reversion_hypothesis(
        self,
        symbol: str,
        market_data: Dict,
        signal: Dict
    ) -> Optional[TradingHypothesis]:
        """Generate mean reversion hypothesis"""
        
        rsi = market_data.get('rsi', 50)
        price = market_data.get('price', 0)
        bb_position = market_data.get('bb_position', 0.5)  # Bollinger Band position
        
        if rsi > 70 or bb_position > 0.9:
            direction = 'sell'
            confidence = 0.6
            rationale = "Overbought conditions, expect mean reversion"
        elif rsi < 30 or bb_position < 0.1:
            direction = 'buy'
            confidence = 0.6
            rationale = "Oversold conditions, expect mean reversion"
        else:
            direction = 'hold'
            confidence = 0.4
            rationale = "No extreme readings for mean reversion"
            
        self.hypothesis_counter += 1
        
        return TradingHypothesis(
            id=f"mr_{self.hypothesis_counter}_{symbol}",
            symbol=symbol,
            source=HypothesisSource.MEAN_REVERSION,
            direction=direction,
            confidence=confidence,
            expected_return=0.015 if direction != 'hold' else 0,
            timeframe='1d',
            rationale=rationale,
            key_factors=['rsi', 'bollinger_position', 'distance_from_mean'],
            invalidation_conditions=['Breakout beyond 2 standard deviations']
        )
        
    def _generate_momentum_hypothesis(
        self,
        symbol: str,
        market_data: Dict,
        signal: Dict
    ) -> Optional[TradingHypothesis]:
        """Generate momentum hypothesis"""
        
        momentum_1m = market_data.get('momentum_1m', 0)
        volume_surge = market_data.get('volume_surge', 1.0)
        
        if momentum_1m > 0.05 and volume_surge > 1.5:
            direction = 'buy'
            confidence = 0.65
            rationale = "Strong momentum with volume confirmation"
        elif momentum_1m < -0.05 and volume_surge > 1.5:
            direction = 'sell'
            confidence = 0.65
            rationale = "Negative momentum with volume confirmation"
        else:
            direction = 'hold'
            confidence = 0.4
            rationale = "Insufficient momentum"
            
        self.hypothesis_counter += 1
        
        return TradingHypothesis(
            id=f"mom_{self.hypothesis_counter}_{symbol}",
            symbol=symbol,
            source=HypothesisSource.MOMENTUM,
            direction=direction,
            confidence=confidence,
            expected_return=0.025 if direction != 'hold' else 0,
            timeframe='1d',
            rationale=rationale,
            key_factors=['price_momentum', 'volume_surge', 'momentum_acceleration'],
            invalidation_conditions=['Momentum deceleration']
        )
        
    def _generate_statistical_hypothesis(
        self,
        symbol: str,
        market_data: Dict,
        signal: Dict
    ) -> Optional[TradingHypothesis]:
        """Generate statistical/factor-based hypothesis"""
        
        z_score = market_data.get('z_score', 0)
        volatility_regime = market_data.get('volatility_regime', 'normal')
        
        if z_score < -2 and volatility_regime == 'normal':
            direction = 'buy'
            confidence = 0.55
            rationale = "Statistical anomaly: price below 2-sigma"
        elif z_score > 2 and volatility_regime == 'normal':
            direction = 'sell'
            confidence = 0.55
            rationale = "Statistical anomaly: price above 2-sigma"
        else:
            direction = 'hold'
            confidence = 0.5
            rationale = "No statistical edge detected"
            
        self.hypothesis_counter += 1
        
        return TradingHypothesis(
            id=f"stat_{self.hypothesis_counter}_{symbol}",
            symbol=symbol,
            source=HypothesisSource.STATISTICAL_ARB,
            direction=direction,
            confidence=confidence,
            expected_return=0.01 if direction != 'hold' else 0,
            timeframe='1d',
            rationale=rationale,
            key_factors=['z_score', 'volatility_regime', 'skewness'],
            invalidation_conditions=['Volatility regime shift']
        )
        
    def _generate_sentiment_hypothesis(
        self,
        symbol: str,
        market_data: Dict,
        signal: Dict
    ) -> Optional[TradingHypothesis]:
        """Generate sentiment-based hypothesis"""
        
        sentiment = market_data.get('sentiment', 0)
        news_score = market_data.get('news_score', 0)
        
        if sentiment > 0.6 and news_score > 0.5:
            direction = 'buy'
            confidence = 0.6
            rationale = "Positive sentiment and news momentum"
        elif sentiment < -0.6 and news_score < -0.5:
            direction = 'sell'
            confidence = 0.6
            rationale = "Negative sentiment and news momentum"
        else:
            direction = 'hold'
            confidence = 0.5
            rationale = "Mixed or neutral sentiment"
            
        self.hypothesis_counter += 1
        
        return TradingHypothesis(
            id=f"sent_{self.hypothesis_counter}_{symbol}",
            symbol=symbol,
            source=HypothesisSource.SENTIMENT,
            direction=direction,
            confidence=confidence,
            expected_return=0.02 if direction != 'hold' else 0,
            timeframe='1d',
            rationale=rationale,
            key_factors=['sentiment_score', 'news_momentum', 'social_volume'],
            invalidation_conditions=['Sentiment reversal']
        )


class CrossStrategyArbitrator:
    """
    Arbitrates between different strategy hypotheses.
    Resolves conflicts and generates ensemble consensus.
    """
    
    def __init__(self):
        self.source_weights = {
            HypothesisSource.TREND_FOLLOWING: 0.20,
            HypothesisSource.MEAN_REVERSION: 0.15,
            HypothesisSource.MOMENTUM: 0.20,
            HypothesisSource.STATISTICAL_ARB: 0.15,
            HypothesisSource.SENTIMENT: 0.15,
            HypothesisSource.ML_MODEL: 0.15
        }
        
    def arbitrate(
        self,
        hypotheses: List[TradingHypothesis],
        min_consensus_threshold: float = 0.6
    ) -> EnsembleDecision:
        """
        Arbitrate between competing hypotheses.
        
        Returns:
            EnsembleDecision with consensus and disagreement metrics
        """
        if not hypotheses:
            return EnsembleDecision(
                consensus_direction='hold',
                consensus_confidence=0.0,
                disagreement_score=0.0,
                contributing_hypotheses=[],
                dissenting_hypotheses=[],
                arbitration_reasoning="No hypotheses provided",
                recommended_action='abstain'
            )
            
        # Weight hypotheses by source reliability
        weighted_votes = {'buy': 0, 'sell': 0, 'hold': 0}
        total_weight = 0
        
        for hyp in hypotheses:
            weight = self.source_weights.get(hyp.source, 0.1) * hyp.confidence
            weighted_votes[hyp.direction] += weight
            total_weight += weight
            
        # Normalize
        for direction in weighted_votes:
            weighted_votes[direction] /= total_weight if total_weight > 0 else 1
            
        # Determine consensus
        consensus_direction = max(weighted_votes, key=weighted_votes.get)
        consensus_confidence = weighted_votes[consensus_direction]
        
        # Calculate disagreement
        # Disagreement is high when the non-consensus directions have significant weight
        non_consensus_weight = sum(
            w for d, w in weighted_votes.items() if d != consensus_direction
        )
        disagreement_score = non_consensus_weight / (consensus_confidence + non_consensus_weight)
        
        # Split hypotheses into contributing and dissenting
        contributing = [h for h in hypotheses if h.direction == consensus_direction]
        dissenting = [h for h in hypotheses if h.direction != consensus_direction]
        
        # Determine recommended action
        if consensus_confidence < 0.5:
            recommended_action = 'abstain'
        elif disagreement_score > 0.5:
            recommended_action = 'size_down'
        elif consensus_confidence >= min_consensus_threshold:
            recommended_action = 'execute'
        else:
            recommended_action = 'further_analysis'
            
        # Generate reasoning
        reasoning = self._generate_reasoning(
            consensus_direction, consensus_confidence, disagreement_score,
            contributing, dissenting
        )
        
        return EnsembleDecision(
            consensus_direction=consensus_direction,
            consensus_confidence=consensus_confidence,
            disagreement_score=disagreement_score,
            contributing_hypotheses=contributing,
            dissenting_hypotheses=dissenting,
            arbitration_reasoning=reasoning,
            recommended_action=recommended_action
        )
    
    def _generate_reasoning(
        self,
        consensus: str,
        confidence: float,
        disagreement: float,
        contributing: List[TradingHypothesis],
        dissenting: List[TradingHypothesis]
    ) -> str:
        """Generate human-readable arbitration reasoning"""
        
        reasoning_parts = [
            f"Consensus: {consensus} with {confidence:.1%} confidence",
            f"Disagreement score: {disagreement:.2f}",
            f"Supporting strategies: {', '.join(h.source.value for h in contributing)}",
        ]
        
        if dissenting:
            reasoning_parts.append(
                f"Dissenting strategies: {', '.join(h.source.value for h in dissenting)}"
            )
            reasoning_parts.append(
                f"Primary dissent rationale: {dissenting[0].rationale[:60]}"
            )
            
        return "; ".join(reasoning_parts)
    
    def calculate_disagreement_entropy(
        self,
        hypotheses: List[TradingHypothesis]
    ) -> float:
        """
        Calculate disagreement using information entropy.
        Higher entropy = more disagreement.
        """
        from math import log2
        
        if not hypotheses:
            return 0.0
            
        # Count directions
        counts = {'buy': 0, 'sell': 0, 'hold': 0}
        for hyp in hypotheses:
            counts[hyp.direction] += 1
            
        total = len(hypotheses)
        probabilities = [c / total for c in counts.values() if c > 0]
        
        # Calculate entropy
        entropy = -sum(p * log2(p) for p in probabilities)
        
        # Normalize by maximum possible entropy (log2(3) for 3 directions)
        max_entropy = log2(3)
        
        return entropy / max_entropy
    
    def update_source_weights(
        self,
        outcomes: List[Dict[str, Any]]
    ) -> None:
        """
        Update source weights based on historical performance.
        """
        source_performance = {}
        
        for outcome in outcomes:
            source = outcome.get('source')
            pnl = outcome.get('pnl', 0)
            
            if source:
                if source not in source_performance:
                    source_performance[source] = {'wins': 0, 'total': 0, 'pnl': 0}
                source_performance[source]['total'] += 1
                source_performance[source]['pnl'] += pnl
                if pnl > 0:
                    source_performance[source]['wins'] += 1
                    
        # Update weights based on win rate
        for source, perf in source_performance.items():
            if perf['total'] >= 5:  # Minimum sample size
                win_rate = perf['wins'] / perf['total']
                # Map to weight range [0.05, 0.30]
                new_weight = 0.05 + win_rate * 0.25
                
                try:
                    hyp_source = HypothesisSource(source)
                    self.source_weights[hyp_source] = new_weight
                except ValueError:
                    pass
                    
        # Normalize weights
        total_weight = sum(self.source_weights.values())
        for source in self.source_weights:
            self.source_weights[source] /= total_weight
