"""
High-Performance Trading Engine
Integrates optimized data pipeline with opportunity scanners
"""

import asyncio
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import logging
from concurrent.futures import ThreadPoolExecutor
import yaml
import json
import time
from pathlib import Path

# Import psutil at module level for system metrics
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

# Import data pipeline components
from trading_bot.database.data_streaming import MarketDataStream
from trading_bot.database.real_time_processor import DataProcessor
from trading_bot.database.market_microstructure import MarketMicrostructure
from trading_bot.database.order_flow_processor import OrderFlowProcessor
from trading_bot.database.analytics_processor import AnalyticsProcessor
from trading_bot.database.signal_processor import SignalProcessor, TradingSignal
from trading_bot.database.timeseries_db import TimeSeriesDB
from trading_bot.database.pipeline_monitor import PipelineMonitor
from trading_bot.database.data_normalizer import DataNormalizer

# Import opportunity scanner
from trading_bot.opportunity_scanner.scanner_interface import UnifiedScanner, OpportunityData

# Import orchestrator components
from trading_bot.orchestrator.master_orchestrator import MasterOrchestrator
from trading_bot.orchestrator.execution_engine import ExecutionEngine
from trading_bot.orchestrator.risk_manager import PortfolioRiskManager as RiskManager

logger = logging.getLogger(__name__)

class TradingEngine:
    """
    High-performance trading engine with optimized data flow
    Features:
    - Real-time data processing
    - Parallel opportunity scanning
    - Advanced market analysis
    - Smart signal generation
    - Risk-managed execution
    - Performance monitoring
    """
    
    def __init__(self, config_path: str):
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize components
        self.market_stream = MarketDataStream(self.config.get('data_pipeline', {}).get('market_stream', {}))
        self.data_processor = DataProcessor(self.config.get('data_pipeline', {}).get('processor', {}))
        self.microstructure = MarketMicrostructure(self.config.get('analysis', {}).get('microstructure', {}))
        self.order_flow = OrderFlowProcessor(self.config.get('analysis', {}).get('order_flow', {}))
        self.analytics = AnalyticsProcessor(self.config.get('analysis', {}).get('analytics', {}))
        self.signal_processor = SignalProcessor(self.config.get('trading', {}))
        self.db = TimeSeriesDB(self.config.get('data_pipeline', {}).get('database', {}))
        self.monitor = PipelineMonitor(self.config.get('monitoring', {}))
        
        # Initialize scanner
        self.scanner = UnifiedScanner(self.config)
        
        # Initialize orchestrator components
        self.orchestrator = MasterOrchestrator(self.config.get('trading', {}))
        self.execution_engine = ExecutionEngine(self.config.get('trading', {}))
        self.risk_manager = RiskManager(self.config.get('trading', {}))
        
        # Connect components
        self.orchestrator.execution_engine = self.execution_engine
        self.orchestrator.risk_manager = self.risk_manager
        self.orchestrator.opportunity_scanner = self.scanner
        
        # Trading state
        self.active_trades = {}
        self.pending_orders = {}
        self.trade_history = []  # Bounded in _close_trade
        self.symbols = []
        self.running = False  # Control flag for graceful shutdown
        self._max_history_size = 10000  # Prevent unbounded growth
        
        # Performance metrics
        self.start_time = datetime.now()
        self.metrics = {
            'trades': 0,
            'wins': 0,
            'losses': 0,
            'total_pnl': 0.0,
            'max_drawdown': 0.0,
            'sharpe_ratio': 0.0,
            'processing_latency': []
        }
        
        # Thread pool for background tasks
        self.executor = ThreadPoolExecutor(
            max_workers=self.config.get('max_workers', 8)
        )
        self._shutdown_event = asyncio.Event()  # For graceful shutdown
        
        logger.info("Trading engine initialized")
    
    async def initialize(self):
        """Initialize all components"""
        # Initialize data pipeline
        await self.market_stream.initialize()
        await self.db.initialize()
        await self.monitor.initialize()
        
        # Initialize scanner
        await self.scanner.initialize(
            self.market_stream,
            self.data_processor,
            self.microstructure,
            self.order_flow
        )
        
        # Create data directory if needed
        Path("data").mkdir(exist_ok=True)
        
        logger.info("Trading engine components initialized")
    
    async def start_trading(self, symbols: List[str]):
        """Start trading for given symbols"""
        self.symbols = symbols
        self.running = True
        
        for symbol in symbols:
            # Create data streams
            await self.market_stream.create_stream(f"{symbol}_market")
            await self.market_stream.create_stream(f"{symbol}_trades")
            await self.market_stream.create_stream(f"{symbol}_orderbook")
            
            logger.info(f"Started trading {symbol}")
        
        # Start processing loops
        asyncio.create_task(self._data_processing_loop())
        asyncio.create_task(self._opportunity_scanning_loop())
        asyncio.create_task(self._signal_generation_loop())
        asyncio.create_task(self._execution_loop())
        asyncio.create_task(self._monitoring_loop())
        
        logger.info("All processing loops started")
    
    async def _data_processing_loop(self):
        """Main data processing loop"""
        while self.running:
            try:
                for symbol in self.symbols:
                    # Get latest market data
                    market_data = await self._get_market_data(symbol)
                    if not market_data:
                        continue
                    
                    # Process through pipeline
                    start_time = time.time()
                    
                    # Process market data
                    processed_data = await self.data_processor.process_market_data(
                        market_data, 'market_data'
                    )
                    
                    # Update metrics (bounded to prevent memory leak)
                    processing_time = time.time() - start_time
                    self.metrics['processing_latency'].append(processing_time)
                    if len(self.metrics['processing_latency']) > 10000:
                        self.metrics['processing_latency'] = self.metrics['processing_latency'][-5000:]
                    
                    # Record metrics
                    await self.monitor.record_metrics('data_processing', {
                        'latency': processing_time,
                        'throughput': 1.0 / processing_time if processing_time > 0 else 0,
                        'queue_size': len(self.market_stream.streams.get(f"{symbol}_market", []))
                    })
                
                # Short sleep to prevent CPU overload
                await asyncio.sleep(0.001)  # 1ms delay
                
            except Exception as e:
                logger.error(f"Error in data processing loop: {e}")
                await asyncio.sleep(1)
    
    async def _opportunity_scanning_loop(self):
        """Opportunity scanning loop"""
        while self.running:
            try:
                for symbol in self.symbols:
                    # Get latest market data
                    market_data = await self._get_market_data(symbol)
                    if not market_data:
                        continue
                    
                    # Scan for opportunities
                    opportunities = await self.scanner.scan_opportunities(
                        symbol, market_data
                    )
                    
                    if opportunities:
                        # Process opportunities through orchestrator
                        await self._process_opportunities(symbol, opportunities)
                
                # Scan at a reasonable frequency
                await asyncio.sleep(0.1)  # 100ms delay
                
            except Exception as e:
                logger.error(f"Error in opportunity scanning loop: {e}")
                await asyncio.sleep(1)
    
    async def _signal_generation_loop(self):
        """Signal generation loop"""
        while self.running:
            try:
                for symbol in self.symbols:
                    # Get latest market data and analytics
                    market_data = await self._get_market_data(symbol)
                    if not market_data:
                        continue
                    
                    # Get microstructure and order flow data
                    micro_data = self.microstructure.get_metrics(symbol)
                    flow_data = self.order_flow.get_order_flow_stats(symbol)
                    
                    # Generate analytics
                    analytics = await self.analytics.process_data(
                        symbol, market_data, flow_data, micro_data
                    )
                    
                    # Generate trading signals
                    signal = await self.signal_processor.process_analytics(
                        symbol, analytics, market_data
                    )
                    
                    if signal:
                        # Execute trading signal
                        await self._execute_signal(signal)
                
                # Generate signals at a reasonable frequency
                await asyncio.sleep(0.05)  # 50ms delay
                
            except Exception as e:
                logger.error(f"Error in signal generation loop: {e}")
                await asyncio.sleep(1)
    
    async def _execution_loop(self):
        """Order execution loop"""
        while self.running:
            try:
                # Process execution queue
                await self.orchestrator.execute_decisions()
                
                # Update trade status
                await self._update_trade_status()
                
                # Short sleep
                await asyncio.sleep(0.01)  # 10ms delay
                
            except Exception as e:
                logger.error(f"Error in execution loop: {e}")
                await asyncio.sleep(1)
    
    async def _monitoring_loop(self):
        """Performance monitoring loop"""
        while self.running:
            try:
                # Get system metrics
                metrics = self._get_system_metrics()
                
                # Log metrics
                logger.info(f"System metrics: {json.dumps(metrics, default=str)}")
                
                # Store metrics in dedicated performance_metrics table
                await self.db.write_performance_metric(
                    metric_type='system_metrics',
                    component='trading_engine',
                    value=metrics.get('trading', {}).get('total_pnl', 0),  # Example: total PnL
                    metadata=metrics
                )
                
                # Sleep for monitoring interval
                await asyncio.sleep(self.config.get('monitoring', {}).get('metrics_interval', 5))
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)
    
    async def _get_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get latest market data for symbol"""
        try:
            # Try to get from cache
            cached_data = await self.db.get_market_data(
                symbol=symbol,
                timeframe='1m',
                limit=1
            )
            
            if not cached_data.empty:
                # Convert to dict and normalize
                market_data = cached_data.iloc[0].to_dict()
                return DataNormalizer.normalize_market_data(market_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting market data for {symbol}: {e}")
            return None
    
    async def _process_opportunities(self, 
                                   symbol: str, 
                                   opportunities: List[OpportunityData]):
        """Process opportunities through orchestrator"""
        try:
            # Convert to orchestrator format
            orchestrator_opps = []
            
            for opp in opportunities:
                orchestrator_opps.append({
                    'unique_id': opp.id,
                    'symbol': opp.symbol,
                    'type': opp.type,
                    'direction': opp.direction,
                    'confidence': opp.confidence,
                    'expected_return': opp.expected_return,
                    'risk': opp.risk_score,
                    'entry_price': opp.entry_price,
                    'stop_loss': opp.stop_loss,
                    'take_profit': opp.take_profit,
                    'timeframe': opp.timeframe,
                    'gathered_at': opp.timestamp
                })
            
            # Get market data for orchestration
            market_data = await self._get_market_data(symbol)
            if not market_data:
                return
            
            # Process through orchestrator
            decisions = await self.orchestrator.orchestrate_trading({
                'symbol': symbol,
                'data': market_data,
                'opportunities': orchestrator_opps
            })
            
            # Log decisions
            if decisions:
                logger.info(f"Generated {len(decisions)} trading decisions for {symbol}")
            
        except Exception as e:
            logger.error(f"Error processing opportunities for {symbol}: {e}")
    
    async def _execute_signal(self, signal: TradingSignal):
        """Execute trading signal"""
        try:
            # Validate signal
            if not self._validate_signal(signal):
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
            
            # Execute through execution engine
            execution_result = await self.execution_engine.execute_order(order)
            
            if execution_result.get('success', False):
                # Update trade tracking
                self.active_trades[order_id] = {
                    'order': order,
                    'execution': execution_result,
                    'signal': signal,
                    'status': 'active',
                    'entry_time': datetime.now()
                }
                
                # Update metrics
                self.metrics['trades'] += 1
                
                logger.info(f"Order executed: {order_id}")
            else:
                logger.warning(f"Order failed: {order_id}")
            
        except Exception as e:
            logger.error(f"Error executing signal: {e}")
    
    def _validate_signal(self, signal: TradingSignal) -> bool:
        """Validate signal before execution"""
        # Check if signal is stale (older than 60 seconds)
        if hasattr(signal, 'timestamp') and signal.timestamp:
            signal_age = (datetime.now() - signal.timestamp).total_seconds()
            max_signal_age = self.config.get('trading', {}).get('max_signal_age_seconds', 60)
            if signal_age > max_signal_age:
                logger.warning(f"Signal too old: {signal_age:.1f}s > {max_signal_age}s")
                return False
        
        # Check market hours (basic check - can be enhanced per symbol)
        if not self._is_market_open(signal.symbol):
            logger.warning(f"Market closed for {signal.symbol}")
            return False
        
        # Check confidence
        if signal.confidence < self.config.get('trading', {}).get('min_signal_confidence', 0.8):
            return False
        
        # Check risk-reward ratio
        risk = abs(signal.entry_price - signal.stop_loss)
        reward = abs(signal.entry_price - signal.take_profit)
        min_rr = self.config.get('trading', {}).get('min_reward_ratio', 1.5)
        
        if risk == 0 or reward / risk < min_rr:
            return False
        
        # Check existing exposure
        symbol_exposure = self._get_symbol_exposure(signal.symbol)
        max_exposure = self.config.get('trading', {}).get('max_symbol_exposure', 100000)
        
        if symbol_exposure + signal.size > max_exposure:
            return False
        
        return True
    
    def _is_market_open(self, symbol: str) -> bool:
        """Check if market is open for the given symbol."""
        now = datetime.utcnow()
        
        # Crypto markets are 24/7
        if 'USDT' in symbol or 'BTC' in symbol or 'ETH' in symbol:
            return True
        
        # Forex markets: Sunday 5pm EST to Friday 5pm EST
        # Simplified check - weekday only
        if now.weekday() >= 5:  # Saturday or Sunday
            # Check if it's Sunday after 5pm EST (22:00 UTC)
            if now.weekday() == 6 and now.hour >= 22:
                return True
            # Check if it's Friday before 5pm EST (22:00 UTC)
            if now.weekday() == 4 and now.hour < 22:
                return True
            return False
        
        # Stock markets: typically 9:30am - 4pm EST (14:30 - 21:00 UTC)
        # This is a simplified check
        if now.hour < 14 or now.hour >= 21:
            # Could be outside regular hours - allow with warning
            logger.debug(f"Outside regular trading hours for {symbol}")
        
        return True
    
    def _get_symbol_exposure(self, symbol: str) -> float:
        """Get current exposure for symbol"""
        exposure = 0.0
        
        for trade in self.active_trades.values():
            if trade['order']['symbol'] == symbol and trade['status'] == 'active':
                exposure += trade['order']['size']
        
        return exposure
    
    async def _update_trade_status(self):
        """Update status of active trades"""
        for trade_id, trade in list(self.active_trades.items()):
            if trade['status'] != 'active':
                continue
            
            # Get current price
            symbol = trade['order']['symbol']
            market_data = await self._get_market_data(symbol)
            if not market_data:
                continue
            
            current_price = market_data.get('price', 0)
            if not current_price:
                continue
            
            # Check stop loss and take profit
            order = trade['order']
            direction = order['direction']
            stop_loss = order['stop_loss']
            take_profit = order['take_profit']
            
            # Calculate profit/loss
            entry_price = order['entry_price']
            size = order['size']
            
            if direction == 'buy':
                pnl = (current_price - entry_price) * size
                
                # Check stop loss
                if current_price <= stop_loss:
                    await self._close_trade(trade_id, 'stop_loss', current_price, pnl)
                
                # Check take profit
                elif current_price >= take_profit:
                    await self._close_trade(trade_id, 'take_profit', current_price, pnl)
                    
            else:  # sell
                pnl = (entry_price - current_price) * size
                
                # Check stop loss
                if current_price >= stop_loss:
                    await self._close_trade(trade_id, 'stop_loss', current_price, pnl)
                
                # Check take profit
                elif current_price <= take_profit:
                    await self._close_trade(trade_id, 'take_profit', current_price, pnl)
    
    async def _close_trade(self, 
                         trade_id: str, 
                         reason: str, 
                         exit_price: float, 
                         pnl: float):
        """Close a trade"""
        if trade_id not in self.active_trades:
            return
        
        trade = self.active_trades[trade_id]
        
        # Update trade status
        trade['status'] = 'closed'
        trade['exit_time'] = datetime.now()
        trade['exit_price'] = exit_price
        trade['pnl'] = pnl
        trade['exit_reason'] = reason
        
        # Move to history (bounded to prevent memory leak)
        self.trade_history.append(trade)
        if len(self.trade_history) > self._max_history_size:
            self.trade_history = self.trade_history[-5000:]
        
        # Update metrics
        self.metrics['total_pnl'] += pnl
        if pnl > 0:
            self.metrics['wins'] += 1
        else:
            self.metrics['losses'] += 1
        
        # Update signal performance
        self.signal_processor.update_signal_performance(
            trade['signal'],
            {'profit': pnl, 'success': pnl > 0}
        )
        # Persist per-signal performance to the database
        await self.db.write_performance_metric(
            metric_type='signal_performance',
            component=trade['signal'].signal_type if hasattr(trade['signal'], 'signal_type') else 'unknown',
            value=pnl,
            metadata={
                'trade_id': trade_id,
                'signal': str(trade['signal']),
                'profit': pnl,
                'success': pnl > 0,
                'exit_reason': reason,
                'timestamp': datetime.now().isoformat()
            }
        )
        
        logger.info(f"Closed trade {trade_id}: {reason}, PnL: {pnl}")
    
    def _get_system_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system metrics"""
        # Calculate trading metrics
        win_rate = self.metrics['wins'] / self.metrics['trades'] if self.metrics['trades'] > 0 else 0
        
        # Calculate Sharpe ratio
        if self.trade_history:
            returns = [t['pnl'] for t in self.trade_history]
            avg_return = np.mean(returns)
            std_return = np.std(returns) if len(returns) > 1 else 1.0
            sharpe = avg_return / std_return if std_return > 0 else 0
        else:
            sharpe = 0
        
        # Calculate max drawdown
        if self.trade_history:
            cumulative = np.cumsum([t['pnl'] for t in self.trade_history])
            peak = np.maximum.accumulate(cumulative)
            drawdown = (cumulative - peak) / peak if any(peak) else np.zeros_like(cumulative)
            max_drawdown = np.min(drawdown) if len(drawdown) > 0 else 0
        else:
            max_drawdown = 0
        
        # Update metrics
        self.metrics['win_rate'] = win_rate
        self.metrics['sharpe_ratio'] = sharpe
        self.metrics['max_drawdown'] = max_drawdown
        
        # Combine all metrics
        return {
            'trading': {
                'trades': self.metrics['trades'],
                'win_rate': win_rate,
                'total_pnl': self.metrics['total_pnl'],
                'sharpe_ratio': sharpe,
                'max_drawdown': max_drawdown,
                'active_trades': len([t for t in self.active_trades.values() if t['status'] == 'active'])
            },
            'pipeline': {
                'avg_latency': np.mean(self.metrics['processing_latency'][-1000:]) if self.metrics['processing_latency'] else 0,
                'max_latency': np.max(self.metrics['processing_latency'][-1000:]) if self.metrics['processing_latency'] else 0,
                'throughput': 1.0 / np.mean(self.metrics['processing_latency'][-1000:]) if self.metrics['processing_latency'] and np.mean(self.metrics['processing_latency'][-1000:]) > 0 else 0
            },
            'opportunities': self.scanner.get_opportunity_metrics(),
            'signals': self.signal_processor.get_signal_metrics(),
            'system': {
                'uptime': (datetime.now() - self.start_time).total_seconds(),
                'memory_usage': self._get_memory_usage()
            }
        }
    
    def _get_memory_usage(self) -> Dict[str, float]:
        """Get memory usage statistics"""
        if not PSUTIL_AVAILABLE:
            return {'rss': 0, 'vms': 0, 'percent': 0}
        try:
        
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                'rss': memory_info.rss / 1024 / 1024,  # MB
                'vms': memory_info.vms / 1024 / 1024,  # MB
                'percent': process.memory_percent()
            }
        except Exception as e:
            logger.debug(f"Error getting memory usage: {e}")
            return {'rss': 0, 'vms': 0, 'percent': 0}
    
    async def stop(self):
        """Stop all trading loops gracefully"""
        logger.info("Stopping trading engine...")
        self.running = False
        self._shutdown_event.set()
        await asyncio.sleep(1)  # Give loops time to exit
    
    async def cleanup(self):
        """Cleanup system resources"""
        # Stop all loops first
        await self.stop()
        
        try:
            # Cleanup components
            await self.market_stream.cleanup()
        except Exception as e:
            logger.error(f"Error cleaning up market stream: {e}")
            await self.data_processor.cleanup()
        except Exception as e:
            logger.error(f"Error cleaning up data processor: {e}")
        
            await self.db.cleanup()
        except Exception as e:
            logger.error(f"Error cleaning up database: {e}")
        
            await self.monitor.cleanup()
        except Exception as e:
            logger.error(f"Error cleaning up monitor: {e}")
        
        # Shutdown executor with wait
        self.executor.shutdown(wait=True)
        logger.info("Trading engine cleaned up")
