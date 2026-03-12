"""
Risk-Adjusted Position Sizing - Improvement #4 (CRITICAL)
==========================================================

Dynamic Kelly Criterion sizing for optimal capital growth.

Features:
- Kelly Criterion calculator
- Volatility-adjusted sizing
- Correlation-aware portfolio sizing
- Drawdown-responsive reduction
- Win rate adaptive sizing
"""

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from collections import deque
import statistics
from typing import Set

logger = logging.getLogger(__name__)


class SizingMethod(Enum):
    """Position sizing methods"""
    FIXED_RISK = "fixed_risk"
    KELLY_CRITERION = "kelly_criterion"
    VOLATILITY_ADJUSTED = "volatility_adjusted"
    CORRELATION_AWARE = "correlation_aware"
    DRAWDOWN_RESPONSIVE = "drawdown_responsive"
    ADAPTIVE = "adaptive"


class RiskLevel(Enum):
    """Risk levels"""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    ULTRA_CONSERVATIVE = "ultra_conservative"


@dataclass
class PositionSize:
    """Position size calculation result"""
    symbol: str
    size: float  # Position size in lots/units
    risk_amount: float  # Dollar risk
    risk_percent: float  # Percentage of account
    method: SizingMethod
    confidence: float
    adjustments: Dict[str, float] = field(default_factory=dict)
    reasoning: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class TradeResult:
    """Trade result for statistics"""
    symbol: str
    direction: str
    entry_price: float
    exit_price: float
    size: float
    pnl: float
    pnl_percent: float
    win: bool
    timestamp: datetime = field(default_factory=datetime.now)


class KellyCriterionCalculator:
    """Kelly Criterion position sizing"""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.max_kelly_fraction = self.config.get('max_kelly_fraction', 0.25)  # Max 25% of Kelly
            self.min_trades_required = self.config.get('min_trades_required', 30)
            self.trade_history: deque = deque(maxlen=1000)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def add_trade(self, result: TradeResult):
        """Add trade result to history"""
        try:
            self.trade_history.append(result)
        except Exception as e:
            logger.error(f"Error in add_trade: {e}")
            raise
    
    def calculate_kelly(self, symbol: Optional[str] = None) -> Tuple[float, Dict[str, float]]:
        """
        Calculate Kelly Criterion fraction.
        Kelly % = W - [(1-W) / R]
        Where:
        - W = Win rate
        - R = Win/Loss ratio (average win / average loss)
        """
        try:
            trades = list(self.trade_history)
        
            if symbol:
                trades = [t for t in trades if t.symbol == symbol]
        
            if len(trades) < self.min_trades_required:
                return 0.01, {'reason': 'Insufficient trade history', 'trades': len(trades)}
        
            # Calculate win rate
            wins = [t for t in trades if t.win]
            win_rate = len(wins) / len(trades)
        
            # Calculate average win and loss
            win_amounts = [t.pnl for t in trades if t.win and t.pnl > 0]
            loss_amounts = [abs(t.pnl) for t in trades if not t.win and t.pnl < 0]
        
            if not win_amounts or not loss_amounts:
                return 0.01, {'reason': 'No wins or losses', 'win_rate': win_rate}
        
            avg_win = statistics.mean(win_amounts)
            avg_loss = statistics.mean(loss_amounts)
        
            if avg_loss == 0:
                return 0.01, {'reason': 'Zero average loss'}
        
            # Win/Loss ratio
            win_loss_ratio = avg_win / avg_loss
        
            # Kelly formula
            kelly = win_rate - ((1 - win_rate) / win_loss_ratio)
        
            # Apply fraction (never use full Kelly)
            kelly_fraction = kelly * self.max_kelly_fraction
        
            # Clamp to reasonable range
            kelly_fraction = max(0.005, min(kelly_fraction, 0.10))  # 0.5% to 10%
        
            stats = {
                'win_rate': win_rate,
                'win_loss_ratio': win_loss_ratio,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'full_kelly': kelly,
                'kelly_fraction': kelly_fraction,
                'trades_analyzed': len(trades)
            }
        
            return kelly_fraction, stats
        except Exception as e:
            logger.error(f"Error in calculate_kelly: {e}")
            raise
    
    def get_optimal_fraction(self, confidence: float = 1.0) -> float:
        """Get optimal Kelly fraction adjusted by confidence"""
        try:
            kelly, _ = self.calculate_kelly()
            return kelly * confidence
        except Exception as e:
            logger.error(f"Error in get_optimal_fraction: {e}")
            raise


class VolatilityAdjustedSizer:
    """Volatility-based position sizing"""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.target_volatility = self.config.get('target_volatility', 0.02)  # 2% daily
            self.atr_period = self.config.get('atr_period', 14)
            self.volatility_cache: Dict[str, float] = {}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update_volatility(self, symbol: str, atr: float, price: float):
        """Update volatility for symbol"""
        try:
            if price > 0:
                self.volatility_cache[symbol] = atr / price
        except Exception as e:
            logger.error(f"Error in update_volatility: {e}")
            raise
    
    def calculate_size(
        self,
        symbol: str,
        account_balance: float,
        entry_price: float,
        stop_loss: float,
        atr: Optional[float] = None
    ) -> Tuple[float, Dict[str, Any]]:
        """Calculate volatility-adjusted position size"""
        # Get volatility
        try:
            if atr and entry_price > 0:
                volatility = atr / entry_price
                self.volatility_cache[symbol] = volatility
            else:
                volatility = self.volatility_cache.get(symbol, 0.02)
        
            # Calculate volatility adjustment factor
            if volatility > 0:
                vol_adjustment = self.target_volatility / volatility
            else:
                vol_adjustment = 1.0
        
            # Clamp adjustment
            vol_adjustment = max(0.25, min(vol_adjustment, 2.0))
        
            # Calculate base risk
            risk_per_unit = abs(entry_price - stop_loss)
        
            if risk_per_unit == 0:
                return 0.0, {'error': 'Zero risk per unit'}
        
            # Base position size (2% risk)
            base_risk_percent = 0.02
            adjusted_risk_percent = base_risk_percent * vol_adjustment
        
            risk_amount = account_balance * adjusted_risk_percent
            position_size = risk_amount / risk_per_unit
        
            return position_size, {
                'volatility': volatility,
                'vol_adjustment': vol_adjustment,
                'base_risk_percent': base_risk_percent,
                'adjusted_risk_percent': adjusted_risk_percent,
                'risk_amount': risk_amount
            }
        except Exception as e:
            logger.error(f"Error in calculate_size: {e}")
            raise


class CorrelationAwareSizer:
    """Correlation-aware portfolio position sizing"""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.max_correlated_exposure = self.config.get('max_correlated_exposure', 0.06)  # 6%
            self.correlation_threshold = self.config.get('correlation_threshold', 0.7)
            self.correlation_matrix: Dict[Tuple[str, str], float] = {}
            self.current_positions: Dict[str, float] = {}  # symbol -> exposure
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update_correlation(self, symbol1: str, symbol2: str, correlation: float):
        """Update correlation between two symbols"""
        try:
            key = tuple(sorted([symbol1, symbol2]))
            self.correlation_matrix[key] = correlation
        except Exception as e:
            logger.error(f"Error in update_correlation: {e}")
            raise
    
    def update_position(self, symbol: str, exposure: float):
        """Update current position exposure"""
        try:
            if exposure == 0:
                self.current_positions.pop(symbol, None)
            else:
                self.current_positions[symbol] = exposure
        except Exception as e:
            logger.error(f"Error in update_position: {e}")
            raise
    
    def get_correlation(self, symbol1: str, symbol2: str) -> float:
        """Get correlation between two symbols"""
        try:
            if symbol1 == symbol2:
                return 1.0
            key = tuple(sorted([symbol1, symbol2]))
            return self.correlation_matrix.get(key, 0.0)
        except Exception as e:
            logger.error(f"Error in get_correlation: {e}")
            raise
    
    def calculate_correlated_exposure(self, symbol: str) -> float:
        """Calculate total correlated exposure for a symbol"""
        try:
            total_correlated = 0.0
        
            for pos_symbol, exposure in self.current_positions.items():
                if pos_symbol == symbol:
                    continue
            
                correlation = self.get_correlation(symbol, pos_symbol)
                if abs(correlation) >= self.correlation_threshold:
                    total_correlated += abs(exposure * correlation)
        
            return total_correlated
        except Exception as e:
            logger.error(f"Error in calculate_correlated_exposure: {e}")
            raise
    
    def adjust_for_correlation(
        self,
        symbol: str,
        proposed_size: float,
        account_balance: float,
        entry_price: float
    ) -> Tuple[float, Dict[str, Any]]:
        """Adjust position size based on correlation"""
        try:
            proposed_exposure = (proposed_size * entry_price) / account_balance
            correlated_exposure = self.calculate_correlated_exposure(symbol)
        
            # Calculate available exposure
            available_exposure = self.max_correlated_exposure - correlated_exposure
        
            if available_exposure <= 0:
                return 0.0, {
                    'reason': 'Max correlated exposure reached',
                    'correlated_exposure': correlated_exposure,
                    'max_allowed': self.max_correlated_exposure
                }
        
            # Adjust if proposed exceeds available
            if proposed_exposure > available_exposure:
                adjustment_factor = available_exposure / proposed_exposure
                adjusted_size = proposed_size * adjustment_factor
            else:
                adjustment_factor = 1.0
                adjusted_size = proposed_size
        
            return adjusted_size, {
                'proposed_exposure': proposed_exposure,
                'correlated_exposure': correlated_exposure,
                'available_exposure': available_exposure,
                'adjustment_factor': adjustment_factor
            }
        except Exception as e:
            logger.error(f"Error in adjust_for_correlation: {e}")
            raise


class DrawdownResponsiveSizer:
    """Drawdown-responsive position sizing"""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.drawdown_levels = self.config.get('drawdown_levels', {
                0.05: 0.75,   # 5% DD -> 75% size
                0.10: 0.50,   # 10% DD -> 50% size
                0.15: 0.25,   # 15% DD -> 25% size
                0.20: 0.10,   # 20% DD -> 10% size
            })
            self.recovery_bonus = self.config.get('recovery_bonus', 0.1)  # 10% bonus when recovering
            self.peak_equity = 0.0
            self.current_equity = 0.0
            self.equity_history: deque = deque(maxlen=100)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update_equity(self, equity: float):
        """Update current equity"""
        try:
            self.current_equity = equity
            self.equity_history.append({
                'equity': equity,
                'timestamp': datetime.now()
            })
        
            if equity > self.peak_equity:
                self.peak_equity = equity
        except Exception as e:
            logger.error(f"Error in update_equity: {e}")
            raise
    
    def get_drawdown(self) -> float:
        """Get current drawdown percentage"""
        try:
            if self.peak_equity <= 0:
                return 0.0
            return (self.peak_equity - self.current_equity) / self.peak_equity
        except Exception as e:
            logger.error(f"Error in get_drawdown: {e}")
            raise
    
    def is_recovering(self) -> bool:
        """Check if equity is recovering"""
        try:
            if len(self.equity_history) < 5:
                return False
        
            recent = [h['equity'] for h in list(self.equity_history)[-5:]]
            return all(recent[i] <= recent[i+1] for i in range(len(recent)-1))
        except Exception as e:
            logger.error(f"Error in is_recovering: {e}")
            raise
    
    def get_size_multiplier(self) -> Tuple[float, Dict[str, Any]]:
        """Get position size multiplier based on drawdown"""
        try:
            drawdown = self.get_drawdown()
        
            # Find applicable level
            multiplier = 1.0
            for dd_level, mult in sorted(self.drawdown_levels.items()):
                if drawdown >= dd_level:
                    multiplier = mult
        
            # Apply recovery bonus
            if self.is_recovering() and drawdown > 0.05:
                multiplier = min(multiplier + self.recovery_bonus, 1.0)
        
            return multiplier, {
                'drawdown': drawdown,
                'peak_equity': self.peak_equity,
                'current_equity': self.current_equity,
                'is_recovering': self.is_recovering(),
                'base_multiplier': multiplier
            }
        except Exception as e:
            logger.error(f"Error in get_size_multiplier: {e}")
            raise


class WinRateAdaptiveSizer:
    """Win rate adaptive position sizing"""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.lookback_trades = self.config.get('lookback_trades', 20)
            self.min_win_rate = self.config.get('min_win_rate', 0.40)
            self.target_win_rate = self.config.get('target_win_rate', 0.55)
            self.trade_history: deque = deque(maxlen=100)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def add_trade(self, result: TradeResult):
        """Add trade result"""
        try:
            self.trade_history.append(result)
        except Exception as e:
            logger.error(f"Error in add_trade: {e}")
            raise
    
    def get_recent_win_rate(self, symbol: Optional[str] = None) -> float:
        """Get recent win rate"""
        try:
            trades = list(self.trade_history)[-self.lookback_trades:]
        
            if symbol:
                trades = [t for t in trades if t.symbol == symbol]
        
            if not trades:
                return self.target_win_rate
        
            wins = sum(1 for t in trades if t.win)
            return wins / len(trades)
        except Exception as e:
            logger.error(f"Error in get_recent_win_rate: {e}")
            raise
    
    def get_size_multiplier(self, symbol: Optional[str] = None) -> Tuple[float, Dict[str, Any]]:
        """Get size multiplier based on recent win rate"""
        try:
            win_rate = self.get_recent_win_rate(symbol)
        
            if win_rate < self.min_win_rate:
                # Below minimum - reduce size significantly
                multiplier = 0.25
                status = "poor_performance"
            elif win_rate < self.target_win_rate:
                # Below target - reduce proportionally
                ratio = (win_rate - self.min_win_rate) / (self.target_win_rate - self.min_win_rate)
                multiplier = 0.5 + (ratio * 0.5)
                status = "below_target"
            elif win_rate > self.target_win_rate + 0.1:
                # Above target - slight increase
                multiplier = min(1.0 + (win_rate - self.target_win_rate - 0.1), 1.25)
                status = "above_target"
            else:
                multiplier = 1.0
                status = "on_target"
        
            return multiplier, {
                'win_rate': win_rate,
                'min_win_rate': self.min_win_rate,
                'target_win_rate': self.target_win_rate,
                'status': status,
                'trades_analyzed': min(len(self.trade_history), self.lookback_trades)
            }
        except Exception as e:
            logger.error(f"Error in get_size_multiplier: {e}")
            raise


class RiskAdjustedPositionSizer:
    """
    Master position sizing system.
    Combines all sizing methods for optimal risk management.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        
            # Initialize components
            self.kelly_calculator = KellyCriterionCalculator(self.config)
            self.volatility_sizer = VolatilityAdjustedSizer(self.config)
            self.correlation_sizer = CorrelationAwareSizer(self.config)
            self.drawdown_sizer = DrawdownResponsiveSizer(self.config)
            self.winrate_sizer = WinRateAdaptiveSizer(self.config)
        
            # Configuration
            self.base_risk_percent = self.config.get('base_risk_percent', 0.02)  # 2%
            self.max_risk_percent = self.config.get('max_risk_percent', 0.05)  # 5%
            self.min_risk_percent = self.config.get('min_risk_percent', 0.005)  # 0.5%
            self.max_position_percent = self.config.get('max_position_percent', 0.20)  # 20% of account
            self.risk_level = RiskLevel(self.config.get('risk_level', 'moderate'))
        
            # Risk level multipliers
            self.risk_multipliers = {
                RiskLevel.ULTRA_CONSERVATIVE: 0.5,
                RiskLevel.CONSERVATIVE: 0.75,
                RiskLevel.MODERATE: 1.0,
                RiskLevel.AGGRESSIVE: 1.5
            }
        
            # Statistics
            self.sizing_history: deque = deque(maxlen=1000)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def add_trade_result(self, result: TradeResult):
        """Add trade result to all components"""
        try:
            self.kelly_calculator.add_trade(result)
            self.winrate_sizer.add_trade(result)
        except Exception as e:
            logger.error(f"Error in add_trade_result: {e}")
            raise
    
    def update_equity(self, equity: float):
        """Update equity for drawdown tracking"""
        try:
            self.drawdown_sizer.update_equity(equity)
        except Exception as e:
            logger.error(f"Error in update_equity: {e}")
            raise
    
    def update_position(self, symbol: str, exposure: float):
        """Update position for correlation tracking"""
        try:
            self.correlation_sizer.update_position(symbol, exposure)
        except Exception as e:
            logger.error(f"Error in update_position: {e}")
            raise
    
    def update_volatility(self, symbol: str, atr: float, price: float):
        """Update volatility data"""
        try:
            self.volatility_sizer.update_volatility(symbol, atr, price)
        except Exception as e:
            logger.error(f"Error in update_volatility: {e}")
            raise
    
    def update_correlation(self, symbol1: str, symbol2: str, correlation: float):
        """Update correlation data"""
        try:
            self.correlation_sizer.update_correlation(symbol1, symbol2, correlation)
        except Exception as e:
            logger.error(f"Error in update_correlation: {e}")
            raise
    
    def calculate_position_size(
        self,
        symbol: str,
        account_balance: float,
        entry_price: float,
        stop_loss: float,
        signal_confidence: float = 1.0,
        atr: Optional[float] = None,
        method: SizingMethod = SizingMethod.ADAPTIVE
    ) -> PositionSize:
        """Calculate optimal position size"""
        try:
            adjustments = {}
            reasoning = []
        
            # Calculate risk per unit
            risk_per_unit = abs(entry_price - stop_loss)
        
            if risk_per_unit == 0:
                return PositionSize(
                    symbol=symbol,
                    size=0.0,
                    risk_amount=0.0,
                    risk_percent=0.0,
                    method=method,
                    confidence=0.0,
                    reasoning=["Zero risk per unit - invalid stop loss"]
                )
        
            # 1. Get base risk from Kelly Criterion
            kelly_fraction, kelly_stats = self.kelly_calculator.calculate_kelly(symbol)
            adjustments['kelly'] = kelly_fraction
            reasoning.append(f"Kelly fraction: {kelly_fraction:.2%}")
        
            # 2. Get volatility adjustment
            vol_size, vol_stats = self.volatility_sizer.calculate_size(
                symbol, account_balance, entry_price, stop_loss, atr
            )
            vol_adjustment = vol_stats.get('vol_adjustment', 1.0)
            adjustments['volatility'] = vol_adjustment
            reasoning.append(f"Volatility adjustment: {vol_adjustment:.2f}x")
        
            # 3. Get drawdown adjustment
            dd_multiplier, dd_stats = self.drawdown_sizer.get_size_multiplier()
            adjustments['drawdown'] = dd_multiplier
            reasoning.append(f"Drawdown multiplier: {dd_multiplier:.2f}x (DD: {dd_stats['drawdown']:.1%})")
        
            # 4. Get win rate adjustment
            wr_multiplier, wr_stats = self.winrate_sizer.get_size_multiplier(symbol)
            adjustments['win_rate'] = wr_multiplier
            reasoning.append(f"Win rate multiplier: {wr_multiplier:.2f}x (WR: {wr_stats['win_rate']:.1%})")
        
            # 5. Apply risk level multiplier
            risk_mult = self.risk_multipliers.get(self.risk_level, 1.0)
            adjustments['risk_level'] = risk_mult
            reasoning.append(f"Risk level ({self.risk_level.value}): {risk_mult:.2f}x")
        
            # 6. Apply signal confidence
            adjustments['confidence'] = signal_confidence
            reasoning.append(f"Signal confidence: {signal_confidence:.2f}x")
        
            # Calculate combined risk percentage
            if method == SizingMethod.KELLY_CRITERION:
                base_risk = kelly_fraction
            elif method == SizingMethod.VOLATILITY_ADJUSTED:
                base_risk = vol_stats.get('adjusted_risk_percent', self.base_risk_percent)
            elif method == SizingMethod.ADAPTIVE:
                # Combine all factors
                base_risk = self.base_risk_percent
                base_risk *= (1 + (kelly_fraction - 0.02) / 0.02)  # Kelly influence
                base_risk *= vol_adjustment
            else:
                base_risk = self.base_risk_percent
        
            # Apply all multipliers
            final_risk = base_risk * dd_multiplier * wr_multiplier * risk_mult * signal_confidence
        
            # Clamp to limits
            final_risk = max(self.min_risk_percent, min(final_risk, self.max_risk_percent))
        
            # Calculate position size
            risk_amount = account_balance * final_risk
            position_size = risk_amount / risk_per_unit
        
            # 7. Check correlation limits
            adj_size, corr_stats = self.correlation_sizer.adjust_for_correlation(
                symbol, position_size, account_balance, entry_price
            )
        
            if adj_size < position_size:
                adjustments['correlation'] = adj_size / position_size if position_size > 0 else 0
                reasoning.append(f"Correlation reduction: {adjustments['correlation']:.2f}x")
                position_size = adj_size
                risk_amount = position_size * risk_per_unit
                final_risk = risk_amount / account_balance
        
            # 8. Check max position size
            position_value = position_size * entry_price
            max_position_value = account_balance * self.max_position_percent
        
            if position_value > max_position_value:
                position_size = max_position_value / entry_price
                risk_amount = position_size * risk_per_unit
                final_risk = risk_amount / account_balance
                reasoning.append(f"Capped to max position: {self.max_position_percent:.0%}")
        
            # Create result
            result = PositionSize(
                symbol=symbol,
                size=position_size,
                risk_amount=risk_amount,
                risk_percent=final_risk,
                method=method,
                confidence=signal_confidence,
                adjustments=adjustments,
                reasoning=reasoning
            )
        
            # Record sizing
            self.sizing_history.append({
                'timestamp': datetime.now(),
                'symbol': symbol,
                'size': position_size,
                'risk_percent': final_risk,
                'method': method.value,
                'adjustments': adjustments
            })
        
            logger.info(f"Position size: {symbol} = {position_size:.4f} ({final_risk:.2%} risk)")
            return result
        except Exception as e:
            logger.error(f"Error in calculate_position_size: {e}")
            raise
    
    def calculate_lot_size(
        self,
        symbol: str,
        account_balance: float,
        entry_price: float,
        stop_loss: float,
        contract_size: float = 100000,  # Standard forex lot
        signal_confidence: float = 1.0,
        atr: Optional[float] = None
    ) -> Tuple[float, PositionSize]:
        """Calculate position size in lots"""
        try:
            position = self.calculate_position_size(
                symbol=symbol,
                account_balance=account_balance,
                entry_price=entry_price,
                stop_loss=stop_loss,
                signal_confidence=signal_confidence,
                atr=atr
            )
        
            # Convert to lots
            lots = position.size / contract_size
        
            # Round to standard lot sizes
            if lots >= 1.0:
                lots = round(lots, 1)  # 0.1 lot increments
            elif lots >= 0.1:
                lots = round(lots, 2)  # 0.01 lot increments
            else:
                lots = round(lots, 3)  # Micro lots
        
            return lots, position
        except Exception as e:
            logger.error(f"Error in calculate_lot_size: {e}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get position sizing statistics"""
        try:
            if not self.sizing_history:
                return {'total_calculations': 0}
        
            history = list(self.sizing_history)
        
            return {
                'total_calculations': len(history),
                'avg_risk_percent': statistics.mean(h['risk_percent'] for h in history),
                'max_risk_percent': max(h['risk_percent'] for h in history),
                'min_risk_percent': min(h['risk_percent'] for h in history),
                'current_drawdown': self.drawdown_sizer.get_drawdown(),
                'kelly_stats': self.kelly_calculator.calculate_kelly()[1],
                'recent_win_rate': self.winrate_sizer.get_recent_win_rate()
            }
        except Exception as e:
            logger.error(f"Error in get_statistics: {e}")
            raise
    
    def set_risk_level(self, level: RiskLevel):
        """Set risk level"""
        try:
            self.risk_level = level
            logger.info(f"Risk level set to: {level.value}")
        except Exception as e:
            logger.error(f"Error in set_risk_level: {e}")
            raise
