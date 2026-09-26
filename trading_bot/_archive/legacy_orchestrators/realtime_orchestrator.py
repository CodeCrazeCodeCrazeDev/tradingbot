"""
Real-Time Orchestrator
======================

Master orchestrator that integrates ALL real-time components
into a unified trading system.

Features:
1. Unified real-time data flow
2. Event-driven signal processing
3. Real-time execution pipeline
4. Streaming risk monitoring
5. Real-time ML predictions
6. Health monitoring
7. Auto-recovery

Author: AlphaAlgo Trading System
Version: 3.0.0
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class SystemMode(Enum):
    """System operating mode"""
    SIMULATION = "simulation"
    PAPER = "paper"
    LIVE = "live"


class SystemState(Enum):
    """System state"""
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    SHUTDOWN = "shutdown"


@dataclass
class RealTimeConfig:
    """Configuration for real-time system"""
    mode: SystemMode = SystemMode.PAPER
    symbols: List[str] = field(default_factory=lambda: ["BTCUSDT"])
    
    # Timing
    tick_interval_ms: int = 100
    signal_check_interval_ms: int = 50
    health_check_interval_s: float = 5.0
    
    # Risk limits
    initial_capital: float = 100000
    max_position_size: float = 0.02
    max_daily_loss: float = 0.05
    max_drawdown: float = 0.20
    
    # Features
    enable_ml: bool = True
    enable_signals: bool = True
    enable_execution: bool = True
    enable_risk: bool = True
    
    # Logging
    log_level: str = "INFO"
    log_to_file: bool = True


@dataclass
class SystemStatus:
    """System status snapshot"""
    timestamp: datetime
    state: SystemState
    mode: SystemMode
    uptime_seconds: float
    symbols: List[str]
    
    # Component status
    data_hub_active: bool
    signal_engine_active: bool
    execution_active: bool
    risk_monitor_active: bool
    ml_engine_active: bool
    
    # Metrics
    ticks_processed: int
    signals_generated: int
    orders_executed: int
    current_pnl: float
    risk_level: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'state': self.state.value,
            'mode': self.mode.value,
            'uptime_seconds': self.uptime_seconds,
            'symbols': self.symbols,
            'data_hub_active': self.data_hub_active,
            'signal_engine_active': self.signal_engine_active,
            'execution_active': self.execution_active,
            'risk_monitor_active': self.risk_monitor_active,
            'ml_engine_active': self.ml_engine_active,
            'ticks_processed': self.ticks_processed,
            'signals_generated': self.signals_generated,
            'orders_executed': self.orders_executed,
            'current_pnl': self.current_pnl,
            'risk_level': self.risk_level
        }


class RealTimeOrchestrator:
    """
    Master orchestrator for the real-time trading system.
    
    Integrates:
    - RealTimeDataHub: WebSocket data streaming
    - RealTimeSignalEngine: Event-driven signals
    - RealTimeExecution: Real-time order execution
    - RealTimeRiskMonitor: Streaming risk monitoring
    - RealTimeMLEngine: Real-time ML predictions
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        config = config or {}
        
        # Parse configuration
        self.config = RealTimeConfig(
            mode=SystemMode(config.get('mode', 'paper')),
            symbols=config.get('symbols', ['BTCUSDT']),
            tick_interval_ms=config.get('tick_interval_ms', 100),
            initial_capital=config.get('initial_capital', 100000),
            max_position_size=config.get('max_position_size', 0.02),
            max_daily_loss=config.get('max_daily_loss', 0.05),
            max_drawdown=config.get('max_drawdown', 0.20),
            enable_ml=config.get('enable_ml', True),
            enable_signals=config.get('enable_signals', True),
            enable_execution=config.get('enable_execution', True),
            enable_risk=config.get('enable_risk', True),
        )
        
        # System state
        self.state = SystemState.INITIALIZING
        self._start_time: Optional[datetime] = None
        self._running = False
        
        # Components (lazy initialized)
        self._data_hub = None
        self._signal_engine = None
        self._execution = None
        self._risk_monitor = None
        self._ml_engine = None
        
        # Metrics
        self._ticks_processed = 0
        self._signals_generated = 0
        self._orders_executed = 0
        
        # Tasks
        self._tasks: List[asyncio.Task] = []
        
        # Event callbacks
        self._status_callbacks: List[Callable] = []
        
        logger.info("RealTimeOrchestrator initialized")
    
    async def initialize(self):
        """Initialize all components"""
        logger.info("=" * 60)
        logger.info("INITIALIZING REAL-TIME TRADING SYSTEM")
        logger.info("=" * 60)
        logger.info(f"Mode: {self.config.mode.value}")
        logger.info(f"Symbols: {self.config.symbols}")
        
        try:
            # Import components
            from .realtime_data_hub import RealTimeDataHub, StreamConfig, StreamType
            from .realtime_signal_engine import RealTimeSignalEngine
            from .realtime_execution import RealTimeExecution, OrderSide, OrderType
            from .realtime_risk import RealTimeRiskMonitor
            from .realtime_ml import RealTimeMLEngine
            
            # Initialize data hub
            logger.info("Initializing RealTimeDataHub...")
            self._data_hub = RealTimeDataHub({
                'use_simulation': self.config.mode == SystemMode.SIMULATION,
                'exchanges': ['binance']
            })
            await self._data_hub.initialize()
            
            # Initialize signal engine
            if self.config.enable_signals:
                logger.info("Initializing RealTimeSignalEngine...")
                self._signal_engine = RealTimeSignalEngine({})
            
            # Initialize execution
            if self.config.enable_execution:
                logger.info("Initializing RealTimeExecution...")
                self._execution = RealTimeExecution({
                    'broker': {
                        'latency_ms': 50 if self.config.mode == SystemMode.SIMULATION else 10,
                        'slippage_bps': 2
                    }
                })
            
            # Initialize risk monitor
            if self.config.enable_risk:
                logger.info("Initializing RealTimeRiskMonitor...")
                self._risk_monitor = RealTimeRiskMonitor({
                    'initial_capital': self.config.initial_capital,
                    'max_position_size': self.config.max_position_size,
                    'max_daily_loss': self.config.max_daily_loss,
                    'max_drawdown': self.config.max_drawdown
                })
            
            # Initialize ML engine
            if self.config.enable_ml:
                logger.info("Initializing RealTimeMLEngine...")
                self._ml_engine = RealTimeMLEngine({})
            
            # Wire up event handlers
            await self._wire_event_handlers()
            
            # Subscribe to data streams
            await self._subscribe_streams()
            
            self.state = SystemState.READY
            logger.info("All components initialized successfully")
            
        except Exception as e:
            logger.error(f"Initialization error: {e}")
            self.state = SystemState.ERROR
            raise
    
    async def _wire_event_handlers(self):
        """Wire up event handlers between components"""
        from .realtime_data_hub import StreamType
        
        # Data hub -> Signal engine, ML engine, Risk monitor
        if self._data_hub:
            self._data_hub.subscribe(StreamType.TICK, self._on_tick)
            self._data_hub.subscribe(StreamType.ORDERBOOK, self._on_orderbook)
            self._data_hub.subscribe(StreamType.TRADE, self._on_trade)
        
        # Signal engine -> Execution
        if self._signal_engine:
            self._signal_engine.subscribe(self._on_signal)
        
        # Execution -> Risk monitor
        if self._execution:
            self._execution.subscribe_orders(self._on_order_update)
        
        # Risk monitor -> Execution (for risk events)
        if self._risk_monitor:
            self._risk_monitor.subscribe_risk(self._on_risk_event)
        
        logger.info("Event handlers wired")
    
    async def _subscribe_streams(self):
        """Subscribe to data streams for all symbols"""
        from .realtime_data_hub import StreamConfig, StreamType
        
        for symbol in self.config.symbols:
            # Subscribe to tick data
            await self._data_hub.subscribe_stream(StreamConfig(
                stream_type=StreamType.TICK,
                symbol=symbol,
                exchange='binance'
            ))
            
            # Subscribe to order book
            await self._data_hub.subscribe_stream(StreamConfig(
                stream_type=StreamType.ORDERBOOK,
                symbol=symbol,
                exchange='binance',
                depth=20
            ))
            
            # Subscribe to trades
            await self._data_hub.subscribe_stream(StreamConfig(
                stream_type=StreamType.TRADE,
                symbol=symbol,
                exchange='binance'
            ))
        
        logger.info(f"Subscribed to streams for {len(self.config.symbols)} symbols")
    
    async def _on_tick(self, symbol: str, tick_data):
        """Handle tick data"""
        self._ticks_processed += 1
        
        # Update execution with current price
        if self._execution:
            self._execution.update_price(symbol, tick_data.last)
        
        # Update risk monitor
        if self._risk_monitor:
            self._risk_monitor.on_price_update(symbol, tick_data.last)
        
        # Feed to signal engine
        if self._signal_engine:
            await self._signal_engine.on_tick(symbol, tick_data)
        
        # Feed to ML engine
        if self._ml_engine:
            await self._ml_engine.on_tick(
                symbol, tick_data.last, tick_data.volume,
                tick_data.bid, tick_data.ask
            )
    
    async def _on_orderbook(self, symbol: str, orderbook):
        """Handle order book update"""
        if self._signal_engine:
            await self._signal_engine.on_orderbook(symbol, orderbook)
    
    async def _on_trade(self, symbol: str, trade_data):
        """Handle trade data"""
        pass  # Can be used for trade flow analysis
    
    async def _on_signal(self, signal):
        """Handle trading signal"""
        self._signals_generated += 1
        
        logger.info(f"Signal received: {signal.symbol} {signal.direction.value} "
                   f"confidence={signal.effective_confidence:.2f}")
        
        # Check if we can trade
        if not self._risk_monitor:
            return
        
        can_trade, reason = self._risk_monitor.can_trade()
        if not can_trade:
            logger.warning(f"Cannot trade: {reason}")
            return
        
        # Check signal confidence
        if signal.effective_confidence < 0.6:
            logger.debug(f"Signal confidence too low: {signal.effective_confidence:.2f}")
            return
        
        # Pre-trade risk check
        from .realtime_execution import OrderSide, OrderType
        
        side = OrderSide.BUY if signal.direction.value == "buy" else OrderSide.SELL
        quantity = self._calculate_position_size(signal)
        
        approved, reason = self._risk_monitor.check_order(
            signal.symbol, side.value, quantity, signal.entry_price
        )
        
        if not approved:
            logger.warning(f"Order rejected by risk: {reason}")
            return
        
        # Execute order
        if self._execution and self.config.enable_execution:
            try:
                order = await self._execution.submit_order(
                    symbol=signal.symbol,
                    side=side,
                    quantity=quantity,
                    order_type=OrderType.MARKET,
                    metadata={
                        'signal_id': signal.signal_id,
                        'signal_type': signal.signal_type.value,
                        'confidence': signal.confidence
                    }
                )
                
                self._orders_executed += 1
                logger.info(f"Order executed: {order.order_id}")
                
            except Exception as e:
                logger.error(f"Order execution error: {e}")
    
    async def _on_order_update(self, order):
        """Handle order update"""
        from .realtime_execution import OrderStatus
        
        if order.status == OrderStatus.FILLED:
            # Update risk monitor with fill
            if self._risk_monitor:
                await self._risk_monitor.on_fill(
                    symbol=order.symbol,
                    side="long" if order.side.value == "buy" else "short",
                    quantity=order.filled_quantity,
                    price=order.avg_fill_price
                )
    
    async def _on_risk_event(self, event):
        """Handle risk event"""
        from .realtime_risk import RiskLevel
        
        logger.warning(f"Risk event: [{event.risk_level.value}] {event.message}")
        
        # Emergency actions
        if event.risk_level in [RiskLevel.CRITICAL, RiskLevel.EMERGENCY]:
            logger.error("CRITICAL RISK EVENT - Halting new trades")
            # Could cancel all open orders here
    
    def _calculate_position_size(self, signal) -> float:
        """Calculate position size based on risk parameters"""
        if not self._risk_monitor:
            return 0.0
        
        equity = self._risk_monitor._calculate_equity()
        max_risk = equity * self.config.max_position_size
        
        # Adjust by confidence
        adjusted_risk = max_risk * signal.effective_confidence
        
        # Calculate quantity
        if signal.entry_price > 0:
            quantity = adjusted_risk / signal.entry_price
        else:
            quantity = 0.0
        
        return quantity
    
    async def start(self):
        """Start the real-time trading system"""
        if self.state != SystemState.READY:
            raise RuntimeError(f"Cannot start from state: {self.state}")
        
        logger.info("=" * 60)
        logger.info("STARTING REAL-TIME TRADING SYSTEM")
        logger.info("=" * 60)
        
        self._running = True
        self._start_time = datetime.now()
        self.state = SystemState.RUNNING
        
        # Start all components
        if self._data_hub:
            await self._data_hub.start()
        if self._signal_engine:
            await self._signal_engine.start()
        if self._execution:
            await self._execution.start()
        if self._risk_monitor:
            await self._risk_monitor.start()
        if self._ml_engine:
            await self._ml_engine.start()
        
        # Start background tasks
        self._tasks = [
            asyncio.create_task(self._health_check_loop()),
            asyncio.create_task(self._status_broadcast_loop()),
        ]
        
        logger.info("Real-time trading system started")
        
        try:
            # Keep running
            while self._running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
    
    async def stop(self):
        """Stop the real-time trading system"""
        logger.info("Stopping real-time trading system...")
        
        self._running = False
        self.state = SystemState.SHUTDOWN
        
        # Cancel tasks
        for task in self._tasks:
            task.cancel()
        
        # Stop all components
        if self._data_hub:
            await self._data_hub.stop()
        if self._signal_engine:
            await self._signal_engine.stop()
        if self._execution:
            await self._execution.stop()
        if self._risk_monitor:
            await self._risk_monitor.stop()
        if self._ml_engine:
            await self._ml_engine.stop()
        
        logger.info("Real-time trading system stopped")
    
    async def _health_check_loop(self):
        """Periodic health check"""
        while self._running:
            try:
                # Check component health
                health = {
                    'data_hub': self._data_hub is not None,
                    'signal_engine': self._signal_engine is not None,
                    'execution': self._execution is not None,
                    'risk_monitor': self._risk_monitor is not None,
                    'ml_engine': self._ml_engine is not None,
                }
                
                # Log if any issues
                unhealthy = [k for k, v in health.items() if not v]
                if unhealthy:
                    logger.warning(f"Unhealthy components: {unhealthy}")
                
                await asyncio.sleep(self.config.health_check_interval_s)
                
            except Exception as e:
                logger.error(f"Health check error: {e}")
                await asyncio.sleep(5)
    
    async def _status_broadcast_loop(self):
        """Broadcast status updates"""
        while self._running:
            try:
                status = self.get_status()
                
                for callback in self._status_callbacks:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(status)
                        else:
                            callback(status)
                    except Exception as e:
                        logger.error(f"Status callback error: {e}")
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Status broadcast error: {e}")
                await asyncio.sleep(5)
    
    def subscribe_status(self, callback: Callable):
        """Subscribe to status updates"""
        self._status_callbacks.append(callback)
    
    def get_status(self) -> SystemStatus:
        """Get current system status"""
        uptime = (datetime.now() - self._start_time).total_seconds() if self._start_time else 0
        
        # Get risk metrics
        risk_level = "unknown"
        current_pnl = 0.0
        if self._risk_monitor:
            metrics = self._risk_monitor.get_metrics()
            risk_level = metrics.get('risk_level', 'unknown')
            current_pnl = metrics.get('unrealized_pnl', 0) + metrics.get('realized_pnl', 0)
        
        return SystemStatus(
            timestamp=datetime.now(),
            state=self.state,
            mode=self.config.mode,
            uptime_seconds=uptime,
            symbols=self.config.symbols,
            data_hub_active=self._data_hub is not None,
            signal_engine_active=self._signal_engine is not None,
            execution_active=self._execution is not None,
            risk_monitor_active=self._risk_monitor is not None,
            ml_engine_active=self._ml_engine is not None,
            ticks_processed=self._ticks_processed,
            signals_generated=self._signals_generated,
            orders_executed=self._orders_executed,
            current_pnl=current_pnl,
            risk_level=risk_level
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive metrics from all components"""
        metrics = {
            'system': {
                'state': self.state.value,
                'mode': self.config.mode.value,
                'uptime': (datetime.now() - self._start_time).total_seconds() if self._start_time else 0,
                'ticks_processed': self._ticks_processed,
                'signals_generated': self._signals_generated,
                'orders_executed': self._orders_executed
            }
        }
        
        if self._data_hub:
            metrics['data_hub'] = self._data_hub.get_metrics()
        if self._signal_engine:
            metrics['signal_engine'] = self._signal_engine.get_metrics()
        if self._execution:
            metrics['execution'] = self._execution.get_metrics()
        if self._risk_monitor:
            metrics['risk'] = self._risk_monitor.get_metrics()
        if self._ml_engine:
            metrics['ml'] = self._ml_engine.get_metrics()
        
        return metrics


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_realtime_system(config: Dict[str, Any] = None) -> RealTimeOrchestrator:
    """Create a real-time trading system"""
    return RealTimeOrchestrator(config or {})


async def quick_start(
    mode: str = "paper",
    symbols: List[str] = None,
    duration_seconds: int = None
) -> RealTimeOrchestrator:
    """Quick start a real-time trading system"""
    config = {
        'mode': mode,
        'symbols': symbols or ['BTCUSDT']
    }
    
    system = create_realtime_system(config)
    await system.initialize()
    
    if duration_seconds:
        async def run_with_timeout():
            task = asyncio.create_task(system.start())
            await asyncio.sleep(duration_seconds)
            await system.stop()
        
        await run_with_timeout()
    else:
        await system.start()
    
    return system


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Real-Time Trading System")
    parser.add_argument('--mode', choices=['simulation', 'paper', 'live'], default='paper')
    parser.add_argument('--symbols', nargs='+', default=['BTCUSDT'])
    parser.add_argument('--duration', type=int, help='Run duration in seconds')
    parser.add_argument('--capital', type=float, default=100000, help='Initial capital')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    async def main():
        config = {
            'mode': args.mode,
            'symbols': args.symbols,
            'initial_capital': args.capital
        }
        
        system = create_realtime_system(config)
        await system.initialize()
        
        try:
            if args.duration:
                task = asyncio.create_task(system.start())
                await asyncio.sleep(args.duration)
                await system.stop()
                
                # Print final status
                status = system.get_status()
                print("\n" + "=" * 60)
                print("FINAL STATUS")
                print("=" * 60)
                for key, value in status.to_dict().items():
                    print(f"  {key}: {value}")
            else:
                await system.start()
        except KeyboardInterrupt:
            await system.stop()
    
    asyncio.run(main())
