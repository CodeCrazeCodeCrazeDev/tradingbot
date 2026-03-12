"""
AlphaAlgo V2 Risk Engine

Main risk management engine coordinating all risk components.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..core.interfaces import IRiskManager
from ..core.types import Signal, Position, Trade, RiskDecision, RiskLevel
from ..core.constants import (
    MAX_RISK_PER_TRADE,
    MAX_DAILY_LOSS,
    MAX_DRAWDOWN,
)
from ..core.exceptions import RiskLimitExceededError, DrawdownLimitError
from .position.sizer import PositionSizer, SizingMethod, SizingResult
from .portfolio.manager import PortfolioRiskManager, PortfolioMetrics
from typing import Set

logger = logging.getLogger(__name__)


class RiskEngine(IRiskManager):
    """
    Main risk management engine
    
    Coordinates:
    - Position sizing
    - Portfolio risk management
    - Pre-trade validation
    - Risk limit monitoring
    - Emergency controls
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Components
        self._position_sizer = PositionSizer(self.config.get("position_sizing", {}))
        self._portfolio_manager = PortfolioRiskManager(self.config.get("portfolio", {}))
        
        # Account info
        self._account_balance = self.config.get("initial_balance", 10000.0)
        self._account_equity = self._account_balance
        
        # Risk state
        self._daily_pnl = 0.0
        self._current_drawdown = 0.0
        self._risk_level = RiskLevel.LOW
        
        # Trading state
        self._trading_enabled = True
        self._emergency_mode = False
        
        # Statistics
        self._trades_today = 0
        self._rejected_trades = 0
        self._win_rate = 0.5
        self._avg_win = 1.0
        self._avg_loss = 1.0
    
    @property
    def current_risk(self) -> float:
        """Get current portfolio risk as percentage"""
        metrics = self._portfolio_manager.get_metrics()
        return metrics.current_drawdown
    
    @property
    def daily_pnl(self) -> float:
        """Get current daily P&L"""
        return self._daily_pnl
    
    @property
    def max_drawdown(self) -> float:
        """Get maximum drawdown"""
        return self._current_drawdown
    
    def validate_trade(
        self,
        signal: Signal,
        position_size: float
    ) -> RiskDecision:
        """
        Validate trade against all risk limits
        
        Args:
            signal: Trading signal
            position_size: Proposed position size
            
        Returns:
            RiskDecision with allowed/rejected and reason
        """
        # Check if trading is enabled
        if not self._trading_enabled:
            return RiskDecision(
                allowed=False,
                reason="Trading is disabled",
                risk_level=RiskLevel.CRITICAL,
            )
        
        if self._emergency_mode:
            return RiskDecision(
                allowed=False,
                reason="Emergency mode active",
                risk_level=RiskLevel.CRITICAL,
            )
        
        # Check signal validity
        if signal.is_expired:
            return RiskDecision(
                allowed=False,
                reason="Signal has expired",
                risk_level=RiskLevel.LOW,
            )
        
        # Check portfolio limits
        portfolio_decision = self._portfolio_manager.validate_new_position(
            symbol=signal.symbol,
            size=position_size,
            price=signal.price,
        )
        
        if not portfolio_decision.allowed:
            self._rejected_trades += 1
            return portfolio_decision
        
        # Check per-trade risk
        trade_risk = self._calculate_trade_risk(signal, position_size)
        
        if trade_risk > MAX_RISK_PER_TRADE:
            self._rejected_trades += 1
            return RiskDecision(
                allowed=False,
                reason=f"Trade risk {trade_risk:.1%} exceeds limit {MAX_RISK_PER_TRADE:.1%}",
                risk_level=RiskLevel.HIGH,
            )
        
        # Check daily loss limit
        if abs(self._daily_pnl / self._account_balance) > MAX_DAILY_LOSS * 0.8:
            # Allow but warn
            portfolio_decision.warnings.append("Approaching daily loss limit")
            portfolio_decision.risk_level = RiskLevel.HIGH
        
        return portfolio_decision
    
    def get_position_size(
        self,
        signal: Signal,
        account_balance: float,
        method: str = "kelly"
    ) -> float:
        """
        Calculate optimal position size
        
        Args:
            signal: Trading signal
            account_balance: Current account balance
            method: Sizing method
            
        Returns:
            Position size
        """
        sizing_method = SizingMethod(method.lower())
        
        result = self._position_sizer.calculate(
            signal=signal,
            account_balance=account_balance,
            method=sizing_method,
            win_rate=self._win_rate,
            avg_win=self._avg_win,
            avg_loss=self._avg_loss,
        )
        
        logger.debug(f"Position size: {result.size:.4f} ({result.reasoning})")
        
        return result.size
    
    def check_limits(self) -> Dict[str, bool]:
        """
        Check all risk limits
        
        Returns:
            Dict with limit name and whether it's breached
        """
        portfolio_limits = self._portfolio_manager.check_limits()
        
        # Add engine-level limits
        portfolio_limits["trading_disabled"] = not self._trading_enabled
        portfolio_limits["emergency_mode"] = self._emergency_mode
        
        return portfolio_limits
    
    def update_position(self, position: Position) -> None:
        """Update risk calculations with new position"""
        self._portfolio_manager.update_position(position)
        self._update_risk_level()
    
    def update_trade(self, trade: Trade) -> None:
        """Update risk calculations with completed trade"""
        self._portfolio_manager.add_trade(trade)
        self._portfolio_manager.remove_position(trade.symbol)
        
        # Update statistics
        self._trades_today += 1
        self._daily_pnl += trade.profit
        
        # Update win rate
        self._update_statistics(trade)
        
        # Update account
        self._account_balance += trade.profit
        self._account_equity = self._account_balance
        self._portfolio_manager.update_balance(self._account_balance)
        
        self._update_risk_level()
    
    def emergency_close_all(self) -> bool:
        """Emergency close all positions"""
        logger.critical("EMERGENCY CLOSE ALL POSITIONS")
        self._emergency_mode = True
        self._trading_enabled = False
        
        # This would trigger position closing in the orchestrator
        return True
    
    def enable_trading(self) -> None:
        """Enable trading"""
        if not self._emergency_mode:
            self._trading_enabled = True
            logger.info("Trading enabled")
    
    def disable_trading(self) -> None:
        """Disable trading"""
        self._trading_enabled = False
        logger.info("Trading disabled")
    
    def reset_emergency(self) -> None:
        """Reset emergency mode (requires manual intervention)"""
        self._emergency_mode = False
        logger.warning("Emergency mode reset - trading still disabled")
    
    def _calculate_trade_risk(self, signal: Signal, size: float) -> float:
        """Calculate risk for a single trade"""
        if signal.stop_loss and signal.price:
            stop_distance = abs(signal.price - signal.stop_loss)
            risk_amount = stop_distance * size
            return risk_amount / self._account_balance if self._account_balance > 0 else 0
        else:
            # Assume 2% risk if no stop loss
            return 0.02
    
    def _update_statistics(self, trade: Trade) -> None:
        """Update trading statistics"""
        # Simple moving average of win rate
        is_win = 1 if trade.profit > 0 else 0
        self._win_rate = self._win_rate * 0.9 + is_win * 0.1
        
        # Update average win/loss
        if trade.profit > 0:
            self._avg_win = self._avg_win * 0.9 + abs(trade.profit) * 0.1
        else:
            self._avg_loss = self._avg_loss * 0.9 + abs(trade.profit) * 0.1
    
    def _update_risk_level(self) -> None:
        """Update overall risk level"""
        limits = self.check_limits()
        
        if limits.get("emergency_mode") or limits.get("max_drawdown"):
            self._risk_level = RiskLevel.CRITICAL
        elif limits.get("max_daily_loss"):
            self._risk_level = RiskLevel.HIGH
        elif any(limits.values()):
            self._risk_level = RiskLevel.MEDIUM
        else:
            self._risk_level = RiskLevel.LOW
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """Get comprehensive risk summary"""
        portfolio_summary = self._portfolio_manager.get_risk_summary()
        
        return {
            "risk_level": self._risk_level.value,
            "trading_enabled": self._trading_enabled,
            "emergency_mode": self._emergency_mode,
            "account": {
                "balance": self._account_balance,
                "equity": self._account_equity,
                "daily_pnl": self._daily_pnl,
            },
            "statistics": {
                "trades_today": self._trades_today,
                "rejected_trades": self._rejected_trades,
                "win_rate": self._win_rate,
                "avg_win": self._avg_win,
                "avg_loss": self._avg_loss,
            },
            "portfolio": portfolio_summary,
        }
    
    def set_account_balance(self, balance: float) -> None:
        """Set account balance"""
        self._account_balance = balance
        self._account_equity = balance
        self._portfolio_manager.update_balance(balance)
