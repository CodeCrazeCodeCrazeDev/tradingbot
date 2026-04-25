"""
GETS Backtesting Framework

Comprehensive backtesting with:
- Walk-forward validation (no lookahead bias)
- Regime-stratified evaluation
- Champion-challenger comparison
- Transaction cost modeling
- Risk metric computation
"""

import logging
from typing import Dict, List, Optional, Tuple, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import numpy as np
import pandas as pd

from .types import MarketData, GETSSignal, ForecastHorizon, GETSConfig
from .gets_system import GETS

logger = logging.getLogger(__name__)


@dataclass
class Trade:
    """Represents a single trade."""
    timestamp: datetime
    symbol: str
    direction: int  # 1 = buy, -1 = sell
    size: float
    entry_price: float
    exit_price: Optional[float] = None
    exit_timestamp: Optional[datetime] = None
    realized_return: Optional[float] = None
    cost_bps: float = 0.0
    signal_confidence: float = 0.0
    signal_edge: float = 0.0


@dataclass
class BacktestResult:
    """Complete backtest results."""
    # Basic metrics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_return: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    
    # Risk metrics
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    max_drawdown_duration: int
    calmar_ratio: float
    var_95: float
    cvar_95: float
    
    # Edge metrics
    information_coefficient: float
    edge_after_cost: float
    cost_impact: float
    
    # Regime metrics
    regime_performance: Dict[str, Dict]
    
    # Time series
    equity_curve: List[float]
    returns_series: List[float]
    drawdown_series: List[float]
    
    # Abstention analysis
    signals_generated: int
    signals_abstained: int
    abstention_rate: float
    
    # Statistical tests
    t_statistic: float
    p_value: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'total_trades': self.total_trades,
            'win_rate': self.win_rate,
            'sharpe_ratio': self.sharpe_ratio,
            'max_drawdown': self.max_drawdown,
            'information_coefficient': self.information_coefficient,
            'edge_after_cost': self.edge_after_cost,
            'regime_performance': self.regime_performance
        }


class TransactionCostModel:
    """Realistic transaction cost modeling."""
    
    def __init__(
        self,
        base_spread_bps: float = 1.0,
        market_impact_bps: float = 5.0,
        commission_bps: float = 1.0,
        slippage_volatility_factor: float = 0.5
    ):
        self.base_spread_bps = base_spread_bps
        self.market_impact_bps = market_impact_bps
        self.commission_bps = commission_bps
        self.slippage_volatility_factor = slippage_volatility_factor
    
    def estimate_cost(
        self,
        size: float,
        price: float,
        volatility: float,
        liquidity_score: float = 0.5
    ) -> float:
        """
        Estimate total transaction cost in basis points.
        
        Args:
            size: Position size
            price: Current price
            volatility: Annualized volatility
            liquidity_score: 0-1, higher = more liquid
            
        Returns:
            Total cost in basis points
        """
        # Spread cost (half spread for each leg)
        spread_cost = self.base_spread_bps / 2
        
        # Market impact (square root law approximation)
        impact_cost = self.market_impact_bps * np.sqrt(size) * (1 - liquidity_score * 0.5)
        
        # Volatility slippage
        vol_slippage = volatility * 10000 * self.slippage_volatility_factor
        
        # Commission
        commission = self.commission_bps
        
        total_cost = spread_cost + impact_cost + vol_slippage + commission
        
        return max(total_cost, 0.5)  # Minimum 0.5 bps


class WalkForwardValidator:
    """
    Walk-forward validation engine for GETS.
    
    Prevents lookahead bias by training on past data only,
    testing on future data only.
    """
    
    def __init__(
        self,
        train_periods: int = 252,  # ~1 year
        test_periods: int = 63,    # ~3 months
        step_size: int = 21        # ~1 month step
    ):
        self.train_periods = train_periods
        self.test_periods = test_periods
        self.step_size = step_size
    
    def generate_splits(
        self,
        data: List[MarketData]
    ) -> List[Tuple[List[MarketData], List[MarketData]]]:
        """
        Generate walk-forward train/test splits.
        
        Returns:
            List of (train_data, test_data) tuples
        """
        splits = []
        total_points = len(data)
        
        start_idx = self.train_periods
        
        while start_idx + self.test_periods <= total_points:
            train_data = data[start_idx - self.train_periods:start_idx]
            test_data = data[start_idx:start_idx + self.test_periods]
            
            splits.append((train_data, test_data))
            start_idx += self.step_size
        
        return splits


class ChampionChallengerTester:
    """
    Champion-challenger testing framework.
    
    Tests new model configurations (challengers) against
    the current production model (champion).
    """
    
    def __init__(
        self,
        champion_config: GETSConfig,
        significance_threshold: float = 0.05,
        min_samples: int = 1000
    ):
        self.champion_config = champion_config
        self.significance_threshold = significance_threshold
        self.min_samples = min_samples
        
        self.champion = GETS(champion_config)
    
    async def test_challenger(
        self,
        challenger_config: GETSConfig,
        test_data: List[MarketData],
        horizon: ForecastHorizon = ForecastHorizon.SHORT
    ) -> Dict:
        """
        Test challenger against champion.
        
        Args:
            challenger_config: Challenger model configuration
            test_data: Out-of-sample test data
            horizon: Forecast horizon
            
        Returns:
            Test results with statistical comparison
        """
        # Initialize models
        if not self.champion.initialize():
            raise RuntimeError("Failed to initialize champion")
        
        challenger = GETS(challenger_config)
        if not challenger.initialize():
            raise RuntimeError("Failed to initialize challenger")
        
        # Run backtests
        champion_result = await self._backtest_model(
            self.champion, test_data, horizon
        )
        challenger_result = await self._backtest_model(
            challenger, test_data, horizon
        )
        
        # Statistical comparison
        comparison = self._statistical_comparison(
            champion_result, challenger_result
        )
        
        return {
            'champion': champion_result.to_dict(),
            'challenger': challenger_result.to_dict(),
            'comparison': comparison,
            'promote_recommended': comparison['promote_recommended']
        }
    
    async def _backtest_model(
        self,
        model: GETS,
        data: List[MarketData],
        horizon: ForecastHorizon
    ) -> BacktestResult:
        """Run backtest on a model."""
        engine = BacktestEngine()
        return engine.run_backtest(model, data, horizon)
    
    def _statistical_comparison(
        self,
        champion: BacktestResult,
        challenger: BacktestResult
    ) -> Dict:
        """Statistical comparison between champion and challenger."""
        # IC comparison
        ic_diff = challenger.information_coefficient - champion.information_coefficient
        
        # Sharpe comparison
        sharpe_diff = challenger.sharpe_ratio - champion.sharpe_ratio
        
        # Edge comparison
        edge_diff = challenger.edge_after_cost - champion.edge_after_cost
        
        # T-test for significance (simplified)
        n = len(champion.returns_series)
        if n > 30:
            from scipy import stats
            t_stat, p_value = stats.ttest_ind(
                challenger.returns_series,
                champion.returns_series
            )
        else:
            t_stat, p_value = 0.0, 1.0
        
        # Promotion criteria
        criteria_met = {
            'ic_improvement': ic_diff > 0.01,
            'sharpe_improvement': sharpe_diff > 0.1,
            'edge_improvement': edge_diff > 0.0001,
            'statistically_significant': p_value < self.significance_threshold,
            'lower_drawdown': challenger.max_drawdown > champion.max_drawdown * 0.9
        }
        
        promote_recommended = (
            criteria_met['ic_improvement'] and
            criteria_met['statistically_significant'] and
            criteria_met['lower_drawdown']
        )
        
        return {
            'ic_difference': ic_diff,
            'sharpe_difference': sharpe_diff,
            'edge_difference': edge_diff,
            't_statistic': t_stat,
            'p_value': p_value,
            'criteria_met': criteria_met,
            'promote_recommended': promote_recommended
        }


class BacktestEngine:
    """Main backtesting engine for GETS."""
    
    def __init__(
        self,
        transaction_cost_model: Optional[TransactionCostModel] = None
    ):
        self.cost_model = transaction_cost_model or TransactionCostModel()
        self.trades: List[Trade] = []
    
    def run_backtest(
        self,
        gets: GETS,
        market_data: List[MarketData],
        horizon: ForecastHorizon,
        position_size_fn: Optional[Callable[[GETSSignal], float]] = None
    ) -> BacktestResult:
        """
        Run complete backtest.
        
        Args:
            gets: GETS instance
            market_data: Historical market data
            horizon: Forecast horizon
            position_size_fn: Function to determine position size from signal
            
        Returns:
            Complete backtest results
        """
        if not position_size_fn:
            position_size_fn = lambda s: 1.0 if s.confidence > 0.6 else 0.0
        
        self.trades = []
        equity = 1.0
        equity_curve = [equity]
        returns_series = []
        
        signals_generated = 0
        signals_abstained = 0
        regime_performance = {}
        
        for i, data in enumerate(market_data):
            # Generate signal
            signal = gets.generate_signal(data, horizon)
            signals_generated += 1
            
            if signal.abstain_recommended:
                signals_abstained += 1
                continue
            
            # Get regime
            regime = signal.diagnosis_report.regime_label.name if signal.diagnosis_report.regime_label else "UNKNOWN"
            
            # Check if we should trade
            size = position_size_fn(signal)
            if size <= 0:
                continue
            
            # Estimate transaction costs
            cost_bps = self.cost_model.estimate_cost(
                size=size,
                price=data.ohlcv['close'],
                volatility=data.realized_volatility or 0.2,
                liquidity_score=signal.diagnosis_report.execution_constraints.get('liquidity_score', 0.5)
            )
            
            # Simulate trade
            entry_price = data.ohlcv['close']
            
            # Look ahead to find exit (simplified: next period)
            exit_idx = min(i + 1, len(market_data) - 1)
            exit_price = market_data[exit_idx].ohlcv['close']
            exit_time = market_data[exit_idx].timestamp
            
            # Calculate return
            price_return = (exit_price - entry_price) / entry_price
            trade_return = price_return * signal.direction - cost_bps / 10000
            
            # Record trade
            trade = Trade(
                timestamp=data.timestamp,
                symbol=data.symbol,
                direction=signal.direction,
                size=size,
                entry_price=entry_price,
                exit_price=exit_price,
                exit_timestamp=exit_time,
                realized_return=trade_return,
                cost_bps=cost_bps,
                signal_confidence=signal.confidence,
                signal_edge=signal.expected_edge
            )
            self.trades.append(trade)
            
            # Update equity
            equity *= (1 + trade_return)
            equity_curve.append(equity)
            returns_series.append(trade_return)
            
            # Track regime performance
            if regime not in regime_performance:
                regime_performance[regime] = {'trades': 0, 'wins': 0, 'returns': []}
            regime_performance[regime]['trades'] += 1
            regime_performance[regime]['wins'] += 1 if trade_return > 0 else 0
            regime_performance[regime]['returns'].append(trade_return)
        
        # Compute metrics
        result = self._compute_metrics(
            trades=self.trades,
            equity_curve=equity_curve,
            returns_series=returns_series,
            regime_performance=regime_performance,
            signals_generated=signals_generated,
            signals_abstained=signals_abstained
        )
        
        return result
    
    def _compute_metrics(
        self,
        trades: List[Trade],
        equity_curve: List[float],
        returns_series: List[float],
        regime_performance: Dict,
        signals_generated: int,
        signals_abstained: int
    ) -> BacktestResult:
        """Compute all backtest metrics."""
        if not trades:
            return BacktestResult(
                total_trades=0, winning_trades=0, losing_trades=0,
                win_rate=0.0, avg_return=0.0, avg_win=0.0, avg_loss=0.0,
                profit_factor=0.0, sharpe_ratio=0.0, sortino_ratio=0.0,
                max_drawdown=0.0, max_drawdown_duration=0, calmar_ratio=0.0,
                var_95=0.0, cvar_95=0.0, information_coefficient=0.0,
                edge_after_cost=0.0, cost_impact=0.0, regime_performance={},
                equity_curve=equity_curve, returns_series=returns_series,
                drawdown_series=[], signals_generated=0, signals_abstained=0,
                abstention_rate=0.0, t_statistic=0.0, p_value=1.0
            )
        
        returns = np.array(returns_series)
        
        # Basic metrics
        total_trades = len(trades)
        winning_trades = sum(1 for t in trades if t.realized_return > 0)
        losing_trades = total_trades - winning_trades
        win_rate = winning_trades / total_trades
        
        returns_list = [t.realized_return for t in trades]
        avg_return = np.mean(returns_list)
        
        wins = [t.realized_return for t in trades if t.realized_return > 0]
        losses = [t.realized_return for t in trades if t.realized_return <= 0]
        
        avg_win = np.mean(wins) if wins else 0
        avg_loss = np.mean(losses) if losses else 0
        
        profit_factor = abs(sum(wins) / sum(losses)) if sum(losses) != 0 else float('inf')
        
        # Risk metrics
        sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
        
        downside_returns = returns[returns < 0]
        sortino = np.mean(returns) / np.std(downside_returns) * np.sqrt(252) if len(downside_returns) > 0 and np.std(downside_returns) > 0 else 0
        
        # Drawdown
        rolling_max = np.maximum.accumulate(equity_curve)
        drawdown = (rolling_max - equity_curve) / rolling_max
        max_dd = np.max(drawdown)
        
        # Drawdown duration
        in_drawdown = drawdown > 0
        dd_durations = []
        current_duration = 0
        for is_dd in in_drawdown:
            if is_dd:
                current_duration += 1
            else:
                if current_duration > 0:
                    dd_durations.append(current_duration)
                current_duration = 0
        max_dd_duration = max(dd_durations) if dd_durations else 0
        
        calmar = np.mean(returns) * 252 / max_dd if max_dd > 0 else 0
        
        # VaR/CVaR
        var_95 = np.percentile(returns, 5)
        cvar_95 = np.mean(returns[returns <= var_95]) if len(returns[returns <= var_95]) > 0 else var_95
        
        # IC calculation (predicted vs realized rank)
        predicted = [t.signal_edge for t in trades]
        realized = [t.realized_return for t in trades]
        ic = np.corrcoef(predicted, realized)[0, 1] if len(predicted) > 1 else 0
        
        # Edge after cost
        avg_cost = np.mean([t.cost_bps for t in trades]) / 10000
        edge_after_cost = avg_return - avg_cost
        
        # Abstention rate
        abstention_rate = signals_abstained / max(signals_generated, 1)
        
        # Statistical test
        from scipy import stats
        t_stat, p_val = stats.ttest_1samp(returns, 0) if len(returns) > 1 else (0, 1)
        
        return BacktestResult(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            avg_return=avg_return,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            max_drawdown=max_dd,
            max_drawdown_duration=max_dd_duration,
            calmar_ratio=calmar,
            var_95=var_95,
            cvar_95=cvar_95,
            information_coefficient=ic,
            edge_after_cost=edge_after_cost,
            cost_impact=avg_cost,
            regime_performance={k: {
                'trades': v['trades'],
                'win_rate': v['wins'] / v['trades'] if v['trades'] > 0 else 0,
                'avg_return': np.mean(v['returns']) if v['returns'] else 0
            } for k, v in regime_performance.items()},
            equity_curve=equity_curve,
            returns_series=returns_series.tolist(),
            drawdown_series=drawdown.tolist(),
            signals_generated=signals_generated,
            signals_abstained=signals_abstained,
            abstention_rate=abstention_rate,
            t_statistic=t_stat,
            p_value=p_val
        )
