"""
Analysis Orchestrator - Coordinates all analysis components

This module serves as the central coordination point for all analysis components,
aggregating signals, resolving conflicts, and providing a unified analysis interface.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import numpy as np
import pandas as pd

# Import analysis components
from trading_bot.analysis.market_structure import MarketStructureAnalyzer
from trading_bot.analysis.liquidity import LiquidityAnalyzer
from trading_bot.analysis.order_flow import OrderFlowAnalyzer, AdvancedOrderFlowAnalyzer
from trading_bot.analysis.market_microstructure import MarketMicrostructureAnalyzer
from trading_bot.analysis.price_action import PriceActionAnalyzer
from trading_bot.analysis.market_context import MarketContextAnalyzer
from trading_bot.analysis.technical_indicators import TechnicalIndicatorAnalyzer
from trading_bot.analysis.sentiment_analyzer import SentimentAnalyzer
from trading_bot.analysis.fundamental_analyzer import FundamentalAnalyzer
from trading_bot.analysis.anomaly_detection import AnomalyDetector
from trading_bot.ml.predictive_models import PredictiveModel
import numpy
import pandas

logger = logging.getLogger(__name__)

class Signal:
    """Trading signal with metadata and confidence score"""
    
    def __init__(self, symbol: str, direction: int, size: float, 
                source: str, confidence: float, timestamp: datetime = None,
                metadata: Dict[str, Any] = None):
        self.symbol = symbol
        self.direction = direction  # 1 for buy, -1 for sell, 0 for neutral
        self.size = size
        self.source = source
        self.confidence = confidence  # 0-100 scale
        self.timestamp = timestamp or datetime.now()
        self.metadata = metadata or {}
        self.urgency = metadata.get('urgency', 0.5)  # 0-1 scale
    
    def __str__(self):
        return (f"Signal({self.symbol}, direction={self.direction}, "
                f"confidence={self.confidence:.1f}, source={self.source})")


class MarketContext:
    """Comprehensive market context information"""
    
    def __init__(self, symbol: str, timeframe: str):
        self.symbol = symbol
        self.timeframe = timeframe
        self.regime = None  # trending, ranging, volatile, etc.
        self.volatility = 0.0
        self.liquidity = 0.0
        self.sentiment = 0.0
        self.trend_strength = 0.0
        self.support_levels = []
        self.resistance_levels = []
        self.key_levels = []
        self.recent_events = []
        self.correlated_assets = {}
        self.anomalies = []
        self.metadata = {}
    
    def update(self, **kwargs):
        """Update context attributes"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                self.metadata[key] = value


class AnalysisOrchestrator:
    """
    Coordinates all analysis components and provides a unified interface
    for generating trading signals and market context.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Initialize analysis components
        self.market_structure = MarketStructureAnalyzer()
        self.liquidity = LiquidityAnalyzer()
        self.order_flow = AdvancedOrderFlowAnalyzer()
        self.microstructure = MarketMicrostructureAnalyzer()
        self.price_action = PriceActionAnalyzer()
        self.market_context = MarketContextAnalyzer()
        self.technical = TechnicalIndicatorAnalyzer()
        self.sentiment = SentimentAnalyzer()
        self.fundamental = FundamentalAnalyzer()
        self.anomaly = AnomalyDetector()
        self.predictive = PredictiveModel()
        
        # Signal weighting configuration
        self.signal_weights = self.config.get('signal_weights', {
            'market_structure': 0.15,
            'liquidity': 0.10,
            'order_flow': 0.15,
            'microstructure': 0.05,
            'price_action': 0.10,
            'technical': 0.15,
            'sentiment': 0.10,
            'fundamental': 0.05,
            'predictive': 0.15
        })
        
        # Minimum confidence threshold
        self.min_confidence = self.config.get('min_confidence', 60.0)
        
        # Signal history
        self.signal_history = {}
        
        logger.info("Analysis Orchestrator initialized")
    
    async def analyze_market(self, symbol: str, timeframe: str, 
                           data: pd.DataFrame) -> MarketContext:
        """
        Perform comprehensive market analysis
        
        Args:
            symbol: Trading symbol
            timeframe: Chart timeframe
            data: OHLCV data as pandas DataFrame
            
        Returns:
            MarketContext object with comprehensive market analysis
        """
        context = MarketContext(symbol, timeframe)
        
        # Analyze market structure
        structure_result = await self.market_structure.analyze(data)
        context.update(
            regime=structure_result.regime,
            trend_strength=structure_result.trend_strength,
            support_levels=structure_result.support_levels,
            resistance_levels=structure_result.resistance_levels
        )
        
        # Analyze liquidity
        liquidity_result = await self.liquidity.analyze(data)
        context.update(
            liquidity=liquidity_result.liquidity_score,
            key_levels=liquidity_result.key_levels
        )
        
        # Analyze order flow
        order_flow_result = await self.order_flow.analyze(data)
        context.update(
            buying_pressure=order_flow_result.buying_pressure,
            selling_pressure=order_flow_result.selling_pressure,
            imbalance=order_flow_result.imbalance
        )
        
        # Analyze microstructure
        micro_result = await self.microstructure.analyze(data)
        context.update(
            spread=micro_result.spread,
            depth=micro_result.depth,
            institutional_activity=micro_result.institutional_activity
        )
        
        # Analyze technical indicators
        tech_result = await self.technical.analyze(data)
        context.update(
            rsi=tech_result.rsi,
            macd=tech_result.macd,
            bollinger=tech_result.bollinger,
            moving_averages=tech_result.moving_averages
        )
        
        # Analyze volatility
        context.volatility = self._calculate_volatility(data)
        
        # Analyze sentiment (if available)
        try:
            sentiment_result = await self.sentiment.analyze(symbol)
            context.update(
                sentiment=sentiment_result.score,
                sentiment_sources=sentiment_result.sources
            )
        except Exception as e:
            logger.warning(f"Sentiment analysis failed: {e}")
        # Analyze fundamentals (if available)
            fundamental_result = await self.fundamental.analyze(symbol)
            context.update(
                fundamentals=fundamental_result.metrics
            )
        except Exception as e:
            logger.warning(f"Fundamental analysis failed: {e}")
        # Detect anomalies
            anomalies = await self.anomaly.detect(data)
            context.anomalies = anomalies
        except Exception as e:
            logger.warning(f"Anomaly detection failed: {e}")
        # Run predictive models
            prediction = await self.predictive.predict(symbol, data)
            context.update(
                price_prediction=prediction.price,
                prediction_confidence=prediction.confidence,
                prediction_horizon=prediction.horizon
            )
        except Exception as e:
            logger.warning(f"Predictive modeling failed: {e}")
        
        logger.info(f"Completed market analysis for {symbol} ({timeframe})")
        return context
    
    async def generate_signals(self, symbol: str, timeframe: str, 
                             data: pd.DataFrame) -> List[Signal]:
        """
        Generate trading signals from all analysis components
        
        Args:
            symbol: Trading symbol
            timeframe: Chart timeframe
            data: OHLCV data as pandas DataFrame
            
        Returns:
            List of Signal objects with confidence scores
        """
        # First analyze the market to get context
        context = await self.analyze_market(symbol, timeframe, data)
        
        # Collect signals from all components
        all_signals = []
        
        # Market structure signals
        structure_signals = await self.market_structure.generate_signals(data, context)
        all_signals.extend([
            Signal(
                symbol=symbol,
                direction=s.direction,
                size=s.size,
                source="market_structure",
                confidence=s.confidence,
                metadata={"type": s.type, "urgency": s.urgency}
            ) for s in structure_signals
        ])
        
        # Liquidity signals
        liquidity_signals = await self.liquidity.generate_signals(data, context)
        all_signals.extend([
            Signal(
                symbol=symbol,
                direction=s.direction,
                size=s.size,
                source="liquidity",
                confidence=s.confidence,
                metadata={"zone_type": s.zone_type, "urgency": s.urgency}
            ) for s in liquidity_signals
        ])
        
        # Order flow signals
        order_flow_signals = await self.order_flow.generate_signals(data, context)
        all_signals.extend([
            Signal(
                symbol=symbol,
                direction=s.direction,
                size=s.size,
                source="order_flow",
                confidence=s.confidence,
                metadata={"imbalance": s.imbalance, "urgency": s.urgency}
            ) for s in order_flow_signals
        ])
        
        # Technical indicator signals
        tech_signals = await self.technical.generate_signals(data, context)
        all_signals.extend([
            Signal(
                symbol=symbol,
                direction=s.direction,
                size=s.size,
                source="technical",
                confidence=s.confidence,
                metadata={"indicator": s.indicator, "urgency": s.urgency}
            ) for s in tech_signals
        ])
        
        # Price action signals
        price_signals = await self.price_action.generate_signals(data, context)
        all_signals.extend([
            Signal(
                symbol=symbol,
                direction=s.direction,
                size=s.size,
                source="price_action",
                confidence=s.confidence,
                metadata={"pattern": s.pattern, "urgency": s.urgency}
            ) for s in price_signals
        ])
        
        # Sentiment signals (if available)
        try:
            sentiment_signals = await self.sentiment.generate_signals(symbol, context)
            all_signals.extend([
                Signal(
                    symbol=symbol,
                    direction=s.direction,
                    size=s.size,
                    source="sentiment",
                    confidence=s.confidence,
                    metadata={"sentiment_type": s.type, "urgency": s.urgency}
                ) for s in sentiment_signals
            ])
        except Exception as e:
            logger.warning(f"Sentiment signal generation failed: {e}")
        # Predictive model signals
            predictive_signals = await self.predictive.generate_signals(symbol, data, context)
            all_signals.extend([
                Signal(
                    symbol=symbol,
                    direction=s.direction,
                    size=s.size,
                    source="predictive",
                    confidence=s.confidence,
                    metadata={"model": s.model, "urgency": s.urgency}
                ) for s in predictive_signals
            ])
        except Exception as e:
            logger.warning(f"Predictive signal generation failed: {e}")
        
        # Filter signals by minimum confidence
        filtered_signals = [s for s in all_signals if s.confidence >= self.min_confidence]
        
        # Resolve conflicts and aggregate signals
        final_signals = self._resolve_conflicts(filtered_signals, context)
        
        # Store signals in history
        self._update_signal_history(symbol, final_signals)
        
        logger.info(f"Generated {len(final_signals)} signals for {symbol} ({timeframe})")
        return final_signals
    
    def _resolve_conflicts(self, signals: List[Signal], 
                          context: MarketContext) -> List[Signal]:
        """
        Resolve conflicting signals and aggregate similar ones
        
        Args:
            signals: List of signals to process
            context: Current market context
            
        Returns:
            List of resolved and aggregated signals
        """
        if not signals:
            return []
        
        # Group signals by direction
        buy_signals = [s for s in signals if s.direction > 0]
        sell_signals = [s for s in signals if s.direction < 0]
        neutral_signals = [s for s in signals if s.direction == 0]
        
        # Calculate weighted confidence for each direction
        buy_confidence = self._calculate_weighted_confidence(buy_signals)
        sell_confidence = self._calculate_weighted_confidence(sell_signals)
        
        # Determine final signals based on confidence difference
        final_signals = []
        
        # Strong buy signal
        if buy_confidence > sell_confidence + 20:
            # Create aggregated buy signal
            final_signals.append(Signal(
                symbol=context.symbol,
                direction=1,
                size=self._calculate_position_size(buy_confidence, context),
                source="aggregated",
                confidence=buy_confidence,
                metadata={
                    "components": [s.source for s in buy_signals],
                    "context": {
                        "regime": context.regime,
                        "volatility": context.volatility,
                        "trend_strength": context.trend_strength
                    },
                    "urgency": self._calculate_urgency(buy_signals, context)
                }
            ))
        
        # Strong sell signal
        elif sell_confidence > buy_confidence + 20:
            # Create aggregated sell signal
            final_signals.append(Signal(
                symbol=context.symbol,
                direction=-1,
                size=self._calculate_position_size(sell_confidence, context),
                source="aggregated",
                confidence=sell_confidence,
                metadata={
                    "components": [s.source for s in sell_signals],
                    "context": {
                        "regime": context.regime,
                        "volatility": context.volatility,
                        "trend_strength": context.trend_strength
                    },
                    "urgency": self._calculate_urgency(sell_signals, context)
                }
            ))
        
        # Mixed signals or neutral
        else:
            # If there are strong individual signals, include them
            strong_signals = [s for s in signals if s.confidence > 80]
            if strong_signals:
                final_signals.extend(strong_signals)
            else:
                # Create neutral signal
                final_signals.append(Signal(
                    symbol=context.symbol,
                    direction=0,
                    size=0,
                    source="aggregated",
                    confidence=max(buy_confidence, sell_confidence),
                    metadata={
                        "reason": "conflicting_signals",
                        "buy_confidence": buy_confidence,
                        "sell_confidence": sell_confidence
                    }
                ))
        
        return final_signals
    
    def _calculate_weighted_confidence(self, signals: List[Signal]) -> float:
        """
        Calculate weighted confidence score for a group of signals
        
        Args:
            signals: List of signals to process
            
        Returns:
            Weighted confidence score (0-100)
        """
        if not signals:
            return 0.0
        
        total_weight = 0.0
        weighted_sum = 0.0
        
        for signal in signals:
            weight = self.signal_weights.get(signal.source, 0.1)
            weighted_sum += signal.confidence * weight
            total_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        return weighted_sum / total_weight
    
    def _calculate_position_size(self, confidence: float, 
                               context: MarketContext) -> float:
        """
        Calculate position size based on signal confidence and market context
        
        Args:
            confidence: Signal confidence (0-100)
            context: Current market context
            
        Returns:
            Recommended position size (0-1 scale)
        """
        # Base size on confidence
        base_size = (confidence - self.min_confidence) / (100 - self.min_confidence)
        base_size = max(0.0, min(1.0, base_size))
        
        # Adjust for volatility
        vol_factor = 1.0 - (context.volatility * 0.5)
        vol_factor = max(0.5, min(1.0, vol_factor))
        
        # Adjust for trend strength
        trend_factor = 0.5 + (context.trend_strength * 0.5)
        trend_factor = max(0.5, min(1.0, trend_factor))
        
        # Calculate final size
        final_size = base_size * vol_factor * trend_factor
        
        return round(final_size, 2)
    
    def _calculate_urgency(self, signals: List[Signal], 
                         context: MarketContext) -> float:
        """
        Calculate execution urgency based on signals and market context
        
        Args:
            signals: List of signals
            context: Current market context
            
        Returns:
            Urgency score (0-1)
        """
        if not signals:
            return 0.5  # Default medium urgency
        
        # Average signal urgency
        signal_urgencies = [s.metadata.get('urgency', 0.5) for s in signals]
        avg_signal_urgency = sum(signal_urgencies) / len(signal_urgencies)
        
        # Adjust for volatility
        volatility_factor = context.volatility
        
        # Adjust for liquidity
        liquidity_factor = 1.0 - context.liquidity
        
        # Calculate final urgency
        urgency = (avg_signal_urgency * 0.6) + (volatility_factor * 0.2) + (liquidity_factor * 0.2)
        
        return max(0.0, min(1.0, urgency))
    
    def _calculate_volatility(self, data: pd.DataFrame) -> float:
        """
        Calculate market volatility from price data
        
        Args:
            data: OHLCV data as pandas DataFrame
            
        Returns:
            Volatility score (0-1)
        """
        if len(data) < 20:
            return 0.5  # Default medium volatility
        
        # Calculate daily returns
        returns = data['close'].pct_change().dropna()
        
        # Calculate volatility (standard deviation of returns)
        volatility = returns.std()
        
        # Normalize to 0-1 scale (assuming max volatility is 5%)
        normalized_volatility = min(1.0, volatility * 20)
        
        return normalized_volatility
    
    def _update_signal_history(self, symbol: str, signals: List[Signal]):
        """
        Update signal history for a symbol
        
        Args:
            symbol: Trading symbol
            signals: New signals to add to history
        """
        if symbol not in self.signal_history:
            self.signal_history[symbol] = []
        
        # Add new signals to history
        self.signal_history[symbol].extend(signals)
        
        # Keep only last 100 signals
        if len(self.signal_history[symbol]) > 100:
            self.signal_history[symbol] = self.signal_history[symbol][-100:]
    
    def get_signal_history(self, symbol: str, limit: int = 20) -> List[Signal]:
        """
        Get recent signal history for a symbol
        
        Args:
            symbol: Trading symbol
            limit: Maximum number of signals to return
            
        Returns:
            List of recent signals
        """
        if symbol not in self.signal_history:
            return []
        
        return self.signal_history[symbol][-limit:]
    
    def calculate_risk_reward(self, symbol: str, direction: int, 
                            entry_price: float, context: MarketContext) -> Dict[str, float]:
        """
        Calculate risk/reward ratio for a potential trade
        
        Args:
            symbol: Trading symbol
            direction: Trade direction (1 for buy, -1 for sell)
            entry_price: Entry price
            context: Current market context
            
        Returns:
            Dictionary with risk/reward metrics
        """
        # Find nearest support/resistance levels
        if direction > 0:  # Buy trade
            # Support is below entry
            supports = [level for level in context.support_levels if level < entry_price]
            stop_level = max(supports) if supports else entry_price * 0.99
            
            # Resistance is above entry
            resistances = [level for level in context.resistance_levels if level > entry_price]
            target_level = min(resistances) if resistances else entry_price * 1.01
        else:  # Sell trade
            # Support is below entry
            supports = [level for level in context.support_levels if level < entry_price]
            target_level = max(supports) if supports else entry_price * 0.99
            
            # Resistance is above entry
            resistances = [level for level in context.resistance_levels if level > entry_price]
            stop_level = min(resistances) if resistances else entry_price * 1.01
        
        # Calculate risk and reward
        risk = abs(entry_price - stop_level)
        reward = abs(entry_price - target_level)
        
        # Calculate ratio
        ratio = reward / risk if risk > 0 else 0
        
        return {
            'entry_price': entry_price,
            'stop_level': stop_level,
            'target_level': target_level,
            'risk': risk,
            'reward': reward,
            'ratio': ratio
        }


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create orchestrator
    orchestrator = AnalysisOrchestrator()
    
    # Example data (would normally come from data feed)
    data = pd.DataFrame({
        'open': [100, 101, 102, 101, 103],
        'high': [102, 103, 104, 103, 105],
        'low': [99, 100, 101, 100, 102],
        'close': [101, 102, 101, 103, 104],
        'volume': [1000, 1200, 900, 1100, 1300]
    })
    
    # Run analysis
    async def test_analysis():
        context = await orchestrator.analyze_market("EURUSD", "H1", data)
        signals = await orchestrator.generate_signals("EURUSD", "H1", data)
        
        logger.info(f"Generated {len(signals)} signals")
        for signal in signals:
            print(signal)
            
        # Calculate risk/reward for first signal
        if signals:
            rr = orchestrator.calculate_risk_reward(
                "EURUSD", signals[0].direction, 1.1050, context
            )
            logger.info(f"Risk/Reward: {rr['ratio']:.2f} (Risk: {rr['risk']:.5f}, Reward: {rr['reward']:.5f})")
    
    # Run the test
    asyncio.run(test_analysis())
