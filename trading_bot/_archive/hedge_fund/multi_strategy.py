"""
Multi-Strategy Engine
=====================
Institutional hedge fund multi-strategy allocation:
- Long/Short Equity
- Market Neutral
- Statistical Arbitrage
- Global Macro
- Event Driven
- Quantitative/Systematic
- Fixed Income Arbitrage
- Convertible Arbitrage
- Merger Arbitrage
- Distressed Securities
"""

import logging
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

try:
    import numpy as np
    import pandas as pd
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


class StrategyType(Enum):
    """Hedge fund strategy types"""
    LONG_SHORT_EQUITY = "long_short_equity"
    MARKET_NEUTRAL = "market_neutral"
    STATISTICAL_ARBITRAGE = "statistical_arbitrage"
    GLOBAL_MACRO = "global_macro"
    EVENT_DRIVEN = "event_driven"
    QUANTITATIVE = "quantitative"
    FIXED_INCOME_ARB = "fixed_income_arb"
    CONVERTIBLE_ARB = "convertible_arb"
    MERGER_ARB = "merger_arb"
    DISTRESSED = "distressed"
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    TREND_FOLLOWING = "trend_following"
    VOLATILITY_ARB = "volatility_arb"
    MULTI_STRATEGY = "multi_strategy"


class StrategyStatus(Enum):
    """Strategy operational status"""
    ACTIVE = "active"
    PAUSED = "paused"
    SCALING_DOWN = "scaling_down"
    SCALING_UP = "scaling_up"
    UNDER_REVIEW = "under_review"
    TERMINATED = "terminated"


@dataclass
class StrategyPerformance:
    """Strategy performance metrics"""
    strategy_id: str
    period_start: date
    period_end: date
    gross_return: float
    net_return: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    current_drawdown: float
    volatility: float
    win_rate: float
    profit_factor: float
    avg_win: float
    avg_loss: float
    num_trades: int
    gross_exposure: float
    net_exposure: float
    turnover: float
    information_ratio: float
    calmar_ratio: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'strategy_id': self.strategy_id,
            'period': f"{self.period_start} to {self.period_end}",
            'gross_return': f"{self.gross_return * 100:.2f}%",
            'net_return': f"{self.net_return * 100:.2f}%",
            'sharpe_ratio': round(self.sharpe_ratio, 2),
            'sortino_ratio': round(self.sortino_ratio, 2),
            'max_drawdown': f"{self.max_drawdown * 100:.2f}%",
            'volatility': f"{self.volatility * 100:.2f}%",
            'win_rate': f"{self.win_rate * 100:.1f}%",
            'profit_factor': round(self.profit_factor, 2),
            'num_trades': self.num_trades,
            'information_ratio': round(self.information_ratio, 2),
            'calmar_ratio': round(self.calmar_ratio, 2)
        }


@dataclass
class StrategyAllocation:
    """Capital allocation to a strategy"""
    strategy_id: str
    target_allocation: float  # Target % of AUM
    current_allocation: float  # Current % of AUM
    min_allocation: float  # Minimum allowed
    max_allocation: float  # Maximum allowed
    risk_budget: float  # % of total risk budget
    leverage_limit: float  # Max leverage for strategy
    gross_exposure_limit: float
    net_exposure_limit: float
    concentration_limit: float  # Max single position
    sector_limits: Dict[str, float] = field(default_factory=dict)
    
    @property
    def allocation_drift(self) -> float:
        """Calculate drift from target"""
        return self.current_allocation - self.target_allocation
    
    @property
    def needs_rebalance(self) -> bool:
        """Check if rebalancing needed"""
        return abs(self.allocation_drift) > 0.02  # 2% threshold


@dataclass
class Strategy:
    """Individual trading strategy"""
    strategy_id: str
    name: str
    strategy_type: StrategyType
    description: str
    status: StrategyStatus
    allocation: StrategyAllocation
    inception_date: date
    portfolio_manager: str
    
    # Strategy parameters
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Universe
    universe: List[str] = field(default_factory=list)
    excluded_symbols: List[str] = field(default_factory=list)
    
    # Risk limits
    max_position_size: float = 0.05  # 5% max single position
    max_sector_exposure: float = 0.25  # 25% max sector
    stop_loss_pct: float = 0.02  # 2% stop loss
    max_daily_loss: float = 0.01  # 1% max daily loss
    
    # Performance tracking
    current_pnl: float = 0.0
    daily_pnl: float = 0.0
    mtd_pnl: float = 0.0
    ytd_pnl: float = 0.0
    
    # Positions
    positions: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # History
    trade_history: List[Dict[str, Any]] = field(default_factory=list)
    performance_history: List[StrategyPerformance] = field(default_factory=list)
    
    def add_position(
        self,
        symbol: str,
        quantity: float,
        price: float,
        side: str
    ) -> Dict[str, Any]:
        """Add or update position"""
        if symbol in self.positions:
            # Update existing
            pos = self.positions[symbol]
            old_qty = pos['quantity']
            old_cost = pos['cost_basis']
            
            if side == 'buy':
                new_qty = old_qty + quantity
                new_cost = old_cost + (quantity * price)
            else:
                new_qty = old_qty - quantity
                new_cost = old_cost - (quantity * price)
            
            pos['quantity'] = new_qty
            pos['cost_basis'] = new_cost
            pos['avg_price'] = new_cost / new_qty if new_qty != 0 else 0
            pos['last_update'] = datetime.now()
        else:
            # New position
            self.positions[symbol] = {
                'symbol': symbol,
                'quantity': quantity if side == 'buy' else -quantity,
                'cost_basis': quantity * price,
                'avg_price': price,
                'current_price': price,
                'unrealized_pnl': 0,
                'realized_pnl': 0,
                'entry_date': datetime.now(),
                'last_update': datetime.now()
            }
        
        # Record trade
        trade = {
            'trade_id': str(uuid.uuid4())[:8],
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'price': price,
            'timestamp': datetime.now(),
            'strategy_id': self.strategy_id
        }
        self.trade_history.append(trade)
        
        return self.positions.get(symbol, {})
    
    def update_prices(self, prices: Dict[str, float]):
        """Update position prices and P&L"""
        for symbol, pos in self.positions.items():
            if symbol in prices:
                old_price = pos['current_price']
                new_price = prices[symbol]
                pos['current_price'] = new_price
                
                # Calculate unrealized P&L
                pos['unrealized_pnl'] = (new_price - pos['avg_price']) * pos['quantity']
        
        # Update strategy P&L
        self.current_pnl = sum(p['unrealized_pnl'] + p['realized_pnl'] for p in self.positions.values())
    
    def get_exposure(self) -> Dict[str, float]:
        """Calculate strategy exposure"""
        long_exposure = sum(
            p['quantity'] * p['current_price']
            for p in self.positions.values()
            if p['quantity'] > 0
        )
        short_exposure = sum(
            abs(p['quantity']) * p['current_price']
            for p in self.positions.values()
            if p['quantity'] < 0
        )
        
        return {
            'long': long_exposure,
            'short': short_exposure,
            'gross': long_exposure + short_exposure,
            'net': long_exposure - short_exposure
        }


class StrategyRotator:
    """
    Dynamic strategy rotation based on market conditions
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.rotation_history: List[Dict[str, Any]] = []
        
        # Market regime mappings
        self.regime_strategy_weights = {
            'trending_up': {
                StrategyType.MOMENTUM: 0.3,
                StrategyType.TREND_FOLLOWING: 0.3,
                StrategyType.LONG_SHORT_EQUITY: 0.2,
                StrategyType.GLOBAL_MACRO: 0.2
            },
            'trending_down': {
                StrategyType.MARKET_NEUTRAL: 0.3,
                StrategyType.STATISTICAL_ARBITRAGE: 0.3,
                StrategyType.VOLATILITY_ARB: 0.2,
                StrategyType.DISTRESSED: 0.2
            },
            'ranging': {
                StrategyType.MEAN_REVERSION: 0.3,
                StrategyType.STATISTICAL_ARBITRAGE: 0.3,
                StrategyType.MARKET_NEUTRAL: 0.2,
                StrategyType.CONVERTIBLE_ARB: 0.2
            },
            'volatile': {
                StrategyType.VOLATILITY_ARB: 0.3,
                StrategyType.MARKET_NEUTRAL: 0.3,
                StrategyType.STATISTICAL_ARBITRAGE: 0.2,
                StrategyType.FIXED_INCOME_ARB: 0.2
            },
            'crisis': {
                StrategyType.MARKET_NEUTRAL: 0.4,
                StrategyType.FIXED_INCOME_ARB: 0.3,
                StrategyType.DISTRESSED: 0.3
            }
        }
    
    def get_optimal_weights(
        self,
        market_regime: str,
        strategy_performances: Dict[str, StrategyPerformance]
    ) -> Dict[StrategyType, float]:
        """Get optimal strategy weights for current regime"""
        base_weights = self.regime_strategy_weights.get(
            market_regime,
            self.regime_strategy_weights['ranging']
        )
        
        # Adjust based on recent performance
        adjusted_weights = {}
        total_weight = 0
        
        for strategy_type, base_weight in base_weights.items():
            # Find performance for this strategy type
            perf_adjustment = 1.0
            for perf in strategy_performances.values():
                if perf.sharpe_ratio > 1.5:
                    perf_adjustment = 1.2
                elif perf.sharpe_ratio < 0.5:
                    perf_adjustment = 0.8
            
            adjusted_weight = base_weight * perf_adjustment
            adjusted_weights[strategy_type] = adjusted_weight
            total_weight += adjusted_weight
        
        # Normalize
        if total_weight > 0:
            adjusted_weights = {
                k: v / total_weight for k, v in adjusted_weights.items()
            }
        
        return adjusted_weights
    
    def should_rotate(
        self,
        current_allocations: Dict[str, StrategyAllocation],
        optimal_weights: Dict[StrategyType, float],
        threshold: float = 0.05
    ) -> Tuple[bool, Dict[str, float]]:
        """Determine if rotation is needed"""
        changes = {}
        max_change = 0
        
        for strategy_id, allocation in current_allocations.items():
            # This would need strategy type mapping
            optimal = optimal_weights.get(StrategyType.QUANTITATIVE, 0.1)
            change = optimal - allocation.current_allocation
            changes[strategy_id] = change
            max_change = max(max_change, abs(change))
        
        return max_change > threshold, changes


class MultiStrategyEngine:
    """
    Multi-Strategy Hedge Fund Engine
    Manages multiple trading strategies with dynamic allocation
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Strategies
        self.strategies: Dict[str, Strategy] = {}
        
        # Allocations
        self.total_capital = config.get('total_capital', 100_000_000)  # $100M default
        self.cash_reserve = config.get('cash_reserve', 0.05)  # 5% cash
        
        # Risk limits
        self.max_gross_exposure = config.get('max_gross_exposure', 2.0)  # 200%
        self.max_net_exposure = config.get('max_net_exposure', 0.5)  # 50%
        self.max_strategy_allocation = config.get('max_strategy_allocation', 0.3)  # 30%
        self.max_single_position = config.get('max_single_position', 0.02)  # 2%
        
        # Rotator
        self.rotator = StrategyRotator()
        
        # Performance tracking
        self.daily_pnl_history: List[Dict[str, Any]] = []
        self.allocation_history: List[Dict[str, Any]] = []
        
        logger.info("Multi-Strategy Engine initialized")
    
    def add_strategy(
        self,
        name: str,
        strategy_type: StrategyType,
        target_allocation: float,
        parameters: Optional[Dict[str, Any]] = None,
        portfolio_manager: str = "System"
    ) -> Strategy:
        """Add a new strategy to the fund"""
        strategy_id = str(uuid.uuid4())[:8]
        
        allocation = StrategyAllocation(
            strategy_id=strategy_id,
            target_allocation=target_allocation,
            current_allocation=0.0,
            min_allocation=0.0,
            max_allocation=self.max_strategy_allocation,
            risk_budget=target_allocation,
            leverage_limit=2.0,
            gross_exposure_limit=2.0,
            net_exposure_limit=1.0,
            concentration_limit=0.1
        )
        
        strategy = Strategy(
            strategy_id=strategy_id,
            name=name,
            strategy_type=strategy_type,
            description=f"{strategy_type.value} strategy",
            status=StrategyStatus.ACTIVE,
            allocation=allocation,
            inception_date=date.today(),
            portfolio_manager=portfolio_manager,
            parameters=parameters or {}
        )
        
        self.strategies[strategy_id] = strategy
        logger.info(f"Added strategy: {name} ({strategy_type.value})")
        
        return strategy
    
    def create_default_strategies(self):
        """Create a diversified set of default strategies"""
        strategies = [
            ("Alpha Long/Short", StrategyType.LONG_SHORT_EQUITY, 0.20),
            ("Market Neutral", StrategyType.MARKET_NEUTRAL, 0.15),
            ("Statistical Arbitrage", StrategyType.STATISTICAL_ARBITRAGE, 0.15),
            ("Global Macro", StrategyType.GLOBAL_MACRO, 0.15),
            ("Momentum", StrategyType.MOMENTUM, 0.10),
            ("Mean Reversion", StrategyType.MEAN_REVERSION, 0.10),
            ("Volatility Arbitrage", StrategyType.VOLATILITY_ARB, 0.10),
            ("Event Driven", StrategyType.EVENT_DRIVEN, 0.05)
        ]
        
        for name, stype, allocation in strategies:
            self.add_strategy(name, stype, allocation)
        
        logger.info(f"Created {len(strategies)} default strategies")
    
    def allocate_capital(self) -> Dict[str, float]:
        """Allocate capital across strategies"""
        available_capital = self.total_capital * (1 - self.cash_reserve)
        allocations = {}
        
        for strategy_id, strategy in self.strategies.items():
            if strategy.status == StrategyStatus.ACTIVE:
                allocation_amount = available_capital * strategy.allocation.target_allocation
                allocations[strategy_id] = allocation_amount
                strategy.allocation.current_allocation = strategy.allocation.target_allocation
        
        # Store allocation
        self.allocation_history.append({
            'timestamp': datetime.now(),
            'allocations': allocations.copy(),
            'total_allocated': sum(allocations.values()),
            'cash_reserve': self.total_capital * self.cash_reserve
        })
        
        return allocations
    
    def rebalance(
        self,
        market_regime: str = 'ranging'
    ) -> Dict[str, Dict[str, float]]:
        """Rebalance strategy allocations"""
        # Get current performance
        performances = {}
        for sid, strategy in self.strategies.items():
            if strategy.performance_history:
                performances[sid] = strategy.performance_history[-1]
        
        # Get optimal weights
        optimal_weights = self.rotator.get_optimal_weights(market_regime, performances)
        
        # Calculate rebalance trades
        rebalance_trades = {}
        
        for strategy_id, strategy in self.strategies.items():
            optimal = optimal_weights.get(strategy.strategy_type, 0.1)
            current = strategy.allocation.current_allocation
            
            if abs(optimal - current) > 0.02:  # 2% threshold
                change = optimal - current
                rebalance_trades[strategy_id] = {
                    'from': current,
                    'to': optimal,
                    'change': change,
                    'amount': change * self.total_capital
                }
                
                # Update allocation
                strategy.allocation.target_allocation = optimal
        
        logger.info(f"Rebalance: {len(rebalance_trades)} strategies adjusted")
        return rebalance_trades
    
    def generate_signals(
        self,
        market_data: Dict[str, Any]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Generate trading signals from all active strategies"""
        all_signals = {}
        
        for strategy_id, strategy in self.strategies.items():
            if strategy.status != StrategyStatus.ACTIVE:
                continue
            
            signals = self._generate_strategy_signals(strategy, market_data)
            if signals:
                all_signals[strategy_id] = signals
        
        return all_signals
    
    def _generate_strategy_signals(
        self,
        strategy: Strategy,
        market_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate signals for a specific strategy"""
        signals = []
        
        # Strategy-specific signal generation
        if strategy.strategy_type == StrategyType.LONG_SHORT_EQUITY:
            signals = self._long_short_signals(strategy, market_data)
        elif strategy.strategy_type == StrategyType.MARKET_NEUTRAL:
            signals = self._market_neutral_signals(strategy, market_data)
        elif strategy.strategy_type == StrategyType.STATISTICAL_ARBITRAGE:
            signals = self._stat_arb_signals(strategy, market_data)
        elif strategy.strategy_type == StrategyType.MOMENTUM:
            signals = self._momentum_signals(strategy, market_data)
        elif strategy.strategy_type == StrategyType.MEAN_REVERSION:
            signals = self._mean_reversion_signals(strategy, market_data)
        elif strategy.strategy_type == StrategyType.GLOBAL_MACRO:
            signals = self._global_macro_signals(strategy, market_data)
        elif strategy.strategy_type == StrategyType.VOLATILITY_ARB:
            signals = self._volatility_arb_signals(strategy, market_data)
        elif strategy.strategy_type == StrategyType.EVENT_DRIVEN:
            signals = self._event_driven_signals(strategy, market_data)
        
        return signals
    
    def _long_short_signals(
        self,
        strategy: Strategy,
        market_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Long/Short equity signals based on fundamental + technical"""
        signals = []
        
        # Example: rank stocks by momentum and value
        prices = market_data.get('prices', {})
        
        for symbol, data in prices.items():
            if not isinstance(data, dict):
                continue
            
            # Simple momentum signal
            returns_20d = data.get('returns_20d', 0)
            returns_60d = data.get('returns_60d', 0)
            
            # Long strong momentum
            if returns_20d > 0.05 and returns_60d > 0.10:
                signals.append({
                    'symbol': symbol,
                    'direction': 'long',
                    'strength': min(returns_20d * 10, 1.0),
                    'strategy_id': strategy.strategy_id,
                    'reason': 'Strong momentum'
                })
            # Short weak momentum
            elif returns_20d < -0.05 and returns_60d < -0.10:
                signals.append({
                    'symbol': symbol,
                    'direction': 'short',
                    'strength': min(abs(returns_20d) * 10, 1.0),
                    'strategy_id': strategy.strategy_id,
                    'reason': 'Weak momentum'
                })
        
        return signals
    
    def _market_neutral_signals(
        self,
        strategy: Strategy,
        market_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Market neutral pairs signals"""
        signals = []
        
        # Example: sector-neutral long/short
        prices = market_data.get('prices', {})
        sectors = market_data.get('sectors', {})
        
        # Group by sector and find relative strength
        sector_stocks = {}
        for symbol, sector in sectors.items():
            if sector not in sector_stocks:
                sector_stocks[sector] = []
            if symbol in prices:
                sector_stocks[sector].append({
                    'symbol': symbol,
                    'return': prices[symbol].get('returns_20d', 0) if isinstance(prices[symbol], dict) else 0
                })
        
        # Long top, short bottom within each sector
        for sector, stocks in sector_stocks.items():
            if len(stocks) < 2:
                continue
            
            sorted_stocks = sorted(stocks, key=lambda x: x['return'], reverse=True)
            
            # Long top performer
            signals.append({
                'symbol': sorted_stocks[0]['symbol'],
                'direction': 'long',
                'strength': 0.7,
                'strategy_id': strategy.strategy_id,
                'reason': f'Sector leader in {sector}'
            })
            
            # Short bottom performer
            signals.append({
                'symbol': sorted_stocks[-1]['symbol'],
                'direction': 'short',
                'strength': 0.7,
                'strategy_id': strategy.strategy_id,
                'reason': f'Sector laggard in {sector}'
            })
        
        return signals
    
    def _stat_arb_signals(
        self,
        strategy: Strategy,
        market_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Statistical arbitrage signals"""
        signals = []
        
        # Example: mean reversion on correlated pairs
        correlations = market_data.get('correlations', {})
        prices = market_data.get('prices', {})
        
        for pair, corr in correlations.items():
            if corr < 0.8:  # Only highly correlated pairs
                continue
            
            symbols = pair.split('_')
            if len(symbols) != 2:
                continue
            
            sym1, sym2 = symbols
            if sym1 not in prices or sym2 not in prices:
                continue
            
            # Calculate spread z-score
            p1 = prices[sym1].get('price', 0) if isinstance(prices[sym1], dict) else prices[sym1]
            p2 = prices[sym2].get('price', 0) if isinstance(prices[sym2], dict) else prices[sym2]
            
            if p2 == 0:
                continue
            
            ratio = p1 / p2
            mean_ratio = market_data.get('mean_ratios', {}).get(pair, ratio)
            std_ratio = market_data.get('std_ratios', {}).get(pair, 0.1)
            
            if std_ratio == 0:
                continue
            
            z_score = (ratio - mean_ratio) / std_ratio
            
            if z_score > 2:
                # Spread too wide, short sym1, long sym2
                signals.append({
                    'symbol': sym1,
                    'direction': 'short',
                    'strength': min(abs(z_score) / 4, 1.0),
                    'strategy_id': strategy.strategy_id,
                    'reason': f'Stat arb: spread z={z_score:.2f}'
                })
                signals.append({
                    'symbol': sym2,
                    'direction': 'long',
                    'strength': min(abs(z_score) / 4, 1.0),
                    'strategy_id': strategy.strategy_id,
                    'reason': f'Stat arb: spread z={z_score:.2f}'
                })
            elif z_score < -2:
                # Spread too narrow, long sym1, short sym2
                signals.append({
                    'symbol': sym1,
                    'direction': 'long',
                    'strength': min(abs(z_score) / 4, 1.0),
                    'strategy_id': strategy.strategy_id,
                    'reason': f'Stat arb: spread z={z_score:.2f}'
                })
                signals.append({
                    'symbol': sym2,
                    'direction': 'short',
                    'strength': min(abs(z_score) / 4, 1.0),
                    'strategy_id': strategy.strategy_id,
                    'reason': f'Stat arb: spread z={z_score:.2f}'
                })
        
        return signals
    
    def _momentum_signals(
        self,
        strategy: Strategy,
        market_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Momentum strategy signals"""
        signals = []
        prices = market_data.get('prices', {})
        
        for symbol, data in prices.items():
            if not isinstance(data, dict):
                continue
            
            # Multi-timeframe momentum
            mom_5d = data.get('returns_5d', 0)
            mom_20d = data.get('returns_20d', 0)
            mom_60d = data.get('returns_60d', 0)
            
            # Strong momentum across timeframes
            if mom_5d > 0 and mom_20d > 0 and mom_60d > 0:
                strength = (mom_5d + mom_20d + mom_60d) / 3
                if strength > 0.02:
                    signals.append({
                        'symbol': symbol,
                        'direction': 'long',
                        'strength': min(strength * 5, 1.0),
                        'strategy_id': strategy.strategy_id,
                        'reason': 'Multi-TF momentum'
                    })
            elif mom_5d < 0 and mom_20d < 0 and mom_60d < 0:
                strength = abs(mom_5d + mom_20d + mom_60d) / 3
                if strength > 0.02:
                    signals.append({
                        'symbol': symbol,
                        'direction': 'short',
                        'strength': min(strength * 5, 1.0),
                        'strategy_id': strategy.strategy_id,
                        'reason': 'Multi-TF momentum (bearish)'
                    })
        
        return signals
    
    def _mean_reversion_signals(
        self,
        strategy: Strategy,
        market_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Mean reversion signals"""
        signals = []
        prices = market_data.get('prices', {})
        
        for symbol, data in prices.items():
            if not isinstance(data, dict):
                continue
            
            # RSI-based mean reversion
            rsi = data.get('rsi', 50)
            bb_position = data.get('bb_position', 0.5)  # 0=lower, 1=upper
            
            # Oversold
            if rsi < 30 and bb_position < 0.2:
                signals.append({
                    'symbol': symbol,
                    'direction': 'long',
                    'strength': (30 - rsi) / 30,
                    'strategy_id': strategy.strategy_id,
                    'reason': f'Oversold: RSI={rsi:.0f}'
                })
            # Overbought
            elif rsi > 70 and bb_position > 0.8:
                signals.append({
                    'symbol': symbol,
                    'direction': 'short',
                    'strength': (rsi - 70) / 30,
                    'strategy_id': strategy.strategy_id,
                    'reason': f'Overbought: RSI={rsi:.0f}'
                })
        
        return signals
    
    def _global_macro_signals(
        self,
        strategy: Strategy,
        market_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Global macro signals"""
        signals = []
        
        # Macro indicators
        macro = market_data.get('macro', {})
        
        # Interest rate differential
        rate_diff = macro.get('rate_differential', 0)
        
        # GDP growth differential
        gdp_diff = macro.get('gdp_differential', 0)
        
        # Inflation differential
        inflation_diff = macro.get('inflation_differential', 0)
        
        # Currency signals based on macro
        currencies = market_data.get('currencies', {})
        for pair, data in currencies.items():
            if not isinstance(data, dict):
                continue
            
            # Carry trade signal
            if rate_diff > 0.02:  # 2% rate differential
                signals.append({
                    'symbol': pair,
                    'direction': 'long',
                    'strength': min(rate_diff * 10, 1.0),
                    'strategy_id': strategy.strategy_id,
                    'reason': f'Carry trade: rate diff={rate_diff*100:.1f}%'
                })
        
        return signals
    
    def _volatility_arb_signals(
        self,
        strategy: Strategy,
        market_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Volatility arbitrage signals"""
        signals = []
        
        # Implied vs realized volatility
        vol_data = market_data.get('volatility', {})
        
        for symbol, data in vol_data.items():
            if not isinstance(data, dict):
                continue
            
            implied_vol = data.get('implied', 0)
            realized_vol = data.get('realized', 0)
            
            if implied_vol == 0 or realized_vol == 0:
                continue
            
            vol_premium = implied_vol - realized_vol
            
            # Sell vol when premium is high
            if vol_premium > 0.05:  # 5% premium
                signals.append({
                    'symbol': symbol,
                    'direction': 'short_vol',
                    'strength': min(vol_premium * 5, 1.0),
                    'strategy_id': strategy.strategy_id,
                    'reason': f'Vol premium: {vol_premium*100:.1f}%'
                })
            # Buy vol when discount
            elif vol_premium < -0.05:
                signals.append({
                    'symbol': symbol,
                    'direction': 'long_vol',
                    'strength': min(abs(vol_premium) * 5, 1.0),
                    'strategy_id': strategy.strategy_id,
                    'reason': f'Vol discount: {vol_premium*100:.1f}%'
                })
        
        return signals
    
    def _event_driven_signals(
        self,
        strategy: Strategy,
        market_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Event-driven signals"""
        signals = []
        
        # Corporate events
        events = market_data.get('events', [])
        
        for event in events:
            symbol = event.get('symbol')
            event_type = event.get('type')
            
            if event_type == 'merger':
                # Merger arb: long target, short acquirer
                target = event.get('target')
                acquirer = event.get('acquirer')
                spread = event.get('spread', 0)
                
                if spread > 0.02:  # 2% spread
                    signals.append({
                        'symbol': target,
                        'direction': 'long',
                        'strength': min(spread * 10, 1.0),
                        'strategy_id': strategy.strategy_id,
                        'reason': f'Merger arb: {spread*100:.1f}% spread'
                    })
                    signals.append({
                        'symbol': acquirer,
                        'direction': 'short',
                        'strength': min(spread * 10, 1.0) * 0.5,  # Smaller hedge
                        'strategy_id': strategy.strategy_id,
                        'reason': f'Merger arb hedge'
                    })
            
            elif event_type == 'earnings':
                # Earnings play
                surprise = event.get('surprise', 0)
                if abs(surprise) > 0.05:  # 5% surprise
                    direction = 'long' if surprise > 0 else 'short'
                    signals.append({
                        'symbol': symbol,
                        'direction': direction,
                        'strength': min(abs(surprise) * 5, 1.0),
                        'strategy_id': strategy.strategy_id,
                        'reason': f'Earnings surprise: {surprise*100:.1f}%'
                    })
        
        return signals
    
    def aggregate_signals(
        self,
        all_signals: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Dict[str, Any]]:
        """Aggregate signals from all strategies"""
        aggregated = {}
        
        for strategy_id, signals in all_signals.items():
            strategy = self.strategies.get(strategy_id)
            if not strategy:
                continue
            
            weight = strategy.allocation.current_allocation
            
            for signal in signals:
                symbol = signal['symbol']
                
                if symbol not in aggregated:
                    aggregated[symbol] = {
                        'symbol': symbol,
                        'long_weight': 0,
                        'short_weight': 0,
                        'signals': []
                    }
                
                weighted_strength = signal['strength'] * weight
                
                if signal['direction'] in ['long', 'long_vol']:
                    aggregated[symbol]['long_weight'] += weighted_strength
                else:
                    aggregated[symbol]['short_weight'] += weighted_strength
                
                aggregated[symbol]['signals'].append(signal)
        
        # Calculate net direction
        for symbol, data in aggregated.items():
            net = data['long_weight'] - data['short_weight']
            data['net_weight'] = net
            data['direction'] = 'long' if net > 0 else 'short' if net < 0 else 'neutral'
            data['conviction'] = abs(net)
        
        return aggregated
    
    def get_portfolio_exposure(self) -> Dict[str, Any]:
        """Get aggregate portfolio exposure"""
        total_long = 0
        total_short = 0
        
        for strategy in self.strategies.values():
            exposure = strategy.get_exposure()
            total_long += exposure['long']
            total_short += exposure['short']
        
        gross = total_long + total_short
        net = total_long - total_short
        
        return {
            'long_exposure': total_long,
            'short_exposure': total_short,
            'gross_exposure': gross,
            'net_exposure': net,
            'gross_pct': gross / self.total_capital if self.total_capital > 0 else 0,
            'net_pct': net / self.total_capital if self.total_capital > 0 else 0,
            'leverage': gross / self.total_capital if self.total_capital > 0 else 0
        }
    
    def get_strategy_summary(self) -> Dict[str, Any]:
        """Get summary of all strategies"""
        summary = {
            'total_strategies': len(self.strategies),
            'active_strategies': sum(1 for s in self.strategies.values() if s.status == StrategyStatus.ACTIVE),
            'total_capital': self.total_capital,
            'strategies': {}
        }
        
        for sid, strategy in self.strategies.items():
            summary['strategies'][sid] = {
                'name': strategy.name,
                'type': strategy.strategy_type.value,
                'status': strategy.status.value,
                'allocation': strategy.allocation.current_allocation,
                'pnl': strategy.current_pnl,
                'positions': len(strategy.positions)
            }
        
        return summary
