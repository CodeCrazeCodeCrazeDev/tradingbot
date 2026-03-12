"""
Performance Tracking and Auto-Optimization System
Continuously improves trading performance through learning
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime, timedelta
from collections import deque
import json
import numpy
import pandas

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Trading performance metrics"""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    average_win: float
    average_loss: float
    profit_factor: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    max_drawdown: float
    recovery_time: float
    total_return: float
    annualized_return: float
    volatility: float

class PerformanceTracker:
    """
    Tracks and analyzes trading performance
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Performance history
        self.trade_history = deque(maxlen=10000)
        self.equity_curve = []
        self.daily_returns = []
        
        # Metrics by strategy
        self.strategy_performance = {}
        
        # Metrics by opportunity type
        self.opportunity_performance = {}
        
        # Time-based metrics
        self.hourly_performance = {}
        self.daily_performance = {}
        self.weekly_performance = {}
        
        # Auto-optimizer
        self.auto_optimizer = AutoOptimizer()
        
        # Metrics calculator
        self.metrics_calculator = MetricsCalculator()
        
        logger.info("Performance Tracker initialized")
    
    def track_trade(self, trade: Dict):
        """
        Track a completed trade
        """
        self.trade_history.append(trade)
        
        # Update equity curve
        self._update_equity_curve(trade)
        
        # Update strategy performance
        strategy = trade.get('strategy', 'unknown')
        if strategy not in self.strategy_performance:
            self.strategy_performance[strategy] = []
        self.strategy_performance[strategy].append(trade)
        
        # Update opportunity type performance
        opp_type = trade.get('opportunity_type', 'unknown')
        if opp_type not in self.opportunity_performance:
            self.opportunity_performance[opp_type] = []
        self.opportunity_performance[opp_type].append(trade)
        
        # Update time-based performance
        self._update_time_performance(trade)
        
        # Trigger optimization if needed
        if len(self.trade_history) % 100 == 0:
            self.auto_optimizer.optimize(self.trade_history)
    
    def _update_equity_curve(self, trade: Dict):
        """Update equity curve with trade result"""
        pnl = trade.get('pnl', 0)
        
        if self.equity_curve:
            new_equity = self.equity_curve[-1] + pnl
        else:
            new_equity = 100000 + pnl  # Starting capital
        
        self.equity_curve.append(new_equity)
        
        # Calculate daily return
        if len(self.equity_curve) > 1:
            daily_return = (self.equity_curve[-1] - self.equity_curve[-2]) / self.equity_curve[-2]
            self.daily_returns.append(daily_return)
    
    def _update_time_performance(self, trade: Dict):
        """Update time-based performance metrics"""
        timestamp = trade.get('timestamp', datetime.now())
        
        # Hourly
        hour = timestamp.hour
        if hour not in self.hourly_performance:
            self.hourly_performance[hour] = []
        self.hourly_performance[hour].append(trade['pnl'])
        
        # Daily
        day = timestamp.date()
        if day not in self.daily_performance:
            self.daily_performance[day] = []
        self.daily_performance[day].append(trade['pnl'])
        
        # Weekly
        week = timestamp.isocalendar()[1]
        if week not in self.weekly_performance:
            self.weekly_performance[week] = []
        self.weekly_performance[week].append(trade['pnl'])
    
    def get_performance_metrics(self) -> PerformanceMetrics:
        """
        Calculate comprehensive performance metrics
        """
        return self.metrics_calculator.calculate_metrics(
            self.trade_history,
            self.equity_curve,
            self.daily_returns
        )
    
    def get_strategy_comparison(self) -> Dict:
        """
        Compare performance across strategies
        """
        comparison = {}
        
        for strategy, trades in self.strategy_performance.items():
            metrics = self.metrics_calculator.calculate_metrics(
                trades, None, None
            )
            comparison[strategy] = {
                'win_rate': metrics.win_rate,
                'profit_factor': metrics.profit_factor,
                'sharpe_ratio': metrics.sharpe_ratio,
                'total_trades': metrics.total_trades,
                'total_return': metrics.total_return
            }
        
        return comparison
    
    def get_optimization_recommendations(self) -> Dict:
        """
        Get optimization recommendations
        """
        return self.auto_optimizer.get_recommendations(
            self.trade_history,
            self.strategy_performance,
            self.opportunity_performance
        )


class MetricsCalculator:
    """
    Calculates trading performance metrics
    """
    
    def calculate_metrics(self, trades: List[Dict], equity_curve: List[float], 
                         daily_returns: List[float]) -> PerformanceMetrics:
        """
        Calculate comprehensive metrics
        """
        if not trades:
            return self._empty_metrics()
        
        # Basic counts
        total_trades = len(trades)
        winning_trades = sum(1 for t in trades if t.get('pnl', 0) > 0)
        losing_trades = sum(1 for t in trades if t.get('pnl', 0) <= 0)
        
        # Win rate
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # Average win/loss
        wins = [t['pnl'] for t in trades if t.get('pnl', 0) > 0]
        losses = [abs(t['pnl']) for t in trades if t.get('pnl', 0) < 0]
        
        average_win = np.mean(wins) if wins else 0
        average_loss = np.mean(losses) if losses else 0
        
        # Profit factor
        total_wins = sum(wins) if wins else 0
        total_losses = sum(losses) if losses else 0
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
        
        # Risk ratios
        sharpe_ratio = self._calculate_sharpe_ratio(daily_returns)
        sortino_ratio = self._calculate_sortino_ratio(daily_returns)
        calmar_ratio = self._calculate_calmar_ratio(equity_curve)
        
        # Drawdown
        max_drawdown = self._calculate_max_drawdown(equity_curve)
        recovery_time = self._calculate_recovery_time(equity_curve)
        
        # Returns
        total_return = self._calculate_total_return(equity_curve)
        daily_returns_len = len(daily_returns) if daily_returns else 0
        annualized_return = self._calculate_annualized_return(total_return, daily_returns_len)
        
        # Volatility
        volatility = np.std(daily_returns) * np.sqrt(252) if daily_returns else 0
        
        return PerformanceMetrics(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            average_win=average_win,
            average_loss=average_loss,
            profit_factor=profit_factor,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            max_drawdown=max_drawdown,
            recovery_time=recovery_time,
            total_return=total_return,
            annualized_return=annualized_return,
            volatility=volatility
        )
    
    def _empty_metrics(self) -> PerformanceMetrics:
        """Return empty metrics"""
        return PerformanceMetrics(
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate=0,
            average_win=0,
            average_loss=0,
            profit_factor=0,
            sharpe_ratio=0,
            sortino_ratio=0,
            calmar_ratio=0,
            max_drawdown=0,
            recovery_time=0,
            total_return=0,
            annualized_return=0,
            volatility=0
        )
    
    def _calculate_sharpe_ratio(self, returns: List[float]) -> float:
        """Calculate Sharpe ratio"""
        if not returns or len(returns) < 2:
            return 0
        
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        if std_return == 0:
            return 0
        
        # Annualized Sharpe
        sharpe = (mean_return * 252) / (std_return * np.sqrt(252))
        
        return sharpe
    
    def _calculate_sortino_ratio(self, returns: List[float]) -> float:
        """Calculate Sortino ratio (downside deviation)"""
        if not returns:
            return 0
        
        mean_return = np.mean(returns)
        downside_returns = [r for r in returns if r < 0]
        
        if not downside_returns:
            return float('inf') if mean_return > 0 else 0
        
        downside_std = np.std(downside_returns)
        
        if downside_std == 0:
            return 0
        
        # Annualized Sortino
        sortino = (mean_return * 252) / (downside_std * np.sqrt(252))
        
        return sortino
    
    def _calculate_calmar_ratio(self, equity_curve: List[float]) -> float:
        """Calculate Calmar ratio (return / max drawdown)"""
        if not equity_curve or len(equity_curve) < 2:
            return 0
        
        total_return = (equity_curve[-1] - equity_curve[0]) / equity_curve[0]
        max_drawdown = self._calculate_max_drawdown(equity_curve)
        
        if max_drawdown == 0:
            return float('inf') if total_return > 0 else 0
        
        return total_return / max_drawdown
    
    def _calculate_max_drawdown(self, equity_curve: List[float]) -> float:
        """Calculate maximum drawdown"""
        if not equity_curve:
            return 0
        
        peak = equity_curve[0]
        max_dd = 0
        
        for value in equity_curve:
            if value > peak:
                peak = value
            
            drawdown = (peak - value) / peak if peak > 0 else 0
            max_dd = max(max_dd, drawdown)
        
        return max_dd
    
    def _calculate_recovery_time(self, equity_curve: List[float]) -> float:
        """Calculate average recovery time from drawdowns"""
        if not equity_curve or len(equity_curve) < 2:
            return 0
        
        recovery_times = []
        peak = equity_curve[0]
        peak_idx = 0
        in_drawdown = False
        
        for i, value in enumerate(equity_curve):
            if value > peak:
                if in_drawdown:
                    recovery_times.append(i - peak_idx)
                    in_drawdown = False
                peak = value
                peak_idx = i
            elif value < peak:
                in_drawdown = True
        
        return np.mean(recovery_times) if recovery_times else 0
    
    def _calculate_total_return(self, equity_curve: List[float]) -> float:
        """Calculate total return"""
        if not equity_curve or len(equity_curve) < 2:
            return 0
        
        return (equity_curve[-1] - equity_curve[0]) / equity_curve[0]
    
    def _calculate_annualized_return(self, total_return: float, num_days: int) -> float:
        """Calculate annualized return"""
        if num_days <= 0:
            return 0
        
        years = num_days / 252
        if years <= 0:
            return 0
        
        return (1 + total_return) ** (1 / years) - 1


class AutoOptimizer:
    """
    Automatically optimizes trading parameters based on performance
    """
    
    def __init__(self):
        self.optimization_history = []
        self.current_parameters = {}
        self.best_parameters = {}
        self.optimization_targets = {
            'sharpe_ratio': 2.0,
            'win_rate': 0.6,
            'profit_factor': 2.0
        }
    
    def optimize(self, trade_history: List[Dict]):
        """
        Run optimization based on recent performance
        """
        if len(trade_history) < 100:
            return
        
        # Analyze recent performance
        recent_trades = list(trade_history)[-100:]
        performance = self._analyze_performance(recent_trades)
        
        # Generate optimization suggestions
        suggestions = self._generate_suggestions(performance)
        
        # Apply optimizations
        self._apply_optimizations(suggestions)
        
        # Track optimization
        self.optimization_history.append({
            'timestamp': datetime.now(),
            'performance': performance,
            'suggestions': suggestions
        })
    
    def _analyze_performance(self, trades: List[Dict]) -> Dict:
        """Analyze recent performance"""
        wins = sum(1 for t in trades if t.get('pnl', 0) > 0)
        total = len(trades)
        
        return {
            'win_rate': wins / total if total > 0 else 0,
            'avg_win': np.mean([t['pnl'] for t in trades if t.get('pnl', 0) > 0]) if wins > 0 else 0,
            'avg_loss': np.mean([abs(t['pnl']) for t in trades if t.get('pnl', 0) < 0]) if wins < total else 0,
            'by_type': self._analyze_by_type(trades),
            'by_time': self._analyze_by_time(trades)
        }
    
    def _analyze_by_type(self, trades: List[Dict]) -> Dict:
        """Analyze performance by opportunity type"""
        by_type = {}
        
        for trade in trades:
            opp_type = trade.get('opportunity_type', 'unknown')
            if opp_type not in by_type:
                by_type[opp_type] = {'wins': 0, 'total': 0, 'pnl': 0}
            
            by_type[opp_type]['total'] += 1
            by_type[opp_type]['pnl'] += trade.get('pnl', 0)
            if trade.get('pnl', 0) > 0:
                by_type[opp_type]['wins'] += 1
        
        # Calculate win rates
        for opp_type in by_type:
            total = by_type[opp_type]['total']
            by_type[opp_type]['win_rate'] = by_type[opp_type]['wins'] / total if total > 0 else 0
        
        return by_type
    
    def _analyze_by_time(self, trades: List[Dict]) -> Dict:
        """Analyze performance by time of day"""
        by_hour = {}
        
        for trade in trades:
            hour = trade.get('timestamp', datetime.now()).hour
            if hour not in by_hour:
                by_hour[hour] = {'wins': 0, 'total': 0}
            
            by_hour[hour]['total'] += 1
            if trade.get('pnl', 0) > 0:
                by_hour[hour]['wins'] += 1
        
        return by_hour
    
    def _generate_suggestions(self, performance: Dict) -> Dict:
        """Generate optimization suggestions"""
        suggestions = {
            'position_sizing': {},
            'opportunity_filters': {},
            'time_filters': {},
            'risk_adjustments': {}
        }
        
        # Position sizing suggestions
        if performance['win_rate'] < 0.5:
            suggestions['position_sizing']['reduce_size'] = 0.8
        elif performance['win_rate'] > 0.7:
            suggestions['position_sizing']['increase_size'] = 1.2
        
        # Opportunity filter suggestions
        for opp_type, stats in performance['by_type'].items():
            if stats['win_rate'] < 0.4:
                suggestions['opportunity_filters'][opp_type] = 'disable'
            elif stats['win_rate'] > 0.7:
                suggestions['opportunity_filters'][opp_type] = 'prioritize'
        
        # Time filter suggestions
        for hour, stats in performance['by_time'].items():
            win_rate = stats['wins'] / stats['total'] if stats['total'] > 0 else 0
            if win_rate < 0.3:
                suggestions['time_filters'][hour] = 'avoid'
        
        # Risk adjustments
        if performance['avg_loss'] > performance['avg_win'] * 1.5:
            suggestions['risk_adjustments']['tighten_stops'] = 0.9
        
        return suggestions
    
    def _apply_optimizations(self, suggestions: Dict):
        """Apply optimization suggestions"""
        # Update current parameters based on suggestions
        
        for category, params in suggestions.items():
            if category not in self.current_parameters:
                self.current_parameters[category] = {}
            
            self.current_parameters[category].update(params)
    
    def get_recommendations(self, trade_history: List[Dict], 
                           strategy_performance: Dict,
                           opportunity_performance: Dict) -> Dict:
        """
        Get optimization recommendations
        """
        recommendations = {
            'parameter_adjustments': self.current_parameters,
            'best_strategies': self._identify_best_strategies(strategy_performance),
            'best_opportunities': self._identify_best_opportunities(opportunity_performance),
            'worst_performers': self._identify_worst_performers(opportunity_performance),
            'optimization_targets': self.optimization_targets
        }
        
        return recommendations
    
    def _identify_best_strategies(self, strategy_performance: Dict) -> List[str]:
        """Identify best performing strategies"""
        strategy_scores = {}
        
        for strategy, trades in strategy_performance.items():
            if len(trades) < 10:
                continue
            
            wins = sum(1 for t in trades if t.get('pnl', 0) > 0)
            win_rate = wins / len(trades)
            avg_pnl = np.mean([t.get('pnl', 0) for t in trades])
            
            score = win_rate * avg_pnl
            strategy_scores[strategy] = score
        
        # Sort by score
        sorted_strategies = sorted(strategy_scores.items(), key=lambda x: x[1], reverse=True)
        
        return [s[0] for s in sorted_strategies[:3]]
    
    def _identify_best_opportunities(self, opportunity_performance: Dict) -> List[str]:
        """Identify best performing opportunity types"""
        opp_scores = {}
        
        for opp_type, trades in opportunity_performance.items():
            if len(trades) < 5:
                continue
            
            wins = sum(1 for t in trades if t.get('pnl', 0) > 0)
            win_rate = wins / len(trades)
            avg_pnl = np.mean([t.get('pnl', 0) for t in trades])
            
            score = win_rate * avg_pnl
            opp_scores[opp_type] = score
        
        sorted_opps = sorted(opp_scores.items(), key=lambda x: x[1], reverse=True)
        
        return [o[0] for o in sorted_opps[:5]]
    
    def _identify_worst_performers(self, opportunity_performance: Dict) -> List[str]:
        """Identify worst performing opportunity types"""
        opp_scores = {}
        
        for opp_type, trades in opportunity_performance.items():
            if len(trades) < 5:
                continue
            
            losses = sum(1 for t in trades if t.get('pnl', 0) < 0)
            loss_rate = losses / len(trades)
            avg_loss = np.mean([t.get('pnl', 0) for t in trades if t.get('pnl', 0) < 0]) if losses > 0 else 0
            
            score = loss_rate * abs(avg_loss)
            opp_scores[opp_type] = score
        
        sorted_opps = sorted(opp_scores.items(), key=lambda x: x[1], reverse=True)
        
        return [o[0] for o in sorted_opps[:3]]


class BacktestEngine:
    """
    Backtests strategies on historical data
    """
    
    def __init__(self):
        self.backtest_results = {}
        
    def backtest_strategy(self, strategy: Dict, historical_data: pd.DataFrame) -> Dict:
        """
        Backtest a trading strategy
        """
        results = {
            'trades': [],
            'equity_curve': [],
            'metrics': {}
        }
        
        # Simulate trading
        equity = 100000
        position = None
        
        for idx, row in historical_data.iterrows():
            # Check for entry signal
            if position is None:
                signal = self._check_entry_signal(strategy, row)
                if signal:
                    position = {
                        'entry_price': row['close'],
                        'entry_time': idx,
                        'size': equity * 0.02 / row['close']  # 2% risk
                    }
            
            # Check for exit signal
            elif position:
                signal = self._check_exit_signal(strategy, row, position)
                if signal:
                    # Close position
                    pnl = (row['close'] - position['entry_price']) * position['size']
                    equity += pnl
                    
                    results['trades'].append({
                        'entry': position['entry_price'],
                        'exit': row['close'],
                        'pnl': pnl,
                        'duration': idx - position['entry_time']
                    })
                    
                    position = None
            
            results['equity_curve'].append(equity)
        
        # Calculate metrics
        if results['trades']:
            calculator = MetricsCalculator()
            results['metrics'] = calculator.calculate_metrics(
                results['trades'],
                results['equity_curve'],
                None
            )
        
        return results
    
    def _check_entry_signal(self, strategy: Dict, row: pd.Series) -> bool:
        """Check for entry signal"""
        # Simplified - would implement actual strategy logic
        return np.random.random() > 0.95
    
    def _check_exit_signal(self, strategy: Dict, row: pd.Series, position: Dict) -> bool:
        """Check for exit signal"""
        # Simple stop loss and take profit
        current_pnl = (row['close'] - position['entry_price']) / position['entry_price']
        
        if current_pnl < -0.02:  # 2% stop loss
            return True
        elif current_pnl > 0.05:  # 5% take profit
            return True
        
        return False
