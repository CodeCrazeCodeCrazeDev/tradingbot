"""
Perfect Bot Dashboard
Real-time visualization of trading performance
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime
import numpy as np


class PerfectBotDashboard:
    """Dashboard for visualizing Perfect Bot performance"""
    
    def __init__(self, logs_dir: str = 'logs'):
        self.logs_dir = Path(logs_dir)
        
    def load_latest_results(self):
        """Load the most recent trading results"""
        if not self.logs_dir.exists():
            print("No logs directory found. Run the bot first!")
            return None, None
        
        # Find latest files
        trade_files = sorted(self.logs_dir.glob('trades_*.json'))
        metric_files = sorted(self.logs_dir.glob('metrics_*.json'))
        
        if not trade_files or not metric_files:
            print("No results found. Run the bot first!")
            return None, None
        
        # Load latest
        with open(trade_files[-1], 'r') as f:
            trades = json.load(f)
        
        with open(metric_files[-1], 'r') as f:
            metrics = json.load(f)
        
        return trades, metrics
    
    def create_dashboard(self):
        """Create comprehensive dashboard"""
        trades, metrics = self.load_latest_results()
        
        if trades is None or metrics is None:
            return
        
        if 'status' in metrics:
            print(f"\n{metrics['status']}")
            print("\nRun the bot with some trades first to see the dashboard!")
            return
        
        # Create figure with subplots
        fig = plt.figure(figsize=(16, 10))
        fig.suptitle('Perfect Bot Performance Dashboard', fontsize=16, fontweight='bold')
        
        # 1. Equity Curve
        ax1 = plt.subplot(2, 3, 1)
        self._plot_equity_curve(ax1, trades, metrics)
        
        # 2. Win/Loss Distribution
        ax2 = plt.subplot(2, 3, 2)
        self._plot_win_loss(ax2, trades)
        
        # 3. Performance Metrics
        ax3 = plt.subplot(2, 3, 3)
        self._plot_metrics(ax3, metrics)
        
        # 4. Trade Distribution by Symbol
        ax4 = plt.subplot(2, 3, 4)
        self._plot_symbol_distribution(ax4, trades)
        
        # 5. P&L Distribution
        ax5 = plt.subplot(2, 3, 5)
        self._plot_pnl_distribution(ax5, trades)
        
        # 6. Trade Timeline
        ax6 = plt.subplot(2, 3, 6)
        self._plot_trade_timeline(ax6, trades)
        
        plt.tight_layout()
        
        # Save dashboard
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'dashboard_{timestamp}.png'
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        print(f"\nDashboard saved to: {filename}")
        
        plt.show()
    
    def _plot_equity_curve(self, ax, trades, metrics):
        """Plot equity curve"""
        if not trades:
            ax.text(0.5, 0.5, 'No trades yet', ha='center', va='center')
            ax.set_title('Equity Curve')
            return
        
        # Calculate cumulative equity
        initial_capital = metrics.get('current_capital', 10000) - sum([t['pnl'] for t in trades])
        equity = [initial_capital]
        
        for trade in trades:
            equity.append(equity[-1] + trade['pnl'])
        
        ax.plot(equity, linewidth=2, color='#2E86AB')
        ax.axhline(y=initial_capital, color='gray', linestyle='--', alpha=0.5)
        ax.fill_between(range(len(equity)), equity, initial_capital, alpha=0.3)
        ax.set_title('Equity Curve', fontweight='bold')
        ax.set_xlabel('Trade Number')
        ax.set_ylabel('Capital ($)')
        ax.grid(True, alpha=0.3)
        
        # Add return percentage
        total_return = metrics.get('total_return', 0)
        color = 'green' if total_return > 0 else 'red'
        ax.text(0.02, 0.98, f'Return: {total_return:.2f}%', 
                transform=ax.transAxes, fontsize=10, fontweight='bold',
                verticalalignment='top', color=color)
    
    def _plot_win_loss(self, ax, trades):
        """Plot win/loss pie chart"""
        if not trades:
            ax.text(0.5, 0.5, 'No trades yet', ha='center', va='center')
            ax.set_title('Win/Loss Distribution')
            return
        
        winning = len([t for t in trades if t['pnl'] > 0])
        losing = len([t for t in trades if t['pnl'] <= 0])
        
        colors = ['#06D6A0', '#EF476F']
        explode = (0.05, 0.05)
        
        ax.pie([winning, losing], labels=['Winning', 'Losing'], 
               autopct='%1.1f%%', colors=colors, explode=explode,
               startangle=90, textprops={'fontweight': 'bold'})
        ax.set_title('Win/Loss Distribution', fontweight='bold')
    
    def _plot_metrics(self, ax, metrics):
        """Plot key metrics"""
        ax.axis('off')
        
        # Key metrics
        metrics_text = f"""
        PERFORMANCE METRICS
        {'='*30}
        
        Total Return:     {metrics.get('total_return', 0):.2f}%
        Current Capital:  ${metrics.get('current_capital', 0):.2f}
        
        Total Trades:     {metrics.get('total_trades', 0)}
        Winning Trades:   {metrics.get('winning_trades', 0)}
        Losing Trades:    {metrics.get('losing_trades', 0)}
        Win Rate:         {metrics.get('win_rate', 0):.1f}%
        
        Avg Win:          ${metrics.get('avg_win', 0):.2f}
        Avg Loss:         ${metrics.get('avg_loss', 0):.2f}
        Profit Factor:    {metrics.get('profit_factor', 0):.2f}
        
        Sharpe Ratio:     {metrics.get('sharpe_ratio', 0):.2f}
        Max Drawdown:     {metrics.get('max_drawdown', 0):.2f}%
        
        Open Positions:   {metrics.get('open_positions', 0)}
        """
        
        ax.text(0.1, 0.95, metrics_text, transform=ax.transAxes,
                fontsize=10, verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
        
        ax.set_title('Key Metrics', fontweight='bold')
    
    def _plot_symbol_distribution(self, ax, trades):
        """Plot trades by symbol"""
        if not trades:
            ax.text(0.5, 0.5, 'No trades yet', ha='center', va='center')
            ax.set_title('Trades by Symbol')
            return
        
        symbols = {}
        for trade in trades:
            symbol = trade['symbol']
            symbols[symbol] = symbols.get(symbol, 0) + 1
        
        ax.bar(symbols.keys(), symbols.values(), color='#118AB2')
        ax.set_title('Trades by Symbol', fontweight='bold')
        ax.set_xlabel('Symbol')
        ax.set_ylabel('Number of Trades')
        ax.grid(True, alpha=0.3, axis='y')
    
    def _plot_pnl_distribution(self, ax, trades):
        """Plot P&L distribution"""
        if not trades:
            ax.text(0.5, 0.5, 'No trades yet', ha='center', va='center')
            ax.set_title('P&L Distribution')
            return
        
        pnls = [t['pnl'] for t in trades]
        
        colors = ['green' if p > 0 else 'red' for p in pnls]
        ax.bar(range(len(pnls)), pnls, color=colors, alpha=0.7)
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax.set_title('P&L per Trade', fontweight='bold')
        ax.set_xlabel('Trade Number')
        ax.set_ylabel('P&L ($)')
        ax.grid(True, alpha=0.3, axis='y')
    
    def _plot_trade_timeline(self, ax, trades):
        """Plot trade timeline"""
        if not trades:
            ax.text(0.5, 0.5, 'No trades yet', ha='center', va='center')
            ax.set_title('Trade Timeline')
            return
        
        # Convert timestamps to datetime
        entry_times = [datetime.fromisoformat(t['entry_time']) for t in trades]
        pnls = [t['pnl'] for t in trades]
        
        colors = ['green' if p > 0 else 'red' for p in pnls]
        ax.scatter(entry_times, pnls, c=colors, alpha=0.6, s=100)
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax.set_title('Trade Timeline', fontweight='bold')
        ax.set_xlabel('Time')
        ax.set_ylabel('P&L ($)')
        ax.grid(True, alpha=0.3)
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    def print_summary(self):
        """Print text summary"""
        trades, metrics = self.load_latest_results()
        
        if trades is None or metrics is None:
            return
        
        if 'status' in metrics:
            print(f"\n{metrics['status']}")
            return
        
        print("\n" + "="*70)
        print("PERFECT BOT PERFORMANCE SUMMARY")
        print("="*70)
        
        print(f"\n📊 OVERALL PERFORMANCE:")
        print(f"  Total Return:     {metrics['total_return']:.2f}%")
        print(f"  Current Capital:  ${metrics['current_capital']:.2f}")
        print(f"  Sharpe Ratio:     {metrics['sharpe_ratio']:.2f}")
        print(f"  Max Drawdown:     {metrics['max_drawdown']:.2f}%")
        
        print(f"\n📈 TRADING STATISTICS:")
        print(f"  Total Trades:     {metrics['total_trades']}")
        print(f"  Winning Trades:   {metrics['winning_trades']}")
        print(f"  Losing Trades:    {metrics['losing_trades']}")
        print(f"  Win Rate:         {metrics['win_rate']:.1f}%")
        
        print(f"\n💰 PROFIT ANALYSIS:")
        print(f"  Average Win:      ${metrics['avg_win']:.2f}")
        print(f"  Average Loss:     ${metrics['avg_loss']:.2f}")
        print(f"  Profit Factor:    {metrics['profit_factor']:.2f}")
        
        print(f"\n🎯 CURRENT STATUS:")
        print(f"  Open Positions:   {metrics['open_positions']}")
        
        # Success indicators
        print(f"\n✅ SUCCESS INDICATORS:")
        if metrics['win_rate'] > 50:
            print(f"  ✅ Win Rate > 50%: {metrics['win_rate']:.1f}%")
        else:
            print(f"  ⚠️  Win Rate < 50%: {metrics['win_rate']:.1f}% (target: >50%)")
        
        if metrics['sharpe_ratio'] > 1.0:
            print(f"  ✅ Sharpe Ratio > 1.0: {metrics['sharpe_ratio']:.2f}")
        else:
            print(f"  ⚠️  Sharpe Ratio < 1.0: {metrics['sharpe_ratio']:.2f} (target: >1.0)")
        
        if metrics['profit_factor'] > 1.5:
            print(f"  ✅ Profit Factor > 1.5: {metrics['profit_factor']:.2f}")
        else:
            print(f"  ⚠️  Profit Factor < 1.5: {metrics['profit_factor']:.2f} (target: >1.5)")
        
        print("\n" + "="*70)


def main():
    """Main function"""
    print("="*70)
    print("PERFECT BOT DASHBOARD")
    print("="*70)
    
    dashboard = PerfectBotDashboard()
    
    # Print text summary
    dashboard.print_summary()
    
    # Create visual dashboard
    print("\nGenerating visual dashboard...")
    dashboard.create_dashboard()


if __name__ == "__main__":
    main()
