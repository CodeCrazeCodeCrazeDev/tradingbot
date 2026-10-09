"""
Self-Evolving Researcher Module
==============================
Autonomous strategy research, generation, backtesting, and deployment system.

Features:
- Generate strategy candidates using genetic programming
- Backtest on multi-year data with walk-forward optimization
- Stress test across regime shifts, crashes, and volatility spikes
- Rank by Sharpe, drawdown, skew, tail risk, and other metrics
- Promote winners to production, kill losers automatically
- Continuous evolution and improvement cycle

Author: AlphaAlgo Research Team
"""

import asyncio
import logging
import hashlib
import json
import pickle
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from collections import deque
import threading
import uuid

import numpy as np
import pandas as pd

try:
    from scipy import stats
    from scipy.optimize import minimize
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
    from sklearn.model_selection import TimeSeriesSplit
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

logger = logging.getLogger(__name__)


class StrategyStatus(Enum):
    """Strategy lifecycle status"""
    CANDIDATE = auto()      # Newly generated
    BACKTESTING = auto()    # Under evaluation
    STRESS_TESTING = auto() # Stress testing phase
    VALIDATED = auto()      # Passed all tests
    PROMOTED = auto()       # Deployed to production
    DEMOTED = auto()        # Removed from production
    KILLED = auto()         # Permanently disabled
    QUARANTINED = auto()    # Under investigation


class RegimeType(Enum):
    """Market regime types for stress testing"""
    NORMAL = auto()
    TRENDING_UP = auto()
    TRENDING_DOWN = auto()
    HIGH_VOLATILITY = auto()
    LOW_VOLATILITY = auto()
    CRASH = auto()
    RECOVERY = auto()
    RANGING = auto()


@dataclass
class StrategyGene:
    """Genetic representation of a strategy component"""
    gene_type: str  # 'indicator', 'condition', 'action', 'filter'
    parameters: Dict[str, Any]
    weight: float = 1.0
    mutation_rate: float = 0.1
    
    def mutate(self) -> 'StrategyGene':
        """Create mutated copy of gene"""
        new_params = {}
        for key, value in self.parameters.items():
            if isinstance(value, (int, float)):
                # Gaussian mutation
                mutation = np.random.normal(0, abs(value) * self.mutation_rate)
                new_value = value + mutation
                # Keep same type
                new_params[key] = type(value)(new_value) if isinstance(value, int) else new_value
            elif isinstance(value, bool):
                # Flip with probability
                new_params[key] = not value if random.random() < self.mutation_rate else value
            elif isinstance(value, str):
                new_params[key] = value  # Don't mutate strings
            else:
                new_params[key] = value
        
        return StrategyGene(
            gene_type=self.gene_type,
            parameters=new_params,
            weight=self.weight * (1 + np.random.normal(0, self.mutation_rate)),
            mutation_rate=self.mutation_rate
        )


@dataclass
class StrategyDNA:
    """Complete genetic representation of a strategy"""
    strategy_id: str
    name: str
    genes: List[StrategyGene]
    generation: int = 0
    parent_ids: List[str] = field(default_factory=list)
    creation_time: datetime = field(default_factory=datetime.now)
    
    def crossover(self, other: 'StrategyDNA') -> 'StrategyDNA':
        """Create offspring through crossover"""
        # Single-point crossover
        crossover_point = random.randint(1, min(len(self.genes), len(other.genes)) - 1)
        
        new_genes = self.genes[:crossover_point] + other.genes[crossover_point:]
        
        return StrategyDNA(
            strategy_id=str(uuid.uuid4())[:8],
            name=f"Offspring_{self.name[:4]}_{other.name[:4]}",
            genes=new_genes,
            generation=max(self.generation, other.generation) + 1,
            parent_ids=[self.strategy_id, other.strategy_id]
        )
    
    def mutate(self) -> 'StrategyDNA':
        """Create mutated copy"""
        new_genes = [gene.mutate() for gene in self.genes]
        
        return StrategyDNA(
            strategy_id=str(uuid.uuid4())[:8],
            name=f"Mutant_{self.name}",
            genes=new_genes,
            generation=self.generation + 1,
            parent_ids=[self.strategy_id]
        )


@dataclass
class BacktestResult:
    """Comprehensive backtest results"""
    strategy_id: str
    start_date: datetime
    end_date: datetime
    
    # Core metrics
    total_return: float = 0.0
    annualized_return: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    
    # Risk metrics
    max_drawdown: float = 0.0
    avg_drawdown: float = 0.0
    drawdown_duration: int = 0  # days
    volatility: float = 0.0
    downside_volatility: float = 0.0
    
    # Distribution metrics
    skewness: float = 0.0
    kurtosis: float = 0.0
    var_95: float = 0.0
    cvar_95: float = 0.0
    tail_ratio: float = 0.0
    
    # Trade metrics
    total_trades: int = 0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    max_consecutive_losses: int = 0
    
    # Stability metrics
    stability_score: float = 0.0  # Rolling Sharpe consistency
    regime_robustness: float = 0.0  # Performance across regimes
    
    # Raw data
    equity_curve: List[float] = field(default_factory=list)
    returns: List[float] = field(default_factory=list)
    trades: List[Dict] = field(default_factory=list)


@dataclass
class StressTestResult:
    """Stress test results across different scenarios"""
    strategy_id: str
    scenario_name: str
    regime_type: RegimeType
    
    # Performance under stress
    return_during_stress: float = 0.0
    max_drawdown_during_stress: float = 0.0
    recovery_time: int = 0  # days
    
    # Behavior metrics
    position_changes: int = 0
    stop_loss_hits: int = 0
    margin_calls: int = 0
    
    # Risk metrics
    var_breach_count: int = 0
    correlation_breakdown: bool = False
    liquidity_issues: bool = False
    
    passed: bool = False
    score: float = 0.0


@dataclass
class StrategyCandidate:
    """Complete strategy candidate with all evaluation data"""
    dna: StrategyDNA
    status: StrategyStatus = StrategyStatus.CANDIDATE
    
    # Evaluation results
    backtest_results: List[BacktestResult] = field(default_factory=list)
    stress_test_results: List[StressTestResult] = field(default_factory=list)
    
    # Ranking scores
    composite_score: float = 0.0
    sharpe_rank: int = 0
    drawdown_rank: int = 0
    stability_rank: int = 0
    tail_risk_rank: int = 0
    
    # Lifecycle
    promoted_at: Optional[datetime] = None
    demoted_at: Optional[datetime] = None
    kill_reason: Optional[str] = None
    
    # Live performance (after promotion)
    live_trades: int = 0
    live_pnl: float = 0.0
    live_sharpe: float = 0.0


class StrategyGenerator:
    """Generates strategy candidates using genetic programming"""
    
    # Building blocks for strategy generation
    INDICATORS = [
        {'name': 'SMA', 'params': {'period': (5, 200)}},
        {'name': 'EMA', 'params': {'period': (5, 200)}},
        {'name': 'RSI', 'params': {'period': (7, 21)}},
        {'name': 'MACD', 'params': {'fast': (8, 15), 'slow': (20, 30), 'signal': (7, 12)}},
        {'name': 'BB', 'params': {'period': (15, 30), 'std': (1.5, 3.0)}},
        {'name': 'ATR', 'params': {'period': (10, 20)}},
        {'name': 'ADX', 'params': {'period': (10, 20)}},
        {'name': 'VWAP', 'params': {}},
        {'name': 'OBV', 'params': {}},
        {'name': 'MFI', 'params': {'period': (10, 20)}},
        {'name': 'CCI', 'params': {'period': (14, 28)}},
        {'name': 'STOCH', 'params': {'k_period': (10, 20), 'd_period': (3, 5)}},
        {'name': 'WILLR', 'params': {'period': (10, 20)}},
        {'name': 'ROC', 'params': {'period': (10, 20)}},
        {'name': 'MOMENTUM', 'params': {'period': (10, 20)}},
    ]
    
    CONDITIONS = [
        'crossover_above', 'crossover_below',
        'greater_than', 'less_than',
        'between', 'outside',
        'increasing', 'decreasing',
        'divergence_bullish', 'divergence_bearish',
    ]
    
    FILTERS = [
        {'name': 'trend_filter', 'params': {'period': (50, 200)}},
        {'name': 'volatility_filter', 'params': {'min_atr': (0.5, 2.0)}},
        {'name': 'volume_filter', 'params': {'min_ratio': (1.0, 3.0)}},
        {'name': 'time_filter', 'params': {'start_hour': (0, 12), 'end_hour': (12, 24)}},
        {'name': 'regime_filter', 'params': {'allowed_regimes': ['trending', 'ranging']}},
    ]
    
    POSITION_SIZING = [
        {'name': 'fixed_fraction', 'params': {'fraction': (0.01, 0.05)}},
        {'name': 'kelly', 'params': {'fraction': (0.1, 0.5)}},
        {'name': 'volatility_adjusted', 'params': {'target_vol': (0.1, 0.3)}},
        {'name': 'atr_based', 'params': {'atr_multiplier': (1.0, 3.0)}},
    ]
    
    EXIT_RULES = [
        {'name': 'fixed_stop', 'params': {'percent': (0.5, 3.0)}},
        {'name': 'atr_stop', 'params': {'multiplier': (1.5, 4.0)}},
        {'name': 'trailing_stop', 'params': {'percent': (1.0, 5.0)}},
        {'name': 'time_stop', 'params': {'bars': (5, 50)}},
        {'name': 'indicator_exit', 'params': {}},
    ]
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.generation_count = 0
        
    def generate_random_strategy(self) -> StrategyDNA:
        """Generate a completely random strategy"""
        genes = []
        
        # Add 2-4 indicators
        num_indicators = random.randint(2, 4)
        for _ in range(num_indicators):
            indicator = random.choice(self.INDICATORS)
            params = self._randomize_params(indicator['params'])
            params['indicator_name'] = indicator['name']
            genes.append(StrategyGene(
                gene_type='indicator',
                parameters=params,
                weight=random.uniform(0.5, 1.5)
            ))
        
        # Add 1-3 conditions
        num_conditions = random.randint(1, 3)
        for _ in range(num_conditions):
            genes.append(StrategyGene(
                gene_type='condition',
                parameters={
                    'condition_type': random.choice(self.CONDITIONS),
                    'threshold': random.uniform(-2, 2)
                },
                weight=random.uniform(0.5, 1.5)
            ))
        
        # Add 0-2 filters
        num_filters = random.randint(0, 2)
        for _ in range(num_filters):
            filter_def = random.choice(self.FILTERS)
            params = self._randomize_params(filter_def['params'])
            params['filter_name'] = filter_def['name']
            genes.append(StrategyGene(
                gene_type='filter',
                parameters=params,
                weight=1.0
            ))
        
        # Add position sizing
        sizing = random.choice(self.POSITION_SIZING)
        params = self._randomize_params(sizing['params'])
        params['sizing_method'] = sizing['name']
        genes.append(StrategyGene(
            gene_type='position_sizing',
            parameters=params,
            weight=1.0
        ))
        
        # Add exit rules
        exit_rule = random.choice(self.EXIT_RULES)
        params = self._randomize_params(exit_rule['params'])
        params['exit_method'] = exit_rule['name']
        genes.append(StrategyGene(
            gene_type='exit',
            parameters=params,
            weight=1.0
        ))
        
        strategy_id = str(uuid.uuid4())[:8]
        self.generation_count += 1
        
        return StrategyDNA(
            strategy_id=strategy_id,
            name=f"Strategy_{strategy_id}",
            genes=genes,
            generation=self.generation_count
        )
    
    def _randomize_params(self, param_ranges: Dict) -> Dict:
        """Randomize parameters within given ranges"""
        params = {}
        for key, value in param_ranges.items():
            if isinstance(value, tuple) and len(value) == 2:
                if isinstance(value[0], int):
                    params[key] = random.randint(value[0], value[1])
                else:
                    params[key] = random.uniform(value[0], value[1])
            elif isinstance(value, list):
                params[key] = random.choice(value)
            else:
                params[key] = value
        return params
    
    def generate_population(self, size: int = 100) -> List[StrategyDNA]:
        """Generate initial population of strategies"""
        return [self.generate_random_strategy() for _ in range(size)]


class BacktestEngine:
    """High-performance backtesting engine with walk-forward optimization"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.risk_free_rate = self.config.get('risk_free_rate', 0.02)
        self.trading_days = self.config.get('trading_days', 252)
        
    def backtest(
        self,
        strategy: StrategyDNA,
        data: pd.DataFrame,
        initial_capital: float = 100000,
        commission: float = 0.001
    ) -> BacktestResult:
        """Run full backtest on strategy"""
        
        # Initialize tracking
        capital = initial_capital
        position = 0
        equity_curve = [capital]
        returns = []
        trades = []
        
        # Generate signals from strategy DNA
        signals = self._generate_signals(strategy, data)
        
        # Simulate trading
        for i in range(1, len(data)):
            signal = signals.iloc[i] if i < len(signals) else 0
            price = data['close'].iloc[i]
            prev_price = data['close'].iloc[i-1]
            
            # Calculate position return
            if position != 0:
                pnl = position * (price - prev_price) / prev_price * capital
                capital += pnl
                returns.append(pnl / equity_curve[-1])
            else:
                returns.append(0)
            
            # Execute signal
            if signal > 0 and position <= 0:
                # Buy signal
                position = 1
                capital -= capital * commission
                trades.append({
                    'type': 'buy',
                    'price': price,
                    'time': data.index[i] if hasattr(data.index[i], 'strftime') else i
                })
            elif signal < 0 and position >= 0:
                # Sell signal
                position = -1
                capital -= capital * commission
                trades.append({
                    'type': 'sell',
                    'price': price,
                    'time': data.index[i] if hasattr(data.index[i], 'strftime') else i
                })
            
            equity_curve.append(capital)
        
        # Calculate metrics
        returns_array = np.array(returns)
        
        result = BacktestResult(
            strategy_id=strategy.strategy_id,
            start_date=data.index[0] if hasattr(data.index[0], 'strftime') else datetime.now(),
            end_date=data.index[-1] if hasattr(data.index[-1], 'strftime') else datetime.now(),
            equity_curve=equity_curve,
            returns=returns,
            trades=trades
        )
        
        # Core metrics
        result.total_return = (capital - initial_capital) / initial_capital
        years = len(data) / self.trading_days
        result.annualized_return = (1 + result.total_return) ** (1/max(years, 0.01)) - 1
        
        # Risk metrics
        if len(returns_array) > 0 and np.std(returns_array) > 0:
            result.volatility = np.std(returns_array) * np.sqrt(self.trading_days)
            result.sharpe_ratio = (result.annualized_return - self.risk_free_rate) / max(result.volatility, 0.001)
            
            # Downside metrics
            downside_returns = returns_array[returns_array < 0]
            if len(downside_returns) > 0:
                result.downside_volatility = np.std(downside_returns) * np.sqrt(self.trading_days)
                result.sortino_ratio = (result.annualized_return - self.risk_free_rate) / max(result.downside_volatility, 0.001)
            
            # Drawdown
            equity_array = np.array(equity_curve)
            running_max = np.maximum.accumulate(equity_array)
            drawdowns = (equity_array - running_max) / running_max
            result.max_drawdown = abs(np.min(drawdowns))
            result.avg_drawdown = abs(np.mean(drawdowns[drawdowns < 0])) if len(drawdowns[drawdowns < 0]) > 0 else 0
            
            if result.max_drawdown > 0:
                result.calmar_ratio = result.annualized_return / result.max_drawdown
            
            # Distribution metrics
            if SCIPY_AVAILABLE and len(returns_array) > 10:
                result.skewness = stats.skew(returns_array)
                result.kurtosis = stats.kurtosis(returns_array)
            
            # VaR and CVaR
            result.var_95 = np.percentile(returns_array, 5)
            result.cvar_95 = np.mean(returns_array[returns_array <= result.var_95]) if len(returns_array[returns_array <= result.var_95]) > 0 else result.var_95
            
            # Tail ratio
            upper_tail = np.percentile(returns_array, 95)
            lower_tail = abs(np.percentile(returns_array, 5))
            result.tail_ratio = upper_tail / max(lower_tail, 0.001)
        
        # Trade metrics
        result.total_trades = len(trades)
        if len(trades) > 1:
            trade_returns = []
            for i in range(1, len(trades)):
                if trades[i]['type'] != trades[i-1]['type']:
                    trade_return = (trades[i]['price'] - trades[i-1]['price']) / trades[i-1]['price']
                    if trades[i-1]['type'] == 'sell':
                        trade_return = -trade_return
                    trade_returns.append(trade_return)
            
            if trade_returns:
                wins = [r for r in trade_returns if r > 0]
                losses = [r for r in trade_returns if r < 0]
                result.win_rate = len(wins) / len(trade_returns)
                result.avg_win = np.mean(wins) if wins else 0
                result.avg_loss = np.mean(losses) if losses else 0
                
                if losses:
                    result.profit_factor = abs(sum(wins) / sum(losses)) if sum(losses) != 0 else float('inf')
                
                # Max consecutive losses
                consecutive = 0
                max_consecutive = 0
                for r in trade_returns:
                    if r < 0:
                        consecutive += 1
                        max_consecutive = max(max_consecutive, consecutive)
                    else:
                        consecutive = 0
                result.max_consecutive_losses = max_consecutive
        
        # Stability score (rolling Sharpe consistency)
        if len(returns_array) > 60:
            window = 20
            rolling_sharpes = []
            for i in range(window, len(returns_array)):
                window_returns = returns_array[i-window:i]
                if np.std(window_returns) > 0:
                    rolling_sharpe = np.mean(window_returns) / np.std(window_returns) * np.sqrt(self.trading_days)
                    rolling_sharpes.append(rolling_sharpe)
            
            if rolling_sharpes:
                result.stability_score = 1 - (np.std(rolling_sharpes) / max(abs(np.mean(rolling_sharpes)), 0.001))
        
        return result
    
    def _generate_signals(self, strategy: StrategyDNA, data: pd.DataFrame) -> pd.Series:
        """Generate trading signals from strategy DNA"""
        signals = pd.Series(0, index=data.index)
        
        # Extract indicator genes
        indicator_values = {}
        for gene in strategy.genes:
            if gene.gene_type == 'indicator':
                indicator_name = gene.parameters.get('indicator_name', 'SMA')
                period = gene.parameters.get('period', 20)
                
                if indicator_name == 'SMA':
                    indicator_values[f'SMA_{period}'] = data['close'].rolling(period).mean()
                elif indicator_name == 'EMA':
                    indicator_values[f'EMA_{period}'] = data['close'].ewm(span=period).mean()
                elif indicator_name == 'RSI':
                    delta = data['close'].diff()
                    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
                    rs = gain / loss.replace(0, 0.001)
                    indicator_values[f'RSI_{period}'] = 100 - (100 / (1 + rs))
                elif indicator_name == 'MOMENTUM':
                    indicator_values[f'MOM_{period}'] = data['close'].diff(period)
        
        # Generate signals based on conditions
        for i, gene in enumerate(strategy.genes):
            if gene.gene_type == 'condition':
                condition_type = gene.parameters.get('condition_type', 'crossover_above')
                
                # Simple signal generation based on available indicators
                if indicator_values:
                    first_indicator = list(indicator_values.values())[0]
                    
                    if 'crossover' in condition_type:
                        if len(indicator_values) > 1:
                            second_indicator = list(indicator_values.values())[1]
                            if 'above' in condition_type:
                                signals += ((first_indicator > second_indicator) & 
                                          (first_indicator.shift(1) <= second_indicator.shift(1))).astype(int) * gene.weight
                            else:
                                signals -= ((first_indicator < second_indicator) & 
                                          (first_indicator.shift(1) >= second_indicator.shift(1))).astype(int) * gene.weight
                    elif 'RSI' in str(list(indicator_values.keys())):
                        rsi_key = [k for k in indicator_values.keys() if 'RSI' in k][0]
                        rsi = indicator_values[rsi_key]
                        signals += (rsi < 30).astype(int) * gene.weight
                        signals -= (rsi > 70).astype(int) * gene.weight
        
        # Normalize signals
        signals = signals.fillna(0)
        signals = np.sign(signals)
        
        return signals
    
    def walk_forward_optimization(
        self,
        strategy: StrategyDNA,
        data: pd.DataFrame,
        n_splits: int = 5,
        train_ratio: float = 0.7
    ) -> List[BacktestResult]:
        """Perform walk-forward optimization"""
        results = []
        
        if SKLEARN_AVAILABLE:
            tscv = TimeSeriesSplit(n_splits=n_splits)
            
            for train_idx, test_idx in tscv.split(data):
                train_data = data.iloc[train_idx]
                test_data = data.iloc[test_idx]
                
                # Backtest on test period
                result = self.backtest(strategy, test_data)
                results.append(result)
        else:
            # Simple split without sklearn
            split_size = len(data) // n_splits
            for i in range(n_splits):
                start_idx = i * split_size
                end_idx = min((i + 1) * split_size, len(data))
                test_data = data.iloc[start_idx:end_idx]
                result = self.backtest(strategy, test_data)
                results.append(result)
        
        return results


class StressTestEngine:
    """Stress testing engine for regime shifts, crashes, and volatility spikes"""
    
    STRESS_SCENARIOS = {
        'flash_crash': {
            'description': 'Sudden 10% drop in 1 hour',
            'regime': RegimeType.CRASH,
            'price_change': -0.10,
            'duration_bars': 12,  # 5-min bars
            'volatility_multiplier': 5.0
        },
        'gradual_crash': {
            'description': '30% decline over 2 weeks',
            'regime': RegimeType.CRASH,
            'price_change': -0.30,
            'duration_bars': 200,
            'volatility_multiplier': 2.0
        },
        'volatility_spike': {
            'description': 'VIX-like spike to 80',
            'regime': RegimeType.HIGH_VOLATILITY,
            'price_change': -0.05,
            'duration_bars': 50,
            'volatility_multiplier': 4.0
        },
        'liquidity_crisis': {
            'description': 'Bid-ask spread widens 10x',
            'regime': RegimeType.HIGH_VOLATILITY,
            'price_change': -0.08,
            'duration_bars': 100,
            'spread_multiplier': 10.0
        },
        'trend_reversal': {
            'description': 'Strong trend suddenly reverses',
            'regime': RegimeType.TRENDING_DOWN,
            'price_change': -0.15,
            'duration_bars': 30,
            'volatility_multiplier': 2.5
        },
        'range_breakout_fake': {
            'description': 'False breakout followed by reversal',
            'regime': RegimeType.RANGING,
            'price_change': 0.05,
            'reversal_change': -0.08,
            'duration_bars': 20
        },
        'gap_down': {
            'description': 'Overnight gap down 5%',
            'regime': RegimeType.CRASH,
            'price_change': -0.05,
            'duration_bars': 1,
            'volatility_multiplier': 3.0
        },
        'correlation_breakdown': {
            'description': 'Historical correlations break',
            'regime': RegimeType.HIGH_VOLATILITY,
            'correlation_change': -0.8,
            'duration_bars': 50
        }
    }
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.backtest_engine = BacktestEngine(config)
        
    def generate_stress_data(
        self,
        base_data: pd.DataFrame,
        scenario_name: str
    ) -> pd.DataFrame:
        """Generate synthetic stress scenario data"""
        scenario = self.STRESS_SCENARIOS.get(scenario_name, self.STRESS_SCENARIOS['flash_crash'])
        
        # Copy base data
        stress_data = base_data.copy()
        
        # Apply scenario modifications
        duration = scenario.get('duration_bars', 50)
        price_change = scenario.get('price_change', -0.10)
        vol_mult = scenario.get('volatility_multiplier', 2.0)
        
        # Find a random point to inject stress
        inject_point = random.randint(len(stress_data) // 4, 3 * len(stress_data) // 4)
        
        # Apply price change
        for i in range(inject_point, min(inject_point + duration, len(stress_data))):
            progress = (i - inject_point) / duration
            stress_data.loc[stress_data.index[i], 'close'] *= (1 + price_change * progress)
            stress_data.loc[stress_data.index[i], 'high'] *= (1 + price_change * progress * 0.8)
            stress_data.loc[stress_data.index[i], 'low'] *= (1 + price_change * progress * 1.2)
        
        # Increase volatility
        if 'volatility_multiplier' in scenario:
            for i in range(inject_point, min(inject_point + duration, len(stress_data))):
                current_range = stress_data.loc[stress_data.index[i], 'high'] - stress_data.loc[stress_data.index[i], 'low']
                stress_data.loc[stress_data.index[i], 'high'] += current_range * (vol_mult - 1) / 2
                stress_data.loc[stress_data.index[i], 'low'] -= current_range * (vol_mult - 1) / 2
        
        return stress_data
    
    def run_stress_test(
        self,
        strategy: StrategyDNA,
        base_data: pd.DataFrame,
        scenario_name: str
    ) -> StressTestResult:
        """Run stress test for a specific scenario"""
        scenario = self.STRESS_SCENARIOS.get(scenario_name, self.STRESS_SCENARIOS['flash_crash'])
        
        # Generate stress data
        stress_data = self.generate_stress_data(base_data, scenario_name)
        
        # Run backtest on stress data
        backtest_result = self.backtest_engine.backtest(strategy, stress_data)
        
        # Evaluate stress test results
        result = StressTestResult(
            strategy_id=strategy.strategy_id,
            scenario_name=scenario_name,
            regime_type=scenario['regime'],
            return_during_stress=backtest_result.total_return,
            max_drawdown_during_stress=backtest_result.max_drawdown,
            position_changes=backtest_result.total_trades
        )
        
        # Determine pass/fail
        # Pass criteria: max drawdown < 30%, no margin calls
        result.passed = (
            result.max_drawdown_during_stress < 0.30 and
            result.margin_calls == 0
        )
        
        # Calculate score (0-100)
        drawdown_score = max(0, 100 - result.max_drawdown_during_stress * 200)
        return_score = max(0, min(100, 50 + result.return_during_stress * 100))
        result.score = (drawdown_score * 0.6 + return_score * 0.4)
        
        return result
    
    def run_all_stress_tests(
        self,
        strategy: StrategyDNA,
        base_data: pd.DataFrame
    ) -> List[StressTestResult]:
        """Run all stress test scenarios"""
        results = []
        for scenario_name in self.STRESS_SCENARIOS.keys():
            result = self.run_stress_test(strategy, base_data, scenario_name)
            results.append(result)
        return results


class StrategyRanker:
    """Ranks strategies by multiple criteria"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Ranking weights
        self.weights = {
            'sharpe': self.config.get('sharpe_weight', 0.25),
            'drawdown': self.config.get('drawdown_weight', 0.20),
            'stability': self.config.get('stability_weight', 0.15),
            'tail_risk': self.config.get('tail_risk_weight', 0.15),
            'profit_factor': self.config.get('profit_factor_weight', 0.10),
            'win_rate': self.config.get('win_rate_weight', 0.10),
            'stress_score': self.config.get('stress_weight', 0.05)
        }
        
    def rank_strategies(
        self,
        candidates: List[StrategyCandidate]
    ) -> List[StrategyCandidate]:
        """Rank all strategy candidates"""
        
        if not candidates:
            return []
        
        # Calculate composite scores
        for candidate in candidates:
            if not candidate.backtest_results:
                candidate.composite_score = 0
                continue
            
            # Average backtest results
            avg_sharpe = np.mean([r.sharpe_ratio for r in candidate.backtest_results])
            avg_drawdown = np.mean([r.max_drawdown for r in candidate.backtest_results])
            avg_stability = np.mean([r.stability_score for r in candidate.backtest_results])
            avg_tail_ratio = np.mean([r.tail_ratio for r in candidate.backtest_results])
            avg_profit_factor = np.mean([r.profit_factor for r in candidate.backtest_results])
            avg_win_rate = np.mean([r.win_rate for r in candidate.backtest_results])
            
            # Stress test score
            stress_score = 0
            if candidate.stress_test_results:
                stress_score = np.mean([r.score for r in candidate.stress_test_results])
            
            # Normalize and combine
            sharpe_score = min(max(avg_sharpe / 3, 0), 1)  # Normalize to 0-1
            drawdown_score = 1 - min(avg_drawdown / 0.5, 1)  # Lower is better
            stability_score = max(avg_stability, 0)
            tail_score = min(avg_tail_ratio / 2, 1)
            pf_score = min(avg_profit_factor / 3, 1)
            wr_score = avg_win_rate
            stress_normalized = stress_score / 100
            
            # Weighted composite
            candidate.composite_score = (
                self.weights['sharpe'] * sharpe_score +
                self.weights['drawdown'] * drawdown_score +
                self.weights['stability'] * stability_score +
                self.weights['tail_risk'] * tail_score +
                self.weights['profit_factor'] * pf_score +
                self.weights['win_rate'] * wr_score +
                self.weights['stress_score'] * stress_normalized
            )
        
        # Sort by composite score
        candidates.sort(key=lambda x: x.composite_score, reverse=True)
        
        # Assign ranks
        for i, candidate in enumerate(candidates):
            candidate.sharpe_rank = i + 1
            candidate.drawdown_rank = i + 1
            candidate.stability_rank = i + 1
            candidate.tail_risk_rank = i + 1
        
        return candidates


class SelfEvolvingResearcher:
    """
    Main orchestrator for the self-evolving research system.
    
    Lifecycle:
    1. Generate strategy candidates
    2. Backtest on multi-year data
    3. Stress test across scenarios
    4. Rank by multiple criteria
    5. Promote winners to production
    6. Kill losers
    7. Evolve and repeat
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Components
        self.generator = StrategyGenerator(config)
        self.backtest_engine = BacktestEngine(config)
        self.stress_engine = StressTestEngine(config)
        self.ranker = StrategyRanker(config)
        
        # Strategy storage
        self.candidates: List[StrategyCandidate] = []
        self.promoted_strategies: List[StrategyCandidate] = []
        self.killed_strategies: List[StrategyCandidate] = []
        
        # Evolution parameters
        self.population_size = self.config.get('population_size', 100)
        self.elite_count = self.config.get('elite_count', 10)
        self.mutation_rate = self.config.get('mutation_rate', 0.1)
        self.crossover_rate = self.config.get('crossover_rate', 0.3)
        self.promotion_threshold = self.config.get('promotion_threshold', 0.7)
        self.kill_threshold = self.config.get('kill_threshold', 0.2)
        
        # State
        self.generation = 0
        self.running = False
        self._lock = threading.Lock()
        
        # Storage path
        self.storage_path = Path(self.config.get('storage_path', 'research_data'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        logger.info("SelfEvolvingResearcher initialized")
    
    async def run_research_cycle(
        self,
        market_data: pd.DataFrame,
        generations: int = 10
    ) -> List[StrategyCandidate]:
        """Run complete research cycle"""
        
        self.running = True
        
        try:
            for gen in range(generations):
                self.generation = gen + 1
                logger.info(f"Starting generation {self.generation}")
                
                # Step 1: Generate or evolve population
                if gen == 0:
                    await self._generate_initial_population()
                else:
                    await self._evolve_population()
                
                # Step 2: Backtest all candidates
                await self._backtest_all(market_data)
                
                # Step 3: Stress test top candidates
                await self._stress_test_top_candidates(market_data)
                
                # Step 4: Rank strategies
                self._rank_strategies()
                
                # Step 5: Promote winners
                self._promote_winners()
                
                # Step 6: Kill losers
                self._kill_losers()
                
                # Log progress
                logger.info(f"Generation {self.generation} complete: "
                          f"{len(self.promoted_strategies)} promoted, "
                          f"{len(self.killed_strategies)} killed")
                
                # Save state
                self._save_state()
                
                if not self.running:
                    break
            
            return self.promoted_strategies
            
        finally:
            self.running = False
    
    async def _generate_initial_population(self):
        """Generate initial population of strategies"""
        logger.info(f"Generating initial population of {self.population_size} strategies")
        
        dna_list = self.generator.generate_population(self.population_size)
        
        self.candidates = [
            StrategyCandidate(dna=dna, status=StrategyStatus.CANDIDATE)
            for dna in dna_list
        ]
    
    async def _evolve_population(self):
        """Evolve population through selection, crossover, and mutation"""
        
        # Keep elite strategies
        elite = self.candidates[:self.elite_count]
        
        new_candidates = []
        
        # Add elite unchanged
        for candidate in elite:
            new_candidates.append(candidate)
        
        # Generate offspring through crossover
        while len(new_candidates) < self.population_size * self.crossover_rate:
            parent1 = random.choice(elite)
            parent2 = random.choice(elite)
            
            if parent1.dna.strategy_id != parent2.dna.strategy_id:
                offspring_dna = parent1.dna.crossover(parent2.dna)
                new_candidates.append(StrategyCandidate(
                    dna=offspring_dna,
                    status=StrategyStatus.CANDIDATE
                ))
        
        # Generate mutations
        while len(new_candidates) < self.population_size * (1 - self.mutation_rate):
            parent = random.choice(elite)
            mutant_dna = parent.dna.mutate()
            new_candidates.append(StrategyCandidate(
                dna=mutant_dna,
                status=StrategyStatus.CANDIDATE
            ))
        
        # Fill remaining with random strategies
        while len(new_candidates) < self.population_size:
            new_dna = self.generator.generate_random_strategy()
            new_candidates.append(StrategyCandidate(
                dna=new_dna,
                status=StrategyStatus.CANDIDATE
            ))
        
        self.candidates = new_candidates
    
    async def _backtest_all(self, market_data: pd.DataFrame):
        """Backtest all candidates"""
        logger.info(f"Backtesting {len(self.candidates)} candidates")
        
        for candidate in self.candidates:
            candidate.status = StrategyStatus.BACKTESTING
            
            # Walk-forward backtest
            results = self.backtest_engine.walk_forward_optimization(
                candidate.dna,
                market_data,
                n_splits=5
            )
            
            candidate.backtest_results = results
            candidate.status = StrategyStatus.VALIDATED
    
    async def _stress_test_top_candidates(
        self,
        market_data: pd.DataFrame,
        top_n: int = 20
    ):
        """Stress test top candidates"""
        
        # Rank first to get top candidates
        self.candidates = self.ranker.rank_strategies(self.candidates)
        
        top_candidates = self.candidates[:top_n]
        logger.info(f"Stress testing top {len(top_candidates)} candidates")
        
        for candidate in top_candidates:
            candidate.status = StrategyStatus.STRESS_TESTING
            
            stress_results = self.stress_engine.run_all_stress_tests(
                candidate.dna,
                market_data
            )
            
            candidate.stress_test_results = stress_results
            candidate.status = StrategyStatus.VALIDATED
    
    def _rank_strategies(self):
        """Rank all strategies"""
        self.candidates = self.ranker.rank_strategies(self.candidates)
    
    def _promote_winners(self):
        """Promote top strategies to production"""
        
        for candidate in self.candidates:
            if (candidate.composite_score >= self.promotion_threshold and
                candidate.status == StrategyStatus.VALIDATED):
                
                # Check stress test pass rate
                if candidate.stress_test_results:
                    pass_rate = sum(1 for r in candidate.stress_test_results if r.passed) / len(candidate.stress_test_results)
                    if pass_rate < 0.6:
                        continue
                
                candidate.status = StrategyStatus.PROMOTED
                candidate.promoted_at = datetime.now()
                
                if candidate not in self.promoted_strategies:
                    self.promoted_strategies.append(candidate)
                    logger.info(f"Promoted strategy {candidate.dna.strategy_id} "
                              f"(score: {candidate.composite_score:.3f})")
    
    def _kill_losers(self):
        """Kill underperforming strategies"""
        
        for candidate in self.candidates:
            if candidate.composite_score < self.kill_threshold:
                candidate.status = StrategyStatus.KILLED
                candidate.kill_reason = f"Low composite score: {candidate.composite_score:.3f}"
                
                if candidate not in self.killed_strategies:
                    self.killed_strategies.append(candidate)
                    logger.info(f"Killed strategy {candidate.dna.strategy_id} "
                              f"(score: {candidate.composite_score:.3f})")
    
    def _save_state(self):
        """Save research state to disk"""
        state = {
            'generation': self.generation,
            'promoted_count': len(self.promoted_strategies),
            'killed_count': len(self.killed_strategies),
            'timestamp': datetime.now().isoformat()
        }
        
        state_file = self.storage_path / 'research_state.json'
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def get_best_strategies(self, n: int = 10) -> List[StrategyCandidate]:
        """Get top N strategies"""
        return self.promoted_strategies[:n]
    
    def get_status(self) -> Dict:
        """Get current research status"""
        return {
            'generation': self.generation,
            'running': self.running,
            'total_candidates': len(self.candidates),
            'promoted': len(self.promoted_strategies),
            'killed': len(self.killed_strategies),
            'best_score': self.candidates[0].composite_score if self.candidates else 0
        }


# Factory function
def create_researcher(config: Optional[Dict] = None) -> SelfEvolvingResearcher:
    """Create and return a SelfEvolvingResearcher instance"""
    return SelfEvolvingResearcher(config)


# Quick start
async def quick_start_research(
    market_data: pd.DataFrame,
    generations: int = 5
) -> List[StrategyCandidate]:
    """Quick start research with default settings"""
    researcher = create_researcher()
    return await researcher.run_research_cycle(market_data, generations)
