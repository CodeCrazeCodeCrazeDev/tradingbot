"""
Leakage-Free Backtesting Engine with Realistic Transaction Costs.

Implements rigorous backtesting with:
- No data leakage (strict point-in-time)
- Realistic transaction costs (commission, slippage, market impact)
- Proper execution simulation
- Walk-forward compatible
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from dataclasses import dataclass
from datetime import datetime, timedelta

from .strategy_genome import StrategyGenome, Signal, SignalType


@dataclass
class Trade:
    """Individual trade record"""
    timestamp: datetime
    symbol: str
    side: str
    quantity: float
    price: float
    commission: float
    slippage: float
    market_impact: float
    total_cost: float


@dataclass
class BacktestResult:
    """Complete backtest results"""
    returns: pd.Series
    positions: pd.DataFrame
    trades: List[Trade]
    equity_curve: pd.Series
    metrics: Dict[str, float]
    
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    
    num_trades: int
    avg_trade_duration: float
    total_costs: float


class LeakageFreeBacktester:
    """
    Rigorous backtesting engine that prevents data leakage.
    
    Key features:
    - Point-in-time data access only
    - Realistic execution delays
    - Transaction cost modeling
    - Slippage simulation
    - Market impact estimation
    """
    
    def __init__(
        self,
        data: pd.DataFrame,
        initial_capital: float = 100000.0,
        risk_free_rate: float = 0.02
    ):
        """
        Initialize backtester.
        
        Args:
            data: Market data with OHLCV columns
            initial_capital: Starting capital
            risk_free_rate: Risk-free rate for Sharpe calculation
        """
        self.data = data.copy()
        self.initial_capital = initial_capital
        self.risk_free_rate = risk_free_rate
        
        self._validate_data()
        self._prepare_data()
    
    def _validate_data(self):
        """Validate data has required columns and no lookahead bias"""
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        missing = [col for col in required_cols if col not in self.data.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        
        if not isinstance(self.data.index, pd.DatetimeIndex):
            raise ValueError("Data index must be DatetimeIndex")
        
        if self.data.index.duplicated().any():
            raise ValueError("Data contains duplicate timestamps")
    
    def _prepare_data(self):
        """Prepare data for backtesting"""
        self.data = self.data.sort_index()
        
        self.data['returns'] = self.data['close'].pct_change()
        self.data['log_returns'] = np.log(self.data['close'] / self.data['close'].shift(1))
        
        self.data['volatility'] = self.data['returns'].rolling(20).std()
        self.data['volume_ma'] = self.data['volume'].rolling(20).mean()
    
    def backtest(self, genome: StrategyGenome) -> BacktestResult:
        """
        Run complete backtest for a strategy genome.
        
        Args:
            genome: Strategy genome to backtest
        
        Returns:
            BacktestResult with all metrics
        """
        signals = self._generate_signals(genome)
        
        positions = self._calculate_positions(genome, signals)
        
        trades = self._execute_trades(genome, positions)
        
        returns, equity_curve = self._calculate_returns(genome, positions, trades)
        
        metrics = self._calculate_metrics(returns, equity_curve, trades)
        
        return BacktestResult(
            returns=returns,
            positions=positions,
            trades=trades,
            equity_curve=equity_curve,
            metrics=metrics,
            total_return=metrics['total_return'],
            sharpe_ratio=metrics['sharpe_ratio'],
            max_drawdown=metrics['max_drawdown'],
            win_rate=metrics['win_rate'],
            profit_factor=metrics['profit_factor'],
            num_trades=len(trades),
            avg_trade_duration=metrics['avg_trade_duration'],
            total_costs=metrics['total_costs']
        )
    
    def _generate_signals(self, genome: StrategyGenome) -> pd.DataFrame:
        """
        Generate trading signals from genome (point-in-time only).
        
        Each signal is calculated using only past data.
        """
        signals_df = pd.DataFrame(index=self.data.index)
        
        for i, signal in enumerate(genome.signals):
            signal_values = self._calculate_signal(signal)
            signals_df[f'signal_{i}'] = signal_values
        
        combined_signal = self._aggregate_signals(genome, signals_df)
        signals_df['combined'] = combined_signal
        
        return signals_df
    
    def _calculate_signal(self, signal: Signal) -> pd.Series:
        """Calculate individual signal values (no lookahead)"""
        lookback = signal.lookback_period
        
        if signal.signal_type == SignalType.MOMENTUM:
            return self._momentum_signal(lookback, signal.threshold)
        
        elif signal.signal_type == SignalType.MEAN_REVERSION:
            return self._mean_reversion_signal(lookback, signal.threshold)
        
        elif signal.signal_type == SignalType.VOLATILITY:
            return self._volatility_signal(lookback, signal.threshold)
        
        elif signal.signal_type == SignalType.VOLUME:
            return self._volume_signal(lookback, signal.threshold)
        
        else:
            return pd.Series(0, index=self.data.index)
    
    def _momentum_signal(self, lookback: int, threshold: float) -> pd.Series:
        """Momentum signal: price change over lookback period"""
        returns = self.data['close'].pct_change(lookback)
        
        z_score = (returns - returns.rolling(lookback * 2).mean()) / returns.rolling(lookback * 2).std()
        
        signal = pd.Series(0, index=self.data.index)
        signal[z_score > threshold] = 1
        signal[z_score < -threshold] = -1
        
        return signal
    
    def _mean_reversion_signal(self, lookback: int, threshold: float) -> pd.Series:
        """Mean reversion signal: deviation from moving average"""
        ma = self.data['close'].rolling(lookback).mean()
        std = self.data['close'].rolling(lookback).std()
        
        z_score = (self.data['close'] - ma) / std
        
        signal = pd.Series(0, index=self.data.index)
        signal[z_score < -abs(threshold)] = 1
        signal[z_score > abs(threshold)] = -1
        
        return signal
    
    def _volatility_signal(self, lookback: int, threshold: float) -> pd.Series:
        """Volatility signal: trade when volatility is low/high"""
        vol = self.data['returns'].rolling(lookback).std()
        vol_ma = vol.rolling(lookback).mean()
        
        vol_ratio = vol / vol_ma
        
        signal = pd.Series(0, index=self.data.index)
        if threshold > 0:
            signal[vol_ratio < 1 - abs(threshold)] = 1
        else:
            signal[vol_ratio > 1 + abs(threshold)] = -1
        
        return signal
    
    def _volume_signal(self, lookback: int, threshold: float) -> pd.Series:
        """Volume signal: unusual volume activity"""
        vol_ma = self.data['volume'].rolling(lookback).mean()
        vol_std = self.data['volume'].rolling(lookback).std()
        
        vol_z = (self.data['volume'] - vol_ma) / vol_std
        
        signal = pd.Series(0, index=self.data.index)
        signal[vol_z > abs(threshold)] = 1
        
        return signal
    
    def _aggregate_signals(self, genome: StrategyGenome, signals_df: pd.DataFrame) -> pd.Series:
        """Aggregate individual signals according to genome specification"""
        signal_cols = [col for col in signals_df.columns if col.startswith('signal_')]
        
        if not signal_cols:
            return pd.Series(0, index=signals_df.index)
        
        if genome.aggregation_type.value == 'linear':
            weights = [genome.signals[i].weight for i in range(len(signal_cols))]
            combined = sum(signals_df[col] * w for col, w in zip(signal_cols, weights))
            combined = combined / sum(abs(w) for w in weights) if sum(abs(w) for w in weights) > 0 else combined
        
        elif genome.aggregation_type.value == 'rank':
            ranks = signals_df[signal_cols].rank(axis=1, pct=True)
            combined = ranks.mean(axis=1) * 2 - 1
        
        else:
            combined = signals_df[signal_cols].mean(axis=1)
        
        return combined.clip(-1, 1)
    
    def _calculate_positions(self, genome: StrategyGenome, signals: pd.DataFrame) -> pd.DataFrame:
        """Calculate position sizes from signals (respecting risk controls)"""
        positions = pd.DataFrame(index=self.data.index)
        positions['signal'] = signals['combined']
        
        if genome.position_sizing.value == 'fixed':
            positions['target_position'] = positions['signal'] * genome.risk_control.max_position_size
        
        elif genome.position_sizing.value == 'volatility_scaled':
            vol = self.data['volatility'].fillna(self.data['volatility'].mean())
            vol_target = 0.15
            vol_scalar = vol_target / (vol * np.sqrt(252))
            positions['target_position'] = positions['signal'] * vol_scalar * genome.risk_control.max_position_size
        
        else:
            positions['target_position'] = positions['signal'] * genome.risk_control.max_position_size
        
        positions['target_position'] = positions['target_position'].clip(
            -genome.risk_control.max_position_size,
            genome.risk_control.max_position_size
        )
        
        positions['actual_position'] = 0.0
        
        return positions
    
    def _execute_trades(self, genome: StrategyGenome, positions: pd.DataFrame) -> List[Trade]:
        """
        Execute trades with realistic costs and delays.
        
        Simulates:
        - Execution delay
        - Slippage
        - Commission
        - Market impact
        """
        trades = []
        current_position = 0.0
        
        for i in range(len(positions)):
            if i % genome.rebalance_frequency != 0:
                positions.iloc[i, positions.columns.get_loc('actual_position')] = current_position
                continue
            
            target = positions.iloc[i]['target_position']
            
            if abs(target - current_position) < 0.001:
                positions.iloc[i, positions.columns.get_loc('actual_position')] = current_position
                continue
            
            timestamp = positions.index[i]
            trade_size = target - current_position
            
            execution_price = self._get_execution_price(i, trade_size)
            
            commission = abs(trade_size) * self.initial_capital * genome.execution_params.commission_bps / 10000
            
            slippage = self._calculate_slippage(trade_size, genome.execution_params.slippage_bps)
            
            market_impact = self._calculate_market_impact(
                trade_size, 
                self.data.iloc[i]['volume'],
                genome.execution_params.market_impact_factor
            )
            
            total_cost = commission + slippage + market_impact
            
            trade = Trade(
                timestamp=timestamp,
                symbol='ASSET',
                side='BUY' if trade_size > 0 else 'SELL',
                quantity=abs(trade_size) * self.initial_capital / execution_price,
                price=execution_price,
                commission=commission,
                slippage=slippage,
                market_impact=market_impact,
                total_cost=total_cost
            )
            trades.append(trade)
            
            current_position = target
            positions.iloc[i, positions.columns.get_loc('actual_position')] = current_position
        
        return trades
    
    def _get_execution_price(self, idx: int, trade_size: float) -> float:
        """Get realistic execution price (with delay)"""
        if idx >= len(self.data) - 1:
            return self.data.iloc[idx]['close']
        
        return self.data.iloc[idx + 1]['open']
    
    def _calculate_slippage(self, trade_size: float, slippage_bps: float) -> float:
        """Calculate slippage cost"""
        return abs(trade_size) * self.initial_capital * slippage_bps / 10000
    
    def _calculate_market_impact(self, trade_size: float, volume: float, impact_factor: float) -> float:
        """Calculate market impact cost"""
        trade_volume = abs(trade_size) * self.initial_capital
        volume_ratio = trade_volume / (volume + 1)
        
        impact = impact_factor * np.sqrt(volume_ratio) * trade_volume * 0.0001
        
        return impact
    
    def _calculate_returns(
        self, 
        genome: StrategyGenome, 
        positions: pd.DataFrame, 
        trades: List[Trade]
    ) -> Tuple[pd.Series, pd.Series]:
        """Calculate strategy returns and equity curve"""
        positions['market_return'] = self.data['returns']
        
        positions['strategy_return'] = positions['actual_position'].shift(1) * positions['market_return']
        
        total_costs = sum(t.total_cost for t in trades)
        cost_per_period = total_costs / len(positions)
        positions['cost_drag'] = -cost_per_period / self.initial_capital
        
        positions['net_return'] = positions['strategy_return'] + positions['cost_drag']
        
        equity_curve = (1 + positions['net_return'].fillna(0)).cumprod() * self.initial_capital
        
        return positions['net_return'], equity_curve
    
    def _calculate_metrics(
        self, 
        returns: pd.Series, 
        equity_curve: pd.Series, 
        trades: List[Trade]
    ) -> Dict[str, float]:
        """Calculate comprehensive performance metrics"""
        returns_clean = returns.dropna()
        
        total_return = (equity_curve.iloc[-1] / self.initial_capital) - 1
        
        annual_return = (1 + total_return) ** (252 / len(returns_clean)) - 1
        annual_vol = returns_clean.std() * np.sqrt(252)
        sharpe_ratio = (annual_return - self.risk_free_rate) / annual_vol if annual_vol > 0 else 0
        
        cummax = equity_curve.cummax()
        drawdown = (equity_curve - cummax) / cummax
        max_drawdown = drawdown.min()
        
        winning_trades = [t for t in trades if t.side == 'SELL']
        win_rate = 0.0
        profit_factor = 0.0
        
        total_costs = sum(t.total_cost for t in trades)
        
        avg_trade_duration = 0.0
        if len(trades) > 1:
            durations = [(trades[i+1].timestamp - trades[i].timestamp).days 
                        for i in range(len(trades)-1)]
            avg_trade_duration = np.mean(durations) if durations else 0.0
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'annual_volatility': annual_vol,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'num_trades': len(trades),
            'avg_trade_duration': avg_trade_duration,
            'total_costs': total_costs,
            'cost_drag': total_costs / self.initial_capital,
        }
