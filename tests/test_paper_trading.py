"""
Paper Trading Validation

Validates bot performance in paper trading mode before live deployment.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import statistics

logger = logging.getLogger(__name__)


@dataclass
class PaperTrade:
    """Paper trade record"""
    entry_time: datetime
    exit_time: Optional[datetime]
    symbol: str
    side: str
    entry_price: float
    exit_price: Optional[float]
    volume: float
    pnl: Optional[float]
    pnl_pct: Optional[float]
    duration_minutes: Optional[float]
    exit_reason: Optional[str]


class PaperTradingValidator:
    """
    Validates trading bot in paper trading mode
    """
    
    def __init__(self, trading_bot, config: Dict[str, Any] = None):
        self.bot = trading_bot
        self.config = config or {}
        
        # Validation parameters
        self.min_trades = self.config.get('min_trades', 50)
        self.validation_days = self.config.get('validation_days', 7)
        self.min_sharpe = self.config.get('min_sharpe', 0.5)
        self.max_drawdown = self.config.get('max_drawdown', 0.15)
        
        # Tracking
        self.trades: List[PaperTrade] = []
        self.daily_pnl = {}
        self.start_time = None
        self.end_time = None
    
    async def run_validation(self, duration_days: int = None) -> Dict[str, Any]:
        """
        Run paper trading validation
        
        Args:
            duration_days: Validation duration (uses config if None)
        
        Returns:
            Validation results
        """
        duration_days = duration_days or self.validation_days
        
        logger.info("=" * 60)
        logger.info("PAPER TRADING VALIDATION - STARTING")
        logger.info("=" * 60)
        logger.info(f"Duration: {duration_days} days")
        logger.info(f"Minimum trades required: {self.min_trades}")
        logger.info("")
        
        self.start_time = datetime.now()
        end_time = self.start_time + timedelta(days=duration_days)
        
        # Start bot in paper trading mode
        await self.bot.start(paper_trading=True)
        
        # Monitor trading
        while datetime.now() < end_time:
            await self._monitor_trades()
            await asyncio.sleep(60)  # Check every minute
            
            # Print progress
            if len(self.trades) % 10 == 0 and len(self.trades) > 0:
                logger.info(f"Progress: {len(self.trades)} trades completed")
        
        self.end_time = datetime.now()
        
        # Stop bot
        await self.bot.stop()
        
        # Analyze results
        results = self._analyze_results()
        
        # Generate report
        report = self._generate_report(results)
        
        logger.info("\n" + "=" * 60)
        logger.info("PAPER TRADING VALIDATION - COMPLETE")
        logger.info("=" * 60)
        
        return {
            'results': results,
            'report': report,
            'trades': [self._trade_to_dict(t) for t in self.trades],
            'validation_passed': results['validation_passed']
        }
    
    async def _monitor_trades(self):
        """Monitor and record trades"""
        # Get current positions
        positions = self.bot.execution.get_active_positions()
        
        # Check for closed positions
        closed_positions = self.bot.execution.get_closed_positions()
        
        for pos in closed_positions:
            # Check if already recorded
            if not any(t.entry_time == pos.entry_time for t in self.trades):
                trade = PaperTrade(
                    entry_time=pos.entry_time,
                    exit_time=pos.exit_time,
                    symbol=pos.symbol,
                    side=pos.side,
                    entry_price=pos.entry_price,
                    exit_price=pos.exit_price,
                    volume=pos.volume,
                    pnl=pos.realized_pnl,
                    pnl_pct=(pos.exit_price - pos.entry_price) / pos.entry_price if pos.side == 'buy' else (pos.entry_price - pos.exit_price) / pos.entry_price,
                    duration_minutes=(pos.exit_time - pos.entry_time).total_seconds() / 60,
                    exit_reason=pos.exit_reason
                )
                
                self.trades.append(trade)
                
                # Update daily P&L
                date = pos.exit_time.date()
                if date not in self.daily_pnl:
                    self.daily_pnl[date] = 0
                self.daily_pnl[date] += pos.realized_pnl
    
    def _analyze_results(self) -> Dict[str, Any]:
        """Analyze trading results"""
        if not self.trades:
            return {
                'validation_passed': False,
                'reason': 'No trades executed'
            }
        
        # Calculate metrics
        total_trades = len(self.trades)
        winning_trades = [t for t in self.trades if t.pnl > 0]
        losing_trades = [t for t in self.trades if t.pnl < 0]
        
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        
        total_pnl = sum(t.pnl for t in self.trades if t.pnl)
        avg_win = statistics.mean([t.pnl for t in winning_trades]) if winning_trades else 0
        avg_loss = statistics.mean([t.pnl for t in losing_trades]) if losing_trades else 0
        
        # Calculate Sharpe ratio
        returns = [t.pnl_pct for t in self.trades if t.pnl_pct]
        if returns:
            sharpe = (statistics.mean(returns) / statistics.stdev(returns) * (252 ** 0.5)) if len(returns) > 1 else 0
        else:
            sharpe = 0
        
        # Calculate max drawdown
        equity_curve = []
        running_equity = 10000  # Starting equity
        for trade in self.trades:
            running_equity += trade.pnl if trade.pnl else 0
            equity_curve.append(running_equity)
        
        max_drawdown = self._calculate_max_drawdown(equity_curve)
        
        # Calculate profit factor
        gross_profit = sum([t.pnl for t in winning_trades]) if winning_trades else 0
        gross_loss = abs(sum([t.pnl for t in losing_trades])) if losing_trades else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Validation checks
        validation_passed = True
        validation_issues = []
        
        if total_trades < self.min_trades:
            validation_passed = False
            validation_issues.append(f"Insufficient trades: {total_trades} < {self.min_trades}")
        
        if sharpe < self.min_sharpe:
            validation_passed = False
            validation_issues.append(f"Low Sharpe ratio: {sharpe:.2f} < {self.min_sharpe}")
        
        if max_drawdown > self.max_drawdown:
            validation_passed = False
            validation_issues.append(f"Excessive drawdown: {max_drawdown:.1%} > {self.max_drawdown:.1%}")
        
        if win_rate < 0.4:
            validation_passed = False
            validation_issues.append(f"Low win rate: {win_rate:.1%} < 40%")
        
        return {
            'validation_passed': validation_passed,
            'validation_issues': validation_issues,
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            'avg_trade_duration_minutes': statistics.mean([t.duration_minutes for t in self.trades if t.duration_minutes]),
            'daily_pnl': self.daily_pnl
        }
    
    def _calculate_max_drawdown(self, equity_curve: List[float]) -> float:
        """Calculate maximum drawdown"""
        if not equity_curve:
            return 0
        
        peak = equity_curve[0]
        max_dd = 0
        
        for equity in equity_curve:
            if equity > peak:
                peak = equity
            
            dd = (peak - equity) / peak if peak > 0 else 0
            max_dd = max(max_dd, dd)
        
        return max_dd
    
    def _generate_report(self, results: Dict[str, Any]) -> str:
        """Generate validation report"""
        report = []
        report.append("=" * 60)
        report.append("PAPER TRADING VALIDATION REPORT")
        report.append("=" * 60)
        report.append("")
        
        # Status
        status = "✓ PASSED" if results['validation_passed'] else "✗ FAILED"
        report.append(f"Status: {status}")
        report.append("")
        
        # Performance Metrics
        report.append("PERFORMANCE METRICS")
        report.append("-" * 60)
        report.append(f"Total Trades: {results['total_trades']}")
        report.append(f"Win Rate: {results['win_rate']:.1%}")
        report.append(f"Total P&L: ${results['total_pnl']:.2f}")
        report.append(f"Avg Win: ${results['avg_win']:.2f}")
        report.append(f"Avg Loss: ${results['avg_loss']:.2f}")
        report.append(f"Profit Factor: {results['profit_factor']:.2f}")
        report.append(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
        report.append(f"Max Drawdown: {results['max_drawdown']:.1%}")
        report.append(f"Avg Trade Duration: {results['avg_trade_duration_minutes']:.1f} minutes")
        report.append("")
        
        # Validation Checks
        report.append("VALIDATION CHECKS")
        report.append("-" * 60)
        report.append(f"Min Trades ({self.min_trades}): {'✓' if results['total_trades'] >= self.min_trades else '✗'}")
        report.append(f"Min Sharpe ({self.min_sharpe}): {'✓' if results['sharpe_ratio'] >= self.min_sharpe else '✗'}")
        report.append(f"Max Drawdown ({self.max_drawdown:.1%}): {'✓' if results['max_drawdown'] <= self.max_drawdown else '✗'}")
        report.append(f"Min Win Rate (40%): {'✓' if results['win_rate'] >= 0.4 else '✗'}")
        report.append("")
        
        # Issues
        if results['validation_issues']:
            report.append("ISSUES FOUND")
            report.append("-" * 60)
            for issue in results['validation_issues']:
                report.append(f"  • {issue}")
            report.append("")
        
        # Recommendation
        report.append("RECOMMENDATION")
        report.append("-" * 60)
        if results['validation_passed']:
            report.append("✓ Bot is ready for live trading with small position sizes")
            report.append("  • Start with 10% of intended position size")
            report.append("  • Monitor closely for first week")
            report.append("  • Gradually increase size if performance continues")
        else:
            report.append("✗ Bot is NOT ready for live trading")
            report.append("  • Address validation issues above")
            report.append("  • Continue paper trading")
            report.append("  • Re-validate after improvements")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def _trade_to_dict(self, trade: PaperTrade) -> Dict[str, Any]:
        """Convert trade to dictionary"""
        return {
            'entry_time': trade.entry_time.isoformat(),
            'exit_time': trade.exit_time.isoformat() if trade.exit_time else None,
            'symbol': trade.symbol,
            'side': trade.side,
            'entry_price': trade.entry_price,
            'exit_price': trade.exit_price,
            'volume': trade.volume,
            'pnl': trade.pnl,
            'pnl_pct': trade.pnl_pct,
            'duration_minutes': trade.duration_minutes,
            'exit_reason': trade.exit_reason
        }


# Export
__all__ = ['PaperTradingValidator', 'PaperTrade']
