import logging
"""Enhanced Adaptive Trading System Demo.

This demo showcases the complete enhanced adaptive trading system with:
    pass
- Advanced pattern recognition
- Real-time sentiment integration
- Market microstructure analysis
- All existing adaptive capabilities
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from loguru import logger
import yaml

from trading_bot.adaptive_systems import (
import numpy
import pandas

logger = logging.getLogger(__name__)

    AdaptiveTradingMaster,
    AdvancedPatternRecognizer,
    RealTimeSentimentEngine,
    MarketMicrostructureAnalyzer
)


class EnhancedAdaptiveDemo:
    pass
    """Enhanced demo showcasing all adaptive capabilities."""
    
    def __init__(self):
    pass
        """Initialize the enhanced demo."""
        self.master = None
        self.demo_data = None
        
    async def run_enhanced_demo(self):
    pass
        """Run the enhanced adaptive trading demo."""
        logger.info("🚀 Enhanced Adaptive Trading System Demo")
        logger.info("=" * 60)
        
        # Generate comprehensive demo data
        self.demo_data = self._generate_enhanced_data()
        
        # Initialize enhanced master controller
        config = self._get_enhanced_config()
        self.master = AdaptiveTradingMaster(config)
        
        # Start sentiment monitoring
        await self.master.sentiment_engine.start_real_time_monitoring(['EURUSD', 'GBPUSD'])
        
        # Start the system
        await self.master.start_system()
        
        # Run enhanced demo phases
        await self._demo_pattern_recognition()
        await self._demo_sentiment_integration()
        await self._demo_microstructure_analysis()
        await self._demo_integrated_decision_making()
        
        # Stop systems
        self.master.sentiment_engine.stop_monitoring()
        await self.master.stop_system()
        
        logger.info("🎉 Enhanced Demo Completed!")
    
    def _generate_enhanced_data(self) -> pd.DataFrame:
    pass
        """Generate enhanced market data with patterns and microstructure."""
        np.random.seed(42)
        
        # Generate base price data
        timestamps = pd.date_range(start=datetime.now() - timedelta(hours=48), 
                                 end=datetime.now(), freq='5min')
        
        prices = []
        volumes = []
        spreads = []
        
        base_price = 1.1000
        
        for i, ts in enumerate(timestamps):
    pass
            # Add pattern-based price movements
            if i % 100 == 0:  # Create patterns every 100 periods
                pattern_type = np.random.choice(['double_top', 'head_shoulders', 'triangle'])
                if pattern_type == 'double_top':
    pass
                    # Create double top pattern
                    for j in range(20):
    pass
                        if j < 5:
    pass
                            base_price += np.random.normal(0.001, 0.0005)
                        elif j < 10:
    pass
                            base_price += np.random.normal(-0.0005, 0.0003)
                        elif j < 15:
    pass
                            base_price += np.random.normal(0.0008, 0.0005)
                        else:
    pass
                            base_price += np.random.normal(-0.001, 0.0005)
            
            # Normal price movement
            base_price += np.random.normal(0, 0.0002)
            
            # Generate OHLCV
            volatility = 0.0001 + abs(np.sin(i / 50)) * 0.0005
            high = base_price + np.random.uniform(0, volatility)
            low = base_price - np.random.uniform(0, volatility)
            open_price = base_price + np.random.normal(0, volatility * 0.5)
            close = base_price
            
            # Volume with patterns
            base_volume = 1000
            if i % 50 == 0:  # Volume spikes
                volume = base_volume * np.random.uniform(3, 8)
            else:
    pass
                volume = base_volume * np.random.uniform(0.5, 2)
            
            # Bid-ask spread
            spread = 0.00001 + np.random.uniform(0, 0.00005)
            
            prices.append({
                'time': ts,
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume,
                'bid': close - spread/2,
                'ask': close + spread/2
            })
        
        df = pd.DataFrame(prices)
        df.set_index('time', inplace=True)
        
        logger.info(f"Generated enhanced data: {len(df)} periods")
        return df
    
    async def _demo_pattern_recognition(self):
    pass
        """Demo advanced pattern recognition."""
        logger.info("\n🔍 PATTERN RECOGNITION DEMO")
        logger.info("-" * 40)
        
        # Detect patterns in different timeframes
        timeframes = ['5min', '15min', '1H']
        
        for tf in timeframes:
    pass
            # Resample data for different timeframes
            if tf == '15min':
    pass
                data = self.demo_data.resample('15min').agg({
                    'open': 'first', 'high': 'max', 'low': 'min', 
                    'close': 'last', 'volume': 'sum'
                }).dropna()
            elif tf == '1H':
    pass
                data = self.demo_data.resample('1H').agg({
                    'open': 'first', 'high': 'max', 'low': 'min', 
                    'close': 'last', 'volume': 'sum'
                }).dropna()
            else:
    pass
                data = self.demo_data
            
            patterns = self.master.pattern_recognizer.detect_patterns(data, tf)
            
            logger.info(f"Timeframe {tf}: {len(patterns)} patterns detected")
            for pattern in patterns[:3]:  # Show top 3
                logger.info(f"  {pattern.pattern_type.value}: confidence={pattern.confidence:.2f}, "
                           f"strength={pattern.strength:.2f}")
    
    async def _demo_sentiment_integration(self):
    pass
        """Demo real-time sentiment integration."""
        logger.info("\n📊 SENTIMENT INTEGRATION DEMO")
        logger.info("-" * 40)
        
        # Simulate sentiment updates
        await asyncio.sleep(2)  # Let sentiment engine collect data
        
        symbols = ['EURUSD', 'GBPUSD']
        for symbol in symbols:
    pass
            sentiment = self.master.sentiment_engine.get_current_sentiment(symbol)
            logger.info(f"{symbol} Sentiment: score={sentiment.get('score', 0):.2f}, "
                       f"confidence={sentiment.get('confidence', 0):.2f}")
        
        # Show sentiment history
        history = self.master.sentiment_engine.get_sentiment_history('EURUSD', hours=1)
        logger.info(f"EURUSD sentiment history: {len(history)} data points")
    
    async def _demo_microstructure_analysis(self):
    pass
        """Demo market microstructure analysis."""
        logger.info("\n🏗️ MICROSTRUCTURE ANALYSIS DEMO")
        logger.info("-" * 40)
        
        # Analyze microstructure on recent data
        recent_data = self.demo_data.tail(100)
        
        # Create mock order book
        order_book = {
            'bids': [[recent_data['bid'].iloc[-1] - i*0.00001, 1000 + i*100] for i in range(10)],
            'asks': [[recent_data['ask'].iloc[-1] + i*0.00001, 1000 + i*100] for i in range(10)]
        }
        
        microstructure_signals = self.master.microstructure_analyzer.analyze_microstructure(
            recent_data, order_book
        )
        
        logger.info(f"Microstructure signals: {len(microstructure_signals)}")
        for signal in microstructure_signals[:3]:
    pass
            logger.info(f"  {signal.signal_type}: strength={signal.strength:.2f}, "
                       f"liquidity={signal.liquidity_score:.2f}")
        
        # Show institutional activity detection
        institutional = self.master.microstructure_analyzer.detect_institutional_activity(recent_data)
        logger.info(f"Institutional activity signals: {len(institutional)}")
    
    async def _demo_integrated_decision_making(self):
    pass
        """Demo integrated decision making with all systems."""
        logger.info("\n🎯 INTEGRATED DECISION MAKING DEMO")
        logger.info("-" * 40)
        
        # Make 5 trading decisions using all systems
        for i in range(5):
    pass
            # Prepare market data
            current_idx = -20 + i * 4
            data_slice = self.demo_data.iloc[current_idx-50:current_idx]
            
            market_data = {
                'symbol': 'EURUSD',
                'current_price': data_slice['close'].iloc[-1],
                'price_data': data_slice,
                'suggested_stop': data_slice['close'].iloc[-1] * 0.999,
                'volatility': data_slice['close'].pct_change().std(),
                'sentiment_score': self.master.sentiment_engine.get_current_sentiment('EURUSD').get('score', 0),
                'volume_ratio': data_slice['volume'].iloc[-1] / data_slice['volume'].mean()
            }
            
            # Get pattern signals
            patterns = self.master.pattern_recognizer.detect_patterns(data_slice.tail(30), '5min')
            pattern_signal = patterns[0] if patterns else None
            
            # Get microstructure signals
            order_book = {
                'bids': [[market_data['current_price'] - j*0.00001, 1000] for j in range(5)],
                'asks': [[market_data['current_price'] + j*0.00001, 1000] for j in range(5)]
            }
            
            micro_signals = self.master.microstructure_analyzer.analyze_microstructure(
                data_slice.tail(20), order_book
            )
            
            # Make integrated decision
            decision = await self.master.make_trading_decision(market_data)
            
            logger.info(f"Decision {i+1}:")
            logger.info(f"  Action: {decision.action} | Confidence: {decision.confidence:.2f}")
            logger.info(f"  Strategy: {decision.strategy.value} | Regime: {decision.regime.value}")
            logger.info(f"  Pattern: {pattern_signal.pattern_type.value if pattern_signal else 'None'}")
            logger.info(f"  Microstructure signals: {len(micro_signals)}")
            logger.info(f"  Sentiment: {market_data['sentiment_score']:.2f}")
            
            # Simulate outcome and record
            outcome = {
                'pnl': np.random.uniform(-20, 40),
                'duration_minutes': np.random.randint(30, 180),
                'max_drawdown': np.random.uniform(0, 15),
                'predicted_regime': decision.regime.value,
                'actual_regime': decision.regime.value
            }
            
            self.master.record_trade_outcome(decision, outcome)
            
            await asyncio.sleep(0.5)  # Brief pause between decisions
        
        # Final system status
        status = self.master.get_system_status()
        logger.info(f"\nFinal Status:")
        logger.info(f"  Total Trades: {status['trade_count']}")
        logger.info(f"  System Health: {status['health_status']['overall_status']}")
        logger.info(f"  Learning Insights: {status['learning_insights']}")
    
    def _get_enhanced_config(self) -> dict:
    pass
        """Get enhanced configuration."""
        return {
            'regime_detection': {'lookback_period': 20, 'confidence_threshold': 0.6},
            'risk_management': {'max_risk_per_trade': 0.02, 'max_total_risk': 0.1},
            'strategy_selection': {'performance_window': 50},
            'parameter_optimization': {'optimization_frequency': 100},
            'self_improvement': {'learning_rate': 0.1, 'pattern_threshold': 5},
            'adaptive_learning': {'retrain_frequency': 50},
            'feedback_system': {'feedback_window': 20},
            'meta_learning': {'discovery_threshold': 0.7},
            'health_monitor': {'check_frequency': 60},
            'pattern_recognition': {
                'min_pattern_length': 15,
                'max_pattern_length': 80,
                'confidence_threshold': 0.6
            },
            'sentiment_engine': {
                'update_interval': 30,
                'news_api_key': 'demo_key',
                'twitter_bearer_token': 'demo_token'
            },
            'microstructure': {
                'depth_levels': 10,
                'volume_window': 20,
                'spread_threshold': 0.00005
            }
        }


async def main():
    pass
    """Run the enhanced adaptive demo."""
    demo = EnhancedAdaptiveDemo()
    await demo.run_enhanced_demo()


if __name__ == "__main__":
    pass
    asyncio.run(main())
