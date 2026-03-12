"""
Optimized Data Pipeline Integration
Connects the optimized data pipeline with the original trading bot architecture
"""

import asyncio
from typing import Any, Dict, List, Optional
import logging
from datetime import datetime

# Import original trading bot components
try:
    from trading_bot.strategy.strategy_engine import StrategyEngine
except ImportError:
    StrategyEngine = None

try:
    from trading_bot.strategy import MLStrategyEngine
except ImportError:
    MLStrategyEngine = None

try:
    from trading_bot.execution import PaperExecutor, TWAPExecutor, VWAPExecutor, SmartOrderRouter
except ImportError:
    PaperExecutor = TWAPExecutor = VWAPExecutor = SmartOrderRouter = None

try:
    from trading_bot.execution.live_executor import LiveExecutor
except ImportError:
    LiveExecutor = None

try:
    from trading_bot.analytics import PerformanceAnalytics
except ImportError:
    PerformanceAnalytics = None

try:
    from trading_bot.data import MT5Interface
except ImportError:
    MT5Interface = None

# Import optimized data pipeline components
from trading_bot.database.data_streaming import MarketDataStream
from trading_bot.database.real_time_processor import DataProcessor
from trading_bot.database.market_microstructure import MarketMicrostructure
from trading_bot.database.order_flow_processor import OrderFlowProcessor
from trading_bot.database.analytics_processor import AnalyticsProcessor
from trading_bot.database.signal_processor import SignalProcessor
from trading_bot.database.timeseries_db import TimeSeriesDB
from trading_bot.database.pipeline_monitor import PipelineMonitor

# Import opportunity scanner
from trading_bot.opportunity_scanner.scanner_interface import UnifiedScanner

# Import trading engine
from trading_bot.trading_engine import TradingEngine

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        """
        decorator function.

    Args:
        func: Description

    Returns:
        Result of operation
        """
        async def wrapper(*args, **kwargs):
            """
            wrapper function.

    Auto-documented by QwenCodeMender.
            """
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator



logger = logging.getLogger(__name__)

class OptimizedIntegration:
    """
    Integrates the optimized data pipeline with the original trading bot
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Initialize original components
        self.mt5_interface = MT5Interface(
            config.get('symbol', 'EURUSD'),
            config.get('timeframe', 'M15')
        )
        
        # Initialize strategy engine based on config
        if config.get('use_ml', False):
            self.strategy_engine = MLStrategyEngine(config)
        else:
            self.strategy_engine = StrategyEngine(config)
        
        # Initialize executor based on config
        self.executor = self._create_executor(config)
        
        # Initialize analytics
        self.analytics = PerformanceAnalytics()
        
        # Initialize optimized components
        self.trading_engine = None
        
        logger.info("Optimized integration initialized")
    
    def _create_executor(self, config: Dict[str, Any]):
        """Create appropriate executor based on config"""
        mode = config.get('mode', 'paper')
        algo = config.get('execution_algo', 'simple')
        
        if mode == 'live':
            return LiveExecutor(config)
        elif algo == 'twap':
            return TWAPExecutor(config)
        elif algo == 'vwap':
            return VWAPExecutor(config)
        elif algo == 'smart':
            return SmartOrderRouter(config)
        else:
            return PaperExecutor(config)
    
    async def initialize(self):
        """Initialize all components"""
        # Initialize MT5 interface
        await self.mt5_interface.connect()
        
        # Initialize optimized trading engine
        self.trading_engine = TradingEngine(self.config)
        await self.trading_engine.initialize()
        
        logger.info("All components initialized")
    
    async def run(self, symbols: List[str]):
        """Run the integrated trading system"""
        # Start optimized trading engine
        await self.trading_engine.start_trading(symbols)
        
        # Connect original strategy engine to optimized data pipeline
        await self._connect_strategy_to_pipeline()
        
        # Connect original executor to optimized signal processor
        await self._connect_executor_to_signals()
        
        logger.info("Integrated trading system running")
    
    async def _connect_strategy_to_pipeline(self):
        """Connect original strategy engine to optimized data pipeline"""
        # Create task to forward market data to strategy engine
        asyncio.create_task(self._forward_market_data())
    
    async def _forward_market_data(self):
        """Forward market data from optimized pipeline to strategy engine"""
        while True:
            try:
                for symbol in self.trading_engine.symbols:
                    # Get latest market data from optimized pipeline
                    market_data = await self.trading_engine._get_market_data(symbol)
                    if not market_data:
                        continue
                    
                    # Convert to format expected by strategy engine
                    converted_data = self._convert_market_data(market_data)
                    
                    # Process with strategy engine
                    signals = self.strategy_engine.process_data(converted_data)
                    
                    # Forward signals to optimized pipeline
                    if signals:
                        await self._forward_signals_to_pipeline(signals, symbol)
                
                # Short sleep to prevent CPU overload
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error forwarding market data: {e}")
                await asyncio.sleep(1)
    
    def _convert_market_data(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert market data format between systems"""
        # Extract OHLCV data
        return {
            'symbol': market_data.get('symbol', ''),
            'timestamp': market_data.get('timestamp', datetime.now()),
            'open': market_data.get('open', 0),
            'high': market_data.get('high', 0),
            'low': market_data.get('low', 0),
            'close': market_data.get('close', market_data.get('price', 0)),
            'volume': market_data.get('volume', 0),
            'tick_volume': market_data.get('tick_volume', 0),
            'spread': market_data.get('spread', 0),
            'real_volume': market_data.get('real_volume', market_data.get('volume', 0))
        }
    
    async def _forward_signals_to_pipeline(self, signals: List[Dict[str, Any]], symbol: str):
        """Forward signals from strategy engine to optimized pipeline"""
        for signal in signals:
            # Convert to format expected by optimized pipeline
            converted_signal = {
                'symbol': symbol,
                'direction': signal.get('direction', 'buy'),
                'confidence': signal.get('strength', 0.5),
                'entry_price': signal.get('entry_price', 0),
                'stop_loss': signal.get('stop_loss', 0),
                'take_profit': signal.get('take_profit', 0),
                'timeframe': signal.get('timeframe', '5m'),
                'signal_type': signal.get('type', 'strategy')
            }
            
            # Process with optimized signal processor
            await self.trading_engine.signal_processor.process_analytics(
                symbol, converted_signal, await self.trading_engine._get_market_data(symbol)
            )
    
    async def _connect_executor_to_signals(self):
        """Connect original executor to optimized signal processor"""
        # Create task to forward signals to executor
        asyncio.create_task(self._forward_signals_to_executor())
    
    async def _forward_signals_to_executor(self):
        """Forward signals from optimized pipeline to executor"""
        while True:
            try:
                for symbol in self.trading_engine.symbols:
                    # Get active signals from optimized pipeline
                    signals = self.trading_engine.signal_processor.get_signal_metrics()
                    
                    # Forward to executor
                    for signal_type, metrics in signals.get('performance', {}).items():
                        if metrics.get('trades', 0) > 0 and metrics.get('win_rate', 0) > 0.5:
                            # This signal type is performing well, forward to executor
                            await self._execute_signal(signal_type, symbol)
                
                # Short sleep to prevent CPU overload
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error forwarding signals: {e}")
                await asyncio.sleep(1)
    
    async def _execute_signal(self, signal_type: str, symbol: str):
        """Execute signal with original executor"""
        # Get market data
        market_data = await self.trading_engine._get_market_data(symbol)
        if not market_data:
            return
        
        # Create order
        order = {
            'symbol': symbol,
            'type': 'MARKET',
            'volume': 0.1,  # Default size
            'price': market_data.get('price', 0),
            'sl': 0,  # Will be set by risk manager
            'tp': 0,  # Will be set by risk manager
            'comment': f"Optimized_{signal_type}"
        }
        
        # Execute order
        result = await self.executor.execute_order(order)
        
        # Log result
        if result.get('success', False):
            logger.info(f"Executed order: {order}")
        else:
            logger.warning(f"Failed to execute order: {order}")
    
    async def cleanup(self):
        """Cleanup all components"""
        # Cleanup MT5 interface
        await self.mt5_interface.disconnect()
        
        # Cleanup optimized trading engine
        if self.trading_engine:
            await self.trading_engine.cleanup()
        
        logger.info("All components cleaned up")
