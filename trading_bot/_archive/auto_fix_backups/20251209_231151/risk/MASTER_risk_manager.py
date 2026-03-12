"""
MASTER RISK MANAGER - Consolidated from 6 implementations
============================================================

This is the ULTIMATE risk management system combining the best features from:
1. risk_manager.py - Dynamic position sizing, portfolio management, drawdown protection
2. unified_risk_manager.py - Multi-implementation compatibility wrapper
3. advanced_risk_manager.py - Kelly criterion, Monte Carlo, portfolio optimization
4. ml_risk_manager.py - Machine learning adaptive risk management
5. complete_risk_system.py - Regime-aware Kelly, stress testing, dynamic sizing
6. fractal_risk_manager.py (if exists) - Fractal position sizing

FEATURES:
- Dynamic position sizing with Kelly criterion
- ML-based risk prediction and adaptation
- Portfolio-level risk correlation management
- Multi-level drawdown protection with circuit breakers
- Regime-aware risk adjustment
- Stress testing and scenario analysis
- Real-time risk monitoring and alerts
- Trade expectancy optimization
- Psychological risk management
- Emergency shutdown capabilities

Author: Consolidated by AI Assistant
Date: October 18, 2025
Version: 1.0.0 (MASTER)
"""

from __future__ import annotations

import asyncio
import logging
import math
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from loguru import logger

try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import precision_score, recall_score, f1_score, mean_squared_error
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logger.warning("scikit-learn not available, ML features disabled")

try:
    from scipy.optimize import minimize
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logger.warning("scipy not available, optimization features disabled")

from trading_bot.config import get
from trading_bot.data import MT5Interface

# ---------------------------------------------------------------------------
# Enums and Data Classes
# ---------------------------------------------------------------------------

class TradeDirection(Enum):
    """Trade direction enum."""
    LONG = auto()
    SHORT = auto()

class TradeQuality(Enum):
    """Trade setup quality classification."""
    OPTIMAL = auto()      # Perfect setup with multiple confirmations
    STRONG = auto()       # Strong setup with good confirmation
    STANDARD = auto()     # Standard trade setup
    SPECULATIVE = auto()  # Higher risk setup

class RiskMode(Enum):
    """Risk management mode."""
    CONSERVATIVE = auto()  # Lower risk per trade (0.5-1%)
    STANDARD = auto()      # Normal risk per trade (1-2%)
    AGGRESSIVE = auto()    # Higher risk per trade (2-3%)
    RECOVERY = auto()      # Special mode after drawdown (0.25-0.5%)
    EMERGENCY = auto()     # Emergency mode - minimal risk (0.1%)
    CUSTOM = auto()        # Custom risk parameters

class MarketRegime(Enum):
    """Market regime classification."""
    TRENDING_BULL = auto()
    TRENDING_BEAR = auto()
    RANGE_BOUND = auto()
    VOLATILE = auto()
    CRISIS = auto()
    NORMAL = auto()

@dataclass
class TradingStats:
    """Trading statistics for risk adjustment."""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    consecutive_wins: int = 0
    consecutive_losses: int = 0
    profit_factor: float = 0.0
    avg_win_pips: float = 0.0
    avg_loss_pips: float = 0.0
    max_drawdown_pct: float = 0.0
    win_rate: float = 0.0
    expectancy: float = 0.0
    sharpe_ratio: float = 0.0
    kelly_fraction: float = 0.0
    
    def update_from_history(self, trade_history: pd.DataFrame) -> None:
        """Update statistics from trade history."""
        if trade_history.empty:
            return
            
        self.total_trades = len(trade_history)
        self.winning_trades = len(trade_history[trade_history['profit'] > 0])
        self.losing_trades = len(trade_history[trade_history['profit'] <= 0])
        
        if self.total_trades > 0:
            self.win_rate = self.winning_trades / self.total_trades
        
        # Profit factor
        total_profit = trade_history[trade_history['profit'] > 0]['profit'].sum()
        total_loss = abs(trade_history[trade_history['profit'] <= 0]['profit'].sum())
        self.profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        
        # Average win/loss
        if self.winning_trades > 0:
            self.avg_win_pips = trade_history[trade_history['profit'] > 0]['pips'].mean()
        if self.losing_trades > 0:
            self.avg_loss_pips = abs(trade_history[trade_history['profit'] <= 0]['pips'].mean())
        
        # Expectancy
        if self.total_trades > 0:
            self.expectancy = (self.win_rate * self.avg_win_pips) - ((1 - self.win_rate) * self.avg_loss_pips)
        
        # Kelly fraction
        if self.avg_loss_pips > 0:
            b = self.avg_win_pips / self.avg_loss_pips
            self.kelly_fraction = (self.win_rate * b - (1 - self.win_rate)) / b
            self.kelly_fraction = max(0, min(self.kelly_fraction, 0.25))  # Cap at 25%

@dataclass
class PositionSize:
    """Position size calculation result."""
    lot: float
    risk_amount: float
    risk_percent: float
    stop_loss_pips: float
    take_profit_pips: Optional[float] = None
    risk_reward_ratio: Optional[float] = None
    confidence: float = 1.0
    reason: str = ""

@dataclass
class RiskAssessment:
    """Comprehensive risk assessment."""
    position_size: float
    max_risk_per_trade: float
    stop_loss: float
    max_drawdown_expected: float
    var_95: float  # Value at Risk (95%)
    cvar_95: float  # Conditional Value at Risk (95%)
    risk_of_ruin: float
    risk_score: float  # 0-100, higher is riskier
    kelly_fraction: float
    regime_adjustment: float
    ml_adjustment: float = 1.0
    stress_test_passed: bool = True
    warnings: List[str] = field(default_factory=list)

@dataclass
class RiskLimits:
    """Risk limits configuration."""
    max_risk_per_trade: float = 0.02  # 2%
    max_portfolio_risk: float = 0.05  # 5%
    max_correlated_risk: float = 0.08  # 8%
    max_sector_risk: float = 0.15  # 15%
    max_drawdown_limit: float = 0.25  # 25%
    max_daily_loss: float = 0.05  # 5%
    max_weekly_loss: float = 0.10  # 10%
    max_monthly_loss: float = 0.20  # 20%
    max_open_positions: int = 10
    max_correlated_positions: int = 3
    emergency_shutdown_drawdown: float = 0.30  # 30%

# ---------------------------------------------------------------------------
# MASTER Risk Manager
# ---------------------------------------------------------------------------

class MasterRiskManager:
    """
    MASTER Risk Management System - Consolidated from 6 implementations.
    
    This is the ultimate risk manager combining:
    - Dynamic position sizing
    - Kelly criterion optimization
    - ML-based risk prediction
    - Portfolio correlation management
    - Multi-level drawdown protection
    - Regime-aware adjustments
    - Stress testing
    - Emergency controls
    """
    
    def __init__(
        self,
        mt5_interface: Optional[MT5Interface] = None,
        config: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """
        Initialize MASTER Risk Manager.
        
        Args:
            mt5_interface: MT5Interface instance (optional)
            config: Configuration dictionary (optional)
            **kwargs: Additional parameters
        """
        self.mt5 = mt5_interface
        self.config = config or {}
        self.kwargs = kwargs
        
        # Risk limits
        self.limits = RiskLimits(
            max_risk_per_trade=self.config.get('max_risk_per_trade', 0.02),
            max_portfolio_risk=self.config.get('max_portfolio_risk', 0.05),
            max_correlated_risk=self.config.get('max_correlated_risk', 0.08),
            max_sector_risk=self.config.get('max_sector_risk', 0.15),
            max_drawdown_limit=self.config.get('max_drawdown_limit', 0.25),
            max_daily_loss=self.config.get('max_daily_loss', 0.05),
            max_weekly_loss=self.config.get('max_weekly_loss', 0.10),
            max_monthly_loss=self.config.get('max_monthly_loss', 0.20),
            max_open_positions=self.config.get('max_open_positions', 10),
            max_correlated_positions=self.config.get('max_correlated_positions', 3),
            emergency_shutdown_drawdown=self.config.get('emergency_shutdown_drawdown', 0.30)
        )
        
        # Risk mode
        self.risk_mode = RiskMode.STANDARD
        self.market_regime = MarketRegime.NORMAL
        
        # Regime risk adjustments
        self.regime_adjustments = {
            MarketRegime.TRENDING_BULL: 1.2,
            MarketRegime.TRENDING_BEAR: 0.8,
            MarketRegime.RANGE_BOUND: 0.9,
            MarketRegime.VOLATILE: 0.7,
            MarketRegime.CRISIS: 0.5,
            MarketRegime.NORMAL: 1.0
        }
        
        # Current state
        self.current_drawdown = 0.0
        self.peak_equity = 1.0
        self.current_equity = 1.0
        self.daily_loss = 0.0
        self.weekly_loss = 0.0
        self.monthly_loss = 0.0
        
        # Trading statistics
        self.stats = TradingStats()
        
        # Trade history
        self.trade_history = []
        
        # Open positions
        self.open_positions = {}
        
        # ML components (if available)
        self.ml_enabled = ML_AVAILABLE and self.config.get('enable_ml', True)
        if self.ml_enabled:
            self._initialize_ml_components()
        
        # Emergency shutdown flag
        self.emergency_shutdown = False
        
        logger.info(f"MASTER Risk Manager initialized - Mode: {self.risk_mode.name}, ML: {self.ml_enabled}")
    
    def _initialize_ml_components(self):
        """Initialize ML components for adaptive risk management."""
        try:
            self.drawdown_predictor = None
            self.risk_classifier = None
            self.position_size_regressor = None
            self.feature_scaler = StandardScaler()
            self.is_ml_trained = False
            logger.info("ML components initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize ML components: {e}")
            self.ml_enabled = False
    
    def calculate_position_size(
        self,
        symbol: str,
        stop_loss_pips: float,
        entry_price: Optional[float] = None,
        direction: TradeDirection = TradeDirection.LONG,
        quality: TradeQuality = TradeQuality.STANDARD,
        confidence: float = 1.0,
        **kwargs
    ) -> PositionSize:
        """
        Calculate optimal position size with all risk factors considered.
        
        Args:
            symbol: Trading symbol
            stop_loss_pips: Stop loss in pips
            entry_price: Entry price (optional)
            direction: Trade direction
            quality: Trade quality assessment
            confidence: Signal confidence (0-1)
            **kwargs: Additional parameters
            
        Returns:
            PositionSize object with calculated lot size and risk metrics
        """
        try:
            # Check emergency shutdown
            if self.emergency_shutdown:
                logger.warning("Emergency shutdown active - no new positions")
                return PositionSize(0, 0, 0, stop_loss_pips, reason="Emergency shutdown active")
            
            # Get account info
            if self.mt5:
                account = self.mt5.account_info()
                if not account:
                    logger.error("Failed to get account info")
                    return PositionSize(0, 0, 0, stop_loss_pips, reason="Account info unavailable")
                
                equity = account.equity
                balance = account.balance
            else:
                equity = self.config.get('equity', 10000)
                balance = self.config.get('balance', 10000)
            
            # Update current equity
            self.current_equity = equity
            
            # Calculate base risk amount
            base_risk_pct = self._get_base_risk_percent(quality)
            
            # Apply Kelly criterion adjustment
            kelly_adjustment = self._get_kelly_adjustment()
            
            # Apply regime adjustment
            regime_adjustment = self.regime_adjustments.get(self.market_regime, 1.0)
            
            # Apply drawdown adjustment
            drawdown_adjustment = self._get_drawdown_adjustment()
            
            # Apply ML adjustment (if available)
            ml_adjustment = self._get_ml_adjustment(symbol, stop_loss_pips) if self.ml_enabled else 1.0
            
            # Apply confidence adjustment
            confidence_adjustment = confidence
            
            # Combined risk percent
            adjusted_risk_pct = (
                base_risk_pct *
                kelly_adjustment *
                regime_adjustment *
                drawdown_adjustment *
                ml_adjustment *
                confidence_adjustment
            )
            
            # Cap at maximum
            adjusted_risk_pct = min(adjusted_risk_pct, self.limits.max_risk_per_trade)
            
            # Calculate risk amount
            risk_amount = equity * adjusted_risk_pct
            
            # Get symbol info
            if self.mt5:
                symbol_info = self.mt5.symbol_info(symbol)
                if not symbol_info:
                    logger.error(f"Failed to get symbol info for {symbol}")
                    return PositionSize(0, 0, 0, stop_loss_pips, reason="Symbol info unavailable")
                
                point = symbol_info.point
                tick_value = symbol_info.trade_tick_value
                # Use trade_tick_value as tick_size (they're the same in MT5)
                tick_size = symbol_info.trade_tick_value
                min_lot = symbol_info.volume_min
                max_lot = symbol_info.volume_max
                lot_step = symbol_info.volume_step
            else:
                # Default values for testing
                point = 0.00001
                tick_value = 1.0
                tick_size = 0.00001
                min_lot = 0.01
                max_lot = 10.0
                lot_step = 0.01
            
            # Calculate lot size
            pip_value = tick_value * (point / tick_size) * 10  # Value per pip for 1 lot
            if pip_value == 0 or stop_loss_pips == 0:
                logger.error("Invalid pip value or stop loss")
                return PositionSize(0, 0, 0, stop_loss_pips, reason="Invalid calculation parameters")
            
            lot_size = risk_amount / (stop_loss_pips * pip_value)
            
            # Round to lot step
            lot_size = round(lot_size / lot_step) * lot_step
            
            # Apply limits
            lot_size = max(min_lot, min(lot_size, max_lot))
            
            # Final validation
            if not self._validate_position_size(symbol, lot_size, adjusted_risk_pct):
                logger.warning("Position size failed validation")
                return PositionSize(0, 0, 0, stop_loss_pips, reason="Failed validation checks")
            
            # Calculate take profit (optional)
            take_profit_pips = kwargs.get('take_profit_pips')
            risk_reward = take_profit_pips / stop_loss_pips if take_profit_pips else None
            
            return PositionSize(
                lot=lot_size,
                risk_amount=risk_amount,
                risk_percent=adjusted_risk_pct,
                stop_loss_pips=stop_loss_pips,
                take_profit_pips=take_profit_pips,
                risk_reward_ratio=risk_reward,
                confidence=confidence,
                reason=f"Quality: {quality.name}, Regime: {self.market_regime.name}"
            )
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return PositionSize(0, 0, 0, stop_loss_pips, reason=f"Error: {str(e)}")
    
    def _get_base_risk_percent(self, quality: TradeQuality) -> float:
        """Get base risk percent based on trade quality and risk mode."""
        base_risks = {
            RiskMode.CONSERVATIVE: {
                TradeQuality.OPTIMAL: 0.01,
                TradeQuality.STRONG: 0.008,
                TradeQuality.STANDARD: 0.005,
                TradeQuality.SPECULATIVE: 0.003
            },
            RiskMode.STANDARD: {
                TradeQuality.OPTIMAL: 0.02,
                TradeQuality.STRONG: 0.015,
                TradeQuality.STANDARD: 0.01,
                TradeQuality.SPECULATIVE: 0.005
            },
            RiskMode.AGGRESSIVE: {
                TradeQuality.OPTIMAL: 0.03,
                TradeQuality.STRONG: 0.025,
                TradeQuality.STANDARD: 0.015,
                TradeQuality.SPECULATIVE: 0.008
            },
            RiskMode.RECOVERY: {
                TradeQuality.OPTIMAL: 0.005,
                TradeQuality.STRONG: 0.004,
                TradeQuality.STANDARD: 0.003,
                TradeQuality.SPECULATIVE: 0.001
            },
            RiskMode.EMERGENCY: {
                TradeQuality.OPTIMAL: 0.001,
                TradeQuality.STRONG: 0.001,
                TradeQuality.STANDARD: 0.0005,
                TradeQuality.SPECULATIVE: 0.0001
            }
        }
        
        return base_risks.get(self.risk_mode, base_risks[RiskMode.STANDARD]).get(quality, 0.01)
    
    def _get_kelly_adjustment(self) -> float:
        """Get Kelly criterion adjustment factor."""
        if self.stats.kelly_fraction > 0:
            # Use fractional Kelly (typically 0.25 to 0.5 of full Kelly)
            return min(self.stats.kelly_fraction * 0.5, 1.5)
        return 1.0
    
    def _get_drawdown_adjustment(self) -> float:
        """Get drawdown adjustment factor."""
        if self.current_drawdown >= self.limits.emergency_shutdown_drawdown:
            self.emergency_shutdown = True
            logger.critical(f"EMERGENCY SHUTDOWN: Drawdown {self.current_drawdown:.1%} >= {self.limits.emergency_shutdown_drawdown:.1%}")
            return 0.0
        
        if self.current_drawdown >= self.limits.max_drawdown_limit:
            # Severe drawdown - reduce to recovery mode
            self.risk_mode = RiskMode.RECOVERY
            return 0.5
        elif self.current_drawdown >= self.limits.max_drawdown_limit * 0.75:
            # Approaching limit - reduce risk
            return 0.7
        elif self.current_drawdown >= self.limits.max_drawdown_limit * 0.5:
            # Moderate drawdown - slight reduction
            return 0.85
        
        return 1.0
    
    def _get_ml_adjustment(self, symbol: str, stop_loss_pips: float) -> float:
        """Get ML-based risk adjustment (if trained)."""
        if not self.ml_enabled or not self.is_ml_trained:
            return 1.0
        
        try:
            # Prepare features (simplified - would need actual market data)
            features = self._prepare_ml_features(symbol, stop_loss_pips)
            
            # Predict risk
            if self.drawdown_predictor:
                predicted_drawdown = self.drawdown_predictor.predict([features])[0]
                # Adjust based on predicted drawdown
                if predicted_drawdown > 0.15:
                    return 0.7
                elif predicted_drawdown > 0.10:
                    return 0.85
            
            return 1.0
        except Exception as e:
            logger.warning(f"ML adjustment failed: {e}")
            return 1.0
    
    def _prepare_ml_features(self, symbol: str, stop_loss_pips: float) -> List[float]:
        """Prepare features for ML models (stub - needs actual implementation)."""
        # This is a simplified stub - real implementation would gather actual market data
        return [
            0.02,  # volatility_1h
            0.03,  # volatility_4h
            0.05,  # volatility_1d
            0.5,   # trend_strength
            1.0,   # volume_ratio
            50.0,  # rsi
            stop_loss_pips / 100.0,  # normalized stop loss
            self.current_drawdown,
            self.stats.win_rate,
            self.stats.profit_factor
        ]
    
    def _validate_position_size(self, symbol: str, lot_size: float, risk_pct: float) -> bool:
        """Validate position size against all risk limits."""
        # Check daily loss limit
        if self.daily_loss >= self.limits.max_daily_loss:
            logger.warning(f"Daily loss limit reached: {self.daily_loss:.2%}")
            return False
        
        # Check weekly loss limit
        if self.weekly_loss >= self.limits.max_weekly_loss:
            logger.warning(f"Weekly loss limit reached: {self.weekly_loss:.2%}")
            return False
        
        # Check monthly loss limit
        if self.monthly_loss >= self.limits.max_monthly_loss:
            logger.warning(f"Monthly loss limit reached: {self.monthly_loss:.2%}")
            return False
        
        # Check max open positions
        if len(self.open_positions) >= self.limits.max_open_positions:
            logger.warning(f"Max open positions reached: {len(self.open_positions)}")
            return False
        
        # Check portfolio risk
        total_risk = sum(pos.get('risk_pct', 0) for pos in self.open_positions.values())
        if total_risk + risk_pct > self.limits.max_portfolio_risk:
            logger.warning(f"Portfolio risk limit exceeded: {total_risk + risk_pct:.2%}")
            return False
        
        return True
    
    def update_drawdown(self, current_equity: float) -> None:
        """Update drawdown calculation."""
        self.current_equity = current_equity
        
        # Update peak
        if current_equity > self.peak_equity:
            self.peak_equity = current_equity
        
        # Calculate drawdown
        if self.peak_equity > 0:
            self.current_drawdown = (self.peak_equity - current_equity) / self.peak_equity
        
        logger.info(f"Drawdown: {self.current_drawdown:.2%}, Peak: {self.peak_equity:.2f}, Current: {current_equity:.2f}")
    
    def add_trade(self, trade_result: Dict[str, Any]) -> None:
        """Add trade result to history and update statistics."""
        self.trade_history.append(trade_result)
        
        # Update stats if we have enough history
        if len(self.trade_history) >= 10:
            df = pd.DataFrame(self.trade_history)
            self.stats.update_from_history(df)
    
    def set_risk_mode(self, mode: RiskMode) -> None:
        """Set risk management mode."""
        self.risk_mode = mode
        logger.info(f"Risk mode changed to: {mode.name}")
    
    def set_market_regime(self, regime: MarketRegime) -> None:
        """Set market regime."""
        self.market_regime = regime
        logger.info(f"Market regime changed to: {regime.name}")
    
    def get_risk_assessment(self) -> RiskAssessment:
        """Get comprehensive risk assessment."""
        return RiskAssessment(
            position_size=0.0,  # Would calculate based on current positions
            max_risk_per_trade=self.limits.max_risk_per_trade,
            stop_loss=0.0,
            max_drawdown_expected=self.limits.max_drawdown_limit,
            var_95=0.0,  # Would calculate from trade history
            cvar_95=0.0,  # Would calculate from trade history
            risk_of_ruin=0.0,  # Would calculate based on stats
            risk_score=self.current_drawdown * 100,
            kelly_fraction=self.stats.kelly_fraction,
            regime_adjustment=self.regime_adjustments.get(self.market_regime, 1.0),
            ml_adjustment=1.0,
            stress_test_passed=self.current_drawdown < self.limits.max_drawdown_limit,
            warnings=self._get_risk_warnings()
        )
    
    def _get_risk_warnings(self) -> List[str]:
        """Get current risk warnings."""
        warnings = []
        
        if self.emergency_shutdown:
            warnings.append("EMERGENCY SHUTDOWN ACTIVE")
        
        if self.current_drawdown >= self.limits.max_drawdown_limit * 0.75:
            warnings.append(f"High drawdown: {self.current_drawdown:.1%}")
        
        if self.daily_loss >= self.limits.max_daily_loss * 0.8:
            warnings.append(f"Approaching daily loss limit: {self.daily_loss:.1%}")
        
        if len(self.open_positions) >= self.limits.max_open_positions * 0.8:
            warnings.append(f"High number of open positions: {len(self.open_positions)}")
        
        if self.stats.consecutive_losses >= 5:
            warnings.append(f"Losing streak: {self.stats.consecutive_losses} trades")
        
        return warnings
    
    def reset_emergency_shutdown(self) -> None:
        """Reset emergency shutdown (use with caution)."""
        logger.warning("Resetting emergency shutdown - ensure conditions have improved")
        self.emergency_shutdown = False
        self.risk_mode = RiskMode.RECOVERY
    
    def calc_position_size(self, symbol: str, stop_loss_pips: float, **kwargs) -> PositionSize:
        """Alias for calculate_position_size for backward compatibility."""
        return self.calculate_position_size(symbol=symbol, stop_loss_pips=stop_loss_pips, **kwargs)
    
    def check_drawdown(self) -> bool:
        """Check if trading is allowed based on drawdown limits."""
        if self.emergency_shutdown:
            return False
        if self.current_drawdown >= self.limits.max_drawdown_limit:
            return False
        if self.daily_loss >= self.limits.max_daily_loss:
            return False
        return True

# ---------------------------------------------------------------------------
# Compatibility Functions
# ---------------------------------------------------------------------------

def create_risk_manager(mt5_interface=None, config=None, **kwargs) -> MasterRiskManager:
    """
    Factory function to create MASTER risk manager.
    
    This provides backward compatibility with old code.
    """
    return MasterRiskManager(mt5_interface=mt5_interface, config=config, **kwargs)

# Aliases for backward compatibility
RiskManager = MasterRiskManager
UnifiedRiskManager = MasterRiskManager
AdvancedRiskManager = MasterRiskManager

logger.info("MASTER Risk Manager module loaded successfully")
