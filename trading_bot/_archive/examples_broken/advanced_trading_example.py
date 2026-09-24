import logging
#!/usr/bin/env python
"""
Advanced Trading Bot Example

This example demonstrates how to use all the advanced features of the trading bot:
    pass
- ML-enhanced strategy engine
- Execution optimization algorithms
- Emotional state tracking
- Enhanced performance analytics

This script provides a programmatic way to use these features rather than
using command-line arguments with main.py.
"""
import sys
import os
import datetime as dt
import pandas as pd
from loguru import logger

# Add parent directory to path to allow importing modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

# Import trading bot modules
from trading_bot.data import MT5Interface
from trading_bot.strategy.ml_strategy import MLStrategyEngine
from trading_bot.execution.paper_executor import PaperExecutor
from trading_bot.execution.algorithms import TWAPExecutor, VWAPExecutor, SmartOrderRouter
from trading_bot.risk import RiskManager
from trading_bot.analytics.emotional_tracker import EmotionalStateTracker
from trading_bot.analytics.enhanced_performance import EnhancedPerformanceAnalytics
from trading_bot.ml.sentiment import SentimentAnalyzer


def setup_logger():
    pass
    """Configure logger."""
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    logger.add(
        "logs/advanced_trading_{time}.log",
        rotation="500 MB",
        retention="10 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG"
    )


def run_advanced_trading_session(
    symbol="EURUSD",
    timeframe="M15",
    bars=300,
    use_ml=True,
    execution_algo="smart",
    track_emotions=True,
    use_sentiment=True
):
    pass
    """
    Run an advanced trading session with all features.
    
    Args:
    pass
        symbol: Trading symbol (e.g., EURUSD)
        timeframe: MT5 timeframe key (M1, M5, M15, H1, etc.)
        bars: Number of historical bars to fetch
        use_ml: Whether to use ML-enhanced strategy
        execution_algo: Execution algorithm to use (default, twap, vwap, smart)
        track_emotions: Whether to track emotional states
        use_sentiment: Whether to use sentiment analysis
    """
    logger.info(f"Starting advanced trading session for {symbol} on {timeframe} timeframe")
    
    # Connect to MT5
    mt5 = MT5Interface()
    if not mt5.connect():
    pass
        logger.error("Failed to connect to MT5. Please check your credentials.")
        return
    
    logger.info("Connected to MT5 successfully")
    
    # Initialize risk manager
    risk = RiskManager(mt5)
    
    # Initialize emotional tracker if enabled
    emotional_tracker = None
    if track_emotions:
    pass
        logger.info("Initializing emotional state tracking")
        emotional_tracker = EmotionalStateTracker()
    
    # Initialize strategy engine
    if use_ml:
    pass
        logger.info("Initializing ML-enhanced strategy engine")
        strategy = MLStrategyEngine(
            mt5,
            symbol=symbol,
            use_price_prediction=True,
            use_pattern_recognition=True,
            use_sentiment=use_sentiment
        )
        
        if use_sentiment:
    pass
            logger.info("Initializing sentiment analyzer")
            sentiment_analyzer = SentimentAnalyzer()
            strategy.sentiment_analyzer = sentiment_analyzer
    else:
    pass
        from trading_bot.strategy.strategy_engine import StrategyEngine
        logger.info("Initializing traditional strategy engine")
        strategy = StrategyEngine(mt5, symbol=symbol)
    
    # Get historical data
    logger.info(f"Fetching {bars} historical bars for {symbol} on {timeframe} timeframe")
    df = mt5.get_ohlc(symbol, timeframe, bars)
    if df is None or df.empty:
    pass
        logger.error("Failed to retrieve historical data")
        return
    
    logger.info(f"Retrieved {len(df)} bars of historical data")
    
    # Analyze market and generate signals
    logger.info("Analyzing market and generating trading signals")
    signals = strategy.analyse(df)
    
    if not signals:
    pass
        logger.info("No trading signals generated")
        return
    
    logger.info(f"Generated {len(signals)} trading signals")
    for i, signal in enumerate(signals):
    pass
        logger.info(f"Signal {i+1}: {signal.direction} {signal.symbol} with confidence {signal.confidence}%")
    
    # Initialize executor with selected algorithm
    logger.info(f"Initializing executor with {execution_algo} algorithm")
    base_executor = PaperExecutor(mt5, risk)
    
    if execution_algo == "twap":
    pass
        executor = TWAPExecutor(base_executor)
    elif execution_algo == "vwap":
    pass
        executor = VWAPExecutor(base_executor)
    elif execution_algo == "smart":
    pass
        executor = SmartOrderRouter(base_executor)
    else:
    pass
        executor = base_executor
    
    # Get current price
    current_price = mt5.get_current_price(symbol)
    logger.info(f"Current price for {symbol}: {current_price}")
    
    # Record emotional state before execution if tracking enabled
    if track_emotions:
    pass
        logger.info("Recording pre-execution emotional state")
        emotional_state = {
            'confidence': 0.7,  # Example values - in a real system these would be measured
            'fear': 0.3,
            'excitement': 0.5,
            'doubt': 0.4
        }
        emotional_tracker.record_state(emotional_state)
    
    # Execute signals
    logger.info("Executing trading signals")
    trades = executor.process(signals, current_price)
    
    if not trades:
    pass
        logger.info("No trades were executed")
        return
    
    logger.info(f"Executed {len(trades)} trades")
    
    # Record emotional state after execution if tracking enabled
    if track_emotions:
    pass
        logger.info("Recording post-execution emotional state")
        emotional_state = {
            'confidence': 0.6,  # Example values
            'fear': 0.4,
            'excitement': 0.7,
            'satisfaction': 0.5
        }
        emotional_tracker.record_state(emotional_state)
    
    # Generate performance analytics
    logger.info("Generating performance analytics")
    if track_emotions:
    pass
        analytics = EnhancedPerformanceAnalytics(trades, emotional_tracker)
        summary = analytics.summary()
        
        logger.info("Performance Summary with Emotional Insights:")
        logger.info(f"Trades: {summary['trades']}")
        logger.info(f"Win Rate: {summary['win_rate']:.2%}")
        logger.info(f"Net Profit: {summary['net_profit']}")
        
        if 'emotional_impact' in summary:
    pass
            logger.info("Emotional Impact Analysis:")
            for emotion, data in summary['emotional_impact'].items():
    pass
                logger.info(f"  {emotion.capitalize()}: correlation {data['correlation']:.2f}")
        
        if 'recommendations' in summary:
    pass
            logger.info("Recommendations:")
            for rec in summary['recommendations']:
    pass
                logger.info(f"  - {rec}")
    else:
    pass
        from trading_bot.analytics.performance import PerformanceAnalytics
import datetime
import pandas

logger = logging.getLogger(__name__)

        analytics = PerformanceAnalytics(trades)
        summary = analytics.summary()
        
        logger.info("Performance Summary:")
        logger.info(f"Trades: {summary['trades']}")
        logger.info(f"Win Rate: {summary['win_rate']:.2%}")
        logger.info(f"Net Profit: {summary['net_profit']}")
    
    logger.info("Advanced trading session completed")
    return summary


if __name__ == "__main__":
    pass
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Setup logger
    setup_logger()
    
    # Run trading session with all features enabled
    run_advanced_trading_session(
        symbol="EURUSD",
        timeframe="M15",
        bars=300,
        use_ml=True,
        execution_algo="smart",
        track_emotions=True,
        use_sentiment=True
    )
