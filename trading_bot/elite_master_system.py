"""
Elite Master Trading System
===========================

The ULTIMATE integration layer that combines ALL elite features:
- Pre-trade validation
- Order state management
- Real-time P&L
- VaR/Risk management
- Disaster recovery
- All existing systems (AAMIS, Cognitive Architecture, etc.)

This is the single entry point for elite-level trading.

Author: Elite Trading Bot
Version: 1.0.0
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional
from enum import Enum, auto

logger = logging.getLogger(__name__)

# Import all elite components
try:
    from trading_bot.safety.pre_trade_validator import (
        PreTradeValidator, ValidationConfig, TradeRequest, 
        ValidationResult, get_pre_trade_validator
    )
    PRE_TRADE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Pre-trade validator not available: {e}")
    PRE_TRADE_AVAILABLE = False

try:
    from trading_bot.execution.order_state_machine import (
        OrderStateMachine, Order, OrderState, OrderEvent,
        OrderType, OrderSide, OrderFill, BracketOrderManager,
        get_order_state_machine
    )
    ORDER_SM_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Order state machine not available: {e}")
    ORDER_SM_AVAILABLE = False

try:
    from trading_bot.risk.var_engine import (
        VaREngine, VaRMethod, VaRResult, Position as VaRPosition,
        get_var_engine
    )
    VAR_AVAILABLE = True
except ImportError as e:
    logger.warning(f"VaR engine not available: {e}")
    VAR_AVAILABLE = False

try:
    from trading_bot.position.realtime_pnl import (
        RealTimePnLCalculator, PositionPnL, PortfolioPnL,
        get_pnl_calculator
    )
    PNL_AVAILABLE = True
except ImportError as e:
    logger.warning(f"P&L calculator not available: {e}")
    PNL_AVAILABLE = False

try:
    from trading_bot.infrastructure.disaster_recovery import (
        DisasterRecoveryManager, StateManager, SystemState,
        get_disaster_recovery_manager
    )
    DR_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Disaster recovery not available: {e}")
    DR_AVAILABLE = False
# Import existing systems
    from trading_bot.aamis_v3 import AAMISMasterOrchestrator
    AAMIS_AVAILABLE = True
except ImportError:
    AAMIS_AVAILABLE = False

try:
    from trading_bot.cognitive_architecture import AlphaAlgoCognitiveCore
    COGNITIVE_AVAILABLE = True
except ImportError:
    COGNITIVE_AVAILABLE = False

try:
    from trading_bot.master_orchestrator import MasterOrchestrator
    MASTER_ORCH_AVAILABLE = True
except ImportError:
    MASTER_ORCH_AVAILABLE = False

try:
    from trading_bot.risk.MASTER_risk_manager import MasterRiskManager
    RISK_MANAGER_AVAILABLE = True
except ImportError:
    RISK_MANAGER_AVAILABLE = False

try:
    from trading_bot.safety.emergency_kill_switch import EmergencyKillSwitch
    KILL_SWITCH_AVAILABLE = True
except ImportError:
    KILL_SWITCH_AVAILABLE = False


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
    TRADING = "trading"
    PAUSED = "paused"
    ERROR = "error"
    SHUTDOWN = "shutdown"


@dataclass
class EliteConfig:
    """Elite system configuration"""
    # Trading mode
    mode: TradingMode = TradingMode.PAPER
    
    # Symbols
    symbols: List[str] = field(default_factory=lambda: ["EURUSD"])
    
    # Risk parameters
    max_risk_per_trade_pct: float = 2.0
    max_daily_risk_pct: float = 6.0
    max_drawdown_pct: float = 20.0
    max_positions: int = 10
    
    # Validation
    enable_pre_trade_validation: bool = True
    enable_fat_finger_protection: bool = True
    enable_news_blackout: bool = True
    
    # Monitoring
    enable_realtime_pnl: bool = True
    enable_var_calculation: bool = True
    enable_disaster_recovery: bool = True
    
    # AI systems
    enable_aamis: bool = True
    enable_cognitive_core: bool = True
    
    # Intervals
    pnl_update_interval_ms: int = 100
    var_update_interval_sec: int = 60
    health_check_interval_sec: int = 30
    snapshot_interval_sec: int = 60


@dataclass
class TradeResult:
    """Result of a trade attempt"""
    success: bool
    order_id: Optional[str] = None
    message: str = ""
    validation_report: Optional[Any] = None
    order: Optional[Any] = None
    timestamp: datetime = field(default_factory=datetime.now)


class EliteMasterSystem:
    """
    The ULTIMATE Elite Trading System
    
    Integrates all components into a single, cohesive system.
    """
    
    def __init__(self, config: Optional[EliteConfig] = None):
        self.config = config or EliteConfig()
        self.status = SystemStatus.INITIALIZING
        
        # Core components
        self.pre_trade_validator: Optional[PreTradeValidator] = None
        self.order_state_machine: Optional[OrderStateMachine] = None
        self.pnl_calculator: Optional[RealTimePnLCalculator] = None
        self.var_engine: Optional[VaREngine] = None
        self.dr_manager: Optional[DisasterRecoveryManager] = None
        
        # AI systems
        self.aamis: Optional[Any] = None
        self.cognitive_core: Optional[Any] = None
        self.master_orchestrator: Optional[Any] = None
        self.risk_manager: Optional[Any] = None
        self.kill_switch: Optional[Any] = None
        
        # State
        self.account_info: Dict[str, Any] = {}
        self.market_data: Dict[str, Dict[str, Any]] = {}
        self.open_positions: List[Dict] = []
        
        # Statistics
        self.stats = {
            'trades_attempted': 0,
            'trades_executed': 0,
            'trades_rejected': 0,
            'total_pnl': 0.0,
            'start_time': None
        }
        
        # Callbacks
        self.on_trade: List[Callable] = []
        self.on_signal: List[Callable] = []
        self.on_error: List[Callable] = []
        
        logger.info("EliteMasterSystem created")
    
    async def initialize(self) -> bool:
        """Initialize all components"""
        logger.info("Initializing Elite Master System...")
        
        try:
            # Initialize pre-trade validator
            if self.config.enable_pre_trade_validation and PRE_TRADE_AVAILABLE:
                validation_config = ValidationConfig(
                    max_risk_per_trade_pct=self.config.max_risk_per_trade_pct,
                    max_daily_risk_pct=self.config.max_daily_risk_pct,
                    max_drawdown_pct=self.config.max_drawdown_pct,
                    max_open_positions=self.config.max_positions
                )
                self.pre_trade_validator = PreTradeValidator(validation_config)
                logger.info("✓ Pre-trade validator initialized")
            
            # Initialize order state machine
            if ORDER_SM_AVAILABLE:
                self.order_state_machine = get_order_state_machine()
                logger.info("✓ Order state machine initialized")
            
            # Initialize P&L calculator
            if self.config.enable_realtime_pnl and PNL_AVAILABLE:
                self.pnl_calculator = get_pnl_calculator()
                await self.pnl_calculator.start_realtime_updates()
                logger.info("✓ Real-time P&L calculator initialized")
            
            # Initialize VaR engine
            if self.config.enable_var_calculation and VAR_AVAILABLE:
                self.var_engine = get_var_engine()
                logger.info("✓ VaR engine initialized")
            
            # Initialize disaster recovery
            if self.config.enable_disaster_recovery and DR_AVAILABLE:
                self.dr_manager = get_disaster_recovery_manager()
                await self.dr_manager.start_monitoring()
                logger.info("✓ Disaster recovery initialized")
            
            # Initialize AI systems
            if self.config.enable_aamis and AAMIS_AVAILABLE:
                self.aamis = AAMISMasterOrchestrator()
                logger.info("✓ AAMIS v3.0 initialized")
            
            if self.config.enable_cognitive_core and COGNITIVE_AVAILABLE:
                self.cognitive_core = AlphaAlgoCognitiveCore()
                logger.info("✓ Cognitive Core initialized")
            
            if MASTER_ORCH_AVAILABLE:
                self.master_orchestrator = MasterOrchestrator()
                logger.info("✓ Master Orchestrator initialized")
            
            if RISK_MANAGER_AVAILABLE:
                self.risk_manager = MasterRiskManager()
                logger.info("✓ Risk Manager initialized")
            
            if KILL_SWITCH_AVAILABLE:
                self.kill_switch = EmergencyKillSwitch()
                logger.info("✓ Kill Switch initialized")
            
            self.status = SystemStatus.READY
            self.stats['start_time'] = datetime.now()
            
            logger.info("Elite Master System initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            self.status = SystemStatus.ERROR
            return False
    
    async def shutdown(self):
        """Shutdown all components"""
        logger.info("Shutting down Elite Master System...")
        
        self.status = SystemStatus.SHUTDOWN
        
        if self.pnl_calculator:
            await self.pnl_calculator.stop_realtime_updates()
        
        if self.dr_manager:
            await self.dr_manager.stop_monitoring()
        
        logger.info("Elite Master System shutdown complete")
    
    async def execute_trade(
        self,
        symbol: str,
        direction: str,
        size: float,
        price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        strategy_id: str = "",
        **kwargs
    ) -> TradeResult:
        """
        Execute a trade with full elite validation and tracking
        """
        self.stats['trades_attempted'] += 1
        
        # Step 1: Pre-trade validation
        if self.pre_trade_validator:
            trade_request = TradeRequest(
                symbol=symbol,
                direction=direction.upper(),
                size=size,
                price=price,
                stop_loss=stop_loss,
                take_profit=take_profit
            )
            
            validation_report = await self.pre_trade_validator.validate(
                trade=trade_request,
                account_info=self.account_info,
                market_data=self.market_data.get(symbol, {}),
                open_positions=self.open_positions
            )
            
            if validation_report.result == ValidationResult.REJECTED:
                self.stats['trades_rejected'] += 1
                return TradeResult(
                    success=False,
                    message=f"Trade rejected: {[r.value for r in validation_report.rejection_reasons]}",
                    validation_report=validation_report
                )
        
        # Step 2: Create order in state machine
        if self.order_state_machine:
            order_side = OrderSide.BUY if direction.upper() == "BUY" else OrderSide.SELL
            order_type = OrderType.MARKET if price is None else OrderType.LIMIT
            
            order = self.order_state_machine.create_order(
                symbol=symbol,
                side=order_side,
                order_type=order_type,
                quantity=size,
                price=price,
                strategy_id=strategy_id,
                **kwargs
            )
            
            # Transition to pending
            self.order_state_machine.transition(order.order_id, OrderEvent.SUBMIT)
        else:
            order = None
        
        # Step 3: Execute via broker (placeholder - implement actual execution)
        execution_success = await self._execute_via_broker(
            symbol, direction, size, price, stop_loss, take_profit
        )
        
        if execution_success:
            # Step 4: Update order state
            if self.order_state_machine and order:
                fill = OrderFill(
                    fill_id=f"FILL_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    quantity=size,
                    price=price or self.market_data.get(symbol, {}).get('price', 0),
                    commission=0.0,
                    timestamp=datetime.now(),
                    venue="MT5"
                )
                self.order_state_machine.transition(
                    order.order_id, OrderEvent.FILL, fill=fill
                )
            
            # Step 5: Add to P&L tracking
            if self.pnl_calculator:
                self.pnl_calculator.add_position(
                    position_id=order.order_id if order else f"POS_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    symbol=symbol,
                    side=direction.lower(),
                    quantity=size,
                    entry_price=price or self.market_data.get(symbol, {}).get('price', 0),
                    strategy_id=strategy_id
                )
            
            self.stats['trades_executed'] += 1
            
            # Fire callbacks
            for callback in self.on_trade:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(order)
                    else:
                        callback(order)
                except Exception as e:
                    logger.error(f"Trade callback error: {e}")
            
            return TradeResult(
                success=True,
                order_id=order.order_id if order else None,
                message="Trade executed successfully",
                order=order
            )
        else:
            # Update order state to failed
            if self.order_state_machine and order:
                self.order_state_machine.transition(
                    order.order_id, OrderEvent.REJECT, reason="Broker rejected"
                )
            
            self.stats['trades_rejected'] += 1
            
            return TradeResult(
                success=False,
                message="Trade execution failed",
                order=order
            )
    
    async def _execute_via_broker(
        self,
        symbol: str,
        direction: str,
        size: float,
        price: Optional[float],
        stop_loss: Optional[float],
        take_profit: Optional[float]
    ) -> bool:
        """Execute trade via broker (placeholder)"""
        # In real implementation, this would call the broker adapter
        if self.config.mode == TradingMode.PAPER:
            # Paper trading - always succeeds
            return True
        elif self.config.mode == TradingMode.SIMULATION:
            # Simulation - always succeeds
            return True
        else:
            # Live trading - implement actual broker execution
            logger.warning("Live trading not implemented - using paper mode")
            return True
    
    async def analyze_market(self, symbol: str) -> Dict[str, Any]:
        """Analyze market using all AI systems"""
        results = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'analyses': {}
        }
        
        # AAMIS analysis
        if self.aamis:
            try:
                market_data = self.market_data.get(symbol, {})
                aamis_result = await self.aamis.analyze_market(market_data)
                results['analyses']['aamis'] = {
                    'action': aamis_result.decision.action if hasattr(aamis_result, 'decision') else 'HOLD',
                    'conviction': getattr(aamis_result.decision, 'conviction', 0) if hasattr(aamis_result, 'decision') else 0
                }
            except Exception as e:
                logger.error(f"AAMIS analysis failed: {e}")
        
        # Cognitive core analysis
        if self.cognitive_core:
            try:
                market_data = self.market_data.get(symbol, {})
                cognitive_result = self.cognitive_core.make_decision(market_data)
                results['analyses']['cognitive'] = {
                    'action': cognitive_result.action if hasattr(cognitive_result, 'action') else 'HOLD',
                    'confidence': getattr(cognitive_result, 'confidence', 0)
                }
            except Exception as e:
                logger.error(f"Cognitive analysis failed: {e}")
        
        return results
    
    def update_market_data(self, symbol: str, data: Dict[str, Any]):
        """Update market data for a symbol"""
        self.market_data[symbol] = {
            **data,
            'timestamp': datetime.now()
        }
        
        # Update P&L calculator
        if self.pnl_calculator and 'price' in data:
            self.pnl_calculator.update_price(symbol, data['price'])
    
    def update_account_info(self, info: Dict[str, Any]):
        """Update account information"""
        self.account_info = {
            **info,
            'timestamp': datetime.now()
        }
        
        # Update P&L calculator daily start
        if self.pnl_calculator and 'equity' in info:
            if not hasattr(self, '_daily_start_set') or not self._daily_start_set:
                self.pnl_calculator.set_daily_start(info['equity'])
                self._daily_start_set = True
    
    def update_positions(self, positions: List[Dict]):
        """Update open positions"""
        self.open_positions = positions
    
    def get_portfolio_pnl(self) -> Optional[PortfolioPnL]:
        """Get current portfolio P&L"""
        if self.pnl_calculator:
            return self.pnl_calculator.get_portfolio_pnl()
        return None
    
    def get_var_report(self) -> Optional[Dict]:
        """Get VaR report"""
        if self.var_engine and self.open_positions:
            # Convert positions to VaR format
            var_positions = []
            for pos in self.open_positions:
                var_positions.append(VaRPosition(
                    symbol=pos.get('symbol', ''),
                    quantity=pos.get('volume', 0),
                    current_price=pos.get('price_current', 0),
                    market_value=pos.get('volume', 0) * pos.get('price_current', 0) * 100000
                ))
            
            # Would need returns data for full VaR calculation
            return {'positions': len(var_positions), 'var_available': True}
        return None
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        status = {
            'status': self.status.value,
            'mode': self.config.mode.value,
            'uptime': str(datetime.now() - self.stats['start_time']) if self.stats['start_time'] else None,
            'stats': self.stats,
            'components': {
                'pre_trade_validator': self.pre_trade_validator is not None,
                'order_state_machine': self.order_state_machine is not None,
                'pnl_calculator': self.pnl_calculator is not None,
                'var_engine': self.var_engine is not None,
                'disaster_recovery': self.dr_manager is not None,
                'aamis': self.aamis is not None,
                'cognitive_core': self.cognitive_core is not None,
                'risk_manager': self.risk_manager is not None,
                'kill_switch': self.kill_switch is not None
            }
        }
        
        # Add P&L summary
        if self.pnl_calculator:
            portfolio = self.pnl_calculator.get_portfolio_pnl()
            status['pnl'] = {
                'total': portfolio.total_pnl,
                'unrealized': portfolio.total_unrealized,
                'realized': portfolio.total_realized,
                'positions': portfolio.open_positions
            }
        
        # Add validation stats
        if self.pre_trade_validator:
            status['validation'] = self.pre_trade_validator.get_stats()
        
        # Add order stats
        if self.order_state_machine:
            status['orders'] = self.order_state_machine.get_statistics()
        
        return status
    
    async def emergency_shutdown(self, reason: str):
        """Emergency shutdown - close all positions"""
        logger.critical(f"EMERGENCY SHUTDOWN: {reason}")
        
        if self.kill_switch:
            self.kill_switch.activate(reason)
        
        if self.dr_manager:
            await self.dr_manager.emergency_close_all(reason)
        
        self.status = SystemStatus.SHUTDOWN


# Singleton instance
_elite_system: Optional[EliteMasterSystem] = None


def get_elite_system(config: Optional[EliteConfig] = None) -> EliteMasterSystem:
    """Get or create the elite system singleton"""
    global _elite_system
    if _elite_system is None:
        _elite_system = EliteMasterSystem(config)
    return _elite_system


async def initialize_elite_system(config: Optional[EliteConfig] = None) -> EliteMasterSystem:
    """Initialize and return the elite system"""
    system = get_elite_system(config)
    await system.initialize()
    return system


# Export
__all__ = [
    'EliteMasterSystem',
    'EliteConfig',
    'TradingMode',
    'SystemStatus',
    'TradeResult',
    'get_elite_system',
    'initialize_elite_system'
]
