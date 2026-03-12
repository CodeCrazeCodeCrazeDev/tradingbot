"""
Unified Trading System
======================

The master system that integrates all 6 layers into a cohesive trading platform.

This is the single entry point for the entire trading bot, combining:
- Layer 1: Data Foundation
- Layer 2: Intelligence Core
- Layer 3: Strategy Engine
- Layer 4: Execution Layer
- Layer 5: Risk & Safety
- Layer 6: Orchestration

Features:
- QwenCodeMender-inspired Generator-Verifier architecture
- 257 Expert Mixture of Experts
- 10-layer Cognitive Architecture
- Offline RL (CQL, BCQ, IQL)
- Hardware-aware resource scaling
- Human-in-loop evolution
- Multi-layer fail-safes
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
from pathlib import Path
import json

# Import all layers
from .layer1_data_foundation import DataFoundation
from .layer2_intelligence_core import IntelligenceCore
from .layer3_strategy_engine import StrategyEngine, SignalDirection
from .layer4_execution import ExecutionLayer, OrderSide
from .layer5_risk_safety import RiskSafetyLayer, RiskLevel
from .layer6_orchestration import MasterOrchestrator, OperationMode

logger = logging.getLogger(__name__)


class TradingMode(Enum):
    """Trading modes"""
    LIVE = "live"
    PAPER = "paper"
    BACKTEST = "backtest"
    SIMULATION = "simulation"


class SystemStatus(Enum):
    """System status"""
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    SHUTDOWN = "shutdown"


@dataclass
class SystemConfig:
    """Complete system configuration"""
    # Trading mode
    mode: TradingMode = TradingMode.PAPER
    
    # Symbols to trade
    symbols: List[str] = field(default_factory=lambda: ["BTCUSDT"])
    
    # Capital
    initial_capital: float = 100000.0
    
    # Risk parameters
    max_risk_per_trade: float = 2.0
    max_daily_loss: float = 5.0
    max_drawdown: float = 20.0
    max_positions: int = 10
    
    # Timing
    cycle_interval_seconds: int = 60
    daily_report_hour: int = 17
    
    # Operation mode
    operation_mode: str = "semi_autonomous"
    
    # Paths
    data_dir: str = "trading_data"
    log_dir: str = "trading_logs"
    
    # Layer configs
    data_config: Dict = field(default_factory=dict)
    intelligence_config: Dict = field(default_factory=dict)
    strategy_config: Dict = field(default_factory=dict)
    execution_config: Dict = field(default_factory=dict)
    risk_config: Dict = field(default_factory=dict)
    orchestration_config: Dict = field(default_factory=dict)


@dataclass
class TradingDecision:
    """Final trading decision from the system"""
    decision_id: str
    timestamp: datetime
    symbol: str
    
    # Action
    action: str  # BUY, SELL, HOLD
    
    # Position details
    entry_price: float
    stop_loss: float
    take_profit: float
    position_size: float
    
    # Confidence
    signal_confidence: float
    verification_score: float
    risk_score: float
    
    # Reasoning
    reasoning: str
    expert_analysis: Dict[str, Any]
    
    # Execution
    executed: bool = False
    execution_result: Optional[Dict] = None


class UnifiedTradingSystem:
    """
    The Unified Trading System
    
    Integrates all 6 layers into a complete autonomous trading platform
    with QwenCodeMender-inspired innovations.
    
    Usage:
        system = UnifiedTradingSystem(config)
        await system.initialize()
        await system.start()
    """
    
    def __init__(self, config: Optional[SystemConfig] = None):
        self.config = config or SystemConfig()
        self.status = SystemStatus.INITIALIZING
        
        # Create directories
        Path(self.config.data_dir).mkdir(parents=True, exist_ok=True)
        Path(self.config.log_dir).mkdir(parents=True, exist_ok=True)
        
        # Initialize layers
        self._init_layers()
        
        # Wire layers together
        self._wire_layers()
        
        # State tracking
        self.start_time: Optional[datetime] = None
        self.decisions: List[TradingDecision] = []
        self.max_decisions = 10000
        
        # Background tasks
        self._tasks: List[asyncio.Task] = []
        self._stop_requested = False
        
        logger.info("=" * 60)
        logger.info("UNIFIED TRADING SYSTEM INITIALIZED")
        logger.info("=" * 60)
        logger.info(f"Mode: {self.config.mode.value}")
        logger.info(f"Symbols: {self.config.symbols}")
        logger.info(f"Initial Capital: ${self.config.initial_capital:,.2f}")
        logger.info("=" * 60)
    
    def _init_layers(self):
        """Initialize all layers"""
        logger.info("Initializing layers...")
        
        # Layer 1: Data Foundation
        self.data_layer = DataFoundation(self.config.data_config)
        logger.info("✓ Layer 1: Data Foundation")
        
        # Layer 2: Intelligence Core
        self.intelligence_layer = IntelligenceCore(self.config.intelligence_config)
        logger.info("✓ Layer 2: Intelligence Core")
        
        # Layer 3: Strategy Engine
        self.strategy_layer = StrategyEngine(self.config.strategy_config)
        logger.info("✓ Layer 3: Strategy Engine")
        
        # Layer 4: Execution Layer
        self.execution_layer = ExecutionLayer(self.config.execution_config)
        logger.info("✓ Layer 4: Execution Layer")
        
        # Layer 5: Risk & Safety
        risk_config = {
            'risk': {
                'initial_equity': self.config.initial_capital,
                'limits': {
                    'max_risk_per_trade_pct': self.config.max_risk_per_trade,
                    'max_daily_loss_pct': self.config.max_daily_loss,
                    'max_drawdown_pct': self.config.max_drawdown,
                    'max_positions': self.config.max_positions
                }
            },
            **self.config.risk_config
        }
        self.risk_layer = RiskSafetyLayer(risk_config)
        logger.info("✓ Layer 5: Risk & Safety")
        
        # Layer 6: Orchestration
        orch_config = {
            'autonomous': {
                'mode': self.config.operation_mode,
                'cycle_interval': self.config.cycle_interval_seconds
            },
            **self.config.orchestration_config
        }
        self.orchestrator = MasterOrchestrator(orch_config)
        logger.info("✓ Layer 6: Orchestration")
    
    def _wire_layers(self):
        """Wire layers together"""
        self.orchestrator.set_layers(
            data=self.data_layer,
            intelligence=self.intelligence_layer,
            strategy=self.strategy_layer,
            execution=self.execution_layer,
            risk=self.risk_layer
        )
        logger.info("✓ Layers wired together")
    
    async def initialize(self) -> bool:
        """Initialize the system (connect to data sources, etc.)"""
        logger.info("Connecting to data sources...")
        
        # Connect data layer
        connection_results = await self.data_layer.connect_all()
        
        connected = sum(1 for v in connection_results.values() if v)
        total = len(connection_results)
        
        logger.info(f"Data sources connected: {connected}/{total}")
        
        if connected == 0:
            logger.error("No data sources connected!")
            self.status = SystemStatus.ERROR
            return False
        
        self.status = SystemStatus.READY
        logger.info("System initialized and ready")
        
        return True
    
    async def start(self):
        """Start the trading system"""
        if self.status != SystemStatus.READY:
            logger.error("System not ready to start")
            return
        
        self.status = SystemStatus.RUNNING
        self.start_time = datetime.now()
        self._stop_requested = False
        
        logger.info("=" * 60)
        logger.info("TRADING SYSTEM STARTED")
        logger.info("=" * 60)
        
        # Send startup notification
        self.orchestrator.human_protocol.send_message(
            message_type=self.orchestrator.human_protocol.messages.__class__.__bases__[0].__subclasses__()[0] if hasattr(self.orchestrator.human_protocol, 'messages') else None,
            priority=None,
            subject="Trading System Started",
            content=f"Unified Trading System started at {self.start_time}\n"
                   f"Mode: {self.config.mode.value}\n"
                   f"Symbols: {', '.join(self.config.symbols)}"
        ) if False else None  # Simplified - would use proper message type
        
        # Start main loop
        await self._main_loop()
    
    async def _main_loop(self):
        """Main trading loop"""
        while not self._stop_requested and self.status == SystemStatus.RUNNING:
            try:
                # Run trading cycle for each symbol
                for symbol in self.config.symbols:
                    if self._stop_requested:
                        break
                    
                    # Run cycle
                    result = await self.orchestrator.run_trading_cycle(symbol)
                    
                    # Log result
                    if 'error' not in result:
                        logger.info(f"Cycle completed for {symbol}")
                    else:
                        logger.error(f"Cycle error for {symbol}: {result['error']}")
                
                # Check for daily report time
                now = datetime.now()
                if now.hour == self.config.daily_report_hour and now.minute < 5:
                    self.orchestrator.send_daily_report()
                
                # Wait for next cycle
                await asyncio.sleep(self.config.cycle_interval_seconds)
                
            except asyncio.CancelledError:
                logger.info("Main loop cancelled")
                break
            except Exception as e:
                logger.error(f"Main loop error: {e}")
                self.risk_layer.record_error(str(e))
                await asyncio.sleep(5)  # Brief pause on error
        
        logger.info("Main loop ended")
    
    async def stop(self):
        """Stop the trading system gracefully"""
        logger.info("Stopping trading system...")
        
        self._stop_requested = True
        self.orchestrator.autonomous.request_stop()
        
        # Cancel background tasks
        for task in self._tasks:
            task.cancel()
        
        # Disconnect data sources
        await self.data_layer.disconnect_all()
        
        self.status = SystemStatus.SHUTDOWN
        
        # Send shutdown notification
        logger.info("Trading system stopped")
    
    async def analyze_symbol(self, symbol: str) -> TradingDecision:
        """
        Analyze a symbol and generate a trading decision
        
        This runs the complete analysis pipeline without execution
        """
        decision_id = f"dec_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{symbol}"
        
        # Fetch data
        data = await self.data_layer.fetch_all(symbol)
        
        if not data or 'data' not in data:
            return TradingDecision(
                decision_id=decision_id,
                timestamp=datetime.now(),
                symbol=symbol,
                action="HOLD",
                entry_price=0,
                stop_loss=0,
                take_profit=0,
                position_size=0,
                signal_confidence=0,
                verification_score=0,
                risk_score=0,
                reasoning="No data available"
            )
        
        # Run intelligence analysis
        intelligence_output = await self.intelligence_layer.analyze(data['data'], symbol)
        
        # Generate signal
        market_data = data['data'].get('market')
        if market_data is None:
            return TradingDecision(
                decision_id=decision_id,
                timestamp=datetime.now(),
                symbol=symbol,
                action="HOLD",
                entry_price=0,
                stop_loss=0,
                take_profit=0,
                position_size=0,
                signal_confidence=intelligence_output.confidence,
                verification_score=0,
                risk_score=0,
                reasoning="No market data"
            )
        
        signal = await self.strategy_layer.generate_signal(
            symbol=symbol,
            market_data=market_data,
            indicators={},
            sentiment=data['data'].get('sentiment', {})
        )
        
        if signal is None:
            return TradingDecision(
                decision_id=decision_id,
                timestamp=datetime.now(),
                symbol=symbol,
                action="HOLD",
                entry_price=0,
                stop_loss=0,
                take_profit=0,
                position_size=0,
                signal_confidence=intelligence_output.confidence,
                verification_score=0,
                risk_score=0,
                reasoning="No signal generated"
            )
        
        # Check risk
        risk_result = self.risk_layer.pre_trade_check(
            symbol=symbol,
            side=signal.direction.value,
            size=signal.position_size,
            entry_price=signal.entry_price,
            stop_loss=signal.stop_loss
        )
        
        # Build decision
        decision = TradingDecision(
            decision_id=decision_id,
            timestamp=datetime.now(),
            symbol=symbol,
            action=signal.direction.value.upper(),
            entry_price=signal.entry_price,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
            position_size=risk_result.adjusted_size,
            signal_confidence=signal.confidence,
            verification_score=signal.verification_score,
            risk_score=1.0 - (risk_result.risk_level.value == 'critical') * 0.5,
            reasoning=signal.reasoning,
            expert_analysis={
                'intelligence_signal': intelligence_output.signal,
                'expert_weights': intelligence_output.expert_weights,
                'market_regime': intelligence_output.market_regime
            }
        )
        
        # Store decision
        self.decisions.append(decision)
        if len(self.decisions) > self.max_decisions:
            self.decisions.pop(0)
        
        return decision
    
    async def execute_decision(self, decision: TradingDecision) -> Dict[str, Any]:
        """Execute a trading decision"""
        if decision.action == "HOLD":
            return {'executed': False, 'reason': 'HOLD signal'}
        
        # Execute
        side = OrderSide.BUY if decision.action == "BUY" else OrderSide.SELL
        
        result = await self.execution_layer.execute(
            symbol=decision.symbol,
            side=side,
            quantity=decision.position_size,
            price=decision.entry_price
        )
        
        decision.executed = result.success
        decision.execution_result = {
            'success': result.success,
            'order_id': result.order.order_id if result.order else None,
            'slippage_bps': result.slippage_bps,
            'execution_time_ms': result.execution_time_ms
        }
        
        return decision.execution_result
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            'system': {
                'status': self.status.value,
                'mode': self.config.mode.value,
                'uptime': str(datetime.now() - self.start_time) if self.start_time else None,
                'symbols': self.config.symbols
            },
            'layers': {
                'data': self.data_layer.get_status(),
                'intelligence': self.intelligence_layer.get_status(),
                'strategy': self.strategy_layer.get_status(),
                'execution': self.execution_layer.get_status(),
                'risk': self.risk_layer.get_status()
            },
            'orchestration': self.orchestrator.get_status(),
            'decisions': {
                'total': len(self.decisions),
                'recent': [
                    {
                        'id': d.decision_id,
                        'symbol': d.symbol,
                        'action': d.action,
                        'confidence': d.signal_confidence,
                        'executed': d.executed
                    }
                    for d in self.decisions[-5:]
                ]
            }
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get trading statistics"""
        return {
            'orchestrator': self.orchestrator.stats,
            'strategy': self.strategy_layer.stats,
            'execution': self.execution_layer.stats,
            'risk': {
                'equity': self.risk_layer.risk_manager.equity,
                'drawdown': self.risk_layer.risk_manager._calculate_drawdown(),
                'positions': len(self.risk_layer.risk_manager.positions)
            }
        }
    
    def save_state(self, filepath: Optional[str] = None):
        """Save system state to file"""
        filepath = filepath or f"{self.config.data_dir}/system_state.json"
        
        state = {
            'timestamp': datetime.now().isoformat(),
            'status': self.status.value,
            'config': {
                'mode': self.config.mode.value,
                'symbols': self.config.symbols,
                'initial_capital': self.config.initial_capital
            },
            'statistics': self.get_statistics(),
            'decisions_count': len(self.decisions)
        }
        
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)
        
        logger.info(f"State saved to {filepath}")
    
    def load_state(self, filepath: Optional[str] = None):
        """Load system state from file"""
        filepath = filepath or f"{self.config.data_dir}/system_state.json"
        
        try:
            with open(filepath, 'r') as f:
                state = json.load(f)
            
            logger.info(f"State loaded from {filepath}")
            return state
        except FileNotFoundError:
            logger.warning(f"State file not found: {filepath}")
            return None


# Factory functions for easy creation
def create_unified_system(
    mode: str = 'paper',
    symbols: Optional[List[str]] = None,
    initial_capital: float = 100000,
    **kwargs
) -> UnifiedTradingSystem:
    """
    Create a Unified Trading System with common configuration
    
    Args:
        mode: Trading mode ('live', 'paper', 'backtest', 'simulation')
        symbols: List of symbols to trade
        initial_capital: Starting capital
        **kwargs: Additional configuration
        
    Returns:
        Configured UnifiedTradingSystem instance
    """
    config = SystemConfig(
        mode=TradingMode(mode),
        symbols=symbols or ["BTCUSDT"],
        initial_capital=initial_capital,
        **kwargs
    )
    
    return UnifiedTradingSystem(config)


async def quick_start(
    symbols: Optional[List[str]] = None,
    mode: str = 'paper',
    capital: float = 100000
) -> UnifiedTradingSystem:
    """
    Quick start the trading system
    
    Args:
        symbols: Symbols to trade
        mode: Trading mode
        capital: Initial capital
        
    Returns:
        Running UnifiedTradingSystem instance
    """
    system = create_unified_system(
        mode=mode,
        symbols=symbols or ["BTCUSDT"],
        initial_capital=capital
    )
    
    await system.initialize()
    
    return system


# Main entry point for direct execution
if __name__ == "__main__":
    import sys

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
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


    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    async def main():
        # Create system
        system = create_unified_system(
            mode='paper',
            symbols=['BTCUSDT', 'ETHUSDT'],
            initial_capital=100000
        )
        
        # Initialize
        if not await system.initialize():
            logger.info("Failed to initialize system")
            return
        
        # Run analysis
        logger.info("\nAnalyzing BTCUSDT...")
        decision = await system.analyze_symbol('BTCUSDT')
        
        logger.info(f"\nDecision: {decision.action}")
        logger.info(f"Confidence: {decision.signal_confidence:.2%}")
        logger.info(f"Entry: {decision.entry_price}")
        logger.info(f"Stop Loss: {decision.stop_loss}")
        logger.info(f"Take Profit: {decision.take_profit}")
        logger.info(f"Position Size: {decision.position_size}")
        logger.info(f"\nReasoning: {decision.reasoning}")
        
        # Get status
        logger.info("\nSystem Status:")
        status = system.get_status()
        print(json.dumps(status, indent=2, default=str))
        
        # Stop
        await system.stop()
    
    asyncio.run(main())
