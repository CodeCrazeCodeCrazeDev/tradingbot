"""
Advanced Position Management System
====================================

Comprehensive position management:
- Position aggregation across accounts
- Exposure calculation by currency/sector
- Hedging engine with suggestions
- Position scaling (scale-in/scale-out)
- Break-even calculation
- Position heat map
- Correlation exposure warnings
- Position aging tracker
- Performance attribution

Author: Elite Trading Bot
Version: 1.0.0
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from enum import Enum, auto
from collections import defaultdict
import threading
import numpy as np
import numpy

logger = logging.getLogger(__name__)


class PositionSide(Enum):
    """Position side"""
    LONG = "long"
    SHORT = "short"
    FLAT = "flat"


class ExposureType(Enum):
    """Exposure types"""
    CURRENCY = "currency"
    SECTOR = "sector"
    ASSET_CLASS = "asset_class"
    REGION = "region"
    STRATEGY = "strategy"


class HedgeType(Enum):
    """Hedge types"""
    DIRECT = "direct"           # Same asset, opposite direction
    CORRELATED = "correlated"   # Correlated asset
    OPTIONS = "options"         # Options hedge
    FUTURES = "futures"         # Futures hedge


class ScaleAction(Enum):
    """Scaling actions"""
    SCALE_IN = "scale_in"
    SCALE_OUT = "scale_out"
    PYRAMID = "pyramid"
    REDUCE = "reduce"


@dataclass
class Position:
    """Position data"""
    position_id: str
    account_id: str
    symbol: str
    side: PositionSide
    quantity: float
    entry_price: float
    current_price: float
    
    # P&L
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    
    # Costs
    commission: float = 0.0
    swap: float = 0.0
    
    # Risk
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    
    # Metadata
    strategy_id: str = ""
    currency: str = "USD"
    sector: str = ""
    asset_class: str = "forex"
    region: str = ""
    
    # Timing
    open_time: datetime = field(default_factory=datetime.now)
    last_update: datetime = field(default_factory=datetime.now)
    
    # Scaling history
    scale_history: List[Dict] = field(default_factory=list)
    
    @property
    def market_value(self) -> float:
        return self.quantity * self.current_price
    
    @property
    def cost_basis(self) -> float:
        return self.quantity * self.entry_price
    
    @property
    def return_pct(self) -> float:
        try:
            if self.cost_basis == 0:
                return 0.0
            return (self.unrealized_pnl / self.cost_basis) * 100
        except Exception as e:
            logger.error(f"Error in return_pct: {e}")
            raise
    
    @property
    def duration(self) -> timedelta:
        return datetime.now() - self.open_time
    
    @property
    def duration_hours(self) -> float:
        return self.duration.total_seconds() / 3600
    
    def to_dict(self) -> Dict:
        return {
            'position_id': self.position_id,
            'account_id': self.account_id,
            'symbol': self.symbol,
            'side': self.side.value,
            'quantity': self.quantity,
            'entry_price': self.entry_price,
            'current_price': self.current_price,
            'unrealized_pnl': self.unrealized_pnl,
            'realized_pnl': self.realized_pnl,
            'return_pct': self.return_pct,
            'market_value': self.market_value,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'duration_hours': self.duration_hours,
            'strategy_id': self.strategy_id
        }


@dataclass
class ExposureReport:
    """Exposure report"""
    exposure_type: ExposureType
    timestamp: datetime
    
    # Exposure by category
    exposures: Dict[str, float] = field(default_factory=dict)
    
    # Limits
    limits: Dict[str, float] = field(default_factory=dict)
    
    # Breaches
    breaches: List[str] = field(default_factory=list)
    
    # Net exposure
    net_long: float = 0.0
    net_short: float = 0.0
    gross_exposure: float = 0.0
    net_exposure: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            'type': self.exposure_type.value,
            'timestamp': self.timestamp.isoformat(),
            'exposures': self.exposures,
            'limits': self.limits,
            'breaches': self.breaches,
            'net_long': self.net_long,
            'net_short': self.net_short,
            'gross_exposure': self.gross_exposure,
            'net_exposure': self.net_exposure
        }


@dataclass
class HedgeSuggestion:
    """Hedge suggestion"""
    suggestion_id: str
    hedge_type: HedgeType
    timestamp: datetime
    
    # What to hedge
    target_position_id: str
    target_symbol: str
    target_exposure: float
    
    # Suggested hedge
    hedge_symbol: str
    hedge_side: PositionSide
    hedge_quantity: float
    hedge_ratio: float
    
    # Expected impact
    expected_reduction_pct: float
    estimated_cost: float
    
    # Confidence
    confidence: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            'suggestion_id': self.suggestion_id,
            'hedge_type': self.hedge_type.value,
            'target_symbol': self.target_symbol,
            'target_exposure': self.target_exposure,
            'hedge_symbol': self.hedge_symbol,
            'hedge_side': self.hedge_side.value,
            'hedge_quantity': self.hedge_quantity,
            'hedge_ratio': self.hedge_ratio,
            'expected_reduction_pct': self.expected_reduction_pct,
            'confidence': self.confidence
        }


@dataclass
class ScalePlan:
    """Position scaling plan"""
    plan_id: str
    position_id: str
    action: ScaleAction
    
    # Levels
    levels: List[Dict] = field(default_factory=list)  # [{price, quantity, triggered}]
    
    # Status
    levels_triggered: int = 0
    total_scaled: float = 0.0
    
    # Configuration
    max_position: float = 0.0
    min_position: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            'plan_id': self.plan_id,
            'position_id': self.position_id,
            'action': self.action.value,
            'levels': self.levels,
            'levels_triggered': self.levels_triggered,
            'total_scaled': self.total_scaled
        }


@dataclass
class BreakEvenInfo:
    """Break-even calculation"""
    position_id: str
    symbol: str
    
    # Prices
    entry_price: float
    current_price: float
    break_even_price: float
    
    # Distance
    distance_points: float
    distance_pct: float
    
    # Including costs
    total_costs: float
    adjusted_break_even: float
    
    def to_dict(self) -> Dict:
        return {
            'position_id': self.position_id,
            'symbol': self.symbol,
            'entry_price': self.entry_price,
            'current_price': self.current_price,
            'break_even_price': self.break_even_price,
            'distance_points': self.distance_points,
            'distance_pct': self.distance_pct,
            'total_costs': self.total_costs,
            'adjusted_break_even': self.adjusted_break_even
        }


@dataclass
class PositionHeatMapCell:
    """Heat map cell"""
    symbol: str
    pnl: float
    pnl_pct: float
    size: float
    duration_hours: float
    heat_score: float  # -1 to 1, negative = losing, positive = winning


class PositionAggregator:
    """
    Aggregates positions across multiple accounts
    """
    
    def __init__(self):
        try:
            self.positions: Dict[str, Position] = {}
            self.accounts: Set[str] = set()
            self._lock = threading.RLock()
        
            logger.info("PositionAggregator initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def add_position(self, position: Position):
        """Add or update a position"""
        try:
            with self._lock:
                self.positions[position.position_id] = position
                self.accounts.add(position.account_id)
        except Exception as e:
            logger.error(f"Error in add_position: {e}")
            raise
    
    def remove_position(self, position_id: str):
        """Remove a position"""
        try:
            with self._lock:
                if position_id in self.positions:
                    del self.positions[position_id]
        except Exception as e:
            logger.error(f"Error in remove_position: {e}")
            raise
    
    def get_all_positions(self) -> List[Position]:
        """Get all positions"""
        try:
            with self._lock:
                return list(self.positions.values())
        except Exception as e:
            logger.error(f"Error in get_all_positions: {e}")
            raise
    
    def get_positions_by_account(self, account_id: str) -> List[Position]:
        """Get positions for an account"""
        try:
            with self._lock:
                return [p for p in self.positions.values() if p.account_id == account_id]
        except Exception as e:
            logger.error(f"Error in get_positions_by_account: {e}")
            raise
    
    def get_positions_by_symbol(self, symbol: str) -> List[Position]:
        """Get positions for a symbol"""
        try:
            with self._lock:
                return [p for p in self.positions.values() if p.symbol == symbol]
        except Exception as e:
            logger.error(f"Error in get_positions_by_symbol: {e}")
            raise
    
    def get_aggregated_position(self, symbol: str) -> Dict:
        """Get aggregated position for a symbol across all accounts"""
        try:
            positions = self.get_positions_by_symbol(symbol)
        
            if not positions:
                return {'symbol': symbol, 'net_quantity': 0, 'positions': 0}
        
            long_qty = sum(p.quantity for p in positions if p.side == PositionSide.LONG)
            short_qty = sum(p.quantity for p in positions if p.side == PositionSide.SHORT)
        
            total_pnl = sum(p.unrealized_pnl for p in positions)
            avg_entry = sum(p.entry_price * p.quantity for p in positions) / sum(p.quantity for p in positions) if positions else 0
        
            return {
                'symbol': symbol,
                'long_quantity': long_qty,
                'short_quantity': short_qty,
                'net_quantity': long_qty - short_qty,
                'total_pnl': total_pnl,
                'avg_entry_price': avg_entry,
                'positions': len(positions),
                'accounts': list(set(p.account_id for p in positions))
            }
        except Exception as e:
            logger.error(f"Error in get_aggregated_position: {e}")
            raise
    
    def get_total_exposure(self) -> Dict:
        """Get total exposure across all positions"""
        try:
            with self._lock:
                long_exposure = sum(
                    p.market_value for p in self.positions.values()
                    if p.side == PositionSide.LONG
                )
                short_exposure = sum(
                    p.market_value for p in self.positions.values()
                    if p.side == PositionSide.SHORT
                )
            
                return {
                    'long_exposure': long_exposure,
                    'short_exposure': short_exposure,
                    'gross_exposure': long_exposure + short_exposure,
                    'net_exposure': long_exposure - short_exposure,
                    'total_positions': len(self.positions),
                    'total_accounts': len(self.accounts)
                }
        except Exception as e:
            logger.error(f"Error in get_total_exposure: {e}")
            raise


class ExposureCalculator:
    """
    Calculates exposure by various dimensions
    """
    
    def __init__(self):
        # Exposure limits
        try:
            self.limits: Dict[ExposureType, Dict[str, float]] = {
                ExposureType.CURRENCY: {},
                ExposureType.SECTOR: {},
                ExposureType.ASSET_CLASS: {},
                ExposureType.REGION: {},
                ExposureType.STRATEGY: {}
            }
        
            # Symbol mappings
            self.symbol_currency: Dict[str, str] = {}
            self.symbol_sector: Dict[str, str] = {}
            self.symbol_region: Dict[str, str] = {}
        
            logger.info("ExposureCalculator initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def set_limit(self, exposure_type: ExposureType, category: str, limit: float):
        """Set exposure limit"""
        try:
            self.limits[exposure_type][category] = limit
        except Exception as e:
            logger.error(f"Error in set_limit: {e}")
            raise
    
    def set_symbol_mapping(self, symbol: str, currency: str = "", sector: str = "", region: str = ""):
        """Set symbol mappings"""
        try:
            if currency:
                self.symbol_currency[symbol] = currency
            if sector:
                self.symbol_sector[symbol] = sector
            if region:
                self.symbol_region[symbol] = region
        except Exception as e:
            logger.error(f"Error in set_symbol_mapping: {e}")
            raise
    
    def calculate_exposure(
        self,
        positions: List[Position],
        exposure_type: ExposureType
    ) -> ExposureReport:
        """Calculate exposure by type"""
        try:
            exposures: Dict[str, float] = defaultdict(float)
        
            for position in positions:
                # Get category based on exposure type
                if exposure_type == ExposureType.CURRENCY:
                    category = position.currency or self.symbol_currency.get(position.symbol, "USD")
                elif exposure_type == ExposureType.SECTOR:
                    category = position.sector or self.symbol_sector.get(position.symbol, "Unknown")
                elif exposure_type == ExposureType.ASSET_CLASS:
                    category = position.asset_class
                elif exposure_type == ExposureType.REGION:
                    category = position.region or self.symbol_region.get(position.symbol, "Unknown")
                elif exposure_type == ExposureType.STRATEGY:
                    category = position.strategy_id or "default"
                else:
                    category = "Unknown"
            
                # Add exposure (positive for long, negative for short)
                if position.side == PositionSide.LONG:
                    exposures[category] += position.market_value
                else:
                    exposures[category] -= position.market_value
        
            # Calculate totals
            net_long = sum(v for v in exposures.values() if v > 0)
            net_short = abs(sum(v for v in exposures.values() if v < 0))
        
            # Check limits
            limits = self.limits.get(exposure_type, {})
            breaches = []
            for category, exposure in exposures.items():
                if category in limits and abs(exposure) > limits[category]:
                    breaches.append(f"{category}: {abs(exposure):.2f} > {limits[category]:.2f}")
        
            return ExposureReport(
                exposure_type=exposure_type,
                timestamp=datetime.now(),
                exposures=dict(exposures),
                limits=limits,
                breaches=breaches,
                net_long=net_long,
                net_short=net_short,
                gross_exposure=net_long + net_short,
                net_exposure=net_long - net_short
            )
        except Exception as e:
            logger.error(f"Error in calculate_exposure: {e}")
            raise
    
    def calculate_all_exposures(self, positions: List[Position]) -> Dict[ExposureType, ExposureReport]:
        """Calculate all exposure types"""
        return {
            etype: self.calculate_exposure(positions, etype)
            for etype in ExposureType
        }


class HedgingEngine:
    """
    Suggests hedges for positions
    """
    
    # Correlation matrix for common pairs
    DEFAULT_CORRELATIONS = {
        ('EURUSD', 'GBPUSD'): 0.85,
        ('EURUSD', 'USDCHF'): -0.90,
        ('EURUSD', 'USDJPY'): -0.30,
        ('GBPUSD', 'USDCHF'): -0.80,
        ('AUDUSD', 'NZDUSD'): 0.90,
        ('USDJPY', 'EURJPY'): 0.70,
    }
    
    def __init__(self):
        try:
            self.correlations: Dict[Tuple[str, str], float] = dict(self.DEFAULT_CORRELATIONS)
            self._next_id = 1
            self._lock = threading.RLock()
        
            logger.info("HedgingEngine initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _generate_id(self) -> str:
        try:
            with self._lock:
                suggestion_id = f"HEDGE_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self._next_id}"
                self._next_id += 1
                return suggestion_id
        except Exception as e:
            logger.error(f"Error in _generate_id: {e}")
            raise
    
    def set_correlation(self, symbol1: str, symbol2: str, correlation: float):
        """Set correlation between two symbols"""
        try:
            self.correlations[(symbol1, symbol2)] = correlation
            self.correlations[(symbol2, symbol1)] = correlation
        except Exception as e:
            logger.error(f"Error in set_correlation: {e}")
            raise
    
    def get_correlation(self, symbol1: str, symbol2: str) -> float:
        """Get correlation between two symbols"""
        try:
            if symbol1 == symbol2:
                return 1.0
            return self.correlations.get((symbol1, symbol2), 0.0)
        except Exception as e:
            logger.error(f"Error in get_correlation: {e}")
            raise
    
    def suggest_direct_hedge(self, position: Position) -> HedgeSuggestion:
        """Suggest a direct hedge (opposite position in same asset)"""
        try:
            hedge_side = PositionSide.SHORT if position.side == PositionSide.LONG else PositionSide.LONG
        
            return HedgeSuggestion(
                suggestion_id=self._generate_id(),
                hedge_type=HedgeType.DIRECT,
                timestamp=datetime.now(),
                target_position_id=position.position_id,
                target_symbol=position.symbol,
                target_exposure=position.market_value,
                hedge_symbol=position.symbol,
                hedge_side=hedge_side,
                hedge_quantity=position.quantity,
                hedge_ratio=1.0,
                expected_reduction_pct=100.0,
                estimated_cost=position.market_value * 0.001,  # Estimate spread cost
                confidence=1.0
            )
        except Exception as e:
            logger.error(f"Error in suggest_direct_hedge: {e}")
            raise
    
    def suggest_correlated_hedge(
        self,
        position: Position,
        available_symbols: List[str],
        min_correlation: float = 0.7
    ) -> List[HedgeSuggestion]:
        """Suggest hedges using correlated assets"""
        try:
            suggestions = []
        
            for symbol in available_symbols:
                if symbol == position.symbol:
                    continue
            
                correlation = self.get_correlation(position.symbol, symbol)
            
                if abs(correlation) >= min_correlation:
                    # Determine hedge direction based on correlation
                    if correlation > 0:
                        # Positive correlation: opposite direction
                        hedge_side = PositionSide.SHORT if position.side == PositionSide.LONG else PositionSide.LONG
                    else:
                        # Negative correlation: same direction
                        hedge_side = position.side
                
                    # Calculate hedge ratio
                    hedge_ratio = abs(correlation)
                    hedge_quantity = position.quantity * hedge_ratio
                
                    suggestions.append(HedgeSuggestion(
                        suggestion_id=self._generate_id(),
                        hedge_type=HedgeType.CORRELATED,
                        timestamp=datetime.now(),
                        target_position_id=position.position_id,
                        target_symbol=position.symbol,
                        target_exposure=position.market_value,
                        hedge_symbol=symbol,
                        hedge_side=hedge_side,
                        hedge_quantity=hedge_quantity,
                        hedge_ratio=hedge_ratio,
                        expected_reduction_pct=abs(correlation) * 100,
                        estimated_cost=hedge_quantity * position.current_price * 0.001,
                        confidence=abs(correlation)
                    ))
        
            # Sort by confidence
            suggestions.sort(key=lambda x: x.confidence, reverse=True)
        
            return suggestions
        except Exception as e:
            logger.error(f"Error in suggest_correlated_hedge: {e}")
            raise
    
    def analyze_portfolio_hedge(
        self,
        positions: List[Position]
    ) -> Dict[str, Any]:
        """Analyze overall portfolio hedging needs"""
        # Calculate net exposure by symbol
        try:
            net_exposures: Dict[str, float] = defaultdict(float)
        
            for position in positions:
                if position.side == PositionSide.LONG:
                    net_exposures[position.symbol] += position.market_value
                else:
                    net_exposures[position.symbol] -= position.market_value
        
            # Find largest exposures
            sorted_exposures = sorted(
                net_exposures.items(),
                key=lambda x: abs(x[1]),
                reverse=True
            )
        
            # Calculate correlation risk
            correlation_risk = 0.0
            symbols = list(net_exposures.keys())
            for i, sym1 in enumerate(symbols):
                for sym2 in symbols[i+1:]:
                    corr = self.get_correlation(sym1, sym2)
                    if corr > 0.5:
                        # Positions moving together increases risk
                        exp1 = net_exposures[sym1]
                        exp2 = net_exposures[sym2]
                        if (exp1 > 0 and exp2 > 0) or (exp1 < 0 and exp2 < 0):
                            correlation_risk += abs(corr * min(abs(exp1), abs(exp2)))
        
            return {
                'net_exposures': dict(net_exposures),
                'largest_exposures': sorted_exposures[:5],
                'correlation_risk': correlation_risk,
                'total_gross_exposure': sum(abs(v) for v in net_exposures.values()),
                'total_net_exposure': sum(net_exposures.values()),
                'hedge_needed': correlation_risk > 10000  # Threshold
            }
        except Exception as e:
            logger.error(f"Error in analyze_portfolio_hedge: {e}")
            raise


class PositionScalingManager:
    """
    Manages position scaling (scale-in/scale-out)
    """
    
    def __init__(self):
        try:
            self.scale_plans: Dict[str, ScalePlan] = {}
            self._next_id = 1
            self._lock = threading.RLock()
        
            logger.info("PositionScalingManager initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _generate_id(self) -> str:
        try:
            with self._lock:
                plan_id = f"SCALE_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self._next_id}"
                self._next_id += 1
                return plan_id
        except Exception as e:
            logger.error(f"Error in _generate_id: {e}")
            raise
    
    def create_scale_in_plan(
        self,
        position_id: str,
        entry_price: float,
        levels: List[Tuple[float, float]],  # [(price, quantity), ...]
        max_position: float
    ) -> ScalePlan:
        """Create a scale-in plan"""
        try:
            plan = ScalePlan(
                plan_id=self._generate_id(),
                position_id=position_id,
                action=ScaleAction.SCALE_IN,
                levels=[
                    {'price': price, 'quantity': qty, 'triggered': False}
                    for price, qty in levels
                ],
                max_position=max_position
            )
        
            self.scale_plans[plan.plan_id] = plan
            return plan
        except Exception as e:
            logger.error(f"Error in create_scale_in_plan: {e}")
            raise
    
    def create_scale_out_plan(
        self,
        position_id: str,
        current_price: float,
        levels: List[Tuple[float, float]],  # [(price, quantity), ...]
        min_position: float = 0.0
    ) -> ScalePlan:
        """Create a scale-out plan"""
        try:
            plan = ScalePlan(
                plan_id=self._generate_id(),
                position_id=position_id,
                action=ScaleAction.SCALE_OUT,
                levels=[
                    {'price': price, 'quantity': qty, 'triggered': False}
                    for price, qty in levels
                ],
                min_position=min_position
            )
        
            self.scale_plans[plan.plan_id] = plan
            return plan
        except Exception as e:
            logger.error(f"Error in create_scale_out_plan: {e}")
            raise
    
    def create_pyramid_plan(
        self,
        position_id: str,
        entry_price: float,
        profit_levels: List[float],  # Price levels to add
        add_quantity: float,
        max_position: float
    ) -> ScalePlan:
        """Create a pyramid plan (add on profit)"""
        try:
            levels = [(price, add_quantity) for price in profit_levels]
        
            plan = ScalePlan(
                plan_id=self._generate_id(),
                position_id=position_id,
                action=ScaleAction.PYRAMID,
                levels=[
                    {'price': price, 'quantity': qty, 'triggered': False}
                    for price, qty in levels
                ],
                max_position=max_position
            )
        
            self.scale_plans[plan.plan_id] = plan
            return plan
        except Exception as e:
            logger.error(f"Error in create_pyramid_plan: {e}")
            raise
    
    def check_triggers(
        self,
        plan_id: str,
        current_price: float,
        position_side: PositionSide
    ) -> List[Dict]:
        """Check if any scale levels are triggered"""
        try:
            plan = self.scale_plans.get(plan_id)
            if not plan:
                return []
        
            triggered = []
        
            for level in plan.levels:
                if level['triggered']:
                    continue
            
                trigger_price = level['price']
            
                # Check trigger based on action and side
                should_trigger = False
            
                if plan.action == ScaleAction.SCALE_IN:
                    # Scale in on pullbacks
                    if position_side == PositionSide.LONG:
                        should_trigger = current_price <= trigger_price
                    else:
                        should_trigger = current_price >= trigger_price
                    
                elif plan.action in [ScaleAction.SCALE_OUT, ScaleAction.PYRAMID]:
                    # Scale out / pyramid on profit
                    if position_side == PositionSide.LONG:
                        should_trigger = current_price >= trigger_price
                    else:
                        should_trigger = current_price <= trigger_price
            
                if should_trigger:
                    level['triggered'] = True
                    plan.levels_triggered += 1
                    plan.total_scaled += level['quantity']
                    triggered.append(level)
        
            return triggered
        except Exception as e:
            logger.error(f"Error in check_triggers: {e}")
            raise
    
    def get_plan(self, plan_id: str) -> Optional[ScalePlan]:
        """Get a scale plan"""
        return self.scale_plans.get(plan_id)
    
    def get_plans_for_position(self, position_id: str) -> List[ScalePlan]:
        """Get all plans for a position"""
        return [p for p in self.scale_plans.values() if p.position_id == position_id]


class BreakEvenCalculator:
    """
    Calculates break-even prices
    """
    
    def __init__(self):
        # Pip values for common pairs
        try:
            self.pip_values = {
                'EURUSD': 10.0, 'GBPUSD': 10.0, 'AUDUSD': 10.0,
                'USDJPY': 9.0, 'USDCHF': 10.0, 'USDCAD': 7.5
            }
        
            logger.info("BreakEvenCalculator initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def calculate(self, position: Position) -> BreakEvenInfo:
        """Calculate break-even for a position"""
        # Total costs
        try:
            total_costs = position.commission + abs(position.swap)
        
            # Cost per unit
            cost_per_unit = total_costs / position.quantity if position.quantity > 0 else 0
        
            # Break-even price
            if position.side == PositionSide.LONG:
                break_even = position.entry_price + cost_per_unit
                adjusted_be = break_even
            else:
                break_even = position.entry_price - cost_per_unit
                adjusted_be = break_even
        
            # Distance
            distance_points = abs(position.current_price - break_even)
            distance_pct = (distance_points / break_even) * 100 if break_even > 0 else 0
        
            return BreakEvenInfo(
                position_id=position.position_id,
                symbol=position.symbol,
                entry_price=position.entry_price,
                current_price=position.current_price,
                break_even_price=break_even,
                distance_points=distance_points,
                distance_pct=distance_pct,
                total_costs=total_costs,
                adjusted_break_even=adjusted_be
            )
        except Exception as e:
            logger.error(f"Error in calculate: {e}")
            raise
    
    def calculate_multi_entry_be(
        self,
        entries: List[Tuple[float, float]]  # [(price, quantity), ...]
    ) -> float:
        """Calculate break-even for multiple entries"""
        try:
            total_value = sum(price * qty for price, qty in entries)
            total_qty = sum(qty for _, qty in entries)
        
            if total_qty == 0:
                return 0.0
        
            return total_value / total_qty
        except Exception as e:
            logger.error(f"Error in calculate_multi_entry_be: {e}")
            raise


class PositionHeatMap:
    """
    Generates position heat map
    """
    
    def __init__(self):
        try:
            logger.info("PositionHeatMap initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def generate(self, positions: List[Position]) -> List[PositionHeatMapCell]:
        """Generate heat map cells"""
        try:
            cells = []
        
            # Find max values for normalization
            max_pnl = max(abs(p.unrealized_pnl) for p in positions) if positions else 1
            max_size = max(p.market_value for p in positions) if positions else 1
        
            for position in positions:
                # Calculate heat score (-1 to 1)
                pnl_score = position.unrealized_pnl / max_pnl if max_pnl > 0 else 0
            
                # Adjust for duration (older losing positions are "hotter")
                duration_factor = min(position.duration_hours / 24, 1.0)  # Cap at 1 day
            
                if pnl_score < 0:
                    # Losing position - heat increases with time
                    heat_score = pnl_score * (1 + duration_factor * 0.5)
                else:
                    # Winning position - heat decreases with time (lock in profits)
                    heat_score = pnl_score * (1 - duration_factor * 0.3)
            
                cells.append(PositionHeatMapCell(
                    symbol=position.symbol,
                    pnl=position.unrealized_pnl,
                    pnl_pct=position.return_pct,
                    size=position.market_value,
                    duration_hours=position.duration_hours,
                    heat_score=max(-1, min(1, heat_score))
                ))
        
            # Sort by heat score (most concerning first)
            cells.sort(key=lambda x: x.heat_score)
        
            return cells
        except Exception as e:
            logger.error(f"Error in generate: {e}")
            raise


class CorrelationExposureMonitor:
    """
    Monitors correlation exposure and warns of concentrated risk
    """
    
    def __init__(self, warning_threshold: float = 0.7):
        try:
            self.warning_threshold = warning_threshold
            self.correlations: Dict[Tuple[str, str], float] = {}
        
            logger.info("CorrelationExposureMonitor initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def set_correlation(self, symbol1: str, symbol2: str, correlation: float):
        """Set correlation"""
        try:
            self.correlations[(symbol1, symbol2)] = correlation
            self.correlations[(symbol2, symbol1)] = correlation
        except Exception as e:
            logger.error(f"Error in set_correlation: {e}")
            raise
    
    def analyze(self, positions: List[Position]) -> Dict[str, Any]:
        """Analyze correlation exposure"""
        try:
            warnings = []
            high_correlation_pairs = []
        
            symbols = list(set(p.symbol for p in positions))
        
            for i, sym1 in enumerate(symbols):
                for sym2 in symbols[i+1:]:
                    corr = self.correlations.get((sym1, sym2), 0)
                
                    if abs(corr) >= self.warning_threshold:
                        # Get positions for each symbol
                        pos1 = [p for p in positions if p.symbol == sym1]
                        pos2 = [p for p in positions if p.symbol == sym2]
                    
                        exp1 = sum(p.market_value * (1 if p.side == PositionSide.LONG else -1) for p in pos1)
                        exp2 = sum(p.market_value * (1 if p.side == PositionSide.LONG else -1) for p in pos2)
                    
                        # Check if exposures are in same direction with positive correlation
                        # or opposite direction with negative correlation
                        if (corr > 0 and exp1 * exp2 > 0) or (corr < 0 and exp1 * exp2 < 0):
                            risk_amount = min(abs(exp1), abs(exp2)) * abs(corr)
                        
                            warnings.append({
                                'symbols': (sym1, sym2),
                                'correlation': corr,
                                'exposure1': exp1,
                                'exposure2': exp2,
                                'risk_amount': risk_amount,
                                'message': f"High correlation ({corr:.2f}) between {sym1} and {sym2}"
                            })
                        
                            high_correlation_pairs.append((sym1, sym2, corr))
        
            return {
                'warnings': warnings,
                'high_correlation_pairs': high_correlation_pairs,
                'total_correlation_risk': sum(w['risk_amount'] for w in warnings),
                'warning_count': len(warnings)
            }
        except Exception as e:
            logger.error(f"Error in analyze: {e}")
            raise


class PositionAgingTracker:
    """
    Tracks position age and flags stale positions
    """
    
    def __init__(
        self,
        warning_hours: float = 24,
        critical_hours: float = 72
    ):
        try:
            self.warning_hours = warning_hours
            self.critical_hours = critical_hours
        
            logger.info("PositionAgingTracker initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def analyze(self, positions: List[Position]) -> Dict[str, Any]:
        """Analyze position ages"""
        try:
            fresh = []      # < warning_hours
            aging = []      # warning_hours to critical_hours
            stale = []      # > critical_hours
        
            for position in positions:
                hours = position.duration_hours
            
                if hours < self.warning_hours:
                    fresh.append(position)
                elif hours < self.critical_hours:
                    aging.append(position)
                else:
                    stale.append(position)
        
            return {
                'fresh_count': len(fresh),
                'aging_count': len(aging),
                'stale_count': len(stale),
                'fresh_positions': [p.position_id for p in fresh],
                'aging_positions': [p.position_id for p in aging],
                'stale_positions': [p.position_id for p in stale],
                'avg_age_hours': np.mean([p.duration_hours for p in positions]) if positions else 0,
                'max_age_hours': max(p.duration_hours for p in positions) if positions else 0,
                'stale_exposure': sum(p.market_value for p in stale)
            }
        except Exception as e:
            logger.error(f"Error in analyze: {e}")
            raise


class PerformanceAttribution:
    """
    Attributes performance to positions
    """
    
    def __init__(self):
        try:
            logger.info("PerformanceAttribution initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def calculate(self, positions: List[Position]) -> Dict[str, Any]:
        """Calculate performance attribution"""
        # By symbol
        try:
            by_symbol: Dict[str, float] = defaultdict(float)
            for p in positions:
                by_symbol[p.symbol] += p.unrealized_pnl + p.realized_pnl
        
            # By strategy
            by_strategy: Dict[str, float] = defaultdict(float)
            for p in positions:
                by_strategy[p.strategy_id or 'default'] += p.unrealized_pnl + p.realized_pnl
        
            # By side
            long_pnl = sum(p.unrealized_pnl + p.realized_pnl for p in positions if p.side == PositionSide.LONG)
            short_pnl = sum(p.unrealized_pnl + p.realized_pnl for p in positions if p.side == PositionSide.SHORT)
        
            # By duration
            short_term = sum(p.unrealized_pnl for p in positions if p.duration_hours < 24)
            medium_term = sum(p.unrealized_pnl for p in positions if 24 <= p.duration_hours < 168)
            long_term = sum(p.unrealized_pnl for p in positions if p.duration_hours >= 168)
        
            total_pnl = sum(p.unrealized_pnl + p.realized_pnl for p in positions)
        
            return {
                'total_pnl': total_pnl,
                'by_symbol': dict(by_symbol),
                'by_strategy': dict(by_strategy),
                'long_pnl': long_pnl,
                'short_pnl': short_pnl,
                'short_term_pnl': short_term,
                'medium_term_pnl': medium_term,
                'long_term_pnl': long_term,
                'best_performer': max(by_symbol.items(), key=lambda x: x[1]) if by_symbol else None,
                'worst_performer': min(by_symbol.items(), key=lambda x: x[1]) if by_symbol else None
            }
        except Exception as e:
            logger.error(f"Error in calculate: {e}")
            raise


class AdvancedPositionManager:
    """
    Complete advanced position management system
    """
    
    def __init__(self):
        try:
            self.aggregator = PositionAggregator()
            self.exposure_calculator = ExposureCalculator()
            self.hedging_engine = HedgingEngine()
            self.scaling_manager = PositionScalingManager()
            self.break_even_calculator = BreakEvenCalculator()
            self.heat_map = PositionHeatMap()
            self.correlation_monitor = CorrelationExposureMonitor()
            self.aging_tracker = PositionAgingTracker()
            self.performance_attribution = PerformanceAttribution()
        
            logger.info("AdvancedPositionManager initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def add_position(self, position: Position):
        """Add a position"""
        try:
            self.aggregator.add_position(position)
        except Exception as e:
            logger.error(f"Error in add_position: {e}")
            raise
    
    def remove_position(self, position_id: str):
        """Remove a position"""
        try:
            self.aggregator.remove_position(position_id)
        except Exception as e:
            logger.error(f"Error in remove_position: {e}")
            raise
    
    def get_full_analysis(self) -> Dict[str, Any]:
        """Get complete position analysis"""
        try:
            positions = self.aggregator.get_all_positions()
        
            return {
                'positions': [p.to_dict() for p in positions],
                'total_exposure': self.aggregator.get_total_exposure(),
                'exposures': {
                    etype.value: self.exposure_calculator.calculate_exposure(positions, etype).to_dict()
                    for etype in ExposureType
                },
                'heat_map': [
                    {'symbol': c.symbol, 'heat_score': c.heat_score, 'pnl': c.pnl}
                    for c in self.heat_map.generate(positions)
                ],
                'correlation_analysis': self.correlation_monitor.analyze(positions),
                'aging_analysis': self.aging_tracker.analyze(positions),
                'performance_attribution': self.performance_attribution.calculate(positions),
                'hedge_analysis': self.hedging_engine.analyze_portfolio_hedge(positions)
            }
        except Exception as e:
            logger.error(f"Error in get_full_analysis: {e}")
            raise


# Singleton instance
_position_manager: Optional[AdvancedPositionManager] = None


def get_position_manager() -> AdvancedPositionManager:
    """Get or create position manager singleton"""
    try:
        global _position_manager
        if _position_manager is None:
            _position_manager = AdvancedPositionManager()
        return _position_manager
    except Exception as e:
        logger.error(f"Error in get_position_manager: {e}")
        raise


# Export
__all__ = [
    'AdvancedPositionManager',
    'PositionAggregator',
    'ExposureCalculator',
    'HedgingEngine',
    'PositionScalingManager',
    'BreakEvenCalculator',
    'PositionHeatMap',
    'CorrelationExposureMonitor',
    'PositionAgingTracker',
    'PerformanceAttribution',
    'Position',
    'PositionSide',
    'ExposureType',
    'ExposureReport',
    'HedgeSuggestion',
    'HedgeType',
    'ScalePlan',
    'ScaleAction',
    'BreakEvenInfo',
    'PositionHeatMapCell',
    'get_position_manager'
]
