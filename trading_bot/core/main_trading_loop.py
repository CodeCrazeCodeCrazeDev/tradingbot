"""
Main Trading Loop - Central Integration Point

This module wires all components together into a cohesive trading system:
- Data pipeline integration
- Signal generation
- Risk management
- Order execution
- Position management
- Monitoring and alerting
"""

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import signal
import sys
from collections import deque

logger = logging.getLogger(__name__)


class SystemState(Enum):
    """Trading system state"""
    INITIALIZING = "INITIALIZING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    ERROR = "ERROR"


class TradingMode(Enum):
    """Trading mode"""
    LIVE = "LIVE"
    PAPER = "PAPER"
    BACKTEST = "BACKTEST"


@dataclass
class SystemHealth:
    """System health status"""
    state: SystemState
    uptime_seconds: float
    last_heartbeat: datetime
    data_feed_status: str
    broker_status: str
    risk_status: str
    active_positions: int
    pending_orders: int
    errors_last_hour: int
    warnings_last_hour: int


@dataclass
class TradingSignal:
    """Trading signal from analysis"""
    symbol: str
    direction: str  # BUY, SELL, HOLD
    strength: float  # 0-1
    confidence: float  # 0-1
    source: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TradeDecision:
    """Final trade decision after risk checks"""
    signal: TradingSignal
    approved: bool
    position_size: float
    stop_loss: float
    take_profit: float
    risk_score: float
    rejection_reason: Optional[str] = None


class CircuitBreaker:
    """Circuit breaker for fault tolerance"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_requests: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_requests = half_open_requests
        
        self.failures = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.half_open_successes = 0
    
    def record_success(self):
        """Record successful operation"""
        if self.state == "HALF_OPEN":
            self.half_open_successes += 1
            if self.half_open_successes >= self.half_open_requests:
                self.state = "CLOSED"
                self.failures = 0
                logger.info("Circuit breaker closed")
        else:
            self.failures = 0
    
    def record_failure(self):
        """Record failed operation"""
        self.failures += 1
        self.last_failure_time = datetime.now()
        
        if self.failures >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(f"Circuit breaker opened after {self.failures} failures")
    
    def can_execute(self) -> bool:
        """Check if operation can be executed"""
        if self.state == "CLOSED":
            return True
        
        if self.state == "OPEN":
            if self.last_failure_time:
                elapsed = (datetime.now() - self.last_failure_time).total_seconds()
                if elapsed >= self.recovery_timeout:
                    self.state = "HALF_OPEN"
                    self.half_open_successes = 0
                    logger.info("Circuit breaker half-open")
                    return True
            return False
        
        return True  # HALF_OPEN


class RateLimiter:
    """Rate limiter for API calls"""
    
    def __init__(self, max_requests: int, time_window: int):
        """
        Args:
            max_requests: Maximum requests allowed
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: deque = deque()
    
    async def acquire(self) -> bool:
        """Acquire rate limit slot"""
        now = datetime.now()
        
        # Remove old requests
        while self.requests and (now - self.requests[0]).total_seconds() > self.time_window:
            self.requests.popleft()
        
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        
        # Wait for slot
        oldest = self.requests[0]
        wait_time = self.time_window - (now - oldest).total_seconds()
        if wait_time > 0:
            await asyncio.sleep(wait_time)
            self.requests.popleft()
            self.requests.append(datetime.now())
        
        return True


class DataValidator:
    """Data validation pipeline"""
    
    @staticmethod
    def validate_ohlcv(data: Dict) -> tuple[bool, List[str]]:
        """Validate OHLCV data"""
        errors = []
        
        required_fields = ['open', 'high', 'low', 'close', 'volume', 'timestamp']
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing field: {field}")
        
        if not errors:
            # Check OHLC relationships
            if data['high'] < data['low']:
                errors.append("High < Low")
            if data['high'] < data['open'] or data['high'] < data['close']:
                errors.append("High not highest")
            if data['low'] > data['open'] or data['low'] > data['close']:
                errors.append("Low not lowest")
            
            # Check for negative values
            if data['volume'] < 0:
                errors.append("Negative volume")
            if any(data[k] < 0 for k in ['open', 'high', 'low', 'close']):
                errors.append("Negative price")
            
            # Check staleness
            if isinstance(data['timestamp'], datetime):
                age = (datetime.now() - data['timestamp']).total_seconds()
                if age > 300:  # 5 minutes
                    errors.append(f"Stale data: {age:.0f}s old")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_signal(signal: TradingSignal) -> tuple[bool, List[str]]:
        """Validate trading signal"""
        errors = []
        
        if signal.direction not in ['BUY', 'SELL', 'HOLD']:
            errors.append(f"Invalid direction: {signal.direction}")
        
        if not 0 <= signal.strength <= 1:
            errors.append(f"Invalid strength: {signal.strength}")
        
        if not 0 <= signal.confidence <= 1:
            errors.append(f"Invalid confidence: {signal.confidence}")
        
        # Check signal age
        age = (datetime.now() - signal.timestamp).total_seconds()
        if age > 60:  # 1 minute
            errors.append(f"Stale signal: {age:.0f}s old")
        
        return len(errors) == 0, errors


class SimplePositionTracker:
    """Simple fallback position tracker when PositionManager is not available"""
    
    def __init__(self):
        self.positions = {}
        self.trades = []
    
    def get_position(self, symbol: str):
        return self.positions.get(symbol)
    
    def get_all_positions(self):
        return list(self.positions.values())
    
    def update_position(self, symbol: str, quantity: float, price: float):
        if symbol in self.positions:
            pos = self.positions[symbol]
            pos['quantity'] += quantity
            if pos['quantity'] == 0:
                del self.positions[symbol]
        else:
            self.positions[symbol] = {
                'symbol': symbol,
                'quantity': quantity,
                'entry_price': price,
                'current_price': price,
                'unrealized_pnl': 0.0
            }
    
    def record_trade(self, trade: Dict):
        self.trades.append(trade)


class MainTradingLoop:
    """
    Main trading loop that orchestrates all components.
    """
    
    def __init__(
        self,
        mode: TradingMode = TradingMode.PAPER,
        config: Optional[Dict] = None
    ):
        self.mode = mode
        self.config = config or {}
        self.state = SystemState.INITIALIZING
        self.start_time: Optional[datetime] = None
        
        # Component references (lazy loaded)
        self._broker = None
        self._risk_manager = None
        self._signal_generator = None
        self._data_feed = None
        self._position_manager = None
        
        # Circuit breakers
        self.circuit_breakers = {
            'broker': CircuitBreaker(failure_threshold=3, recovery_timeout=30),
            'data_feed': CircuitBreaker(failure_threshold=5, recovery_timeout=60),
            'risk': CircuitBreaker(failure_threshold=3, recovery_timeout=30)
        }
        
        # Rate limiters
        self.rate_limiters = {
            'broker_api': RateLimiter(max_requests=10, time_window=1),
            'data_api': RateLimiter(max_requests=100, time_window=60)
        }
        
        # Metrics
        self.metrics = {
            'signals_generated': 0,
            'trades_executed': 0,
            'trades_rejected': 0,
            'errors': 0,
            'warnings': 0
        }
        
        # Error tracking
        self.recent_errors: deque = deque(maxlen=100)
        self.recent_warnings: deque = deque(maxlen=100)
        
        # Callbacks
        self.on_signal: Optional[Callable] = None
        self.on_trade: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
        
        # Graceful shutdown
        self._shutdown_event = asyncio.Event()
        
        logger.info(f"Trading loop initialized in {mode.value} mode")
    
    async def initialize(self) -> bool:
        """Initialize all components"""
        logger.info("Initializing trading system...")
        
        try:
            # Initialize broker
            await self._initialize_broker()
            
            # Initialize data feed
            await self._initialize_data_feed()
            
            # Initialize risk manager
            await self._initialize_risk_manager()
            
            # Initialize signal generator
            await self._initialize_signal_generator()
            
            # Initialize position manager
            await self._initialize_position_manager()
            
            self.state = SystemState.RUNNING
            self.start_time = datetime.now()
            
            logger.info("Trading system initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            self.state = SystemState.ERROR
            return False
    
    async def _initialize_broker(self):
        """Initialize broker adapter"""
        try:
            from trading_bot.brokers.broker_adapter import MockBrokerAdapter, MT5BrokerAdapter
            
            if self.mode == TradingMode.LIVE:
                self._broker = MT5BrokerAdapter(self.config.get('broker', {}))
            else:
                self._broker = MockBrokerAdapter(self.config.get('broker', {}))
            
            connected = await self._broker.connect()
            if not connected:
                raise Exception("Failed to connect to broker")
            
            logger.info(f"Broker initialized: {type(self._broker).__name__}")
            
        except ImportError as e:
            logger.warning(f"Broker module not available: {e}")
            # Create minimal mock
            self._broker = None
    
    async def _initialize_data_feed(self):
        """Initialize data feed"""
        try:
            from trading_bot.data.market_data_stream import MarketDataStream
            self._data_feed = MarketDataStream(self.config.get('data_feed', {}))
            await self._data_feed.connect()
            logger.info("Data feed initialized successfully")
        except ImportError as e:
            logger.warning(f"MarketDataStream not available: {e}")
            self._data_feed = None
        except Exception as e:
            logger.error(f"Failed to initialize data feed: {e}")
            self._data_feed = None
    
    async def _initialize_risk_manager(self):
        """Initialize risk manager"""
        try:
            from trading_bot.risk.MASTER_risk_manager import MasterRiskManager
            self._risk_manager = MasterRiskManager(self.config.get('risk', {}))
            logger.info("Risk manager initialized")
        except ImportError as e:
            logger.warning(f"Risk manager not available: {e}")
            self._risk_manager = None
    
    async def _initialize_signal_generator(self):
        """Initialize signal generator"""
        try:
            from trading_bot.core.analysis_orchestrator import AnalysisOrchestrator
            self._signal_generator = AnalysisOrchestrator(self.config.get('analysis', {}))
            logger.info("Signal generator initialized successfully")
        except ImportError as e:
            logger.warning(f"AnalysisOrchestrator not available: {e}")
            self._signal_generator = None
        except Exception as e:
            logger.error(f"Failed to initialize signal generator: {e}")
            self._signal_generator = None
    
    async def _initialize_position_manager(self):
        """Initialize position manager"""
        try:
            from trading_bot.trading.position_manager import PositionManager
            self._position_manager = PositionManager(self.config.get('position_manager', {}))
            logger.info("Position manager initialized successfully")
        except ImportError as e:
            logger.warning(f"PositionManager not available: {e}")
            # Create a simple position tracker as fallback
            self._position_manager = SimplePositionTracker()
        except Exception as e:
            logger.error(f"Failed to initialize position manager: {e}")
            self._position_manager = SimplePositionTracker()


    async def run(self):
        """Main trading loop"""
        logger.info("Starting main trading loop...")
        
        # Setup signal handlers for graceful shutdown
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, lambda: asyncio.create_task(self.shutdown()))
            except (NotImplementedError, RuntimeError):
                # Windows doesn't support add_signal_handler
                pass
        
        try:
            while self.state == SystemState.RUNNING:
                try:
                    # Check for shutdown
                    if self._shutdown_event.is_set():
                        break
                    
                    # Main loop iteration
                    await self._loop_iteration()
                    
                    # Small delay to prevent CPU spinning
                    await asyncio.sleep(0.1)
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    await self._handle_error(e)
                    
        finally:
            await self._cleanup()
    
    async def _loop_iteration(self):
        """Single iteration of the trading loop"""
        # 1. Fetch market data
        market_data = await self._fetch_market_data()
        if not market_data:
            return
        
        # 2. Validate data
        valid, errors = DataValidator.validate_ohlcv(market_data)
        if not valid:
            logger.warning(f"Invalid market data: {errors}")
            return
        
        # 3. Generate signals
        signals = await self._generate_signals(market_data)
        
        # 4. Process each signal
        for signal in signals:
            await self._process_signal(signal)
        
        # 5. Update positions
        await self._update_positions()
        
        # 6. Check risk limits
        await self._check_risk_limits()
    
    async def _fetch_market_data(self) -> Optional[Dict]:
        """Fetch current market data"""
        if not self.circuit_breakers['data_feed'].can_execute():
            logger.warning("Data feed circuit breaker open")
            return None
        
        try:
            await self.rate_limiters['data_api'].acquire()
            
            # Placeholder - implement actual data fetching
            data = {
                'symbol': 'EURUSD',
                'open': 1.1000,
                'high': 1.1010,
                'low': 1.0990,
                'close': 1.1005,
                'volume': 10000,
                'timestamp': datetime.now()
            }
            
            self.circuit_breakers['data_feed'].record_success()
            return data
            
        except Exception as e:
            self.circuit_breakers['data_feed'].record_failure()
            raise
    
    async def _generate_signals(self, market_data: Dict) -> List[TradingSignal]:
        """Generate trading signals from market data"""
        signals = []
        
        # Placeholder - implement actual signal generation
        # This would call your ML models, technical analysis, etc.
        
        return signals
    
    async def _process_signal(self, signal: TradingSignal):
        """Process a trading signal"""
        # Validate signal
        valid, errors = DataValidator.validate_signal(signal)
        if not valid:
            logger.warning(f"Invalid signal: {errors}")
            return
        
        self.metrics['signals_generated'] += 1
        
        # Callback
        if self.on_signal:
            await self.on_signal(signal)
        
        # Skip HOLD signals
        if signal.direction == 'HOLD':
            return
        
        # Risk check
        decision = await self._risk_check(signal)
        
        if decision.approved:
            await self._execute_trade(decision)
        else:
            self.metrics['trades_rejected'] += 1
            logger.info(f"Trade rejected: {decision.rejection_reason}")
    
    async def _risk_check(self, signal: TradingSignal) -> TradeDecision:
        """Perform risk checks on signal"""
        if not self.circuit_breakers['risk'].can_execute():
            return TradeDecision(
                signal=signal,
                approved=False,
                position_size=0,
                stop_loss=0,
                take_profit=0,
                risk_score=1.0,
                rejection_reason="Risk circuit breaker open"
            )
        
            # Placeholder - implement actual risk checks
            # This would call your risk manager
            
            decision = TradeDecision(
                signal=signal,
                approved=signal.confidence > 0.6,
                position_size=0.01,  # 1% of account
                stop_loss=0.002,  # 20 pips
                take_profit=0.004,  # 40 pips
                risk_score=0.3,
                rejection_reason=None if signal.confidence > 0.6 else "Low confidence"
            )
            
            self.circuit_breakers['risk'].record_success()
            return decision
            
    async def _execute_trade(self, decision: TradeDecision):
        """Execute approved trade"""
        if not self._broker:
            logger.warning("No broker available")
            return
        
        if not self.circuit_breakers['broker'].can_execute():
            logger.warning("Broker circuit breaker open")
            return
        
            await self.rate_limiters['broker_api'].acquire()
            
            from trading_bot.brokers.broker_adapter import OrderSide, OrderType
            
            side = OrderSide.BUY if decision.signal.direction == 'BUY' else OrderSide.SELL
            
            response = await self._broker.place_order(
                symbol=decision.signal.symbol,
                side=side,
                order_type=OrderType.MARKET,
                quantity=decision.position_size
            )
            
            if response and response.success:
                self.metrics['trades_executed'] += 1
                self.circuit_breakers['broker'].record_success()
                
                logger.info(f"Trade executed: {decision.signal.symbol} {side.value} {decision.position_size}")
                
                if self.on_trade:
                    await self.on_trade(decision, response)
            else:
                self.circuit_breakers['broker'].record_failure()
                logger.error(f"Trade execution failed")
                
    async def _update_positions(self):
        """Update position information"""
        if not self._broker:
            return
        
            positions = await self._broker.get_positions()
            # Update position manager
    async def _check_risk_limits(self):
        """Check portfolio risk limits"""
        # Placeholder - implement actual risk limit checks
        pass
    
    async def _handle_error(self, error: Exception):
        """Handle errors in the trading loop"""
        self.metrics['errors'] += 1
        self.recent_errors.append({
            'timestamp': datetime.now(),
            'error': str(error),
            'type': type(error).__name__
        })
        
        logger.error(f"Trading loop error: {error}")
        
        if self.on_error:
            await self.on_error(error)
        
        # Check if we should stop
        errors_last_hour = sum(
            1 for e in self.recent_errors
            if (datetime.now() - e['timestamp']).total_seconds() < 3600
        )
        
        if errors_last_hour > 10:
            logger.critical("Too many errors, stopping trading")
            self.state = SystemState.ERROR
    
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("Initiating graceful shutdown...")
        self.state = SystemState.STOPPING
        self._shutdown_event.set()
    
    async def _cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up...")
        
        # Close broker connection
        if self._broker:
            await self._broker.disconnect()
        
        self.state = SystemState.STOPPED
        logger.info("Trading system stopped")
    
    def get_health(self) -> SystemHealth:
        """Get system health status"""
        uptime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        
        errors_last_hour = sum(
            1 for e in self.recent_errors
            if (datetime.now() - e['timestamp']).total_seconds() < 3600
        )
        
        warnings_last_hour = sum(
            1 for w in self.recent_warnings
            if (datetime.now() - w['timestamp']).total_seconds() < 3600
        )
        
        return SystemHealth(
            state=self.state,
            uptime_seconds=uptime,
            last_heartbeat=datetime.now(),
            data_feed_status=self.circuit_breakers['data_feed'].state,
            broker_status=self.circuit_breakers['broker'].state,
            risk_status=self.circuit_breakers['risk'].state,
            active_positions=0,  # Would get from position manager
            pending_orders=0,
            errors_last_hour=errors_last_hour,
            warnings_last_hour=warnings_last_hour
        )


# Health check endpoint
async def health_check_handler(trading_loop: MainTradingLoop) -> Dict:
    """Health check endpoint handler"""
    health = trading_loop.get_health()
    
    return {
        'status': 'healthy' if health.state == SystemState.RUNNING else 'unhealthy',
        'state': health.state.value,
        'uptime': health.uptime_seconds,
        'data_feed': health.data_feed_status,
        'broker': health.broker_status,
        'risk': health.risk_status,
        'errors_last_hour': health.errors_last_hour,
        'timestamp': datetime.now().isoformat()
    }


# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    async def main():
        # Create trading loop
        loop = MainTradingLoop(
            mode=TradingMode.PAPER,
            config={
                'broker': {'initial_balance': 10000},
                'risk': {'max_risk_per_trade': 0.02}
            }
        )
        
        # Initialize
        if await loop.initialize():
            try:
                # Run for a short time
                await asyncio.wait_for(loop.run(), timeout=10)
            except asyncio.TimeoutError:
                await loop.shutdown()
        
        # Print health
        health = loop.get_health()
        logger.info(f"\nSystem Health: {health.state.value}")
        logger.info(f"Uptime: {health.uptime_seconds:.0f}s")
        logger.info(f"Errors: {health.errors_last_hour}")
    
    asyncio.run(main())
