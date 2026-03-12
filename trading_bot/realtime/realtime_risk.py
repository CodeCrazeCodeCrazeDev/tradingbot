"""
Real-Time Risk Monitor
======================

Streaming risk monitoring with real-time position and P&L tracking.
No polling - continuous risk assessment.

Features:
1. Real-time position tracking
2. Real-time P&L calculation
3. Streaming drawdown monitoring
4. Real-time exposure limits
5. Circuit breaker triggers
6. Risk event broadcasting

Author: AlphaAlgo Trading System
Version: 3.0.0
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk level classification"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class RiskEventType(Enum):
    """Types of risk events"""
    POSITION_LIMIT = "position_limit"
    DAILY_LOSS_LIMIT = "daily_loss_limit"
    DRAWDOWN_LIMIT = "drawdown_limit"
    EXPOSURE_LIMIT = "exposure_limit"
    VOLATILITY_SPIKE = "volatility_spike"
    CORRELATION_BREAK = "correlation_break"
    CIRCUIT_BREAKER = "circuit_breaker"


@dataclass
class Position:
    """Real-time position"""
    symbol: str
    side: str  # "long" or "short"
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    opened_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    @property
    def market_value(self) -> float:
        return self.quantity * self.current_price
    
    @property
    def cost_basis(self) -> float:
        return self.quantity * self.entry_price
    
    @property
    def pnl_percent(self) -> float:
        if self.cost_basis == 0:
            return 0.0
        return (self.unrealized_pnl / self.cost_basis) * 100
    
    def update_price(self, price: float):
        """Update position with new price"""
        self.current_price = price
        if self.side == "long":
            self.unrealized_pnl = (price - self.entry_price) * self.quantity
        else:
            self.unrealized_pnl = (self.entry_price - price) * self.quantity
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'side': self.side,
            'quantity': self.quantity,
            'entry_price': self.entry_price,
            'current_price': self.current_price,
            'unrealized_pnl': self.unrealized_pnl,
            'realized_pnl': self.realized_pnl,
            'market_value': self.market_value,
            'pnl_percent': self.pnl_percent,
            'opened_at': self.opened_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


@dataclass
class RiskEvent:
    """Risk event"""
    event_id: str
    event_type: RiskEventType
    risk_level: RiskLevel
    symbol: Optional[str]
    message: str
    value: float
    threshold: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'risk_level': self.risk_level.value,
            'symbol': self.symbol,
            'message': self.message,
            'value': self.value,
            'threshold': self.threshold,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }


@dataclass
class RiskLimits:
    """Risk limits configuration"""
    max_position_size: float = 0.02  # 2% of capital per position
    max_daily_loss: float = 0.05  # 5% daily loss limit
    max_drawdown: float = 0.20  # 20% max drawdown
    max_total_exposure: float = 1.0  # 100% of capital
    max_single_exposure: float = 0.25  # 25% in single asset
    max_correlation_exposure: float = 0.50  # 50% in correlated assets
    volatility_multiplier: float = 2.0  # Reduce size when vol is 2x normal
    circuit_breaker_loss: float = 0.10  # 10% triggers circuit breaker


@dataclass
class PortfolioSnapshot:
    """Real-time portfolio snapshot"""
    timestamp: datetime
    total_equity: float
    cash: float
    positions_value: float
    unrealized_pnl: float
    realized_pnl: float
    daily_pnl: float
    drawdown: float
    drawdown_percent: float
    peak_equity: float
    risk_level: RiskLevel
    num_positions: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'total_equity': self.total_equity,
            'cash': self.cash,
            'positions_value': self.positions_value,
            'unrealized_pnl': self.unrealized_pnl,
            'realized_pnl': self.realized_pnl,
            'daily_pnl': self.daily_pnl,
            'drawdown': self.drawdown,
            'drawdown_percent': self.drawdown_percent,
            'peak_equity': self.peak_equity,
            'risk_level': self.risk_level.value,
            'num_positions': self.num_positions
        }


class RealTimeRiskMonitor:
    """
    Real-time risk monitoring system.
    
    Features:
    - Continuous position tracking
    - Real-time P&L calculation
    - Streaming risk metrics
    - Circuit breaker triggers
    - Risk event broadcasting
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Risk limits
        self._limits = RiskLimits(
            max_position_size=config.get('max_position_size', 0.02),
            max_daily_loss=config.get('max_daily_loss', 0.05),
            max_drawdown=config.get('max_drawdown', 0.20),
            max_total_exposure=config.get('max_total_exposure', 1.0),
            max_single_exposure=config.get('max_single_exposure', 0.25),
            circuit_breaker_loss=config.get('circuit_breaker_loss', 0.10)
        )
        
        # Portfolio state
        self._initial_capital = config.get('initial_capital', 100000)
        self._cash = self._initial_capital
        self._positions: Dict[str, Position] = {}
        
        # P&L tracking
        self._peak_equity = self._initial_capital
        self._daily_start_equity = self._initial_capital
        self._realized_pnl = 0.0
        self._daily_realized_pnl = 0.0
        
        # Risk state
        self._risk_level = RiskLevel.LOW
        self._circuit_breaker_active = False
        self._trading_halted = False
        
        # Event history
        self._risk_events: deque = deque(maxlen=500)
        self._event_counter = 0
        
        # Subscribers
        self._risk_subscribers: List[Callable] = []
        self._position_subscribers: List[Callable] = []
        
        # Snapshot history
        self._snapshots: deque = deque(maxlen=1000)
        
        self._running = False
        
        logger.info("RealTimeRiskMonitor initialized")
    
    def on_price_update(self, symbol: str, price: float):
        """Handle real-time price update"""
        if symbol in self._positions:
            position = self._positions[symbol]
            position.update_price(price)
            
            # Check position-level risks
            asyncio.create_task(self._check_position_risk(position))
        
        # Update portfolio snapshot
        asyncio.create_task(self._update_portfolio_snapshot())
    
    async def on_fill(self, symbol: str, side: str, quantity: float, 
                      price: float, is_close: bool = False):
        """Handle order fill"""
        if is_close and symbol in self._positions:
            # Close position
            position = self._positions[symbol]
            realized = position.unrealized_pnl
            self._realized_pnl += realized
            self._daily_realized_pnl += realized
            self._cash += position.market_value + realized
            del self._positions[symbol]
            
            logger.info(f"Position closed: {symbol} realized P&L: {realized:.2f}")
            
        elif not is_close:
            # Open or add to position
            if symbol in self._positions:
                # Average into position
                position = self._positions[symbol]
                total_qty = position.quantity + quantity
                avg_price = (position.entry_price * position.quantity + price * quantity) / total_qty
                position.quantity = total_qty
                position.entry_price = avg_price
                position.current_price = price
            else:
                # New position
                position = Position(
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    entry_price=price,
                    current_price=price
                )
                self._positions[symbol] = position
                self._cash -= quantity * price
            
            logger.info(f"Position opened/added: {symbol} {side} {quantity} @ {price}")
        
        # Notify subscribers
        await self._notify_position_update(symbol)
        await self._update_portfolio_snapshot()
    
    async def _check_position_risk(self, position: Position):
        """Check position-level risk limits"""
        equity = self._calculate_equity()
        
        # Check position size limit
        position_pct = position.market_value / equity if equity > 0 else 0
        if position_pct > self._limits.max_single_exposure:
            await self._emit_risk_event(
                RiskEventType.EXPOSURE_LIMIT,
                RiskLevel.HIGH,
                position.symbol,
                f"Position {position.symbol} exceeds single exposure limit",
                position_pct,
                self._limits.max_single_exposure
            )
        
        # Check position loss
        if position.pnl_percent < -10:  # 10% loss on position
            await self._emit_risk_event(
                RiskEventType.POSITION_LIMIT,
                RiskLevel.MODERATE,
                position.symbol,
                f"Position {position.symbol} down {abs(position.pnl_percent):.1f}%",
                position.pnl_percent,
                -10
            )
    
    async def _update_portfolio_snapshot(self):
        """Update and check portfolio-level risks"""
        equity = self._calculate_equity()
        unrealized = sum(p.unrealized_pnl for p in self._positions.values())
        positions_value = sum(p.market_value for p in self._positions.values())
        
        # Update peak equity
        if equity > self._peak_equity:
            self._peak_equity = equity
        
        # Calculate drawdown
        drawdown = self._peak_equity - equity
        drawdown_pct = drawdown / self._peak_equity if self._peak_equity > 0 else 0
        
        # Calculate daily P&L
        daily_pnl = equity - self._daily_start_equity
        daily_pnl_pct = daily_pnl / self._daily_start_equity if self._daily_start_equity > 0 else 0
        
        # Determine risk level
        risk_level = self._calculate_risk_level(drawdown_pct, daily_pnl_pct)
        
        # Create snapshot
        snapshot = PortfolioSnapshot(
            timestamp=datetime.now(),
            total_equity=equity,
            cash=self._cash,
            positions_value=positions_value,
            unrealized_pnl=unrealized,
            realized_pnl=self._realized_pnl,
            daily_pnl=daily_pnl,
            drawdown=drawdown,
            drawdown_percent=drawdown_pct,
            peak_equity=self._peak_equity,
            risk_level=risk_level,
            num_positions=len(self._positions)
        )
        
        self._snapshots.append(snapshot)
        self._risk_level = risk_level
        
        # Check portfolio-level limits
        await self._check_portfolio_limits(snapshot)
    
    def _calculate_equity(self) -> float:
        """Calculate total equity"""
        positions_value = sum(p.market_value for p in self._positions.values())
        unrealized = sum(p.unrealized_pnl for p in self._positions.values())
        return self._cash + positions_value + unrealized
    
    def _calculate_risk_level(self, drawdown_pct: float, daily_pnl_pct: float) -> RiskLevel:
        """Calculate overall risk level"""
        if drawdown_pct >= self._limits.max_drawdown or daily_pnl_pct <= -self._limits.circuit_breaker_loss:
            return RiskLevel.EMERGENCY
        elif drawdown_pct >= self._limits.max_drawdown * 0.8 or daily_pnl_pct <= -self._limits.max_daily_loss:
            return RiskLevel.CRITICAL
        elif drawdown_pct >= self._limits.max_drawdown * 0.5 or daily_pnl_pct <= -self._limits.max_daily_loss * 0.5:
            return RiskLevel.HIGH
        elif drawdown_pct >= self._limits.max_drawdown * 0.25:
            return RiskLevel.MODERATE
        else:
            return RiskLevel.LOW
    
    async def _check_portfolio_limits(self, snapshot: PortfolioSnapshot):
        """Check portfolio-level risk limits"""
        # Daily loss limit
        daily_loss_pct = -snapshot.daily_pnl / self._daily_start_equity if self._daily_start_equity > 0 else 0
        if daily_loss_pct >= self._limits.max_daily_loss:
            await self._emit_risk_event(
                RiskEventType.DAILY_LOSS_LIMIT,
                RiskLevel.CRITICAL,
                None,
                f"Daily loss limit reached: {daily_loss_pct:.1%}",
                daily_loss_pct,
                self._limits.max_daily_loss
            )
            self._trading_halted = True
        
        # Drawdown limit
        if snapshot.drawdown_percent >= self._limits.max_drawdown:
            await self._emit_risk_event(
                RiskEventType.DRAWDOWN_LIMIT,
                RiskLevel.CRITICAL,
                None,
                f"Max drawdown reached: {snapshot.drawdown_percent:.1%}",
                snapshot.drawdown_percent,
                self._limits.max_drawdown
            )
            self._trading_halted = True
        
        # Circuit breaker
        if daily_loss_pct >= self._limits.circuit_breaker_loss:
            await self._emit_risk_event(
                RiskEventType.CIRCUIT_BREAKER,
                RiskLevel.EMERGENCY,
                None,
                f"Circuit breaker triggered: {daily_loss_pct:.1%} daily loss",
                daily_loss_pct,
                self._limits.circuit_breaker_loss
            )
            self._circuit_breaker_active = True
            self._trading_halted = True
        
        # Total exposure
        exposure_pct = snapshot.positions_value / snapshot.total_equity if snapshot.total_equity > 0 else 0
        if exposure_pct > self._limits.max_total_exposure:
            await self._emit_risk_event(
                RiskEventType.EXPOSURE_LIMIT,
                RiskLevel.HIGH,
                None,
                f"Total exposure exceeds limit: {exposure_pct:.1%}",
                exposure_pct,
                self._limits.max_total_exposure
            )
    
    async def _emit_risk_event(self, event_type: RiskEventType, risk_level: RiskLevel,
                               symbol: Optional[str], message: str, 
                               value: float, threshold: float):
        """Emit a risk event"""
        self._event_counter += 1
        
        event = RiskEvent(
            event_id=f"RISK-{self._event_counter:06d}",
            event_type=event_type,
            risk_level=risk_level,
            symbol=symbol,
            message=message,
            value=value,
            threshold=threshold
        )
        
        self._risk_events.append(event)
        
        logger.warning(f"Risk Event: [{risk_level.value.upper()}] {message}")
        
        # Notify subscribers
        for callback in self._risk_subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"Risk subscriber error: {e}")
    
    async def _notify_position_update(self, symbol: str):
        """Notify position update subscribers"""
        position = self._positions.get(symbol)
        
        for callback in self._position_subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(symbol, position)
                else:
                    callback(symbol, position)
            except Exception as e:
                logger.error(f"Position subscriber error: {e}")
    
    def subscribe_risk(self, callback: Callable):
        """Subscribe to risk events"""
        self._risk_subscribers.append(callback)
    
    def subscribe_positions(self, callback: Callable):
        """Subscribe to position updates"""
        self._position_subscribers.append(callback)
    
    def can_trade(self) -> tuple:
        """Check if trading is allowed"""
        if self._circuit_breaker_active:
            return False, "Circuit breaker active"
        if self._trading_halted:
            return False, "Trading halted due to risk limits"
        if self._risk_level == RiskLevel.EMERGENCY:
            return False, "Emergency risk level"
        return True, "OK"
    
    def check_order(self, symbol: str, side: str, quantity: float, price: float) -> tuple:
        """Pre-trade risk check"""
        can_trade, reason = self.can_trade()
        if not can_trade:
            return False, reason
        
        equity = self._calculate_equity()
        order_value = quantity * price
        
        # Check position size
        position_pct = order_value / equity if equity > 0 else 0
        if position_pct > self._limits.max_position_size:
            return False, f"Order exceeds max position size ({position_pct:.1%} > {self._limits.max_position_size:.1%})"
        
        # Check single exposure
        existing_value = self._positions.get(symbol, Position(symbol, side, 0, 0, 0)).market_value
        new_exposure = (existing_value + order_value) / equity if equity > 0 else 0
        if new_exposure > self._limits.max_single_exposure:
            return False, f"Order would exceed single asset exposure limit"
        
        # Check total exposure
        total_positions = sum(p.market_value for p in self._positions.values())
        new_total = (total_positions + order_value) / equity if equity > 0 else 0
        if new_total > self._limits.max_total_exposure:
            return False, f"Order would exceed total exposure limit"
        
        return True, "Approved"
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for symbol"""
        return self._positions.get(symbol)
    
    def get_all_positions(self) -> List[Position]:
        """Get all positions"""
        return list(self._positions.values())
    
    def get_portfolio_snapshot(self) -> Optional[PortfolioSnapshot]:
        """Get latest portfolio snapshot"""
        return self._snapshots[-1] if self._snapshots else None
    
    def get_risk_events(self, limit: int = 50) -> List[RiskEvent]:
        """Get recent risk events"""
        return list(self._risk_events)[-limit:]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get risk metrics"""
        snapshot = self.get_portfolio_snapshot()
        
        return {
            'risk_level': self._risk_level.value,
            'circuit_breaker_active': self._circuit_breaker_active,
            'trading_halted': self._trading_halted,
            'equity': self._calculate_equity(),
            'cash': self._cash,
            'num_positions': len(self._positions),
            'unrealized_pnl': sum(p.unrealized_pnl for p in self._positions.values()),
            'realized_pnl': self._realized_pnl,
            'daily_pnl': snapshot.daily_pnl if snapshot else 0,
            'drawdown_percent': snapshot.drawdown_percent if snapshot else 0,
            'risk_events_count': len(self._risk_events)
        }
    
    def reset_daily(self):
        """Reset daily counters (call at start of trading day)"""
        self._daily_start_equity = self._calculate_equity()
        self._daily_realized_pnl = 0.0
        self._trading_halted = False
        
        # Don't reset circuit breaker automatically
        if not self._circuit_breaker_active:
            self._risk_level = RiskLevel.LOW
        
        logger.info("Daily risk counters reset")
    
    def reset_circuit_breaker(self):
        """Manually reset circuit breaker (requires human approval)"""
        self._circuit_breaker_active = False
        self._trading_halted = False
        self._risk_level = RiskLevel.LOW
        logger.info("Circuit breaker reset")
    
    async def start(self):
        """Start risk monitor"""
        self._running = True
        logger.info("RealTimeRiskMonitor started")
    
    async def stop(self):
        """Stop risk monitor"""
        self._running = False
        logger.info("RealTimeRiskMonitor stopped")
