"""
AAMIS v3.0 - Advanced Analysis Tools

This module implements:
1. Chaos-Resistant Signal Engine
2. Market Emotional Radar
3. Order Flow & Market Microstructure (enhanced)
4. Multi-Timescale Thinking (enhanced)
5. Dimensional State Awareness
6. Dimensional Anomaly Detection
7. Probability Collapsing
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
import random
from collections import deque

logger = logging.getLogger(__name__)


class ChaosLevel(Enum):
    """Market chaos levels"""
    ORDERLY = "ORDERLY"
    MILD_CHAOS = "MILD_CHAOS"
    MODERATE_CHAOS = "MODERATE_CHAOS"
    HIGH_CHAOS = "HIGH_CHAOS"
    EXTREME_CHAOS = "EXTREME_CHAOS"


class Dimension(Enum):
    """Market dimensions"""
    PRICE = "PRICE"
    VOLUME = "VOLUME"
    TIME = "TIME"
    VOLATILITY = "VOLATILITY"
    SENTIMENT = "SENTIMENT"
    LIQUIDITY = "LIQUIDITY"
    CORRELATION = "CORRELATION"


class Timeframe(Enum):
    """Analysis timeframes"""
    TICK = "TICK"
    SECOND = "SECOND"
    MINUTE = "MINUTE"
    HOUR = "HOUR"
    DAY = "DAY"
    WEEK = "WEEK"
    MONTH = "MONTH"


@dataclass
class ChaosResistantSignal:
    """Signal that survives chaos"""
    signal_id: str
    direction: str
    strength: float
    chaos_resistance: float  # 0-1, how well it survives chaos
    confidence: float
    timeframe: Timeframe
    filters_passed: List[str] = field(default_factory=list)
    chaos_level_tested: ChaosLevel = ChaosLevel.ORDERLY


@dataclass
class EmotionalRadarReading:
    """Emotional radar reading"""
    timestamp: datetime
    fear_level: float
    greed_level: float
    uncertainty_level: float
    momentum_sentiment: float
    contrarian_signal: float
    radar_strength: float


@dataclass
class MicrostructureAnalysis:
    """Market microstructure analysis"""
    timestamp: datetime
    bid_ask_spread: float
    order_imbalance: float
    trade_intensity: float
    price_impact: float
    informed_trading_probability: float
    liquidity_score: float


@dataclass
class DimensionalState:
    """State across multiple dimensions"""
    timestamp: datetime
    dimensions: Dict[Dimension, float]
    anomaly_scores: Dict[Dimension, float]
    overall_state: str
    stability: float


@dataclass
class ProbabilityCollapse:
    """Collapsed probability distribution"""
    timestamp: datetime
    most_likely_outcome: str
    probability: float
    alternative_outcomes: List[Tuple[str, float]]
    entropy: float
    confidence: float


class ChaosResistantSignalEngine:
    """
    Chaos-Resistant Signal Engine
    Generates signals that survive market chaos
    """
    
    def __init__(self):
        self.signal_history: List[ChaosResistantSignal] = []
        self.chaos_filters = self._initialize_filters()
        
    def _initialize_filters(self) -> Dict[str, callable]:
        """Initialize chaos filters"""
        return {
            'volatility_filter': self._volatility_filter,
            'volume_filter': self._volume_filter,
            'trend_filter': self._trend_filter,
            'momentum_filter': self._momentum_filter,
            'correlation_filter': self._correlation_filter,
            'liquidity_filter': self._liquidity_filter
        }
    
    def generate_signal(self, market_data: Dict, chaos_level: ChaosLevel) -> ChaosResistantSignal:
        """Generate chaos-resistant signal"""
        # Base signal from market data
        trend = market_data.get('trend', 0)
        momentum = market_data.get('momentum', 0)
        
        if trend > 0.01 and momentum > 0:
            direction = 'BUY'
            base_strength = (trend + momentum) / 2
        elif trend < -0.01 and momentum < 0:
            direction = 'SELL'
            base_strength = abs((trend + momentum) / 2)
        else:
            direction = 'HOLD'
            base_strength = 0.3
        
        # Apply chaos filters
        filters_passed = []
        chaos_resistance = 1.0
        
        for filter_name, filter_func in self.chaos_filters.items():
            passed, resistance_impact = filter_func(market_data, chaos_level)
            if passed:
                filters_passed.append(filter_name)
            chaos_resistance *= resistance_impact
        
        # Adjust strength based on chaos level
        chaos_multipliers = {
            ChaosLevel.ORDERLY: 1.0,
            ChaosLevel.MILD_CHAOS: 0.9,
            ChaosLevel.MODERATE_CHAOS: 0.7,
            ChaosLevel.HIGH_CHAOS: 0.5,
            ChaosLevel.EXTREME_CHAOS: 0.3
        }
        
        adjusted_strength = base_strength * chaos_multipliers.get(chaos_level, 0.5)
        
        # Calculate confidence
        confidence = (len(filters_passed) / len(self.chaos_filters)) * chaos_resistance
        
        signal = ChaosResistantSignal(
            signal_id=f"CHAOS_SIG_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            direction=direction,
            strength=adjusted_strength,
            chaos_resistance=chaos_resistance,
            confidence=confidence,
            timeframe=self._determine_timeframe(market_data),
            filters_passed=filters_passed,
            chaos_level_tested=chaos_level
        )
        
        self.signal_history.append(signal)
        
        logger.info(f"🌪️ Chaos-Resistant Signal: {direction} (resistance: {chaos_resistance:.2f})")
        
        return signal
    
    def _volatility_filter(self, market_data: Dict, chaos_level: ChaosLevel) -> Tuple[bool, float]:
        """Volatility-based filter"""
        volatility = market_data.get('volatility', 0.15)
        
        # Higher volatility = lower resistance
        if volatility < 0.15:
            return True, 1.0
        elif volatility < 0.25:
            return True, 0.8
        elif volatility < 0.35:
            return False, 0.6
        else:
            return False, 0.4
    
    def _volume_filter(self, market_data: Dict, chaos_level: ChaosLevel) -> Tuple[bool, float]:
        """Volume-based filter"""
        volume_ratio = market_data.get('volume_ratio', 1.0)
        
        # Need sufficient volume
        if volume_ratio > 1.5:
            return True, 1.0
        elif volume_ratio > 1.0:
            return True, 0.9
        elif volume_ratio > 0.5:
            return False, 0.7
        else:
            return False, 0.5
    
    def _trend_filter(self, market_data: Dict, chaos_level: ChaosLevel) -> Tuple[bool, float]:
        """Trend confirmation filter"""
        trend = abs(market_data.get('trend', 0))
        
        if trend > 0.02:
            return True, 1.0
        elif trend > 0.01:
            return True, 0.85
        else:
            return False, 0.7
    
    def _momentum_filter(self, market_data: Dict, chaos_level: ChaosLevel) -> Tuple[bool, float]:
        """Momentum filter"""
        momentum = market_data.get('momentum', 0)
        trend = market_data.get('trend', 0)
        
        # Momentum should align with trend
        if momentum * trend > 0:
            return True, 1.0
        else:
            return False, 0.6
    
    def _correlation_filter(self, market_data: Dict, chaos_level: ChaosLevel) -> Tuple[bool, float]:
        """Correlation stability filter"""
        correlation = market_data.get('correlation', 0.5)
        
        # Stable correlations are better
        if abs(correlation) > 0.7:
            return True, 0.9
        elif abs(correlation) > 0.5:
            return True, 0.8
        else:
            return False, 0.7
    
    def _liquidity_filter(self, market_data: Dict, chaos_level: ChaosLevel) -> Tuple[bool, float]:
        """Liquidity filter"""
        spread = market_data.get('spread', 0.0001)
        
        if spread < 0.0001:
            return True, 1.0
        elif spread < 0.0003:
            return True, 0.9
        else:
            return False, 0.7
    
    def _determine_timeframe(self, market_data: Dict) -> Timeframe:
        """Determine appropriate timeframe"""
        volatility = market_data.get('volatility', 0.15)
        
        if volatility > 0.30:
            return Timeframe.MINUTE
        elif volatility > 0.20:
            return Timeframe.HOUR
        else:
            return Timeframe.DAY


class MarketEmotionalRadar:
    """
    Market Emotional Radar
    Scans market for emotional signals
    """
    
    def __init__(self):
        self.readings: deque = deque(maxlen=500)
        
    def scan(self, market_data: Dict, sentiment_data: Dict = None) -> EmotionalRadarReading:
        """Scan market emotions"""
        # Calculate fear level
        vix = market_data.get('vix', 20)
        volatility = market_data.get('volatility', 0.15)
        fear_level = self._calculate_fear(vix, volatility)
        
        # Calculate greed level
        price_change = market_data.get('price_change', 0)
        volume_ratio = market_data.get('volume_ratio', 1)
        greed_level = self._calculate_greed(price_change, volume_ratio)
        
        # Calculate uncertainty
        uncertainty_level = self._calculate_uncertainty(market_data)
        
        # Momentum sentiment
        momentum_sentiment = self._calculate_momentum_sentiment(market_data)
        
        # Contrarian signal
        contrarian_signal = self._calculate_contrarian(fear_level, greed_level)
        
        # Radar strength (signal quality)
        radar_strength = self._calculate_radar_strength(market_data)
        
        reading = EmotionalRadarReading(
            timestamp=datetime.now(),
            fear_level=fear_level,
            greed_level=greed_level,
            uncertainty_level=uncertainty_level,
            momentum_sentiment=momentum_sentiment,
            contrarian_signal=contrarian_signal,
            radar_strength=radar_strength
        )
        
        self.readings.append(reading)
        
        logger.info(f"📡 Emotional Radar: Fear={fear_level:.2f}, Greed={greed_level:.2f}")
        
        return reading
    
    def _calculate_fear(self, vix: float, volatility: float) -> float:
        """Calculate fear level"""
        vix_component = min(1, vix / 50)
        vol_component = min(1, volatility / 0.40)
        return (vix_component + vol_component) / 2
    
    def _calculate_greed(self, price_change: float, volume_ratio: float) -> float:
        """Calculate greed level"""
        if price_change > 0:
            price_component = min(1, price_change / 0.05)
            volume_component = min(1, volume_ratio / 3)
            return (price_component + volume_component) / 2
        return 0.2
    
    def _calculate_uncertainty(self, market_data: Dict) -> float:
        """Calculate uncertainty level"""
        volatility = market_data.get('volatility', 0.15)
        spread = market_data.get('spread', 0.0001)
        
        vol_uncertainty = min(1, volatility / 0.30)
        spread_uncertainty = min(1, spread / 0.001)
        
        return (vol_uncertainty + spread_uncertainty) / 2
    
    def _calculate_momentum_sentiment(self, market_data: Dict) -> float:
        """Calculate momentum sentiment (-1 to 1)"""
        trend = market_data.get('trend', 0)
        momentum = market_data.get('momentum', 0)
        
        return max(-1, min(1, (trend + momentum) * 10))
    
    def _calculate_contrarian(self, fear: float, greed: float) -> float:
        """Calculate contrarian signal"""
        # Extreme fear = buy signal, extreme greed = sell signal
        if fear > 0.8:
            return 0.8  # Strong buy
        elif greed > 0.8:
            return -0.8  # Strong sell
        else:
            return 0.0  # Neutral
    
    def _calculate_radar_strength(self, market_data: Dict) -> float:
        """Calculate radar signal strength"""
        volume_ratio = market_data.get('volume_ratio', 1)
        return min(1, volume_ratio / 2)


class EnhancedMicrostructureAnalyzer:
    """
    Enhanced Order Flow & Market Microstructure Analysis
    """
    
    def __init__(self):
        self.analysis_history: List[MicrostructureAnalysis] = []
        
    def analyze(self, market_data: Dict, order_book: Dict = None) -> MicrostructureAnalysis:
        """Analyze market microstructure"""
        # Bid-ask spread
        bid = market_data.get('bid', 1.0)
        ask = market_data.get('ask', 1.0)
        spread = (ask - bid) / bid if bid > 0 else 0
        
        # Order imbalance
        if order_book:
            bid_volume = sum(order_book.get('bids', [0]))
            ask_volume = sum(order_book.get('asks', [0]))
            total_volume = bid_volume + ask_volume
            imbalance = (bid_volume - ask_volume) / total_volume if total_volume > 0 else 0
        else:
            imbalance = market_data.get('order_imbalance', 0)
        
        # Trade intensity
        volume = market_data.get('volume', 1000)
        avg_volume = market_data.get('avg_volume', 1000)
        trade_intensity = volume / avg_volume if avg_volume > 0 else 1
        
        # Price impact estimation
        price_impact = self._estimate_price_impact(market_data)
        
        # Informed trading probability (PIN model simplified)
        informed_prob = self._estimate_informed_trading(market_data, imbalance)
        
        # Liquidity score
        liquidity_score = self._calculate_liquidity_score(spread, trade_intensity)
        
        analysis = MicrostructureAnalysis(
            timestamp=datetime.now(),
            bid_ask_spread=spread,
            order_imbalance=imbalance,
            trade_intensity=trade_intensity,
            price_impact=price_impact,
            informed_trading_probability=informed_prob,
            liquidity_score=liquidity_score
        )
        
        self.analysis_history.append(analysis)
        
        logger.info(f"🔬 Microstructure: Spread={spread:.5f}, Imbalance={imbalance:.2f}, Liquidity={liquidity_score:.2f}")
        
        return analysis
    
    def _estimate_price_impact(self, market_data: Dict) -> float:
        """Estimate price impact of trades"""
        volatility = market_data.get('volatility', 0.15)
        volume_ratio = market_data.get('volume_ratio', 1)
        
        # Kyle's lambda approximation
        return volatility * np.sqrt(volume_ratio) * 0.1
    
    def _estimate_informed_trading(self, market_data: Dict, imbalance: float) -> float:
        """Estimate probability of informed trading"""
        # High imbalance + high volume = likely informed trading
        volume_ratio = market_data.get('volume_ratio', 1)
        
        imbalance_component = abs(imbalance)
        volume_component = min(1, volume_ratio / 3)
        
        return (imbalance_component + volume_component) / 2
    
    def _calculate_liquidity_score(self, spread: float, intensity: float) -> float:
        """Calculate liquidity score"""
        spread_score = 1 - min(1, spread / 0.001)
        intensity_score = min(1, intensity / 2)
        
        return (spread_score + intensity_score) / 2


class MultiTimescaleAnalyzer:
    """
    Multi-Timescale Thinking
    Analyzes across multiple timeframes simultaneously
    """
    
    def __init__(self):
        self.timeframe_data: Dict[Timeframe, deque] = {
            tf: deque(maxlen=100) for tf in Timeframe
        }
        
    def analyze_all_timeframes(self, market_data: Dict) -> Dict[Timeframe, Dict]:
        """Analyze across all timeframes"""
        results = {}
        
        for timeframe in [Timeframe.MINUTE, Timeframe.HOUR, Timeframe.DAY, Timeframe.WEEK]:
            analysis = self._analyze_timeframe(timeframe, market_data)
            results[timeframe] = analysis
            self.timeframe_data[timeframe].append(analysis)
        
        # Calculate alignment
        alignment = self._calculate_alignment(results)
        
        results['alignment'] = alignment
        results['dominant_timeframe'] = self._find_dominant_timeframe(results)
        
        logger.info(f"⏰ Multi-Timeframe: Alignment={alignment:.2f}")
        
        return results
    
    def _analyze_timeframe(self, timeframe: Timeframe, market_data: Dict) -> Dict:
        """Analyze single timeframe"""
        # Simulate different timeframe perspectives
        multipliers = {
            Timeframe.MINUTE: 0.1,
            Timeframe.HOUR: 0.5,
            Timeframe.DAY: 1.0,
            Timeframe.WEEK: 2.0
        }
        
        mult = multipliers.get(timeframe, 1.0)
        
        trend = market_data.get('trend', 0) * mult
        momentum = market_data.get('momentum', 0) * mult
        volatility = market_data.get('volatility', 0.15) / mult
        
        # Determine bias
        if trend > 0.01:
            bias = 'BULLISH'
        elif trend < -0.01:
            bias = 'BEARISH'
        else:
            bias = 'NEUTRAL'
        
        return {
            'timeframe': timeframe.value,
            'trend': trend,
            'momentum': momentum,
            'volatility': volatility,
            'bias': bias,
            'strength': abs(trend) + abs(momentum)
        }
    
    def _calculate_alignment(self, results: Dict) -> float:
        """Calculate timeframe alignment"""
        biases = [r['bias'] for tf, r in results.items() if isinstance(tf, Timeframe)]
        
        if not biases:
            return 0.5
        
        # Count most common bias
        from collections import Counter
        bias_counts = Counter(biases)
        most_common = bias_counts.most_common(1)[0][1]
        
        return most_common / len(biases)
    
    def _find_dominant_timeframe(self, results: Dict) -> Timeframe:
        """Find the dominant timeframe"""
        max_strength = 0
        dominant = Timeframe.DAY
        
        for tf, analysis in results.items():
            if isinstance(tf, Timeframe):
                if analysis['strength'] > max_strength:
                    max_strength = analysis['strength']
                    dominant = tf
        
        return dominant


class DimensionalStateAnalyzer:
    """
    Dimensional State Awareness
    Tracks market state across multiple dimensions
    """
    
    def __init__(self):
        self.state_history: List[DimensionalState] = []
        
    def analyze_dimensions(self, market_data: Dict) -> DimensionalState:
        """Analyze all market dimensions"""
        dimensions = {}
        anomaly_scores = {}
        
        # Price dimension
        dimensions[Dimension.PRICE] = self._normalize(market_data.get('price_change', 0), -0.05, 0.05)
        anomaly_scores[Dimension.PRICE] = self._calculate_anomaly(dimensions[Dimension.PRICE])
        
        # Volume dimension
        dimensions[Dimension.VOLUME] = self._normalize(market_data.get('volume_ratio', 1), 0.5, 2.0)
        anomaly_scores[Dimension.VOLUME] = self._calculate_anomaly(dimensions[Dimension.VOLUME])
        
        # Volatility dimension
        dimensions[Dimension.VOLATILITY] = self._normalize(market_data.get('volatility', 0.15), 0.05, 0.40)
        anomaly_scores[Dimension.VOLATILITY] = self._calculate_anomaly(dimensions[Dimension.VOLATILITY])
        
        # Sentiment dimension
        dimensions[Dimension.SENTIMENT] = market_data.get('sentiment', 0.5)
        anomaly_scores[Dimension.SENTIMENT] = self._calculate_anomaly(dimensions[Dimension.SENTIMENT])
        
        # Liquidity dimension
        spread = market_data.get('spread', 0.0001)
        dimensions[Dimension.LIQUIDITY] = 1 - self._normalize(spread, 0, 0.001)
        anomaly_scores[Dimension.LIQUIDITY] = self._calculate_anomaly(dimensions[Dimension.LIQUIDITY])
        
        # Correlation dimension
        dimensions[Dimension.CORRELATION] = abs(market_data.get('correlation', 0.5))
        anomaly_scores[Dimension.CORRELATION] = self._calculate_anomaly(dimensions[Dimension.CORRELATION])
        
        # Overall state
        avg_value = np.mean(list(dimensions.values()))
        if avg_value > 0.6:
            overall_state = 'BULLISH'
        elif avg_value < 0.4:
            overall_state = 'BEARISH'
        else:
            overall_state = 'NEUTRAL'
        
        # Stability (inverse of anomaly)
        avg_anomaly = np.mean(list(anomaly_scores.values()))
        stability = 1 - avg_anomaly
        
        state = DimensionalState(
            timestamp=datetime.now(),
            dimensions=dimensions,
            anomaly_scores=anomaly_scores,
            overall_state=overall_state,
            stability=stability
        )
        
        self.state_history.append(state)
        
        logger.info(f"📊 Dimensional State: {overall_state} (stability: {stability:.2f})")
        
        return state
    
    def _normalize(self, value: float, min_val: float, max_val: float) -> float:
        """Normalize to 0-1"""
        return max(0, min(1, (value - min_val) / (max_val - min_val)))
    
    def _calculate_anomaly(self, value: float) -> float:
        """Calculate anomaly score (distance from 0.5)"""
        return abs(value - 0.5) * 2


class DimensionalAnomalyDetector:
    """
    Dimensional Anomaly Detection
    Detects anomalies across market dimensions
    """
    
    def __init__(self):
        self.anomaly_history: List[Dict] = []
        self.baseline: Dict[Dimension, Dict] = {}
        
    def detect_anomalies(self, dimensional_state: DimensionalState) -> List[Dict]:
        """Detect anomalies in dimensional state"""
        anomalies = []
        
        for dimension, value in dimensional_state.dimensions.items():
            anomaly_score = dimensional_state.anomaly_scores.get(dimension, 0)
            
            if anomaly_score > 0.7:  # High anomaly threshold
                anomaly = {
                    'dimension': dimension.value,
                    'value': value,
                    'anomaly_score': anomaly_score,
                    'severity': 'HIGH' if anomaly_score > 0.85 else 'MODERATE',
                    'timestamp': datetime.now()
                }
                anomalies.append(anomaly)
                
                logger.warning(f"⚠️ Anomaly in {dimension.value}: score={anomaly_score:.2f}")
        
        self.anomaly_history.extend(anomalies)
        
        return anomalies
    
    def get_anomaly_summary(self) -> Dict:
        """Get summary of recent anomalies"""
        if not self.anomaly_history:
            return {'total': 0, 'by_dimension': {}}
        
        recent = self.anomaly_history[-50:]
        
        by_dimension = {}
        for anomaly in recent:
            dim = anomaly['dimension']
            by_dimension[dim] = by_dimension.get(dim, 0) + 1
        
        return {
            'total': len(recent),
            'by_dimension': by_dimension,
            'most_anomalous': max(by_dimension.items(), key=lambda x: x[1])[0] if by_dimension else None
        }


class ProbabilityCollapser:
    """
    Probability Collapsing
    Collapses probability distributions to actionable decisions
    """
    
    def __init__(self):
        self.collapse_history: List[ProbabilityCollapse] = []
        
    def collapse_probabilities(self, scenarios: List[Dict]) -> ProbabilityCollapse:
        """Collapse probability distribution"""
        if not scenarios:
            return ProbabilityCollapse(
                timestamp=datetime.now(),
                most_likely_outcome='UNKNOWN',
                probability=0.5,
                alternative_outcomes=[],
                entropy=1.0,
                confidence=0.0
            )
        
        # Normalize probabilities
        total_prob = sum(s.get('probability', 0) for s in scenarios)
        if total_prob > 0:
            for s in scenarios:
                s['probability'] = s.get('probability', 0) / total_prob
        
        # Sort by probability
        sorted_scenarios = sorted(scenarios, key=lambda x: x.get('probability', 0), reverse=True)
        
        # Most likely outcome
        most_likely = sorted_scenarios[0]
        
        # Alternative outcomes
        alternatives = [(s['outcome'], s['probability']) for s in sorted_scenarios[1:4]]
        
        # Calculate entropy
        entropy = self._calculate_entropy([s['probability'] for s in scenarios])
        
        # Confidence (inverse of entropy, normalized)
        confidence = 1 - min(1, entropy / 2)
        
        collapse = ProbabilityCollapse(
            timestamp=datetime.now(),
            most_likely_outcome=most_likely.get('outcome', 'UNKNOWN'),
            probability=most_likely.get('probability', 0),
            alternative_outcomes=alternatives,
            entropy=entropy,
            confidence=confidence
        )
        
        self.collapse_history.append(collapse)
        
        logger.info(f"🎲 Probability Collapsed: {collapse.most_likely_outcome} ({collapse.probability:.2%})")
        
        return collapse
    
    def _calculate_entropy(self, probabilities: List[float]) -> float:
        """Calculate Shannon entropy"""
        entropy = 0
        for p in probabilities:
            if p > 0:
                entropy -= p * np.log2(p)
        return entropy
    
    def generate_scenarios(self, market_data: Dict) -> List[Dict]:
        """Generate probability scenarios"""
        scenarios = []
        
        trend = market_data.get('trend', 0)
        volatility = market_data.get('volatility', 0.15)
        
        # Bullish scenario
        bullish_prob = 0.3 + trend * 5 + (0.5 - volatility)
        scenarios.append({
            'outcome': 'BULLISH',
            'probability': max(0.1, min(0.6, bullish_prob)),
            'description': 'Price increases significantly'
        })
        
        # Bearish scenario
        bearish_prob = 0.3 - trend * 5 + (0.5 - volatility)
        scenarios.append({
            'outcome': 'BEARISH',
            'probability': max(0.1, min(0.6, bearish_prob)),
            'description': 'Price decreases significantly'
        })
        
        # Neutral scenario
        neutral_prob = 0.4 - volatility
        scenarios.append({
            'outcome': 'NEUTRAL',
            'probability': max(0.1, min(0.5, neutral_prob)),
            'description': 'Price remains range-bound'
        })
        
        # Volatile scenario
        volatile_prob = volatility * 2
        scenarios.append({
            'outcome': 'VOLATILE',
            'probability': max(0.05, min(0.4, volatile_prob)),
            'description': 'High volatility with unclear direction'
        })
        
        return scenarios


class AdvancedAnalysisSystem:
    """
    Complete Advanced Analysis System
    Integrates all analysis components
    """
    
    def __init__(self):
        self.chaos_engine = ChaosResistantSignalEngine()
        self.emotional_radar = MarketEmotionalRadar()
        self.microstructure = EnhancedMicrostructureAnalyzer()
        self.multitimescale = MultiTimescaleAnalyzer()
        self.dimensional = DimensionalStateAnalyzer()
        self.anomaly_detector = DimensionalAnomalyDetector()
        self.probability_collapser = ProbabilityCollapser()
        
    def comprehensive_analysis(self, market_data: Dict, chaos_level: ChaosLevel = ChaosLevel.MODERATE_CHAOS) -> Dict:
        """Run comprehensive analysis"""
        logger.info("🔬 Running comprehensive advanced analysis...")
        
        analysis = {
            'timestamp': datetime.now()
        }
        
        # 1. Chaos-resistant signal
        analysis['chaos_signal'] = self.chaos_engine.generate_signal(market_data, chaos_level)
        
        # 2. Emotional radar
        analysis['emotional_radar'] = self.emotional_radar.scan(market_data)
        
        # 3. Microstructure
        analysis['microstructure'] = self.microstructure.analyze(market_data)
        
        # 4. Multi-timescale
        analysis['multitimescale'] = self.multitimescale.analyze_all_timeframes(market_data)
        
        # 5. Dimensional state
        analysis['dimensional_state'] = self.dimensional.analyze_dimensions(market_data)
        
        # 6. Anomaly detection
        analysis['anomalies'] = self.anomaly_detector.detect_anomalies(analysis['dimensional_state'])
        
        # 7. Probability collapse
        scenarios = self.probability_collapser.generate_scenarios(market_data)
        analysis['probability_collapse'] = self.probability_collapser.collapse_probabilities(scenarios)
        
        # Overall recommendation
        analysis['recommendation'] = self._generate_recommendation(analysis)
        
        logger.info(f"🔬 Analysis complete: {analysis['recommendation']['action']}")
        
        return analysis
    
    def _generate_recommendation(self, analysis: Dict) -> Dict:
        """Generate overall recommendation"""
        signals = []
        
        # Chaos signal
        chaos_signal = analysis.get('chaos_signal')
        if chaos_signal and chaos_signal.confidence > 0.6:
            signals.append((chaos_signal.direction, chaos_signal.confidence))
        
        # Emotional radar
        radar = analysis.get('emotional_radar')
        if radar and radar.contrarian_signal != 0:
            direction = 'BUY' if radar.contrarian_signal > 0 else 'SELL'
            signals.append((direction, abs(radar.contrarian_signal)))
        
        # Probability collapse
        prob = analysis.get('probability_collapse')
        if prob and prob.confidence > 0.5:
            if prob.most_likely_outcome == 'BULLISH':
                signals.append(('BUY', prob.confidence))
            elif prob.most_likely_outcome == 'BEARISH':
                signals.append(('SELL', prob.confidence))
        
        # Aggregate signals
        if not signals:
            return {'action': 'HOLD', 'confidence': 0.5, 'reasoning': 'No clear signals'}
        
        buy_weight = sum(c for d, c in signals if d == 'BUY')
        sell_weight = sum(c for d, c in signals if d == 'SELL')
        
        if buy_weight > sell_weight * 1.2:
            action = 'BUY'
            confidence = buy_weight / (buy_weight + sell_weight)
        elif sell_weight > buy_weight * 1.2:
            action = 'SELL'
            confidence = sell_weight / (buy_weight + sell_weight)
        else:
            action = 'HOLD'
            confidence = 0.5
        
        return {
            'action': action,
            'confidence': confidence,
            'signals_count': len(signals),
            'reasoning': f'{len(signals)} signals analyzed'
        }


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create analysis system
    analysis_system = AdvancedAnalysisSystem()
    
    # Sample market data
    market_data = {
        'price_change': 0.015,
        'trend': 0.02,
        'momentum': 0.01,
        'volatility': 0.18,
        'volume_ratio': 1.3,
        'vix': 22,
        'sentiment': 0.6,
        'spread': 0.00015,
        'bid': 1.0999,
        'ask': 1.1001,
        'correlation': 0.65
    }
    
    # Run analysis
    result = analysis_system.comprehensive_analysis(market_data, ChaosLevel.MODERATE_CHAOS)
    
    print("\n" + "="*80)
    logger.info("ADVANCED ANALYSIS REPORT")
    print("="*80)
    logger.info(f"Chaos Signal: {result['chaos_signal'].direction} (resistance: {result['chaos_signal'].chaos_resistance:.2f})")
    logger.info(f"Emotional Radar: Fear={result['emotional_radar'].fear_level:.2f}, Greed={result['emotional_radar'].greed_level:.2f}")
    logger.info(f"Microstructure: Liquidity={result['microstructure'].liquidity_score:.2f}")
    logger.info(f"Timeframe Alignment: {result['multitimescale']['alignment']:.2f}")
    logger.info(f"Dimensional State: {result['dimensional_state'].overall_state} (stability: {result['dimensional_state'].stability:.2f})")
    logger.info(f"Anomalies: {len(result['anomalies'])}")
    logger.info(f"Most Likely Outcome: {result['probability_collapse'].most_likely_outcome} ({result['probability_collapse'].probability:.2%})")
    logger.info(f"\nRecommendation: {result['recommendation']['action']} (confidence: {result['recommendation']['confidence']:.2%})")
    print("="*80)
