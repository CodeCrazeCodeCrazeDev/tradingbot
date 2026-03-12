"""
Growth Optimization Framework - Capital Preservation and Compound Growth

Implements institutional-grade growth optimization:
- Capital preservation foundation
- Compound growth engine
- Progressive position scaling
- Performance-based risk adjustment
- Drawdown management
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
import numpy as np
from collections import deque
import numpy

logger = logging.getLogger(__name__)


class GrowthMode(Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    RECOVERY = "recovery"
    PROTECTION = "protection"


class DrawdownLevel(Enum):
    NORMAL = "normal"           # < 5%
    ELEVATED = "elevated"       # 5-10%
    HIGH = "high"               # 10-15%
    CRITICAL = "critical"       # 15-20%
    EMERGENCY = "emergency"     # > 20%


@dataclass
class GrowthMetrics:
    """Growth performance metrics"""
    total_return: float
    monthly_return: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    current_drawdown: float
    recovery_factor: float
    profit_factor: float
    win_rate: float
    avg_win: float
    avg_loss: float
    expectancy: float
    trades_count: int
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class PositionScaling:
    """Position scaling parameters"""
    base_risk_pct: float
    current_risk_pct: float
    max_risk_pct: float
    scaling_factor: float
    drawdown_adjustment: float
    volatility_adjustment: float
    performance_adjustment: float
    final_position_size: float


@dataclass
class DrawdownManagement:
    """Drawdown management state"""
    current_drawdown: float
    peak_equity: float
    drawdown_level: DrawdownLevel
    risk_reduction: float
    cooling_off: bool
    cooling_off_until: Optional[datetime]
    recovery_mode: bool
    trades_since_peak: int


class GrowthOptimizationFramework:
    """
    Growth Optimization Framework
    
    Implements sophisticated capital growth strategies:
    - Progressive position scaling based on performance
    - Dynamic risk adjustment based on drawdown
    - Compound growth optimization
    - Capital preservation mechanisms
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
        
            # Base parameters
            self.initial_capital = self.config.get('initial_capital', 10000)
            self.current_equity = self.initial_capital
            self.peak_equity = self.initial_capital
        
            # Risk parameters
            self.base_risk_pct = self.config.get('base_risk_pct', 0.5)  # 0.5% base risk
            self.max_risk_pct = self.config.get('max_risk_pct', 2.0)   # 2% max risk
            self.min_risk_pct = self.config.get('min_risk_pct', 0.1)   # 0.1% min risk
        
            # Drawdown limits
            self.daily_loss_limit = self.config.get('daily_loss_limit', 3.0)    # 3%
            self.weekly_loss_limit = self.config.get('weekly_loss_limit', 5.0)  # 5%
            self.monthly_loss_limit = self.config.get('monthly_loss_limit', 10.0)  # 10%
            self.max_drawdown_limit = self.config.get('max_drawdown_limit', 20.0)  # 20%
        
            # Growth targets
            self.monthly_target = self.config.get('monthly_target', 5.0)  # 5% monthly
            self.annual_target = self.config.get('annual_target', 60.0)  # 60% annual
        
            # Scaling parameters
            self.scaling_threshold = self.config.get('scaling_threshold', 100)  # trades
            self.performance_window = self.config.get('performance_window', 50)  # trades
        
            # State tracking
            self.trade_history: deque = deque(maxlen=1000)
            self.equity_curve: deque = deque(maxlen=10000)
            self.daily_pnl: Dict[str, float] = {}
            self.weekly_pnl: Dict[str, float] = {}
            self.monthly_pnl: Dict[str, float] = {}
        
            # Current state
            self.growth_mode = GrowthMode.MODERATE
            self.drawdown_state = DrawdownManagement(
                current_drawdown=0.0,
                peak_equity=self.initial_capital,
                drawdown_level=DrawdownLevel.NORMAL,
                risk_reduction=1.0,
                cooling_off=False,
                cooling_off_until=None,
                recovery_mode=False,
                trades_since_peak=0
            )
        
            logger.info("GrowthOptimizationFramework initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def calculate_position_size(
        self,
        signal: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> PositionScaling:
        """
        Calculate optimal position size based on multiple factors
        
        Args:
            signal: Trading signal with entry, stop_loss
            market_data: Current market data
            
        Returns:
            PositionScaling with all adjustments
        """
        # Get base risk
        try:
            base_risk = self.base_risk_pct
        
            # Calculate adjustments
            drawdown_adj = self._calculate_drawdown_adjustment()
            volatility_adj = self._calculate_volatility_adjustment(market_data)
            performance_adj = self._calculate_performance_adjustment()
        
            # Calculate scaling factor
            scaling_factor = self._calculate_scaling_factor()
        
            # Apply all adjustments
            adjusted_risk = base_risk * drawdown_adj * volatility_adj * performance_adj * scaling_factor
        
            # Clamp to limits
            final_risk = max(self.min_risk_pct, min(self.max_risk_pct, adjusted_risk))
        
            # Calculate actual position size
            entry_price = signal.get('entry_price') or 0
            stop_loss = signal.get('stop_loss') or 0
        
            if entry_price and entry_price > 0 and stop_loss and stop_loss > 0:
                risk_per_unit = abs(entry_price - stop_loss)
                risk_amount = self.current_equity * (final_risk / 100)
                position_size = risk_amount / risk_per_unit if risk_per_unit > 0 else 0
            else:
                position_size = 0
        
            return PositionScaling(
                base_risk_pct=base_risk,
                current_risk_pct=final_risk,
                max_risk_pct=self.max_risk_pct,
                scaling_factor=scaling_factor,
                drawdown_adjustment=drawdown_adj,
                volatility_adjustment=volatility_adj,
                performance_adjustment=performance_adj,
                final_position_size=position_size
            )
        except Exception as e:
            logger.error(f"Error in calculate_position_size: {e}")
            raise
    
    def update_equity(self, pnl: float, trade_result: Optional[Dict[str, Any]] = None):
        """Update equity and track performance"""
        try:
            self.current_equity += pnl
        
            # Update peak equity
            if self.current_equity > self.peak_equity:
                self.peak_equity = self.current_equity
                self.drawdown_state.trades_since_peak = 0
                self.drawdown_state.recovery_mode = False
            else:
                self.drawdown_state.trades_since_peak += 1
        
            # Update drawdown
            self._update_drawdown()
        
            # Track equity curve
            self.equity_curve.append({
                'equity': self.current_equity,
                'pnl': pnl,
                'timestamp': datetime.now()
            })
        
            # Track daily/weekly/monthly PnL
            self._track_periodic_pnl(pnl)
        
            # Track trade if provided
            if trade_result:
                self.trade_history.append(trade_result)
        
            # Update growth mode
            self._update_growth_mode()
        
            logger.debug(f"Equity updated: {self.current_equity:.2f}, DD: {self.drawdown_state.current_drawdown:.2%}")
        except Exception as e:
            logger.error(f"Error in update_equity: {e}")
            raise
    
    def get_growth_metrics(self) -> GrowthMetrics:
        """Calculate comprehensive growth metrics"""
        try:
            trades = list(self.trade_history)
            equity_data = list(self.equity_curve)
        
            if not trades:
                return GrowthMetrics(
                    total_return=0, monthly_return=0, sharpe_ratio=0, sortino_ratio=0,
                    max_drawdown=0, current_drawdown=0, recovery_factor=0, profit_factor=0,
                    win_rate=0, avg_win=0, avg_loss=0, expectancy=0, trades_count=0
                )
        
            # Calculate returns
            total_return = (self.current_equity - self.initial_capital) / self.initial_capital
        
            # Monthly return (simplified)
            if equity_data:
                days = (datetime.now() - equity_data[0]['timestamp']).days or 1
                monthly_return = total_return * (30 / days)
            else:
                monthly_return = 0
        
            # Win/Loss statistics
            wins = [t for t in trades if t.get('pnl', 0) > 0]
            losses = [t for t in trades if t.get('pnl', 0) < 0]
        
            win_rate = len(wins) / len(trades) if trades else 0
            avg_win = np.mean([t['pnl'] for t in wins]) if wins else 0
            avg_loss = abs(np.mean([t['pnl'] for t in losses])) if losses else 0
        
            # Profit factor
            gross_profit = sum(t['pnl'] for t in wins)
            gross_loss = abs(sum(t['pnl'] for t in losses))
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
            # Expectancy
            expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
        
            # Sharpe/Sortino (simplified)
            returns = [e['pnl'] / self.initial_capital for e in equity_data]
            if len(returns) > 1:
                sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
                negative_returns = [r for r in returns if r < 0]
                downside_std = np.std(negative_returns) if negative_returns else 0.0001
                sortino_ratio = np.mean(returns) / downside_std * np.sqrt(252)
            else:
                sharpe_ratio = 0
                sortino_ratio = 0
        
            # Max drawdown
            max_dd = self._calculate_max_drawdown()
        
            # Recovery factor
            recovery_factor = total_return / max_dd if max_dd > 0 else float('inf')
        
            return GrowthMetrics(
                total_return=total_return,
                monthly_return=monthly_return,
                sharpe_ratio=sharpe_ratio,
                sortino_ratio=sortino_ratio,
                max_drawdown=max_dd,
                current_drawdown=self.drawdown_state.current_drawdown,
                recovery_factor=recovery_factor,
                profit_factor=profit_factor,
                win_rate=win_rate,
                avg_win=avg_win,
                avg_loss=avg_loss,
                expectancy=expectancy,
                trades_count=len(trades)
            )
        except Exception as e:
            logger.error(f"Error in get_growth_metrics: {e}")
            raise
    
    def check_trading_allowed(self) -> tuple:
        """Check if trading is allowed based on risk limits"""
        try:
            reasons = []
            allowed = True
        
            # Check cooling off period
            if self.drawdown_state.cooling_off:
                if datetime.now() < self.drawdown_state.cooling_off_until:
                    allowed = False
                    reasons.append("Cooling off period active")
                else:
                    self.drawdown_state.cooling_off = False
        
            # Check daily loss limit
            today = datetime.now().strftime('%Y-%m-%d')
            daily_loss = self.daily_pnl.get(today, 0)
            if daily_loss < -self.daily_loss_limit * self.current_equity / 100:
                allowed = False
                reasons.append(f"Daily loss limit reached: {daily_loss:.2f}")
        
            # Check drawdown level
            if self.drawdown_state.drawdown_level == DrawdownLevel.EMERGENCY:
                allowed = False
                reasons.append(f"Emergency drawdown: {self.drawdown_state.current_drawdown:.2%}")
        
            # Check max drawdown
            if self.drawdown_state.current_drawdown > self.max_drawdown_limit / 100:
                allowed = False
                reasons.append(f"Max drawdown exceeded: {self.drawdown_state.current_drawdown:.2%}")
        
            return allowed, reasons
        except Exception as e:
            logger.error(f"Error in check_trading_allowed: {e}")
            raise
    
    def _calculate_drawdown_adjustment(self) -> float:
        """Calculate risk adjustment based on drawdown"""
        try:
            dd = self.drawdown_state.current_drawdown
        
            if dd < 0.05:  # < 5%
                return 1.0
            elif dd < 0.10:  # 5-10%
                return 0.75
            elif dd < 0.15:  # 10-15%
                return 0.5
            elif dd < 0.20:  # 15-20%
                return 0.25
            else:  # > 20%
                return 0.1
        except Exception as e:
            logger.error(f"Error in _calculate_drawdown_adjustment: {e}")
            raise
    
    def _calculate_volatility_adjustment(self, market_data: Dict[str, Any]) -> float:
        """Calculate risk adjustment based on volatility"""
        try:
            prices = market_data.get('prices', [])
            if len(prices) < 10:
                return 1.0
        
            price_array = np.array(prices)
            returns = np.diff(price_array) / price_array[:-1]
            volatility = np.std(returns)
        
            # Reduce risk in high volatility
            if volatility < 0.01:
                return 1.2  # Low vol = increase size
            elif volatility < 0.02:
                return 1.0
            elif volatility < 0.03:
                return 0.8
            elif volatility < 0.05:
                return 0.5
            else:
                return 0.3
        except Exception as e:
            logger.error(f"Error in _calculate_volatility_adjustment: {e}")
            raise
    
    def _calculate_performance_adjustment(self) -> float:
        """Calculate risk adjustment based on recent performance"""
        try:
            recent_trades = list(self.trade_history)[-self.performance_window:]
        
            if len(recent_trades) < 10:
                return 1.0
        
            wins = sum(1 for t in recent_trades if t.get('pnl', 0) > 0)
            win_rate = wins / len(recent_trades)
        
            # Adjust based on win rate
            if win_rate > 0.6:
                return 1.2  # Good performance = increase
            elif win_rate > 0.5:
                return 1.0
            elif win_rate > 0.4:
                return 0.8
            else:
                return 0.5  # Poor performance = reduce
        except Exception as e:
            logger.error(f"Error in _calculate_performance_adjustment: {e}")
            raise
    
    def _calculate_scaling_factor(self) -> float:
        """Calculate progressive scaling factor"""
        try:
            trades_count = len(self.trade_history)
        
            if trades_count < self.scaling_threshold:
                return 1.0  # Base level until proven
        
            metrics = self.get_growth_metrics()
        
            # Scale up if profitable and consistent
            if metrics.profit_factor > 1.5 and metrics.win_rate > 0.5:
                scale = min(2.0, 1.0 + (trades_count - self.scaling_threshold) / 500)
            elif metrics.profit_factor > 1.2:
                scale = 1.0
            else:
                scale = 0.8
        
            return scale
        except Exception as e:
            logger.error(f"Error in _calculate_scaling_factor: {e}")
            raise
    
    def _update_drawdown(self):
        """Update drawdown state"""
        try:
            if self.peak_equity > 0:
                dd = (self.peak_equity - self.current_equity) / self.peak_equity
            else:
                dd = 0
        
            self.drawdown_state.current_drawdown = dd
            self.drawdown_state.peak_equity = self.peak_equity
        
            # Determine drawdown level
            if dd < 0.05:
                self.drawdown_state.drawdown_level = DrawdownLevel.NORMAL
                self.drawdown_state.risk_reduction = 1.0
            elif dd < 0.10:
                self.drawdown_state.drawdown_level = DrawdownLevel.ELEVATED
                self.drawdown_state.risk_reduction = 0.75
            elif dd < 0.15:
                self.drawdown_state.drawdown_level = DrawdownLevel.HIGH
                self.drawdown_state.risk_reduction = 0.5
                self.drawdown_state.recovery_mode = True
            elif dd < 0.20:
                self.drawdown_state.drawdown_level = DrawdownLevel.CRITICAL
                self.drawdown_state.risk_reduction = 0.25
                self.drawdown_state.recovery_mode = True
            else:
                self.drawdown_state.drawdown_level = DrawdownLevel.EMERGENCY
                self.drawdown_state.risk_reduction = 0.1
                self.drawdown_state.cooling_off = True
                self.drawdown_state.cooling_off_until = datetime.now() + timedelta(hours=24)
        except Exception as e:
            logger.error(f"Error in _update_drawdown: {e}")
            raise
    
    def _track_periodic_pnl(self, pnl: float):
        """Track daily/weekly/monthly PnL"""
        try:
            now = datetime.now()
        
            # Daily
            day_key = now.strftime('%Y-%m-%d')
            self.daily_pnl[day_key] = self.daily_pnl.get(day_key, 0) + pnl
        
            # Weekly
            week_key = now.strftime('%Y-W%W')
            self.weekly_pnl[week_key] = self.weekly_pnl.get(week_key, 0) + pnl
        
            # Monthly
            month_key = now.strftime('%Y-%m')
            self.monthly_pnl[month_key] = self.monthly_pnl.get(month_key, 0) + pnl
        except Exception as e:
            logger.error(f"Error in _track_periodic_pnl: {e}")
            raise
    
    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown from equity curve"""
        try:
            equity_data = list(self.equity_curve)
            if not equity_data:
                return 0
        
            equities = [e['equity'] for e in equity_data]
            peak = equities[0]
            max_dd = 0
        
            for equity in equities:
                if equity > peak:
                    peak = equity
                dd = (peak - equity) / peak
                max_dd = max(max_dd, dd)
        
            return max_dd
        except Exception as e:
            logger.error(f"Error in _calculate_max_drawdown: {e}")
            raise
    
    def _update_growth_mode(self):
        """Update growth mode based on current state"""
        try:
            dd_level = self.drawdown_state.drawdown_level
        
            if dd_level == DrawdownLevel.EMERGENCY:
                self.growth_mode = GrowthMode.PROTECTION
            elif dd_level in [DrawdownLevel.CRITICAL, DrawdownLevel.HIGH]:
                self.growth_mode = GrowthMode.RECOVERY
            elif dd_level == DrawdownLevel.ELEVATED:
                self.growth_mode = GrowthMode.CONSERVATIVE
            else:
                # Check performance for aggressive mode
                metrics = self.get_growth_metrics()
                if metrics.profit_factor > 1.5 and metrics.win_rate > 0.55:
                    self.growth_mode = GrowthMode.AGGRESSIVE
                else:
                    self.growth_mode = GrowthMode.MODERATE
        except Exception as e:
            logger.error(f"Error in _update_growth_mode: {e}")
            raise
    
    def get_growth_status(self) -> Dict[str, Any]:
        """Get current growth status"""
        try:
            metrics = self.get_growth_metrics()
            allowed, reasons = self.check_trading_allowed()
        
            return {
                'current_equity': self.current_equity,
                'peak_equity': self.peak_equity,
                'total_return': metrics.total_return,
                'current_drawdown': self.drawdown_state.current_drawdown,
                'drawdown_level': self.drawdown_state.drawdown_level.value,
                'growth_mode': self.growth_mode.value,
                'trading_allowed': allowed,
                'trading_reasons': reasons,
                'risk_reduction': self.drawdown_state.risk_reduction,
                'recovery_mode': self.drawdown_state.recovery_mode,
                'trades_count': metrics.trades_count,
                'win_rate': metrics.win_rate,
                'profit_factor': metrics.profit_factor,
                'sharpe_ratio': metrics.sharpe_ratio
            }
        except Exception as e:
            logger.error(f"Error in get_growth_status: {e}")
            raise
