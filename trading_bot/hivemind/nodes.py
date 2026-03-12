"""
Specialized Hivemind Nodes
============================================================

Each node is a specialized AI agent with domain expertise.
Nodes analyze market data from their unique perspective and
cast votes that contribute to the collective decision.
"""

import logging
import numpy as np
from datetime import datetime
from typing import Any, Dict, List, Optional
import asyncio

from .core import (
    HiveNode,
    NodeType,
    NodeState,
    NodeVote,
    SignalDirection,
    MarketContext,
)

logger = logging.getLogger(__name__)


class TechnicalNode(HiveNode):
    """
    Technical Analysis Node
    
    Analyzes price action, patterns, and indicators:
    - Trend analysis (MA, MACD)
    - Momentum (RSI, Stochastic)
    - Volatility (ATR, Bollinger)
    - Chart patterns
    - Support/Resistance
    """
    
    def __init__(self, node_id: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, NodeType.TECHNICAL, config)
        self.indicators = config.get('indicators', ['rsi', 'macd', 'ma', 'atr'])
    
    async def analyze(self, symbol: str, market_data: Dict[str, Any]) -> NodeVote:
        self.state = NodeState.ANALYZING
        
        try:
            signals = []
            reasoning_parts = []
            
            # Get OHLCV data
            ohlcv = market_data.get('ohlcv', [])
            if not ohlcv:
                return self._neutral_vote("No OHLCV data available")
            
            closes = [bar.get('close', 0) for bar in ohlcv[-50:]]
            if len(closes) < 20:
                return self._neutral_vote("Insufficient data")
            
            # RSI Analysis
            rsi = self._calculate_rsi(closes)
            if rsi < 30:
                signals.append(0.7)
                reasoning_parts.append(f"RSI oversold ({rsi:.1f})")
            elif rsi > 70:
                signals.append(-0.7)
                reasoning_parts.append(f"RSI overbought ({rsi:.1f})")
            else:
                signals.append(0)
                reasoning_parts.append(f"RSI neutral ({rsi:.1f})")
            
            # Moving Average Analysis
            ma_20 = np.mean(closes[-20:])
            ma_50 = np.mean(closes[-50:]) if len(closes) >= 50 else ma_20
            current_price = closes[-1]
            
            if current_price > ma_20 > ma_50:
                signals.append(0.6)
                reasoning_parts.append("Price above MAs, bullish alignment")
            elif current_price < ma_20 < ma_50:
                signals.append(-0.6)
                reasoning_parts.append("Price below MAs, bearish alignment")
            else:
                signals.append(0)
                reasoning_parts.append("MAs mixed")
            
            # Trend strength
            price_change = (closes[-1] - closes[-20]) / closes[-20]
            if price_change > 0.02:
                signals.append(0.5)
                reasoning_parts.append(f"Strong uptrend ({price_change:.1%})")
            elif price_change < -0.02:
                signals.append(-0.5)
                reasoning_parts.append(f"Strong downtrend ({price_change:.1%})")
            
            # Aggregate signals
            avg_signal = np.mean(signals) if signals else 0
            confidence = min(abs(avg_signal) + 0.3, 0.95)
            
            direction = SignalDirection.from_numeric(avg_signal)
            
            self.state = NodeState.IDLE
            vote = NodeVote(
                node_id=self.node_id,
                node_type=self.node_type,
                direction=direction,
                confidence=confidence,
                weight=self.current_weight,
                reasoning=" | ".join(reasoning_parts),
            )
            self.last_vote = vote
            return vote
            
        except Exception as e:
            logger.error(f"Technical node error: {e}")
            self.state = NodeState.ERROR
            return self._neutral_vote(f"Error: {str(e)}")
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        if len(prices) < period + 1:
            return 50.0
        
        deltas = np.diff(prices[-period-1:])
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def _neutral_vote(self, reason: str) -> NodeVote:
        return NodeVote(
            node_id=self.node_id,
            node_type=self.node_type,
            direction=SignalDirection.NEUTRAL,
            confidence=0.3,
            weight=self.current_weight,
            reasoning=reason,
        )


class FundamentalNode(HiveNode):
    """
    Fundamental Analysis Node
    
    Analyzes economic and fundamental data:
    - Interest rate differentials
    - Economic indicators (GDP, CPI, NFP)
    - Central bank policy
    - Trade balance
    """
    
    def __init__(self, node_id: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, NodeType.FUNDAMENTAL, config)
    
    async def analyze(self, symbol: str, market_data: Dict[str, Any]) -> NodeVote:
        self.state = NodeState.ANALYZING
        
        try:
            signals = []
            reasoning_parts = []
            
            fundamentals = market_data.get('fundamentals', {})
            
            # Interest rate differential
            rate_diff = fundamentals.get('interest_rate_differential', 0)
            if rate_diff > 1.0:
                signals.append(0.5)
                reasoning_parts.append(f"Positive rate differential ({rate_diff:.1f}%)")
            elif rate_diff < -1.0:
                signals.append(-0.5)
                reasoning_parts.append(f"Negative rate differential ({rate_diff:.1f}%)")
            
            # Economic outlook
            outlook = fundamentals.get('economic_outlook', 'neutral')
            if outlook == 'bullish':
                signals.append(0.4)
                reasoning_parts.append("Bullish economic outlook")
            elif outlook == 'bearish':
                signals.append(-0.4)
                reasoning_parts.append("Bearish economic outlook")
            
            # Central bank stance
            cb_stance = fundamentals.get('central_bank_stance', 'neutral')
            if cb_stance == 'hawkish':
                signals.append(0.3)
                reasoning_parts.append("Hawkish central bank")
            elif cb_stance == 'dovish':
                signals.append(-0.3)
                reasoning_parts.append("Dovish central bank")
            
            # GDP growth
            gdp_growth = fundamentals.get('gdp_growth', 0)
            if gdp_growth > 2.5:
                signals.append(0.3)
                reasoning_parts.append(f"Strong GDP growth ({gdp_growth:.1f}%)")
            elif gdp_growth < 1.0:
                signals.append(-0.3)
                reasoning_parts.append(f"Weak GDP growth ({gdp_growth:.1f}%)")
            
            if not signals:
                return self._neutral_vote("No fundamental data available")
            
            avg_signal = np.mean(signals)
            confidence = min(abs(avg_signal) + 0.4, 0.90)
            direction = SignalDirection.from_numeric(avg_signal)
            
            self.state = NodeState.IDLE
            vote = NodeVote(
                node_id=self.node_id,
                node_type=self.node_type,
                direction=direction,
                confidence=confidence,
                weight=self.current_weight,
                reasoning=" | ".join(reasoning_parts) if reasoning_parts else "Neutral fundamentals",
            )
            self.last_vote = vote
            return vote
            
        except Exception as e:
            logger.error(f"Fundamental node error: {e}")
            self.state = NodeState.ERROR
            return self._neutral_vote(f"Error: {str(e)}")
    
    def _neutral_vote(self, reason: str) -> NodeVote:
        return NodeVote(
            node_id=self.node_id,
            node_type=self.node_type,
            direction=SignalDirection.NEUTRAL,
            confidence=0.3,
            weight=self.current_weight,
            reasoning=reason,
        )


class SentimentNode(HiveNode):
    """
    Sentiment Analysis Node
    
    Analyzes market sentiment from various sources:
    - Social media sentiment
    - News sentiment
    - Positioning data
    - Fear/Greed indicators
    """
    
    def __init__(self, node_id: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, NodeType.SENTIMENT, config)
    
    async def analyze(self, symbol: str, market_data: Dict[str, Any]) -> NodeVote:
        self.state = NodeState.ANALYZING
        
        try:
            signals = []
            reasoning_parts = []
            
            sentiment = market_data.get('sentiment', {})
            
            # Overall sentiment score
            overall_score = sentiment.get('overall_score', 0)
            if overall_score > 0.3:
                signals.append(0.6)
                reasoning_parts.append(f"Bullish sentiment ({overall_score:.2f})")
            elif overall_score < -0.3:
                signals.append(-0.6)
                reasoning_parts.append(f"Bearish sentiment ({overall_score:.2f})")
            else:
                signals.append(0)
                reasoning_parts.append(f"Neutral sentiment ({overall_score:.2f})")
            
            # Fear/Greed index
            fear_greed = sentiment.get('fear_greed_index', 50)
            if fear_greed > 70:
                # Extreme greed - contrarian bearish
                signals.append(-0.3)
                reasoning_parts.append(f"Extreme greed ({fear_greed}) - contrarian bearish")
            elif fear_greed < 30:
                # Extreme fear - contrarian bullish
                signals.append(0.3)
                reasoning_parts.append(f"Extreme fear ({fear_greed}) - contrarian bullish")
            
            # Positioning
            positioning = sentiment.get('positioning', {})
            retail_long = positioning.get('retail', {}).get('long_percent', 50)
            if retail_long > 70:
                # Retail very long - contrarian
                signals.append(-0.2)
                reasoning_parts.append(f"Retail heavily long ({retail_long}%) - contrarian")
            elif retail_long < 30:
                signals.append(0.2)
                reasoning_parts.append(f"Retail heavily short ({100-retail_long}%) - contrarian")
            
            if not signals:
                return self._neutral_vote("No sentiment data available")
            
            avg_signal = np.mean(signals)
            confidence = min(abs(avg_signal) + 0.3, 0.85)
            direction = SignalDirection.from_numeric(avg_signal)
            
            self.state = NodeState.IDLE
            vote = NodeVote(
                node_id=self.node_id,
                node_type=self.node_type,
                direction=direction,
                confidence=confidence,
                weight=self.current_weight,
                reasoning=" | ".join(reasoning_parts) if reasoning_parts else "Neutral sentiment",
            )
            self.last_vote = vote
            return vote
            
        except Exception as e:
            logger.error(f"Sentiment node error: {e}")
            self.state = NodeState.ERROR
            return self._neutral_vote(f"Error: {str(e)}")
    
    def _neutral_vote(self, reason: str) -> NodeVote:
        return NodeVote(
            node_id=self.node_id,
            node_type=self.node_type,
            direction=SignalDirection.NEUTRAL,
            confidence=0.3,
            weight=self.current_weight,
            reasoning=reason,
        )


class RiskNode(HiveNode):
    """
    Risk Analysis Node
    
    Analyzes risk factors:
    - Volatility levels
    - Drawdown risk
    - Correlation risk
    - Position sizing
    - Risk/Reward ratios
    """
    
    def __init__(self, node_id: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, NodeType.RISK, config)
        self.max_risk_per_trade = config.get('max_risk_per_trade', 0.02)
    
    async def analyze(self, symbol: str, market_data: Dict[str, Any]) -> NodeVote:
        self.state = NodeState.ANALYZING
        
        try:
            signals = []
            reasoning_parts = []
            
            # Get price data for volatility
            ohlcv = market_data.get('ohlcv', [])
            
            if ohlcv:
                # Calculate ATR-based volatility
                highs = [bar.get('high', 0) for bar in ohlcv[-20:]]
                lows = [bar.get('low', 0) for bar in ohlcv[-20:]]
                closes = [bar.get('close', 0) for bar in ohlcv[-20:]]
                
                if len(closes) >= 14:
                    atr = self._calculate_atr(highs, lows, closes)
                    atr_percent = atr / closes[-1] * 100
                    
                    if atr_percent > 2.0:
                        signals.append(-0.3)
                        reasoning_parts.append(f"High volatility (ATR {atr_percent:.2f}%) - reduce size")
                    elif atr_percent < 0.5:
                        signals.append(0.2)
                        reasoning_parts.append(f"Low volatility (ATR {atr_percent:.2f}%) - favorable")
                    else:
                        reasoning_parts.append(f"Normal volatility (ATR {atr_percent:.2f}%)")
            
            # Check risk parameters from context
            risk_data = market_data.get('risk', {})
            
            current_drawdown = risk_data.get('current_drawdown', 0)
            if current_drawdown > 0.1:
                signals.append(-0.5)
                reasoning_parts.append(f"High drawdown ({current_drawdown:.1%}) - reduce exposure")
            
            daily_loss = risk_data.get('daily_loss', 0)
            if daily_loss > 0.03:
                signals.append(-0.7)
                reasoning_parts.append(f"Daily loss limit approaching ({daily_loss:.1%})")
            
            # Risk/Reward assessment
            potential_rr = risk_data.get('potential_risk_reward', 0)
            if potential_rr >= 2.0:
                signals.append(0.4)
                reasoning_parts.append(f"Good R:R ratio ({potential_rr:.1f})")
            elif potential_rr < 1.0 and potential_rr > 0:
                signals.append(-0.4)
                reasoning_parts.append(f"Poor R:R ratio ({potential_rr:.1f})")
            
            if not signals:
                signals.append(0)
                reasoning_parts.append("Risk parameters acceptable")
            
            avg_signal = np.mean(signals)
            confidence = 0.85  # Risk node should have high confidence
            direction = SignalDirection.from_numeric(avg_signal)
            
            self.state = NodeState.IDLE
            vote = NodeVote(
                node_id=self.node_id,
                node_type=self.node_type,
                direction=direction,
                confidence=confidence,
                weight=self.current_weight,
                reasoning=" | ".join(reasoning_parts),
            )
            self.last_vote = vote
            return vote
            
        except Exception as e:
            logger.error(f"Risk node error: {e}")
            self.state = NodeState.ERROR
            return self._neutral_vote(f"Error: {str(e)}")
    
    def _calculate_atr(self, highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
        if len(highs) < period:
            return 0.0
        
        tr_list = []
        for i in range(1, len(highs)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i-1]),
                abs(lows[i] - closes[i-1])
            )
            tr_list.append(tr)
        
        return np.mean(tr_list[-period:])
    
    def _neutral_vote(self, reason: str) -> NodeVote:
        return NodeVote(
            node_id=self.node_id,
            node_type=self.node_type,
            direction=SignalDirection.NEUTRAL,
            confidence=0.5,
            weight=self.current_weight,
            reasoning=reason,
        )


class ExecutionNode(HiveNode):
    """
    Execution Analysis Node
    
    Analyzes execution factors:
    - Liquidity conditions
    - Spread analysis
    - Optimal entry timing
    - Slippage estimation
    """
    
    def __init__(self, node_id: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, NodeType.EXECUTION, config)
    
    async def analyze(self, symbol: str, market_data: Dict[str, Any]) -> NodeVote:
        self.state = NodeState.ANALYZING
        
        try:
            signals = []
            reasoning_parts = []
            
            execution = market_data.get('execution', {})
            
            # Spread analysis
            spread = execution.get('spread', 0)
            avg_spread = execution.get('avg_spread', spread)
            
            if spread > 0 and avg_spread > 0:
                spread_ratio = spread / avg_spread
                if spread_ratio > 1.5:
                    signals.append(-0.4)
                    reasoning_parts.append(f"Wide spread ({spread_ratio:.1f}x avg) - poor execution")
                elif spread_ratio < 0.8:
                    signals.append(0.3)
                    reasoning_parts.append(f"Tight spread ({spread_ratio:.1f}x avg) - good execution")
                else:
                    reasoning_parts.append("Normal spread conditions")
            
            # Liquidity
            liquidity = execution.get('liquidity_score', 0.5)
            if liquidity < 0.3:
                signals.append(-0.5)
                reasoning_parts.append(f"Low liquidity ({liquidity:.0%}) - execution risk")
            elif liquidity > 0.7:
                signals.append(0.2)
                reasoning_parts.append(f"Good liquidity ({liquidity:.0%})")
            
            # Market session
            session = execution.get('session', 'unknown')
            if session in ['london', 'new_york', 'overlap']:
                signals.append(0.2)
                reasoning_parts.append(f"Active session ({session})")
            elif session in ['asian', 'off_hours']:
                signals.append(-0.2)
                reasoning_parts.append(f"Quiet session ({session})")
            
            if not signals:
                signals.append(0)
                reasoning_parts.append("Execution conditions acceptable")
            
            avg_signal = np.mean(signals)
            confidence = 0.75
            direction = SignalDirection.from_numeric(avg_signal)
            
            self.state = NodeState.IDLE
            vote = NodeVote(
                node_id=self.node_id,
                node_type=self.node_type,
                direction=direction,
                confidence=confidence,
                weight=self.current_weight,
                reasoning=" | ".join(reasoning_parts),
            )
            self.last_vote = vote
            return vote
            
        except Exception as e:
            logger.error(f"Execution node error: {e}")
            self.state = NodeState.ERROR
            return self._neutral_vote(f"Error: {str(e)}")
    
    def _neutral_vote(self, reason: str) -> NodeVote:
        return NodeVote(
            node_id=self.node_id,
            node_type=self.node_type,
            direction=SignalDirection.NEUTRAL,
            confidence=0.5,
            weight=self.current_weight,
            reasoning=reason,
        )


class MacroNode(HiveNode):
    """
    Macro Analysis Node
    
    Analyzes macroeconomic factors:
    - Global risk sentiment
    - Cross-market correlations
    - Economic calendar events
    - Geopolitical factors
    """
    
    def __init__(self, node_id: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, NodeType.MACRO, config)
    
    async def analyze(self, symbol: str, market_data: Dict[str, Any]) -> NodeVote:
        self.state = NodeState.ANALYZING
        
        try:
            signals = []
            reasoning_parts = []
            
            macro = market_data.get('macro', {})
            
            # Risk appetite
            risk_appetite = macro.get('risk_appetite', 'neutral')
            if risk_appetite == 'risk_on':
                signals.append(0.4)
                reasoning_parts.append("Risk-on environment")
            elif risk_appetite == 'risk_off':
                signals.append(-0.4)
                reasoning_parts.append("Risk-off environment")
            
            # Dollar strength (for USD pairs)
            if 'USD' in symbol:
                dxy_trend = macro.get('dxy_trend', 'neutral')
                is_usd_base = symbol.startswith('USD')
                
                if dxy_trend == 'bullish':
                    signal = 0.3 if is_usd_base else -0.3
                    reasoning_parts.append(f"USD strength ({'bullish' if is_usd_base else 'bearish'} for {symbol})")
                elif dxy_trend == 'bearish':
                    signal = -0.3 if is_usd_base else 0.3
                    reasoning_parts.append(f"USD weakness ({'bearish' if is_usd_base else 'bullish'} for {symbol})")
                else:
                    signal = 0
                signals.append(signal)
            
            # Upcoming events
            high_impact_events = macro.get('high_impact_events_24h', 0)
            if high_impact_events > 2:
                signals.append(-0.3)
                reasoning_parts.append(f"Multiple high-impact events ({high_impact_events}) - caution")
            
            # Yield differentials
            yield_diff = macro.get('yield_differential', 0)
            if abs(yield_diff) > 1.0:
                signal = 0.3 if yield_diff > 0 else -0.3
                signals.append(signal)
                reasoning_parts.append(f"Yield differential: {yield_diff:.2f}%")
            
            if not signals:
                signals.append(0)
                reasoning_parts.append("Neutral macro environment")
            
            avg_signal = np.mean(signals)
            confidence = min(abs(avg_signal) + 0.4, 0.85)
            direction = SignalDirection.from_numeric(avg_signal)
            
            self.state = NodeState.IDLE
            vote = NodeVote(
                node_id=self.node_id,
                node_type=self.node_type,
                direction=direction,
                confidence=confidence,
                weight=self.current_weight,
                reasoning=" | ".join(reasoning_parts) if reasoning_parts else "Neutral macro",
            )
            self.last_vote = vote
            return vote
            
        except Exception as e:
            logger.error(f"Macro node error: {e}")
            self.state = NodeState.ERROR
            return self._neutral_vote(f"Error: {str(e)}")
    
    def _neutral_vote(self, reason: str) -> NodeVote:
        return NodeVote(
            node_id=self.node_id,
            node_type=self.node_type,
            direction=SignalDirection.NEUTRAL,
            confidence=0.4,
            weight=self.current_weight,
            reasoning=reason,
        )


class MicrostructureNode(HiveNode):
    """
    Market Microstructure Node
    
    Analyzes order flow and market depth:
    - Order book imbalance
    - Trade flow analysis
    - Toxicity detection
    - Smart money tracking
    """
    
    def __init__(self, node_id: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, NodeType.MICROSTRUCTURE, config)
    
    async def analyze(self, symbol: str, market_data: Dict[str, Any]) -> NodeVote:
        self.state = NodeState.ANALYZING
        
        try:
            signals = []
            reasoning_parts = []
            
            microstructure = market_data.get('microstructure', {})
            
            # Order flow imbalance
            order_flow = microstructure.get('order_flow', {})
            imbalance = order_flow.get('imbalance', 0)
            
            if imbalance > 0.2:
                signals.append(0.5)
                reasoning_parts.append(f"Buying pressure (imbalance: {imbalance:.0%})")
            elif imbalance < -0.2:
                signals.append(-0.5)
                reasoning_parts.append(f"Selling pressure (imbalance: {imbalance:.0%})")
            
            # Toxicity
            toxicity = microstructure.get('toxicity', 0)
            if toxicity > 0.5:
                signals.append(-0.3)
                reasoning_parts.append(f"High toxicity ({toxicity:.0%}) - adverse selection risk")
            
            # Large order detection
            large_orders = microstructure.get('large_orders', {})
            large_buys = large_orders.get('buy_count', 0)
            large_sells = large_orders.get('sell_count', 0)
            
            if large_buys > large_sells * 1.5:
                signals.append(0.4)
                reasoning_parts.append(f"Large buyer activity ({large_buys} vs {large_sells})")
            elif large_sells > large_buys * 1.5:
                signals.append(-0.4)
                reasoning_parts.append(f"Large seller activity ({large_sells} vs {large_buys})")
            
            if not signals:
                signals.append(0)
                reasoning_parts.append("Neutral order flow")
            
            avg_signal = np.mean(signals)
            confidence = min(abs(avg_signal) + 0.35, 0.85)
            direction = SignalDirection.from_numeric(avg_signal)
            
            self.state = NodeState.IDLE
            vote = NodeVote(
                node_id=self.node_id,
                node_type=self.node_type,
                direction=direction,
                confidence=confidence,
                weight=self.current_weight,
                reasoning=" | ".join(reasoning_parts) if reasoning_parts else "Neutral microstructure",
            )
            self.last_vote = vote
            return vote
            
        except Exception as e:
            logger.error(f"Microstructure node error: {e}")
            self.state = NodeState.ERROR
            return self._neutral_vote(f"Error: {str(e)}")
    
    def _neutral_vote(self, reason: str) -> NodeVote:
        return NodeVote(
            node_id=self.node_id,
            node_type=self.node_type,
            direction=SignalDirection.NEUTRAL,
            confidence=0.4,
            weight=self.current_weight,
            reasoning=reason,
        )


class QuantNode(HiveNode):
    """
    Quantitative Analysis Node
    
    Analyzes statistical and quantitative factors:
    - Mean reversion signals
    - Momentum factors
    - Statistical arbitrage
    - Machine learning predictions
    """
    
    def __init__(self, node_id: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, NodeType.QUANT, config)
    
    async def analyze(self, symbol: str, market_data: Dict[str, Any]) -> NodeVote:
        self.state = NodeState.ANALYZING
        
        try:
            signals = []
            reasoning_parts = []
            
            ohlcv = market_data.get('ohlcv', [])
            if not ohlcv or len(ohlcv) < 50:
                return self._neutral_vote("Insufficient data for quant analysis")
            
            closes = [bar.get('close', 0) for bar in ohlcv[-100:]]
            
            # Z-score (mean reversion)
            mean = np.mean(closes[-50:])
            std = np.std(closes[-50:])
            if std > 0:
                z_score = (closes[-1] - mean) / std
                
                if z_score < -2:
                    signals.append(0.6)
                    reasoning_parts.append(f"Oversold (z-score: {z_score:.2f})")
                elif z_score > 2:
                    signals.append(-0.6)
                    reasoning_parts.append(f"Overbought (z-score: {z_score:.2f})")
                elif abs(z_score) < 0.5:
                    reasoning_parts.append(f"Near mean (z-score: {z_score:.2f})")
            
            # Momentum
            returns_5d = (closes[-1] - closes[-5]) / closes[-5] if len(closes) >= 5 else 0
            returns_20d = (closes[-1] - closes[-20]) / closes[-20] if len(closes) >= 20 else 0
            
            if returns_5d > 0.02 and returns_20d > 0.03:
                signals.append(0.5)
                reasoning_parts.append(f"Strong momentum (5d: {returns_5d:.1%}, 20d: {returns_20d:.1%})")
            elif returns_5d < -0.02 and returns_20d < -0.03:
                signals.append(-0.5)
                reasoning_parts.append(f"Negative momentum (5d: {returns_5d:.1%}, 20d: {returns_20d:.1%})")
            
            # Volatility regime
            recent_vol = np.std(closes[-20:]) / np.mean(closes[-20:])
            historical_vol = np.std(closes[-50:]) / np.mean(closes[-50:])
            
            if recent_vol > historical_vol * 1.5:
                signals.append(-0.2)
                reasoning_parts.append("Elevated volatility regime")
            elif recent_vol < historical_vol * 0.7:
                signals.append(0.2)
                reasoning_parts.append("Low volatility regime")
            
            if not signals:
                signals.append(0)
                reasoning_parts.append("Neutral quant signals")
            
            avg_signal = np.mean(signals)
            confidence = min(abs(avg_signal) + 0.4, 0.90)
            direction = SignalDirection.from_numeric(avg_signal)
            
            self.state = NodeState.IDLE
            vote = NodeVote(
                node_id=self.node_id,
                node_type=self.node_type,
                direction=direction,
                confidence=confidence,
                weight=self.current_weight,
                reasoning=" | ".join(reasoning_parts),
            )
            self.last_vote = vote
            return vote
            
        except Exception as e:
            logger.error(f"Quant node error: {e}")
            self.state = NodeState.ERROR
            return self._neutral_vote(f"Error: {str(e)}")
    
    def _neutral_vote(self, reason: str) -> NodeVote:
        return NodeVote(
            node_id=self.node_id,
            node_type=self.node_type,
            direction=SignalDirection.NEUTRAL,
            confidence=0.4,
            weight=self.current_weight,
            reasoning=reason,
        )


# Node factory
def create_node(node_type: NodeType, node_id: Optional[str] = None, config: Optional[Dict[str, Any]] = None) -> HiveNode:
    """Factory function to create nodes"""
    node_classes = {
        NodeType.TECHNICAL: TechnicalNode,
        NodeType.FUNDAMENTAL: FundamentalNode,
        NodeType.SENTIMENT: SentimentNode,
        NodeType.RISK: RiskNode,
        NodeType.EXECUTION: ExecutionNode,
        NodeType.MACRO: MacroNode,
        NodeType.MICROSTRUCTURE: MicrostructureNode,
        NodeType.QUANT: QuantNode,
    }
    
    node_class = node_classes.get(node_type, TechnicalNode)
    return node_class(node_id, config)
