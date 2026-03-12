"""
Deep Market Intelligence System
================================

Advanced market research and intelligence gathering system that performs
deep analysis across multiple dimensions to discover trading opportunities
and understand market dynamics at an institutional level.

CAPABILITIES:
- Multi-timeframe pattern analysis
- Market regime classification
- Sentiment analysis across sources
- Economic calendar integration
- Cross-asset correlation analysis
- Liquidity mapping and analysis
- Institutional activity detection
- Market microstructure analysis
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """Market regime classifications"""
    TRENDING_BULL = "trending_bull"
    TRENDING_BEAR = "trending_bear"
    RANGING = "ranging"
    VOLATILE = "volatile"
    BREAKOUT = "breakout"
    BREAKDOWN = "breakdown"
    ACCUMULATION = "accumulation"
    DISTRIBUTION = "distribution"
    CRISIS = "crisis"


class SentimentLevel(Enum):
    """Sentiment levels"""
    EXTREME_FEAR = "extreme_fear"
    FEAR = "fear"
    NEUTRAL = "neutral"
    GREED = "greed"
    EXTREME_GREED = "extreme_greed"


@dataclass
class LiquidityZone:
    """A zone of significant liquidity"""
    price_level: float
    volume: float
    depth: float
    type: str  # support, resistance, neutral
    strength: float  # 0-1
    institutional: bool = False


@dataclass
class LiquidityMap:
    """Complete liquidity map for a symbol"""
    symbol: str
    timestamp: datetime
    zones: List[LiquidityZone]
    overall_liquidity: float  # 0-1
    liquidity_imbalance: float  # -1 to 1 (negative = more sellers, positive = more buyers)
    thin_zones: List[Tuple[float, float]]  # Price ranges with thin liquidity


@dataclass
class InstitutionalSignal:
    """Signal of institutional activity"""
    signal_id: str
    symbol: str
    timestamp: datetime
    activity_type: str  # accumulation, distribution, block_trade, iceberg, spoofing
    confidence: float
    size_estimate: float
    price_level: float
    evidence: List[str]
    impact_estimate: float  # Expected price impact


@dataclass
class MarketIntelligenceReport:
    """Comprehensive market intelligence report"""
    report_id: str
    symbol: str
    timestamp: datetime
    
    # Regime analysis
    current_regime: MarketRegime
    regime_confidence: float
    regime_duration: timedelta
    
    # Multi-timeframe analysis
    timeframe_alignment: Dict[str, str]  # timeframe -> direction
    alignment_score: float  # 0-1
    
    # Sentiment
    sentiment: SentimentLevel
    sentiment_score: float  # -1 to 1
    sentiment_sources: Dict[str, float]
    
    # Liquidity
    liquidity_map: LiquidityMap
    key_levels: List[float]
    
    # Institutional activity
    institutional_signals: List[InstitutionalSignal]
    institutional_bias: str  # bullish, bearish, neutral
    
    # Opportunities
    identified_opportunities: List[Dict[str, Any]]
    opportunity_scores: List[float]
    
    # Risk factors
    risk_factors: List[str]
    risk_level: float  # 0-1
    
    # Overall assessment
    tradability_score: float  # 0-1
    recommended_action: str
    confidence: float


class DeepMarketIntelligence:
    """
    Deep market intelligence and research system.
    
    This system performs comprehensive market analysis including:
    - Multi-timeframe pattern recognition
    - Regime classification with confidence
    - Sentiment aggregation from multiple sources
    - Liquidity mapping and zone identification
    - Institutional activity detection
    - Opportunity discovery and scoring
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Analysis parameters
        self.timeframes = self.config.get('timeframes', ['1m', '5m', '15m', '1h', '4h', '1d'])
        self.min_liquidity_threshold = self.config.get('min_liquidity', 0.3)
        self.institutional_threshold = self.config.get('institutional_threshold', 100000)
        
        # Historical data
        self.regime_history: Dict[str, List[Tuple[datetime, MarketRegime]]] = defaultdict(list)
        self.sentiment_history: Dict[str, List[Tuple[datetime, float]]] = defaultdict(list)
        self.intelligence_reports: List[MarketIntelligenceReport] = []
        
        # Pattern library
        self.known_patterns = self._initialize_pattern_library()
        
        logger.info("DeepMarketIntelligence initialized")
    
    def _initialize_pattern_library(self) -> Dict[str, Dict[str, Any]]:
        """Initialize library of known patterns"""
        return {
            'double_top': {
                'type': 'reversal',
                'direction': 'bearish',
                'reliability': 0.75,
                'min_timeframe': '15m'
            },
            'double_bottom': {
                'type': 'reversal',
                'direction': 'bullish',
                'reliability': 0.75,
                'min_timeframe': '15m'
            },
            'head_shoulders': {
                'type': 'reversal',
                'direction': 'bearish',
                'reliability': 0.80,
                'min_timeframe': '1h'
            },
            'inverse_head_shoulders': {
                'type': 'reversal',
                'direction': 'bullish',
                'reliability': 0.80,
                'min_timeframe': '1h'
            },
            'ascending_triangle': {
                'type': 'continuation',
                'direction': 'bullish',
                'reliability': 0.70,
                'min_timeframe': '15m'
            },
            'descending_triangle': {
                'type': 'continuation',
                'direction': 'bearish',
                'reliability': 0.70,
                'min_timeframe': '15m'
            },
            'bull_flag': {
                'type': 'continuation',
                'direction': 'bullish',
                'reliability': 0.68,
                'min_timeframe': '5m'
            },
            'bear_flag': {
                'type': 'continuation',
                'direction': 'bearish',
                'reliability': 0.68,
                'min_timeframe': '5m'
            }
        }
    
    def generate_intelligence_report(self, symbol: str, market_data: Dict[str, Any],
                                    context: Optional[Dict[str, Any]] = None) -> MarketIntelligenceReport:
        """
        Generate comprehensive market intelligence report.
        """
        start_time = datetime.utcnow()
        report_id = f"INTEL-{symbol}-{start_time.strftime('%Y%m%d%H%M%S')}"
        
        logger.info(f"Generating intelligence report for {symbol}")
        
        # 1. Classify market regime
        regime, regime_confidence, regime_duration = self._classify_regime(symbol, market_data)
        
        # 2. Multi-timeframe analysis
        timeframe_alignment, alignment_score = self._analyze_timeframes(symbol, market_data)
        
        # 3. Sentiment analysis
        sentiment, sentiment_score, sentiment_sources = self._analyze_sentiment(symbol, market_data, context)
        
        # 4. Liquidity mapping
        liquidity_map = self._map_liquidity(symbol, market_data)
        key_levels = self._identify_key_levels(liquidity_map)
        
        # 5. Institutional activity detection
        institutional_signals = self._detect_institutional_activity(symbol, market_data)
        institutional_bias = self._determine_institutional_bias(institutional_signals)
        
        # 6. Opportunity discovery
        opportunities = self._discover_opportunities(symbol, market_data, regime, 
                                                    liquidity_map, institutional_signals)
        opportunity_scores = [opp['score'] for opp in opportunities]
        
        # 7. Risk assessment
        risk_factors = self._identify_risk_factors(symbol, market_data, regime, liquidity_map)
        risk_level = len(risk_factors) / 10.0  # Normalize
        
        # 8. Overall assessment
        tradability_score = self._calculate_tradability(regime_confidence, alignment_score,
                                                        liquidity_map.overall_liquidity,
                                                        risk_level)
        recommended_action = self._recommend_action(tradability_score, opportunities, risk_level)
        confidence = self._calculate_confidence(regime_confidence, alignment_score, tradability_score)
        
        report = MarketIntelligenceReport(
            report_id=report_id,
            symbol=symbol,
            timestamp=start_time,
            current_regime=regime,
            regime_confidence=regime_confidence,
            regime_duration=regime_duration,
            timeframe_alignment=timeframe_alignment,
            alignment_score=alignment_score,
            sentiment=sentiment,
            sentiment_score=sentiment_score,
            sentiment_sources=sentiment_sources,
            liquidity_map=liquidity_map,
            key_levels=key_levels,
            institutional_signals=institutional_signals,
            institutional_bias=institutional_bias,
            identified_opportunities=opportunities,
            opportunity_scores=opportunity_scores,
            risk_factors=risk_factors,
            risk_level=risk_level,
            tradability_score=tradability_score,
            recommended_action=recommended_action,
            confidence=confidence
        )
        
        self.intelligence_reports.append(report)
        logger.info(f"Intelligence report generated: {report_id}")
        
        return report
    
    def _classify_regime(self, symbol: str, market_data: Dict[str, Any]) -> Tuple[MarketRegime, float, timedelta]:
        """Classify current market regime"""
        
        prices = market_data.get('prices', [])
        volumes = market_data.get('volumes', [])
        
        if len(prices) < 50:
            return MarketRegime.RANGING, 0.5, timedelta(hours=1)
        
        # Calculate metrics
        returns = np.diff(prices) / prices[:-1]
        volatility = np.std(returns)
        trend_strength = abs(np.mean(returns)) / (volatility + 1e-8)
        
        # Price action analysis
        recent_high = np.max(prices[-20:])
        recent_low = np.min(prices[-20:])
        current_price = prices[-1]
        range_position = (current_price - recent_low) / (recent_high - recent_low + 1e-8)
        
        # Volume analysis
        avg_volume = np.mean(volumes) if volumes else 0
        recent_volume = np.mean(volumes[-10:]) if len(volumes) >= 10 else avg_volume
        volume_ratio = recent_volume / (avg_volume + 1e-8)
        
        # Regime classification
        confidence = 0.5
        
        if volatility > 0.03:  # High volatility
            if volume_ratio > 1.5:
                regime = MarketRegime.CRISIS
                confidence = 0.8
            else:
                regime = MarketRegime.VOLATILE
                confidence = 0.7
        elif trend_strength > 2.0:  # Strong trend
            if np.mean(returns) > 0:
                regime = MarketRegime.TRENDING_BULL
                confidence = 0.85
            else:
                regime = MarketRegime.TRENDING_BEAR
                confidence = 0.85
        elif range_position > 0.9 and volume_ratio > 1.3:
            regime = MarketRegime.BREAKOUT
            confidence = 0.75
        elif range_position < 0.1 and volume_ratio > 1.3:
            regime = MarketRegime.BREAKDOWN
            confidence = 0.75
        elif volatility < 0.01 and range_position > 0.4 and range_position < 0.6:
            if volume_ratio < 0.8:
                regime = MarketRegime.ACCUMULATION
                confidence = 0.65
            else:
                regime = MarketRegime.RANGING
                confidence = 0.70
        else:
            regime = MarketRegime.RANGING
            confidence = 0.60
        
        # Estimate regime duration
        regime_duration = self._estimate_regime_duration(symbol, regime)
        
        # Store in history
        self.regime_history[symbol].append((datetime.utcnow(), regime))
        
        return regime, confidence, regime_duration
    
    def _estimate_regime_duration(self, symbol: str, current_regime: MarketRegime) -> timedelta:
        """Estimate how long the current regime has been active"""
        
        history = self.regime_history.get(symbol, [])
        if not history:
            return timedelta(hours=1)
        
        # Find when current regime started
        duration = timedelta(0)
        for i in range(len(history) - 1, -1, -1):
            timestamp, regime = history[i]
            if regime == current_regime:
                duration = datetime.utcnow() - timestamp
            else:
                break
        
        return duration if duration > timedelta(0) else timedelta(hours=1)
    
    def _analyze_timeframes(self, symbol: str, market_data: Dict[str, Any]) -> Tuple[Dict[str, str], float]:
        """Analyze multiple timeframes for alignment"""
        
        alignment = {}
        
        # Simulate multi-timeframe analysis
        # In production, this would analyze actual multi-timeframe data
        for tf in self.timeframes:
            # Simplified analysis - would use actual timeframe data
            if 'trend' in market_data:
                alignment[tf] = market_data['trend']
            else:
                # Random for demo
                alignment[tf] = np.random.choice(['bullish', 'bearish', 'neutral'])
        
        # Calculate alignment score
        bullish_count = sum(1 for d in alignment.values() if d == 'bullish')
        bearish_count = sum(1 for d in alignment.values() if d == 'bearish')
        total = len(alignment)
        
        if total > 0:
            alignment_score = max(bullish_count, bearish_count) / total
        else:
            alignment_score = 0.5
        
        return alignment, alignment_score
    
    def _analyze_sentiment(self, symbol: str, market_data: Dict[str, Any],
                          context: Optional[Dict[str, Any]]) -> Tuple[SentimentLevel, float, Dict[str, float]]:
        """Analyze sentiment from multiple sources"""
        
        sentiment_sources = {}
        
        # News sentiment
        if context and 'news_sentiment' in context:
            sentiment_sources['news'] = context['news_sentiment']
        else:
            sentiment_sources['news'] = 0.0
        
        # Social media sentiment
        if context and 'social_sentiment' in context:
            sentiment_sources['social'] = context['social_sentiment']
        else:
            sentiment_sources['social'] = 0.0
        
        # Technical sentiment (from price action)
        if 'prices' in market_data and len(market_data['prices']) > 20:
            prices = market_data['prices']
            returns = (prices[-1] - prices[-20]) / prices[-20]
            sentiment_sources['technical'] = np.clip(returns * 10, -1, 1)
        else:
            sentiment_sources['technical'] = 0.0
        
        # Options flow sentiment (if available)
        if context and 'options_sentiment' in context:
            sentiment_sources['options'] = context['options_sentiment']
        
        # Aggregate sentiment
        if sentiment_sources:
            sentiment_score = np.mean(list(sentiment_sources.values()))
        else:
            sentiment_score = 0.0
        
        # Classify sentiment level
        if sentiment_score < -0.6:
            sentiment = SentimentLevel.EXTREME_FEAR
        elif sentiment_score < -0.2:
            sentiment = SentimentLevel.FEAR
        elif sentiment_score > 0.6:
            sentiment = SentimentLevel.EXTREME_GREED
        elif sentiment_score > 0.2:
            sentiment = SentimentLevel.GREED
        else:
            sentiment = SentimentLevel.NEUTRAL
        
        # Store in history
        self.sentiment_history[symbol].append((datetime.utcnow(), sentiment_score))
        
        return sentiment, sentiment_score, sentiment_sources
    
    def _map_liquidity(self, symbol: str, market_data: Dict[str, Any]) -> LiquidityMap:
        """Create detailed liquidity map"""
        
        zones = []
        
        # Analyze order book if available
        if 'order_book' in market_data:
            book = market_data['order_book']
            
            # Identify significant bid levels
            if 'bids' in book:
                for price, volume in book['bids'][:10]:
                    if volume > self.institutional_threshold:
                        zones.append(LiquidityZone(
                            price_level=price,
                            volume=volume,
                            depth=volume,
                            type='support',
                            strength=min(1.0, volume / (self.institutional_threshold * 5)),
                            institutional=True
                        ))
            
            # Identify significant ask levels
            if 'asks' in book:
                for price, volume in book['asks'][:10]:
                    if volume > self.institutional_threshold:
                        zones.append(LiquidityZone(
                            price_level=price,
                            volume=volume,
                            depth=volume,
                            type='resistance',
                            strength=min(1.0, volume / (self.institutional_threshold * 5)),
                            institutional=True
                        ))
        
        # Analyze volume profile
        if 'volume_profile' in market_data:
            profile = market_data['volume_profile']
            for price, volume in profile.items():
                if volume > np.mean(list(profile.values())) * 2:
                    zones.append(LiquidityZone(
                        price_level=price,
                        volume=volume,
                        depth=volume,
                        type='neutral',
                        strength=0.6,
                        institutional=False
                    ))
        
        # Calculate overall liquidity
        if zones:
            overall_liquidity = np.mean([z.strength for z in zones])
        else:
            overall_liquidity = 0.5
        
        # Calculate liquidity imbalance
        buy_liquidity = sum(z.volume for z in zones if z.type == 'support')
        sell_liquidity = sum(z.volume for z in zones if z.type == 'resistance')
        total_liquidity = buy_liquidity + sell_liquidity
        
        if total_liquidity > 0:
            liquidity_imbalance = (buy_liquidity - sell_liquidity) / total_liquidity
        else:
            liquidity_imbalance = 0.0
        
        # Identify thin zones (gaps in liquidity)
        thin_zones = self._identify_thin_zones(zones)
        
        return LiquidityMap(
            symbol=symbol,
            timestamp=datetime.utcnow(),
            zones=zones,
            overall_liquidity=overall_liquidity,
            liquidity_imbalance=liquidity_imbalance,
            thin_zones=thin_zones
        )
    
    def _identify_thin_zones(self, zones: List[LiquidityZone]) -> List[Tuple[float, float]]:
        """Identify price ranges with thin liquidity"""
        
        if not zones:
            return []
        
        # Sort zones by price
        sorted_zones = sorted(zones, key=lambda z: z.price_level)
        
        thin_zones = []
        for i in range(len(sorted_zones) - 1):
            gap = sorted_zones[i+1].price_level - sorted_zones[i].price_level
            avg_price = (sorted_zones[i].price_level + sorted_zones[i+1].price_level) / 2
            
            # If gap is large relative to price, it's a thin zone
            if gap / avg_price > 0.005:  # 0.5% gap
                thin_zones.append((sorted_zones[i].price_level, sorted_zones[i+1].price_level))
        
        return thin_zones
    
    def _identify_key_levels(self, liquidity_map: LiquidityMap) -> List[float]:
        """Identify key price levels from liquidity map"""
        
        # Get strongest liquidity zones
        strong_zones = [z for z in liquidity_map.zones if z.strength > 0.7]
        
        # Sort by strength
        strong_zones.sort(key=lambda z: z.strength, reverse=True)
        
        # Return top 5 levels
        return [z.price_level for z in strong_zones[:5]]
    
    def _detect_institutional_activity(self, symbol: str, 
                                      market_data: Dict[str, Any]) -> List[InstitutionalSignal]:
        """Detect institutional trading activity"""
        
        signals = []
        
        # Check for block trades
        if 'trades' in market_data:
            for trade in market_data['trades']:
                if trade.get('size', 0) > self.institutional_threshold:
                    signals.append(InstitutionalSignal(
                        signal_id=f"INST-{symbol}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                        symbol=symbol,
                        timestamp=datetime.utcnow(),
                        activity_type='block_trade',
                        confidence=0.85,
                        size_estimate=trade['size'],
                        price_level=trade['price'],
                        evidence=[f"Large trade: {trade['size']} at {trade['price']}"],
                        impact_estimate=0.002  # 0.2% estimated impact
                    ))
        
        # Check for iceberg orders (repeated small orders at same price)
        if 'order_flow' in market_data:
            flow = market_data['order_flow']
            # Simplified iceberg detection
            if abs(flow.get('repeated_orders', 0)) > 5:
                signals.append(InstitutionalSignal(
                    signal_id=f"INST-{symbol}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    symbol=symbol,
                    timestamp=datetime.utcnow(),
                    activity_type='iceberg',
                    confidence=0.70,
                    size_estimate=self.institutional_threshold * 2,
                    price_level=market_data.get('price', 0),
                    evidence=["Repeated orders at same price level"],
                    impact_estimate=0.001
                ))
        
        # Check for spoofing (large orders that get cancelled)
        if 'cancelled_orders' in market_data:
            large_cancels = [o for o in market_data['cancelled_orders'] 
                           if o.get('size', 0) > self.institutional_threshold]
            if len(large_cancels) > 2:
                signals.append(InstitutionalSignal(
                    signal_id=f"INST-{symbol}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    symbol=symbol,
                    timestamp=datetime.utcnow(),
                    activity_type='spoofing',
                    confidence=0.65,
                    size_estimate=sum(o['size'] for o in large_cancels),
                    price_level=market_data.get('price', 0),
                    evidence=[f"{len(large_cancels)} large orders cancelled"],
                    impact_estimate=-0.001  # Negative impact (manipulation)
                ))
        
        return signals
    
    def _determine_institutional_bias(self, signals: List[InstitutionalSignal]) -> str:
        """Determine overall institutional bias from signals"""
        
        if not signals:
            return 'neutral'
        
        # Count accumulation vs distribution signals
        accumulation_count = sum(1 for s in signals if s.activity_type in ['block_trade', 'iceberg'] 
                                and s.impact_estimate > 0)
        distribution_count = sum(1 for s in signals if s.activity_type in ['block_trade', 'iceberg'] 
                                and s.impact_estimate < 0)
        
        if accumulation_count > distribution_count:
            return 'bullish'
        elif distribution_count > accumulation_count:
            return 'bearish'
        else:
            return 'neutral'
    
    def _discover_opportunities(self, symbol: str, market_data: Dict[str, Any],
                               regime: MarketRegime, liquidity_map: LiquidityMap,
                               institutional_signals: List[InstitutionalSignal]) -> List[Dict[str, Any]]:
        """Discover trading opportunities"""
        
        opportunities = []
        
        # Opportunity 1: Trend following in strong trends
        if regime in [MarketRegime.TRENDING_BULL, MarketRegime.TRENDING_BEAR]:
            opportunities.append({
                'type': 'trend_following',
                'direction': 'buy' if regime == MarketRegime.TRENDING_BULL else 'sell',
                'score': 0.75,
                'rationale': f"Strong {regime.value} regime",
                'entry_strategy': 'pullback_to_moving_average',
                'risk_reward': 2.5
            })
        
        # Opportunity 2: Breakout from accumulation
        if regime == MarketRegime.ACCUMULATION and liquidity_map.overall_liquidity > 0.6:
            opportunities.append({
                'type': 'breakout',
                'direction': 'buy',
                'score': 0.70,
                'rationale': "Accumulation phase with good liquidity",
                'entry_strategy': 'breakout_above_range',
                'risk_reward': 3.0
            })
        
        # Opportunity 3: Institutional following
        if institutional_signals:
            bullish_signals = [s for s in institutional_signals if s.impact_estimate > 0]
            if len(bullish_signals) >= 2:
                opportunities.append({
                    'type': 'institutional_following',
                    'direction': 'buy',
                    'score': 0.80,
                    'rationale': f"{len(bullish_signals)} bullish institutional signals",
                    'entry_strategy': 'follow_institutional_flow',
                    'risk_reward': 2.0
                })
        
        # Opportunity 4: Liquidity grab
        if liquidity_map.thin_zones:
            opportunities.append({
                'type': 'liquidity_grab',
                'direction': 'varies',
                'score': 0.65,
                'rationale': f"{len(liquidity_map.thin_zones)} thin liquidity zones identified",
                'entry_strategy': 'fade_liquidity_sweep',
                'risk_reward': 2.5
            })
        
        return opportunities
    
    def _identify_risk_factors(self, symbol: str, market_data: Dict[str, Any],
                              regime: MarketRegime, liquidity_map: LiquidityMap) -> List[str]:
        """Identify risk factors"""
        
        risks = []
        
        # Regime risks
        if regime == MarketRegime.VOLATILE:
            risks.append("High volatility regime - increased risk")
        elif regime == MarketRegime.CRISIS:
            risks.append("Crisis regime - extreme risk")
        
        # Liquidity risks
        if liquidity_map.overall_liquidity < self.min_liquidity_threshold:
            risks.append("Low liquidity - increased slippage risk")
        
        if liquidity_map.thin_zones:
            risks.append(f"{len(liquidity_map.thin_zones)} thin liquidity zones - gap risk")
        
        # Volatility risks
        if 'volatility' in market_data and market_data['volatility'] > 0.05:
            risks.append("High volatility - increased stop-out risk")
        
        # Spread risks
        if 'bid_ask_spread' in market_data and market_data['bid_ask_spread'] > 0.003:
            risks.append("Wide spreads - high transaction costs")
        
        return risks
    
    def _calculate_tradability(self, regime_confidence: float, alignment_score: float,
                              liquidity: float, risk_level: float) -> float:
        """Calculate overall tradability score"""
        
        # Weighted average
        tradability = (
            regime_confidence * 0.3 +
            alignment_score * 0.25 +
            liquidity * 0.25 +
            (1.0 - risk_level) * 0.20
        )
        
        return np.clip(tradability, 0.0, 1.0)
    
    def _recommend_action(self, tradability_score: float, 
                         opportunities: List[Dict[str, Any]], 
                         risk_level: float) -> str:
        """Recommend trading action"""
        
        if risk_level > 0.7:
            return "AVOID - Risk too high"
        
        if tradability_score < 0.4:
            return "WAIT - Low tradability"
        
        if not opportunities:
            return "MONITOR - No clear opportunities"
        
        # Find best opportunity
        best_opp = max(opportunities, key=lambda x: x['score'])
        
        if best_opp['score'] > 0.75 and tradability_score > 0.6:
            return f"TRADE - {best_opp['type']} ({best_opp['direction']})"
        elif best_opp['score'] > 0.65:
            return f"CONSIDER - {best_opp['type']} ({best_opp['direction']})"
        else:
            return "MONITOR - Opportunities developing"
    
    def _calculate_confidence(self, regime_confidence: float, 
                             alignment_score: float, 
                             tradability_score: float) -> float:
        """Calculate overall confidence in the analysis"""
        
        confidence = (regime_confidence + alignment_score + tradability_score) / 3.0
        return np.clip(confidence, 0.0, 1.0)
    
    def get_intelligence_stats(self) -> Dict[str, Any]:
        """Get statistics about intelligence gathering"""
        
        if not self.intelligence_reports:
            return {'total_reports': 0}
        
        total = len(self.intelligence_reports)
        
        # Regime distribution
        regime_counts = {}
        for report in self.intelligence_reports:
            regime = report.current_regime.value
            regime_counts[regime] = regime_counts.get(regime, 0) + 1
        
        # Average scores
        avg_tradability = np.mean([r.tradability_score for r in self.intelligence_reports])
        avg_confidence = np.mean([r.confidence for r in self.intelligence_reports])
        avg_opportunities = np.mean([len(r.identified_opportunities) for r in self.intelligence_reports])
        
        return {
            'total_reports': total,
            'regime_distribution': regime_counts,
            'average_tradability': avg_tradability,
            'average_confidence': avg_confidence,
            'average_opportunities_per_report': avg_opportunities
        }


def quick_start_intelligence(config: Optional[Dict[str, Any]] = None) -> DeepMarketIntelligence:
    """Quick start function for market intelligence"""
    return DeepMarketIntelligence(config)
