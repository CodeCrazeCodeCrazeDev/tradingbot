"""
Example of optimized trading using the enhanced data pipeline
"""

import asyncio
from typing import Dict, Any
import logging
from datetime import datetime
import json

from trading_bot.database.data_streaming import MarketDataStream
from trading_bot.database.real_time_processor import DataProcessor
from trading_bot.database.market_microstructure import MarketMicrostructure
from trading_bot.database.order_flow_processor import OrderFlowProcessor
from trading_bot.database.analytics_processor import AnalyticsProcessor
from trading_bot.database.signal_processor import SignalProcessor
from trading_bot.database.timeseries_db import TimeSeriesDB
from typing import List

logger = logging.getLogger(__name__)

class OptimizedTradingSystem:
    """
    Trading system using optimized data pipeline
    Features:
    - Real-time data processing
    - Market microstructure analysis
    - Order flow analysis
    - ML-based predictions
    - Smart signal generation
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Initialize components
        self.market_stream = MarketDataStream(config)
        self.data_processor = DataProcessor(config)
        self.microstructure = MarketMicrostructure(config)
        self.order_flow = OrderFlowProcessor(config)
        self.analytics = AnalyticsProcessor(config)
        self.signal_processor = SignalProcessor(config)
        self.db = TimeSeriesDB(config)
        
        # Trading state
        self.active_trades = {}
        self.pending_orders = {}
        self.trade_history = []
        
        logger.info("Optimized trading system initialized")
    
    async def initialize(self):
        """Initialize all components"""
        await self.market_stream.initialize()
        await self.db.initialize()
        
        # Add data processors
        self.data_processor.add_processor('MARKET', self._process_market_data)
        self.data_processor.add_processor('TRADES', self._process_trades)
        
        logger.info("All components initialized")
    
    async def start_trading(self, symbols: List[str]):
        """Start trading for given symbols"""
        for symbol in symbols:
            # Create data streams
            await self.market_stream.create_stream(f"{symbol}_market")
            await self.market_stream.create_stream(f"{symbol}_trades")
            
            logger.info(f"Started trading {symbol}")
        
        # Start processing loop
        asyncio.create_task(self._processing_loop(symbols))
    
    async def _processing_loop(self, symbols: List[str]):
        """Main processing loop"""
        while True:
            try:
                for symbol in symbols:
                    # Get latest market data
                    market_data = await self._get_market_data(symbol)
                    if not market_data:
                        continue
                    
                    # Process through pipeline
                    await self._process_symbol(symbol, market_data)
                
                # Short sleep to prevent CPU overload
                await asyncio.sleep(0.001)  # 1ms delay
                
            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
                await asyncio.sleep(1)
    
    async def _process_symbol(self, symbol: str, market_data: Dict[str, Any]):
        """Process single symbol"""
        try:
            # Step 1: Process market microstructure
            micro_analysis = await self.microstructure.process_trade(
                symbol, market_data
            )
            
            # Step 2: Process order flow
            flow_signal = await self.order_flow.process_tick(
                symbol, market_data
            )
            
            # Step 3: Generate analytics
            analytics = await self.analytics.process_data(
                symbol, market_data, flow_signal, micro_analysis
            )
            
            # Step 4: Generate trading signals
            signal = await self.signal_processor.process_analytics(
                symbol, analytics, market_data
            )
            
            if signal:
                # Execute trading signal
                await self._execute_signal(signal)
            
            # Store processed data
            await self._store_data(symbol, {
                'market_data': market_data,
                'micro_analysis': micro_analysis,
                'flow_signal': flow_signal,
                'analytics': analytics,
                'signal': signal
            })
            
        except Exception as e:
            logger.error(f"Error processing {symbol}: {e}")
    
    async def _execute_signal(self, signal: TradingSignal):
        """Execute trading signal"""
        # Validate signal
        if not self._validate_trade(signal):
            return
        
        # Create order
        order = {
            'symbol': signal.symbol,
            'direction': signal.direction,
            'size': signal.size,
            'entry_price': signal.entry_price,
            'stop_loss': signal.stop_loss,
            'take_profit': signal.take_profit,
            'signal_type': signal.signal_type,
            'timestamp': datetime.now()
        }
        
        # Store pending order
        order_id = f"{signal.symbol}_{datetime.now().timestamp()}"
        self.pending_orders[order_id] = order
        
        logger.info(f"Executing signal: {json.dumps(order, default=str)}")
        
        # Execute order (implementation depends on broker)
        try:
            # Place order here
            execution_result = await self._place_order(order)
            
            if execution_result['success']:
                # Update trade tracking
                self.active_trades[order_id] = {
                    'order': order,
                    'execution': execution_result,
                    'signal': signal
                }
                
                logger.info(f"Order executed: {order_id}")
            else:
                logger.warning(f"Order failed: {order_id}")
            
        except Exception as e:
            logger.error(f"Error executing order: {e}")
    
    def _validate_trade(self, signal: TradingSignal) -> bool:
        """Validate trade before execution"""
        # Check existing exposure
        symbol_exposure = self._get_symbol_exposure(signal.symbol)
        max_exposure = self.config.get('max_symbol_exposure', 100000)
        
        if symbol_exposure + signal.size > max_exposure:
            logger.warning(f"Trade exceeds max exposure for {signal.symbol}")
            return False
        
        # Check risk limits
        risk_amount = abs(signal.entry_price - signal.stop_loss) * signal.size
        max_risk = self.config.get('max_risk_per_trade', 1000)
        
        if risk_amount > max_risk:
            logger.warning(f"Trade exceeds max risk: {risk_amount} > {max_risk}")
            return False
        
        # Check signal quality
        if signal.confidence < 0.8:
            logger.warning(f"Signal confidence too low: {signal.confidence}")
            return False
        
        return True
    
    def _get_symbol_exposure(self, symbol: str) -> float:
        """Get current exposure for symbol"""
        exposure = 0.0
        
        for trade in self.active_trades.values():
            if trade['order']['symbol'] == symbol:
                exposure += trade['order']['size']
        
        return exposure
    
    async def _store_data(self, symbol: str, data: Dict[str, Any]):
        """Store processed data"""
        try:
            # Store in time series database
            await self.db.write_market_data(
                symbol=symbol,
                data=data['market_data'],
                timeframe='1m'
            )
            
            # Store analytics
            if data.get('analytics'):
                await self.db.write_market_data(
                    symbol=symbol,
                    data={
                        'timestamp': datetime.now(),
                        'analytics': data['analytics']
                    },
                    timeframe='analytics'
                )
            
            # Store signals
            if data.get('signal'):
                await self.db.write_market_data(
                    symbol=symbol,
                    data={
                        'timestamp': datetime.now(),
                        'signal': data['signal']
                    },
                    timeframe='signals'
                )
                
        except Exception as e:
            logger.error(f"Error storing data: {e}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics"""
        return {
            'data_pipeline': {
                'stream': self.market_stream.get_metrics(),
                'processor': self.data_processor.get_stats(),
                'database': self.db.get_metrics()
            },
            'analysis': {
                'analytics': self.analytics.get_analytics_metrics(),
                'signals': self.signal_processor.get_signal_metrics()
            },
            'trading': {
                'active_trades': len(self.active_trades),
                'pending_orders': len(self.pending_orders),
                'total_trades': len(self.trade_history)
            }
        }
    
    async def cleanup(self):
        """Cleanup system resources"""
        await self.market_stream.cleanup()
        await self.data_processor.cleanup()
        await self.analytics.cleanup()
        await self.db.cleanup()
        logger.info("System cleanup completed")
