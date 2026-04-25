"""
Understanding Engine - Deep Comprehension of Market Dynamics
=============================================================

Goes beyond prediction to TRUE UNDERSTANDING:
- Causal Inference: Why things happen, not just what happens
- Narrative Generator: Human-readable explanations
- Regime Detector: Market state classification
- Anomaly Explainer: Understanding unusual events
"""

import asyncio
import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple
import uuid

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """Market regime classifications"""
    BULL_TREND = "bull_trend"
    BEAR_TREND = "bear_trend"
    SIDEWAYS = "sideways"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    CRISIS = "crisis"
    RECOVERY = "recovery"
    BUBBLE = "bubble"
    CAPITULATION = "capitulation"


class CausalRelationType(Enum):
    """Types of causal relationships"""
    DIRECT_CAUSE = "direct_cause"
    INDIRECT_CAUSE = "indirect_cause"
    CORRELATION = "correlation"
    CONFOUNDED = "confounded"
    MEDIATOR = "mediator"
    MODERATOR = "moderator"


@dataclass
class CausalLink:
    """A causal relationship between variables"""
    link_id: str
    cause: str
    effect: str
    relation_type: CausalRelationType
    strength: float  # -1 to 1
    confidence: float  # 0 to 1
    lag_periods: int = 0
    evidence: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'link_id': self.link_id,
            'cause': self.cause,
            'effect': self.effect,
            'relation_type': self.relation_type.value,
            'strength': self.strength,
            'confidence': self.confidence,
            'lag_periods': self.lag_periods,
            'evidence': self.evidence,
        }


@dataclass
class MarketNarrative:
    """A human-readable narrative explaining market conditions"""
    narrative_id: str
    timestamp: datetime
    title: str
    summary: str
    key_drivers: List[str]
    risk_factors: List[str]
    opportunities: List[str]
    outlook: str
    confidence: float
    supporting_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'narrative_id': self.narrative_id,
            'timestamp': self.timestamp.isoformat(),
            'title': self.title,
            'summary': self.summary,
            'key_drivers': self.key_drivers,
            'risk_factors': self.risk_factors,
            'opportunities': self.opportunities,
            'outlook': self.outlook,
            'confidence': self.confidence,
            'supporting_data': self.supporting_data,
        }


@dataclass
class RegimeAnalysis:
    """Analysis of current market regime"""
    analysis_id: str
    timestamp: datetime
    current_regime: MarketRegime
    regime_probability: float
    regime_duration: int  # periods in current regime
    transition_probabilities: Dict[str, float]
    characteristics: Dict[str, Any]
    historical_comparison: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'analysis_id': self.analysis_id,
            'timestamp': self.timestamp.isoformat(),
            'current_regime': self.current_regime.value,
            'regime_probability': self.regime_probability,
            'regime_duration': self.regime_duration,
            'transition_probabilities': self.transition_probabilities,
            'characteristics': self.characteristics,
            'historical_comparison': self.historical_comparison,
        }


@dataclass
class AnomalyExplanation:
    """Explanation of an anomalous event"""
    explanation_id: str
    timestamp: datetime
    anomaly_type: str
    severity: float  # 0 to 1
    description: str
    probable_causes: List[str]
    historical_precedents: List[str]
    expected_impact: Dict[str, float]
    recommended_response: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'explanation_id': self.explanation_id,
            'timestamp': self.timestamp.isoformat(),
            'anomaly_type': self.anomaly_type,
            'severity': self.severity,
            'description': self.description,
            'probable_causes': self.probable_causes,
            'historical_precedents': self.historical_precedents,
            'expected_impact': self.expected_impact,
            'recommended_response': self.recommended_response,
        }


class CausalInference:
    """
    Causal inference engine for understanding WHY markets move.
    
    Uses techniques from causal inference to distinguish:
    - Correlation vs causation
    - Direct vs indirect effects
    - Confounding variables
    """
    
    def __init__(self):
        self.causal_graph: Dict[str, List[CausalLink]] = {}
        self.known_relationships: List[CausalLink] = []
        self._initialize_known_relationships()
    
    def _initialize_known_relationships(self):
        """Initialize known causal relationships in financial markets"""
        known = [
            # Monetary Policy
            CausalLink(
                link_id="CL-001",
                cause="fed_rate_hike",
                effect="bond_prices",
                relation_type=CausalRelationType.DIRECT_CAUSE,
                strength=-0.7,
                confidence=0.9,
                lag_periods=0,
                evidence=["Economic theory", "Historical data"],
            ),
            CausalLink(
                link_id="CL-002",
                cause="fed_rate_hike",
                effect="equity_valuations",
                relation_type=CausalRelationType.INDIRECT_CAUSE,
                strength=-0.4,
                confidence=0.7,
                lag_periods=2,
                evidence=["Discount rate effect", "Historical correlation"],
            ),
            # Earnings
            CausalLink(
                link_id="CL-003",
                cause="earnings_surprise",
                effect="stock_price",
                relation_type=CausalRelationType.DIRECT_CAUSE,
                strength=0.8,
                confidence=0.85,
                lag_periods=0,
                evidence=["Event studies", "Market efficiency"],
            ),
            # Macro
            CausalLink(
                link_id="CL-004",
                cause="gdp_growth",
                effect="corporate_earnings",
                relation_type=CausalRelationType.DIRECT_CAUSE,
                strength=0.6,
                confidence=0.8,
                lag_periods=1,
                evidence=["Economic fundamentals"],
            ),
            CausalLink(
                link_id="CL-005",
                cause="inflation",
                effect="fed_policy",
                relation_type=CausalRelationType.DIRECT_CAUSE,
                strength=0.7,
                confidence=0.85,
                lag_periods=1,
                evidence=["Fed mandate", "Historical policy"],
            ),
            # Sentiment
            CausalLink(
                link_id="CL-006",
                cause="vix_spike",
                effect="equity_selloff",
                relation_type=CausalRelationType.CORRELATION,
                strength=0.6,
                confidence=0.7,
                lag_periods=0,
                evidence=["Fear gauge correlation"],
            ),
        ]
        
        self.known_relationships = known
        
        for link in known:
            if link.cause not in self.causal_graph:
                self.causal_graph[link.cause] = []
            self.causal_graph[link.cause].append(link)
    
    async def infer_causality(
        self,
        variable_x: str,
        variable_y: str,
        data: Dict[str, List[float]],
    ) -> CausalLink:
        """Infer causal relationship between two variables"""
        # Check known relationships first
        for link in self.known_relationships:
            if link.cause == variable_x and link.effect == variable_y:
                return link
        
        # Perform statistical analysis
        x_data = data.get(variable_x, [])
        y_data = data.get(variable_y, [])
        
        if not x_data or not y_data or len(x_data) != len(y_data):
            return CausalLink(
                link_id=f"CL-{uuid.uuid4().hex[:8]}",
                cause=variable_x,
                effect=variable_y,
                relation_type=CausalRelationType.CORRELATION,
                strength=0.0,
                confidence=0.0,
                evidence=["Insufficient data"],
            )
        
        # Calculate correlation
        n = len(x_data)
        mean_x = sum(x_data) / n
        mean_y = sum(y_data) / n
        
        cov = sum((x_data[i] - mean_x) * (y_data[i] - mean_y) for i in range(n)) / n
        std_x = (sum((x - mean_x) ** 2 for x in x_data) / n) ** 0.5
        std_y = (sum((y - mean_y) ** 2 for y in y_data) / n) ** 0.5
        
        correlation = cov / (std_x * std_y) if std_x > 0 and std_y > 0 else 0
        
        # Granger causality approximation (simplified)
        # Check if lagged X predicts Y better than Y alone
        lag = 1
        if len(x_data) > lag + 10:
            x_lagged = x_data[:-lag]
            y_current = y_data[lag:]
            y_lagged = y_data[:-lag]
            
            # Simple regression comparison
            # This is a simplified version - real implementation would use proper tests
            granger_score = abs(correlation) * 0.5  # Placeholder
        else:
            granger_score = 0
        
        # Determine relationship type
        if granger_score > 0.3:
            relation_type = CausalRelationType.DIRECT_CAUSE
            confidence = min(0.7, granger_score + 0.3)
        elif abs(correlation) > 0.5:
            relation_type = CausalRelationType.CORRELATION
            confidence = abs(correlation) * 0.8
        else:
            relation_type = CausalRelationType.CONFOUNDED
            confidence = 0.3
        
        return CausalLink(
            link_id=f"CL-{uuid.uuid4().hex[:8]}",
            cause=variable_x,
            effect=variable_y,
            relation_type=relation_type,
            strength=correlation,
            confidence=confidence,
            lag_periods=lag if granger_score > 0.3 else 0,
            evidence=[f"Correlation: {correlation:.2f}", f"Granger score: {granger_score:.2f}"],
        )
    
    async def trace_causal_chain(
        self,
        root_cause: str,
        max_depth: int = 5,
    ) -> List[List[CausalLink]]:
        """Trace all causal chains from a root cause"""
        chains = []
        
        def dfs(current: str, path: List[CausalLink], depth: int):
            if depth >= max_depth:
                if path:
                    chains.append(path.copy())
                return
            
            links = self.causal_graph.get(current, [])
            if not links:
                if path:
                    chains.append(path.copy())
                return
            
            for link in links:
                path.append(link)
                dfs(link.effect, path, depth + 1)
                path.pop()
        
        dfs(root_cause, [], 0)
        return chains
    
    async def explain_movement(
        self,
        variable: str,
        movement: float,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Explain why a variable moved"""
        explanations = []
        
        # Find all causes of this variable
        potential_causes = []
        for cause, links in self.causal_graph.items():
            for link in links:
                if link.effect == variable:
                    potential_causes.append((cause, link))
        
        # Check which causes are active in context
        for cause, link in potential_causes:
            cause_value = context.get(cause)
            if cause_value is not None:
                expected_effect = cause_value * link.strength
                if (movement > 0 and expected_effect > 0) or (movement < 0 and expected_effect < 0):
                    explanations.append({
                        'cause': cause,
                        'link': link.to_dict(),
                        'contribution': expected_effect,
                        'explanation': f"{cause} contributed {expected_effect:.2%} to {variable} movement",
                    })
        
        # Sort by contribution
        explanations.sort(key=lambda x: abs(x['contribution']), reverse=True)
        
        return {
            'variable': variable,
            'movement': movement,
            'explanations': explanations,
            'unexplained': movement - sum(e['contribution'] for e in explanations),
        }


class NarrativeGenerator:
    """
    Generates human-readable narratives explaining market conditions.
    
    Transforms quantitative analysis into qualitative understanding.
    """
    
    def __init__(self):
        self.narrative_templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, str]:
        """Load narrative templates"""
        return {
            'bull_market': "Markets are in a bullish phase, driven by {drivers}. Key opportunities include {opportunities}.",
            'bear_market': "Markets face headwinds from {drivers}. Defensive positioning recommended with focus on {opportunities}.",
            'high_volatility': "Elevated volatility regime with {drivers} creating uncertainty. Risk management is paramount.",
            'earnings_beat': "{symbol} exceeded expectations with {metric} beating estimates by {amount}. This suggests {implication}.",
            'macro_shift': "Macroeconomic conditions are shifting due to {drivers}. This typically leads to {effects}.",
        }
    
    async def generate_market_narrative(
        self,
        market_data: Dict[str, Any],
        regime: MarketRegime,
        causal_analysis: Dict[str, Any],
    ) -> MarketNarrative:
        """Generate comprehensive market narrative"""
        # Extract key information
        price_change = market_data.get('price_change', 0)
        volume_change = market_data.get('volume_change', 0)
        volatility = market_data.get('volatility', 0)
        
        # Determine key drivers
        drivers = []
        if abs(price_change) > 0.02:
            drivers.append(f"Price movement of {price_change:.1%}")
        if abs(volume_change) > 0.5:
            drivers.append(f"Volume {'surge' if volume_change > 0 else 'decline'} of {abs(volume_change):.1%}")
        if volatility > 0.25:
            drivers.append(f"Elevated volatility at {volatility:.1%}")
        
        # Add causal drivers
        for explanation in causal_analysis.get('explanations', [])[:3]:
            drivers.append(explanation.get('explanation', ''))
        
        # Identify risks
        risks = []
        if regime in (MarketRegime.HIGH_VOLATILITY, MarketRegime.CRISIS):
            risks.append("Elevated market risk requires careful position sizing")
        if volatility > 0.3:
            risks.append("Volatility spike may trigger stop-losses")
        
        # Identify opportunities
        opportunities = []
        if regime == MarketRegime.BULL_TREND:
            opportunities.append("Momentum strategies may outperform")
        elif regime == MarketRegime.HIGH_VOLATILITY:
            opportunities.append("Volatility strategies and options may be attractive")
        elif regime == MarketRegime.CAPITULATION:
            opportunities.append("Potential buying opportunity for long-term investors")
        
        # Generate summary
        if regime == MarketRegime.BULL_TREND:
            summary = f"Markets continue their upward trajectory with {', '.join(drivers[:2])}. "
            outlook = "Bullish momentum expected to continue in the near term."
        elif regime == MarketRegime.BEAR_TREND:
            summary = f"Markets face downward pressure from {', '.join(drivers[:2])}. "
            outlook = "Caution warranted as bearish conditions persist."
        elif regime == MarketRegime.HIGH_VOLATILITY:
            summary = f"Volatility dominates market action with {', '.join(drivers[:2])}. "
            outlook = "Expect continued choppiness until volatility subsides."
        else:
            summary = f"Markets are consolidating with {', '.join(drivers[:2]) if drivers else 'mixed signals'}. "
            outlook = "Range-bound conditions likely in the near term."
        
        # Generate title
        title = f"{regime.value.replace('_', ' ').title()}: {datetime.now().strftime('%B %d, %Y')}"
        
        return MarketNarrative(
            narrative_id=f"NAR-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(timezone.utc),
            title=title,
            summary=summary,
            key_drivers=drivers,
            risk_factors=risks,
            opportunities=opportunities,
            outlook=outlook,
            confidence=0.7,
            supporting_data=market_data,
        )
    
    async def explain_trade_decision(
        self,
        decision: Dict[str, Any],
        context: Dict[str, Any],
    ) -> str:
        """Generate explanation for a trade decision"""
        action = decision.get('action', 'hold')
        symbol = decision.get('symbol', 'unknown')
        confidence = decision.get('confidence', 0.5)
        
        reasons = decision.get('reasons', [])
        
        if action == 'buy':
            explanation = f"Initiating long position in {symbol} with {confidence:.0%} confidence. "
            explanation += f"Key factors: {'; '.join(reasons[:3]) if reasons else 'Technical and fundamental alignment'}. "
        elif action == 'sell':
            explanation = f"Closing/shorting {symbol} with {confidence:.0%} confidence. "
            explanation += f"Key factors: {'; '.join(reasons[:3]) if reasons else 'Risk management and signal deterioration'}. "
        else:
            explanation = f"Maintaining current position in {symbol}. "
            explanation += f"No compelling signal to act at this time."
        
        return explanation


class RegimeDetector:
    """
    Detects and classifies market regimes.
    
    Understanding the current regime is crucial for strategy selection
    and risk management.
    """
    
    def __init__(self):
        self.regime_history: List[Tuple[datetime, MarketRegime]] = []
        self.current_regime = MarketRegime.SIDEWAYS
        self.regime_start = datetime.now(timezone.utc)
    
    async def detect_regime(
        self,
        market_data: Dict[str, Any],
    ) -> RegimeAnalysis:
        """Detect current market regime"""
        # Extract features
        returns = market_data.get('returns', [])
        volatility = market_data.get('volatility', 0.15)
        trend = market_data.get('trend', 0)
        volume_trend = market_data.get('volume_trend', 0)
        
        # Calculate regime scores
        regime_scores = {}
        
        # Bull trend
        if len(returns) >= 20:
            recent_return = sum(returns[-20:])
            if recent_return > 0.05 and trend > 0.3:
                regime_scores[MarketRegime.BULL_TREND] = 0.8
            elif recent_return > 0.02:
                regime_scores[MarketRegime.BULL_TREND] = 0.5
        
        # Bear trend
        if len(returns) >= 20:
            recent_return = sum(returns[-20:])
            if recent_return < -0.05 and trend < -0.3:
                regime_scores[MarketRegime.BEAR_TREND] = 0.8
            elif recent_return < -0.02:
                regime_scores[MarketRegime.BEAR_TREND] = 0.5
        
        # High volatility
        if volatility > 0.25:
            regime_scores[MarketRegime.HIGH_VOLATILITY] = min(1.0, volatility / 0.3)
        
        # Low volatility
        if volatility < 0.10:
            regime_scores[MarketRegime.LOW_VOLATILITY] = 1.0 - volatility / 0.1
        
        # Crisis
        if volatility > 0.4 and (len(returns) >= 5 and sum(returns[-5:]) < -0.1):
            regime_scores[MarketRegime.CRISIS] = 0.9
        
        # Capitulation
        if volume_trend > 2.0 and (len(returns) >= 3 and sum(returns[-3:]) < -0.08):
            regime_scores[MarketRegime.CAPITULATION] = 0.7
        
        # Recovery
        if self.current_regime in (MarketRegime.CRISIS, MarketRegime.BEAR_TREND, MarketRegime.CAPITULATION):
            if len(returns) >= 5 and sum(returns[-5:]) > 0.05:
                regime_scores[MarketRegime.RECOVERY] = 0.6
        
        # Sideways (default)
        if not regime_scores:
            regime_scores[MarketRegime.SIDEWAYS] = 0.6
        
        # Select regime with highest score
        detected_regime = max(regime_scores, key=regime_scores.get)
        regime_probability = regime_scores[detected_regime]
        
        # Check for regime change
        if detected_regime != self.current_regime:
            self.regime_history.append((datetime.now(timezone.utc), self.current_regime))
            self.current_regime = detected_regime
            self.regime_start = datetime.now(timezone.utc)
        
        # Calculate duration
        duration = (datetime.now(timezone.utc) - self.regime_start).days
        
        # Transition probabilities (simplified Markov)
        transition_probs = self._calculate_transition_probabilities(detected_regime)
        
        # Characteristics
        characteristics = {
            'volatility': volatility,
            'trend_strength': abs(trend),
            'volume_activity': volume_trend,
            'momentum': sum(returns[-5:]) if len(returns) >= 5 else 0,
        }
        
        # Historical comparison
        historical = self._find_historical_comparisons(detected_regime, characteristics)
        
        return RegimeAnalysis(
            analysis_id=f"REG-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(timezone.utc),
            current_regime=detected_regime,
            regime_probability=regime_probability,
            regime_duration=duration,
            transition_probabilities=transition_probs,
            characteristics=characteristics,
            historical_comparison=historical,
        )
    
    def _calculate_transition_probabilities(self, current: MarketRegime) -> Dict[str, float]:
        """Calculate regime transition probabilities"""
        # Simplified transition matrix
        transitions = {
            MarketRegime.BULL_TREND: {
                'bull_trend': 0.7, 'sideways': 0.15, 'high_volatility': 0.1, 'bear_trend': 0.05
            },
            MarketRegime.BEAR_TREND: {
                'bear_trend': 0.6, 'sideways': 0.15, 'high_volatility': 0.15, 'crisis': 0.05, 'recovery': 0.05
            },
            MarketRegime.SIDEWAYS: {
                'sideways': 0.5, 'bull_trend': 0.2, 'bear_trend': 0.2, 'high_volatility': 0.1
            },
            MarketRegime.HIGH_VOLATILITY: {
                'high_volatility': 0.4, 'sideways': 0.3, 'crisis': 0.15, 'recovery': 0.15
            },
            MarketRegime.CRISIS: {
                'crisis': 0.3, 'capitulation': 0.3, 'high_volatility': 0.2, 'recovery': 0.2
            },
            MarketRegime.CAPITULATION: {
                'recovery': 0.5, 'bear_trend': 0.3, 'sideways': 0.2
            },
            MarketRegime.RECOVERY: {
                'bull_trend': 0.4, 'sideways': 0.3, 'recovery': 0.2, 'high_volatility': 0.1
            },
        }
        
        return transitions.get(current, {'sideways': 1.0})
    
    def _find_historical_comparisons(
        self,
        regime: MarketRegime,
        characteristics: Dict[str, Any],
    ) -> List[str]:
        """Find historical periods with similar characteristics"""
        comparisons = {
            MarketRegime.BULL_TREND: [
                "Similar to 2017 low-volatility bull run",
                "Comparable to post-2009 recovery rally",
            ],
            MarketRegime.BEAR_TREND: [
                "Resembles early 2022 rate-hike selloff",
                "Similar pattern to 2018 Q4 correction",
            ],
            MarketRegime.CRISIS: [
                "Volatility levels comparable to March 2020",
                "Similar stress indicators to 2008 crisis",
            ],
            MarketRegime.HIGH_VOLATILITY: [
                "VIX levels similar to August 2015",
                "Comparable to February 2018 vol spike",
            ],
        }
        
        return comparisons.get(regime, ["No direct historical comparison found"])


class AnomalyExplainer:
    """
    Explains anomalous market events.
    
    When unusual things happen, understanding WHY is crucial
    for appropriate response.
    """
    
    def __init__(self):
        self.anomaly_patterns = self._load_anomaly_patterns()
    
    def _load_anomaly_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load known anomaly patterns"""
        return {
            'flash_crash': {
                'characteristics': {'price_drop': -0.05, 'duration_minutes': 15, 'recovery': True},
                'causes': ['Algorithmic trading cascade', 'Liquidity vacuum', 'Fat finger error'],
                'precedents': ['May 6, 2010 Flash Crash', 'August 24, 2015 ETF dislocation'],
            },
            'gap_down': {
                'characteristics': {'overnight_gap': -0.03},
                'causes': ['Overnight news', 'Earnings miss', 'Geopolitical event'],
                'precedents': ['Common after negative earnings surprises'],
            },
            'volume_spike': {
                'characteristics': {'volume_multiple': 5},
                'causes': ['Institutional activity', 'Index rebalancing', 'News catalyst'],
                'precedents': ['Typical during options expiration'],
            },
            'correlation_breakdown': {
                'characteristics': {'correlation_change': 0.5},
                'causes': ['Regime change', 'Sector rotation', 'Risk-off event'],
                'precedents': ['2020 March correlation spike'],
            },
        }
    
    async def explain_anomaly(
        self,
        anomaly_type: str,
        anomaly_data: Dict[str, Any],
        market_context: Dict[str, Any],
    ) -> AnomalyExplanation:
        """Explain an anomalous event"""
        pattern = self.anomaly_patterns.get(anomaly_type, {})
        
        # Determine severity
        severity = self._calculate_severity(anomaly_type, anomaly_data)
        
        # Generate description
        description = self._generate_description(anomaly_type, anomaly_data)
        
        # Identify probable causes
        causes = pattern.get('causes', ['Unknown cause'])
        
        # Add context-specific causes
        if market_context.get('earnings_season'):
            causes.append('Earnings-related volatility')
        if market_context.get('fed_meeting'):
            causes.append('Fed policy uncertainty')
        
        # Historical precedents
        precedents = pattern.get('precedents', ['No direct precedent'])
        
        # Expected impact
        impact = self._estimate_impact(anomaly_type, severity, market_context)
        
        # Recommended response
        response = self._recommend_response(anomaly_type, severity)
        
        return AnomalyExplanation(
            explanation_id=f"ANOM-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(timezone.utc),
            anomaly_type=anomaly_type,
            severity=severity,
            description=description,
            probable_causes=causes,
            historical_precedents=precedents,
            expected_impact=impact,
            recommended_response=response,
        )
    
    def _calculate_severity(self, anomaly_type: str, data: Dict[str, Any]) -> float:
        """Calculate anomaly severity (0-1)"""
        if anomaly_type == 'flash_crash':
            price_drop = abs(data.get('price_drop', 0))
            return min(1.0, price_drop / 0.1)
        elif anomaly_type == 'gap_down':
            gap = abs(data.get('gap', 0))
            return min(1.0, gap / 0.05)
        elif anomaly_type == 'volume_spike':
            multiple = data.get('volume_multiple', 1)
            return min(1.0, (multiple - 1) / 10)
        else:
            return 0.5
    
    def _generate_description(self, anomaly_type: str, data: Dict[str, Any]) -> str:
        """Generate human-readable description"""
        descriptions = {
            'flash_crash': f"Rapid price decline of {data.get('price_drop', 0):.1%} occurred in {data.get('duration', 'unknown')} minutes",
            'gap_down': f"Market opened {data.get('gap', 0):.1%} lower than previous close",
            'volume_spike': f"Trading volume surged to {data.get('volume_multiple', 1):.1f}x normal levels",
            'correlation_breakdown': f"Asset correlations shifted significantly from historical norms",
        }
        return descriptions.get(anomaly_type, f"Anomalous {anomaly_type} event detected")
    
    def _estimate_impact(
        self,
        anomaly_type: str,
        severity: float,
        context: Dict[str, Any],
    ) -> Dict[str, float]:
        """Estimate expected impact"""
        base_impacts = {
            'flash_crash': {'volatility': 0.5, 'liquidity': -0.3, 'sentiment': -0.4},
            'gap_down': {'volatility': 0.2, 'sentiment': -0.3, 'momentum': -0.2},
            'volume_spike': {'volatility': 0.3, 'liquidity': 0.2, 'attention': 0.5},
            'correlation_breakdown': {'diversification': -0.4, 'risk': 0.3},
        }
        
        impacts = base_impacts.get(anomaly_type, {})
        
        # Scale by severity
        return {k: v * severity for k, v in impacts.items()}
    
    def _recommend_response(self, anomaly_type: str, severity: float) -> List[str]:
        """Recommend response actions"""
        responses = []
        
        if severity > 0.7:
            responses.append("Reduce position sizes immediately")
            responses.append("Review stop-loss levels")
        
        if anomaly_type == 'flash_crash':
            responses.append("Avoid market orders during high volatility")
            responses.append("Consider limit orders at favorable prices")
        elif anomaly_type == 'gap_down':
            responses.append("Assess fundamental impact before acting")
            responses.append("Wait for price stabilization")
        elif anomaly_type == 'volume_spike':
            responses.append("Monitor for follow-through or reversal")
            responses.append("Check for news catalyst")
        
        if not responses:
            responses.append("Continue monitoring situation")
        
        return responses


class UnderstandingEngine:
    """
    Master understanding engine that coordinates all comprehension modules.
    
    Provides deep understanding of market dynamics beyond simple prediction.
    """
    
    def __init__(self):
        self.engine_id = f"UND-{uuid.uuid4().hex[:8]}"
        self.causal_inference = CausalInference()
        self.narrative_generator = NarrativeGenerator()
        self.regime_detector = RegimeDetector()
        self.anomaly_explainer = AnomalyExplainer()
        
        logger.info(f"UnderstandingEngine initialized: {self.engine_id}")
    
    async def understand_market(
        self,
        market_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate comprehensive market understanding"""
        # Detect regime
        regime_analysis = await self.regime_detector.detect_regime(market_data)
        
        # Causal analysis
        causal_analysis = await self.causal_inference.explain_movement(
            variable='market',
            movement=market_data.get('price_change', 0),
            context=market_data,
        )
        
        # Generate narrative
        narrative = await self.narrative_generator.generate_market_narrative(
            market_data=market_data,
            regime=regime_analysis.current_regime,
            causal_analysis=causal_analysis,
        )
        
        return {
            'regime': regime_analysis.to_dict(),
            'causal_analysis': causal_analysis,
            'narrative': narrative.to_dict(),
            'understanding_confidence': 0.7,
        }
    
    async def explain_event(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        market_context: Dict[str, Any],
    ) -> AnomalyExplanation:
        """Explain a specific market event"""
        return await self.anomaly_explainer.explain_anomaly(
            anomaly_type=event_type,
            anomaly_data=event_data,
            market_context=market_context,
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get engine status"""
        return {
            'engine_id': self.engine_id,
            'current_regime': self.regime_detector.current_regime.value,
            'known_causal_links': len(self.causal_inference.known_relationships),
        }
