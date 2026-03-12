"""
Elite Trading System - Main integration of all three pillars

This module integrates the Analysis, Execution, and Monitoring pillars
into a complete trading system.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime
import pandas as pd
import numpy as np
try:
    import yaml
except ImportError:
    yaml = None
import os
import json
from pathlib import Path

# Import pillar components
from trading_bot.core.analysis_orchestrator import AnalysisOrchestrator, Signal, MarketContext
from trading_bot.core.execution_manager import ExecutionManager, Order, OrderType, OrderStatus
from trading_bot.core.monitoring_system import MonitoringSystem

# Import data components
from trading_bot.data.market_data_stream import MarketDataStream
from trading_bot.data.time_series_db import TimeSeriesDB
import numpy
import pandas

logger = logging.getLogger(__name__)


class TradingSystem:
    """
    Elite Trading System that integrates all three pillars:
    Analysis, Execution, and Monitoring.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the trading system
        
        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize components
        self.data_stream = MarketDataStream(self.config.get('data_stream', {}))
        self.time_series_db = TimeSeriesDB(self.config.get('time_series_db', {}))
        
        self.analysis = AnalysisOrchestrator(self.config.get('analysis', {}))
        self.execution = ExecutionManager(self.config.get('execution', {}))
        self.monitoring = MonitoringSystem(self.config.get('monitoring', {}))
        
        # Trading parameters
        self.symbols = self.config.get('symbols', ['EURUSD'])
        self.timeframes = self.config.get('timeframes', ['M15'])
        self.trading_hours = self.config.get('trading_hours', {
            'start': '00:00',
            'end': '23:59',
            'timezone': 'UTC',
            'weekend_trading': False
        })
        
        # System state
        self.running = False
        self.paused = False
        self.last_update = {}
        self.market_data = {}
        
        # Event loop and tasks
        self.loop = None
        self.tasks = {}
        
        logger.info("Trading system initialized")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """
        Load configuration from file
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        default_config = {
            'symbols': ['EURUSD'],
            'timeframes': ['M15'],
            'data_update_interval': 1.0,  # seconds
            'analysis_interval': 5.0,  # seconds
            'trading_enabled': True,
            'risk_per_trade': 1.0,  # percent
            'max_open_trades': 5,
            'trading_hours': {
                'start': '00:00',
                'end': '23:59',
                'timezone': 'UTC',
                'weekend_trading': False
            }
        }
        
        if not config_path:
            logger.info("No configuration file provided, using defaults")
            return default_config
        try:
        
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                logger.info(f"Configuration loaded from {config_path}")
                
                # Merge with defaults
                merged_config = {**default_config, **config}
                return merged_config
                
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return default_config
    
    async def start(self) -> None:
        """Start the trading system"""
        if self.running:
            logger.warning("Trading system already running")
            return
        
        logger.info("Starting trading system")
        self.running = True
        self.paused = False
        
        # Store event loop
        self.loop = asyncio.get_running_loop()
        
        # Start data stream
        await self.data_stream.connect()
        
        # Subscribe to symbols
        for symbol in self.symbols:
            await self.data_stream.subscribe(symbol)
        
        # Start tasks
        self.tasks['data_update'] = asyncio.create_task(self._data_update_loop())
        self.tasks['analysis'] = asyncio.create_task(self._analysis_loop())
        self.tasks['monitoring'] = asyncio.create_task(self._monitoring_loop())
        
        # Update system status
        self.monitoring.update_component_status('system', 'ok', {'state': 'running'})
        
        logger.info("Trading system started")
    
    async def stop(self) -> None:
        """Stop the trading system"""
        if not self.running:
            logger.warning("Trading system not running")
            return
        
        logger.info("Stopping trading system")
        self.running = False
        
        # Cancel tasks
        for name, task in self.tasks.items():
            if not task.done():
                task.cancel()
        
        # Wait for tasks to complete
        for name, task in self.tasks.items():
            try:
                await task
            except asyncio.CancelledError:
                logger.info(f"Task {name} cancelled")
        
        # Close data stream
        await self.data_stream.disconnect()
        
        # Update system status
        self.monitoring.update_component_status('system', 'ok', {'state': 'stopped'})
        
        logger.info("Trading system stopped")
    
    async def pause(self) -> None:
        """Pause trading"""
        if not self.running:
            logger.warning("Trading system not running")
            return
        
        if self.paused:
            logger.warning("Trading already paused")
            return
        
        logger.info("Pausing trading")
        self.paused = True
        
        # Update system status
        self.monitoring.update_component_status('system', 'ok', {'state': 'paused'})
        
        logger.info("Trading paused")
    
    async def resume(self) -> None:
        """Resume trading"""
        if not self.running:
            logger.warning("Trading system not running")
            return
        
        if not self.paused:
            logger.warning("Trading not paused")
            return
        
        logger.info("Resuming trading")
        self.paused = False
        
        # Update system status
        self.monitoring.update_component_status('system', 'ok', {'state': 'running'})
        
        logger.info("Trading resumed")
    
    async def _data_update_loop(self) -> None:
        """Background task for updating market data"""
        logger.info("Data update loop started")
        
        update_interval = self.config.get('data_update_interval', 1.0)
        
        while self.running:
            try:
                # Update market data for each symbol and timeframe
                for symbol in self.symbols:
                    # Get latest tick data
                    tick_data = await self.data_stream.get_latest_tick(symbol)
                    
                    if tick_data:
                        # Store tick data
                        if symbol not in self.market_data:
                            self.market_data[symbol] = {'tick': None, 'ohlcv': {}}
                        
                        self.market_data[symbol]['tick'] = tick_data
                        
                        # Update last price in execution manager
                        await self.execution.update_market_price(symbol, tick_data['bid'])
                        
                        # Update last update time
                        self.last_update[symbol] = datetime.now()
                        
                        # Update OHLCV data for each timeframe
                        for timeframe in self.timeframes:
                            # Get OHLCV data
                            ohlcv_data = await self.data_stream.get_ohlcv(symbol, timeframe, 200)
                            
                            if ohlcv_data is not None:
                                # Store OHLCV data
                                self.market_data[symbol]['ohlcv'][timeframe] = ohlcv_data
                                
                                # Store in time series database
                                await self.time_series_db.store(symbol, timeframe, ohlcv_data)
                
                # Update data feed status
                self.monitoring.update_component_status('data_feed', 'ok', {
                    'last_update': datetime.now(),
                    'symbols': list(self.last_update.keys())
                })
                
            except Exception as e:
                logger.error(f"Error in data update loop: {e}")
                self.monitoring.update_component_status('data_feed', 'error', {
                    'error': str(e),
                    'last_update': datetime.now()
                })
                self.monitoring.add_error('data_feed', 'update_error', str(e))
            
            # Sleep until next update
            await asyncio.sleep(update_interval)
    
    async def _analysis_loop(self) -> None:
        """Background task for market analysis and signal generation"""
        logger.info("Analysis loop started")
        
        analysis_interval = self.config.get('analysis_interval', 5.0)
        
        while self.running:
            try:
                # Skip if trading is paused
                if self.paused:
                    await asyncio.sleep(analysis_interval)
                    continue
                
                # Process each symbol and timeframe
                for symbol in self.symbols:
                    if symbol not in self.market_data:
                        continue
                    
                    for timeframe in self.timeframes:
                        if timeframe not in self.market_data[symbol]['ohlcv']:
                            continue
                        
                        # Get OHLCV data
                        ohlcv_data = self.market_data[symbol]['ohlcv'][timeframe]
                        
                        # Generate signals
                        signals = await self.analysis.generate_signals(symbol, timeframe, ohlcv_data)
                        
                        # Process signals
                        await self._process_signals(symbol, timeframe, signals)
                
                # Update analysis status
                self.monitoring.update_component_status('analysis', 'ok', {
                    'last_update': datetime.now()
                })
                
            except Exception as e:
                logger.error(f"Error in analysis loop: {e}")
                self.monitoring.update_component_status('analysis', 'error', {
                    'error': str(e),
                    'last_update': datetime.now()
                })
                self.monitoring.add_error('analysis', 'analysis_error', str(e))
            
            # Sleep until next analysis
            await asyncio.sleep(analysis_interval)
    
    async def _process_signals(self, symbol: str, timeframe: str, signals: List[Signal]) -> None:
        """
        Process trading signals
        
        Args:
            symbol: Trading symbol
            timeframe: Chart timeframe
            signals: List of trading signals
        """
        if not signals:
            return
        
        # Check if trading is enabled
        if not self.config.get('trading_enabled', True):
            logger.info(f"Trading disabled, ignoring {len(signals)} signals for {symbol}")
            return
        
        # Check trading hours
        if not self._is_within_trading_hours():
            logger.info(f"Outside trading hours, ignoring {len(signals)} signals for {symbol}")
            return
        
        # Check max open trades
        open_positions = self.execution.get_active_positions()
        if len(open_positions) >= self.config.get('max_open_trades', 5):
            logger.info(f"Max open trades reached, ignoring {len(signals)} signals for {symbol}")
            return
        
        # Process each signal
        for signal in signals:
            # Skip signals with zero direction (neutral)
            if signal.direction == 0:
                continue
            
            # Check if we already have a position for this symbol
            position = self.execution.get_position(symbol)
            if position and position.quantity != 0:
                # If signal is in opposite direction, close position
                if (position.quantity > 0 and signal.direction < 0) or (position.quantity < 0 and signal.direction > 0):
                    logger.info(f"Closing position for {symbol} based on signal: {signal}")
                    await self.execution.close_position(symbol)
                else:
                    logger.info(f"Already have position for {symbol}, ignoring signal: {signal}")
                continue
            
            # Calculate position size
            risk_pct = self.config.get('risk_per_trade', 1.0)
            position_size = self._calculate_position_size(symbol, risk_pct, signal.confidence / 100.0)
            
            # Determine order type
            order_type = OrderType.MARKET
            
            # Place order
            side = 'buy' if signal.direction > 0 else 'sell'
            
            logger.info(f"Placing {side} order for {symbol} based on signal: {signal}")
            
            order = await self.execution.place_order(
                symbol=symbol,
                order_type=order_type,
                side=side,
                quantity=position_size,
                urgency=signal.urgency,
                metadata={
                    'signal': {
                        'source': signal.source,
                        'confidence': signal.confidence,
                        'timeframe': timeframe
                    }
                }
            )
            
            logger.info(f"Order placed: {order.id}, Status: {order.status}")
    
    async def _monitoring_loop(self) -> None:
        """Background task for system monitoring"""
        logger.info("Monitoring loop started")
        
        monitoring_interval = self.config.get('monitoring_interval', 10.0)
        
        while self.running:
            try:
                # Get system status
                system_status = self.monitoring.get_system_status()
                
                # Check for critical issues
                if system_status['status'] == 'error':
                    logger.warning("System status is ERROR, pausing trading")
                    await self.pause()
                
                # Check data feed freshness
                now = datetime.now()
                for symbol, last_update in self.last_update.items():
                    if (now - last_update).total_seconds() > 60:
                        logger.warning(f"Data feed for {symbol} is stale")
                        self.monitoring.add_alert('warning', 'data_feed', f"Stale data for {symbol}")
                
                # Log system status
                logger.debug(f"System status: {system_status['status']}")
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
            
            # Sleep until next monitoring cycle
            await asyncio.sleep(monitoring_interval)
    
    def _is_within_trading_hours(self) -> bool:
        """
        Check if current time is within trading hours
        
        Returns:
            True if within trading hours
        """
        # Get trading hours from config
        trading_hours = self.config.get('trading_hours', {
            'start': '00:00',
            'end': '23:59',
            'timezone': 'UTC',
            'weekend_trading': False
        })
        
        # Get current time
        now = datetime.now()
        
        # Check weekend
        if not trading_hours.get('weekend_trading', False):
            if now.weekday() >= 5:  # Saturday or Sunday
                return False
        
        # Parse trading hours
        start_time = datetime.strptime(trading_hours.get('start', '00:00'), '%H:%M').time()
        end_time = datetime.strptime(trading_hours.get('end', '23:59'), '%H:%M').time()
        
        # Check if current time is within trading hours
        current_time = now.time()
        
        if start_time <= end_time:
            return start_time <= current_time <= end_time
        else:
            # Handle overnight trading hours
            return current_time >= start_time or current_time <= end_time
    
    def _calculate_position_size(self, symbol: str, risk_pct: float, confidence: float) -> float:
        """
        Calculate position size based on risk percentage and signal confidence
        
        Args:
            symbol: Trading symbol
            risk_pct: Risk percentage (0-100)
            confidence: Signal confidence (0-1)
            
        Returns:
            Position size
        """
        # This is a simplified calculation
        # In a real system, would consider account balance, leverage, stop loss, etc.
        base_size = 1.0
        
        # Adjust size based on risk percentage
        risk_factor = risk_pct / 1.0  # Normalize to 1% risk
        
        # Adjust size based on confidence
        confidence_factor = 0.5 + (confidence * 0.5)  # 0.5-1.0 range
        
        # Calculate final size
        position_size = base_size * risk_factor * confidence_factor
        
        # Round to appropriate precision
        position_size = round(position_size, 2)
        
        return position_size
    
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Get comprehensive data for dashboard
        
        Returns:
            Dictionary with system status, performance metrics, and market data
        """
        # Get monitoring data
        monitoring_data = self.monitoring.get_dashboard_data()
        
        # Get positions
        positions = self.execution.get_positions()
        
        # Get orders
        orders = self.execution.get_orders()
        
        # Get market data summary
        market_summary = {}
        for symbol in self.market_data:
            if 'tick' in self.market_data[symbol]:
                tick = self.market_data[symbol]['tick']
                market_summary[symbol] = {
                    'bid': tick['bid'],
                    'ask': tick['ask'],
                    'last_update': self.last_update.get(symbol, None)
                }
        
        # Combine all data
        return {
            'system': {
                'status': monitoring_data['system']['status'],
                'components': monitoring_data['system']['components'],
                'running': self.running,
                'paused': self.paused
            },
            'performance': monitoring_data['performance'],
            'positions': [
                {
                    'symbol': p.symbol,
                    'quantity': p.quantity,
                    'entry_price': p.entry_price,
                    'current_price': p.current_price,
                    'unrealized_pnl': p.unrealized_pnl,
                    'realized_pnl': p.realized_pnl
                }
                for p in positions
            ],
            'orders': [
                {
                    'id': o.id,
                    'symbol': o.symbol,
                    'type': o.order_type.value,
                    'side': o.side,
                    'quantity': o.quantity,
                    'price': o.price,
                    'status': o.status.value,
                    'filled_quantity': o.filled_quantity,
                    'created_at': o.created_at
                }
                for o in orders
            ],
            'market': market_summary,
            'alerts': monitoring_data['alerts']
        }


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create trading system
    trading_system = TradingSystem()
    
    # Run the system
    async def run_system():
        # Start the system
        await trading_system.start()
        
        try:
            # Run for a while
            await asyncio.sleep(60)
            
            # Get dashboard data
            dashboard_data = await trading_system.get_dashboard_data()
            logger.info("Dashboard Data:")
            print(json.dumps(dashboard_data, default=str, indent=2))
            
        finally:
            # Stop the system
            await trading_system.stop()
    
    # Run the example
    asyncio.run(run_system())
