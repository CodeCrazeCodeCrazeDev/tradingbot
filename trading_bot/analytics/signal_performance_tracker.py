"""
Signal Performance Tracker
Tracks and analyzes signal performance to identify winning strategies
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
import json
from pathlib import Path
import matplotlib.pyplot as plt
from dataclasses import dataclass, field
import numpy
import pandas

logger = logging.getLogger(__name__)

@dataclass
class SignalStats:
    """Statistics for a signal type"""
    signal_type: str
    trades: int = 0
    wins: int = 0
    losses: int = 0
    total_profit: float = 0.0
    total_loss: float = 0.0
    avg_profit: float = 0.0
    avg_loss: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    returns: List[float] = field(default_factory=list)
    
    def update(self, profit: float):
        """Update stats with trade result"""
        self.trades += 1
        
        # Track returns for Sharpe calculation
        self.returns.append(profit)
        
        if profit > 0:
            self.wins += 1
            self.total_profit += profit
            self.avg_profit = self.total_profit / self.wins if self.wins > 0 else 0
        else:
            self.losses += 1
            self.total_loss += abs(profit)
            self.avg_loss = self.total_loss / self.losses if self.losses > 0 else 0
        
        # Calculate metrics
        self.win_rate = self.wins / self.trades if self.trades > 0 else 0
        self.profit_factor = self.total_profit / self.total_loss if self.total_loss > 0 else float('inf')
        
        # Calculate Sharpe ratio
        if len(self.returns) > 1:
            returns_array = np.array(self.returns)
            self.sharpe_ratio = np.mean(returns_array) / np.std(returns_array) if np.std(returns_array) > 0 else 0
        
        # Calculate max drawdown
        if len(self.returns) > 0:
            cumulative = np.cumsum(self.returns)
            peak = np.maximum.accumulate(cumulative)
            drawdown = (cumulative - peak) / peak if any(peak) else np.zeros_like(cumulative)
            self.max_drawdown = np.min(drawdown) if len(drawdown) > 0 else 0

class SignalPerformanceTracker:
    """
    Tracks and analyzes signal performance
    Features:
    - Per-signal performance metrics
    - Sharpe ratio calculation
    - Signal ranking and weighting
    - Performance visualization
    - Signal leaderboard
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.signals: Dict[str, SignalStats] = {}
        self.trade_history: List[Dict[str, Any]] = []
        
        # Performance thresholds
        self.min_trades = config.get('min_trades_for_ranking', 10)
        self.min_win_rate = config.get('min_win_rate', 0.5)
        self.min_profit_factor = config.get('min_profit_factor', 1.2)
        
        # Signal weights (dynamically updated)
        self.signal_weights: Dict[str, float] = {}
        
        # Create data directory
        Path("data/performance").mkdir(parents=True, exist_ok=True)
        
        logger.info("Signal performance tracker initialized")
    
    def track_signal(self, signal_type: str, trade_result: Dict[str, Any]):
        """
        Track signal performance
        
        Args:
            signal_type: Type of signal (e.g., 'momentum', 'reversal')
            trade_result: Trade execution result
        """
        # Initialize if new signal type
        if signal_type not in self.signals:
            self.signals[signal_type] = SignalStats(signal_type=signal_type)
        
        # Extract profit
        profit = trade_result.get('profit', 0.0)
        
        # Update stats
        self.signals[signal_type].update(profit)
        
        # Add to trade history
        self.trade_history.append({
            'timestamp': datetime.now(),
            'signal_type': signal_type,
            'profit': profit,
            **trade_result
        })
        
        # Update signal weights
        self._update_signal_weights()
        
        # Log performance
        logger.info(f"Signal {signal_type} performance updated: " +
                  f"Win rate: {self.signals[signal_type].win_rate:.2f}, " +
                  f"Profit factor: {self.signals[signal_type].profit_factor:.2f}")
    
    def _update_signal_weights(self):
        """Update signal weights based on performance"""
        # Calculate base weights
        base_weights = {}
        
        for signal_type, stats in self.signals.items():
            # Only consider signals with enough trades
            if stats.trades < self.min_trades:
                base_weights[signal_type] = 0.1  # Default low weight
                continue
            
            # Calculate weight based on performance metrics
            # Higher win rate, profit factor, and Sharpe ratio = higher weight
            win_rate_score = stats.win_rate * 2  # 0-2 range
            profit_factor_score = min(stats.profit_factor / 3, 2)  # Cap at 2
            sharpe_score = min(stats.sharpe_ratio, 3) / 3  # 0-1 range
            
            # Penalize high drawdown
            drawdown_penalty = 1.0 - min(abs(stats.max_drawdown) * 2, 0.5)  # 0.5-1 range
            
            # Combined score
            weight = (win_rate_score * 0.4 + 
                     profit_factor_score * 0.3 + 
                     sharpe_score * 0.2 + 
                     drawdown_penalty * 0.1)
            
            # Minimum threshold
            if stats.win_rate < self.min_win_rate or stats.profit_factor < self.min_profit_factor:
                weight *= 0.5  # Reduce weight for underperforming signals
            
            base_weights[signal_type] = weight
        
        # Normalize weights
        total_weight = sum(base_weights.values())
        if total_weight > 0:
            self.signal_weights = {
                signal_type: weight / total_weight
                for signal_type, weight in base_weights.items()
            }
        else:
            # Equal weights if no data
            signal_count = len(self.signals)
            self.signal_weights = {
                signal_type: 1.0 / signal_count if signal_count > 0 else 1.0
                for signal_type in self.signals
            }
    
    def get_signal_weight(self, signal_type: str) -> float:
        """Get weight for a signal type"""
        return self.signal_weights.get(signal_type, 0.1)  # Default weight for unknown signals
    
    def get_signal_ranking(self) -> List[Tuple[str, float]]:
        """Get ranked list of signals by performance score"""
        rankings = []
        
        for signal_type, stats in self.signals.items():
            # Only rank signals with enough trades
            if stats.trades < self.min_trades:
                continue
            
            # Calculate performance score
            score = (stats.win_rate * 0.4 + 
                    (stats.profit_factor / 5) * 0.3 + 
                    (stats.sharpe_ratio / 2) * 0.3)
            
            rankings.append((signal_type, score))
        
        # Sort by score (descending)
        rankings.sort(key=lambda x: x[1], reverse=True)
        return rankings
    
    def get_leaderboard(self) -> Dict[str, Any]:
        """Get signal performance leaderboard"""
        leaderboard = {
            'timestamp': datetime.now(),
            'signals': []
        }
        
        # Get rankings
        rankings = self.get_signal_ranking()
        
        # Build leaderboard
        for signal_type, score in rankings:
            stats = self.signals[signal_type]
            leaderboard['signals'].append({
                'signal_type': signal_type,
                'score': score,
                'win_rate': stats.win_rate,
                'profit_factor': stats.profit_factor,
                'sharpe_ratio': stats.sharpe_ratio,
                'trades': stats.trades,
                'weight': self.signal_weights.get(signal_type, 0)
            })
        
        # Add signals with insufficient trades
        for signal_type, stats in self.signals.items():
            if stats.trades < self.min_trades:
                leaderboard['signals'].append({
                    'signal_type': signal_type,
                    'score': 0,
                    'win_rate': stats.win_rate,
                    'profit_factor': stats.profit_factor,
                    'sharpe_ratio': stats.sharpe_ratio,
                    'trades': stats.trades,
                    'weight': self.signal_weights.get(signal_type, 0),
                    'status': 'insufficient_data'
                })
        
        return leaderboard
    
    def save_performance_data(self):
        """Save performance data to disk"""
        # Save signal stats
        signal_data = {
            signal_type: {
                'trades': stats.trades,
                'wins': stats.wins,
                'losses': stats.losses,
                'win_rate': stats.win_rate,
                'profit_factor': stats.profit_factor,
                'sharpe_ratio': stats.sharpe_ratio,
                'max_drawdown': stats.max_drawdown,
                'total_profit': stats.total_profit,
                'total_loss': stats.total_loss
            }
            for signal_type, stats in self.signals.items()
        }
        
        with open('data/performance/signal_stats.json', 'w') as f:
            json.dump(signal_data, f, indent=2, default=str)
        
        # Save leaderboard
        with open('data/performance/leaderboard.json', 'w') as f:
            json.dump(self.get_leaderboard(), f, indent=2, default=str)
        
        # Save weights
        with open('data/performance/signal_weights.json', 'w') as f:
            json.dump(self.signal_weights, f, indent=2)
        
        logger.info("Performance data saved")
    
    def load_performance_data(self):
        """Load performance data from disk"""
        try:
            # Load signal stats
            if Path('data/performance/signal_stats.json').exists():
                with open('data/performance/signal_stats.json', 'r') as f:
                    signal_data = json.load(f)
                
                for signal_type, data in signal_data.items():
                    stats = SignalStats(signal_type=signal_type)
                    stats.trades = data.get('trades', 0)
                    stats.wins = data.get('wins', 0)
                    stats.losses = data.get('losses', 0)
                    stats.win_rate = data.get('win_rate', 0)
                    stats.profit_factor = data.get('profit_factor', 0)
                    stats.sharpe_ratio = data.get('sharpe_ratio', 0)
                    stats.max_drawdown = data.get('max_drawdown', 0)
                    stats.total_profit = data.get('total_profit', 0)
                    stats.total_loss = data.get('total_loss', 0)
                    
                    self.signals[signal_type] = stats
            
            # Load weights
            if Path('data/performance/signal_weights.json').exists():
                with open('data/performance/signal_weights.json', 'r') as f:
                    self.signal_weights = json.load(f)
            
            logger.info("Performance data loaded")
            return True
        except Exception as e:
            logger.error(f"Error loading performance data: {e}")
            return False
    
    def generate_performance_report(self):
        """Generate performance report with visualizations"""
        if not self.signals:
            logger.warning("No signal data available for report")
            return
        
        # Create report directory
        Path("reports").mkdir(exist_ok=True)
        
        # Generate plots
        self._generate_performance_plots()
        
        # Generate summary report
        self._generate_summary_report()
        
        logger.info("Performance report generated")
    
    def _generate_performance_plots(self):
        """Generate performance visualization plots"""
        # Create figure with subplots
        fig, axs = plt.subplots(2, 2, figsize=(15, 12))
        
        # Plot 1: Win rates
        ax1 = axs[0, 0]
        signal_types = list(self.signals.keys())
        win_rates = [self.signals[s].win_rate for s in signal_types]
        
        ax1.bar(signal_types, win_rates)
        ax1.set_title('Signal Win Rates')
        ax1.set_ylabel('Win Rate')
        ax1.set_ylim(0, 1)
        ax1.grid(axis='y')
        plt.setp(ax1.get_xticklabels(), rotation=45, ha='right')
        
        # Plot 2: Profit factors
        ax2 = axs[0, 1]
        profit_factors = [min(self.signals[s].profit_factor, 5) for s in signal_types]  # Cap at 5 for visualization
        
        ax2.bar(signal_types, profit_factors)
        ax2.set_title('Signal Profit Factors (capped at 5)')
        ax2.set_ylabel('Profit Factor')
        ax2.set_ylim(0, 5)
        ax2.grid(axis='y')
        plt.setp(ax2.get_xticklabels(), rotation=45, ha='right')
        
        # Plot 3: Signal weights
        ax3 = axs[1, 0]
        weights = [self.signal_weights.get(s, 0) for s in signal_types]
        
        ax3.bar(signal_types, weights)
        ax3.set_title('Signal Weights')
        ax3.set_ylabel('Weight')
        ax3.set_ylim(0, max(weights) * 1.2)
        ax3.grid(axis='y')
        plt.setp(ax3.get_xticklabels(), rotation=45, ha='right')
        
        # Plot 4: Trade counts
        ax4 = axs[1, 1]
        trades = [self.signals[s].trades for s in signal_types]
        wins = [self.signals[s].wins for s in signal_types]
        losses = [self.signals[s].losses for s in signal_types]
        
        ax4.bar(signal_types, wins, label='Wins')
        ax4.bar(signal_types, losses, bottom=wins, label='Losses')
        ax4.set_title('Signal Trade Counts')
        ax4.set_ylabel('Trades')
        ax4.legend()
        ax4.grid(axis='y')
        plt.setp(ax4.get_xticklabels(), rotation=45, ha='right')
        
        # Adjust layout and save
        plt.tight_layout()
        plt.savefig("reports/signal_performance.png")
        plt.close()
    
    def _generate_summary_report(self):
        """Generate summary report"""
        # Get leaderboard
        leaderboard = self.get_leaderboard()
        
        # Calculate overall stats
        total_trades = sum(stats.trades for stats in self.signals.values())
        total_wins = sum(stats.wins for stats in self.signals.values())
        total_losses = sum(stats.losses for stats in self.signals.values())
        total_profit = sum(stats.total_profit for stats in self.signals.values())
        total_loss = sum(stats.total_loss for stats in self.signals.values())
        
        overall_win_rate = total_wins / total_trades if total_trades > 0 else 0
        overall_profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        
        # Create summary
        summary = {
            'timestamp': datetime.now(),
            'overall_stats': {
                'total_trades': total_trades,
                'win_rate': overall_win_rate,
                'profit_factor': overall_profit_factor,
                'total_profit': total_profit,
                'total_loss': total_loss,
                'net_profit': total_profit - total_loss
            },
            'top_signals': leaderboard['signals'][:5] if len(leaderboard['signals']) > 5 else leaderboard['signals'],
            'signal_count': len(self.signals)
        }
        
        # Save summary
        with open('reports/performance_summary.json', 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        # Generate markdown report
        md_report = f"""# Signal Performance Report
Generated: {datetime.now()}

## Overall Performance
- Total Trades: {total_trades}
- Win Rate: {overall_win_rate:.2%}
- Profit Factor: {overall_profit_factor:.2f}
- Net Profit: {total_profit - total_loss:.2f}

## Top Performing Signals
"""
        
        # Add top signals
        for i, signal in enumerate(summary['top_signals']):
            md_report += f"""
### {i+1}. {signal['signal_type']}
- Score: {signal['score']:.2f}
- Win Rate: {signal['win_rate']:.2%}
- Profit Factor: {signal['profit_factor']:.2f}
- Sharpe Ratio: {signal['sharpe_ratio']:.2f}
- Trades: {signal['trades']}
- Weight: {signal['weight']:.2f}
"""
        
        # Save markdown report
        with open('reports/performance_report.md', 'w') as f:
            f.write(md_report)
