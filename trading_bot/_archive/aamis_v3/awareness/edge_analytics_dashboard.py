"""
AAMIS v3.0 - Edge Analytics Dashboard

This module implements:
1. Performance visualization and analytics
2. Real-time edge tracking
3. Strategy performance comparison
4. Risk-adjusted metrics dashboard
5. Trade quality scoring
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of performance metrics"""
    RETURN = "RETURN"
    RISK = "RISK"
    EFFICIENCY = "EFFICIENCY"
    QUALITY = "QUALITY"
    CONSISTENCY = "CONSISTENCY"


class TimeFrame(Enum):
    """Time frames for analysis"""
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    YEARLY = "YEARLY"
    ALL_TIME = "ALL_TIME"


@dataclass
class PerformanceMetrics:
    """Complete performance metrics"""
    # Return metrics
    total_return: float = 0.0
    annualized_return: float = 0.0
    daily_return_avg: float = 0.0
    monthly_return_avg: float = 0.0
    
    # Risk metrics
    volatility: float = 0.0
    max_drawdown: float = 0.0
    current_drawdown: float = 0.0
    var_95: float = 0.0  # Value at Risk
    cvar_95: float = 0.0  # Conditional VaR
    
    # Risk-adjusted metrics
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    omega_ratio: float = 0.0
    
    # Trade metrics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    average_win: float = 0.0
    average_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    
    # Consistency metrics
    consecutive_wins: int = 0
    consecutive_losses: int = 0
    max_consecutive_wins: int = 0
    max_consecutive_losses: int = 0
    
    # Edge metrics
    edge_score: float = 0.0
    expectancy: float = 0.0
    r_multiple_avg: float = 0.0


@dataclass
class StrategyPerformance:
    """Performance data for a strategy"""
    strategy_id: str
    strategy_name: str
    metrics: PerformanceMetrics = field(default_factory=PerformanceMetrics)
    equity_curve: List[float] = field(default_factory=list)
    drawdown_curve: List[float] = field(default_factory=list)
    trade_history: List[Dict] = field(default_factory=list)
    timestamps: List[datetime] = field(default_factory=list)


@dataclass
class EdgeAnalysis:
    """Edge analysis results"""
    edge_exists: bool = False
    edge_strength: float = 0.0
    edge_consistency: float = 0.0
    edge_decay_rate: float = 0.0
    statistical_significance: float = 0.0
    confidence_interval: Tuple[float, float] = (0.0, 0.0)
    recommendations: List[str] = field(default_factory=list)


class MetricsCalculator:
    """
    Calculates all performance metrics
    """
    
    def __init__(self, risk_free_rate: float = 0.02):
        self.risk_free_rate = risk_free_rate
    
    def calculate_all_metrics(
        self,
        returns: List[float],
        trades: List[Dict]
    ) -> PerformanceMetrics:
        """Calculate all performance metrics"""
        metrics = PerformanceMetrics()
        
        if not returns:
            return metrics
        
        returns_array = np.array(returns)
        
        # Return metrics
        metrics.total_return = np.prod(1 + returns_array) - 1
        metrics.daily_return_avg = np.mean(returns_array)
        metrics.monthly_return_avg = metrics.daily_return_avg * 21  # ~21 trading days
        metrics.annualized_return = (1 + metrics.total_return) ** (252 / len(returns)) - 1
        
        # Risk metrics
        metrics.volatility = np.std(returns_array) * np.sqrt(252)
        metrics.max_drawdown = self._calculate_max_drawdown(returns_array)
        metrics.current_drawdown = self._calculate_current_drawdown(returns_array)
        metrics.var_95 = self._calculate_var(returns_array, 0.05)
        metrics.cvar_95 = self._calculate_cvar(returns_array, 0.05)
        
        # Risk-adjusted metrics
        metrics.sharpe_ratio = self._calculate_sharpe(returns_array)
        metrics.sortino_ratio = self._calculate_sortino(returns_array)
        metrics.calmar_ratio = self._calculate_calmar(metrics.annualized_return, metrics.max_drawdown)
        metrics.omega_ratio = self._calculate_omega(returns_array)
        
        # Trade metrics
        if trades:
            metrics = self._calculate_trade_metrics(metrics, trades)
        
        # Edge metrics
        metrics.edge_score = self._calculate_edge_score(metrics)
        metrics.expectancy = self._calculate_expectancy(metrics)
        
        return metrics
    
    def _calculate_max_drawdown(self, returns: np.ndarray) -> float:
        """Calculate maximum drawdown"""
        cumulative = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdowns = (cumulative - running_max) / running_max
        return abs(np.min(drawdowns))
    
    def _calculate_current_drawdown(self, returns: np.ndarray) -> float:
        """Calculate current drawdown"""
        cumulative = np.cumprod(1 + returns)
        peak = np.max(cumulative)
        current = cumulative[-1]
        return (peak - current) / peak if peak > 0 else 0.0
    
    def _calculate_var(self, returns: np.ndarray, alpha: float) -> float:
        """Calculate Value at Risk"""
        return np.percentile(returns, alpha * 100)
    
    def _calculate_cvar(self, returns: np.ndarray, alpha: float) -> float:
        """Calculate Conditional Value at Risk (Expected Shortfall)"""
        var = self._calculate_var(returns, alpha)
        return np.mean(returns[returns <= var])
    
    def _calculate_sharpe(self, returns: np.ndarray) -> float:
        """Calculate Sharpe ratio"""
        excess_returns = returns - self.risk_free_rate / 252
        if np.std(excess_returns) == 0:
            return 0.0
        return np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)
    
    def _calculate_sortino(self, returns: np.ndarray) -> float:
        """Calculate Sortino ratio"""
        excess_returns = returns - self.risk_free_rate / 252
        downside_returns = returns[returns < 0]
        if len(downside_returns) == 0 or np.std(downside_returns) == 0:
            return 0.0
        return np.mean(excess_returns) / np.std(downside_returns) * np.sqrt(252)
    
    def _calculate_calmar(self, annualized_return: float, max_drawdown: float) -> float:
        """Calculate Calmar ratio"""
        if max_drawdown == 0:
            return 0.0
        return annualized_return / max_drawdown
    
    def _calculate_omega(self, returns: np.ndarray, threshold: float = 0.0) -> float:
        """Calculate Omega ratio"""
        gains = returns[returns > threshold] - threshold
        losses = threshold - returns[returns <= threshold]
        
        if np.sum(losses) == 0:
            return float('inf') if np.sum(gains) > 0 else 1.0
        
        return np.sum(gains) / np.sum(losses)
    
    def _calculate_trade_metrics(
        self,
        metrics: PerformanceMetrics,
        trades: List[Dict]
    ) -> PerformanceMetrics:
        """Calculate trade-based metrics"""
        metrics.total_trades = len(trades)
        
        pnls = [t.get('pnl', 0) for t in trades]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]
        
        metrics.winning_trades = len(wins)
        metrics.losing_trades = len(losses)
        metrics.win_rate = len(wins) / len(trades) if trades else 0.0
        
        metrics.average_win = np.mean(wins) if wins else 0.0
        metrics.average_loss = np.mean(losses) if losses else 0.0
        metrics.largest_win = max(wins) if wins else 0.0
        metrics.largest_loss = min(losses) if losses else 0.0
        
        total_wins = sum(wins)
        total_losses = abs(sum(losses))
        metrics.profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
        
        # Consecutive wins/losses
        metrics.max_consecutive_wins, metrics.max_consecutive_losses = \
            self._calculate_consecutive_streaks(pnls)
        
        return metrics
    
    def _calculate_consecutive_streaks(self, pnls: List[float]) -> Tuple[int, int]:
        """Calculate max consecutive wins and losses"""
        max_wins = 0
        max_losses = 0
        current_wins = 0
        current_losses = 0
        
        for pnl in pnls:
            if pnl > 0:
                current_wins += 1
                current_losses = 0
                max_wins = max(max_wins, current_wins)
            elif pnl < 0:
                current_losses += 1
                current_wins = 0
                max_losses = max(max_losses, current_losses)
            else:
                current_wins = 0
                current_losses = 0
        
        return max_wins, max_losses
    
    def _calculate_edge_score(self, metrics: PerformanceMetrics) -> float:
        """Calculate overall edge score (0-100)"""
        score = 0.0
        
        # Win rate contribution (max 25 points)
        score += min(25, metrics.win_rate * 40)
        
        # Profit factor contribution (max 25 points)
        if metrics.profit_factor >= 2:
            score += 25
        elif metrics.profit_factor >= 1.5:
            score += 20
        elif metrics.profit_factor >= 1.2:
            score += 15
        elif metrics.profit_factor >= 1:
            score += 10
        
        # Sharpe ratio contribution (max 25 points)
        if metrics.sharpe_ratio >= 2:
            score += 25
        elif metrics.sharpe_ratio >= 1.5:
            score += 20
        elif metrics.sharpe_ratio >= 1:
            score += 15
        elif metrics.sharpe_ratio >= 0.5:
            score += 10
        
        # Consistency contribution (max 25 points)
        if metrics.max_consecutive_losses <= 3:
            score += 25
        elif metrics.max_consecutive_losses <= 5:
            score += 20
        elif metrics.max_consecutive_losses <= 7:
            score += 15
        elif metrics.max_consecutive_losses <= 10:
            score += 10
        
        return min(100, score)
    
    def _calculate_expectancy(self, metrics: PerformanceMetrics) -> float:
        """Calculate trade expectancy"""
        if metrics.total_trades == 0:
            return 0.0
        
        return (metrics.win_rate * metrics.average_win + 
                (1 - metrics.win_rate) * metrics.average_loss)


class EdgeAnalyzer:
    """
    Analyzes trading edge
    """
    
    def __init__(self):
        self.min_trades_for_significance = 30
    
    def analyze_edge(
        self,
        metrics: PerformanceMetrics,
        trades: List[Dict]
    ) -> EdgeAnalysis:
        """Analyze trading edge"""
        analysis = EdgeAnalysis()
        
        if len(trades) < self.min_trades_for_significance:
            analysis.recommendations.append(
                f"Need at least {self.min_trades_for_significance} trades for statistical significance. "
                f"Current: {len(trades)}"
            )
            return analysis
        
        # Check if edge exists
        analysis.edge_exists = metrics.expectancy > 0 and metrics.profit_factor > 1
        
        # Calculate edge strength
        analysis.edge_strength = self._calculate_edge_strength(metrics)
        
        # Calculate edge consistency
        analysis.edge_consistency = self._calculate_edge_consistency(trades)
        
        # Calculate statistical significance
        analysis.statistical_significance = self._calculate_significance(trades)
        
        # Calculate confidence interval
        analysis.confidence_interval = self._calculate_confidence_interval(trades)
        
        # Calculate edge decay
        analysis.edge_decay_rate = self._calculate_edge_decay(trades)
        
        # Generate recommendations
        analysis.recommendations = self._generate_recommendations(analysis, metrics)
        
        return analysis
    
    def _calculate_edge_strength(self, metrics: PerformanceMetrics) -> float:
        """Calculate edge strength (0-1)"""
        # Combine multiple factors
        factors = []
        
        # Win rate factor
        if metrics.win_rate > 0.5:
            factors.append((metrics.win_rate - 0.5) * 2)
        else:
            factors.append(0)
        
        # Profit factor
        if metrics.profit_factor > 1:
            factors.append(min(1, (metrics.profit_factor - 1) / 2))
        else:
            factors.append(0)
        
        # Sharpe ratio
        if metrics.sharpe_ratio > 0:
            factors.append(min(1, metrics.sharpe_ratio / 3))
        else:
            factors.append(0)
        
        return np.mean(factors) if factors else 0.0
    
    def _calculate_edge_consistency(self, trades: List[Dict]) -> float:
        """Calculate edge consistency over time"""
        if len(trades) < 10:
            return 0.0
        
        # Split trades into periods
        n_periods = min(10, len(trades) // 5)
        period_size = len(trades) // n_periods
        
        period_win_rates = []
        for i in range(n_periods):
            period_trades = trades[i * period_size:(i + 1) * period_size]
            wins = sum(1 for t in period_trades if t.get('pnl', 0) > 0)
            period_win_rates.append(wins / len(period_trades))
        
        # Consistency = 1 - coefficient of variation
        if np.mean(period_win_rates) == 0:
            return 0.0
        
        cv = np.std(period_win_rates) / np.mean(period_win_rates)
        return max(0, 1 - cv)
    
    def _calculate_significance(self, trades: List[Dict]) -> float:
        """Calculate statistical significance using t-test"""
        pnls = [t.get('pnl', 0) for t in trades]
        
        if len(pnls) < 2 or np.std(pnls) == 0:
            return 0.0
        
        # t-statistic
        t_stat = np.mean(pnls) / (np.std(pnls) / np.sqrt(len(pnls)))
        
        # Approximate p-value (simplified)
        # For large samples, t-distribution approaches normal
        from scipy import stats
        try:
            p_value = 2 * (1 - stats.t.cdf(abs(t_stat), len(pnls) - 1))
            return 1 - p_value
        except Exception:
            # Fallback if scipy not available
            return min(1, abs(t_stat) / 3)
    
    def _calculate_confidence_interval(
        self,
        trades: List[Dict],
        confidence: float = 0.95
    ) -> Tuple[float, float]:
        """Calculate confidence interval for expected return"""
        pnls = [t.get('pnl', 0) for t in trades]
        
        if len(pnls) < 2:
            return (0.0, 0.0)
        
        mean = np.mean(pnls)
        std_error = np.std(pnls) / np.sqrt(len(pnls))
        
        # Z-score for 95% confidence
        z = 1.96
        
        lower = mean - z * std_error
        upper = mean + z * std_error
        
        return (lower, upper)
    
    def _calculate_edge_decay(self, trades: List[Dict]) -> float:
        """Calculate edge decay rate over time"""
        if len(trades) < 20:
            return 0.0
        
        # Compare first half vs second half
        mid = len(trades) // 2
        first_half = trades[:mid]
        second_half = trades[mid:]
        
        first_wr = sum(1 for t in first_half if t.get('pnl', 0) > 0) / len(first_half)
        second_wr = sum(1 for t in second_half if t.get('pnl', 0) > 0) / len(second_half)
        
        # Decay rate (positive = edge improving, negative = edge decaying)
        decay = (second_wr - first_wr) / first_wr if first_wr > 0 else 0
        
        return decay
    
    def _generate_recommendations(
        self,
        analysis: EdgeAnalysis,
        metrics: PerformanceMetrics
    ) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        if not analysis.edge_exists:
            recommendations.append(
                "⚠️ No statistical edge detected. Review strategy fundamentals."
            )
        
        if analysis.edge_strength < 0.3:
            recommendations.append(
                "📉 Edge strength is weak. Consider additional filters or signals."
            )
        
        if analysis.edge_consistency < 0.5:
            recommendations.append(
                "📊 Edge is inconsistent. May be regime-dependent. "
                "Consider adding regime filters."
            )
        
        if analysis.edge_decay_rate < -0.1:
            recommendations.append(
                "⚡ Edge appears to be decaying. Market may be adapting. "
                "Consider strategy refresh."
            )
        
        if analysis.statistical_significance < 0.95:
            recommendations.append(
                f"📈 Statistical significance: {analysis.statistical_significance:.1%}. "
                "More trades needed for confidence."
            )
        
        if metrics.max_drawdown > 0.2:
            recommendations.append(
                f"💰 Max drawdown is {metrics.max_drawdown:.1%}. "
                "Consider reducing position sizes."
            )
        
        if metrics.max_consecutive_losses > 5:
            recommendations.append(
                f"🔴 Max consecutive losses: {metrics.max_consecutive_losses}. "
                "Add drawdown protection rules."
            )
        
        if not recommendations:
            recommendations.append(
                "✅ Edge analysis looks healthy. Continue monitoring."
            )
        
        return recommendations


class EdgeAnalyticsDashboard:
    """
    Complete Edge Analytics Dashboard
    """
    
    def __init__(self):
        self.metrics_calculator = MetricsCalculator()
        self.edge_analyzer = EdgeAnalyzer()
        
        self.strategies: Dict[str, StrategyPerformance] = {}
        self.global_metrics: PerformanceMetrics = PerformanceMetrics()
        self.last_update: datetime = datetime.now()
        
        logger.info("Edge Analytics Dashboard initialized")
    
    def add_strategy(self, strategy_id: str, strategy_name: str) -> StrategyPerformance:
        """Add a strategy to track"""
        strategy = StrategyPerformance(
            strategy_id=strategy_id,
            strategy_name=strategy_name
        )
        self.strategies[strategy_id] = strategy
        logger.info(f"Added strategy: {strategy_name}")
        return strategy
    
    def record_trade(
        self,
        strategy_id: str,
        trade: Dict
    ):
        """Record a trade for a strategy"""
        if strategy_id not in self.strategies:
            self.add_strategy(strategy_id, strategy_id)
        
        strategy = self.strategies[strategy_id]
        strategy.trade_history.append(trade)
        
        # Update equity curve
        pnl = trade.get('pnl', 0)
        if strategy.equity_curve:
            new_equity = strategy.equity_curve[-1] + pnl
        else:
            new_equity = 10000 + pnl  # Starting equity
        
        strategy.equity_curve.append(new_equity)
        strategy.timestamps.append(datetime.now())
        
        # Update drawdown curve
        peak = max(strategy.equity_curve)
        drawdown = (peak - new_equity) / peak if peak > 0 else 0
        strategy.drawdown_curve.append(drawdown)
        
        # Recalculate metrics
        self._update_strategy_metrics(strategy_id)
    
    def _update_strategy_metrics(self, strategy_id: str):
        """Update metrics for a strategy"""
        strategy = self.strategies[strategy_id]
        
        if not strategy.trade_history:
            return
        
        # Calculate returns from equity curve
        if len(strategy.equity_curve) > 1:
            returns = [
                (strategy.equity_curve[i] - strategy.equity_curve[i-1]) / strategy.equity_curve[i-1]
                for i in range(1, len(strategy.equity_curve))
            ]
        else:
            returns = []
        
        strategy.metrics = self.metrics_calculator.calculate_all_metrics(
            returns, strategy.trade_history
        )
        
        self.last_update = datetime.now()
    
    def get_strategy_dashboard(self, strategy_id: str) -> Dict:
        """Get dashboard data for a strategy"""
        if strategy_id not in self.strategies:
            return {'error': 'Strategy not found'}
        
        strategy = self.strategies[strategy_id]
        edge_analysis = self.edge_analyzer.analyze_edge(
            strategy.metrics, strategy.trade_history
        )
        
        return {
            'strategy_id': strategy_id,
            'strategy_name': strategy.strategy_name,
            'last_update': self.last_update.isoformat(),
            
            # Summary metrics
            'summary': {
                'total_trades': strategy.metrics.total_trades,
                'win_rate': f"{strategy.metrics.win_rate:.1%}",
                'profit_factor': f"{strategy.metrics.profit_factor:.2f}",
                'sharpe_ratio': f"{strategy.metrics.sharpe_ratio:.2f}",
                'max_drawdown': f"{strategy.metrics.max_drawdown:.1%}",
                'edge_score': f"{strategy.metrics.edge_score:.0f}/100"
            },
            
            # Return metrics
            'returns': {
                'total_return': f"{strategy.metrics.total_return:.2%}",
                'annualized_return': f"{strategy.metrics.annualized_return:.2%}",
                'daily_avg': f"{strategy.metrics.daily_return_avg:.4%}",
                'monthly_avg': f"{strategy.metrics.monthly_return_avg:.2%}"
            },
            
            # Risk metrics
            'risk': {
                'volatility': f"{strategy.metrics.volatility:.2%}",
                'max_drawdown': f"{strategy.metrics.max_drawdown:.2%}",
                'current_drawdown': f"{strategy.metrics.current_drawdown:.2%}",
                'var_95': f"{strategy.metrics.var_95:.4%}",
                'cvar_95': f"{strategy.metrics.cvar_95:.4%}"
            },
            
            # Risk-adjusted metrics
            'risk_adjusted': {
                'sharpe_ratio': strategy.metrics.sharpe_ratio,
                'sortino_ratio': strategy.metrics.sortino_ratio,
                'calmar_ratio': strategy.metrics.calmar_ratio,
                'omega_ratio': strategy.metrics.omega_ratio
            },
            
            # Trade statistics
            'trade_stats': {
                'total_trades': strategy.metrics.total_trades,
                'winning_trades': strategy.metrics.winning_trades,
                'losing_trades': strategy.metrics.losing_trades,
                'win_rate': strategy.metrics.win_rate,
                'average_win': f"${strategy.metrics.average_win:.2f}",
                'average_loss': f"${strategy.metrics.average_loss:.2f}",
                'largest_win': f"${strategy.metrics.largest_win:.2f}",
                'largest_loss': f"${strategy.metrics.largest_loss:.2f}",
                'max_consecutive_wins': strategy.metrics.max_consecutive_wins,
                'max_consecutive_losses': strategy.metrics.max_consecutive_losses
            },
            
            # Edge analysis
            'edge_analysis': {
                'edge_exists': edge_analysis.edge_exists,
                'edge_strength': f"{edge_analysis.edge_strength:.1%}",
                'edge_consistency': f"{edge_analysis.edge_consistency:.1%}",
                'statistical_significance': f"{edge_analysis.statistical_significance:.1%}",
                'edge_decay_rate': f"{edge_analysis.edge_decay_rate:.1%}",
                'confidence_interval': edge_analysis.confidence_interval,
                'recommendations': edge_analysis.recommendations
            },
            
            # Charts data
            'charts': {
                'equity_curve': strategy.equity_curve[-100:],  # Last 100 points
                'drawdown_curve': strategy.drawdown_curve[-100:],
                'timestamps': [t.isoformat() for t in strategy.timestamps[-100:]]
            }
        }
    
    def get_comparison_dashboard(self) -> Dict:
        """Get comparison dashboard for all strategies"""
        if not self.strategies:
            return {'message': 'No strategies to compare'}
        
        comparison = {
            'strategies': [],
            'best_performer': None,
            'worst_performer': None,
            'rankings': {}
        }
        
        for strategy_id, strategy in self.strategies.items():
            comparison['strategies'].append({
                'strategy_id': strategy_id,
                'strategy_name': strategy.strategy_name,
                'total_return': strategy.metrics.total_return,
                'sharpe_ratio': strategy.metrics.sharpe_ratio,
                'win_rate': strategy.metrics.win_rate,
                'max_drawdown': strategy.metrics.max_drawdown,
                'edge_score': strategy.metrics.edge_score
            })
        
        # Find best/worst performers
        if comparison['strategies']:
            by_return = sorted(comparison['strategies'], key=lambda x: x['total_return'], reverse=True)
            comparison['best_performer'] = by_return[0]['strategy_name']
            comparison['worst_performer'] = by_return[-1]['strategy_name']
            
            # Rankings
            comparison['rankings'] = {
                'by_return': [s['strategy_name'] for s in by_return],
                'by_sharpe': [s['strategy_name'] for s in sorted(comparison['strategies'], key=lambda x: x['sharpe_ratio'], reverse=True)],
                'by_win_rate': [s['strategy_name'] for s in sorted(comparison['strategies'], key=lambda x: x['win_rate'], reverse=True)],
                'by_edge_score': [s['strategy_name'] for s in sorted(comparison['strategies'], key=lambda x: x['edge_score'], reverse=True)]
            }
        
        return comparison
    
    def get_global_dashboard(self) -> Dict:
        """Get global dashboard across all strategies"""
        all_trades = []
        all_returns = []
        
        for strategy in self.strategies.values():
            all_trades.extend(strategy.trade_history)
            if len(strategy.equity_curve) > 1:
                returns = [
                    (strategy.equity_curve[i] - strategy.equity_curve[i-1]) / strategy.equity_curve[i-1]
                    for i in range(1, len(strategy.equity_curve))
                ]
                all_returns.extend(returns)
        
        if all_returns:
            self.global_metrics = self.metrics_calculator.calculate_all_metrics(
                all_returns, all_trades
            )
        
        return {
            'total_strategies': len(self.strategies),
            'total_trades': self.global_metrics.total_trades,
            'global_metrics': {
                'total_return': f"{self.global_metrics.total_return:.2%}",
                'win_rate': f"{self.global_metrics.win_rate:.1%}",
                'sharpe_ratio': f"{self.global_metrics.sharpe_ratio:.2f}",
                'max_drawdown': f"{self.global_metrics.max_drawdown:.2%}",
                'edge_score': f"{self.global_metrics.edge_score:.0f}/100"
            },
            'comparison': self.get_comparison_dashboard(),
            'last_update': self.last_update.isoformat()
        }
    
    def render_text_dashboard(self, strategy_id: str = None) -> str:
        """Render a text-based dashboard"""
        if strategy_id:
            data = self.get_strategy_dashboard(strategy_id)
        else:
            data = self.get_global_dashboard()
        
        dashboard = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                         EDGE ANALYTICS DASHBOARD                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
"""
        
        if strategy_id and 'summary' in data:
            dashboard += f"""
║ Strategy: {data['strategy_name']}
║ Last Update: {data['last_update']}
╠══════════════════════════════════════════════════════════════════════════════╣
║                              SUMMARY                                          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Total Trades: {data['summary']['total_trades']:>10}  │  Win Rate: {data['summary']['win_rate']:>10}
║ Profit Factor: {data['summary']['profit_factor']:>9}  │  Sharpe Ratio: {data['summary']['sharpe_ratio']:>7}
║ Max Drawdown: {data['summary']['max_drawdown']:>10}  │  Edge Score: {data['summary']['edge_score']:>9}
╠══════════════════════════════════════════════════════════════════════════════╣
║                              RETURNS                                          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Total Return: {data['returns']['total_return']:>10}  │  Annualized: {data['returns']['annualized_return']:>10}
║ Daily Avg: {data['returns']['daily_avg']:>13}  │  Monthly Avg: {data['returns']['monthly_avg']:>9}
╠══════════════════════════════════════════════════════════════════════════════╣
║                           EDGE ANALYSIS                                       ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Edge Exists: {'✅ YES' if data['edge_analysis']['edge_exists'] else '❌ NO':>12}  │  Strength: {data['edge_analysis']['edge_strength']:>12}
║ Consistency: {data['edge_analysis']['edge_consistency']:>11}  │  Significance: {data['edge_analysis']['statistical_significance']:>8}
╠══════════════════════════════════════════════════════════════════════════════╣
║                          RECOMMENDATIONS                                      ║
╠══════════════════════════════════════════════════════════════════════════════╣
"""
            for rec in data['edge_analysis']['recommendations']:
                dashboard += f"║ • {rec[:70]}\n"
        
        else:
            dashboard += f"""
║ Total Strategies: {data.get('total_strategies', 0)}
║ Total Trades: {data.get('total_trades', 0)}
║ Last Update: {data.get('last_update', 'N/A')}
"""
        
        dashboard += """
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        
        return dashboard
    
    def export_dashboard(self, filename: str = None) -> str:
        """Export dashboard data to JSON"""
        if filename is None:
            filename = f"edge_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        data = {
            'global': self.get_global_dashboard(),
            'strategies': {
                sid: self.get_strategy_dashboard(sid)
                for sid in self.strategies
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.info(f"Dashboard exported to {filename}")
        return filename


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create dashboard
    dashboard = EdgeAnalyticsDashboard()
    
    # Add strategies
    dashboard.add_strategy("momentum", "Momentum Strategy")
    dashboard.add_strategy("mean_reversion", "Mean Reversion Strategy")
    
    # Simulate some trades
    import random
    
    for _ in range(50):
        # Momentum trades
        pnl = random.gauss(50, 100)
        dashboard.record_trade("momentum", {
            'pnl': pnl,
            'entry_time': datetime.now(),
            'exit_time': datetime.now()
        })
        
        # Mean reversion trades
        pnl = random.gauss(30, 80)
        dashboard.record_trade("mean_reversion", {
            'pnl': pnl,
            'entry_time': datetime.now(),
            'exit_time': datetime.now()
        })
    
    # Print dashboard
    print(dashboard.render_text_dashboard("momentum"))
    
    # Get comparison
    comparison = dashboard.get_comparison_dashboard()
    print("\n" + "="*60)
    logger.info("STRATEGY COMPARISON")
    print("="*60)
    logger.info(f"Best Performer: {comparison['best_performer']}")
    logger.info(f"Rankings by Sharpe: {comparison['rankings']['by_sharpe']}")
