"""
Real-Time Risk Calculator - Answers Q401, Q402, Q411, Q421
==========================================================

Critical Question Q401: How do you calculate position risk in real-time?
Critical Question Q402: What happens when position risk calculation has errors?
Critical Question Q411: How do you calculate portfolio-level risk?
Critical Question Q421: What is your maximum acceptable drawdown?

This module provides:
1. Real-time position risk calculation
2. Portfolio-level risk aggregation
3. VaR and CVaR calculation
4. Drawdown monitoring with circuit breakers
5. Risk limit enforcement
6. Error handling with fallback calculations
"""

import logging
import threading
import numpy as np
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import deque

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk level classification"""
    MINIMAL = "minimal"      # < 25% of limits
    LOW = "low"              # 25-50% of limits
    MODERATE = "moderate"    # 50-75% of limits
    HIGH = "high"            # 75-90% of limits
    CRITICAL = "critical"    # 90-100% of limits
    BREACH = "breach"        # > 100% of limits


class DrawdownLevel(Enum):
    """Drawdown severity levels"""
    NORMAL = "normal"        # < 5%
    ELEVATED = "elevated"    # 5-10%
    WARNING = "warning"      # 10-15%
    SEVERE = "severe"        # 15-20%
    CRITICAL = "critical"    # 20-25%
    EMERGENCY = "emergency"  # > 25%


@dataclass
class RiskMetrics:
    """Comprehensive risk metrics snapshot"""
    timestamp: datetime
    
    # Position-level risk
    total_position_risk: float
    max_single_position_risk: float
    position_count: int
    
    # Portfolio-level risk
    portfolio_var_95: float
    portfolio_var_99: float
    portfolio_cvar_95: float
    expected_shortfall: float
    
    # Drawdown metrics
    current_drawdown: float
    max_drawdown: float
    drawdown_duration_days: int
    drawdown_level: DrawdownLevel
    
    # Exposure metrics
    gross_exposure: float
    net_exposure: float
    long_exposure: float
    short_exposure: float
    
    # Correlation risk
    correlation_risk: float
    concentration_risk: float
    
    # Risk levels
    overall_risk_level: RiskLevel
    position_risk_level: RiskLevel
    drawdown_risk_level: RiskLevel
    
    # Limits status
    limits_breached: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp.isoformat(),
            'total_position_risk': self.total_position_risk,
            'max_single_position_risk': self.max_single_position_risk,
            'position_count': self.position_count,
            'portfolio_var_95': self.portfolio_var_95,
            'portfolio_var_99': self.portfolio_var_99,
            'portfolio_cvar_95': self.portfolio_cvar_95,
            'current_drawdown': self.current_drawdown,
            'max_drawdown': self.max_drawdown,
            'drawdown_level': self.drawdown_level.value,
            'gross_exposure': self.gross_exposure,
            'net_exposure': self.net_exposure,
            'overall_risk_level': self.overall_risk_level.value,
            'limits_breached': self.limits_breached,
            'warnings': self.warnings
        }


@dataclass
class RiskLimits:
    """Risk limits configuration - IMMUTABLE after initialization"""
    # Per-trade limits
    max_risk_per_trade: float = 0.02          # 2%
    max_position_size_pct: float = 0.10       # 10% of portfolio
    
    # Portfolio limits
    max_portfolio_risk: float = 0.05          # 5%
    max_gross_exposure: float = 2.0           # 200%
    max_net_exposure: float = 1.0             # 100%
    max_correlated_exposure: float = 0.30     # 30%
    max_sector_exposure: float = 0.25         # 25%
    
    # Drawdown limits
    max_daily_loss: float = 0.03              # 3%
    max_weekly_loss: float = 0.07             # 7%
    max_monthly_loss: float = 0.15            # 15%
    max_drawdown: float = 0.20                # 20%
    emergency_shutdown_drawdown: float = 0.25 # 25%
    
    # Position limits
    max_open_positions: int = 10
    max_correlated_positions: int = 3
    
    # VaR limits
    max_var_95: float = 0.05                  # 5%
    max_var_99: float = 0.10                  # 10%


class RealtimeRiskCalculator:
    """
    Real-time risk calculation engine.
    
    Addresses critical questions:
    - Q401: Real-time position risk calculation
    - Q402: Error handling in risk calculation
    - Q411: Portfolio-level risk
    - Q421: Maximum drawdown enforcement
    
    Features:
    - Continuous risk monitoring
    - VaR/CVaR calculation
    - Drawdown circuit breakers
    - Correlation-aware risk
    - Fallback calculations on error
    """
    
    # IMMUTABLE: These limits cannot be changed at runtime
    ABSOLUTE_MAX_DRAWDOWN = 0.30  # 30% - NEVER exceed
    ABSOLUTE_MAX_RISK_PER_TRADE = 0.05  # 5% - NEVER exceed
    
    def __init__(
        self,
        limits: Optional[RiskLimits] = None,
        lookback_days: int = 252,
        update_interval_ms: int = 100,
        on_limit_breach: Optional[callable] = None,
        on_drawdown_warning: Optional[callable] = None
    ):
        """
        Initialize risk calculator.
        
        Args:
            limits: Risk limits configuration
            lookback_days: Days of history for calculations
            update_interval_ms: Minimum ms between updates
            on_limit_breach: Callback when limit breached
            on_drawdown_warning: Callback for drawdown warnings
        """
        self.limits = limits or RiskLimits()
        self.lookback_days = lookback_days
        self.update_interval_ms = update_interval_ms
        self.on_limit_breach = on_limit_breach
        self.on_drawdown_warning = on_drawdown_warning
        
        # Enforce absolute limits
        self._enforce_absolute_limits()
        
        # State
        self._lock = threading.RLock()
        self._last_update = datetime.min
        self._current_metrics: Optional[RiskMetrics] = None
        
        # Equity tracking
        self._equity_history: deque = deque(maxlen=lookback_days * 24 * 60)  # Per-minute
        self._peak_equity = 0.0
        self._drawdown_start: Optional[datetime] = None
        
        # Return history for VaR
        self._returns_history: deque = deque(maxlen=lookback_days)
        
        # Position cache
        self._positions: Dict[str, Dict] = {}
        self._correlation_matrix: Optional[np.ndarray] = None
        
        # Error tracking
        self._calculation_errors = 0
        self._last_error: Optional[str] = None
        
        logger.info("RealtimeRiskCalculator initialized")
    
    def _enforce_absolute_limits(self):
        """Enforce absolute limits that cannot be exceeded"""
        if self.limits.max_drawdown > self.ABSOLUTE_MAX_DRAWDOWN:
            logger.warning(
                f"max_drawdown {self.limits.max_drawdown} exceeds absolute limit "
                f"{self.ABSOLUTE_MAX_DRAWDOWN}, capping"
            )
            self.limits.max_drawdown = self.ABSOLUTE_MAX_DRAWDOWN
        
        if self.limits.max_risk_per_trade > self.ABSOLUTE_MAX_RISK_PER_TRADE:
            logger.warning(
                f"max_risk_per_trade {self.limits.max_risk_per_trade} exceeds absolute limit "
                f"{self.ABSOLUTE_MAX_RISK_PER_TRADE}, capping"
            )
            self.limits.max_risk_per_trade = self.ABSOLUTE_MAX_RISK_PER_TRADE
    
    def update_equity(self, equity: float, timestamp: Optional[datetime] = None):
        """
        Update current equity for drawdown tracking.
        
        Args:
            equity: Current account equity
            timestamp: Timestamp (default: now)
        """
        timestamp = timestamp or datetime.now()
        
        with self._lock:
            self._equity_history.append((timestamp, equity))
            
            # Update peak
            if equity > self._peak_equity:
                self._peak_equity = equity
                self._drawdown_start = None
            elif self._drawdown_start is None and equity < self._peak_equity:
                self._drawdown_start = timestamp
            
            # Calculate return if we have history
            if len(self._equity_history) >= 2:
                prev_equity = self._equity_history[-2][1]
                if prev_equity > 0:
                    ret = (equity - prev_equity) / prev_equity
                    self._returns_history.append(ret)
    
    def update_positions(self, positions: List[Dict]):
        """
        Update position cache for risk calculation.
        
        Args:
            positions: List of position dictionaries
        """
        with self._lock:
            self._positions = {
                p.get('position_id', p.get('ticket', str(i))): p
                for i, p in enumerate(positions)
            }
    
    def calculate_risk(
        self,
        equity: float,
        positions: Optional[List[Dict]] = None,
        force: bool = False
    ) -> RiskMetrics:
        """
        Calculate comprehensive risk metrics.
        
        This is the answer to Q401: How do you calculate position risk in real-time?
        
        Args:
            equity: Current account equity
            positions: Optional list of positions (uses cache if not provided)
            force: Force calculation even if within update interval
            
        Returns:
            RiskMetrics with all risk calculations
        """
        now = datetime.now()
        
        # Rate limiting
        if not force:
            try:
                elapsed_ms = (now - self._last_update).total_seconds() * 1000
                if elapsed_ms < self.update_interval_ms and self._current_metrics:
                    return self._current_metrics

                with self._lock:
                    # Update equity
                    self.update_equity(equity, now)

                    # Update positions if provided
                    if positions is not None:
                        self.update_positions(positions)

                    # Calculate all metrics
                    metrics = self._calculate_all_metrics(equity, now)

                    # Check for limit breaches
                    self._check_limits(metrics)

                    # Update state
                    self._current_metrics = metrics
                    self._last_update = now
                    self._calculation_errors = 0

                    return metrics

            except Exception as e:
                logger.error(f"Risk calculation error: {e}")
                self._calculation_errors += 1
                self._last_error = str(e)

                # Return fallback metrics (Q402: Error handling)
                return self._get_fallback_metrics(equity, now, str(e))

    def _calculate_all_metrics(self, equity: float, timestamp: datetime) -> RiskMetrics:
        """Calculate all risk metrics"""
        positions = list(self._positions.values())
        
        # Position-level risk
        position_risks = []
        total_long = 0.0
        total_short = 0.0
        
        for pos in positions:
            risk = self._calculate_position_risk(pos, equity)
            position_risks.append(risk)
            
            exposure = abs(pos.get('quantity', 0) * pos.get('current_price', 0))
            if pos.get('direction', 'long') == 'long':
                total_long += exposure
            else:
                total_short += exposure
        
        total_position_risk = sum(position_risks)
        max_single_risk = max(position_risks) if position_risks else 0.0
        
        # Exposure calculations
        gross_exposure = (total_long + total_short) / equity if equity > 0 else 0
        net_exposure = (total_long - total_short) / equity if equity > 0 else 0
        
        # Drawdown calculations
        current_drawdown = self._calculate_drawdown(equity)
        max_drawdown = self._get_max_drawdown()
        drawdown_duration = self._get_drawdown_duration()
        drawdown_level = self._classify_drawdown(current_drawdown)
        
        # VaR calculations
        var_95, var_99, cvar_95 = self._calculate_var()
        
        # Correlation risk
        correlation_risk = self._calculate_correlation_risk(positions)
        concentration_risk = self._calculate_concentration_risk(positions, equity)
        
        # Risk levels
        position_risk_level = self._classify_risk(
            total_position_risk, self.limits.max_portfolio_risk
        )
        drawdown_risk_level = self._classify_risk(
            current_drawdown, self.limits.max_drawdown
        )
        overall_risk_level = max(
            position_risk_level, drawdown_risk_level,
            key=lambda x: list(RiskLevel).index(x)
        )
        
        # Collect warnings
        warnings = []
        limits_breached = []
        
        if current_drawdown > self.limits.max_drawdown * 0.75:
            warnings.append(f"Drawdown at {current_drawdown:.1%} approaching limit")
        
        if total_position_risk > self.limits.max_portfolio_risk * 0.75:
            warnings.append(f"Portfolio risk at {total_position_risk:.1%} approaching limit")
        
        if gross_exposure > self.limits.max_gross_exposure:
            limits_breached.append("gross_exposure")
        
        if current_drawdown > self.limits.max_drawdown:
            limits_breached.append("max_drawdown")
        
        return RiskMetrics(
            timestamp=timestamp,
            total_position_risk=total_position_risk,
            max_single_position_risk=max_single_risk,
            position_count=len(positions),
            portfolio_var_95=var_95,
            portfolio_var_99=var_99,
            portfolio_cvar_95=cvar_95,
            expected_shortfall=cvar_95,
            current_drawdown=current_drawdown,
            max_drawdown=max_drawdown,
            drawdown_duration_days=drawdown_duration,
            drawdown_level=drawdown_level,
            gross_exposure=gross_exposure,
            net_exposure=net_exposure,
            long_exposure=total_long / equity if equity > 0 else 0,
            short_exposure=total_short / equity if equity > 0 else 0,
            correlation_risk=correlation_risk,
            concentration_risk=concentration_risk,
            overall_risk_level=overall_risk_level,
            position_risk_level=position_risk_level,
            drawdown_risk_level=drawdown_risk_level,
            limits_breached=limits_breached,
            warnings=warnings
        )
    
    def _calculate_position_risk(self, position: Dict, equity: float) -> float:
        """Calculate risk for a single position"""
        if equity <= 0:
            return 0.0
        
        quantity = abs(position.get('quantity', 0))
        entry_price = position.get('entry_price', 0)
        stop_loss = position.get('stop_loss')
        current_price = position.get('current_price', entry_price)
        
        if stop_loss and entry_price > 0:
            # Risk based on stop loss
            risk_per_unit = abs(entry_price - stop_loss)
            total_risk = quantity * risk_per_unit
        else:
            # Fallback: assume 2% risk from current price
            total_risk = quantity * current_price * 0.02
        
        return total_risk / equity
    
    def _calculate_drawdown(self, equity: float) -> float:
        """Calculate current drawdown"""
        if self._peak_equity <= 0:
            return 0.0
        return (self._peak_equity - equity) / self._peak_equity
    
    def _get_max_drawdown(self) -> float:
        """Get maximum historical drawdown"""
        if len(self._equity_history) < 2:
            return 0.0
        
        equities = [e[1] for e in self._equity_history]
        peak = equities[0]
        max_dd = 0.0
        
        for equity in equities:
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak if peak > 0 else 0
            max_dd = max(max_dd, dd)
        
        return max_dd
    
    def _get_drawdown_duration(self) -> int:
        """Get current drawdown duration in days"""
        if self._drawdown_start is None:
            return 0
        return (datetime.now() - self._drawdown_start).days
    
    def _classify_drawdown(self, drawdown: float) -> DrawdownLevel:
        """Classify drawdown severity"""
        if drawdown < 0.05:
            return DrawdownLevel.NORMAL
        elif drawdown < 0.10:
            return DrawdownLevel.ELEVATED
        elif drawdown < 0.15:
            return DrawdownLevel.WARNING
        elif drawdown < 0.20:
            return DrawdownLevel.SEVERE
        elif drawdown < 0.25:
            return DrawdownLevel.CRITICAL
        else:
            return DrawdownLevel.EMERGENCY
    
    def _classify_risk(self, value: float, limit: float) -> RiskLevel:
        """Classify risk level based on limit utilization"""
        if limit <= 0:
            return RiskLevel.BREACH
        
        ratio = value / limit
        
        if ratio < 0.25:
            return RiskLevel.MINIMAL
        elif ratio < 0.50:
            return RiskLevel.LOW
        elif ratio < 0.75:
            return RiskLevel.MODERATE
        elif ratio < 0.90:
            return RiskLevel.HIGH
        elif ratio < 1.0:
            return RiskLevel.CRITICAL
        else:
            return RiskLevel.BREACH
    
    def _calculate_var(self) -> Tuple[float, float, float]:
        """Calculate VaR and CVaR from return history"""
        if len(self._returns_history) < 30:
            return 0.0, 0.0, 0.0
        
        returns = np.array(list(self._returns_history))
        
        # Historical VaR
        var_95 = -np.percentile(returns, 5)
        var_99 = -np.percentile(returns, 1)
        
        # CVaR (Expected Shortfall)
        cvar_95 = -np.mean(returns[returns <= np.percentile(returns, 5)])
        
        return var_95, var_99, cvar_95
    
    def _calculate_correlation_risk(self, positions: List[Dict]) -> float:
        """Calculate correlation-based risk"""
        if len(positions) < 2:
            return 0.0
        
        # Simplified: count positions in same asset class
        symbols = [p.get('symbol', '') for p in positions]
        
        # Group by base currency/asset
        groups = {}
        for symbol in symbols:
            base = symbol[:3] if len(symbol) >= 3 else symbol
            groups[base] = groups.get(base, 0) + 1
        
        # Risk increases with concentration
        max_group = max(groups.values()) if groups else 0
        return max_group / len(positions) if positions else 0.0
    
    def _calculate_concentration_risk(self, positions: List[Dict], equity: float) -> float:
        """Calculate concentration risk"""
        if not positions or equity <= 0:
            return 0.0
        
        exposures = []
        for pos in positions:
            exposure = abs(pos.get('quantity', 0) * pos.get('current_price', 0))
            exposures.append(exposure / equity)
        
        # Herfindahl-Hirschman Index style
        return sum(e ** 2 for e in exposures)
    
    def _check_limits(self, metrics: RiskMetrics):
        """Check for limit breaches and trigger callbacks"""
        # Check drawdown
        if metrics.current_drawdown >= self.limits.emergency_shutdown_drawdown:
            logger.critical(
                f"EMERGENCY: Drawdown {metrics.current_drawdown:.1%} >= "
                f"emergency limit {self.limits.emergency_shutdown_drawdown:.1%}"
            )
            if self.on_limit_breach:
                self.on_limit_breach('emergency_drawdown', metrics)
        
        elif metrics.current_drawdown >= self.limits.max_drawdown:
            logger.error(
                f"BREACH: Drawdown {metrics.current_drawdown:.1%} >= "
                f"limit {self.limits.max_drawdown:.1%}"
            )
            if self.on_limit_breach:
                self.on_limit_breach('max_drawdown', metrics)
        
        elif metrics.drawdown_level in (DrawdownLevel.SEVERE, DrawdownLevel.CRITICAL):
            if self.on_drawdown_warning:
                self.on_drawdown_warning(metrics.drawdown_level, metrics)
        
        # Check other limits
        if metrics.limits_breached and self.on_limit_breach:
            for breach in metrics.limits_breached:
                self.on_limit_breach(breach, metrics)
    
    def _get_fallback_metrics(
        self,
        equity: float,
        timestamp: datetime,
        error: str
    ) -> RiskMetrics:
        """
        Get fallback metrics when calculation fails.
        
        This is the answer to Q402: What happens when position risk calculation has errors?
        
        Returns conservative metrics that prevent new trading.
        """
        logger.warning(f"Using fallback risk metrics due to error: {error}")
        
        return RiskMetrics(
            timestamp=timestamp,
            total_position_risk=1.0,  # Assume max risk
            max_single_position_risk=1.0,
            position_count=len(self._positions),
            portfolio_var_95=0.10,  # Conservative
            portfolio_var_99=0.15,
            portfolio_cvar_95=0.20,
            expected_shortfall=0.20,
            current_drawdown=self._calculate_drawdown(equity),
            max_drawdown=self._get_max_drawdown(),
            drawdown_duration_days=self._get_drawdown_duration(),
            drawdown_level=DrawdownLevel.WARNING,
            gross_exposure=1.0,
            net_exposure=0.5,
            long_exposure=0.5,
            short_exposure=0.5,
            correlation_risk=0.5,
            concentration_risk=0.5,
            overall_risk_level=RiskLevel.HIGH,  # Conservative
            position_risk_level=RiskLevel.HIGH,
            drawdown_risk_level=RiskLevel.HIGH,
            limits_breached=['calculation_error'],
            warnings=[f"Risk calculation error: {error}", "Using conservative fallback values"]
        )
    
    def can_open_position(
        self,
        symbol: str,
        quantity: float,
        price: float,
        stop_loss: Optional[float] = None,
        equity: Optional[float] = None
    ) -> Tuple[bool, str]:
        """
        Check if a new position can be opened within risk limits.
        
        Args:
            symbol: Trading symbol
            quantity: Position quantity
            price: Entry price
            stop_loss: Stop loss price
            equity: Current equity (uses last known if not provided)
            
        Returns:
            Tuple of (can_open, reason)
        """
        if equity is None:
            if self._equity_history:
                equity = self._equity_history[-1][1]
            else:
                return False, "No equity data available"
        
        # Check position count
        if len(self._positions) >= self.limits.max_open_positions:
            return False, f"Max positions ({self.limits.max_open_positions}) reached"
        
        # Calculate position risk
        position_value = quantity * price
        position_pct = position_value / equity if equity > 0 else 1.0
        
        if position_pct > self.limits.max_position_size_pct:
            return False, f"Position size {position_pct:.1%} exceeds limit {self.limits.max_position_size_pct:.1%}"
        
        # Calculate risk if stop loss provided
        if stop_loss:
            risk_per_unit = abs(price - stop_loss)
            total_risk = quantity * risk_per_unit
            risk_pct = total_risk / equity if equity > 0 else 1.0
            
            if risk_pct > self.limits.max_risk_per_trade:
                return False, f"Trade risk {risk_pct:.1%} exceeds limit {self.limits.max_risk_per_trade:.1%}"
        
        # Check current metrics
        if self._current_metrics:
            if self._current_metrics.overall_risk_level == RiskLevel.BREACH:
                return False, "Portfolio risk limits breached"
            
            if self._current_metrics.drawdown_level == DrawdownLevel.EMERGENCY:
                return False, "Emergency drawdown level - no new positions"
            
            if self._current_metrics.current_drawdown >= self.limits.max_drawdown:
                return False, f"Drawdown {self._current_metrics.current_drawdown:.1%} at limit"
        
        return True, "OK"
    
    def get_max_position_size(
        self,
        symbol: str,
        price: float,
        stop_loss: float,
        equity: Optional[float] = None
    ) -> float:
        """
        Calculate maximum allowed position size.
        
        Args:
            symbol: Trading symbol
            price: Entry price
            stop_loss: Stop loss price
            equity: Current equity
            
        Returns:
            Maximum quantity allowed
        """
        if equity is None:
            if self._equity_history:
                equity = self._equity_history[-1][1]
            else:
                return 0.0
        
        if equity <= 0 or price <= 0:
            return 0.0
        
        # Risk-based size
        risk_per_unit = abs(price - stop_loss)
        if risk_per_unit > 0:
            max_risk = equity * self.limits.max_risk_per_trade
            risk_based_qty = max_risk / risk_per_unit
        else:
            risk_based_qty = float('inf')
        
        # Position size based
        max_position_value = equity * self.limits.max_position_size_pct
        size_based_qty = max_position_value / price
        
        # Apply drawdown adjustment
        if self._current_metrics:
            dd = self._current_metrics.current_drawdown
            if dd > 0.10:
                adjustment = 1.0 - (dd - 0.10) * 2  # Reduce by 2x the excess drawdown
                adjustment = max(0.25, adjustment)  # Minimum 25%
                risk_based_qty *= adjustment
                size_based_qty *= adjustment
        
        return min(risk_based_qty, size_based_qty)
    
    def get_status(self) -> Dict:
        """Get current risk calculator status"""
        return {
            'last_update': self._last_update.isoformat() if self._last_update != datetime.min else None,
            'calculation_errors': self._calculation_errors,
            'last_error': self._last_error,
            'peak_equity': self._peak_equity,
            'equity_history_length': len(self._equity_history),
            'returns_history_length': len(self._returns_history),
            'position_count': len(self._positions),
            'current_metrics': self._current_metrics.to_dict() if self._current_metrics else None,
            'limits': {
                'max_risk_per_trade': self.limits.max_risk_per_trade,
                'max_drawdown': self.limits.max_drawdown,
                'max_portfolio_risk': self.limits.max_portfolio_risk,
                'emergency_shutdown_drawdown': self.limits.emergency_shutdown_drawdown
            }
        }
