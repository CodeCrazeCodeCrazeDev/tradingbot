"""
Causal Attribution Engine

Post-trade causal analysis to explain WHY outcomes occurred.
Maps outcomes back to decisions, evidence, and market conditions.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class CausalFactorType(Enum):
    """Types of causal factors"""
    MARKET_MOVEMENT = "market_movement"
    SIGNAL_ACCURACY = "signal_accuracy"
    TIMING = "timing"
    EXECUTION_QUALITY = "execution_quality"
    REGIME_MATCH = "regime_match"
    UNEXPECTED_EVENT = "unexpected_event"
    ALPHA_DECAY = "alpha_decay"
    RANDOM_NOISE = "random_noise"


class MarketDriverType(Enum):
    """Types of market drivers for causal isolation"""
    MACRO_DRIVER = "macro_driver"
    LIQUIDITY_SWEEP = "liquidity_sweep"
    POSITIONING_UNWIND = "positioning_unwind"
    NEWS_SHOCK = "news_shock"
    ALGO_FLOW = "algo_flow"
    OPTION_HEDGING = "option_hedging"
    CROSS_ASSET_ARB = "cross_asset_arbitrage"
    RETAIL_SENTIMENT = "retail_sentiment"
    INSTITUTIONAL_BLOCK = "institutional_block"
    DARK_POOL_PRINT = "dark_pool_print"


@dataclass
class MarketDriverHypothesis:
    """Hypothesis about what drove a market move"""
    driver_type: MarketDriverType
    confidence: float  # 0-1
    evidence: List[str]
    expected_price_impact: float
    duration_estimate_minutes: int
    validation_rules: List[str]
    

@dataclass
class CausalDriverIsolation:
    """Complete causal driver breakdown for a trade"""
    trade_id: str
    symbol: str
    timestamp: datetime
    primary_driver: Optional[MarketDriverHypothesis]
    secondary_drivers: List[MarketDriverHypothesis]
    rejected_drivers: List[Tuple[MarketDriverType, str]]  # (type, rejection_reason)
    driver_agreement_score: float  # How well drivers agree
    narrative_vs_reality_divergence: float  # Narrative vs actual driver mismatch
    lessons: List[str]


class CausalDriverIsolationEngine:
    """
    Causal Driver Isolation Engine
    
    Break every trade into causal hypotheses:
    - Macro driver?
    - Liquidity sweep?
    - Positioning unwind?
    - News shock?
    
    Then validate which ones mattered.
    
    Result:
    - Stops false reasoning
    - Builds true market understanding
    - Improves transfer across regimes
    """
    
    def __init__(self):
        self.driver_history: Dict[str, List[CausalDriverIsolation]] = defaultdict(list)
        self.validation_accuracy: Dict[MarketDriverType, List[float]] = defaultdict(list)
        
    def isolate_drivers(
        self,
        trade: Dict[str, Any],
        market_context: Dict[str, Any],
        microstructure: Dict[str, Any]
    ) -> CausalDriverIsolation:
        """
        Isolate what actually caused the market move.
        
        Args:
            trade: Trade details
            market_context: Market conditions during trade
            microstructure: Order book and flow data
            
        Returns:
            CausalDriverIsolation with validated drivers
        """
        symbol = trade.get('symbol', 'unknown')
        trade_id = trade.get('id', 'unknown')
        
        # Generate hypotheses for all driver types
        hypotheses = []
        
        # 1. Macro Driver Hypothesis
        macro_hypothesis = self._test_macro_driver(trade, market_context)
        hypotheses.append(macro_hypothesis)
        
        # 2. Liquidity Sweep Hypothesis
        liquidity_hypothesis = self._test_liquidity_sweep(trade, microstructure)
        hypotheses.append(liquidity_hypothesis)
        
        # 3. Positioning Unwind Hypothesis
        unwind_hypothesis = self._test_positioning_unwind(trade, market_context, microstructure)
        hypotheses.append(unwind_hypothesis)
        
        # 4. News Shock Hypothesis
        news_hypothesis = self._test_news_shock(trade, market_context)
        hypotheses.append(news_hypothesis)
        
        # 5. Algo Flow Hypothesis
        algo_hypothesis = self._test_algo_flow(trade, microstructure)
        hypotheses.append(algo_hypothesis)
        
        # 6. Cross-Asset Arbitrage Hypothesis
        arb_hypothesis = self._test_cross_asset_arb(trade, market_context)
        hypotheses.append(arb_hypothesis)
        
        # Validate and rank hypotheses
        validated = self._validate_hypotheses(hypotheses, trade, market_context)
        
        # Separate primary, secondary, and rejected
        primary = None
        secondary = []
        rejected = []
        
        if validated:
            primary = validated[0]
            secondary = validated[1:3] if len(validated) > 1 else []
            rejected = [(h.driver_type, "Low confidence") for h in hypotheses if h not in validated]
        
        # Calculate driver agreement
        agreement_score = self._calculate_driver_agreement(primary, secondary)
        
        # Calculate narrative vs reality divergence
        narrative = trade.get('narrative', '')
        divergence = self._calculate_narrative_divergence(narrative, primary)
        
        # Extract lessons
        lessons = self._extract_driver_lessons(primary, secondary, rejected, trade)
        
        isolation = CausalDriverIsolation(
            trade_id=trade_id,
            symbol=symbol,
            timestamp=datetime.now(),
            primary_driver=primary,
            secondary_drivers=secondary,
            rejected_drivers=rejected,
            driver_agreement_score=agreement_score,
            narrative_vs_reality_divergence=divergence,
            lessons=lessons
        )
        
        self.driver_history[symbol].append(isolation)
        
        return isolation
    
    def _test_macro_driver(self, trade: Dict, market_context: Dict) -> MarketDriverHypothesis:
        """Test if macro events drove the move."""
        evidence = []
        confidence = 0.0
        
        # Check for macro events
        macro_events = market_context.get('macro_events', [])
        if macro_events:
            for event in macro_events:
                if event.get('impact', 0) > 0.5:
                    evidence.append(f"High-impact macro event: {event.get('name')}")
                    confidence += 0.3
        
        # Check for correlation with macro assets
        macro_correlation = market_context.get('macro_correlation', 0)
        if abs(macro_correlation) > 0.7:
            evidence.append(f"High macro correlation: {macro_correlation:.2f}")
            confidence += 0.3
        
        # Check timing relative to macro releases
        minutes_to_release = market_context.get('minutes_to_macro_release', 999)
        if minutes_to_release < 5:
            evidence.append(f"Trade within {minutes_to_release} min of macro release")
            confidence += 0.4
        
        return MarketDriverHypothesis(
            driver_type=MarketDriverType.MACRO_DRIVER,
            confidence=min(1.0, confidence),
            evidence=evidence,
            expected_price_impact=market_context.get('macro_expected_impact', 0),
            duration_estimate_minutes=30,
            validation_rules=["Macro correlation > 0.7", "Post-release price action aligns"]
        )
    
    def _test_liquidity_sweep(self, trade: Dict, microstructure: Dict) -> MarketDriverHypothesis:
        """Test if liquidity sweep drove the move."""
        evidence = []
        confidence = 0.0
        
        # Check for stop runs
        stop_levels = microstructure.get('stop_levels', [])
        price_move = trade.get('price_movement', 0)
        
        for stop in stop_levels:
            if abs(price_move) > abs(stop['distance']):
                evidence.append(f"Price swept stop level at {stop['price']}")
                confidence += 0.4
        
        # Check for thin order book
        book_depth = microstructure.get('book_depth', 0)
        if book_depth < 100:
            evidence.append(f"Thin order book: {book_depth} contracts")
            confidence += 0.3
        
        # Check for rapid price move
        velocity = microstructure.get('price_velocity', 0)
        if velocity > 5:  # 5x normal
            evidence.append(f"High price velocity: {velocity:.1f}x normal")
            confidence += 0.3
        
        return MarketDriverHypothesis(
            driver_type=MarketDriverType.LIQUIDITY_SWEEP,
            confidence=min(1.0, confidence),
            evidence=evidence,
            expected_price_impact=price_move * 1.5,
            duration_estimate_minutes=5,
            validation_rules=["Stop level taken", "Immediate reversal"]
        )
    
    def _test_positioning_unwind(
        self, trade: Dict, market_context: Dict, microstructure: Dict
    ) -> MarketDriverHypothesis:
        """Test if positioning unwind drove the move."""
        evidence = []
        confidence = 0.0
        
        # Check for crowded positioning
        positioning = market_context.get('positioning', {})
        long_pct = positioning.get('long_percentage', 50)
        
        if long_pct > 80:
            evidence.append(f"Crowded longs: {long_pct:.0f}%")
            if trade.get('direction') == 'sell':
                confidence += 0.5  # Unwind likely
        elif long_pct < 20:
            evidence.append(f"Crowded shorts: {100-long_pct:.0f}%")
            if trade.get('direction') == 'buy':
                confidence += 0.5
        
        # Check for liquidation cascades
        liquidations = microstructure.get('liquidations', 0)
        if liquidations > 1000000:  # $1M+
            evidence.append(f"High liquidations: ${liquidations:,.0f}")
            confidence += 0.3
        
        # Check for delta bleed
        delta_change = microstructure.get('delta_change', 0)
        if abs(delta_change) > 0.3:
            evidence.append(f"Large delta change: {delta_change:.2f}")
            confidence += 0.2
        
        return MarketDriverHypothesis(
            driver_type=MarketDriverType.POSITIONING_UNWIND,
            confidence=min(1.0, confidence),
            evidence=evidence,
            expected_price_impact=trade.get('price_movement', 0),
            duration_estimate_minutes=15,
            validation_rules=["Positioning data aligns", "Cascade pattern in order book"]
        )
    
    def _test_news_shock(self, trade: Dict, market_context: Dict) -> MarketDriverHypothesis:
        """Test if news shock drove the move."""
        evidence = []
        confidence = 0.0
        
        # Check for news events
        news = market_context.get('news', [])
        for item in news:
            if item.get('sentiment_score', 0) > 0.8:
                evidence.append(f"High sentiment news: {item.get('headline', '')[:50]}")
                confidence += 0.4
        
        # Check for social media spike
        social_volume = market_context.get('social_volume_spike', 0)
        if social_volume > 3:  # 3x normal
            evidence.append(f"Social volume spike: {social_volume:.1f}x")
            confidence += 0.3
        
        # Check for sudden volume
        volume_spike = market_context.get('volume_spike', 0)
        if volume_spike > 5:  # 5x normal
            evidence.append(f"Volume spike: {volume_spike:.1f}x normal")
            confidence += 0.3
        
        return MarketDriverHypothesis(
            driver_type=MarketDriverType.NEWS_SHOCK,
            confidence=min(1.0, confidence),
            evidence=evidence,
            expected_price_impact=market_context.get('news_expected_impact', 0),
            duration_estimate_minutes=60,
            validation_rules=["News timestamp matches", "Volume confirms"]
        )
    
    def _test_algo_flow(self, trade: Dict, microstructure: Dict) -> MarketDriverHypothesis:
        """Test if algo flow drove the move."""
        evidence = []
        confidence = 0.0
        
        # Check for iceberg patterns
        iceberg_detected = microstructure.get('iceberg_detected', False)
        if iceberg_detected:
            evidence.append("Iceberg order detected")
            confidence += 0.3
        
        # Check for VWAP deviation
        vwap_dev = microstructure.get('vwap_deviation', 0)
        if abs(vwap_dev) > 0.5:
            evidence.append(f"High VWAP deviation: {vwap_dev:.2f}%")
            confidence += 0.3
        
        # Check for twap patterns
        twap_pattern = microstructure.get('twap_pattern_score', 0)
        if twap_pattern > 0.7:
            evidence.append(f"TWAP pattern detected: {twap_pattern:.2f}")
            confidence += 0.4
        
        return MarketDriverHypothesis(
            driver_type=MarketDriverType.ALGO_FLOW,
            confidence=min(1.0, confidence),
            evidence=evidence,
            expected_price_impact=0,
            duration_estimate_minutes=120,
            validation_rules=["Pattern persistence", "Volume profile match"]
        )
    
    def _test_cross_asset_arb(self, trade: Dict, market_context: Dict) -> MarketDriverHypothesis:
        """Test if cross-asset arbitrage drove the move."""
        evidence = []
        confidence = 0.0
        
        # Check for correlation breakdown
        correlations = market_context.get('correlation_changes', {})
        for asset, change in correlations.items():
            if abs(change) > 0.3:
                evidence.append(f"Correlation breakdown with {asset}: {change:+.2f}")
                confidence += 0.3
        
        # Check for basis/futures dislocation
        basis = market_context.get('basis', 0)
        if abs(basis) > 0.5:
            evidence.append(f"High basis: {basis:.2f}%")
            confidence += 0.4
        
        return MarketDriverHypothesis(
            driver_type=MarketDriverType.CROSS_ASSET_ARB,
            confidence=min(1.0, confidence),
            evidence=evidence,
            expected_price_impact=0,
            duration_estimate_minutes=10,
            validation_rules=["Arb window open", "Mean reversion"]
        )
    
    def _validate_hypotheses(
        self,
        hypotheses: List[MarketDriverHypothesis],
        trade: Dict,
        market_context: Dict
    ) -> List[MarketDriverHypothesis]:
        """Validate hypotheses against actual outcome."""
        validated = []
        
        for h in hypotheses:
            if h.confidence > 0.5:
                # Post-hoc validation
                validated.append(h)
                self.validation_accuracy[h.driver_type].append(1.0 if h.confidence > 0.7 else 0.5)
        
        # Sort by confidence
        validated.sort(key=lambda x: x.confidence, reverse=True)
        return validated
    
    def _calculate_driver_agreement(
        self,
        primary: Optional[MarketDriverHypothesis],
        secondary: List[MarketDriverHypothesis]
    ) -> float:
        """Calculate how well primary and secondary drivers agree."""
        if not primary:
            return 0.0
        
        if not secondary:
            return 1.0
        
        # Agreement = how complementary the drivers are
        agreement = 1.0
        for s in secondary:
            # Penalize if secondary contradicts primary direction
            if (primary.expected_price_impact > 0 and s.expected_price_impact < 0) or \
               (primary.expected_price_impact < 0 and s.expected_price_impact > 0):
                agreement -= 0.2
        
        return max(0.0, agreement)
    
    def _calculate_narrative_divergence(
        self,
        narrative: str,
        primary: Optional[MarketDriverHypothesis]
    ) -> float:
        """Calculate divergence between stated narrative and actual driver."""
        if not narrative or not primary:
            return 0.0
        
        # Simple keyword matching
        narrative_lower = narrative.lower()
        driver_keywords = {
            MarketDriverType.MACRO_DRIVER: ['fed', 'cpi', 'jobs', 'gdp', 'rates'],
            MarketDriverType.LIQUIDITY_SWEEP: ['stop', 'sweep', 'liquidity'],
            MarketDriverType.POSITIONING_UNWIND: ['liquidation', 'cascade', 'unwind'],
            MarketDriverType.NEWS_SHOCK: ['news', 'announcement', 'earnings'],
        }
        
        keywords = driver_keywords.get(primary.driver_type, [])
        matches = sum(1 for kw in keywords if kw in narrative_lower)
        
        # Divergence = 1 - match_ratio
        return 1.0 - (matches / max(1, len(keywords)))
    
    def _extract_driver_lessons(
        self,
        primary: Optional[MarketDriverHypothesis],
        secondary: List[MarketDriverHypothesis],
        rejected: List[Tuple[MarketDriverType, str]],
        trade: Dict
    ) -> List[str]:
        """Extract lessons from driver isolation."""
        lessons = []
        
        if primary:
            lessons.append(f"Primary driver identified as {primary.driver_type.value}")
            
            if primary.confidence < 0.7:
                lessons.append("Low driver confidence - consider waiting for clarity")
        
        if len(secondary) > 2:
            lessons.append("Multiple competing drivers - reduce position size")
        
        for driver_type, reason in rejected:
            if driver_type == MarketDriverType.LIQUIDITY_SWEEP and trade.get('direction') == 'buy':
                lessons.append("Not a liquidity sweep - entry may be premature")
        
        return lessons
    
    def get_driver_accuracy(self, driver_type: MarketDriverType) -> float:
        """Get historical accuracy for a driver type."""
        if driver_type not in self.validation_accuracy:
            return 0.5
        
        scores = self.validation_accuracy[driver_type]
        return sum(scores) / len(scores) if scores else 0.5
    
    def generate_driver_report(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Generate report on driver performance."""
        if symbol:
            history = self.driver_history.get(symbol, [])
        else:
            history = [item for sublist in self.driver_history.values() for item in sublist]
        
        if not history:
            return {'error': 'No driver history available'}
        
        # Count primary drivers
        driver_counts = defaultdict(int)
        divergence_scores = []
        
        for isolation in history:
            if isolation.primary_driver:
                driver_counts[isolation.primary_driver.driver_type.value] += 1
            divergence_scores.append(isolation.narrative_vs_reality_divergence)
        
        return {
            'total_analyzed': len(history),
            'primary_driver_distribution': dict(driver_counts),
            'avg_narrative_divergence': sum(divergence_scores) / len(divergence_scores),
            'driver_accuracy_by_type': {
                dt.value: self.get_driver_accuracy(dt) for dt in MarketDriverType
            },
            'lessons_learned': list(set([
                lesson for h in history for lesson in h.lessons
            ]))[:10]
        }


@dataclass
class CausalFactor:
    """A factor that contributed to an outcome"""
    factor_type: CausalFactorType
    description: str
    contribution_pct: float  # -100 to +100
    evidence: List[str]
    confidence: float


@dataclass
class CausalAttribution:
    """Complete causal attribution for a trade outcome"""
    decision_id: str
    symbol: str
    realized_pnl: float
    expected_pnl: float
    attribution_error: float  # Difference between expected and attributed
    factors: List[CausalFactor]
    primary_cause: str
    secondary_causes: List[str]
    lessons: List[str]
    timestamp: datetime = field(default_factory=datetime.utcnow)


class CausalAttributionEngine:
    """
    Performs post-trade causal attribution analysis.
    
    Answers:
    - What actually caused the PnL?
    - How did the decision lead to the outcome?
    - What was the calibration error?
    - What can be learned?
    """
    
    def __init__(self):
        self.attribution_history: List[CausalAttribution] = []
        self.factor_effectiveness: Dict[CausalFactorType, List[float]] = defaultdict(list)
        
    def analyze_outcome(
        self,
        decision: Dict[str, Any],
        outcome: Dict[str, Any],
        market_context: Dict[str, Any]
    ) -> CausalAttribution:
        """
        Perform causal attribution analysis.
        
        Args:
            decision: The decision that led to the trade
            outcome: The realized outcome
            market_context: Market conditions during the trade
            
        Returns:
            CausalAttribution with complete analysis
        """
        factors = []
        
        # Factor 1: Market movement attribution
        market_factor = self._attribute_market_movement(
            decision, outcome, market_context
        )
        factors.append(market_factor)
        
        # Factor 2: Signal accuracy
        signal_factor = self._attribute_signal_accuracy(
            decision, outcome, market_context
        )
        factors.append(signal_factor)
        
        # Factor 3: Timing attribution
        timing_factor = self._attribute_timing(
            decision, outcome, market_context
        )
        factors.append(timing_factor)
        
        # Factor 4: Execution quality
        execution_factor = self._attribute_execution(
            decision, outcome
        )
        factors.append(execution_factor)
        
        # Factor 5: Regime match
        regime_factor = self._attribute_regime_match(
            decision, outcome, market_context
        )
        factors.append(regime_factor)
        
        # Factor 6: Unexpected events
        event_factor = self._attribute_unexpected_events(
            outcome, market_context
        )
        if event_factor:
            factors.append(event_factor)
            
        # Normalize contributions to sum to 100%
        factors = self._normalize_contributions(factors, outcome.get('pnl', 0))
        
        # Determine primary and secondary causes
        sorted_factors = sorted(factors, key=lambda f: abs(f.contribution_pct), reverse=True)
        primary_cause = sorted_factors[0].description if sorted_factors else "Unknown"
        secondary_causes = [f.description for f in sorted_factors[1:3]]
        
        # Extract lessons
        lessons = self._extract_lessons(factors, decision, outcome)
        
        # Calculate attribution error
        total_attributed = sum(f.contribution_pct for f in factors)
        realized = outcome.get('pnl', 0) * 100  # Convert to percentage
        attribution_error = abs(realized - total_attributed)
        
        attribution = CausalAttribution(
            decision_id=decision.get('id', 'unknown'),
            symbol=decision.get('symbol', 'unknown'),
            realized_pnl=outcome.get('pnl', 0),
            expected_pnl=decision.get('expected_pnl', 0),
            attribution_error=attribution_error,
            factors=factors,
            primary_cause=primary_cause,
            secondary_causes=secondary_causes,
            lessons=lessons
        )
        
        self.attribution_history.append(attribution)
        
        # Update factor effectiveness tracking
        for factor in factors:
            self.factor_effectiveness[factor.factor_type].append(
                abs(factor.contribution_pct)
            )
            
        return attribution
    
    def _attribute_market_movement(
        self,
        decision: Dict,
        outcome: Dict,
        market_context: Dict
    ) -> CausalFactor:
        """Attribute outcome to market movement"""
        
        direction = decision.get('direction', 'hold')
        market_return = market_context.get('market_return', 0)
        beta = market_context.get('beta', 1.0)
        
        # Expected contribution from market beta
        expected_market_contribution = market_return * beta
        
        # Actual PnL
        actual_pnl = outcome.get('pnl', 0)
        
        # Attribution: how much of actual PnL is explained by market
        if actual_pnl != 0:
            contribution = (expected_market_contribution / actual_pnl) * 100
        else:
            contribution = 0
            
        return CausalFactor(
            factor_type=CausalFactorType.MARKET_MOVEMENT,
            description=f"Market return of {market_return:.2%} with beta {beta}",
            contribution_pct=max(-100, min(100, contribution)),
            evidence=[
                f"Market return: {market_return:.2%}",
                f"Position beta: {beta}",
                f"Expected contribution: {expected_market_contribution:.2%}"
            ],
            confidence=0.8
        )
    
    def _attribute_signal_accuracy(
        self,
        decision: Dict,
        outcome: Dict,
        market_context: Dict
    ) -> CausalFactor:
        """Attribute outcome to signal accuracy"""
        
        signal_direction = decision.get('direction', 'hold')
        realized_return = outcome.get('pnl', 0)
        
        # Signal was correct if direction matches outcome sign
        signal_correct = (
            (signal_direction == 'buy' and realized_return > 0) or
            (signal_direction == 'sell' and realized_return < 0)
        )
        
        confidence = decision.get('confidence', 0.5)
        
        if signal_correct:
            contribution = confidence * 30  # Up to 30% attribution
            description = f"Signal correctly predicted direction with {confidence:.0%} confidence"
        else:
            contribution = -confidence * 30
            description = f"Signal predicted wrong direction despite {confidence:.0%} confidence"
            
        return CausalFactor(
            factor_type=CausalFactorType.SIGNAL_ACCURACY,
            description=description,
            contribution_pct=contribution,
            evidence=[
                f"Signal direction: {signal_direction}",
                f"Realized return: {realized_return:.2%}",
                f"Signal correct: {signal_correct}"
            ],
            confidence=0.7
        )
    
    def _attribute_timing(
        self,
        decision: Dict,
        outcome: Dict,
        market_context: Dict
    ) -> CausalFactor:
        """Attribute outcome to entry/exit timing"""
        
        entry_timing_score = market_context.get('entry_timing_score', 0.5)
        
        # Good timing = bought at relative low, sold at relative high
        timing_contribution = (entry_timing_score - 0.5) * 40  # +/- 20%
        
        return CausalFactor(
            factor_type=CausalFactorType.TIMING,
            description=f"Entry timing score: {entry_timing_score:.2f}",
            contribution_pct=timing_contribution,
            evidence=[
                f"Entry price vs range: {market_context.get('entry_position_in_range', 0):.0%}",
                f"Timing score: {entry_timing_score:.2f}"
            ],
            confidence=0.6
        )
    
    def _attribute_execution(
        self,
        decision: Dict,
        outcome: Dict
    ) -> CausalFactor:
        """Attribute outcome to execution quality"""
        
        expected_slippage = decision.get('expected_slippage', 0.001)
        realized_slippage = outcome.get('slippage', 0.001)
        
        slippage_diff = expected_slippage - realized_slippage  # Positive = good
        
        # Convert to contribution (slippage is negative, so positive diff is good)
        contribution = slippage_diff * 100 * 10  # Scale to percentage contribution
        
        return CausalFactor(
            factor_type=CausalFactorType.EXECUTION_QUALITY,
            description=f"Slippage: expected {expected_slippage:.3%}, realized {realized_slippage:.3%}",
            contribution_pct=contribution,
            evidence=[
                f"Expected slippage: {expected_slippage:.3%}",
                f"Realized slippage: {realized_slippage:.3%}",
                f"Fill quality: {outcome.get('fill_behavior', 'unknown')}"
            ],
            confidence=0.9
        )
    
    def _attribute_regime_match(
        self,
        decision: Dict,
        outcome: Dict,
        market_context: Dict
    ) -> CausalFactor:
        """Attribute outcome to regime match quality"""
        
        predicted_regime = decision.get('predicted_regime', 'unknown')
        realized_regime = outcome.get('realized_regime', 'unknown')
        
        regime_match = predicted_regime == realized_regime
        
        if regime_match:
            contribution = 10  # Small positive for correct regime prediction
            description = f"Correctly predicted {predicted_regime} regime"
        else:
            contribution = -15  # Negative for regime mismatch
            description = f"Regime mismatch: predicted {predicted_regime}, got {realized_regime}"
            
        return CausalFactor(
            factor_type=CausalFactorType.REGIME_MATCH,
            description=description,
            contribution_pct=contribution,
            evidence=[
                f"Predicted regime: {predicted_regime}",
                f"Realized regime: {realized_regime}",
                f"Regime fit score: {decision.get('regime_fit_score', 0):.2f}"
            ],
            confidence=0.65
        )
    
    def _attribute_unexpected_events(
        self,
        outcome: Dict,
        market_context: Dict
    ) -> Optional[CausalFactor]:
        """Attribute outcome to unexpected events"""
        
        events = market_context.get('unexpected_events', [])
        
        if not events:
            return None
            
        # Estimate impact of unexpected events
        event_impact = market_context.get('event_return_impact', 0)
        
        return CausalFactor(
            factor_type=CausalFactorType.UNEXPECTED_EVENT,
            description=f"Unexpected events: {', '.join(events)}",
            contribution_pct=event_impact * 100,
            evidence=[f"Event: {e}" for e in events],
            confidence=0.5
        )
    
    def _normalize_contributions(
        self,
        factors: List[CausalFactor],
        realized_pnl: float
    ) -> List[CausalFactor]:
        """Normalize factor contributions to explain realized PnL"""
        
        if not factors or realized_pnl == 0:
            return factors
            
        # Target: contributions should sum to realized PnL (in percentage)
        target = realized_pnl * 100
        current_sum = sum(f.contribution_pct for f in factors)
        
        if current_sum == 0:
            return factors
            
        # Scale factors proportionally
        scale = target / current_sum
        
        normalized = []
        for factor in factors:
            normalized_factor = CausalFactor(
                factor_type=factor.factor_type,
                description=factor.description,
                contribution_pct=factor.contribution_pct * scale,
                evidence=factor.evidence,
                confidence=factor.confidence
            )
            normalized.append(normalized_factor)
            
        return normalized
    
    def _extract_lessons(
        self,
        factors: List[CausalFactor],
        decision: Dict,
        outcome: Dict
    ) -> List[str]:
        """Extract actionable lessons from attribution"""
        
        lessons = []
        
        # Lesson from signal accuracy
        signal_factors = [f for f in factors if f.factor_type == CausalFactorType.SIGNAL_ACCURACY]
        if signal_factors and signal_factors[0].contribution_pct < 0:
            lessons.append(
                f"Signal from {decision.get('source', 'unknown')} was wrong - "
                "consider reducing weight or requiring more evidence"
            )
            
        # Lesson from regime mismatch
        regime_factors = [f for f in factors if f.factor_type == CausalFactorType.REGIME_MATCH]
        if regime_factors and regime_factors[0].contribution_pct < 0:
            lessons.append(
                "Regime prediction failed - improve regime detection or add regime-specific validation"
            )
            
        # Lesson from execution
        exec_factors = [f for f in factors if f.factor_type == CausalFactorType.EXECUTION_QUALITY]
        if exec_factors and abs(exec_factors[0].contribution_pct) > 5:
            lessons.append(
                f"Execution contributed {exec_factors[0].contribution_pct:.1f}% - "
                "review execution parameters"
            )
            
        # Lesson from unexpected events
        event_factors = [f for f in factors if f.factor_type == CausalFactorType.UNEXPECTED_EVENT]
        if event_factors:
            lessons.append(
                "Unexpected events impacted outcome - consider adding event risk monitoring"
            )
            
        return lessons if lessons else ["No clear lessons - outcome within expected variance"]
    
    def generate_attribution_report(
        self,
        symbol: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive attribution report"""
        
        attributions = self.attribution_history
        
        if symbol:
            attributions = [a for a in attributions if a.symbol == symbol]
        if since:
            attributions = [a for a in attributions if a.timestamp >= since]
            
        if not attributions:
            return {'error': 'No attributions found for criteria'}
            
        # Aggregate by factor type
        factor_totals = defaultdict(lambda: {'count': 0, 'total_contribution': 0})
        
        for attr in attributions:
            for factor in attr.factors:
                ft = factor.factor_type
                factor_totals[ft]['count'] += 1
                factor_totals[ft]['total_contribution'] += factor.contribution_pct
                
        # Calculate averages
        factor_averages = {
            ft: {
                'avg_contribution': data['total_contribution'] / data['count'],
                'occurrences': data['count']
            }
            for ft, data in factor_totals.items()
        }
        
        return {
            'total_attributions': len(attributions),
            'avg_attribution_error': sum(a.attribution_error for a in attributions) / len(attributions),
            'factor_breakdown': factor_averages,
            'most_common_primary_causes': self._get_common_causes(attributions),
            'lessons_learned': self._aggregate_lessons(attributions)
        }
    
    def _get_common_causes(
        self,
        attributions: List[CausalAttribution]
    ) -> List[Tuple[str, int]]:
        """Get most common primary causes"""
        
        cause_counts = defaultdict(int)
        for attr in attributions:
            cause_counts[attr.primary_cause] += 1
            
        return sorted(cause_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    def _aggregate_lessons(
        self,
        attributions: List[CausalAttribution]
    ) -> List[str]:
        """Aggregate and deduplicate lessons"""
        
        all_lessons = []
        for attr in attributions:
            all_lessons.extend(attr.lessons)
            
        # Simple deduplication by similarity
        unique_lessons = []
        for lesson in all_lessons:
            if not any(self._lesson_similar(lesson, ul) for ul in unique_lessons):
                unique_lessons.append(lesson)
                
        return unique_lessons[:10]  # Top 10 lessons
    
    def _lesson_similar(self, l1: str, l2: str) -> bool:
        """Check if two lessons are similar"""
        # Simple heuristic: first 20 chars match
        return l1[:20] == l2[:20]
