"""
Trading Orchestrator
Central coordinator for all trading operations
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class TradingMode(Enum):
    """Trading modes"""
    PAPER = "paper"
    LIVE = "live"
    BACKTEST = "backtest"


class SignalType(Enum):
    """Signal types"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    CLOSE = "close"


@dataclass
class TradingSignal:
    """Trading signal"""
    symbol: str
    signal_type: SignalType
    confidence: float
    price: float
    timestamp: datetime
    reasons: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Position:
    """Trading position"""
    symbol: str
    side: str  # 'long' or 'short'
    entry_price: float
    quantity: float
    entry_time: datetime
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    current_price: Optional[float] = None
    unrealized_pnl: float = 0.0


class TradingOrchestrator:
    """
    Central orchestrator for trading operations
    
    Coordinates:
    - Signal generation
    - Risk management
    - Order execution
    - Position management
    - Performance tracking
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.mode = TradingMode(config.get('trading', {}).get('mode', 'paper'))
        
        # State
        self.positions: Dict[str, Position] = {}
        self.pending_signals: List[TradingSignal] = []
        self.trade_history: List[Dict[str, Any]] = []
        
        # Risk parameters
        risk_config = config.get('risk', {})
        self.max_risk_per_trade = risk_config.get('max_risk_per_trade', 0.02)
        self.max_daily_loss = risk_config.get('max_daily_loss', 0.05)
        self.max_drawdown = risk_config.get('max_drawdown', 0.20)
        self.max_positions = config.get('trading', {}).get('max_concurrent_positions', 5)
        
        # Performance tracking
        self.daily_pnl = 0.0
        self.total_pnl = 0.0
        self.peak_equity = 0.0
        self.current_drawdown = 0.0
        
        # Components (lazy loaded)
        self._signal_generator = None
        self._risk_manager = None
        self._executor = None
        
        logger.info(f"Trading orchestrator initialized in {self.mode.value} mode")
        
    async def initialize(self):
        """Initialize all components"""
        logger.info("Initializing trading orchestrator components...")
        
        try:
            # Initialize signal generator
            from trading_bot.signals import SignalGenerator
            self._signal_generator = SignalGenerator(self.config)
            logger.info("  Signal generator initialized")
        except ImportError:
            logger.warning("  Signal generator not available")
        # Initialize risk manager
            from trading_bot.risk import RiskManager
            self._risk_manager = RiskManager(self.config.get('risk', {}))
            logger.info("  Risk manager initialized")
        except ImportError:
            logger.warning("  Risk manager not available")
        # Initialize executor
            from trading_bot.execution import OrderExecutor
            self._executor = OrderExecutor(self.config)
            logger.info("  Order executor initialized")
        except ImportError:
            logger.warning("  Order executor not available")
            
        logger.info("Trading orchestrator initialization complete")
        
    async def generate_signal(self, symbol: str, market_data: Dict[str, Any]) -> Optional[TradingSignal]:
        """
        Generate trading signal for a symbol
        
        Args:
            symbol: Trading symbol
            market_data: Current market data
            
        Returns:
            TradingSignal if conditions met, None otherwise
        """
        try:
            price = market_data.get('price', 0)
            
            if price <= 0:
                return None
                
            # Simple signal generation (replace with actual strategy)
            signal = await self._analyze_market(symbol, market_data)
            
            if signal and signal.confidence >= 0.7:
                # Validate against risk limits
                if await self._validate_signal(signal):
                    self.pending_signals.append(signal)
                    logger.info(f"Signal generated: {symbol} {signal.signal_type.value} @ {price}")
                    return signal
                    
            return None
            
        except Exception as e:
            logger.error(f"Error generating signal for {symbol}: {e}")
            return None
            
    async def _analyze_market(self, symbol: str, market_data: Dict[str, Any]) -> Optional[TradingSignal]:
        """Analyze market and generate signal"""
        price = market_data.get('price', 0)
        change_24h = market_data.get('change_24h', 0)
        
        # Simple momentum strategy (placeholder)
        if change_24h > 3:  # Strong upward momentum
            return TradingSignal(
                symbol=symbol,
                signal_type=SignalType.BUY,
                confidence=min(0.5 + change_24h / 20, 0.9),
                price=price,
                timestamp=datetime.now(),
                reasons=[f"Strong momentum: +{change_24h:.1f}%"]
            )
        elif change_24h < -3:  # Strong downward momentum
            return TradingSignal(
                symbol=symbol,
                signal_type=SignalType.SELL,
                confidence=min(0.5 + abs(change_24h) / 20, 0.9),
                price=price,
                timestamp=datetime.now(),
                reasons=[f"Strong momentum: {change_24h:.1f}%"]
            )
            
        return TradingSignal(
            symbol=symbol,
            signal_type=SignalType.HOLD,
            confidence=0.5,
            price=price,
            timestamp=datetime.now(),
            reasons=["No clear signal"]
        )
        
    async def _validate_signal(self, signal: TradingSignal) -> bool:
        """Validate signal against risk limits"""
        # Check position limits
        if len(self.positions) >= self.max_positions:
            if signal.signal_type in [SignalType.BUY, SignalType.SELL]:
                logger.warning(f"Max positions ({self.max_positions}) reached")
                return False
                
        # Check daily loss limit
        if self.daily_pnl <= -self.max_daily_loss * 10000:  # Assuming $10k capital
            logger.warning("Daily loss limit reached")
            return False
            
        # Check drawdown limit
        if self.current_drawdown >= self.max_drawdown:
            logger.warning("Max drawdown reached")
            return False
            
        return True
        
    async def execute_signal(self, signal: TradingSignal) -> bool:
        """
        Execute a trading signal
        
        Args:
            signal: Signal to execute
            
        Returns:
            True if executed successfully
        """
        if self.mode == TradingMode.PAPER:
            return await self._paper_execute(signal)
        elif self.mode == TradingMode.LIVE:
            return await self._live_execute(signal)
        else:
            return False
            
    async def _paper_execute(self, signal: TradingSignal) -> bool:
        """Execute signal in paper trading mode"""
        try:
            if signal.signal_type == SignalType.BUY:
                # Calculate position size
                position_size = self._calculate_position_size(signal.price)
                
                # Create position
                position = Position(
                    symbol=signal.symbol,
                    side='long',
                    entry_price=signal.price,
                    quantity=position_size,
                    entry_time=datetime.now(),
                    stop_loss=signal.price * 0.98,  # 2% stop loss
                    take_profit=signal.price * 1.06,  # 6% take profit
                )
                
                self.positions[signal.symbol] = position
                logger.info(f"PAPER: Opened long {signal.symbol} @ {signal.price}")
                return True
                
            elif signal.signal_type == SignalType.SELL:
                if signal.symbol in self.positions:
                    position = self.positions[signal.symbol]
                    pnl = (signal.price - position.entry_price) * position.quantity
                    
                    self.daily_pnl += pnl
                    self.total_pnl += pnl
                    
                    del self.positions[signal.symbol]
                    logger.info(f"PAPER: Closed {signal.symbol} @ {signal.price}, PnL: ${pnl:.2f}")
                    return True
                    
            return False
            
        except Exception as e:
            logger.error(f"Paper execution error: {e}")
            return False
            
    async def _live_execute(self, signal: TradingSignal) -> bool:
        """Execute signal in live trading mode"""
        logger.warning("Live execution not implemented - use paper mode")
        return False
        
    def _calculate_position_size(self, price: float) -> float:
        """Calculate position size based on risk"""
        capital = 10000  # Placeholder
        risk_amount = capital * self.max_risk_per_trade
        stop_distance = price * 0.02  # 2% stop
        
        if stop_distance > 0:
            position_size = risk_amount / stop_distance
        else:
            position_size = 0
            
        return position_size
        
    async def update_positions(self, market_data: Dict[str, Dict[str, Any]]):
        """Update position P&L with current prices"""
        for symbol, position in self.positions.items():
            if symbol in market_data:
                current_price = market_data[symbol].get('price', position.entry_price)
                position.current_price = current_price
                
                if position.side == 'long':
                    position.unrealized_pnl = (current_price - position.entry_price) * position.quantity
                else:
                    position.unrealized_pnl = (position.entry_price - current_price) * position.quantity
                    
    def get_portfolio_status(self) -> Dict[str, Any]:
        """Get current portfolio status"""
        total_unrealized = sum(p.unrealized_pnl for p in self.positions.values())
        
        return {
            'mode': self.mode.value,
            'positions': len(self.positions),
            'max_positions': self.max_positions,
            'daily_pnl': self.daily_pnl,
            'total_pnl': self.total_pnl,
            'unrealized_pnl': total_unrealized,
            'current_drawdown': self.current_drawdown,
            'positions_detail': {
                symbol: {
                    'side': p.side,
                    'entry_price': p.entry_price,
                    'current_price': p.current_price,
                    'quantity': p.quantity,
                    'unrealized_pnl': p.unrealized_pnl
                }
                for symbol, p in self.positions.items()
            }
        }
        
    async def shutdown(self):
        """Shutdown orchestrator"""
        logger.info("Shutting down trading orchestrator...")
        
        # Close all positions in paper mode
        if self.mode == TradingMode.PAPER and self.positions:
            logger.info(f"Closing {len(self.positions)} paper positions...")
            self.positions.clear()
            
        logger.info("Trading orchestrator shutdown complete")
