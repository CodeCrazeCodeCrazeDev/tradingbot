"""
Edge Decay Monitor: Detect and track statistical edge degradation.

Monitors strategies in production to detect when edges decay and
trigger re-evolution or strategy retirement.
"""

from typing import List, Dict, Optional, Tuple
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from scipy import stats
import logging

from .strategy_genome import StrategyGenome
from .backtesting_engine import BacktestResult


logger = logging.getLogger(__name__)


@dataclass
class EdgeMetrics:
    """Metrics for tracking edge quality"""
    sharpe_ratio: float
    information_ratio: float
    win_rate: float
    profit_factor: float
    
    avg_trade_pnl: float
    trade_frequency: float
    
    regime_consistency: float
    statistical_significance: float
    
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class DecaySignal:
    """Signal indicating edge decay"""
    signal_type: str
    severity: float
    description: str
    timestamp: datetime
    
    metrics_before: EdgeMetrics
    metrics_after: EdgeMetrics


@dataclass
class EdgeStatus:
    """Current status of a strategy edge"""
    genome_id: str
    is_active: bool
    
    current_metrics: EdgeMetrics
    baseline_metrics: EdgeMetrics
    
    decay_signals: List[DecaySignal]
    
    days_since_deployment: int
    performance_trend: str
    
    recommendation: str


class EdgeDecayMonitor:
    """
    Monitor strategy edges for decay and degradation.
    
    Detects:
    - Performance degradation
    - Statistical significance loss
    - Regime changes
    - Overfitting manifestation
    - Competition/crowding effects
    """
    
    def __init__(
        self,
        lookback_days: int = 90,
        decay_threshold: float = 0.3,
        significance_level: float = 0.05,
        min_trades_per_period: int = 10
    ):
        """
        Initialize edge decay monitor.
        
        Args:
            lookback_days: Days to look back for comparison
            decay_threshold: Threshold for declaring decay (30% degradation)
            significance_level: Statistical significance level
            min_trades_per_period: Minimum trades required per period
        """
        self.lookback_days = lookback_days
        self.decay_threshold = decay_threshold
        self.significance_level = significance_level
        self.min_trades_per_period = min_trades_per_period
        
        self.strategy_baselines: Dict[str, EdgeMetrics] = {}
        self.strategy_history: Dict[str, List[EdgeMetrics]] = {}
    
    def monitor_strategy(
        self,
        genome_id: str,
        recent_performance: pd.DataFrame,
        baseline_performance: Optional[pd.DataFrame] = None
    ) -> EdgeStatus:
        """
        Monitor a strategy for edge decay.
        
        Args:
            genome_id: Strategy genome ID
            recent_performance: Recent trading performance data
            baseline_performance: Baseline performance (backtest or early live)
        
        Returns:
            EdgeStatus with decay analysis
        """
        current_metrics = self._calculate_metrics(recent_performance)
        
        if genome_id not in self.strategy_baselines:
            if baseline_performance is not None:
                baseline_metrics = self._calculate_metrics(baseline_performance)
                self.strategy_baselines[genome_id] = baseline_metrics
            else:
                self.strategy_baselines[genome_id] = current_metrics
        
        baseline_metrics = self.strategy_baselines[genome_id]
        
        if genome_id not in self.strategy_history:
            self.strategy_history[genome_id] = []
        self.strategy_history[genome_id].append(current_metrics)
        
        decay_signals = self._detect_decay(
            genome_id,
            current_metrics,
            baseline_metrics,
            recent_performance
        )
        
        performance_trend = self._analyze_trend(genome_id)
        
        recommendation = self._generate_recommendation(
            decay_signals,
            performance_trend,
            current_metrics
        )
        
        days_deployed = (datetime.now() - baseline_metrics.timestamp).days
        
        return EdgeStatus(
            genome_id=genome_id,
            is_active=len([s for s in decay_signals if s.severity > 0.7]) == 0,
            current_metrics=current_metrics,
            baseline_metrics=baseline_metrics,
            decay_signals=decay_signals,
            days_since_deployment=days_deployed,
            performance_trend=performance_trend,
            recommendation=recommendation
        )
    
    def _calculate_metrics(self, performance: pd.DataFrame) -> EdgeMetrics:
        """Calculate edge metrics from performance data"""
        if 'returns' not in performance.columns:
            raise ValueError("Performance data must contain 'returns' column")
        
        returns = performance['returns'].dropna()
        
        if len(returns) == 0:
            return self._create_zero_metrics()
        
        sharpe = self._calculate_sharpe(returns)
        
        information_ratio = sharpe
        
        if 'pnl' in performance.columns:
            pnl = performance['pnl'].dropna()
            win_rate = (pnl > 0).sum() / len(pnl) if len(pnl) > 0 else 0
            
            wins = pnl[pnl > 0].sum()
            losses = abs(pnl[pnl < 0].sum())
            profit_factor = wins / losses if losses > 0 else 0
            
            avg_trade_pnl = pnl.mean()
        else:
            win_rate = (returns > 0).sum() / len(returns)
            profit_factor = 0
            avg_trade_pnl = returns.mean()
        
        trade_frequency = len(returns) / max(1, (performance.index[-1] - performance.index[0]).days)
        
        regime_consistency = self._calculate_regime_consistency(returns)
        
        statistical_significance = self._calculate_significance(returns)
        
        return EdgeMetrics(
            sharpe_ratio=sharpe,
            information_ratio=information_ratio,
            win_rate=win_rate,
            profit_factor=profit_factor,
            avg_trade_pnl=avg_trade_pnl,
            trade_frequency=trade_frequency,
            regime_consistency=regime_consistency,
            statistical_significance=statistical_significance
        )
    
    def _create_zero_metrics(self) -> EdgeMetrics:
        """Create zero metrics for invalid data"""
        return EdgeMetrics(
            sharpe_ratio=0.0,
            information_ratio=0.0,
            win_rate=0.0,
            profit_factor=0.0,
            avg_trade_pnl=0.0,
            trade_frequency=0.0,
            regime_consistency=0.0,
            statistical_significance=0.0
        )
    
    def _calculate_sharpe(self, returns: pd.Series) -> float:
        """Calculate Sharpe ratio"""
        if len(returns) < 2 or returns.std() == 0:
            return 0.0
        
        return (returns.mean() / returns.std()) * np.sqrt(252)
    
    def _calculate_regime_consistency(self, returns: pd.Series) -> float:
        """Calculate consistency across different regimes"""
        if len(returns) < 60:
            return 0.5
        
        n_regimes = 4
        regime_size = len(returns) // n_regimes
        
        regime_sharpes = []
        for i in range(n_regimes):
            start_idx = i * regime_size
            end_idx = (i + 1) * regime_size if i < n_regimes - 1 else len(returns)
            regime_returns = returns.iloc[start_idx:end_idx]
            
            if len(regime_returns) > 5:
                regime_sharpe = self._calculate_sharpe(regime_returns)
                regime_sharpes.append(regime_sharpe)
        
        if not regime_sharpes:
            return 0.5
        
        consistency = 1.0 - (np.std(regime_sharpes) / (abs(np.mean(regime_sharpes)) + 1.0))
        
        return max(0, min(1, consistency))
    
    def _calculate_significance(self, returns: pd.Series) -> float:
        """Calculate statistical significance of returns"""
        if len(returns) < 10:
            return 0.0
        
        t_stat, p_value = stats.ttest_1samp(returns, 0.0)
        
        significance = 1.0 - p_value
        
        return max(0, min(1, significance))
    
    def _detect_decay(
        self,
        genome_id: str,
        current: EdgeMetrics,
        baseline: EdgeMetrics,
        performance: pd.DataFrame
    ) -> List[DecaySignal]:
        """Detect various types of edge decay"""
        signals = []
        
        sharpe_decay = (baseline.sharpe_ratio - current.sharpe_ratio) / (abs(baseline.sharpe_ratio) + 1e-6)
        if sharpe_decay > self.decay_threshold:
            signals.append(DecaySignal(
                signal_type="sharpe_degradation",
                severity=min(1.0, sharpe_decay / self.decay_threshold),
                description=f"Sharpe ratio declined {sharpe_decay*100:.1f}% from baseline",
                timestamp=datetime.now(),
                metrics_before=baseline,
                metrics_after=current
            ))
        
        if current.win_rate < baseline.win_rate * (1 - self.decay_threshold):
            signals.append(DecaySignal(
                signal_type="win_rate_decline",
                severity=0.6,
                description=f"Win rate declined from {baseline.win_rate:.2%} to {current.win_rate:.2%}",
                timestamp=datetime.now(),
                metrics_before=baseline,
                metrics_after=current
            ))
        
        if current.statistical_significance < self.significance_level:
            signals.append(DecaySignal(
                signal_type="significance_loss",
                severity=0.8,
                description=f"Strategy no longer statistically significant (p={1-current.statistical_significance:.3f})",
                timestamp=datetime.now(),
                metrics_before=baseline,
                metrics_after=current
            ))
        
        if current.regime_consistency < 0.3:
            signals.append(DecaySignal(
                signal_type="regime_instability",
                severity=0.7,
                description=f"Low regime consistency: {current.regime_consistency:.2f}",
                timestamp=datetime.now(),
                metrics_before=baseline,
                metrics_after=current
            ))
        
        if current.trade_frequency < baseline.trade_frequency * 0.5:
            signals.append(DecaySignal(
                signal_type="opportunity_decline",
                severity=0.5,
                description=f"Trade frequency declined {((baseline.trade_frequency - current.trade_frequency) / baseline.trade_frequency * 100):.1f}%",
                timestamp=datetime.now(),
                metrics_before=baseline,
                metrics_after=current
            ))
        
        return signals
    
    def _analyze_trend(self, genome_id: str) -> str:
        """Analyze performance trend over time"""
        if genome_id not in self.strategy_history or len(self.strategy_history[genome_id]) < 3:
            return "insufficient_data"
        
        history = self.strategy_history[genome_id]
        recent_sharpes = [m.sharpe_ratio for m in history[-5:]]
        
        if len(recent_sharpes) < 3:
            return "insufficient_data"
        
        x = np.arange(len(recent_sharpes))
        slope, _, r_value, _, _ = stats.linregress(x, recent_sharpes)
        
        if r_value ** 2 < 0.3:
            return "volatile"
        
        if slope > 0.1:
            return "improving"
        elif slope < -0.1:
            return "declining"
        else:
            return "stable"
    
    def _generate_recommendation(
        self,
        decay_signals: List[DecaySignal],
        trend: str,
        current_metrics: EdgeMetrics
    ) -> str:
        """Generate recommendation based on decay analysis"""
        high_severity_signals = [s for s in decay_signals if s.severity > 0.7]
        medium_severity_signals = [s for s in decay_signals if 0.4 < s.severity <= 0.7]
        
        if len(high_severity_signals) >= 2:
            return "RETIRE: Multiple severe decay signals detected"
        
        if len(high_severity_signals) == 1 and trend == "declining":
            return "RETIRE: Severe decay with declining trend"
        
        if len(medium_severity_signals) >= 3:
            return "REDUCE_ALLOCATION: Multiple moderate decay signals"
        
        if trend == "declining" and current_metrics.sharpe_ratio < 0.5:
            return "MONITOR_CLOSELY: Declining performance"
        
        if current_metrics.statistical_significance < self.significance_level:
            return "REDUCE_ALLOCATION: Lost statistical significance"
        
        if trend == "improving":
            return "MAINTAIN: Strategy performing well"
        
        if current_metrics.sharpe_ratio > 1.5:
            return "MAINTAIN: Strong performance"
        
        return "MONITOR: Normal operation"
    
    def get_portfolio_health(
        self,
        strategy_statuses: List[EdgeStatus]
    ) -> Dict[str, any]:
        """
        Analyze overall portfolio health.
        
        Args:
            strategy_statuses: List of strategy edge statuses
        
        Returns:
            Portfolio health metrics
        """
        active_strategies = [s for s in strategy_statuses if s.is_active]
        
        avg_sharpe = np.mean([s.current_metrics.sharpe_ratio for s in active_strategies]) if active_strategies else 0
        
        strategies_with_decay = [s for s in strategy_statuses if len(s.decay_signals) > 0]
        decay_rate = len(strategies_with_decay) / len(strategy_statuses) if strategy_statuses else 0
        
        severe_decay = [s for s in strategy_statuses 
                       if any(sig.severity > 0.7 for sig in s.decay_signals)]
        
        recommendations = {}
        for status in strategy_statuses:
            rec = status.recommendation.split(':')[0]
            recommendations[rec] = recommendations.get(rec, 0) + 1
        
        return {
            'total_strategies': len(strategy_statuses),
            'active_strategies': len(active_strategies),
            'avg_sharpe': avg_sharpe,
            'decay_rate': decay_rate,
            'severe_decay_count': len(severe_decay),
            'recommendations': recommendations,
            'health_score': self._calculate_health_score(strategy_statuses)
        }
    
    def _calculate_health_score(self, statuses: List[EdgeStatus]) -> float:
        """Calculate overall portfolio health score (0-1)"""
        if not statuses:
            return 0.0
        
        active_ratio = sum(1 for s in statuses if s.is_active) / len(statuses)
        
        avg_sharpe = np.mean([s.current_metrics.sharpe_ratio for s in statuses])
        sharpe_score = min(1.0, avg_sharpe / 2.0)
        
        severe_decay_penalty = sum(
            1 for s in statuses 
            if any(sig.severity > 0.7 for sig in s.decay_signals)
        ) / len(statuses)
        
        health_score = (
            0.4 * active_ratio +
            0.4 * sharpe_score +
            0.2 * (1 - severe_decay_penalty)
        )
        
        return max(0, min(1, health_score))
