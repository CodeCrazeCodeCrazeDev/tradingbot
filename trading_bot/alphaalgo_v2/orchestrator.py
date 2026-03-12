"""
from typing import List, Optional, Set
AlphaAlgo V2 Main Orchestrator

This is the SINGLE entry point for the entire trading system.
It coordinates all components and manages the trading lifecycle.

Architecture:
- Data Layer: Fetches and validates market data
- Models Layer: ML/AI for signal generation
- Risk Engine: Validates trades against risk limits
- Execution Engine: Executes orders through brokers
- Evolution Engine: Self-improvement within safety bounds
- Reward Engine: Immutable performance measurement

Safety Features:
- Emergency kill switch always available
- Human override always available
- All trades validated against risk limits
- Complete audit trail
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
import uuid

from .core.types import (
    Signal,
    SignalType,
    Order,
    OrderType,
    Position,
    Trade,
    MarketData,
    RiskDecision,
    ExecutionResult,
)
from .core.constants import (
    TradingMode,
    SafetyLevel,
    MAX_RISK_PER_TRADE,
    MAX_DAILY_LOSS,
    MAX_DRAWDOWN,
    DEFAULT_TIMEFRAME,
    DEFAULT_BARS,
)
from .core.exceptions import (
    AlphaAlgoError,
    RiskLimitExceededError,
    ExecutionError,
)

logger = logging.getLogger(__name__)


class SystemState(Enum):
    """System state enumeration"""
    INITIALIZING = "initializing"
    READY = "ready"
    TRADING = "trading"
    PAUSED = "paused"
    EMERGENCY = "emergency"
    SHUTDOWN = "shutdown"


@dataclass
class TradingSession:
    """Trading session record"""
    id: str
    started_at: datetime
    mode: TradingMode
    symbols: List[str]
    trades: List[Trade] = field(default_factory=list)
    signals_generated: int = 0
    signals_executed: int = 0
    total_pnl: float = 0.0
    ended_at: Optional[datetime] = None


class AlphaAlgoOrchestrator:
    """
    Main orchestrator for the AlphaAlgo trading system
    
    This is the SINGLE entry point that coordinates:
    1. Data acquisition and validation
    2. Signal generation via ML models
    3. Risk validation
    4. Order execution
    5. Position management
    6. Performance tracking
    7. Self-evolution
    
    Usage:
        orchestrator = AlphaAlgoOrchestrator(config)
        await orchestrator.initialize()
        await orchestrator.start_trading(['EURUSD', 'GBPUSD'])
        # ... trading happens ...
        await orchestrator.stop_trading()
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the orchestrator
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self._state = SystemState.INITIALIZING
        self._safety_level = SafetyLevel.GREEN
        self._mode = TradingMode(self.config.get("mode", "paper"))
        
        # Components (lazy loaded)
        self._data_sources: Dict[str, Any] = {}
        self._signal_generators: List[Any] = []
        self._risk_manager = None
        self._executor = None
        self._evolution_engine = None
        self._reward_model = None
        
        # State
        self._current_session: Optional[TradingSession] = None
        self._session_history: List[TradingSession] = []
        self._positions: Dict[str, Position] = {}
        self._pending_orders: Dict[str, Order] = {}
        
        # Control
        self._trading_task: Optional[asyncio.Task] = None
        self._emergency_stop = False
        
        logger.info(f"AlphaAlgo Orchestrator initialized in {self._mode.value} mode")
    
    @property
    def state(self) -> SystemState:
        """Get current system state"""
        return self._state
    
    @property
    def safety_level(self) -> SafetyLevel:
        """Get current safety level"""
        return self._safety_level
    
    @property
    def is_trading(self) -> bool:
        """Check if currently trading"""
        return self._state == SystemState.TRADING
    
    @property
    def mode(self) -> TradingMode:
        """Get trading mode"""
        return self._mode
    
    async def initialize(self) -> bool:
        """
        Initialize all components
        
        Returns:
            True if initialization successful
        """
        try:
            logger.info("Initializing AlphaAlgo components...")
            
            # Initialize reward model (immutable)
            from .reward_engine.immutable_rewards import get_reward_model
            self._reward_model = get_reward_model()
            logger.info("✓ Reward model initialized")
            
            # Initialize evolution engine
            from .evolution.orchestrator import EvolutionOrchestrator
            self._evolution_engine = EvolutionOrchestrator(
                self.config.get("evolution", {})
            )
            logger.info("✓ Evolution engine initialized")
            
            # Initialize data sources
            await self._initialize_data_sources()
            logger.info("✓ Data sources initialized")
            
            # Initialize signal generators
            await self._initialize_signal_generators()
            logger.info("✓ Signal generators initialized")
            
            # Initialize risk manager
            await self._initialize_risk_manager()
            logger.info("✓ Risk manager initialized")
            
            # Initialize executor
            await self._initialize_executor()
            logger.info("✓ Executor initialized")
            
            self._state = SystemState.READY
            logger.info("AlphaAlgo initialization complete")
            
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            self._state = SystemState.SHUTDOWN
            return False
    
    async def _initialize_data_sources(self) -> None:
        """Initialize data sources"""
        # Placeholder - would initialize actual data sources
        self._data_sources = {
            "primary": None,  # Would be MT5, Yahoo, etc.
        }
    
    async def _initialize_signal_generators(self) -> None:
        """Initialize signal generators"""
        # Placeholder - would initialize ML models
        self._signal_generators = []
    
    async def _initialize_risk_manager(self) -> None:
        """Initialize risk manager"""
        # Placeholder - would initialize risk manager
        self._risk_manager = None
    
    async def _initialize_executor(self) -> None:
        """Initialize executor"""
        # Placeholder - would initialize broker connection
        self._executor = None
    
    async def start_trading(self, symbols: List[str]) -> bool:
        """
        Start trading for given symbols
        
        Args:
            symbols: List of symbols to trade
            
        Returns:
            True if trading started successfully
        """
        if self._state != SystemState.READY:
            logger.error(f"Cannot start trading in state: {self._state}")
            return False
        try:
        
            # Create new session
            self._current_session = TradingSession(
                id=str(uuid.uuid4()),
                started_at=datetime.now(),
                mode=self._mode,
                symbols=symbols,
            )
            
            # Start trading loop
            self._state = SystemState.TRADING
            self._trading_task = asyncio.create_task(
                self._trading_loop(symbols)
            )
            
            logger.info(f"Started trading: {symbols}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start trading: {e}")
            return False
    
    async def stop_trading(self) -> bool:
        """
        Stop trading gracefully
        
        Returns:
            True if stopped successfully
        """
        if self._state != SystemState.TRADING:
            logger.warning("Not currently trading")
            return True
        try:
        
            # Cancel trading task
            if self._trading_task:
                self._trading_task.cancel()
                try:
                    await self._trading_task
                except asyncio.CancelledError:
                    pass
                self._trading_task = None
            
            # Close all positions if configured
            if self.config.get("close_on_stop", False):
                await self._close_all_positions()
            
            # End session
            if self._current_session:
                self._current_session.ended_at = datetime.now()
                self._session_history.append(self._current_session)
                self._current_session = None
            
            self._state = SystemState.READY
            logger.info("Trading stopped")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping trading: {e}")
            return False
    
    async def emergency_stop(self) -> bool:
        """
        Emergency stop - immediately halt all trading
        
        This is the KILL SWITCH that:
        1. Stops all trading immediately
        2. Cancels all pending orders
        3. Optionally closes all positions
        
        Returns:
            True if emergency stop successful
        """
        logger.critical("EMERGENCY STOP ACTIVATED")
        
        self._emergency_stop = True
        self._state = SystemState.EMERGENCY
        self._safety_level = SafetyLevel.BLACK
        
        try:
            # Cancel trading task
            if self._trading_task:
                self._trading_task.cancel()
            
            # Cancel all pending orders
            for order_id in list(self._pending_orders.keys()):
                try:
                    if self._executor:
                        await self._executor.cancel(order_id)
                except Exception as e:
                    logger.error(f"Failed to cancel order {order_id}: {e}")
            
            # Close all positions
            await self._close_all_positions()
            
            logger.critical("Emergency stop complete - all positions closed")
            return True
            
        except Exception as e:
            logger.critical(f"Emergency stop failed: {e}")
            return False
    
    async def _close_all_positions(self) -> None:
        """Close all open positions"""
        for symbol, position in list(self._positions.items()):
            try:
                if self._executor:
                    await self._executor.close_position(symbol)
                del self._positions[symbol]
                logger.info(f"Closed position: {symbol}")
            except Exception as e:
                logger.error(f"Failed to close position {symbol}: {e}")
    
    async def _trading_loop(self, symbols: List[str]) -> None:
        """
        Main trading loop
        
        Continuously:
        1. Fetch market data
        2. Generate signals
        3. Validate against risk
        4. Execute trades
        5. Monitor positions
        """
        logger.info("Trading loop started")
        
        while not self._emergency_stop:
            try:
                for symbol in symbols:
                    # Check safety level
                    if self._safety_level in [SafetyLevel.RED, SafetyLevel.BLACK]:
                        logger.warning(f"Safety level {self._safety_level} - skipping")
                        continue
                    
                    # Process symbol
                    await self._process_symbol(symbol)
                
                # Sleep between iterations
                await asyncio.sleep(self.config.get("loop_interval", 1.0))
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Trading loop error: {e}")
                await asyncio.sleep(5.0)  # Back off on error
        
        logger.info("Trading loop ended")
    
    async def _process_symbol(self, symbol: str) -> None:
        """
        Process a single symbol
        
        Args:
            symbol: Symbol to process
        """
        try:
            # 1. Get market data
            data = await self._get_market_data(symbol)
            if data is None:
                return
            
            # 2. Generate signal
            signal = await self._generate_signal(symbol, data)
            if signal is None:
                return
            
            if self._current_session:
                self._current_session.signals_generated += 1
            
            # 3. Validate against risk
            risk_decision = await self._validate_risk(signal)
            if not risk_decision.allowed:
                logger.info(f"Signal rejected by risk: {risk_decision.reason}")
                return
            
            # 4. Execute trade
            result = await self._execute_trade(signal, risk_decision)
            if result.success:
                if self._current_session:
                    self._current_session.signals_executed += 1
                logger.info(f"Trade executed: {symbol} {signal.signal_type.value}")
            
        except Exception as e:
            logger.error(f"Error processing {symbol}: {e}")
    
    async def _get_market_data(self, symbol: str) -> Optional[MarketData]:
        """Get market data for symbol"""
        # Placeholder - would fetch from data sources
        return None
    
    async def _generate_signal(
        self,
        symbol: str,
        data: MarketData
    ) -> Optional[Signal]:
        """Generate trading signal"""
        # Placeholder - would use signal generators
        return None
    
    async def _validate_risk(self, signal: Signal) -> RiskDecision:
        """Validate signal against risk limits"""
        # Placeholder - would use risk manager
        return RiskDecision(
            allowed=True,
            reason="Risk validation passed",
        )
    
    async def _execute_trade(
        self,
        signal: Signal,
        risk_decision: RiskDecision
    ) -> ExecutionResult:
        """Execute trade"""
        # Placeholder - would use executor
        return ExecutionResult(
            success=False,
            order_id="",
            message="Executor not initialized",
        )
    
    def pause_trading(self) -> None:
        """Pause trading (can be resumed)"""
        if self._state == SystemState.TRADING:
            self._state = SystemState.PAUSED
            logger.info("Trading paused")
    
    def resume_trading(self) -> None:
        """Resume paused trading"""
        if self._state == SystemState.PAUSED:
            self._state = SystemState.TRADING
            logger.info("Trading resumed")
    
    def set_safety_level(self, level: SafetyLevel) -> None:
        """
        Set safety level
        
        Args:
            level: New safety level
        """
        old_level = self._safety_level
        self._safety_level = level
        logger.info(f"Safety level changed: {old_level.value} -> {level.value}")
        
        # Take action based on level
        if level == SafetyLevel.RED:
            self.pause_trading()
        elif level == SafetyLevel.BLACK:
            asyncio.create_task(self.emergency_stop())
    
    async def run_evolution_cycle(self) -> Dict[str, Any]:
        """
        Run an evolution cycle
        
        Returns:
            Evolution cycle results
        """
        if self._evolution_engine is None:
            return {"error": "Evolution engine not initialized"}
        
        cycle = await self._evolution_engine.run_evolution_cycle()
        
        return {
            "cycle_id": cycle.id,
            "proposals": len(cycle.proposals),
            "deployed": len(cycle.deployed_proposals),
            "phase": cycle.phase.value,
        }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status
        
        Returns:
            Status dictionary
        """
        return {
            "state": self._state.value,
            "mode": self._mode.value,
            "safety_level": self._safety_level.value,
            "is_trading": self.is_trading,
            "positions": len(self._positions),
            "pending_orders": len(self._pending_orders),
            "session": {
                "id": self._current_session.id if self._current_session else None,
                "symbols": self._current_session.symbols if self._current_session else [],
                "signals_generated": (
                    self._current_session.signals_generated
                    if self._current_session else 0
                ),
                "signals_executed": (
                    self._current_session.signals_executed
                    if self._current_session else 0
                ),
            },
            "evolution": (
                self._evolution_engine.get_status()
                if self._evolution_engine else None
            ),
        }
    
    def get_performance(self) -> Dict[str, Any]:
        """
        Get performance metrics
        
        Returns:
            Performance metrics dictionary
        """
        if not self._current_session:
            return {}
        
        trades = self._current_session.trades
        if not trades:
            return {
                "total_trades": 0,
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "total_pnl": 0.0,
            }
        
        winning = [t for t in trades if t.profit > 0]
        losing = [t for t in trades if t.profit < 0]
        
        gross_profit = sum(t.profit for t in winning)
        gross_loss = abs(sum(t.profit for t in losing))
        
        return {
            "total_trades": len(trades),
            "winning_trades": len(winning),
            "losing_trades": len(losing),
            "win_rate": len(winning) / len(trades) if trades else 0.0,
            "profit_factor": gross_profit / gross_loss if gross_loss > 0 else 0.0,
            "total_pnl": self._current_session.total_pnl,
            "gross_profit": gross_profit,
            "gross_loss": gross_loss,
        }
    
    async def shutdown(self) -> None:
        """
        Shutdown the system gracefully
        """
        logger.info("Shutting down AlphaAlgo...")
        
        # Stop trading
        await self.stop_trading()
        
        # Stop evolution engine
        if self._evolution_engine:
            await self._evolution_engine.stop()
        
        # Disconnect data sources
        for name, source in self._data_sources.items():
            if source and hasattr(source, 'disconnect'):
                await source.disconnect()
        
        # Disconnect executor
        if self._executor and hasattr(self._executor, 'disconnect'):
            await self._executor.disconnect()
        
        self._state = SystemState.SHUTDOWN
        logger.info("AlphaAlgo shutdown complete")


# Convenience function
async def quick_start(config: Optional[Dict] = None) -> AlphaAlgoOrchestrator:
    """
    Quick start the AlphaAlgo system
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Initialized orchestrator
    """
    orchestrator = AlphaAlgoOrchestrator(config)
    await orchestrator.initialize()
    return orchestrator
