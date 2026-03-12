"""
from typing import List, Optional, Set
AlphaAlgo V2 Portfolio Risk Manager

Portfolio-level risk management.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from ...core.types import Position, Trade, RiskDecision, RiskLevel
from ...core.constants import (
    MAX_DAILY_LOSS,
    MAX_DRAWDOWN,
    MAX_POSITION_SIZE,
    MAX_CORRELATED_EXPOSURE,
)

logger = logging.getLogger(__name__)


@dataclass
class PortfolioMetrics:
    """Portfolio risk metrics"""
    total_exposure: float = 0.0
    daily_pnl: float = 0.0
    daily_pnl_percent: float = 0.0
    max_drawdown: float = 0.0
    current_drawdown: float = 0.0
    position_count: int = 0
    largest_position: float = 0.0
    correlation_exposure: float = 0.0


class PortfolioRiskManager:
    """
    Portfolio-level risk management
    
    Monitors:
    - Total exposure
    - Daily P&L
    - Drawdown
    - Position concentration
    - Correlation exposure
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Limits (use constants as maximums)
        self._max_daily_loss = min(
            self.config.get("max_daily_loss", 0.05),
            MAX_DAILY_LOSS
        )
        self._max_drawdown = min(
            self.config.get("max_drawdown", 0.20),
            MAX_DRAWDOWN
        )
        self._max_position_size = min(
            self.config.get("max_position_size", 0.10),
            MAX_POSITION_SIZE
        )
        self._max_correlated_exposure = min(
            self.config.get("max_correlated_exposure", 0.30),
            MAX_CORRELATED_EXPOSURE
        )
        self._max_positions = self.config.get("max_positions", 10)
        
        # State
        self._initial_balance = self.config.get("initial_balance", 10000.0)
        self._peak_balance = self._initial_balance
        self._current_balance = self._initial_balance
        self._daily_start_balance = self._initial_balance
        self._daily_pnl = 0.0
        self._last_reset = datetime.now().date()
        
        # Position tracking
        self._positions: Dict[str, Position] = {}
        self._trade_history: List[Trade] = []
        
        # Correlation matrix (simplified)
        self._correlations: Dict[str, Dict[str, float]] = {}
    
    def update_balance(self, balance: float) -> None:
        """Update current balance"""
        self._current_balance = balance
        
        # Update peak
        if balance > self._peak_balance:
            self._peak_balance = balance
        
        # Reset daily if new day
        today = datetime.now().date()
        if today > self._last_reset:
            self._daily_start_balance = balance
            self._daily_pnl = 0.0
            self._last_reset = today
        else:
            self._daily_pnl = balance - self._daily_start_balance
    
    def update_position(self, position: Position) -> None:
        """Update position tracking"""
        self._positions[position.symbol] = position
    
    def remove_position(self, symbol: str) -> None:
        """Remove position from tracking"""
        if symbol in self._positions:
            del self._positions[symbol]
    
    def add_trade(self, trade: Trade) -> None:
        """Add completed trade to history"""
        self._trade_history.append(trade)
    
    def get_metrics(self) -> PortfolioMetrics:
        """Get current portfolio metrics"""
        # Calculate exposure
        total_exposure = sum(
            p.volume * p.current_price
            for p in self._positions.values()
        )
        
        # Calculate drawdown
        current_drawdown = 0.0
        if self._peak_balance > 0:
            current_drawdown = (self._peak_balance - self._current_balance) / self._peak_balance
        
        # Find largest position
        largest = 0.0
        if self._positions:
            largest = max(
                p.volume * p.current_price
                for p in self._positions.values()
            )
        
        # Daily P&L percent
        daily_pnl_pct = 0.0
        if self._daily_start_balance > 0:
            daily_pnl_pct = self._daily_pnl / self._daily_start_balance
        
        return PortfolioMetrics(
            total_exposure=total_exposure,
            daily_pnl=self._daily_pnl,
            daily_pnl_percent=daily_pnl_pct,
            max_drawdown=self._max_drawdown,
            current_drawdown=current_drawdown,
            position_count=len(self._positions),
            largest_position=largest,
            correlation_exposure=self._calculate_correlation_exposure(),
        )
    
    def check_limits(self) -> Dict[str, bool]:
        """
        Check all risk limits
        
        Returns:
            Dict of limit name to breach status (True = breached)
        """
        metrics = self.get_metrics()
        
        return {
            "max_daily_loss": abs(metrics.daily_pnl_percent) > self._max_daily_loss,
            "max_drawdown": metrics.current_drawdown > self._max_drawdown,
            "max_positions": metrics.position_count >= self._max_positions,
            "max_correlated_exposure": metrics.correlation_exposure > self._max_correlated_exposure,
        }
    
    def validate_new_position(
        self,
        symbol: str,
        size: float,
        price: float
    ) -> RiskDecision:
        """
        Validate new position against portfolio limits
        
        Args:
            symbol: Symbol to trade
            size: Position size
            price: Entry price
            
        Returns:
            RiskDecision
        """
        metrics = self.get_metrics()
        limits = self.check_limits()
        warnings = []
        
        # Check if any limits breached
        if limits["max_daily_loss"]:
            return RiskDecision(
                allowed=False,
                reason=f"Daily loss limit breached: {metrics.daily_pnl_percent:.1%}",
                risk_level=RiskLevel.CRITICAL,
            )
        
        if limits["max_drawdown"]:
            return RiskDecision(
                allowed=False,
                reason=f"Drawdown limit breached: {metrics.current_drawdown:.1%}",
                risk_level=RiskLevel.CRITICAL,
            )
        
        if limits["max_positions"]:
            return RiskDecision(
                allowed=False,
                reason=f"Maximum positions reached: {metrics.position_count}",
                risk_level=RiskLevel.HIGH,
            )
        
        # Check position size
        position_value = size * price
        position_pct = position_value / self._current_balance if self._current_balance > 0 else 0
        
        if position_pct > self._max_position_size:
            # Adjust size instead of rejecting
            adjusted_size = (self._max_position_size * self._current_balance) / price
            warnings.append(f"Size reduced from {size:.4f} to {adjusted_size:.4f}")
            
            return RiskDecision(
                allowed=True,
                reason="Position size adjusted to meet limits",
                risk_level=RiskLevel.MEDIUM,
                adjusted_size=adjusted_size,
                warnings=warnings,
            )
        
        # Check correlation exposure
        if limits["max_correlated_exposure"]:
            warnings.append("High correlation exposure")
        
        # Determine risk level
        if metrics.current_drawdown > self._max_drawdown * 0.7:
            risk_level = RiskLevel.HIGH
        elif metrics.current_drawdown > self._max_drawdown * 0.5:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
        
        return RiskDecision(
            allowed=True,
            reason="Position approved",
            risk_level=risk_level,
            warnings=warnings,
        )
    
    def _calculate_correlation_exposure(self) -> float:
        """Calculate correlated exposure"""
        if len(self._positions) < 2:
            return 0.0
        
        # Simplified: assume forex pairs with same base/quote are correlated
        exposure = 0.0
        symbols = list(self._positions.keys())
        
        for i, sym1 in enumerate(symbols):
            for sym2 in symbols[i+1:]:
                corr = self._get_correlation(sym1, sym2)
                if corr > 0.7:
                    pos1 = self._positions[sym1]
                    pos2 = self._positions[sym2]
                    exposure += min(
                        pos1.volume * pos1.current_price,
                        pos2.volume * pos2.current_price
                    ) * corr
        
        return exposure / self._current_balance if self._current_balance > 0 else 0
    
    def _get_correlation(self, sym1: str, sym2: str) -> float:
        """Get correlation between two symbols"""
        # Check stored correlations
        if sym1 in self._correlations and sym2 in self._correlations[sym1]:
            return self._correlations[sym1][sym2]
        
        # Default correlations for common pairs
        default_correlations = {
            ("EURUSD", "GBPUSD"): 0.85,
            ("EURUSD", "USDCHF"): -0.90,
            ("GBPUSD", "EURGBP"): -0.75,
            ("USDJPY", "EURJPY"): 0.80,
        }
        
        key = (sym1, sym2) if sym1 < sym2 else (sym2, sym1)
        return default_correlations.get(key, 0.0)
    
    def set_correlation(self, sym1: str, sym2: str, correlation: float) -> None:
        """Set correlation between two symbols"""
        if sym1 not in self._correlations:
            self._correlations[sym1] = {}
        self._correlations[sym1][sym2] = correlation
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """Get risk summary"""
        metrics = self.get_metrics()
        limits = self.check_limits()
        
        return {
            "metrics": {
                "total_exposure": metrics.total_exposure,
                "daily_pnl": metrics.daily_pnl,
                "daily_pnl_percent": metrics.daily_pnl_percent,
                "current_drawdown": metrics.current_drawdown,
                "position_count": metrics.position_count,
            },
            "limits": limits,
            "limits_config": {
                "max_daily_loss": self._max_daily_loss,
                "max_drawdown": self._max_drawdown,
                "max_positions": self._max_positions,
                "max_position_size": self._max_position_size,
            },
            "any_breach": any(limits.values()),
        }
