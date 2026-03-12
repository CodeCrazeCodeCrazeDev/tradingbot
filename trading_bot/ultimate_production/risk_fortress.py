"""
Risk Fortress - Bulletproof Risk Management System
==================================================

This module implements institutional-grade risk management with multiple
layers of protection to ensure capital preservation.

Risk Layers:
1. Pre-Trade Risk Checks
2. Position Sizing (Kelly, Fixed Fractional, Volatility-Based)
3. Portfolio Risk Management
4. Correlation Management
5. Drawdown Protection
6. Circuit Breakers
7. Emergency Controls

Core Principle: SURVIVAL FIRST - We can always make money tomorrow,
but only if we have capital to trade with.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import deque
import logging
import json

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk level classification"""
    MINIMAL = 1
    LOW = 2
    MODERATE = 3
    HIGH = 4
    EXTREME = 5


class PositionSizingMethod(Enum):
    """Position sizing methods"""
    FIXED_FRACTIONAL = "fixed_fractional"
    KELLY = "kelly"
    VOLATILITY_ADJUSTED = "volatility_adjusted"
    OPTIMAL_F = "optimal_f"
    ANTI_MARTINGALE = "anti_martingale"


@dataclass
class RiskLimits:
    """Risk limits configuration"""
    max_position_size: float = 0.02  # 2% per position
    max_portfolio_risk: float = 0.06  # 6% total portfolio risk
    max_daily_loss: float = 0.02  # 2% daily loss limit
    max_weekly_loss: float = 0.05  # 5% weekly loss limit
    max_monthly_loss: float = 0.10  # 10% monthly loss limit
    max_drawdown: float = 0.15  # 15% max drawdown
    max_positions: int = 5
    max_correlation: float = 0.7
    max_sector_exposure: float = 0.30  # 30% max in one sector
    min_risk_reward: float = 1.5
    max_leverage: float = 1.0  # No leverage by default
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'max_position_size': self.max_position_size,
            'max_portfolio_risk': self.max_portfolio_risk,
            'max_daily_loss': self.max_daily_loss,
            'max_weekly_loss': self.max_weekly_loss,
            'max_monthly_loss': self.max_monthly_loss,
            'max_drawdown': self.max_drawdown,
            'max_positions': self.max_positions,
            'max_correlation': self.max_correlation,
            'max_sector_exposure': self.max_sector_exposure,
            'min_risk_reward': self.min_risk_reward,
            'max_leverage': self.max_leverage,
        }


@dataclass
class RiskAssessment:
    """Risk assessment result"""
    approved: bool
    risk_level: RiskLevel
    risk_score: float  # 0-100
    position_size: float
    stop_loss: float
    take_profit: float
    reasons: List[str]
    warnings: List[str]
    adjustments: Dict[str, Any]


class PositionSizer:
    """
    Advanced position sizing calculator
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
            self.method = PositionSizingMethod(
                self.config.get('method', 'fixed_fractional')
            )
            self.base_risk = self.config.get('base_risk', 0.02)  # 2%
        
            # Performance tracking for Kelly
            self.trade_history: List[float] = []
            self.win_rate = 0.5
            self.avg_win = 0.0
            self.avg_loss = 0.0
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def calculate_size(
        self,
        capital: float,
        entry_price: float,
        stop_loss: float,
        volatility: float = 0.0,
        confidence: float = 0.5
    ) -> float:
        """
        Calculate optimal position size
        
        Args:
            capital: Available capital
            entry_price: Entry price
            stop_loss: Stop loss price
            volatility: Current volatility (0-1)
            confidence: Signal confidence (0-1)
        
        Returns:
            Position size as fraction of capital
        """
        try:
            risk_per_unit = abs(entry_price - stop_loss) / entry_price
        
            if risk_per_unit == 0:
                return 0
        
            if self.method == PositionSizingMethod.FIXED_FRACTIONAL:
                size = self._fixed_fractional(risk_per_unit)
            elif self.method == PositionSizingMethod.KELLY:
                size = self._kelly_criterion(risk_per_unit)
            elif self.method == PositionSizingMethod.VOLATILITY_ADJUSTED:
                size = self._volatility_adjusted(risk_per_unit, volatility)
            elif self.method == PositionSizingMethod.OPTIMAL_F:
                size = self._optimal_f(risk_per_unit)
            elif self.method == PositionSizingMethod.ANTI_MARTINGALE:
                size = self._anti_martingale(risk_per_unit)
            else:
                size = self._fixed_fractional(risk_per_unit)
        
            # Adjust for confidence
            size *= (0.5 + confidence * 0.5)  # Scale between 50% and 100%
        
            # Cap at maximum
            size = min(size, self.base_risk * 2)
        
            return size
        except Exception as e:
            logger.error(f"Error in calculate_size: {e}")
            raise
    
    def _fixed_fractional(self, risk_per_unit: float) -> float:
        """Fixed fractional position sizing"""
        return self.base_risk / risk_per_unit
    
    def _kelly_criterion(self, risk_per_unit: float) -> float:
        """Kelly criterion position sizing"""
        try:
            if self.avg_loss == 0 or len(self.trade_history) < 20:
                return self._fixed_fractional(risk_per_unit)
        
            # Kelly formula: f = (bp - q) / b
            # where b = avg_win/avg_loss, p = win_rate, q = 1 - p
            b = self.avg_win / self.avg_loss if self.avg_loss > 0 else 1
            p = self.win_rate
            q = 1 - p
        
            kelly = (b * p - q) / b if b > 0 else 0
        
            # Use half-Kelly for safety
            kelly = kelly * 0.5
        
            # Bound between 0 and base_risk * 2
            kelly = max(0, min(kelly, self.base_risk * 2))
        
            return kelly / risk_per_unit if risk_per_unit > 0 else 0
        except Exception as e:
            logger.error(f"Error in _kelly_criterion: {e}")
            raise
    
    def _volatility_adjusted(self, risk_per_unit: float, volatility: float) -> float:
        """Volatility-adjusted position sizing"""
        # Reduce size in high volatility
        try:
            vol_factor = 1 - (volatility * 0.5)  # Reduce up to 50% in high vol
            vol_factor = max(0.5, min(1.0, vol_factor))
        
            base_size = self._fixed_fractional(risk_per_unit)
            return base_size * vol_factor
        except Exception as e:
            logger.error(f"Error in _volatility_adjusted: {e}")
            raise
    
    def _optimal_f(self, risk_per_unit: float) -> float:
        """Optimal f position sizing (Ralph Vince)"""
        try:
            if len(self.trade_history) < 20:
                return self._fixed_fractional(risk_per_unit)
        
            # Find optimal f that maximizes geometric growth
            best_f = 0.01
            best_twp = 0
        
            for f in np.arange(0.01, 0.5, 0.01):
                twp = 1.0
                for trade in self.trade_history[-50:]:
                    twp *= (1 + f * trade)
                    if twp <= 0:
                        break
            
                if twp > best_twp:
                    best_twp = twp
                    best_f = f
        
            # Use fraction of optimal f for safety
            return (best_f * 0.5) / risk_per_unit if risk_per_unit > 0 else 0
        except Exception as e:
            logger.error(f"Error in _optimal_f: {e}")
            raise
    
    def _anti_martingale(self, risk_per_unit: float) -> float:
        """Anti-martingale: increase size after wins, decrease after losses"""
        try:
            if len(self.trade_history) < 5:
                return self._fixed_fractional(risk_per_unit)
        
            recent = self.trade_history[-5:]
            wins = sum(1 for t in recent if t > 0)
        
            # Adjust based on recent performance
            if wins >= 4:
                multiplier = 1.5  # Increase after winning streak
            elif wins <= 1:
                multiplier = 0.5  # Decrease after losing streak
            else:
                multiplier = 1.0
        
            base_size = self._fixed_fractional(risk_per_unit)
            return base_size * multiplier
        except Exception as e:
            logger.error(f"Error in _anti_martingale: {e}")
            raise
    
    def update_history(self, trade_return: float):
        """Update trade history for adaptive sizing"""
        try:
            self.trade_history.append(trade_return)
        
            # Keep last 100 trades
            if len(self.trade_history) > 100:
                self.trade_history = self.trade_history[-100:]
        
            # Update statistics
            if len(self.trade_history) >= 10:
                wins = [t for t in self.trade_history if t > 0]
                losses = [t for t in self.trade_history if t < 0]
            
                self.win_rate = len(wins) / len(self.trade_history)
                self.avg_win = np.mean(wins) if wins else 0
                self.avg_loss = abs(np.mean(losses)) if losses else 0
        except Exception as e:
            logger.error(f"Error in update_history: {e}")
            raise


class CorrelationManager:
    """
    Manage correlation between positions
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
            self.max_correlation = self.config.get('max_correlation', 0.7)
        
            # Known correlations (simplified - in production, calculate from data)
            self.correlation_matrix = {
                ('EURUSD', 'GBPUSD'): 0.85,
                ('EURUSD', 'USDCHF'): -0.90,
                ('EURUSD', 'USDJPY'): -0.30,
                ('GBPUSD', 'USDJPY'): -0.20,
                ('AUDUSD', 'NZDUSD'): 0.90,
                ('AUDUSD', 'USDCAD'): -0.70,
                ('BTCUSD', 'ETHUSD'): 0.85,
            }
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def get_correlation(self, symbol1: str, symbol2: str) -> float:
        """Get correlation between two symbols"""
        try:
            if symbol1 == symbol2:
                return 1.0
        
            key = (symbol1, symbol2)
            if key in self.correlation_matrix:
                return self.correlation_matrix[key]
        
            key = (symbol2, symbol1)
            if key in self.correlation_matrix:
                return self.correlation_matrix[key]
        
            return 0.0  # Unknown correlation
        except Exception as e:
            logger.error(f"Error in get_correlation: {e}")
            raise
    
    def check_portfolio_correlation(
        self,
        new_symbol: str,
        existing_positions: Dict[str, Any]
    ) -> Tuple[bool, float, str]:
        """
        Check if adding a new position would create too much correlation
        
        Returns:
            approved: Whether the position is approved
            max_corr: Maximum correlation with existing positions
            reason: Explanation
        """
        try:
            if not existing_positions:
                return True, 0.0, "No existing positions"
        
            max_corr = 0.0
            high_corr_symbol = None
        
            for symbol in existing_positions:
                corr = abs(self.get_correlation(new_symbol, symbol))
                if corr > max_corr:
                    max_corr = corr
                    high_corr_symbol = symbol
        
            if max_corr > self.max_correlation:
                return False, max_corr, f"High correlation ({max_corr:.2f}) with {high_corr_symbol}"
        
            return True, max_corr, "Correlation acceptable"
        except Exception as e:
            logger.error(f"Error in check_portfolio_correlation: {e}")
            raise


class DrawdownProtector:
    """
    Protect against excessive drawdowns
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
            self.max_drawdown = self.config.get('max_drawdown', 0.15)
        
            # Drawdown levels and actions
            self.levels = [
                (0.05, "reduce_size_25"),  # 5% DD: reduce size by 25%
                (0.08, "reduce_size_50"),  # 8% DD: reduce size by 50%
                (0.10, "reduce_size_75"),  # 10% DD: reduce size by 75%
                (0.12, "close_losers"),    # 12% DD: close losing positions
                (0.15, "stop_trading"),    # 15% DD: stop all trading
            ]
        
            # Tracking
            self.peak_equity = 0.0
            self.current_equity = 0.0
            self.current_drawdown = 0.0
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(self, equity: float):
        """Update equity and calculate drawdown"""
        try:
            self.current_equity = equity
        
            if equity > self.peak_equity:
                self.peak_equity = equity
        
            if self.peak_equity > 0:
                self.current_drawdown = (self.peak_equity - equity) / self.peak_equity
            else:
                self.current_drawdown = 0.0
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise
    
    def get_action(self) -> Tuple[str, float]:
        """
        Get recommended action based on current drawdown
        
        Returns:
            action: Recommended action
            size_multiplier: Position size multiplier
        """
        try:
            for level, action in self.levels:
                if self.current_drawdown >= level:
                    if action == "reduce_size_25":
                        return action, 0.75
                    elif action == "reduce_size_50":
                        return action, 0.50
                    elif action == "reduce_size_75":
                        return action, 0.25
                    elif action == "close_losers":
                        return action, 0.0
                    elif action == "stop_trading":
                        return action, 0.0
        
            return "normal", 1.0
        except Exception as e:
            logger.error(f"Error in get_action: {e}")
            raise
    
    def can_trade(self) -> Tuple[bool, str]:
        """Check if trading is allowed"""
        try:
            if self.current_drawdown >= self.max_drawdown:
                return False, f"Max drawdown reached: {self.current_drawdown:.2%}"
        
            return True, "Drawdown within limits"
        except Exception as e:
            logger.error(f"Error in can_trade: {e}")
            raise


class CircuitBreaker:
    """
    Circuit breaker for automatic trading halts
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
        
            # Thresholds
            self.max_daily_loss = self.config.get('max_daily_loss', 0.02)
            self.max_consecutive_losses = self.config.get('max_consecutive_losses', 5)
            self.max_hourly_trades = self.config.get('max_hourly_trades', 10)
        
            # State
            self.daily_pnl = 0.0
            self.consecutive_losses = 0
            self.hourly_trades = deque(maxlen=100)
            self.is_tripped = False
            self.trip_reason = ""
            self.trip_time: Optional[datetime] = None
            self.cooldown_minutes = self.config.get('cooldown_minutes', 60)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def record_trade(self, pnl: float, timestamp: datetime):
        """Record a trade result"""
        try:
            self.daily_pnl += pnl
            self.hourly_trades.append(timestamp)
        
            if pnl < 0:
                self.consecutive_losses += 1
            else:
                self.consecutive_losses = 0
        
            # Check triggers
            self._check_triggers()
        except Exception as e:
            logger.error(f"Error in record_trade: {e}")
            raise
    
    def _check_triggers(self):
        """Check if circuit breaker should trip"""
        # Daily loss limit
        try:
            if self.daily_pnl < -self.max_daily_loss:
                self._trip(f"Daily loss limit exceeded: {self.daily_pnl:.2%}")
                return
        
            # Consecutive losses
            if self.consecutive_losses >= self.max_consecutive_losses:
                self._trip(f"Consecutive losses: {self.consecutive_losses}")
                return
        
            # Hourly trade limit
            now = datetime.now()
            hour_ago = now - timedelta(hours=1)
            recent_trades = sum(1 for t in self.hourly_trades if t > hour_ago)
            if recent_trades >= self.max_hourly_trades:
                self._trip(f"Hourly trade limit exceeded: {recent_trades}")
                return
        except Exception as e:
            logger.error(f"Error in _check_triggers: {e}")
            raise
    
    def _trip(self, reason: str):
        """Trip the circuit breaker"""
        try:
            self.is_tripped = True
            self.trip_reason = reason
            self.trip_time = datetime.now()
            logger.warning(f"Circuit breaker tripped: {reason}")
        except Exception as e:
            logger.error(f"Error in _trip: {e}")
            raise
    
    def can_trade(self) -> Tuple[bool, str]:
        """Check if trading is allowed"""
        try:
            if not self.is_tripped:
                return True, "Circuit breaker not tripped"
        
            # Check cooldown
            if self.trip_time:
                elapsed = (datetime.now() - self.trip_time).total_seconds() / 60
                if elapsed >= self.cooldown_minutes:
                    self.reset()
                    return True, "Circuit breaker reset after cooldown"
        
            return False, f"Circuit breaker tripped: {self.trip_reason}"
        except Exception as e:
            logger.error(f"Error in can_trade: {e}")
            raise
    
    def reset(self):
        """Reset the circuit breaker"""
        try:
            self.is_tripped = False
            self.trip_reason = ""
            self.trip_time = None
            self.consecutive_losses = 0
            logger.info("Circuit breaker reset")
        except Exception as e:
            logger.error(f"Error in reset: {e}")
            raise
    
    def reset_daily(self):
        """Reset daily counters"""
        try:
            self.daily_pnl = 0.0
        except Exception as e:
            logger.error(f"Error in reset_daily: {e}")
            raise


class RiskFortress:
    """
    Main Risk Management System
    
    Coordinates all risk management components
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
        
            # Initialize components
            self.limits = RiskLimits(**self.config.get('limits', {}))
            self.position_sizer = PositionSizer(self.config.get('position_sizing', {}))
            self.correlation_manager = CorrelationManager(self.config.get('correlation', {}))
            self.drawdown_protector = DrawdownProtector(self.config.get('drawdown', {}))
            self.circuit_breaker = CircuitBreaker(self.config.get('circuit_breaker', {}))
        
            # Risk state
            self.current_risk_level = RiskLevel.MINIMAL
            self.total_exposure = 0.0
            self.daily_trades = 0
            self.daily_pnl = 0.0
        
            logger.info("Risk Fortress initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    async def check_signal(
        self,
        signal: Any,
        capital: float,
        available_capital: float,
        positions: Dict[str, Any],
        metrics: Any
    ) -> Tuple[bool, Any]:
        """
        Comprehensive risk check for a trading signal
        
        Returns:
            approved: Whether the signal is approved
            adjusted_signal: Signal with adjusted parameters
        """
        try:
            reasons = []
            warnings = []
            adjustments = {}
        
            # 1. Circuit breaker check
            can_trade, cb_reason = self.circuit_breaker.can_trade()
            if not can_trade:
                reasons.append(cb_reason)
                return False, signal
        
            # 2. Drawdown check
            self.drawdown_protector.update(capital)
            can_trade, dd_reason = self.drawdown_protector.can_trade()
            if not can_trade:
                reasons.append(dd_reason)
                return False, signal
        
            # 3. Position limit check
            if len(positions) >= self.limits.max_positions:
                reasons.append(f"Max positions ({self.limits.max_positions}) reached")
                return False, signal
        
            # 4. Correlation check
            corr_ok, max_corr, corr_reason = self.correlation_manager.check_portfolio_correlation(
                signal.symbol, positions
            )
            if not corr_ok:
                reasons.append(corr_reason)
                return False, signal
            elif max_corr > 0.5:
                warnings.append(f"Moderate correlation ({max_corr:.2f}) with existing positions")
        
            # 5. Risk/reward check
            if signal.risk_reward_ratio < self.limits.min_risk_reward:
                reasons.append(f"Risk/reward ({signal.risk_reward_ratio:.2f}) below minimum ({self.limits.min_risk_reward})")
                return False, signal
        
            # 6. Calculate position size
            volatility = signal.metadata.get('volatility', 0.5)
            position_size = self.position_sizer.calculate_size(
                capital=capital,
                entry_price=signal.entry_price,
                stop_loss=signal.stop_loss,
                volatility=volatility,
                confidence=signal.confidence
            )
        
            # 7. Apply drawdown adjustment
            dd_action, dd_multiplier = self.drawdown_protector.get_action()
            if dd_multiplier < 1.0:
                position_size *= dd_multiplier
                adjustments['drawdown_adjustment'] = dd_multiplier
                warnings.append(f"Position size reduced due to drawdown: {dd_action}")
        
            # 8. Cap position size
            if position_size > self.limits.max_position_size:
                position_size = self.limits.max_position_size
                adjustments['size_capped'] = True
        
            # 9. Check total exposure
            current_exposure = sum(
                p.quantity * p.entry_price / capital 
                for p in positions.values()
            )
            new_exposure = current_exposure + position_size
        
            if new_exposure > self.limits.max_portfolio_risk:
                # Reduce size to fit within limit
                available_risk = self.limits.max_portfolio_risk - current_exposure
                if available_risk <= 0:
                    reasons.append("Portfolio risk limit reached")
                    return False, signal
                position_size = min(position_size, available_risk)
                adjustments['exposure_limited'] = True
        
            # 10. Check available capital
            required_capital = position_size * signal.entry_price
            if required_capital > available_capital:
                position_size = available_capital / signal.entry_price * 0.95  # 5% buffer
                adjustments['capital_limited'] = True
        
            # 11. Final validation
            if position_size <= 0:
                reasons.append("Position size too small")
                return False, signal
        
            # 12. Calculate risk score
            risk_score = self._calculate_risk_score(
                position_size=position_size,
                volatility=volatility,
                correlation=max_corr,
                drawdown=self.drawdown_protector.current_drawdown,
                confidence=signal.confidence
            )
        
            # 13. Determine risk level
            if risk_score < 20:
                risk_level = RiskLevel.MINIMAL
            elif risk_score < 40:
                risk_level = RiskLevel.LOW
            elif risk_score < 60:
                risk_level = RiskLevel.MODERATE
            elif risk_score < 80:
                risk_level = RiskLevel.HIGH
            else:
                risk_level = RiskLevel.EXTREME
        
            # 14. Block extreme risk
            if risk_level == RiskLevel.EXTREME:
                reasons.append(f"Risk score too high: {risk_score:.0f}")
                return False, signal
        
            # 15. Update signal with adjusted values
            signal.position_size = position_size
            signal.metadata['risk_assessment'] = {
                'risk_score': risk_score,
                'risk_level': risk_level.name,
                'adjustments': adjustments,
                'warnings': warnings,
            }
        
            if warnings:
                logger.info(f"Signal approved with warnings: {warnings}")
        
            return True, signal
        except Exception as e:
            logger.error(f"Error in check_signal: {e}")
            raise
    
    def _calculate_risk_score(
        self,
        position_size: float,
        volatility: float,
        correlation: float,
        drawdown: float,
        confidence: float
    ) -> float:
        """Calculate overall risk score (0-100)"""
        # Position size component (0-25)
        try:
            size_score = (position_size / self.limits.max_position_size) * 25
        
            # Volatility component (0-25)
            vol_score = volatility * 25
        
            # Correlation component (0-20)
            corr_score = correlation * 20
        
            # Drawdown component (0-20)
            dd_score = (drawdown / self.limits.max_drawdown) * 20
        
            # Confidence inverse (0-10) - lower confidence = higher risk
            conf_score = (1 - confidence) * 10
        
            total = size_score + vol_score + corr_score + dd_score + conf_score
            return min(100, max(0, total))
        except Exception as e:
            logger.error(f"Error in _calculate_risk_score: {e}")
            raise
    
    def record_trade_result(self, pnl: float, pnl_percent: float):
        """Record trade result for risk tracking"""
        try:
            self.daily_pnl += pnl
            self.daily_trades += 1
        
            # Update components
            self.circuit_breaker.record_trade(pnl_percent, datetime.now())
            self.position_sizer.update_history(pnl_percent)
        except Exception as e:
            logger.error(f"Error in record_trade_result: {e}")
            raise
    
    def reset_daily(self):
        """Reset daily counters"""
        try:
            self.daily_pnl = 0.0
            self.daily_trades = 0
            self.circuit_breaker.reset_daily()
        except Exception as e:
            logger.error(f"Error in reset_daily: {e}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """Get current risk status"""
        return {
            'risk_level': self.current_risk_level.name,
            'total_exposure': self.total_exposure,
            'daily_pnl': self.daily_pnl,
            'daily_trades': self.daily_trades,
            'current_drawdown': self.drawdown_protector.current_drawdown,
            'circuit_breaker_tripped': self.circuit_breaker.is_tripped,
            'limits': self.limits.to_dict(),
        }
    
    def emergency_stop(self) -> str:
        """Trigger emergency stop"""
        try:
            self.circuit_breaker._trip("Emergency stop triggered")
            return "Emergency stop activated"
        except Exception as e:
            logger.error(f"Error in emergency_stop: {e}")
            raise
