import logging
logger = logging.getLogger(__name__)
"""Performance Attribution System.

This module implements comprehensive performance attribution capabilities
to break down profits by strategy, market condition, and time period.
"""

import numpy as np
import pandas as pd
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure
import seaborn as sns
from loguru import logger
from ..adaptive_systems.market_regime import MarketRegime
import numpy
import pandas


class AttributionFactor(Enum):
    """Performance attribution factors."""
    STRATEGY = auto()
    MARKET_REGIME = auto()
    TIMEFRAME = auto()
    SYMBOL = auto()
    SESSION = auto()
    ENTRY_TYPE = auto()
    EXIT_TYPE = auto()
    RISK_PROFILE = auto()
    SENTIMENT = auto()
    VOLATILITY = auto()


@dataclass
class TradePerformance:
    """Performance data for a single trade."""
    trade_id: str
    symbol: str
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    position_size: float
    direction: str  # 'long' or 'short'
    pnl: float
    pnl_percent: float
    strategy: str
    market_regime: MarketRegime
    timeframe: str
    entry_type: str
    exit_type: str
    risk_profile: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration(self) -> timedelta:
        """Get trade duration."""
        return self.exit_time - self.entry_time
    
    @property
    def duration_hours(self) -> float:
        """Get trade duration in hours."""
        return self.duration.total_seconds() / 3600
    
    @property
    def is_winner(self) -> bool:
        """Check if trade was profitable."""
        return self.pnl > 0
    
    @property
    def risk_reward_ratio(self) -> float:
        """Calculate realized risk-reward ratio."""
        initial_risk = self.metadata.get('initial_risk', 0)
        if initial_risk <= 0:
            return 0
        return abs(self.pnl / initial_risk) if self.is_winner else 0


class PerformanceAttributionSystem:
    """Advanced performance attribution system.
    
    Features:
    - Multi-factor performance attribution
    - Strategy-level performance breakdown
    - Market regime performance analysis
    - Time-based performance analysis
    - Risk-adjusted performance metrics
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the performance attribution system.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.trade_history: List[TradePerformance] = []
        self.min_sample_size = self.config.get('min_sample_size', 10)
        self.lookback_days = self.config.get('lookback_days', 30)
        logger.info("PerformanceAttributionSystem initialized")
    
    def add_trade(self, trade_data: Dict[str, Any]):
        """Add a completed trade to the performance history.
        
        Args:
            trade_data: Dictionary with trade information
        """
        try:
            # Create TradePerformance object
            trade = TradePerformance(
                trade_id=trade_data.get('trade_id', str(len(self.trade_history))),
                symbol=trade_data.get('symbol', 'UNKNOWN'),
                entry_time=trade_data.get('entry_time', datetime.now()),
                exit_time=trade_data.get('exit_time', datetime.now()),
                entry_price=trade_data.get('entry_price', 0.0),
                exit_price=trade_data.get('exit_price', 0.0),
                position_size=trade_data.get('position_size', 0.0),
                direction=trade_data.get('direction', 'long'),
                pnl=trade_data.get('pnl', 0.0),
                pnl_percent=trade_data.get('pnl_percent', 0.0),
                strategy=trade_data.get('strategy', 'default'),
                market_regime=trade_data.get('market_regime', MarketRegime.RANGING),
                timeframe=trade_data.get('timeframe', '1h'),
                entry_type=trade_data.get('entry_type', 'manual'),
                exit_type=trade_data.get('exit_type', 'manual'),
                risk_profile=trade_data.get('risk_profile', 'medium'),
                metadata=trade_data.get('metadata', {})
            )
            
            # Add to history
            self.trade_history.append(trade)
            logger.info(f"Added trade {trade.trade_id} to performance history")
            
        except Exception as e:
            logger.error(f"Error adding trade to performance history: {e}")
    
    def get_overall_performance(self) -> Dict[str, Any]:
        """Get overall performance metrics.
        
        Returns:
            Dictionary with performance metrics
        """
        if not self.trade_history:
            return {'status': 'no_data'}
        
        # Calculate basic metrics
        total_trades = len(self.trade_history)
        winning_trades = sum(1 for t in self.trade_history if t.is_winner)
        losing_trades = total_trades - winning_trades
        
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        total_profit = sum(t.pnl for t in self.trade_history if t.pnl > 0)
        total_loss = sum(t.pnl for t in self.trade_history if t.pnl < 0)
        net_profit = total_profit + total_loss
        
        profit_factor = abs(total_profit / total_loss) if total_loss != 0 else float('inf')
        
        # Calculate average metrics
        avg_winner = total_profit / winning_trades if winning_trades > 0 else 0
        avg_loser = total_loss / losing_trades if losing_trades > 0 else 0
        
        # Calculate expectancy
        expectancy = (win_rate * avg_winner) + ((1 - win_rate) * avg_loser)
        
        # Calculate drawdown
        drawdown, max_drawdown = self._calculate_drawdown()
        
        # Calculate Sharpe ratio (simplified)
        returns = [t.pnl_percent for t in self.trade_history]
        sharpe_ratio = np.mean(returns) / np.std(returns) if returns and np.std(returns) > 0 else 0
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_profit': total_profit,
            'total_loss': total_loss,
            'net_profit': net_profit,
            'profit_factor': profit_factor,
            'avg_winner': avg_winner,
            'avg_loser': avg_loser,
            'expectancy': expectancy,
            'current_drawdown': drawdown,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'first_trade_date': self.trade_history[0].entry_time.isoformat() if self.trade_history else None,
            'last_trade_date': self.trade_history[-1].exit_time.isoformat() if self.trade_history else None
        }
    
    def attribute_performance(self, factor: AttributionFactor) -> Dict[str, Any]:
        """Attribute performance to a specific factor.
        
        Args:
            factor: Attribution factor to analyze
            
        Returns:
            Dictionary with attribution analysis
        """
        if not self.trade_history:
            return {'status': 'no_data'}
        
        # Group trades by the specified factor
        grouped_trades = self._group_trades_by_factor(factor)
        
        # Calculate performance metrics for each group
        attribution = {}
        
        for group_name, trades in grouped_trades.items():
            # Skip groups with too few trades
            if len(trades) < self.min_sample_size:
                continue
            
            # Calculate metrics
            total_trades = len(trades)
            winning_trades = sum(1 for t in trades if t.is_winner)
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            
            total_profit = sum(t.pnl for t in trades if t.pnl > 0)
            total_loss = sum(t.pnl for t in trades if t.pnl < 0)
            net_profit = total_profit + total_loss
            
            profit_factor = abs(total_profit / total_loss) if total_loss != 0 else float('inf')
            
            # Calculate contribution to overall performance
            overall_net_profit = sum(t.pnl for t in self.trade_history)
            contribution = net_profit / overall_net_profit if overall_net_profit != 0 else 0
            
            attribution[group_name] = {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'win_rate': win_rate,
                'net_profit': net_profit,
                'profit_factor': profit_factor,
                'contribution': contribution
            }
        
        return {
            'factor': factor.name,
            'attribution': attribution,
            'total_groups': len(attribution)
        }
    
    def get_strategy_performance(self) -> Dict[str, Any]:
        """Get performance breakdown by strategy.
        
        Returns:
            Dictionary with strategy performance metrics
        """
        return self.attribute_performance(AttributionFactor.STRATEGY)
    
    def get_regime_performance(self) -> Dict[str, Any]:
        """Get performance breakdown by market regime.
        
        Returns:
            Dictionary with market regime performance metrics
        """
        return self.attribute_performance(AttributionFactor.MARKET_REGIME)
    
    def get_timeframe_performance(self) -> Dict[str, Any]:
        """Get performance breakdown by timeframe.
        
        Returns:
            Dictionary with timeframe performance metrics
        """
        return self.attribute_performance(AttributionFactor.TIMEFRAME)
    
    def get_symbol_performance(self) -> Dict[str, Any]:
        """Get performance breakdown by symbol.
        
        Returns:
            Dictionary with symbol performance metrics
        """
        return self.attribute_performance(AttributionFactor.SYMBOL)
    
    def get_performance_over_time(self, interval: str = 'day') -> Dict[str, Any]:
        """Get performance metrics over time.
        
        Args:
            interval: Time interval ('day', 'week', 'month')
            
        Returns:
            Dictionary with time-based performance metrics
        """
        if not self.trade_history:
            return {'status': 'no_data'}
        
        # Sort trades by exit time
        sorted_trades = sorted(self.trade_history, key=lambda t: t.exit_time)
        
        # Group trades by time interval
        grouped_trades = {}
        
        for trade in sorted_trades:
            if interval == 'day':
                key = trade.exit_time.strftime('%Y-%m-%d')
            elif interval == 'week':
                key = f"{trade.exit_time.year}-W{trade.exit_time.isocalendar()[1]}"
            elif interval == 'month':
                key = trade.exit_time.strftime('%Y-%m')
            else:
                key = trade.exit_time.strftime('%Y-%m-%d')
            
            if key not in grouped_trades:
                grouped_trades[key] = []
            
            grouped_trades[key].append(trade)
        
        # Calculate metrics for each time period
        time_performance = {}
        cumulative_pnl = 0
        
        for period, trades in grouped_trades.items():
            total_trades = len(trades)
            winning_trades = sum(1 for t in trades if t.is_winner)
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            
            period_pnl = sum(t.pnl for t in trades)
            cumulative_pnl += period_pnl
            
            time_performance[period] = {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'win_rate': win_rate,
                'period_pnl': period_pnl,
                'cumulative_pnl': cumulative_pnl
            }
        
        return {
            'interval': interval,
            'performance': time_performance,
            'periods': len(time_performance)
        }
    
    def generate_equity_curve(self) -> Figure:
        """Generate an equity curve visualization.
        
        Returns:
            Matplotlib Figure with equity curve
        """
        if not self.trade_history:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, "No trade data available", ha='center', va='center')
            return fig
        
        # Sort trades by exit time
        sorted_trades = sorted(self.trade_history, key=lambda t: t.exit_time)
        
        # Create equity curve data
        dates = [t.exit_time for t in sorted_trades]
        equity = np.cumsum([t.pnl for t in sorted_trades])
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Plot equity curve
        ax.plot(dates, equity, label='Equity Curve', color='blue')
        
        # Add drawdown shading
        self._add_drawdown_shading(ax, dates, equity)
        
        # Format x-axis as dates
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        
        # Add labels and title
        ax.set_xlabel('Date')
        ax.set_ylabel('Cumulative P&L')
        ax.set_title('Equity Curve with Drawdown')
        ax.grid(True, alpha=0.3)
        
        # Add legend
        ax.legend()
        
        # Rotate date labels
        plt.xticks(rotation=45)
        
        fig.tight_layout()
        return fig
    
    def generate_attribution_chart(self, factor: AttributionFactor) -> Figure:
        """Generate a chart visualizing performance attribution.
        
        Args:
            factor: Attribution factor to visualize
            
        Returns:
            Matplotlib Figure with attribution chart
        """
        attribution_data = self.attribute_performance(factor)
        
        if attribution_data.get('status') == 'no_data' or not attribution_data.get('attribution'):
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, f"No attribution data available for {factor.name}", ha='center', va='center')
            return fig
        
        # Extract data for visualization
        groups = []
        net_profits = []
        win_rates = []
        trade_counts = []
        
        for group_name, metrics in attribution_data['attribution'].items():
            groups.append(str(group_name))
            net_profits.append(metrics['net_profit'])
            win_rates.append(metrics['win_rate'] * 100)  # Convert to percentage
            trade_counts.append(metrics['total_trades'])
        
        # Create figure with multiple subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Plot net profit by group
        bars = ax1.bar(groups, net_profits, color='skyblue')
        ax1.set_title(f'Net Profit by {factor.name}')
        ax1.set_ylabel('Net Profit')
        ax1.grid(axis='y', alpha=0.3)
        
        # Add data labels
        for bar in bars:
            height = bar.get_height()
            label_text = f"{height:.2f}"
            ax1.text(
                bar.get_x() + bar.get_width() / 2,
                height + (0.1 * max(net_profits) if height > 0 else -0.1 * max(net_profits)),
                label_text,
                ha='center',
                va='bottom' if height > 0 else 'top',
                rotation=0
            )
        
        # Plot win rate and trade count
        ax2.bar(groups, win_rates, color='lightgreen', label='Win Rate (%)')
        
        # Add trade count as text
        for i, count in enumerate(trade_counts):
            ax2.text(i, win_rates[i] + 2, f"{count} trades", ha='center')
        
        ax2.set_title(f'Win Rate by {factor.name}')
        ax2.set_ylabel('Win Rate (%)')
        ax2.set_ylim(0, 100)
        ax2.grid(axis='y', alpha=0.3)
        
        # Rotate x-axis labels if needed
        if max(len(str(g)) for g in groups) > 10:
            plt.setp(ax1.get_xticklabels(), rotation=45, ha='right')
            plt.setp(ax2.get_xticklabels(), rotation=45, ha='right')
        
        fig.tight_layout()
        return fig
    
    def _group_trades_by_factor(self, factor: AttributionFactor) -> Dict[str, List[TradePerformance]]:
        """Group trades by the specified attribution factor."""
        grouped_trades = {}
        
        for trade in self.trade_history:
            if factor == AttributionFactor.STRATEGY:
                key = trade.strategy
            elif factor == AttributionFactor.MARKET_REGIME:
                key = trade.market_regime.value if hasattr(trade.market_regime, 'value') else str(trade.market_regime)
            elif factor == AttributionFactor.TIMEFRAME:
                key = trade.timeframe
            elif factor == AttributionFactor.SYMBOL:
                key = trade.symbol
            elif factor == AttributionFactor.SESSION:
                # Determine trading session based on time
                hour = trade.entry_time.hour
                if 0 <= hour < 8:
                    key = 'Asian'
                elif 8 <= hour < 16:
                    key = 'European'
                else:
                    key = 'American'
            elif factor == AttributionFactor.ENTRY_TYPE:
                key = trade.entry_type
            elif factor == AttributionFactor.EXIT_TYPE:
                key = trade.exit_type
            elif factor == AttributionFactor.RISK_PROFILE:
                key = trade.risk_profile
            elif factor == AttributionFactor.SENTIMENT:
                key = trade.metadata.get('sentiment', 'unknown')
            elif factor == AttributionFactor.VOLATILITY:
                key = trade.metadata.get('volatility', 'medium')
            else:
                key = 'unknown'
            
            if key not in grouped_trades:
                grouped_trades[key] = []
            
            grouped_trades[key].append(trade)
        
        return grouped_trades
    
    def _calculate_drawdown(self) -> Tuple[float, float]:
        """Calculate current and maximum drawdown."""
        if not self.trade_history:
            return 0.0, 0.0
        
        # Sort trades by exit time
        sorted_trades = sorted(self.trade_history, key=lambda t: t.exit_time)
        
        # Calculate equity curve
        equity = np.cumsum([t.pnl for t in sorted_trades])
        
        # Calculate drawdown
        peak = 0
        drawdown = 0
        max_drawdown = 0
        
        for i, e in enumerate(equity):
            if e > peak:
                peak = e
            
            dd = peak - e
            drawdown = dd
            
            if dd > max_drawdown:
                max_drawdown = dd
        
        return drawdown, max_drawdown
    
    def _add_drawdown_shading(self, ax, dates, equity):
        """Add drawdown shading to equity curve plot."""
        # Calculate drawdown for shading
        running_max = np.maximum.accumulate(equity)
        drawdown = running_max - equity
        
        # Find drawdown periods
        is_drawdown = drawdown > 0
        
        # Shade drawdown periods
        for i in range(1, len(is_drawdown)):
            if is_drawdown[i] and is_drawdown[i-1]:
                ax.fill_between([dates[i-1], dates[i]], 
                               [equity[i-1], equity[i]], 
                               [running_max[i-1], running_max[i]], 
                               color='red', alpha=0.3)
    
    def get_recent_performance(self, days: int = None) -> Dict[str, Any]:
        """Get performance metrics for recent trades.
        
        Args:
            days: Number of days to look back (default: use lookback_days from config)
            
        Returns:
            Dictionary with recent performance metrics
        """
        if not self.trade_history:
            return {'status': 'no_data'}
        
        # Use configured lookback days if not specified
        if days is None:
            days = self.lookback_days
        
        # Calculate cutoff date
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Filter recent trades
        recent_trades = [t for t in self.trade_history if t.exit_time >= cutoff_date]
        
        if not recent_trades:
            return {'status': 'no_recent_data'}
        
        # Calculate metrics
        total_trades = len(recent_trades)
        winning_trades = sum(1 for t in recent_trades if t.is_winner)
        losing_trades = total_trades - winning_trades
        
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        total_profit = sum(t.pnl for t in recent_trades if t.pnl > 0)
        total_loss = sum(t.pnl for t in recent_trades if t.pnl < 0)
        net_profit = total_profit + total_loss
        
        profit_factor = abs(total_profit / total_loss) if total_loss != 0 else float('inf')
        
        return {
            'period_days': days,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'net_profit': net_profit,
            'profit_factor': profit_factor,
            'first_trade_date': recent_trades[0].entry_time.isoformat() if recent_trades else None,
            'last_trade_date': recent_trades[-1].exit_time.isoformat() if recent_trades else None
        }
