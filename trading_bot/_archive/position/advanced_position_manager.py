"""
Advanced Position Management System.

This module implements:
- Dynamic position sizing
- Pyramiding strategies
- Scale-in/Scale-out management
- Position hedging
- Portfolio rebalancing
- Risk-adjusted position management
- Correlation-aware sizing
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime
import logging
import numpy
import pandas

logger = logging.getLogger(__name__)


class PositionAction(Enum):
    """Position management actions."""
    OPEN = "open"
    ADD = "add"  # Pyramid/scale-in
    REDUCE = "reduce"  # Scale-out
    CLOSE = "close"
    HEDGE = "hedge"
    REVERSE = "reverse"
    HOLD = "hold"


class SizingMethod(Enum):
    """Position sizing methods."""
    FIXED_FRACTIONAL = "fixed_fractional"
    KELLY_CRITERION = "kelly_criterion"
    OPTIMAL_F = "optimal_f"
    VOLATILITY_ADJUSTED = "volatility_adjusted"
    RISK_PARITY = "risk_parity"
    EQUAL_WEIGHT = "equal_weight"
    ANTI_MARTINGALE = "anti_martingale"
    MARTINGALE = "martingale"


class PyramidStrategy(Enum):
    """Pyramiding strategies."""
    EQUAL_UNITS = "equal_units"
    DECREASING = "decreasing"
    INCREASING = "increasing"
    FIBONACCI = "fibonacci"
    VOLATILITY_SCALED = "volatility_scaled"


class ScaleOutStrategy(Enum):
    """Scale-out strategies."""
    FIXED_TARGETS = "fixed_targets"
    TRAILING = "trailing"
    TIME_BASED = "time_based"
    VOLATILITY_BASED = "volatility_based"
    FIBONACCI_EXTENSION = "fibonacci_extension"


@dataclass
class Position:
    """Represents a trading position."""
    symbol: str
    direction: str  # 'long' or 'short'
    entry_price: float
    current_price: float
    size: float
    units: int = 1  # Number of pyramid levels
    stop_loss: float = 0.0
    take_profit: float = 0.0
    entry_time: datetime = field(default_factory=datetime.now)
    last_update: datetime = field(default_factory=datetime.now)
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    max_favorable_excursion: float = 0.0
    max_adverse_excursion: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update_price(self, price: float) -> None:
        """Update position with new price."""
        self.current_price = price
        self.last_update = datetime.now()
        
        if self.direction == 'long':
            self.unrealized_pnl = (price - self.entry_price) * self.size
            excursion = (price - self.entry_price) / self.entry_price
        else:
            self.unrealized_pnl = (self.entry_price - price) * self.size
            excursion = (self.entry_price - price) / self.entry_price
        
        if excursion > 0:
            self.max_favorable_excursion = max(self.max_favorable_excursion, excursion)
        else:
            self.max_adverse_excursion = max(self.max_adverse_excursion, abs(excursion))


@dataclass
class PositionSizeResult:
    """Result of position size calculation."""
    size: float
    units: int
    risk_amount: float
    position_value: float
    leverage: float
    sizing_method: SizingMethod
    confidence: float
    adjustments: List[str] = field(default_factory=list)


@dataclass
class ScaleAction:
    """Scale-in or scale-out action."""
    action: PositionAction
    size: float
    price: float
    reason: str
    target_level: int
    remaining_size: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class PortfolioState:
    """Current portfolio state."""
    total_equity: float
    used_margin: float
    free_margin: float
    total_exposure: float
    positions: List[Position]
    correlation_matrix: Optional[np.ndarray] = None
    risk_budget_used: float = 0.0
    max_risk_budget: float = 0.1  # 10% of equity


class PositionSizer:
    """
    Advanced position sizing calculator.
    
    Implements multiple sizing methods with risk management.
    """
    
    def __init__(
        self,
        method: SizingMethod = SizingMethod.VOLATILITY_ADJUSTED,
        max_risk_per_trade: float = 0.02,
        max_portfolio_risk: float = 0.1,
        max_position_size: float = 0.25,
        min_position_size: float = 0.01
    ):
        self.method = method
        self.max_risk_per_trade = max_risk_per_trade
        self.max_portfolio_risk = max_portfolio_risk
        self.max_position_size = max_position_size
        self.min_position_size = min_position_size
        
    def calculate_fixed_fractional(
        self,
        equity: float,
        risk_per_trade: float,
        entry_price: float,
        stop_loss: float
    ) -> float:
        """Calculate position size using fixed fractional method."""
        risk_amount = equity * risk_per_trade
        price_risk = abs(entry_price - stop_loss)
        
        if price_risk <= 0:
            return 0.0
        
        size = risk_amount / price_risk
        return size
    
    def calculate_kelly_criterion(
        self,
        equity: float,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        kelly_fraction: float = 0.5  # Half Kelly for safety
    ) -> float:
        """Calculate position size using Kelly Criterion."""
        if avg_loss <= 0:
            return 0.0
        
        win_loss_ratio = avg_win / avg_loss
        kelly = (win_rate * win_loss_ratio - (1 - win_rate)) / win_loss_ratio
        
        # Apply fraction and limits
        kelly = max(0, min(kelly * kelly_fraction, self.max_position_size))
        
        return equity * kelly
    
    def calculate_optimal_f(
        self,
        equity: float,
        trade_results: List[float],
        fraction: float = 0.5
    ) -> float:
        """Calculate position size using Optimal F."""
        if not trade_results:
            return equity * self.min_position_size
        
        # Find the largest loss
        max_loss = abs(min(trade_results))
        if max_loss <= 0:
            return equity * self.min_position_size
        
        # Calculate optimal f through simulation
        best_f = 0.0
        best_twr = 0.0
        
        for f in np.arange(0.01, 1.0, 0.01):
            twr = 1.0
            for trade in trade_results:
                hpr = 1 + (f * trade / max_loss)
                if hpr <= 0:
                    twr = 0
                    break
                twr *= hpr
            
            if twr > best_twr:
                best_twr = twr
                best_f = f
        
        # Apply safety fraction
        optimal_f = best_f * fraction
        
        return equity * optimal_f / max_loss
    
    def calculate_volatility_adjusted(
        self,
        equity: float,
        entry_price: float,
        atr: float,
        atr_multiplier: float = 2.0,
        target_risk: float = 0.02
    ) -> float:
        """Calculate position size adjusted for volatility."""
        risk_amount = equity * target_risk
        price_risk = atr * atr_multiplier
        
        if price_risk <= 0:
            return 0.0
        
        size = risk_amount / price_risk
        return size
    
    def calculate_risk_parity(
        self,
        equity: float,
        volatilities: Dict[str, float],
        target_risk: float = 0.02
    ) -> Dict[str, float]:
        """Calculate position sizes for risk parity allocation."""
        if not volatilities:
            return {}
        
        # Inverse volatility weighting
        inv_vols = {k: 1/v for k, v in volatilities.items() if v > 0}
        total_inv_vol = sum(inv_vols.values())
        
        if total_inv_vol <= 0:
            return {}
        
        # Allocate based on inverse volatility
        sizes = {}
        for symbol, inv_vol in inv_vols.items():
            weight = inv_vol / total_inv_vol
            sizes[symbol] = equity * weight * target_risk / volatilities[symbol]
        
        return sizes
    
    def calculate_size(
        self,
        equity: float,
        entry_price: float,
        stop_loss: float,
        volatility: float = 0.0,
        win_rate: float = 0.5,
        avg_win: float = 1.0,
        avg_loss: float = 1.0,
        trade_history: Optional[List[float]] = None
    ) -> PositionSizeResult:
        """Calculate position size based on configured method."""
        adjustments = []
        
        if self.method == SizingMethod.FIXED_FRACTIONAL:
            size = self.calculate_fixed_fractional(
                equity, self.max_risk_per_trade, entry_price, stop_loss
            )
            
        elif self.method == SizingMethod.KELLY_CRITERION:
            size = self.calculate_kelly_criterion(
                equity, win_rate, avg_win, avg_loss
            )
            
        elif self.method == SizingMethod.OPTIMAL_F:
            size = self.calculate_optimal_f(
                equity, trade_history or []
            )
            
        elif self.method == SizingMethod.VOLATILITY_ADJUSTED:
            size = self.calculate_volatility_adjusted(
                equity, entry_price, volatility, target_risk=self.max_risk_per_trade
            )
            
        else:
            # Default to fixed fractional
            size = self.calculate_fixed_fractional(
                equity, self.max_risk_per_trade, entry_price, stop_loss
            )
        
        # Apply limits
        position_value = size * entry_price
        max_value = equity * self.max_position_size
        min_value = equity * self.min_position_size
        
        if position_value > max_value:
            size = max_value / entry_price
            adjustments.append(f"Reduced to max position size ({self.max_position_size*100}%)")
        
        if position_value < min_value:
            size = min_value / entry_price
            adjustments.append(f"Increased to min position size ({self.min_position_size*100}%)")
        
        # Calculate risk amount
        price_risk = abs(entry_price - stop_loss)
        risk_amount = size * price_risk
        
        # Calculate leverage
        leverage = (size * entry_price) / equity if equity > 0 else 0
        
        return PositionSizeResult(
            size=size,
            units=1,
            risk_amount=risk_amount,
            position_value=size * entry_price,
            leverage=leverage,
            sizing_method=self.method,
            confidence=0.8,
            adjustments=adjustments
        )


class PyramidManager:
    """
    Manages pyramiding (adding to winning positions).
    """
    
    def __init__(
        self,
        strategy: PyramidStrategy = PyramidStrategy.DECREASING,
        max_units: int = 4,
        unit_distance_atr: float = 1.0,
        initial_unit_fraction: float = 0.25
    ):
        self.strategy = strategy
        self.max_units = max_units
        self.unit_distance_atr = unit_distance_atr
        self.initial_unit_fraction = initial_unit_fraction
        
    def get_unit_sizes(self, total_size: float) -> List[float]:
        """Get size for each pyramid unit."""
        if self.strategy == PyramidStrategy.EQUAL_UNITS:
            unit_size = total_size / self.max_units
            return [unit_size] * self.max_units
            
        elif self.strategy == PyramidStrategy.DECREASING:
            # Each unit is smaller than the previous
            sizes = []
            remaining = total_size
            for i in range(self.max_units):
                unit = remaining * 0.5
                sizes.append(unit)
                remaining -= unit
            if remaining > 0:
                sizes[-1] += remaining
            return sizes
            
        elif self.strategy == PyramidStrategy.INCREASING:
            # Each unit is larger than the previous
            sizes = []
            base = total_size / (2 ** self.max_units - 1)
            for i in range(self.max_units):
                sizes.append(base * (2 ** i))
            return sizes
            
        elif self.strategy == PyramidStrategy.FIBONACCI:
            # Fibonacci-based sizing
            fib = [1, 1]
            for i in range(2, self.max_units):
                fib.append(fib[-1] + fib[-2])
            total_fib = sum(fib[:self.max_units])
            return [total_size * f / total_fib for f in fib[:self.max_units]]
            
        else:
            return [total_size / self.max_units] * self.max_units
    
    def should_add_unit(
        self,
        position: Position,
        current_price: float,
        atr: float
    ) -> Tuple[bool, Optional[ScaleAction]]:
        """Determine if we should add another pyramid unit."""
        if position.units >= self.max_units:
            return False, None
        
        # Calculate required price movement
        required_move = atr * self.unit_distance_atr * position.units
        
        if position.direction == 'long':
            target_price = position.entry_price + required_move
            should_add = current_price >= target_price
        else:
            target_price = position.entry_price - required_move
            should_add = current_price <= target_price
        
        if should_add:
            unit_sizes = self.get_unit_sizes(position.size * self.max_units)
            add_size = unit_sizes[position.units] if position.units < len(unit_sizes) else unit_sizes[-1]
            
            action = ScaleAction(
                action=PositionAction.ADD,
                size=add_size,
                price=current_price,
                reason=f"Pyramid unit {position.units + 1} triggered at {current_price:.4f}",
                target_level=position.units + 1,
                remaining_size=position.size + add_size
            )
            return True, action
        
        return False, None


class ScaleOutManager:
    """
    Manages scaling out of positions.
    """
    
    def __init__(
        self,
        strategy: ScaleOutStrategy = ScaleOutStrategy.FIXED_TARGETS,
        targets: Optional[List[float]] = None,  # As multiples of risk
        scale_percentages: Optional[List[float]] = None
    ):
        self.strategy = strategy
        self.targets = targets or [1.0, 2.0, 3.0]  # 1R, 2R, 3R
        self.scale_percentages = scale_percentages or [0.33, 0.33, 0.34]
        self.scaled_levels: Dict[str, List[int]] = {}
        
    def get_scale_targets(
        self,
        entry_price: float,
        stop_loss: float,
        direction: str
    ) -> List[float]:
        """Calculate scale-out target prices."""
        risk = abs(entry_price - stop_loss)
        
        targets = []
        for multiple in self.targets:
            if direction == 'long':
                target = entry_price + (risk * multiple)
            else:
                target = entry_price - (risk * multiple)
            targets.append(target)
        
        return targets
    
    def should_scale_out(
        self,
        position: Position,
        current_price: float
    ) -> Tuple[bool, Optional[ScaleAction]]:
        """Determine if we should scale out."""
        symbol = position.symbol
        if symbol not in self.scaled_levels:
            self.scaled_levels[symbol] = []
        
        targets = self.get_scale_targets(
            position.entry_price,
            position.stop_loss,
            position.direction
        )
        
        for i, target in enumerate(targets):
            if i in self.scaled_levels[symbol]:
                continue
            
            hit_target = (position.direction == 'long' and current_price >= target) or \
                        (position.direction == 'short' and current_price <= target)
            
            if hit_target:
                scale_pct = self.scale_percentages[i] if i < len(self.scale_percentages) else 0.25
                scale_size = position.size * scale_pct
                
                self.scaled_levels[symbol].append(i)
                
                action = ScaleAction(
                    action=PositionAction.REDUCE,
                    size=scale_size,
                    price=current_price,
                    reason=f"Scale-out target {i+1} hit at {current_price:.4f} ({self.targets[i]}R)",
                    target_level=i + 1,
                    remaining_size=position.size - scale_size
                )
                return True, action
        
        return False, None
    
    def reset_position(self, symbol: str) -> None:
        """Reset scale tracking for a position."""
        if symbol in self.scaled_levels:
            del self.scaled_levels[symbol]


class AdvancedPositionManager:
    """
    Complete advanced position management system.
    
    Features:
    - Dynamic position sizing
    - Pyramiding
    - Scale-out management
    - Portfolio-level risk management
    - Correlation-aware sizing
    - Hedging recommendations
    """
    
    def __init__(
        self,
        sizer: Optional[PositionSizer] = None,
        pyramid_manager: Optional[PyramidManager] = None,
        scale_out_manager: Optional[ScaleOutManager] = None,
        max_positions: int = 10,
        max_correlated_exposure: float = 0.3
    ):
        self.sizer = sizer or PositionSizer()
        self.pyramid_manager = pyramid_manager or PyramidManager()
        self.scale_out_manager = scale_out_manager or ScaleOutManager()
        self.max_positions = max_positions
        self.max_correlated_exposure = max_correlated_exposure
        
        self.positions: Dict[str, Position] = {}
        self.position_history: List[Position] = []
        self.action_history: List[ScaleAction] = []
        
    def calculate_position_size(
        self,
        symbol: str,
        equity: float,
        entry_price: float,
        stop_loss: float,
        volatility: float = 0.0,
        correlation_with_portfolio: float = 0.0
    ) -> PositionSizeResult:
        """Calculate position size with portfolio considerations."""
        # Get base size
        result = self.sizer.calculate_size(
            equity=equity,
            entry_price=entry_price,
            stop_loss=stop_loss,
            volatility=volatility
        )
        
        # Adjust for correlation
        if correlation_with_portfolio > 0.5:
            reduction = (correlation_with_portfolio - 0.5) * 0.5
            result.size *= (1 - reduction)
            result.adjustments.append(f"Reduced by {reduction*100:.1f}% due to correlation")
        
        # Check position count
        if len(self.positions) >= self.max_positions:
            result.size = 0
            result.adjustments.append("Max positions reached")
        
        return result
    
    def open_position(
        self,
        symbol: str,
        direction: str,
        entry_price: float,
        size: float,
        stop_loss: float,
        take_profit: float = 0.0
    ) -> Position:
        """Open a new position."""
        position = Position(
            symbol=symbol,
            direction=direction,
            entry_price=entry_price,
            current_price=entry_price,
            size=size,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        self.positions[symbol] = position
        
        action = ScaleAction(
            action=PositionAction.OPEN,
            size=size,
            price=entry_price,
            reason=f"Opened {direction} position",
            target_level=1,
            remaining_size=size
        )
        self.action_history.append(action)
        
        return position
    
    def update_position(
        self,
        symbol: str,
        current_price: float,
        atr: float = 0.0
    ) -> List[ScaleAction]:
        """Update position and check for scaling actions."""
        if symbol not in self.positions:
            return []
        
        position = self.positions[symbol]
        position.update_price(current_price)
        
        actions = []
        
        # Check for pyramid opportunity
        if atr > 0:
            should_add, add_action = self.pyramid_manager.should_add_unit(
                position, current_price, atr
            )
            if should_add and add_action:
                position.size += add_action.size
                position.units += 1
                actions.append(add_action)
                self.action_history.append(add_action)
        
        # Check for scale-out
        should_scale, scale_action = self.scale_out_manager.should_scale_out(
            position, current_price
        )
        if should_scale and scale_action:
            position.size -= scale_action.size
            position.realized_pnl += scale_action.size * (
                current_price - position.entry_price if position.direction == 'long'
                else position.entry_price - current_price
            )
            actions.append(scale_action)
            self.action_history.append(scale_action)
        
        return actions
    
    def close_position(
        self,
        symbol: str,
        exit_price: float,
        reason: str = "Manual close"
    ) -> Optional[Position]:
        """Close a position."""
        if symbol not in self.positions:
            return None
        
        position = self.positions[symbol]
        position.update_price(exit_price)
        
        # Calculate final P&L
        if position.direction == 'long':
            position.realized_pnl += (exit_price - position.entry_price) * position.size
        else:
            position.realized_pnl += (position.entry_price - exit_price) * position.size
        
        position.unrealized_pnl = 0
        
        action = ScaleAction(
            action=PositionAction.CLOSE,
            size=position.size,
            price=exit_price,
            reason=reason,
            target_level=0,
            remaining_size=0
        )
        self.action_history.append(action)
        
        # Move to history
        self.position_history.append(position)
        del self.positions[symbol]
        
        # Reset scale tracking
        self.scale_out_manager.reset_position(symbol)
        
        return position
    
    def get_hedge_recommendation(
        self,
        portfolio_beta: float,
        target_beta: float = 0.0
    ) -> Dict[str, Any]:
        """Get hedging recommendation."""
        beta_difference = portfolio_beta - target_beta
        
        if abs(beta_difference) < 0.1:
            return {
                'action': 'none',
                'reason': 'Portfolio beta within acceptable range'
            }
        
        if beta_difference > 0:
            return {
                'action': 'hedge_short',
                'beta_to_hedge': beta_difference,
                'reason': f'Portfolio too long, hedge {beta_difference:.2f} beta'
            }
        else:
            return {
                'action': 'hedge_long',
                'beta_to_hedge': abs(beta_difference),
                'reason': f'Portfolio too short, add {abs(beta_difference):.2f} beta'
            }
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get portfolio summary."""
        total_exposure = sum(p.size * p.current_price for p in self.positions.values())
        total_unrealized = sum(p.unrealized_pnl for p in self.positions.values())
        total_realized = sum(p.realized_pnl for p in self.position_history)
        
        return {
            'open_positions': len(self.positions),
            'total_exposure': total_exposure,
            'unrealized_pnl': total_unrealized,
            'realized_pnl': total_realized,
            'total_pnl': total_unrealized + total_realized,
            'positions': [
                {
                    'symbol': p.symbol,
                    'direction': p.direction,
                    'size': p.size,
                    'entry': p.entry_price,
                    'current': p.current_price,
                    'pnl': p.unrealized_pnl,
                    'units': p.units
                }
                for p in self.positions.values()
            ]
        }
    
    def rebalance_portfolio(
        self,
        target_weights: Dict[str, float],
        current_prices: Dict[str, float],
        equity: float
    ) -> List[Dict[str, Any]]:
        """Generate rebalancing orders."""
        orders = []
        
        # Calculate current weights
        total_value = sum(
            self.positions[s].size * current_prices.get(s, self.positions[s].current_price)
            for s in self.positions
        )
        
        current_weights = {}
        for symbol, position in self.positions.items():
            price = current_prices.get(symbol, position.current_price)
            current_weights[symbol] = (position.size * price) / total_value if total_value > 0 else 0
        
        # Calculate required changes
        for symbol, target_weight in target_weights.items():
            current_weight = current_weights.get(symbol, 0)
            weight_diff = target_weight - current_weight
            
            if abs(weight_diff) < 0.01:  # 1% threshold
                continue
            
            price = current_prices.get(symbol, 0)
            if price <= 0:
                continue
            
            value_change = weight_diff * equity
            size_change = value_change / price
            
            orders.append({
                'symbol': symbol,
                'action': 'buy' if size_change > 0 else 'sell',
                'size': abs(size_change),
                'current_weight': current_weight,
                'target_weight': target_weight
            })
        
        return orders


# Convenience functions
def calculate_position_size(
    equity: float,
    entry_price: float,
    stop_loss: float,
    risk_percent: float = 0.02
) -> float:
    """Quick position size calculation."""
    sizer = PositionSizer(max_risk_per_trade=risk_percent)
    result = sizer.calculate_size(equity, entry_price, stop_loss)
    return result.size


def get_pyramid_levels(
    total_size: float,
    strategy: str = "decreasing",
    max_units: int = 4
) -> List[float]:
    """Get pyramid unit sizes."""
    manager = PyramidManager(
        strategy=PyramidStrategy(strategy),
        max_units=max_units
    )
    return manager.get_unit_sizes(total_size)


def get_scale_out_targets(
    entry_price: float,
    stop_loss: float,
    direction: str,
    r_multiples: List[float] = None
) -> List[float]:
    """Get scale-out target prices."""
    manager = ScaleOutManager(targets=r_multiples or [1.0, 2.0, 3.0])
    return manager.get_scale_targets(entry_price, stop_loss, direction)
