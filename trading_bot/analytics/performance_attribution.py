"""
Real-Time Performance Attribution System
Institutional-Grade P&L Decomposition

This module provides comprehensive performance attribution:
- Strategy-level P&L tracking
- Signal-level attribution
- Factor-based decomposition (Brinson-Fachler)
- Regime-based performance analysis
- Real-time alpha/beta decomposition
- Transaction cost analysis
- Risk-adjusted attribution

Portfolio Manager + Quantitative Analyst + Auditor Perspective
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
from collections import deque, defaultdict
import warnings
import numpy
import pandas

warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class AttributionLevel(Enum):
    """Attribution granularity levels"""
    PORTFOLIO = "PORTFOLIO"  # Total portfolio level
    STRATEGY = "STRATEGY"  # Strategy level
    SIGNAL = "SIGNAL"  # Individual signal level
    ASSET = "ASSET"  # Asset level
    FACTOR = "FACTOR"  # Factor level


class AttributionMethod(Enum):
    """Attribution methodology"""
    BRINSON_FACHLER = "BRINSON_FACHLER"  # Classic allocation/selection
    FACTOR_BASED = "FACTOR_BASED"  # Factor decomposition
    RETURNS_BASED = "RETURNS_BASED"  # Returns-based style analysis
    TRANSACTION_COST = "TRANSACTION_COST"  # TCA attribution


@dataclass
class Trade:
    """Individual trade record"""
    trade_id: str
    timestamp: datetime
    symbol: str
    side: str  # BUY or SELL
    quantity: float
    price: float
    strategy: str
    signal_id: str
    commission: float = 0.0
    slippage: float = 0.0
    
    @property
    def value(self) -> float:
        return self.quantity * self.price
    
    @property
    def total_cost(self) -> float:
        return self.commission + self.slippage
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'trade_id': self.trade_id,
            'timestamp': self.timestamp.isoformat(),
            'symbol': self.symbol,
            'side': self.side,
            'quantity': self.quantity,
            'price': self.price,
            'value': self.value,
            'strategy': self.strategy,
            'signal_id': self.signal_id,
            'commission': self.commission,
            'slippage': self.slippage
        }


@dataclass
class Position:
    """Current position"""
    symbol: str
    quantity: float
    avg_cost: float
    current_price: float
    strategy: str
    entry_time: datetime
    
    @property
    def market_value(self) -> float:
        return self.quantity * self.current_price
    
    @property
    def cost_basis(self) -> float:
        return self.quantity * self.avg_cost
    
    @property
    def unrealized_pnl(self) -> float:
        return self.market_value - self.cost_basis
    
    @property
    def unrealized_pnl_pct(self) -> float:
        try:
            if self.cost_basis != 0:
                return self.unrealized_pnl / abs(self.cost_basis)
            return 0.0
        except Exception as e:
            logger.error(f"Error in unrealized_pnl_pct: {e}")
            raise
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'quantity': self.quantity,
            'avg_cost': self.avg_cost,
            'current_price': self.current_price,
            'market_value': self.market_value,
            'unrealized_pnl': self.unrealized_pnl,
            'unrealized_pnl_pct': round(self.unrealized_pnl_pct, 4),
            'strategy': self.strategy
        }


@dataclass
class StrategyPerformance:
    """Strategy-level performance metrics"""
    strategy_name: str
    period_start: datetime
    period_end: datetime
    
    # P&L
    gross_pnl: float
    net_pnl: float
    realized_pnl: float
    unrealized_pnl: float
    
    # Costs
    total_commissions: float
    total_slippage: float
    total_costs: float
    
    # Returns
    gross_return: float
    net_return: float
    
    # Risk metrics
    volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    
    # Activity
    num_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    
    # Attribution
    alpha: float
    beta: float
    information_ratio: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'strategy_name': self.strategy_name,
            'period': f"{self.period_start.date()} to {self.period_end.date()}",
            'gross_pnl': round(self.gross_pnl, 2),
            'net_pnl': round(self.net_pnl, 2),
            'total_costs': round(self.total_costs, 2),
            'gross_return': round(self.gross_return, 4),
            'net_return': round(self.net_return, 4),
            'sharpe_ratio': round(self.sharpe_ratio, 2),
            'sortino_ratio': round(self.sortino_ratio, 2),
            'max_drawdown': round(self.max_drawdown, 4),
            'num_trades': self.num_trades,
            'win_rate': round(self.win_rate, 4),
            'profit_factor': round(self.profit_factor, 2),
            'alpha': round(self.alpha, 4),
            'beta': round(self.beta, 2),
            'information_ratio': round(self.information_ratio, 2)
        }


@dataclass
class SignalPerformance:
    """Signal-level performance metrics"""
    signal_id: str
    signal_type: str
    strategy: str
    symbol: str
    direction: str
    entry_time: datetime
    exit_time: Optional[datetime]
    
    # P&L
    gross_pnl: float
    net_pnl: float
    return_pct: float
    
    # Costs
    entry_slippage: float
    exit_slippage: float
    commissions: float
    
    # Quality metrics
    signal_strength: float
    confidence: float
    hit_take_profit: bool
    hit_stop_loss: bool
    
    # Duration
    holding_period_hours: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'signal_id': self.signal_id,
            'signal_type': self.signal_type,
            'strategy': self.strategy,
            'symbol': self.symbol,
            'direction': self.direction,
            'gross_pnl': round(self.gross_pnl, 2),
            'net_pnl': round(self.net_pnl, 2),
            'return_pct': round(self.return_pct, 4),
            'holding_period_hours': round(self.holding_period_hours, 1),
            'hit_take_profit': self.hit_take_profit,
            'hit_stop_loss': self.hit_stop_loss
        }


@dataclass
class FactorAttribution:
    """Factor-based attribution"""
    factor_name: str
    exposure: float  # Beta to factor
    factor_return: float  # Factor return
    contribution: float  # Exposure * Factor Return
    contribution_pct: float  # % of total return
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'factor_name': self.factor_name,
            'exposure': round(self.exposure, 3),
            'factor_return': round(self.factor_return, 4),
            'contribution': round(self.contribution, 4),
            'contribution_pct': round(self.contribution_pct, 4)
        }


@dataclass
class BrinsonAttribution:
    """Brinson-Fachler attribution"""
    segment: str  # Asset class, sector, etc.
    portfolio_weight: float
    benchmark_weight: float
    portfolio_return: float
    benchmark_return: float
    
    # Attribution effects
    allocation_effect: float  # Weight difference * benchmark return
    selection_effect: float  # Portfolio weight * return difference
    interaction_effect: float  # Weight diff * return diff
    total_effect: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'segment': self.segment,
            'portfolio_weight': round(self.portfolio_weight, 4),
            'benchmark_weight': round(self.benchmark_weight, 4),
            'portfolio_return': round(self.portfolio_return, 4),
            'benchmark_return': round(self.benchmark_return, 4),
            'allocation_effect': round(self.allocation_effect, 4),
            'selection_effect': round(self.selection_effect, 4),
            'interaction_effect': round(self.interaction_effect, 4),
            'total_effect': round(self.total_effect, 4)
        }


class PerformanceAttributionSystem:
    """
    Real-Time Performance Attribution System
    
    Provides comprehensive P&L decomposition and attribution:
    
    1. Strategy Attribution
       - Track P&L by strategy
       - Identify best/worst performers
       - Real-time optimization signals
    
    2. Signal Attribution
       - Individual signal performance
       - Signal quality scoring
       - Entry/exit timing analysis
    
    3. Factor Attribution
       - Market, size, value, momentum factors
       - Alpha vs beta decomposition
       - Risk factor exposures
    
    4. Brinson-Fachler Attribution
       - Allocation effect (weight decisions)
       - Selection effect (security selection)
       - Interaction effect
    
    5. Transaction Cost Analysis
       - Commission tracking
       - Slippage analysis
       - Implementation shortfall
    
    6. Regime-Based Analysis
       - Performance by market regime
       - Conditional attribution
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize performance attribution system
        
        Args:
            config: Configuration dictionary
        """
        try:
            self.config = config or {}
        
            # Risk-free rate for Sharpe calculation
            self.risk_free_rate = self.config.get('risk_free_rate', 0.04)
        
            # Benchmark for relative attribution
            self.benchmark_returns: deque = deque(maxlen=1000)
        
            # Trade and position tracking
            self.trades: List[Trade] = []
            self.positions: Dict[str, Position] = {}
            self.closed_positions: List[Dict[str, Any]] = []
        
            # Strategy tracking
            self.strategy_trades: Dict[str, List[Trade]] = defaultdict(list)
            self.strategy_pnl: Dict[str, List[float]] = defaultdict(list)
            self.strategy_returns: Dict[str, deque] = defaultdict(lambda: deque(maxlen=252))
        
            # Signal tracking
            self.signal_performance: Dict[str, SignalPerformance] = {}
            self.active_signals: Dict[str, Dict[str, Any]] = {}
        
            # Daily P&L tracking
            self.daily_pnl: deque = deque(maxlen=252)
            self.daily_returns: deque = deque(maxlen=252)
        
            # Factor returns (simplified)
            self.factor_returns: Dict[str, deque] = {
                'market': deque(maxlen=252),
                'size': deque(maxlen=252),
                'value': deque(maxlen=252),
                'momentum': deque(maxlen=252),
                'volatility': deque(maxlen=252)
            }
        
            # Statistics
            self.total_trades = 0
            self.total_pnl = 0.0
        
            logger.info("PerformanceAttributionSystem initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def record_trade(self, trade: Trade):
        """
        Record a new trade
        
        Args:
            trade: Trade object
        """
        try:
            self.trades.append(trade)
            self.strategy_trades[trade.strategy].append(trade)
            self.total_trades += 1
        
            # Update position
            self._update_position(trade)
        
            # Update signal tracking
            if trade.signal_id in self.active_signals:
                self._update_signal_performance(trade)
        
            logger.debug(f"Trade recorded: {trade.symbol} {trade.side} {trade.quantity} @ {trade.price}")
        except Exception as e:
            logger.error(f"Error in record_trade: {e}")
            raise
    
    def _update_position(self, trade: Trade):
        """Update position based on trade"""
        try:
            symbol = trade.symbol
        
            if symbol not in self.positions:
                # New position
                if trade.side == 'BUY':
                    self.positions[symbol] = Position(
                        symbol=symbol,
                        quantity=trade.quantity,
                        avg_cost=trade.price,
                        current_price=trade.price,
                        strategy=trade.strategy,
                        entry_time=trade.timestamp
                    )
                else:
                    # Short position
                    self.positions[symbol] = Position(
                        symbol=symbol,
                        quantity=-trade.quantity,
                        avg_cost=trade.price,
                        current_price=trade.price,
                        strategy=trade.strategy,
                        entry_time=trade.timestamp
                    )
            else:
                pos = self.positions[symbol]
            
                if trade.side == 'BUY':
                    if pos.quantity >= 0:
                        # Adding to long
                        new_qty = pos.quantity + trade.quantity
                        new_cost = (pos.cost_basis + trade.value) / new_qty
                        pos.quantity = new_qty
                        pos.avg_cost = new_cost
                    else:
                        # Covering short
                        if trade.quantity >= abs(pos.quantity):
                            # Close and potentially go long
                            realized_pnl = abs(pos.quantity) * (pos.avg_cost - trade.price)
                            self._record_realized_pnl(symbol, realized_pnl, trade)
                        
                            remaining = trade.quantity - abs(pos.quantity)
                            if remaining > 0:
                                pos.quantity = remaining
                                pos.avg_cost = trade.price
                            else:
                                del self.positions[symbol]
                        else:
                            # Partial cover
                            realized_pnl = trade.quantity * (pos.avg_cost - trade.price)
                            self._record_realized_pnl(symbol, realized_pnl, trade)
                            pos.quantity += trade.quantity
                else:  # SELL
                    if pos.quantity <= 0:
                        # Adding to short
                        new_qty = pos.quantity - trade.quantity
                        new_cost = (pos.cost_basis + trade.value) / abs(new_qty)
                        pos.quantity = new_qty
                        pos.avg_cost = new_cost
                    else:
                        # Closing long
                        if trade.quantity >= pos.quantity:
                            # Close and potentially go short
                            realized_pnl = pos.quantity * (trade.price - pos.avg_cost)
                            self._record_realized_pnl(symbol, realized_pnl, trade)
                        
                            remaining = trade.quantity - pos.quantity
                            if remaining > 0:
                                pos.quantity = -remaining
                                pos.avg_cost = trade.price
                            else:
                                del self.positions[symbol]
                        else:
                            # Partial close
                            realized_pnl = trade.quantity * (trade.price - pos.avg_cost)
                            self._record_realized_pnl(symbol, realized_pnl, trade)
                            pos.quantity -= trade.quantity
        except Exception as e:
            logger.error(f"Error in _update_position: {e}")
            raise
    
    def _record_realized_pnl(self, symbol: str, pnl: float, trade: Trade):
        """Record realized P&L"""
        try:
            net_pnl = pnl - trade.total_cost
        
            self.strategy_pnl[trade.strategy].append(net_pnl)
            self.total_pnl += net_pnl
        
            self.closed_positions.append({
                'symbol': symbol,
                'timestamp': trade.timestamp,
                'gross_pnl': pnl,
                'net_pnl': net_pnl,
                'costs': trade.total_cost,
                'strategy': trade.strategy,
                'signal_id': trade.signal_id
            })
        except Exception as e:
            logger.error(f"Error in _record_realized_pnl: {e}")
            raise
    
    def update_prices(self, prices: Dict[str, float]):
        """
        Update current prices for positions
        
        Args:
            prices: Dictionary of {symbol: price}
        """
        try:
            for symbol, price in prices.items():
                if symbol in self.positions:
                    self.positions[symbol].current_price = price
        except Exception as e:
            logger.error(f"Error in update_prices: {e}")
            raise
    
    def record_signal_entry(self,
                           signal_id: str,
                           signal_type: str,
                           strategy: str,
                           symbol: str,
                           direction: str,
                           entry_price: float,
                           confidence: float = 0.5,
                           signal_strength: float = 0.5):
        """Record signal entry for attribution"""
        try:
            self.active_signals[signal_id] = {
                'signal_type': signal_type,
                'strategy': strategy,
                'symbol': symbol,
                'direction': direction,
                'entry_price': entry_price,
                'entry_time': datetime.now(),
                'confidence': confidence,
                'signal_strength': signal_strength,
                'entry_slippage': 0.0,
                'trades': []
            }
        except Exception as e:
            logger.error(f"Error in record_signal_entry: {e}")
            raise
    
    def record_signal_exit(self,
                          signal_id: str,
                          exit_price: float,
                          hit_take_profit: bool = False,
                          hit_stop_loss: bool = False):
        """Record signal exit and calculate performance"""
        try:
            if signal_id not in self.active_signals:
                return
        
            signal = self.active_signals[signal_id]
            entry_price = signal['entry_price']
        
            # Calculate return
            if signal['direction'] == 'BUY':
                return_pct = (exit_price - entry_price) / entry_price
            else:
                return_pct = (entry_price - exit_price) / entry_price
        
            # Calculate P&L from trades
            gross_pnl = sum(t.get('pnl', 0) for t in signal.get('trades', []))
            commissions = sum(t.get('commission', 0) for t in signal.get('trades', []))
        
            # Calculate holding period
            holding_hours = (datetime.now() - signal['entry_time']).total_seconds() / 3600
        
            perf = SignalPerformance(
                signal_id=signal_id,
                signal_type=signal['signal_type'],
                strategy=signal['strategy'],
                symbol=signal['symbol'],
                direction=signal['direction'],
                entry_time=signal['entry_time'],
                exit_time=datetime.now(),
                gross_pnl=gross_pnl,
                net_pnl=gross_pnl - commissions,
                return_pct=return_pct,
                entry_slippage=signal.get('entry_slippage', 0),
                exit_slippage=0.0,
                commissions=commissions,
                signal_strength=signal['signal_strength'],
                confidence=signal['confidence'],
                hit_take_profit=hit_take_profit,
                hit_stop_loss=hit_stop_loss,
                holding_period_hours=holding_hours
            )
        
            self.signal_performance[signal_id] = perf
            del self.active_signals[signal_id]
        except Exception as e:
            logger.error(f"Error in record_signal_exit: {e}")
            raise
    
    def _update_signal_performance(self, trade: Trade):
        """Update signal with trade info"""
        try:
            if trade.signal_id in self.active_signals:
                self.active_signals[trade.signal_id]['trades'].append({
                    'trade_id': trade.trade_id,
                    'side': trade.side,
                    'quantity': trade.quantity,
                    'price': trade.price,
                    'commission': trade.commission,
                    'slippage': trade.slippage
                })
        except Exception as e:
            logger.error(f"Error in _update_signal_performance: {e}")
            raise
    
    def record_daily_return(self, portfolio_return: float, benchmark_return: float = 0.0):
        """
        Record daily returns for attribution
        
        Args:
            portfolio_return: Portfolio daily return
            benchmark_return: Benchmark daily return
        """
        try:
            self.daily_returns.append(portfolio_return)
            self.benchmark_returns.append(benchmark_return)
        except Exception as e:
            logger.error(f"Error in record_daily_return: {e}")
            raise
    
    def record_factor_returns(self, factor_returns: Dict[str, float]):
        """
        Record factor returns for factor attribution
        
        Args:
            factor_returns: Dictionary of {factor: return}
        """
        try:
            for factor, ret in factor_returns.items():
                if factor in self.factor_returns:
                    self.factor_returns[factor].append(ret)
        except Exception as e:
            logger.error(f"Error in record_factor_returns: {e}")
            raise
    
    def get_strategy_performance(self,
                                strategy: str,
                                start_date: Optional[datetime] = None,
                                end_date: Optional[datetime] = None) -> StrategyPerformance:
        """
        Get performance metrics for a strategy
        
        Args:
            strategy: Strategy name
            start_date: Start of period
            end_date: End of period
            
        Returns:
            StrategyPerformance object
        """
        # Filter trades by date
        try:
            trades = self.strategy_trades.get(strategy, [])
        
            if start_date:
                trades = [t for t in trades if t.timestamp >= start_date]
            if end_date:
                trades = [t for t in trades if t.timestamp <= end_date]
        
            if not trades:
                return self._empty_strategy_performance(strategy)
        
            # Calculate P&L
            pnl_list = self.strategy_pnl.get(strategy, [])
            gross_pnl = sum(pnl_list)
        
            total_commissions = sum(t.commission for t in trades)
            total_slippage = sum(t.slippage for t in trades)
            total_costs = total_commissions + total_slippage
        
            net_pnl = gross_pnl - total_costs
        
            # Calculate unrealized P&L
            unrealized_pnl = sum(
                pos.unrealized_pnl for pos in self.positions.values()
                if pos.strategy == strategy
            )
        
            # Calculate returns
            returns = list(self.strategy_returns.get(strategy, []))
        
            if returns:
                gross_return = np.sum(returns)
                net_return = gross_return - (total_costs / max(1, abs(gross_pnl)))
                volatility = np.std(returns) * np.sqrt(252)
            
                # Sharpe ratio
                excess_returns = np.array(returns) - self.risk_free_rate / 252
                sharpe = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252) if np.std(excess_returns) > 0 else 0
            
                # Sortino ratio
                downside_returns = [r for r in returns if r < 0]
                downside_std = np.std(downside_returns) * np.sqrt(252) if downside_returns else volatility
                sortino = (np.mean(returns) * 252 - self.risk_free_rate) / downside_std if downside_std > 0 else 0
            
                # Max drawdown
                cumulative = np.cumprod(1 + np.array(returns))
                running_max = np.maximum.accumulate(cumulative)
                drawdown = (cumulative - running_max) / running_max
                max_drawdown = abs(drawdown.min())
            else:
                gross_return = net_return = volatility = sharpe = sortino = max_drawdown = 0.0
        
            # Win/loss analysis
            wins = [p for p in pnl_list if p > 0]
            losses = [p for p in pnl_list if p < 0]
        
            win_rate = len(wins) / len(pnl_list) if pnl_list else 0
            avg_win = np.mean(wins) if wins else 0
            avg_loss = np.mean(losses) if losses else 0
            profit_factor = abs(sum(wins) / sum(losses)) if losses and sum(losses) != 0 else float('inf')
        
            # Alpha/Beta calculation
            alpha, beta, ir = self._calculate_alpha_beta(returns)
        
            return StrategyPerformance(
                strategy_name=strategy,
                period_start=trades[0].timestamp if trades else datetime.now(),
                period_end=trades[-1].timestamp if trades else datetime.now(),
                gross_pnl=gross_pnl,
                net_pnl=net_pnl,
                realized_pnl=gross_pnl,
                unrealized_pnl=unrealized_pnl,
                total_commissions=total_commissions,
                total_slippage=total_slippage,
                total_costs=total_costs,
                gross_return=gross_return,
                net_return=net_return,
                volatility=volatility,
                sharpe_ratio=sharpe,
                sortino_ratio=sortino,
                max_drawdown=max_drawdown,
                num_trades=len(trades),
                win_rate=win_rate,
                avg_win=avg_win,
                avg_loss=avg_loss,
                profit_factor=profit_factor,
                alpha=alpha,
                beta=beta,
                information_ratio=ir
            )
        except Exception as e:
            logger.error(f"Error in get_strategy_performance: {e}")
            raise
    
    def _calculate_alpha_beta(self, returns: List[float]) -> Tuple[float, float, float]:
        """Calculate alpha, beta, and information ratio"""
        try:
            if len(returns) < 10 or len(self.benchmark_returns) < 10:
                return 0.0, 1.0, 0.0
        
            # Align returns
            n = min(len(returns), len(self.benchmark_returns))
            port_returns = np.array(list(returns)[-n:])
            bench_returns = np.array(list(self.benchmark_returns)[-n:])
        
            # Calculate beta
            covariance = np.cov(port_returns, bench_returns)[0, 1]
            variance = np.var(bench_returns)
            beta = covariance / variance if variance > 0 else 1.0
        
            # Calculate alpha (annualized)
            alpha = (np.mean(port_returns) - beta * np.mean(bench_returns)) * 252
        
            # Information ratio
            active_returns = port_returns - bench_returns
            tracking_error = np.std(active_returns) * np.sqrt(252)
            ir = np.mean(active_returns) * 252 / tracking_error if tracking_error > 0 else 0
        
            return alpha, beta, ir
        except Exception as e:
            logger.error(f"Error in _calculate_alpha_beta: {e}")
            raise
    
    def get_factor_attribution(self) -> List[FactorAttribution]:
        """
        Get factor-based attribution
        
        Returns:
            List of FactorAttribution objects
        """
        try:
            if len(self.daily_returns) < 20:
                return []
        
            port_returns = np.array(list(self.daily_returns))
            attributions = []
        
            total_return = np.sum(port_returns)
            explained_return = 0.0
        
            for factor_name, factor_rets in self.factor_returns.items():
                if len(factor_rets) < 20:
                    continue
            
                factor_returns_arr = np.array(list(factor_rets)[-len(port_returns):])
            
                if len(factor_returns_arr) != len(port_returns):
                    continue
            
                # Calculate factor exposure (beta)
                covariance = np.cov(port_returns, factor_returns_arr)[0, 1]
                variance = np.var(factor_returns_arr)
                exposure = covariance / variance if variance > 0 else 0
            
                # Factor contribution
                factor_return = np.sum(factor_returns_arr)
                contribution = exposure * factor_return
                explained_return += contribution
            
                contribution_pct = contribution / total_return if total_return != 0 else 0
            
                attributions.append(FactorAttribution(
                    factor_name=factor_name,
                    exposure=exposure,
                    factor_return=factor_return,
                    contribution=contribution,
                    contribution_pct=contribution_pct
                ))
        
            # Add alpha (unexplained return)
            alpha = total_return - explained_return
            attributions.append(FactorAttribution(
                factor_name='alpha',
                exposure=1.0,
                factor_return=alpha,
                contribution=alpha,
                contribution_pct=alpha / total_return if total_return != 0 else 0
            ))
        
            return attributions
        except Exception as e:
            logger.error(f"Error in get_factor_attribution: {e}")
            raise
    
    def get_brinson_attribution(self,
                               portfolio_weights: Dict[str, float],
                               benchmark_weights: Dict[str, float],
                               portfolio_returns: Dict[str, float],
                               benchmark_returns: Dict[str, float]) -> List[BrinsonAttribution]:
        """
        Calculate Brinson-Fachler attribution
        
        Args:
            portfolio_weights: Portfolio weights by segment
            benchmark_weights: Benchmark weights by segment
            portfolio_returns: Portfolio returns by segment
            benchmark_returns: Benchmark returns by segment
            
        Returns:
            List of BrinsonAttribution objects
        """
        try:
            segments = set(portfolio_weights.keys()) | set(benchmark_weights.keys())
        
            # Calculate benchmark total return
            bench_total = sum(
                benchmark_weights.get(s, 0) * benchmark_returns.get(s, 0)
                for s in segments
            )
        
            attributions = []
        
            for segment in segments:
                pw = portfolio_weights.get(segment, 0)
                bw = benchmark_weights.get(segment, 0)
                pr = portfolio_returns.get(segment, 0)
                br = benchmark_returns.get(segment, 0)
            
                # Brinson-Fachler effects
                allocation = (pw - bw) * (br - bench_total)
                selection = bw * (pr - br)
                interaction = (pw - bw) * (pr - br)
                total = allocation + selection + interaction
            
                attributions.append(BrinsonAttribution(
                    segment=segment,
                    portfolio_weight=pw,
                    benchmark_weight=bw,
                    portfolio_return=pr,
                    benchmark_return=br,
                    allocation_effect=allocation,
                    selection_effect=selection,
                    interaction_effect=interaction,
                    total_effect=total
                ))
        
            return attributions
        except Exception as e:
            logger.error(f"Error in get_brinson_attribution: {e}")
            raise
    
    def get_signal_rankings(self,
                           top_n: int = 10,
                           metric: str = 'net_pnl') -> List[SignalPerformance]:
        """
        Get top/bottom performing signals
        
        Args:
            top_n: Number of signals to return
            metric: Metric to rank by
            
        Returns:
            List of SignalPerformance objects
        """
        try:
            signals = list(self.signal_performance.values())
        
            if metric == 'net_pnl':
                signals.sort(key=lambda x: x.net_pnl, reverse=True)
            elif metric == 'return_pct':
                signals.sort(key=lambda x: x.return_pct, reverse=True)
            elif metric == 'sharpe':
                # Approximate Sharpe from return and holding period
                signals.sort(key=lambda x: x.return_pct / max(0.01, x.holding_period_hours / 24), reverse=True)
        
            return signals[:top_n]
        except Exception as e:
            logger.error(f"Error in get_signal_rankings: {e}")
            raise
    
    def get_strategy_rankings(self) -> List[StrategyPerformance]:
        """Get all strategies ranked by Sharpe ratio"""
        try:
            strategies = list(self.strategy_trades.keys())
            performances = [self.get_strategy_performance(s) for s in strategies]
            performances.sort(key=lambda x: x.sharpe_ratio, reverse=True)
            return performances
        except Exception as e:
            logger.error(f"Error in get_strategy_rankings: {e}")
            raise
    
    def get_transaction_cost_analysis(self) -> Dict[str, Any]:
        """
        Get transaction cost analysis
        
        Returns:
            Dictionary with TCA metrics
        """
        try:
            if not self.trades:
                return {'message': 'No trades to analyze'}
        
            total_value = sum(t.value for t in self.trades)
            total_commission = sum(t.commission for t in self.trades)
            total_slippage = sum(t.slippage for t in self.trades)
            total_cost = total_commission + total_slippage
        
            # By strategy
            strategy_costs = defaultdict(lambda: {'value': 0, 'commission': 0, 'slippage': 0})
            for trade in self.trades:
                strategy_costs[trade.strategy]['value'] += trade.value
                strategy_costs[trade.strategy]['commission'] += trade.commission
                strategy_costs[trade.strategy]['slippage'] += trade.slippage
        
            return {
                'total_trades': len(self.trades),
                'total_value': round(total_value, 2),
                'total_commission': round(total_commission, 2),
                'total_slippage': round(total_slippage, 2),
                'total_cost': round(total_cost, 2),
                'cost_bps': round(total_cost / total_value * 10000, 2) if total_value > 0 else 0,
                'avg_commission_per_trade': round(total_commission / len(self.trades), 2),
                'avg_slippage_per_trade': round(total_slippage / len(self.trades), 2),
                'by_strategy': {
                    strategy: {
                        'value': round(data['value'], 2),
                        'cost_bps': round((data['commission'] + data['slippage']) / data['value'] * 10000, 2) if data['value'] > 0 else 0
                    }
                    for strategy, data in strategy_costs.items()
                }
            }
        except Exception as e:
            logger.error(f"Error in get_transaction_cost_analysis: {e}")
            raise
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get portfolio summary"""
        try:
            total_value = sum(pos.market_value for pos in self.positions.values())
            total_unrealized = sum(pos.unrealized_pnl for pos in self.positions.values())
        
            return {
                'num_positions': len(self.positions),
                'total_value': round(total_value, 2),
                'total_unrealized_pnl': round(total_unrealized, 2),
                'total_realized_pnl': round(self.total_pnl, 2),
                'total_pnl': round(self.total_pnl + total_unrealized, 2),
                'total_trades': self.total_trades,
                'positions': [pos.to_dict() for pos in self.positions.values()]
            }
        except Exception as e:
            logger.error(f"Error in get_portfolio_summary: {e}")
            raise
    
    def _empty_strategy_performance(self, strategy: str) -> StrategyPerformance:
        """Return empty performance for strategy with no trades"""
        try:
            now = datetime.now()
            return StrategyPerformance(
                strategy_name=strategy,
                period_start=now,
                period_end=now,
                gross_pnl=0, net_pnl=0, realized_pnl=0, unrealized_pnl=0,
                total_commissions=0, total_slippage=0, total_costs=0,
                gross_return=0, net_return=0,
                volatility=0, sharpe_ratio=0, sortino_ratio=0, max_drawdown=0,
                num_trades=0, win_rate=0, avg_win=0, avg_loss=0, profit_factor=0,
                alpha=0, beta=1, information_ratio=0
            )
        except Exception as e:
            logger.error(f"Error in _empty_strategy_performance: {e}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get system statistics"""
        return {
            'total_trades': self.total_trades,
            'total_pnl': round(self.total_pnl, 2),
            'num_strategies': len(self.strategy_trades),
            'num_positions': len(self.positions),
            'num_closed_positions': len(self.closed_positions),
            'num_signals_tracked': len(self.signal_performance),
            'daily_returns_recorded': len(self.daily_returns)
        }


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create attribution system
    attribution = PerformanceAttributionSystem({
        'risk_free_rate': 0.04
    })
    
    # Simulate trades
    strategies = ['momentum', 'mean_reversion', 'trend_following']
    symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
    
    logger.info("\n=== Recording Trades ===")
    for i in range(50):
        strategy = np.random.choice(strategies)
        symbol = np.random.choice(symbols)
        side = np.random.choice(['BUY', 'SELL'])
        quantity = np.random.randint(100, 1000)
        price = 100 + np.random.randn() * 10
        
        trade = Trade(
            trade_id=f"T{i:04d}",
            timestamp=datetime.now() - timedelta(days=np.random.randint(0, 30)),
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
            strategy=strategy,
            signal_id=f"S{i:04d}",
            commission=quantity * 0.01,
            slippage=quantity * price * 0.0001
        )
        
        attribution.record_trade(trade)
        
        # Record signal
        attribution.record_signal_entry(
            signal_id=f"S{i:04d}",
            signal_type='technical',
            strategy=strategy,
            symbol=symbol,
            direction=side,
            entry_price=price,
            confidence=np.random.uniform(0.5, 0.9)
        )
        
        # Close signal
        exit_price = price * (1 + np.random.randn() * 0.02)
        attribution.record_signal_exit(
            signal_id=f"S{i:04d}",
            exit_price=exit_price,
            hit_take_profit=exit_price > price if side == 'BUY' else exit_price < price
        )
    
    # Record daily returns
    for i in range(60):
        attribution.record_daily_return(
            portfolio_return=np.random.randn() * 0.01,
            benchmark_return=np.random.randn() * 0.008
        )
        
        attribution.record_factor_returns({
            'market': np.random.randn() * 0.01,
            'size': np.random.randn() * 0.005,
            'value': np.random.randn() * 0.005,
            'momentum': np.random.randn() * 0.005,
            'volatility': np.random.randn() * 0.003
        })
    
    # Get strategy performance
    logger.info("\n=== Strategy Performance ===")
    rankings = attribution.get_strategy_rankings()
    for perf in rankings:
        logger.info(f"\n{perf.strategy_name}:")
        logger.info(f"  Net P&L: ${perf.net_pnl:,.2f}")
        logger.info(f"  Sharpe: {perf.sharpe_ratio:.2f}")
        logger.info(f"  Win Rate: {perf.win_rate:.1%}")
        logger.info(f"  Trades: {perf.num_trades}")
    
    # Get factor attribution
    logger.info("\n=== Factor Attribution ===")
    factors = attribution.get_factor_attribution()
    for factor in factors:
        logger.info(f"  {factor.factor_name}: {factor.contribution:.4f} ({factor.contribution_pct:.1%})")
    
    # Get TCA
    logger.info("\n=== Transaction Cost Analysis ===")
    tca = attribution.get_transaction_cost_analysis()
    logger.info(f"  Total Cost: ${tca['total_cost']:,.2f}")
    logger.info(f"  Cost (bps): {tca['cost_bps']:.2f}")
    
    # Get top signals
    logger.info("\n=== Top Signals ===")
    top_signals = attribution.get_signal_rankings(top_n=5)
    for sig in top_signals:
        logger.info(f"  {sig.signal_id}: ${sig.net_pnl:,.2f} ({sig.return_pct:.2%})")
    
    # Portfolio summary
    logger.info("\n=== Portfolio Summary ===")
    summary = attribution.get_portfolio_summary()
    logger.info(f"  Positions: {summary['num_positions']}")
    logger.info(f"  Total P&L: ${summary['total_pnl']:,.2f}")
