"""
Risk Controller - Advanced risk management and position control
Implements comprehensive risk controls and portfolio protection
"""

import asyncio
import logging
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/risk_controller.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk level classification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskAction(Enum):
    """Risk mitigation actions."""
    ALLOW = "allow"
    REDUCE = "reduce"
    BLOCK = "block"
    CLOSE_ALL = "close_all"


@dataclass
class Position:
    """Trading position."""
    symbol: str
    direction: str  # BUY or SELL
    size: float
    entry_price: float
    current_price: float
    pnl: float
    unrealized_pnl: float
    entry_time: datetime
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


@dataclass
class RiskMetrics:
    """Portfolio risk metrics."""
    total_exposure: float = 0.0
    portfolio_var: float = 0.0
    portfolio_cvar: float = 0.0
    max_drawdown: float = 0.0
    current_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    correlation_risk: float = 0.0
    concentration_risk: float = 0.0
    leverage: float = 1.0
    risk_level: RiskLevel = RiskLevel.LOW


class RiskController:
    """
    Advanced risk management system.
    
    Features:
    - Position size limits
    - Portfolio exposure limits
    - Drawdown protection
    - Correlation monitoring
    - Concentration limits
    - Dynamic risk adjustment
    - Emergency stop mechanisms
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize risk controller."""
        self.config = config or self._default_config()
        
        # Portfolio state
        self.positions: Dict[str, Position] = {}
        self.equity = self.config['initial_equity']
        self.peak_equity = self.equity
        self.daily_pnl = 0.0
        self.total_pnl = 0.0
        
        # Risk limits
        self.max_position_size = self.config['max_position_size']
        self.max_portfolio_risk = self.config['max_portfolio_risk']
        self.max_drawdown = self.config['max_drawdown']
        self.max_daily_loss = self.config['max_daily_loss']
        self.max_positions = self.config['max_positions']
        self.max_correlation = self.config['max_correlation']
        
        # Risk tracking
        self.risk_metrics = RiskMetrics()
        self.risk_violations: List[Dict] = []
        self.emergency_stop = False
        
        logger.info("✅ Risk Controller initialized")
        self._log_risk_limits()
    
    def _default_config(self) -> Dict:
        """Default risk configuration."""
        return {
            'initial_equity': 100000.0,
            'max_position_size': 0.02,  # 2% per position
            'max_portfolio_risk': 0.10,  # 10% total risk
            'max_drawdown': 0.15,  # 15% max drawdown
            'max_daily_loss': 0.05,  # 5% daily loss limit
            'max_positions': 5,
            'max_correlation': 0.7,  # Max correlation between positions
            'risk_free_rate': 0.02,  # 2% annual
            'var_confidence': 0.95,  # 95% VaR
            'enable_dynamic_sizing': True,
            'enable_correlation_check': True
        }
    
    def _log_risk_limits(self):
        """Log risk limits."""
        logger.info("\n📊 RISK LIMITS:")
        logger.info(f"   Max Position Size: {self.max_position_size:.1%}")
        logger.info(f"   Max Portfolio Risk: {self.max_portfolio_risk:.1%}")
        logger.info(f"   Max Drawdown: {self.max_drawdown:.1%}")
        logger.info(f"   Max Daily Loss: {self.max_daily_loss:.1%}")
        logger.info(f"   Max Positions: {self.max_positions}")
    
    def check_trade_allowed(self, symbol: str, direction: str, size: float) -> Tuple[bool, str, RiskAction]:
        """
        Check if a trade is allowed based on risk limits.
        
        Args:
            symbol: Trading symbol
            direction: BUY or SELL
            size: Position size
        
        Returns:
            Tuple of (allowed, reason, action)
        """
        # Emergency stop check
        if self.emergency_stop:
            return False, "Emergency stop activated", RiskAction.BLOCK
        
        # Position count check
        if len(self.positions) >= self.max_positions:
            if symbol not in self.positions:
                return False, f"Max positions reached ({self.max_positions})", RiskAction.BLOCK
        
        # Position size check
        position_risk = size * self.equity
        max_position_value = self.max_position_size * self.equity
        
        if position_risk > max_position_value:
            # Suggest reduced size
            suggested_size = max_position_value / self.equity
            return False, f"Position too large (max: {self.max_position_size:.1%})", RiskAction.REDUCE
        
        # Portfolio risk check
        total_risk = self._calculate_portfolio_risk()
        if total_risk > self.max_portfolio_risk:
            return False, f"Portfolio risk too high ({total_risk:.1%})", RiskAction.BLOCK
        
        # Drawdown check
        current_drawdown = (self.peak_equity - self.equity) / self.peak_equity
        if current_drawdown > self.max_drawdown:
            return False, f"Max drawdown exceeded ({current_drawdown:.1%})", RiskAction.CLOSE_ALL
        
        # Daily loss check
        daily_loss_pct = abs(self.daily_pnl) / self.equity
        if self.daily_pnl < 0 and daily_loss_pct > self.max_daily_loss:
            return False, f"Daily loss limit reached ({daily_loss_pct:.1%})", RiskAction.CLOSE_ALL
        
        # Correlation check
        if self.config['enable_correlation_check']:
            correlation_risk = self._check_correlation_risk(symbol, direction)
            if correlation_risk > self.max_correlation:
                return False, f"High correlation risk ({correlation_risk:.2f})", RiskAction.BLOCK
        
        return True, "Trade allowed", RiskAction.ALLOW
    
    def calculate_position_size(self, symbol: str, direction: str, 
                               confidence: float = 1.0, volatility: float = 1.0) -> float:
        """
        Calculate optimal position size based on risk parameters.
        
        Args:
            symbol: Trading symbol
            direction: BUY or SELL
            confidence: Trade confidence (0-1)
            volatility: Market volatility multiplier
        
        Returns:
            Position size as fraction of equity
        """
        # Base position size
        base_size = self.max_position_size
        
        # Adjust for confidence
        confidence_adjusted = base_size * confidence
        
        # Adjust for volatility (inverse relationship)
        volatility_adjusted = confidence_adjusted / max(volatility, 0.5)
        
        # Adjust for current drawdown
        current_drawdown = (self.peak_equity - self.equity) / self.peak_equity
        if current_drawdown > 0.05:  # If in drawdown > 5%
            drawdown_factor = 1.0 - (current_drawdown / self.max_drawdown)
            volatility_adjusted *= drawdown_factor
        
        # Adjust for daily performance
        if self.daily_pnl < 0:
            daily_loss_pct = abs(self.daily_pnl) / self.equity
            daily_factor = 1.0 - (daily_loss_pct / self.max_daily_loss)
            volatility_adjusted *= max(daily_factor, 0.5)
        
        # Ensure within limits
        final_size = min(volatility_adjusted, self.max_position_size)
        final_size = max(final_size, self.max_position_size * 0.25)  # Min 25% of max
        
        logger.info(f"📏 Position Size Calculation for {symbol}:")
        logger.info(f"   Base: {base_size:.3%} → Confidence: {confidence_adjusted:.3%}")
        logger.info(f"   → Volatility: {volatility_adjusted:.3%} → Final: {final_size:.3%}")
        
        return final_size
    
    def add_position(self, position: Position):
        """Add a new position."""
        self.positions[position.symbol] = position
        logger.info(f"➕ Position added: {position.symbol} {position.direction} {position.size:.4f}")
        self._update_risk_metrics()
    
    def update_position(self, symbol: str, current_price: float):
        """Update position with current price."""
        if symbol not in self.positions:
            return
        
        position = self.positions[symbol]
        position.current_price = current_price
        
        # Calculate P/L
        if position.direction == "BUY":
            position.unrealized_pnl = (current_price - position.entry_price) * position.size
        else:
            position.unrealized_pnl = (position.entry_price - current_price) * position.size
        
        # Check stop loss / take profit
        self._check_exit_conditions(position)
        
        self._update_risk_metrics()
    
    def close_position(self, symbol: str, exit_price: float, reason: str = "Manual") -> Optional[float]:
        """
        Close a position.
        
        Args:
            symbol: Trading symbol
            exit_price: Exit price
            reason: Close reason
        
        Returns:
            Realized P/L or None
        """
        if symbol not in self.positions:
            logger.warning(f"⚠️ Position not found: {symbol}")
            return None
        
        position = self.positions[symbol]
        
        # Calculate final P/L
        if position.direction == "BUY":
            pnl = (exit_price - position.entry_price) * position.size
        else:
            pnl = (position.entry_price - exit_price) * position.size
        
        # Update equity
        self.equity += pnl
        self.total_pnl += pnl
        self.daily_pnl += pnl
        
        # Update peak equity
        if self.equity > self.peak_equity:
            self.peak_equity = self.equity
        
        # Remove position
        del self.positions[symbol]
        
        icon = "✅" if pnl > 0 else "❌"
        logger.info(f"{icon} Position closed: {symbol} | Reason: {reason} | P/L: ${pnl:.2f}")
        
        self._update_risk_metrics()
        
        return pnl
    
    def close_all_positions(self, reason: str = "Risk Management"):
        """Close all open positions."""
        logger.warning(f"🚨 CLOSING ALL POSITIONS - Reason: {reason}")
        
        symbols = list(self.positions.keys())
        for symbol in symbols:
            position = self.positions[symbol]
            self.close_position(symbol, position.current_price, reason)
        
        logger.info(f"✅ All positions closed. Equity: ${self.equity:.2f}")
    
    def _check_exit_conditions(self, position: Position):
        """Check if position should be closed based on stop loss / take profit."""
        should_close = False
        reason = ""
        
        if position.stop_loss is not None:
            if position.direction == "BUY" and position.current_price <= position.stop_loss:
                should_close = True
                reason = "Stop Loss"
            elif position.direction == "SELL" and position.current_price >= position.stop_loss:
                should_close = True
                reason = "Stop Loss"
        
        if position.take_profit is not None:
            if position.direction == "BUY" and position.current_price >= position.take_profit:
                should_close = True
                reason = "Take Profit"
            elif position.direction == "SELL" and position.current_price <= position.take_profit:
                should_close = True
                reason = "Take Profit"
        
        if should_close:
            self.close_position(position.symbol, position.current_price, reason)
    
    def _calculate_portfolio_risk(self) -> float:
        """Calculate total portfolio risk."""
        if not self.positions:
            return 0.0
        
        total_risk = sum(pos.size for pos in self.positions.values())
        return total_risk / self.equity
    
    def _check_correlation_risk(self, symbol: str, direction: str) -> float:
        """Check correlation risk with existing positions."""
        # Simplified correlation check
        # In production, would use actual price correlation
        
        if not self.positions:
            return 0.0
        
        # Count positions in same direction
        same_direction = sum(1 for pos in self.positions.values() if pos.direction == direction)
        
        # Return correlation proxy
        return same_direction / len(self.positions)
    
    def _update_risk_metrics(self):
        """Update portfolio risk metrics."""
        self.risk_metrics.total_exposure = sum(
            pos.size * pos.current_price for pos in self.positions.values()
        )
        
        self.risk_metrics.current_drawdown = (self.peak_equity - self.equity) / self.peak_equity
        self.risk_metrics.max_drawdown = max(
            self.risk_metrics.max_drawdown,
            self.risk_metrics.current_drawdown
        )
        
        self.risk_metrics.leverage = self.risk_metrics.total_exposure / self.equity
        
        # Determine risk level
        if self.risk_metrics.current_drawdown > 0.10:
            self.risk_metrics.risk_level = RiskLevel.CRITICAL
        elif self.risk_metrics.current_drawdown > 0.07:
            self.risk_metrics.risk_level = RiskLevel.HIGH
        elif self.risk_metrics.current_drawdown > 0.04:
            self.risk_metrics.risk_level = RiskLevel.MEDIUM
        else:
            self.risk_metrics.risk_level = RiskLevel.LOW
    
    def activate_emergency_stop(self, reason: str):
        """Activate emergency stop."""
        logger.error(f"🚨 EMERGENCY STOP ACTIVATED - {reason}")
        self.emergency_stop = True
        self.close_all_positions(f"Emergency Stop: {reason}")
    
    def deactivate_emergency_stop(self):
        """Deactivate emergency stop."""
        logger.info("✅ Emergency stop deactivated")
        self.emergency_stop = False
    
    def reset_daily_pnl(self):
        """Reset daily P/L (call at start of trading day)."""
        logger.info(f"📅 Daily P/L reset. Previous: ${self.daily_pnl:.2f}")
        self.daily_pnl = 0.0
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """Get risk summary."""
        return {
            'equity': self.equity,
            'peak_equity': self.peak_equity,
            'total_pnl': self.total_pnl,
            'daily_pnl': self.daily_pnl,
            'open_positions': len(self.positions),
            'total_exposure': self.risk_metrics.total_exposure,
            'current_drawdown': self.risk_metrics.current_drawdown,
            'max_drawdown': self.risk_metrics.max_drawdown,
            'leverage': self.risk_metrics.leverage,
            'risk_level': self.risk_metrics.risk_level.value,
            'emergency_stop': self.emergency_stop,
            'risk_violations': len(self.risk_violations)
        }
    
    def display_risk_dashboard(self):
        """Display risk dashboard."""
        logger.info("\n" + "="*80)
        logger.info("🛡️ RISK DASHBOARD")
        logger.info("="*80)
        
        logger.info(f"\n💰 EQUITY:")
        logger.info(f"   Current: ${self.equity:,.2f}")
        logger.info(f"   Peak: ${self.peak_equity:,.2f}")
        logger.info(f"   Total P/L: ${self.total_pnl:,.2f}")
        logger.info(f"   Daily P/L: ${self.daily_pnl:,.2f}")
        
        logger.info(f"\n📊 POSITIONS:")
        logger.info(f"   Open: {len(self.positions)}/{self.max_positions}")
        logger.info(f"   Total Exposure: ${self.risk_metrics.total_exposure:,.2f}")
        logger.info(f"   Leverage: {self.risk_metrics.leverage:.2f}x")
        
        logger.info(f"\n⚠️ RISK METRICS:")
        logger.info(f"   Current Drawdown: {self.risk_metrics.current_drawdown:.2%}")
        logger.info(f"   Max Drawdown: {self.risk_metrics.max_drawdown:.2%}")
        logger.info(f"   Risk Level: {self.risk_metrics.risk_level.value.upper()}")
        logger.info(f"   Emergency Stop: {'ACTIVE' if self.emergency_stop else 'Inactive'}")
        
        if self.positions:
            logger.info(f"\n📈 OPEN POSITIONS:")
            for symbol, pos in self.positions.items():
                pnl_pct = (pos.unrealized_pnl / (pos.entry_price * pos.size)) * 100
                icon = "📈" if pos.unrealized_pnl > 0 else "📉"
                logger.info(f"   {icon} {symbol} {pos.direction}: ${pos.unrealized_pnl:.2f} ({pnl_pct:+.2f}%)")
        
        logger.info("="*80)


    """Test risk controller."""
import numpy
import pandas

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


async def main():
    """Test the risk controller"""
    os.makedirs('logs', exist_ok=True)
    
    controller = RiskController()
    
    # Test position
    position = Position(
        symbol="EURUSD",
        direction="BUY",
        size=0.01,
        entry_price=1.1000,
        current_price=1.1000,
        pnl=0.0,
        unrealized_pnl=0.0,
        entry_time=datetime.now()
    )
    
    # Check if trade allowed
    allowed, reason, action = controller.check_trade_allowed("EURUSD", "BUY", 0.01)
    logger.info(f"Trade allowed: {allowed} - {reason} - {action.value}")
    
    if allowed:
        controller.add_position(position)
    
    # Simulate price movement
    for i in range(10):
        new_price = 1.1000 + (i * 0.0010)
        controller.update_position("EURUSD", new_price)
        await asyncio.sleep(0.5)
    
    # Display dashboard
    controller.display_risk_dashboard()


if __name__ == '__main__':
    asyncio.run(main())
